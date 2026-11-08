# MotorSense

**A low-cost edge-AI sensor that predicts motor failures before they happen.**

MotorSense is a custom STM32-based board that clamps onto an industrial motor, measures vibration, current and temperature, analyzes the signals on-device (FFT + features + a small ML model), and reports motor health (healthy / warning / fault) over CAN.

The board is designed to be fab-ready and is verified virtually: SPICE simulation for the analog/power circuits, and a Renode "digital twin" that runs the real firmware against real bearing-fault vibration data.

## Why
- Unplanned motor failures stop production lines.
- Most older machines have no condition monitoring at all.
- A cheap retrofit sensor that runs ML locally avoids streaming raw data to the cloud.

## System overview
| Block | Choice (initial) |
|---|---|
| MCU | STM32G474 (Cortex-M4F, 170 MHz, CAN-FD, CORDIC/FMAC) |
| Vibration | Wide-bandwidth MEMS accelerometer (IIS3DWB), SPI |
| Current | Hall-effect current sensor, ADC |
| Temperature | Digital sensor (TMP117), I2C |
| Comms | CAN-FD transceiver; USB-C for debug/data |
| Power | 12–24 V input → buck → 3.3 V |
| Firmware | Bare-metal C, CMSIS headers only, no HAL |
| DSP | CMSIS-DSP (FFT, envelope analysis) |
| ML | Feature-based model → small autoencoder, int8 on MCU |
| Verification | KiCad + ngspice, Renode, CI on GitHub Actions |

## Repository layout
```
hardware/
  kicad/        Schematic + PCB project
  sim/          SPICE simulations (power, analog front end)
  docs/         Calculations, BOM notes, design review log
firmware/
  startup/      Vector table, startup code
  linker/       Linker script
  drivers/      Register-level drivers (RCC, GPIO, UART, SPI, I2C, TIM, DMA, ADC, CAN)
  app/          Sampling, DSP, inference, CAN protocol
  include/
  renode/       Board description (.repl), scripts (.resc), Robot tests
  tests/        Unit tests (host)
ml/
  notebooks/    Exploration
  src/          Feature extraction, training, export
  data/         Datasets (not committed)
tools/
  dashboard/    PC-side viewer (CAN/USB → live plots)
docs/
  PLAN.md       Phased roadmap and progress
  decisions/    Design decisions (why this part, why this approach)
.github/workflows/  CI: build firmware, run Renode tests
```

## Status
Early development. See [docs/PLAN.md](docs/PLAN.md).

## Author
Karima Boussetta — Industrial Computing & Automation, INSAT
