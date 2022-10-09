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

import re

from robot.api import ExecutionResult, ResultVisitor, logger
from robot.libraries.BuiltIn import BuiltIn
from robot.output import Message

duplicate_test_pattern = re.compile(
    r"Multiple .*? with name '(?P<test>.*?)' executed in.*? suite '(?P<suite>.*?)'."
)
linebreak = "\n"


class RetryFailed:

    ROBOT_LISTENER_API_VERSION = 3

    def __init__(self):
        self.retried_tests = []
        self.retries = 0
        self.max_retries = 0

    def start_test(self, test, result):
        for tag in test.tags:
            retry_match = re.match(r"(?:test|task)\:retry\((\d+)\)", tag)
            if retry_match:
                self.max_retries = int(retry_match.group(1))
                return
        self.max_retries = 0
        return

    def end_test(self, test, result):
        if not self.max_retries:
            return
        if result.status == "FAIL":
            if self.retries < self.max_retries:
                index = test.parent.tests.index(test)
                test.parent.tests.insert(index + 1, test)
                result.status = "SKIP"
                result.message += "\nSkipped for Retry"
                self.retried_tests.append(test.longname)
                self.retries += 1
                return
            else:
                result.message += (
                    f"{linebreak * bool(result.message)}[RETRY] FAIL on {self.retries}. retry."
                )
        else:
            if self.retries:
                result.message += (
                    f"{linebreak * bool(result.message)}[RETRY] PASS on {self.retries}. retry."
                )
        self.retries = 0
        return

    def end_suite(self, suite, result):
        test_dict = {}
        result_dict = {}
        for result_test, test in zip(result.tests, suite.tests):
            test_dict[test.id] = test
            result_dict[test.id] = result_test
        result.tests = list(result_dict.values())
        suite.tests = list(test_dict.values())

    def message(self, message):
        if message.level == "WARN":
            match = duplicate_test_pattern.match(message.message)
            if match and f"{match.group('suite')}.{match.group('test')}" in self.retried_tests:
                message.message = (
                    f"Retry {self.retries}/{self.max_retries} of test '{match.group('test')}':"
                )

    def output_file(self, original_output_xml):
        result = ExecutionResult(original_output_xml)
        result.visit(RetryMerger(self.retried_tests))
        result.save()


class RetryMerger(ResultVisitor):
    def __init__(self, retried_tests):
        self.retried_tests = retried_tests
        self.test_ids = {}

    def start_suite(self, suite):
        test_dict = {}
        for test in suite.tests:
            test_dict[test.name] = test
        suite.tests = list(test_dict.values())

    def end_suite(self, suite):
        for test in suite.tests:
            if test.longname in self.retried_tests:
                self.test_ids[test.name] = test.id

    def start_errors(self, errors):
        messages = []
        retry_messages = {}
        for message in errors.messages:
            if message.level == "WARN":
                pattern = re.compile(
                    r"(?P<retries>\d+)/(?P<max_retries>\d+) retry of test '(?P<test>.+)':"
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

    def _get_test_link(self, test_name):
        test_id = self.test_ids.get(test_name)
        link = (
            f"<a "
            f"onclick=\"makeElementVisible('{test_id}')\" "
            f'href="#{test_id}" '
            f'title="Link to details">'
            f"{test_name}"
            f"</a>"
            if test_id
            else test_name
        )
        return link
