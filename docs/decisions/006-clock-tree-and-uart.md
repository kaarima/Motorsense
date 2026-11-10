# Decision 006: clock tree and UART

## Problem

The Renode firmware needs a deterministic 170 MHz clock, a console suitable for
the eventual NUCLEO-G474RE, and useful boot and fault diagnostics. Firmware must
remain register-only and use the same target register programming in simulation.

## Clock choice

- Start from reset HSI16 and use it as the PLL source.
- Configure PLLM = 4, PLLN = 85, PLLR = 2, and enable PLLR: `16 MHz / 4 * 85 / 2 = 170 MHz`.
- Select voltage Range 1 boost mode and four Flash wait states before switching SYSCLK to PLL. Leave HCLK and APB prescalers undivided.
- Keep HSE as a future board option. Confirm the NUCLEO clock configuration before selecting a crystal source; the virtual build does not depend on one.
- Derive SysTick from SYSCLK with reload 169999 for a 1 ms tick.

The operating point, voltage scaling, and Flash latency follow RM0440. Clock
startup uses bounded waits so failed hardware startup does not continue at an
unknown frequency.

## UART choice

Use LPUART1 at 115200 baud. On the NUCLEO-G474RE, PA2/PA3 are the default
ST-LINK VCP connection (UM2505); configure both pins for AF12. LPUART1 is
configured from the 170 MHz PCLK using the LPUART BRR scaling. TX uses a
single-producer/single-consumer interrupt-driven ring buffer, and `_write`
retargets newlib `printf`.

The HardFault path bypasses buffered output and polls TXE/TC so it can print
the Cortex-M exception frame (R0-R3, R12, LR, PC, xPSR) and fault status (CFSR,
HFSR, MMFAR, BFAR). It drains queued bytes, prints the dump, then stops.

## Renode choice

Renode 1.15.3's legacy `STM32_UART` model does not implement the G4 LPUART ISR
and TDR offsets. The digital twin uses Renode's `STM32F7_USART` model in
`lowPowerMode` at the LPUART1 address and IRQ, which implements the modern
register layout used by the firmware. This is a simulator compatibility model;
firmware continues to access STM32G4 LPUART1 registers and pins.

Renode 1.15.3 vectors the deliberate `UDF` test instruction through the
UsageFault slot even though configurable faults are disabled. Both the
UsageFault slot and HardFault vector point to the same diagnostic handler,
matching disabled-fault escalation on the MCU while letting the simulator
exercise the dump path.

## References

- [RM0440: STM32G4 reference manual](https://www.st.com/resource/en/reference_manual/rm0440-stm32g4-series-advanced-armbased-32bit-mcus-stmicroelectronics.pdf)
- [UM2505: NUCLEO-G474RE user manual](https://www.st.com/resource/en/user_manual/um2505-getting-started-with-stm32g4-series-nucleo64-board-stmicroelectronics.pdf)
