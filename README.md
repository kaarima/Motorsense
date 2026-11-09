# MotorSense

**A virtual-first edge-AI motor condition monitor, with hardware-ready firmware and board design.**

MotorSense targets an STM32G474-based sensor that measures vibration, current, and temperature, analyzes signals on-device, and reports motor health (healthy / warning / fault) over CAN. The current project scope verifies the firmware and end-to-end behavior in Renode, and the analog and power circuits in SPICE. Physical hardware is deferred.

The custom board remains a design deliverable: fab-ready KiCad files with clean ERC/DRC and supporting SPICE simulations. Renode models the IIS3DWB over SPI and feeds it CWRU bearing data; a PC viewer reads the health and spectrum output through Renode CAN. A real NUCLEO-G474RE may be added later as an optional hardware milestone.

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
| Firmware | Bare-metal C, register-level drivers, no HAL |
| DSP | CMSIS-DSP (FFT, envelope analysis) |
| Detection | Per-motor healthy-baseline anomaly score; fault classifier remains an offline reference |
| Verification | Renode virtual MCU/sensors/CAN + CWRU data; ngspice; KiCad ERC/DRC; CI |

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
  dashboard/    PC-side viewer (Renode CAN → live health and spectrum plots)
docs/
  PLAN.md       Phased roadmap and progress
  decisions/    Design decisions (why this part, why this approach)
.github/workflows/  CI: build firmware, run Renode tests
```

## Status
Phase 1 analysis is complete. Phase 2 boot firmware is in progress. The initial acceptance path is fully virtual; see [docs/PLAN.md](docs/PLAN.md).

## Author
Karima Boussetta — Industrial Computing & Automation, INSAT
