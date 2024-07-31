*** Settings ***
Test Tags    test:retry(1)

*** Test Cases ***
My Simple Test
    Log     Hello World
    Should Be Equal    Hello    Hello

Simple test to skip retry
    [Tags]    test:skipretry
    Fail     failing this test but it should not retry
