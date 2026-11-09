# Decision 005: STM32G474 memory map and startup

## Problem

The firmware needs a standalone reset path and a linker map that reflects the STM32G474 family’s discontiguous SRAM regions without relying on STM32 HAL or CMSIS startup code.

## Memory map

- Flash begins at `0x08000000` and is configured as 512 KiB for the G474xE target.
- SRAM1 is 80 KiB at `0x20000000`; SRAM2 is 16 KiB at `0x20014000`. They are adjacent, so the general RAM region is 96 KiB.
- CCM SRAM is 32 KiB at `0x10000000` and is separate from the SRAM1/SRAM2 address range. It has its own `.ccmram` and `.ccm_bss` sections.
- General `.data`, `.bss`, heap, and stack live in SRAM1/SRAM2. The linker reserves a 1 KiB heap and a 2 KiB stack and asserts that the heap cannot overlap the stack.

These sizes and addresses follow the [STM32G474xB/xC/xE datasheet](https://www.st.com/resource/en/datasheet/stm32g474rc.pdf), section 3.4–3.5.

## Startup choice

Use a project-owned C vector table and reset handler. The reset handler enables the Cortex-M4F coprocessor access bits, copies initialized data from flash to SRAM and CCM SRAM, clears both BSS regions, then calls `main`. This keeps the boot path visible and testable while avoiding a dependency on generated vendor startup files. Unhandled exceptions and interrupts go to a default infinite-loop handler.

## Boot smoke-test choice

The first demonstration uses the reset MSI clock (4 MHz), a 1 ms SysTick, and PA5 as a virtual GPIO output. The initial acceptance path uses Renode for the MCU and sensor/CAN peripherals, SPICE for analog and power circuits, and KiCad ERC/DRC for the board design. A NUCLEO-G474RE may be added as an optional hardware milestone later. The current Renode platform is a minimal boot-test model, not full STM32G4 peripheral coverage.
