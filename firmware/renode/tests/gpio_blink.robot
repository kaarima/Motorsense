*** Settings ***
Suite Setup       Setup
Suite Teardown    Teardown
Resource          /opt/renode/tests/renode-keywords.robot

*** Test Cases ***
GPIO LED toggles under SysTick control
    Execute Command          mach create
    Execute Command          machine LoadPlatformDescription @${CURDIR}/../motorsense_g474.repl
    Execute Command          sysbus LoadELF @${CURDIR}/../../../build/firmware/motorsense.elf
    Create LED Tester        sysbus.gpioPortA.led  defaultTimeout=2
    Start Emulation
    Assert LED State         true   pauseEmulation=true
    Assert LED State         false  pauseEmulation=true
