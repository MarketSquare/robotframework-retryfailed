# robotframework-retryfailed

A listener to automatically retry tests or tasks based on tags.

## Installation

Install with pip:

    pip install robotframework-retryfailed

## Usage

Add the listener to your robot execution, via command line arguments.
When your tests do fail and you have tagged them with `test:retry(2)`, it will retry the test 2 times.
Retry can be also set globally as a parameter to the listener.

### Attaching Listener

Example:

    robot --listener RetryFailed <your robot suite>

    robot --listener RetryFailed:1 <robot suite>

Second one will by default retry once every failing test.

### Tagging Tests

Example:

    *** Test Cases ***
    Test Case
        [Tags]    test:retry(2)
        Log    This test will be retried 2 times if it fails

Tagging tasks by `task:retry(3)` should also work.

### Configuration

On top of specifying the number of retries, you can also define whether your want to **keep the logs** of the retried tests and change the **log level** when retrying, by providing respectfully second and third parameter to the listener: `RetryFailed:<global_retries>:<keep_retried_tests>:<log_level>`

By default the logs of the retried tests are not kept, and the log level remains the same as the regular run.

Example:

    # keep the logs of the retried tests
    robot --listener RetryFailed:1:True

    # does not keep the logs of the retried tests and change log level to DEBUG when retrying
    robot --listener RetryFailed:2:False:DEBUG

    # keep the logs of the retried tests and change the log level to TRACE when retrying
    robot --listener RetryFailed:1:True:TRACE
