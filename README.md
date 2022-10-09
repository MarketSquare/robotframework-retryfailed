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