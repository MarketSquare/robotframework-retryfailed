*** Variables ***
${counter_01: int} =    0
${counter_02: int} =    0
${counter_03: int} =    0


*** Test Cases ***
Test 1 - PASS
    [Tags]    test:retry(0)
    Successful Keyword

Test 2 - Failed - Pass on 2. Retry
    [Tags]    test:retry(0)
    Error - Pass on Retry    2

Test 3 - Failed Child Keyword - Passed on Multiple Retries
    [Tags]    test:retry(0)
    VAR    ${counter_01} =    ${0}    scope=suite

    Test 3 - Failed Child Keyword

Test 4 - Failed - Retry Test & Keywords
    [Tags]    test:retry(10)

    Test 4 - Parent Keyword

Test 5 - Failed Multiple Child Keywords - Pass on Retry
    [Tags]    test:retry(2)

    Test 5 - Parent Keyword


*** Keywords ***
Successful Keyword
    [Tags]    keyword:retry(2)
    Log    Successful

Error - Pass on Retry
    [Tags]    keyword:retry(2)
    [Arguments]    ${successful_retry: int}
    ${counter_01} =    Evaluate    $counter_01 + 1
    VAR    ${counter_01} =    ${counter_01}    scope=SUITE
    Should Be Equal    ${counter_01}    ${successful_retry}

Test 3 - Failed Child Keyword
    [Tags]    keyword:retry(3)

    Error - Pass on Retry    5

Test 4 - Parent Keyword
    [Tags]    keyword:retry(2)

    Test 4 - Child Keyword    20

Test 4 - Child Keyword
    [Tags]    keyword:retry(2)
    [Arguments]    ${successful_retry: int}
    ${counter_02} =    Evaluate    $counter_02 + 1
    VAR    ${counter_02} =    ${counter_02}    scope=GLOBAL
    Should Be Equal    ${counter_02}    ${successful_retry}

Test 5 - Parent Keyword
    [Tags]    keyword:retry(2)

    Test 5 - First Child Keyword

Test 5 - First Child Keyword
    [Tags]    keyword:retry(2)

    Test 5 - Second Child Keyword    70

Test 5 - Second Child Keyword
    [Tags]    keyword:retry(2)
    [Arguments]    ${successful_retry: int}
    ${counter_03} =    Evaluate    $counter_03 + 1
    VAR    ${counter_03} =    ${counter_03}    scope=GLOBAL
    Should Be Equal    ${counter_03}    ${successful_retry}
