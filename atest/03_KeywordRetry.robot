*** Settings ***
Library     KeywordRetry.py


*** Test Cases ***
Test 1 - Low Level Retry PASS
    [Tags]    pass
    Retry Three Times    3    test

Test 2 - Low Level Retry FAIL in Test
    [Tags]    fail    robot:skip-on-failure
    [Teardown]    Run Keyword If    $TEST_STATUS == "PASS"    Fail    Test was expected to fail but it did pass!
    Retry Three Times    5    test

Test 4 - User level Retry PASS
    [Tags]    pass
    VAR    ${retries}    ${1}    scope=TEST
    User Level Retry Three Times    3    retries

Test 5 - User level Retry FAIL
    [Tags]    fail    robot:skip-on-failure
    [Teardown]    Run Keyword If    $TEST_STATUS == "PASS"    Fail    Test was expected to fail but it did pass!
    VAR    ${retries}    ${1}    scope=TEST
    User Level Retry Three Times    5    retries

Test 6 - Recurse Keyword Retry
    Recurse    0    10


*** Keywords ***
Recurse
    [Tags]    keyword:retry(4)
    [Arguments]    ${arg: int}    ${pass_on_count: int}=3
    IF    $arg == $pass_on_count    RETURN

    Recurse    ${arg + 1}    ${pass_on_count}

High Level Pass
    Log    High Level Pass

User Level With Low level Retry
    [Arguments]    ${attempts}
    Retry Three Times    ${attempts}

User Level Retry Three Times
    [Tags]    keyword:retry(3)
    [Arguments]    ${attempts: int}    ${variable: str}=retries
    TRY
        Should Be True    $${variable} == $attempts
    FINALLY
        Inc Test Variable By Name    ${variable}
    END
