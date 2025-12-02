*** Settings ***
Library     KeywordRetry.py


*** Test Cases ***
Test 0 - Low Level Retry PASS
    [Tags]    pass
    Retry Three Times    3    test

Test 1 - Low Level Retry PASS with Setup and Teardown
    [Tags]    pass
    [Setup]    Retry Three Times    3    setup
    Retry Three Times    3    test
    [Teardown]    Retry Three Times    3    teardown

Test 2 - Low Level Retry FAIL in Setup
    [Tags]    fail
    [Setup]    Retry Three Times    5    setup
    Retry Three Times    5    test
    [Teardown]    Retry Three Times    5    teardown

Test 3 - Low Level Retry FAIL in Test
    [Tags]    fail
    Retry Three Times    5    test

Test 4 - User level Retry PASS
    [Tags]    pass
    VAR    ${retries}    ${1}    scope=TEST
    User Level Retry Three Times    3    retries

Test 5 - User level Retry FAIL
    [Tags]    fail
    VAR    ${retries}    ${1}    scope=TEST
    User Level Retry Three Times    5    retries

Test 6 - User level Retry PASS with Teardown
    [Tags]    fail
    VAR    ${keyword}    ${1}    scope=TEST
    VAR    ${teardown}    ${1}    scope=TEST
    User Level Retry Three Times    3    keyword
    [Teardown]    User Level Retry Three Times    3    teardown

Test 7 - User level Retry FAIL with Teardown
    [Tags]    fail
    VAR    ${keyword}    ${1}    scope=TEST
    VAR    ${teardown}    ${1}    scope=TEST
    User Level Retry Three Times    5    keyword
    [Teardown]    User Level Retry Three Times    5    teardown


*** Keywords ***
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
