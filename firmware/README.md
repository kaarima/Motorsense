# Bare-metal boot slice

This Phase 2 slice builds a standalone STM32G474 image with register-only startup and GPIO code. The initial project verification path is virtual; a NUCLEO-G474RE is an optional later target.

## Configure and build

From the repository root, with `arm-none-eabi-gcc` and CMake installed:

```sh
cmake -S . -B build -DCMAKE_TOOLCHAIN_FILE=firmware/cmake/arm-none-eabi.cmake
cmake --build build
```

The ELF and map file are written to `build/firmware/`. Every successful link prints flash usage (`text + data`) and SRAM1+SRAM2 usage (`data + bss`), along with the device capacities. CCM SRAM has a separate linker region and can be used with `.ccmram` or `.ccm_bss` section attributes.

## Run in Renode

From the repository root, with Renode and its Robot test runner installed:

```sh
renode --console -e 'include @firmware/renode/motorsense_g474.resc'
renode-test firmware/renode/tests/gpio_blink.robot
```

The smoke test observes the PA5 output as the firmware configures GPIOA and toggles it from a 1 ms SysTick. PA5 is a convenient virtual GPIO for this boot test. Later, the digital twin will model the IIS3DWB over SPI, replay CWRU data, and carry health messages over Renode CAN to the PC viewer. The Renode platform is intentionally a boot-test digital twin, not a complete STM32G4 model.
