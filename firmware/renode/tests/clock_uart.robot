*** Settings ***
Suite Setup       Setup
Suite Teardown    Teardown
Resource          /opt/renode/tests/renode-keywords.robot

*** Test Cases ***
GPIO LED toggles with the reconfigured SysTick
    Create Machine And Load ELF    motorsense.elf
    Create LED Tester              sysbus.gpioPortA.led  defaultTimeout=2
    Start Emulation
    Assert LED State               true   pauseEmulation=true
    Assert LED State               false  pauseEmulation=true

Boot message reports configured clock and firmware version
    Create Machine And Load ELF    motorsense.elf
    Create Terminal Tester         sysbus.lpuart1
    Start Emulation
    Wait For Line On Uart          MotorSense fw .* boot, SYSCLK=170000000    treatAsRegex=true

HardFault prints the stacked and fault status registers
    Create Machine And Load ELF    motorsense_fault_test.elf
    Create Terminal Tester         sysbus.lpuart1
    Start Emulation
    Wait For Line On Uart          MotorSense fw .* boot, SYSCLK=170000000    treatAsRegex=true
    Wait For Line On Uart          Fault register dump
    ${core_registers}=    Set Variable    0x[0-9A-F]{8} .*0x[0-9A-F]{8} .*0x[0-9A-F]{8} .*0x[0-9A-F]{8}
    ${fault_registers}=    Set Variable    0x[0-9A-F]{8} .*0x[0-9A-F]{8} .*0x[0-9A-F]{8} .*0x[0-9A-F]{8}
    ${status_registers}=    Set Variable    0x[0-9A-F]{8} .*0x[0-9A-F]{8}
    ${address_registers}=    Set Variable    0x[0-9A-F]{8} .*0x[0-9A-F]{8}
    Wait For Line On Uart          ${core_registers}       treatAsRegex=true
    Wait For Line On Uart          ${fault_registers}      treatAsRegex=true
    Wait For Line On Uart          ${status_registers}     treatAsRegex=true
    Wait For Line On Uart          ${address_registers}    treatAsRegex=true

*** Keywords ***
Create Machine And Load ELF
    [Arguments]    ${elf}
    Execute Command    mach create
    Execute Command    machine LoadPlatformDescription @${CURDIR}/../motorsense_g474.repl
    Execute Command    sysbus LoadELF @${CURDIR}/../../../build/firmware/${elf}
