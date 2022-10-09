*** Settings ***
# Library     RetryFailed    log_level=TRACE


*** Variables ***
${retry_1}    ${0}
${retry_2}    ${0}


*** Test Cases ***
My Simple Test
    Log     Hello World
    Should Be Equal    Hello    Hello

Sometime Fail
    [Tags]    test:retry(1)
    Should Be True    ${{random.randint(0, 1)}} == 1

Sometime Fail1
    [Tags]    test:retry(3)
    Should Be True    ${{random.randint(0, 1)}} == 1

Sometime Fail2
    [Tags]    test:retry(1)
    Should Be True    ${{random.randint(0, 1)}} == 1

Passes after 3 Fails
    [Tags]    test:retry(3)
    Should Be Equal    ${retry_1}    ${3}
    [Teardown]    Set Suite Variable    ${retry_1}    ${retry_1 + 1}

Fails on 4th Exec
    [Tags]    task:retry(5)
    Should Be Equal    ${retry_2}    ${4}
    [Teardown]    Set Suite Variable    ${retry_2}    ${retry_2 + 1}

My Simple Test1
    Log    Hello World
    Should Be Equal    Hello    Hello
