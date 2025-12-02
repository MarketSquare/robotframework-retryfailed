*** Variables ***
${tc_01}        ${0}
${tc_02}        ${0}
${retry_1}      ${0}
${retry_2}      ${0}


*** Test Cases ***
My Simple Test
    Log    Hello World
    Log    This TRACE message should not be logged!    level=TRACE
    Should Be Equal    Hello    Hello

TC01 - Retry Once
    [Tags]    test:retry(2)
    Log    This TRACE message can be logged sometimes    level=TRACE
    VAR    ${tc_01} =    ${${tc_01}+1}    scope=SUITE
    Should Be Equal As Integers    ${tc_01}    ${2}

TC01 - Retry Twice
    [Tags]    test:retry(2)
    Log    This TRACE message can be logged sometimes    level=TRACE
    VAR    ${tc_02} =    ${${tc_02}+1}    scope=SUITE
    Should Be Equal As Integers    ${tc_02}    ${3}

My Simple Test2
    Log    Hello World
    Log    This TRACE message should not be logged!    level=TRACE
    Should Be Equal    Hello    Hello

Log Trace Message
    Log    This TRACE message should not be logged!    level=TRACE

Passes after 3 Fails
    [Tags]    test:retry(3)
    Log    This TRACE message should be logged on failures only!    level=TRACE
    Should Be Equal    ${retry_1}    ${3}
    [Teardown]    Set Suite Variable    ${retry_1}    ${retry_1 + 1}

Passes on 4th Exec
    [Tags]    task:retry(5)
    Log    This TRACE message should be logged on failures only!    level=TRACE
    Should Be Equal    ${retry_2}    ${4}
    [Teardown]    Set Suite Variable    ${retry_2}    ${retry_2 + 1}

My Simple Test1
    Log    Hello World
    Should Be Equal    Hello    Hello
