# MotorSense — Project Plan

Tracks run in parallel: **ML (Python)**, **Firmware (Renode)**, **Hardware (KiCad)**.
Rough pace: part-time, ~16 weeks.

---

## Phase 0 — Setup (week 1)
- [ ] Create GitHub repo, push this skeleton
- [ ] Install: arm-none-eabi-gcc, CMake, OpenOCD/GDB, Renode, KiCad, Python (numpy, scipy, matplotlib, scikit-learn)
- [ ] Download STM32G474 reference manual (RM0440) + datasheet
- [ ] Download CWRU bearing dataset

## Phase 1 — Signals & ML basics (weeks 1–4) · Python
- [ ] Load CWRU data, plot raw vibration (healthy vs faulty)
- [ ] FFT + windowing; see fault frequencies
- [ ] Envelope analysis for bearing faults
- [ ] Features: RMS, peak, crest factor, kurtosis, band energies
- [ ] First classifier (thresholds / decision tree / isolation forest)
- [ ] Write results in `docs/decisions/` (which features work and why)

## Phase 2 — Bare-metal firmware in Renode (weeks 1–6)
- [ ] Linker script, startup code, vector table
- [ ] Blink a GPIO in Renode (via registers only)
- [ ] Clock: PLL to 170 MHz, flash wait states, SysTick
- [ ] UART: interrupt-driven, ring buffer, printf
- [ ] HardFault handler that dumps registers
- [ ] Timer-triggered sampling + DMA double buffer
- [ ] SPI driver; virtual accelerometer in Renode fed with CWRU data
- [ ] Robot Framework test in Renode + GitHub Actions CI

## Phase 3 — Schematic (weeks 3–8) · KiCad
- [ ] Block diagram + power budget
- [ ] MCU core: decoupling, HSE crystal, NRST, BOOT0, SWD
- [ ] Power: 12–24 V input, protection, buck → 3.3 V
- [ ] Accelerometer, current sensor, temperature sensor
- [ ] CAN-FD transceiver + termination; USB-C
- [ ] SPICE: buck behavior, current-sense amp, anti-aliasing filter
- [ ] ERC clean; schematic PDF exported

## Phase 4 — DSP + ML on the MCU (weeks 7–11)
- [ ] Port features to C with CMSIS-DSP
- [ ] Check C results match Python (same input → same numbers)
- [ ] Quantize model to int8; deploy (TFLite Micro or ST Edge AI)
- [ ] Measure RAM, flash, inference time
- [ ] Health state output: healthy / warning / fault

## Phase 5 — PCB layout (weeks 8–12)
- [ ] Stackup (4-layer), placement, routing
- [ ] DRC clean; 3D render
- [ ] BOM with real part numbers; Gerbers generated
- [ ] Design review (r/PrintedCircuitBoard + Claude); log fixes in `hardware/docs/`

## Phase 6 — Communication & dashboard (weeks 11–14)
- [ ] CAN protocol: message IDs, health frames, config frames
- [ ] (Optional) Modbus RTU
- [ ] Dashboard: live health + spectrum plot

## Phase 7 — Security & polish (weeks 14–16)
- [ ] Secure boot + signed firmware updates (MCUboot)
- [ ] README: block diagram, renders, plots, results
- [ ] Demo video: Renode run → fault detected → dashboard alert
- [ ] LinkedIn post + add to CV

---

## Decisions log
Record each important choice in `docs/decisions/NNN-title.md`: problem, options, choice, reason.
