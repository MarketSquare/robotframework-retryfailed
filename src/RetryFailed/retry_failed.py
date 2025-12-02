"""Copyright 2022-  René Rohner

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License."""

import copy
import re
from dataclasses import dataclass
from pathlib import Path

from robot.api.deco import library
from robot.api.interfaces import ListenerV3
from robot.libraries.BuiltIn import BuiltIn
from robot.model import Error as ModelError
from robot.model import TestSuite as ModelTestSuite
from robot.result import ExecutionResult, ResultVisitor
from robot.result import Keyword as ResultKeyword
from robot.result import Message as ResultMessage
from robot.result import TestCase as ResultTestCase
from robot.result import TestSuite as ResultTestSuite
from robot.running import Keyword as RunningKeyword
from robot.running import TestCase as RunningTestCase
from robot.running import TestSuite as RunningTestSuite
from robot.utils.robottypes import is_truthy

duplicate_test_pattern = re.compile(
    r"Multiple .*? with name '(?P<test>.*?)' executed in.*? suite '(?P<suite>.*?)'."
)
linebreak = "\n"


@dataclass
class KeywordMetaData:
    kw_obj: RunningKeyword
    kw_index: int
    kw_name: str
    kw_source: str
    kw_lineno: int
    retries: int
    retries_performed: int


@library(scope="GLOBAL")
class RetryFailed(ListenerV3):
    def __init__(
        self,
        global_test_retries: int = 0,
        keep_retried_tests: bool = False,
        log_level: str | None = None,
        warn_on_test_retry: bool = True,
        warn_on_kw_retry: bool = False,
    ):
        self.ROBOT_LIBRARY_LISTENER = self

        # Generic Settings
        self.warn_on_test_retry: bool = is_truthy(warn_on_test_retry)
        self.warn_on_kw_retry: bool = is_truthy(warn_on_kw_retry)

        # TestRetryListener
        self.retried_tests: list[str] = []
        self.retries = 0
        self._max_retries_by_default = int(global_test_retries)
        self.max_retries = global_test_retries
        self.keep_retried_tests = is_truthy(keep_retried_tests)
        self.log_level = log_level
        self._original_log_level: str | None = None
        self.test_retry_active: bool = False
        self.original_testcase_object: RunningTestCase = None

        # KeywordRetryListener
        self.retry_keywords: list[KeywordMetaData] = []
        self._index_counter: int = 1

    def start_test(self, test: RunningTestCase, result: ResultTestCase) -> None:
        if self.retries:
            BuiltIn().set_test_variable("${RETRYFAILED_RETRY_INDEX}", self.retries)
            if self.log_level is not None:
                self._original_log_level = BuiltIn().set_log_level(self.log_level)
        if self.retries == 0 and not self.test_retry_active:
            self.original_testcase_object = copy.deepcopy(test)
        for tag in test.tags:
            retry_match = re.match(r"(?:test|task):retry\((\d+)\)", tag)
            if retry_match:
                self.max_retries = int(retry_match.group(1))
                return
        self.max_retries = self._max_retries_by_default
        return

    def start_keyword(self, keyword: RunningKeyword, result: ResultKeyword) -> None:
        for tag in result.tags:
            retry_kw = re.match(r"keyword:retry\((\d+)\)", tag)
            if not retry_kw:
                return
            _retries = int(retry_kw.group(1))
            if retry_kw and _retries > 0:
                kw_data = KeywordMetaData(
                    kw_obj=keyword,
                    kw_index=keyword.parent.body.index(keyword),
                    kw_name=keyword.name,
                    kw_source=Path(keyword.source).name,
                    kw_lineno=keyword.lineno,
                    retries=_retries,
                    retries_performed=0,
                )

                # check if keyword is already registered for the retry
                for registered_retry_keyword in self.retry_keywords:
                    if (
                        registered_retry_keyword.kw_name == kw_data.kw_name
                        and registered_retry_keyword.kw_source == kw_data.kw_source
                        and registered_retry_keyword.kw_lineno == kw_data.kw_lineno
                    ):
                        return
                self.retry_keywords.append(kw_data)

    def end_keyword(self, keyword: RunningKeyword, result: ResultKeyword) -> None:
        executed_kw_name = keyword.name
        executed_kw_source = Path(keyword.source).name

        # reset original loglevel
        if self._original_log_level:
            BuiltIn().set_log_level(self._original_log_level)

        match_kw_retry = False
        kw_to_retry: KeywordMetaData
        for index, kw in enumerate(self.retry_keywords):
            if kw.kw_name != executed_kw_name or kw.kw_source != executed_kw_source:
                continue
            match_kw_retry = True
            current_index = index
            kw_to_retry = kw

        # If currently executed keyword does not match any defined RetryKeyword -> just return
        if not match_kw_retry:
            return

        link = self._get_keyword_link(result)
        level: str = "WARN" if self.warn_on_kw_retry else "INFO"

        if result.status == "PASS":
            doc = (
                f"[Keyword: {kw_to_retry.kw_name}] PASSED on "
                f"{kw_to_retry.retries_performed}. retry."
            )
            msg = f"[Keyword: {link}] PASSED on {kw_to_retry.retries_performed}. retry."
            if kw_to_retry.retries_performed > 0:
                BuiltIn().log(msg, level=level, html=True)
                result.doc += f"\n\n{doc}"
            self.retry_keywords.pop(current_index)

        if result.status == "FAIL":
            if kw_to_retry.retries and kw_to_retry.retries_performed < kw_to_retry.retries:
                # Set loglevel for retry
                if self.log_level:
                    self._original_log_level = BuiltIn().set_log_level(self.log_level)

                keyword.parent.body.insert(
                    kw_to_retry.kw_index + self._index_counter, kw_to_retry.kw_obj
                )
                result.status = "NOT RUN"
                kw_to_retry.retries_performed += 1
                self.retry_keywords[current_index].retries_performed = kw_to_retry.retries_performed

                performed = self.retry_keywords[current_index].retries_performed
                msg = f"[Keyword: {kw_to_retry.kw_name}] - Skipped for {performed}. Retry..."
                result.doc += f"\n\n{msg}"
            else:
                prefix = "\n\n" if result.message else ""
                doc = (
                    f"{prefix}[Keyword: {kw_to_retry.kw_name}] FAILED on "
                    f"{kw_to_retry.retries_performed}. retry."
                )
                performed = self.retry_keywords[current_index].retries_performed
                msg = f"{prefix}[Keyword: {link}] FAILED on {performed}. retry."
                result.doc += doc
                result.message += doc
                BuiltIn().log(msg.replace("\n", ""), level=level, html=True)
                self.retry_keywords.pop(current_index)

    def end_test(self, test: RunningTestCase, result: ResultTestCase) -> None:
        if self.retries and self._original_log_level is not None:
            BuiltIn().set_log_level(self._original_log_level)
        if not self.max_retries:
            self.retries = 0
            return
        if result.status == "FAIL":
            if self.retries < self.max_retries:
                self.test_retry_active = True
                index = test.parent.tests.index(test)
                test.parent.tests.insert(index + 1, copy.deepcopy(self.original_testcase_object))
                result.status = "SKIP"
                result.message += "\nSkipped for Retry"
                self.retried_tests.append(test.longname)
                self.retries += 1
                return
            self.test_retry_active = False
            result.message += (
                f"{linebreak * bool(result.message)}[RETRY] FAIL on {self.retries}. retry."
            )
        elif self.retries:
            self.test_retry_active = False
            result.message += (
                f"{linebreak * bool(result.message)}[RETRY] PASS on {self.retries}. retry."
            )
        self.retries = 0
        return

    def end_suite(self, suite: RunningTestSuite, result: ResultTestSuite) -> None:
        test_dict = {}
        result_dict = {}
        for result_test, test in zip(result.tests, suite.tests, strict=False):
            test_dict[test.id] = test
            result_dict[test.id] = result_test
        result.tests = list(result_dict.values())
        suite.tests = list(test_dict.values())

    def message(self, message: ResultMessage) -> None:
        if message.level == "WARN":
            match = duplicate_test_pattern.match(message.message)
            if match and f"{match.group('suite')}.{match.group('test')}" in self.retried_tests:
                message.message = (
                    f"Retry {self.retries}/{self.max_retries} of test '{match.group('test')}':"
                )
                if not self.warn_on_test_retry:
                    message.level = "INFO"

    def output_file(self, original_output_xml: Path | None) -> None:
        if original_output_xml is None:
            return
        result = ExecutionResult(original_output_xml)
        result.visit(
            RetryMerger(self.retried_tests, self.keep_retried_tests, self.warn_on_test_retry)
        )
        result.save()

    def _get_keyword_link(self, keyword_result: ResultKeyword) -> str:
        return (
            f"<a "
            f"onclick=\"makeElementVisible('{keyword_result.id}')\" "
            f'href="#{keyword_result.id}" '
            f'title="Link to details">'
            f"{keyword_result.kwname}"
            f"</a>"
            if keyword_result.id
            else keyword_result.kwname
        )


class RetryMerger(ResultVisitor):  # type: ignore[misc]
    def __init__(
        self,
        retried_tests: list[str],
        keep_retried_tests: bool = False,
        warn_on_test_retry: bool = True,
    ):
        self.retried_tests = retried_tests
        self.keep_retried_tests = keep_retried_tests
        self.warn_on_test_retry = warn_on_test_retry
        self.test_ids: dict[str, str] = {}

    def start_suite(self, suite: ModelTestSuite) -> None:
        if self.keep_retried_tests:
            return
        test_dict = {}
        for test in suite.tests:
            test_dict[test.name] = test
        suite.tests = list(test_dict.values())

    def end_suite(self, suite: ModelTestSuite) -> None:
        for test in suite.tests:
            if test.longname in self.retried_tests:
                self.test_ids[test.name] = test.id

    def start_errors(self, errors: ModelError) -> None:
        messages = []
        retry_messages = {}
        for message in errors.messages:
            if message.level == "WARN" and self.warn_on_test_retry:
                pattern = re.compile(
                    r"Retry (?P<retries>\d+)/(?P<max_retries>\d+) of test '(?P<test>.+)':"
                )
                match = pattern.match(message.message)
                if match:
                    link = self._get_test_link(match.group("test"))
                    message.message = (
                        f"Test '{link}' has been retried {match.group('retries')} times "
                        f"(max: {match.group('max_retries')})."
                    )
                    message.html = True
                    retry_messages[match.group("test")] = message
                    continue
            messages.append(message)
        errors.messages = sorted(
            messages + list(retry_messages.values()), key=lambda m: m.timestamp
        )

    def _get_test_link(self, test_name: str) -> str:
        test_id = self.test_ids.get(test_name)
        return (
            f"<a "
            f"onclick=\"makeElementVisible('{test_id}')\" "
            f'href="#{test_id}" '
            f'title="Link to details">'
            f"{test_name}"
            f"</a>"
            if test_id
            else test_name
        )
