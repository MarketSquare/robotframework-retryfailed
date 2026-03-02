from robot.api import logger
from robot.api.deco import keyword
from robot.libraries.BuiltIn import BuiltIn


class KeywordRetry:
    def __init__(self) -> None:
        self.retries: dict[str, int] = {}

    @keyword(tags=["keyword:retry(3)"])
    def retry_three_times(self, attempts: int = 3, alias: str = "Retry Three Times") -> None:
        """A keyword that is set to be retried 3 times upon failure."""
        try:
            assert self.retries.get(alias, 1) == attempts, (
                f"Attempt {self.retries.get(alias, 0)} failed."
            )
        except AssertionError as e:
            self.retries[alias] = self.retries.get(alias, 1) + 1
            raise e

    @keyword
    def inc_test_variable_by_name(self, name: str) -> None:
        """Sets a variable in the Robot Framework context by its name."""
        value = BuiltIn().get_variable_value(f"${{{name}}}", 0) + 1
        logger.info(f"Incrementing variable '${{{name}}}' to {value}")
        BuiltIn().set_test_variable(f"${{{name}}}", value)
