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
from typing import Any, Literal

from robot.api import logger
from robot.api.deco import library
from robot.api.interfaces import ListenerV3
from robot.api.logger import LogLevel
from robot.libraries.BuiltIn import BuiltIn
from robot.model import Error as ModelError
from robot.model import TestSuite as ModelTestSuite
from robot.result import ExecutionResult, ResultVisitor
from robot.result import Keyword as ResultKeyword
from robot.result import Message as ResultMessage
from robot.result import TestCase as ResultTestCase
from robot.running import Keyword as RunningKeyword
from robot.running import TestCase as RunningTestCase
from robot.utils.robottypes import is_truthy

duplicate_test_pattern = re.compile(
    r"Multiple .*? with name '(?P<test>.*?)' executed in.*? suite '(?P<suite>.*?)'."
)
linebreak = "\n"


@dataclass
class RetryKeyword:
    keyword: RunningKeyword
    remaining_retries: int


@library(scope="GLOBAL")
class RetryFailed(ListenerV3):
    def __init__(
        self,
        global_test_retries: int = 0,
        keep_retried_tests: bool = False,
        log_level: LogLevel | None = None,
        warn_on_test_retry: bool = True,
        warn_on_kw_retry: bool = False,
    ):
        self.ROBOT_LIBRARY_LISTENER = self

        # Generic Settings
        self.warn_on_test_retry: bool = is_truthy(warn_on_test_retry)
        self.warn_on_kw_retry: bool = is_truthy(warn_on_kw_retry)

        # TestRetryListener
        self.retried_tests: list[str] = []
        self.test_retries = 0
        self._max_retries_by_default = int(global_test_retries)
        self.max_retries = global_test_retries
        self.keep_retried_tests = is_truthy(keep_retried_tests)
        self.log_level: LogLevel | None = log_level
        self.initial_log_level: str | None = None
        self.test_retry_active: bool = False
        self.original_testcase_object: RunningTestCase = None

        # KeywordRetryListener
        self.retry_stack: list[RetryKeyword] = []

        # Regex to identify retry definition in tags
        self.kw_retry_regex = r"keyword:retry\((\d+)\)"
        self.test_retry_regex = r"(?:test|task):retry\((\d+)\)"

    def start_test(self, test: RunningTestCase, _: ResultTestCase) -> None:
        if self.test_retries:
            BuiltIn().set_test_variable("${RETRYFAILED_RETRY_INDEX}", self.test_retries)
        if self.test_retries == 0 and not self.test_retry_active:
            self.original_testcase_object = copy.deepcopy(test)

        retries = self._check_if_retry(test.tags, "TEST")
        if retries:
            self.max_retries = retries
            return
        self.max_retries = self._max_retries_by_default
        return

    def end_keyword(self, keyword: RunningKeyword, result: ResultKeyword) -> Any:

        # if keyword is not registered for retries -> return
        if not (retries := self._check_if_retry(result.tags, "KEYWORD")):
            return

        level: LogLevel = "WARN" if self.warn_on_kw_retry else "INFO"

        if result.status != "FAIL":
            if self.retry_stack and self.retry_stack[-1].keyword == keyword:
                doc = f"[Keyword: {keyword.name}] PASSED on {retries - self.retry_stack[-1].remaining_retries}. retry."  # noqa
                msg = f"[Keyword: {self._get_keyword_link(result)}] PASSED on {retries - self.retry_stack[-1].remaining_retries}. retry."  # noqa
                BuiltIn().log(msg, level=level, html=True)
                result.doc += f"\n\n{doc}"
                self.retry_stack.pop()
                if not self.retry_stack and not self.test_retry_active:
                    self.reset_loglevel()
            return

        if keyword.type in ("SETUP", "TEARDOWN"):
            BuiltIn().log(
                "Keyword in SETUP & TEARDOWN can't be retried directly - use wrapper keyword!",
                level="WARN",
                html=True,
            )
            return

        # keyword is already getting retried
        if self.retry_stack and self.retry_stack[-1].keyword == keyword:
            # all retries have been executed and keyword still failed
            if not self.retry_stack[-1].remaining_retries:
                msg = f"Keyword '{keyword.name}' FAILED after {retries - self.retry_stack[-1].remaining_retries}. retry!"  # noqa
                self.retry_stack.pop()
                result.doc += f"\n\n{msg}"
                BuiltIn().log(msg, level=level, html=True)
                self.reset_loglevel()
                return
        # keyword failure gets detected the first time
        else:
            self.retry_stack.append(RetryKeyword(keyword, retries))

        msg = f"Keyword '{keyword.name}' - Perform {retries - self.retry_stack[-1].remaining_retries + 1}. retry..."  # noqa
        BuiltIn().log(msg, level=level, html=True)

        # insert keyword to the next executing index in the parent object
        result.status = "NOT RUN"
        keyword.parent.body.insert(keyword.parent.body.index(keyword), keyword)
        self.retry_stack[-1].remaining_retries -= 1

        # set log level in case of keyword must be retried
        if self.log_level:
            self.set_loglevel()

    def end_test(self, test: RunningTestCase, result: ResultTestCase) -> None:
        if not self.max_retries:
            self.test_retries = 0
            return
        if result.status == "FAIL":
            if self.test_retries < self.max_retries:
                if self.log_level:
                    self.set_loglevel()
                self.test_retry_active = True
                index = test.parent.tests.index(test)
                test.parent.tests.insert(index + 1, copy.deepcopy(self.original_testcase_object))
                result.status = "SKIP"
                result.message += "\nSkipped for Retry"
                self.retried_tests.append(test.longname)
                self.test_retries += 1
                return
            self.test_retry_active = False
            result.message += (
                f"{linebreak * bool(result.message)}[RETRY] FAIL on {self.test_retries}. retry."
            )
        elif self.test_retries:
            self.test_retry_active = False
            result.message += (
                f"{linebreak * bool(result.message)}[RETRY] PASS on {self.test_retries}. retry."
            )
        if self.log_level:
            self.reset_loglevel()
        self.test_retries = 0
        return

    def message(self, message: ResultMessage) -> None:
        if message.level == "WARN":
            match = duplicate_test_pattern.match(message.message)
            if match and f"{match.group('suite')}.{match.group('test')}" in self.retried_tests:
                message.message = (
                    f"Retry {self.test_retries}/{self.max_retries} of test '{match.group('test')}':"
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

    def _check_if_retry(self, tags: list[str], token: Literal["TEST", "KEYWORD"]) -> int:
        """
        Function checks if the given test / keyword should be retried or not - defined by their tags
        """
        for tag in tags:
            regex = self.kw_retry_regex if token == "KEYWORD" else self.test_retry_regex
            retry_kw = re.match(regex, tag)
            if not retry_kw:
                continue
            return int(retry_kw.group(1))
        return 0

    def set_loglevel(self) -> None:
        """
        Custom function to set robot log level correctly.
        """
        if BuiltIn()._context.output.log_level.level == self.log_level:
            return
        self.initial_log_level = BuiltIn()._context.output.set_log_level(self.log_level)
        BuiltIn()._namespace.variables.set_global("${LOG_LEVEL}", self.log_level)
        if BuiltIn()._context.output.log_level.level != self.log_level:
            logger.warn("Setting log level failed!")

    def reset_loglevel(self) -> None:
        """
        Custom function to reset robot log level correctly.
        """
        _initial_log_level = BuiltIn()._context.output.initial_log_level
        if BuiltIn()._context.output.log_level.level == _initial_log_level:
            return
        BuiltIn()._context.output.set_log_level(_initial_log_level)
        BuiltIn()._namespace.variables.set_global("${LOG_LEVEL}", _initial_log_level)
        if BuiltIn()._context.output.log_level.level != self.initial_log_level:
            logger.warn("Resetting log level failed!")


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
