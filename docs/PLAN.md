# MotorSense — Project Plan

Tracks run in parallel: **ML (Python)**, **Firmware and digital twin (Renode)**, **Hardware design and analog simulation (KiCad/ngspice)**.
Rough pace: part-time, ~16 weeks. No physical hardware is required for the initial project acceptance.

## Initial end-to-end acceptance

Replay CWRU vibration through a Renode IIS3DWB-over-SPI model, run the bare-metal acquisition and frozen anomaly detector, send health over Renode CAN, and display it in the PC viewer. Verify analog and power circuits with SPICE and deliver a fab-ready KiCad design with clean ERC/DRC. A NUCLEO-G474RE hardware run is optional future work.

---

## Phase 0 — Setup (week 1)
- [ ] Create GitHub repo, push this skeleton
- [ ] Install: arm-none-eabi-gcc, CMake, Renode, KiCad/ngspice, Python (numpy, scipy, matplotlib, scikit-learn); OpenOCD/GDB is optional for later hardware work
- [ ] Download STM32G474 reference manual (RM0440) + datasheet
- [x] Download CWRU bearing dataset

## Phase 1 — Signals & ML basics (weeks 1–4) · Python
- [x] Load CWRU data, plot raw vibration (healthy vs faulty)
- [x] FFT + windowing; compare shaft harmonics to verify the 97.mat sample rate
- [x] Identify bearing fault frequencies from RPM + bearing geometry
- [x] Envelope analysis for bearing faults
- [x] Features: RMS, peak, crest factor, kurtosis
- [x] Band energies around drive-end bearing defect orders in the envelope spectrum
- [x] First classifier with a load-held-out test set
- [x] Write results in `docs/decisions/` (which features work and why)
- [x] Compare scale-invariant fault features and per-motor healthy-baseline anomaly detection
- [x] Freeze Phase 1 anomaly features and model as the initial firmware spec

## Phase 2 — Bare-metal firmware in Renode (weeks 1–6)
Current slice: standalone STM32G474 boot, GPIOA/PA5 blink using SysTick, and a Renode LED smoke test on `fw/bare-metal-boot`.
- [ ] Linker script, startup code, vector table
- [ ] Blink a GPIO in Renode (via registers only)
- [ ] Clock: PLL to 170 MHz, flash wait states, SysTick
- [ ] UART: interrupt-driven, ring buffer, printf
- [ ] HardFault handler that dumps registers
- [ ] Timer-triggered sampling + DMA double buffer
- [ ] SPI driver; Renode IIS3DWB model fed with CWRU data
- [ ] Robot Framework test in Renode + GitHub Actions CI

## Phase 3 — Schematic and analog simulation (weeks 3–8) · KiCad/ngspice
- [ ] Block diagram + power budget
- [ ] MCU core: decoupling, HSE crystal, NRST, BOOT0, SWD
- [ ] Power: 12–24 V input, protection, buck → 3.3 V
- [ ] Accelerometer, current sensor, temperature sensor
- [ ] CAN-FD transceiver + termination; USB-C
- [ ] SPICE: buck behavior, current-sense amp, anti-aliasing filter
- [ ] ERC clean; schematic PDF exported
Scope: schematic and SPICE verification only; stop at design and simulation.

## Phase 4 — DSP + anomaly detection on the MCU (weeks 7–11)
- [ ] Port features to C with CMSIS-DSP
- [ ] Check C results match Python (same input → same numbers)
- [ ] Store per-motor robust healthy baseline (feature medians, scales, threshold) and score on-device
- [ ] Measure RAM, flash, inference time
- [ ] Health state output: healthy / warning / fault

## Phase 5 — PCB layout (weeks 8–12)
- [ ] Stackup (4-layer), placement, routing
- [ ] DRC clean; 3D render
- [ ] BOM with real part numbers; Gerbers generated
- [ ] Design review (r/PrintedCircuitBoard + Claude); log fixes in `hardware/docs/`
Deliverable: fab-ready KiCad project. Fabrication and physical bring-up are outside the current scope.

## Phase 6 — Renode CAN & PC viewer (weeks 11–14)
- [ ] CAN protocol: message IDs, health frames, config frames
- [ ] Renode CAN model/bridge sends health and spectrum data to the PC viewer
- [ ] PC viewer reads Renode CAN and displays live health + spectrum
- [ ] Robot/host integration test covers CWRU replay through to viewer-visible health output

## Phase 7 — Virtual demo & polish (weeks 14–16)
- [ ] README: block diagram, renders, plots, results
- [ ] Demo video: CWRU replay in Renode → fault detected → PC viewer alert
- [ ] LinkedIn post + add to CV
- [ ] Optional follow-up: run the hardware-ready firmware on a NUCLEO-G474RE

---

## Decisions log
Record each important choice in `docs/decisions/NNN-title.md`: problem, options, choice, reason.
