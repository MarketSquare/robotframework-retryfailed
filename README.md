# robotframework-retryfailed

A listener to automatically retry tests, tasks or keywords based on tags.

## Installation

Install with pip:
```
pip install robotframework-retryfailed
```

## CLI Arguments

You can configure the following CLI arguments when registering the listener in your robotframework cli call:

| Argument | Description | Mandatory | Default Value |
|----------|-------------|-----------|---------------|
| ``global_test_retries`` | Define a global number of retries which is valid for ALL your tests by default! | No | `**0** |
| ``keep_retried_tests`` | Define if the retried tests should be kept in the logs or not. If ``True``, they will be marked with status ``Skip`` | No | **False** |
| ``log_level`` | If set, the loglevel will be changed to the given value IF a test / keyword is getting retried. | No | **None** |
| ``warn_on_test_retry`` | If ``True``, the retried tests will be logged as warning to the ``log.html`` | No | **True** |
| ``warn_on_kw_retry`` | If ``True``, the retried keywords will be logged as warning to the ``log.html`` | No | **False** |

## Usage

Add the listener to your robot execution, via command line arguments.
When your tests do fail and you have tagged them with `test:retry(2)`, it will retry the test 2 times.
Retry can be also set globally as a parameter to the listener.

### Attaching Listener - Retry Tests

Example:
```
# Attaching listener without any default retry configuratio
robot --listener RetryFailed <your robot suite>

# Attach listener & retrying every failed tests once if failed
robot --listener RetryFailed:1 <robot suite>

# Attaching listener, retrying every tests once, keep failed tests in logfile & increase loglevel to TRACE for retry tests.
robot --listener RetryFailed:1:True:TRACE <robot suite>
```

### Retry Test Cases - Tagging Tests

If attaching the listener without any default retry configuration, you must set the count of max. retry as ``Test Tag``.

See Example:
```
*** Test Cases ***
Test Case
    [Tags]    test:retry(2)
    Log    This test will be retried 2 times if it fails
```

Tagging tasks by `task:retry(3)` should also work.

### Retry Keywords - Tagging Keywords

The ``KeywordRetryListener`` is basically always ``activated`` & needs to be defined by yourself within your test.

It makes no sense to configure a default retry count for every keyword, because usually too many keywords are part a test / parent keyword to retry them **ALL** !
This means, you need to define the keywords which should be retried by yourself!

Therefore, you must configure the following ``Keyword Tags``:
```
*** Keywords ***
KeywordABC
    [Documentation]    Keyword takes max. 1 retry!
    [Tags]    keyword:retry(1)

KeywordDEF
    [Documentation]    Keyword takes max. 5 retries!
    [Tags]    keyword:retry(5)
```


### Configuration

On top of specifying the number of retries, you can also define whether your want to **keep the logs** of the retried tests and change the **log level** when retrying, by providing respectfully second and third parameter to the listener: `RetryFailed:<global_retries>:<keep_retried_tests>:<log_level>`

By default the logs of the retried tests are not kept, and the log level remains the same as the regular run.

Example:
```
# keep the logs of the retried tests
robot --listener RetryFailed:1:True

# does not keep the logs of the retried tests and change log level to DEBUG when retrying
robot --listener RetryFailed:2:False:DEBUG

# keep the logs of the retried tests and change the log level to TRACE when retrying
robot --listener RetryFailed:1:True:TRACE

# Same like previous one, but keep in mind: all retried tests are getting logged as warning. But all retried keywords are not getting logged as warning!
robot --listener RetryFailed:1:True:TRACE

# Both retried tests & retried keywords are getting logged as warning into the log.html
robot --listener RetryFailed:1:True:TRACE:True:True

# Only retried keywords are getting logged as warning into the log.html
robot --listener RetryFailed:1:True:TRACE:False:True
```

### Log Warnings at Retry

If you've set both parameters, ``warn_on_test_retry`` & ``warn_on_kw_retry``, to ``False``, a simple ``Info`` message gets logged during the keyword execution in the log.html.

You won't see at the top of the log file, but you can find it directly within the logged keyword execution.