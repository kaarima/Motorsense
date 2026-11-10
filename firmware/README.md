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

## Vibration replay milestone

Decision 007 keeps the existing 12 kHz DSP input contract. The IIS3DWB runs at
its fixed 26.667 kHz ODR, so acquisition must anti-alias and resample at 9/20
before producing 6,000-sample windows. The Renode test replays the 12 kHz
drive-end channel from CWRU `105.mat`, checks reported window RMS against the
Python reference, and checks the overrun counter.

Generate the ignored replay file, build, and run the Robot suite in the project
Docker image:

```sh
docker run --rm -v "$PWD:/workspace" -w /workspace motorsense-dev:latest \
  bash -lc 'python tools/generate_iis3dwb_playback.py ml/data/105.mat && \
  cmake -S . -B build -DCMAKE_TOOLCHAIN_FILE=firmware/cmake/arm-none-eabi.cmake && \
  cmake --build build --parallel 2 && \
  renode-test firmware/renode/tests/clock_uart.robot'
```

Current Renode 1.15.3 platform support does not connect the custom Python
register shim to an STM32 SPI controller or DMA request lines. The current
firmware therefore polls the mock SPI window and uses CPU-filled ping-pong
sample blocks; this proves CWRU playback and RMS parity, but does not meet the
DMA half/full interrupt requirement. Replace the shim with a connected SPI
slave model and add real DMA plus timer or DRDY-driven acquisition before
treating the sampling milestone as complete or targeting the NUCLEO board.
