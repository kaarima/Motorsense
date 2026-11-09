*** Settings ***
Suite Setup       Setup
Suite Teardown    Teardown
Library           RenodeLibrary

*** Test Cases ***
GPIO LED toggles under SysTick control
    Execute Command       machine LoadPlatformDescription @firmware/renode/motorsense_g474.repl
    Execute Command       sysbus LoadELF @build/firmware/motorsense.elf
    Create LED Tester     sysbus.gpioPortA.led defaultTimeout=2
    Start Emulation
    Wait For LED On
    Wait For LED Off

*** Keywords ***
Setup
    Execute Command    mach create

Teardown
    Execute Command    pause
