# Clock and UART boot slice

This Phase 2 slice builds a standalone STM32G474 image with register-only
startup, a 170 MHz HSI16-PLL clock, 1 ms SysTick, PA5 blink, and LPUART1 at
115200 baud. `printf` uses an interrupt-driven TX ring buffer. A separate test
image deliberately faults to exercise the polled HardFault register dump.
Renode is the current verification target; a NUCLEO-G474RE is an optional later
target.

## Configure and build

From the repository root, with `arm-none-eabi-gcc` and CMake installed:

```sh
cmake -S . -B build -DCMAKE_TOOLCHAIN_FILE=firmware/cmake/arm-none-eabi.cmake
cmake --build build
```

The ELF and map file are written to `build/firmware/`. Every build prints flash
usage (`text + data`) and SRAM1+SRAM2 usage (`data + bss`) for both firmware
images. CCM SRAM has a separate linker region and can be used with `.ccmram` or
`.ccm_bss` section attributes. Firmware version comes from `git describe
--always --dirty --tags` at build time.

## Run in Renode

From the repository root, with Renode and its Robot test runner installed:

```sh
renode --console -e 'include @firmware/renode/motorsense_g474.resc'
renode-test firmware/renode/tests/clock_uart.robot
```

The Robot suite checks PA5 toggling, the boot UART line, and the register dump
from the deliberate HardFault image. Renode 1.15.3 models the G4 LPUART
registers with its `STM32F7_USART` peripheral in low-power mode. The platform
is intentionally a boot-test digital twin, not a complete STM32G4 model.
Later, the digital twin will model the IIS3DWB over SPI, replay CWRU data, and
carry health messages over Renode CAN to the PC viewer.
