# Decision 004: scale-invariant features and per-motor anomaly detection

## Problem

Decision 003 showed strong transfer across held-out loads but weak transfer to an unseen 0.021-inch fault size: recording balanced accuracy was 0.750. The absolute classifier includes RMS and absolute envelope-band energies, so differences in defect severity or sensor amplitude may change its features. MotorSense's primary output should answer whether this motor has moved away from its own healthy behavior; identifying the fault type is a useful secondary output.

## Comparison design

The comparison reuses the same recordings, segmenting, random seeds, and held-out splits from `ml/notebooks/02_classifier.ipynb` and Decision 003.

- **Absolute classifier reference:** RMS, kurtosis, crest factor, and log energies around bearing fault orders. Model selection occurs inside grouped training folds among dummy, logistic regression, and random forest.
- **Scale-invariant classifier:** kurtosis, crest factor, fault-order envelope energy ratios (fault-band energy divided by total envelope energy up to 500 Hz), and fundamental envelope peak-to-neighbor amplitude ratios in dB. It uses the same model selection and the same held-out recordings as the reference.
- **Per-motor anomaly detector:** robustly standardizes these scale-invariant features using the median and median absolute deviation of healthy training windows, then reports their distance from that healthy center. Its threshold is the 95th percentile of training-only leave-one-recording-out healthy scores. It does not use fault labels to fit the baseline or set the threshold.
- **Load holdout:** four outer folds, each holding out one complete 0–3 HP load. Every recording is held out once; no recording's windows cross a split.
- **Fault-size holdout:** train on normal and 0.007/0.014-inch faults; test on the same 12 recordings (120 windows) of 0.021-inch faults used in Decision 003. Since the test contains only faults, anomaly detection reports sensitivity only, not specificity or balanced accuracy.

The scale-invariance unit test multiplies a synthetic modulated carrier by a constant gain and verifies the ratios and peak-to-neighbor features stay unchanged. The kurtosis and crest factor are also scale-invariant by definition.

## Results

### Leave-one-load-out

Balanced accuracy is shown at both the segment and recording levels. Recording results aggregate window probabilities for classification and median anomaly scores for detection.

| Held-out load | Absolute classifier window / recording | Scale-invariant classifier window / recording |
|---:|---:|---:|
| 0 HP | 0.992 / 1.000 | 0.600 / 0.583 |
| 1 HP | 1.000 / 1.000 | 0.725 / 0.833 |
| 2 HP | 0.992 / 1.000 | 0.792 / 0.833 |
| 3 HP | 0.975 / 1.000 | 0.658 / 0.833 |
| **All folds** | **0.990 / 1.000** | **0.694 / 0.771** |

The scale-invariant classifier is substantially worse on this four-class task. Removing RMS and absolute spectral levels discards class-separating information in this dataset; the ratios as currently defined do not recover it.

The healthy-baseline detector reached **0.857 window balanced accuracy** and **0.861 recording balanced accuracy** across the same load folds. With its reserved-window protocol, it flagged 266/360 fault windows (73.9% sensitivity) and 1/40 held-out-load healthy windows (2.5% false alarms; 97.5% specificity). At the recording level it flagged 26/36 fault recordings and all 4/4 healthy recordings.

To estimate false alarms without fitting or calibrating on the evaluated healthy samples, each training healthy recording contributes even-indexed windows to the baseline and threshold calibration. Its odd-indexed windows are reserved for false-alarm evaluation. The full healthy recording at the held-out load is also evaluated. Across the four folds this gives 40 distinct selected healthy windows; 1 was flagged (2.5%). The 20 reserved within-recording windows are each scored in three different fold contexts (60 decisions total); none was flagged in any context (0/20 unique windows ever flagged). These are overlapping CWRU windows from only four normal recordings, so the point estimate is coarse and not a product false-alarm guarantee.

### Held-out 0.021-inch fault size

| Method | Window accuracy / balanced accuracy | Recording accuracy / balanced accuracy |
|---|---:|---:|
| Absolute classifier (random forest) | 0.558 / 0.558 | 0.750 / 0.750 |
| Scale-invariant classifier (logistic regression) | 0.425 / 0.425 | 0.417 / 0.417 |
| Healthy-baseline anomaly detector | 0.875 sensitivity | 0.917 sensitivity |

The absolute classifier correctly identified 9/12 fault recordings; the scale-invariant classifier correctly identified 5/12. With the reserved-window healthy-baseline protocol, the detector flagged 11/12 fault recordings. Because there are no healthy examples in this size holdout, the detector's false-alarm rate on this split is unknown.

## Phase 1 firmware spec freeze

Freeze this as the first MCU implementation target. It is a compact anomaly scorer; fault-type classification remains an offline/secondary diagnostic for now.

| Item | Frozen target |
|---|---|
| Input | 12 kHz vibration, shaft frequency in Hz supplied by configuration or a speed source |
| Window | 6,000 samples (0.5 s), non-overlapping, Hann window for envelope spectrum |
| Carrier band | 2.5–3.5 kHz bandpass before envelope extraction |
| Bearing orders | BPFI 5.4152, BPFO 3.5848, BSF 4.7135, FTF 0.39828 times shaft frequency |
| Feature count | 10: kurtosis, crest factor; four first-three-harmonic band-energy / total-envelope-energy ratios; four fundamental peak-to-neighbor amplitude ratios in dB |
| Spectrum bands | ±2 Hz around each of the first three fault harmonics; total-energy denominator from 0–500 Hz; neighbor bands ±2 Hz around offsets of ±6 Hz |
| MCU transform target | 8,192-point Q15 CMSIS-DSP real FFT, zero-padding each 6,000-sample window; 1.465 Hz bin spacing. The Python reference uses a 6,000-point float FFT (2 Hz bins), so Q15 parity and baseline recalibration are required before deployment. |
| Model | Per-motor robust healthy baseline: 10 feature medians + 10 MAD-derived scales; score `sqrt(mean(((x - median) / scale)^2))`; flag when score exceeds the 95th-percentile healthy calibration threshold |
| Model storage / scoring | 21 float32 values (84 bytes) for centers, scales, and threshold; O(10) feature normalizations and square-sum operations per window |

Feature-vector order is fixed as: `kurtosis`, `crest_factor`, `bpfi_energy_ratio`, `bpfo_energy_ratio`, `bsf_energy_ratio`, `ftf_energy_ratio`, `bpfi_peak_neighbor_db`, `bpfo_peak_neighbor_db`, `bsf_peak_neighbor_db`, `ftf_peak_neighbor_db`. The MAD scale is `max(1.4826 * MAD, 1e-8 * max(1, abs(median)))` for each feature. The total-energy denominator sums bins above DC through 500 Hz; each ratio numerator sums the first three harmonic bands.

The Python reference uses a Hilbert analytic envelope plus an envelope spectrum. To bound MCU memory, the selected port target uses a 63-tap Q15 quadrature FIR for the Hilbert component and one Q15 envelope-spectrum RFFT per window. That FIR choice must be checked against the Python envelope on identical inputs. The 95th-percentile threshold and per-motor centers/scales should be generated from healthy commissioning data and stored with device configuration; commissioning duration and drift handling remain open engineering parameters.

The fault-type secondary model remains the Decision 003 absolute-feature random forest baseline: RMS, kurtosis, crest factor, and four log envelope energies (7 features). It is not part of this first frozen MCU anomaly path because its 0.021-inch fault-size recording balanced accuracy was 0.750 and it cannot flag fault types absent from training.

### FFT implementation comparison

The float and fixed-point candidates are not interchangeable one-for-one: CMSIS-DSP's fast float32 real FFT supports sizes through 4096; the Q15 real FFT supports 8192. The Q15 transform scales its output by a size-dependent amount to avoid overflow (13 bits for 8192), which cancels in the energy and peak ratios but still needs quantization checks. Buffer figures below are transform source plus destination only; they omit the acquisition staging, envelope/filter state, model state, and stack.

| FFT path | CMSIS-DSP support on Cortex-M | Input span at 12 kHz | Bin spacing | FFT source + destination RAM | Main tradeoff |
|---|---|---:|---:|---:|---|
| float32, 4096 RFFT | Supported (`arm_rfft_fast_f32`) | 4,096 samples = 0.341 s | 2.93 Hz | 32 KiB (N float source + N float destination) | M4F FPU and simpler scaling; shorter observation and coarse bins make the current ±2 Hz feature bands unreliable. |
| Q15, 4096 RFFT | Supported (`arm_rfft_q15`) | 4,096 samples = 0.341 s | 2.93 Hz | 24.0 KiB (N Q15 source + (2N+2) Q15 destination) | Smallest footprint, but same lost span and frequency-bin limitation. |
| float32, 8192 RFFT | Not supported by CMSIS-DSP fast float RFFT | 6,000 samples fit with zero padding | 1.465 Hz | Not applicable | Would need a custom/complex path and extra workspace; reject for this spec. |
| **Q15, 8192 RFFT** | **Supported (`arm_rfft_q15`)** | **6,000 samples = 0.5 s, padded by 2,192 zeros** | **1.465 Hz** | **48.0 KiB (8,192 Q15 source + 16,386 Q15 destination values)** | **Selected. Preserves the whole reference window and gives a denser grid for evaluating the current fault bands; requires Q15 scaling/quantization parity tests.** |

At 12 kHz, a 4096-point transform only covers 0.341 seconds. Using the full half-second window would require another design (for example, a new 8 kHz envelope-rate path), with new filtering, features, and training. The 8192-point zero-padded FFT has 1.465 Hz *bin spacing*; zero padding does not create new information beyond the 0.5-second observation. For equal lengths, FFT operation count grows approximately with N log2(N), so 8192 costs about 2.17× a 4096 transform. Q15 can use Cortex-M DSP instructions, while the STM32G474 also has a single-precision FPU; actual Q15-vs-float cycle speed is not assumed and must be measured.

### Initial resource budget

The MCU target is STM32G474xE (512 KiB Flash, 128 KiB SRAM in the family datasheet). The figures are a planning budget, not a linker-map or board measurement. Q15 RFFT uses an in-place-modified source and a full-spectrum destination; CMSIS-DSP lists no separate RFFT scratch buffer for the Cortex-M scalar/DSP path. The transform tables and Hann coefficients reside in Flash.

| SRAM item | Budget | Basis |
|---|---:|---|
| Q15 FFT source / capture window | 16.0 KiB | 8,192 `q15_t`; same buffer receives 6,000 samples then zero padding |
| Q15 RFFT output | 32.0 KiB | (2N+2) `q15_t` for the CMSIS-DSP Cortex-M output format |
| DMA staging | 0.5 KiB | 256 Q15 samples; source buffer is filled incrementally |
| Bandpass + quadrature FIR state | 1.0 KiB | Delay state, coefficients copied to RAM only if needed, temporary envelope values; reuse source after demodulation |
| Feature and score working state | 0.25 KiB | 10 features plus float32 baseline parameters/temporary score |
| Main/interrupt stack allocation | 8.0 KiB | Require measured high-water ≤6.0 KiB, retaining ≥2.0 KiB stack margin |
| Other application/driver `.data` + `.bss` allowance | 32.0 KiB | Planning allowance for sampling, CAN, UART, and state; verify from map |
| **Estimated allocated total** | **89.8 KiB** | Leaves about 38.2 KiB from 128 KiB |
| Reserved SRAM headroom | 32.0 KiB | 25% of total SRAM; current estimate leaves about 6.2 KiB beyond this reserve |

The chosen Q15 FFT constants are approximately 51.9 KiB in Flash before code: two 8,192-entry Q15 real-FFT coefficient tables (32 KiB), the 4,096-point Q15 complex twiddle table (12 KiB), and its 4,032-entry uint16 bit-reversal table (7.9 KiB). A 6,000-entry Q15 Hann table adds about 11.7 KiB; 63 Hilbert coefficients, filter coefficients, and the 84-byte anomaly baseline add under 0.3 KiB. Thus the planned constant-data total is about **63.8 KiB**, plus retained CMSIS-DSP routine and application code. Link only the selected FFT tables/routines and verify actual `.text`/`.rodata` in the linker map; the exact STM32 order code must be confirmed before claiming the 512 KiB maximum.

| Per-window CPU budget | Initial target |
|---|---:|
| Q15 63-tap quadrature FIR | ≤378,000 MACs (6,000 × 63, unoptimized upper count) |
| 2.5–3.5 kHz bandpass | About 120,000 multiplies for four biquad sections × 6,000 samples × 5 multiplies; verify section realization |
| Envelope spectrum | One 8,192-point Q15 real FFT plus windowing and ≤~350 bins of energy reduction (0–500 Hz) |
| Feature and anomaly score | 10 features; 10 robust normalizations, square/sum, and one square root |
| End-to-end budget | Finish DSP ≤17 million cycles (100 ms at 170 MHz, 20% of a 0.5 s window); no cycle measurement exists yet |

Use the 100 ms target as an acceptance ceiling, not a measured result. The Q15 transform output scale and fixed-point filter headroom must be handled explicitly. The first firmware validation should compare all 10 feature values and anomaly decisions against Python, measure DWT cycles, inspect linker SRAM/Flash totals, and confirm stack high-water while CAN and sampling interrupts run. If Q15 quantization changes decisions, the fallback is not silently assumed: widen/revisit feature bands or train/calibrate against the selected fixed-point implementation before deployment.

## Decision

Use **per-motor healthy-baseline anomaly detection as the primary product output** and fault-type classification as a secondary diagnostic. Keep the absolute-feature classifier as the current fault-type reference. Do not replace it with this scale-invariant feature classifier: it lowered held-out-size and held-out-load fault-type accuracy. The anomaly result is encouraging for detection, but it is an initial research result, not validated product performance.

A real installation must collect a representative healthy baseline for that particular motor, across its operating range. This experiment instead uses the available healthy recordings from one CWRU motor as training baselines. Before deployment claims, validate on multiple motors, sensor remounts, operating conditions, and held-out healthy periods; tune the alarm threshold against false-alarm costs and baseline drift.

## Concepts to understand

- A ratio such as fault-band energy / total envelope energy is unchanged by multiplying the whole signal by a constant, while an absolute energy changes by the square of that constant.
- Kurtosis and crest factor describe signal shape relative to its scale. Peak-to-neighbor dB compares a fault-order peak to its local spectral floor.
- An anomaly detector learns a description of normal data and asks “does this look unusual?” It can flag an unseen fault type, but by itself cannot name the fault.
- Median absolute deviation gives a robust feature scale. Leave-one-recording-out calibration prevents the threshold calibration score for a healthy recording from being computed by a baseline that already fitted that recording.
- Window-level measurements from one file are correlated. Recording-level results are the more meaningful independent-unit comparison here.

## Firmware references

- [CMSIS-DSP float32 real FFT API and supported sizes](https://arm-software.github.io/CMSIS-DSP/main/group__RealFFTF32.html)
- [CMSIS-DSP Q15 real FFT API, supported sizes, and output scaling](https://arm-software.github.io/CMSIS-DSP/latest/group__RealFFTQ15.html)
- [CMSIS-DSP transform buffer sizes](https://arm-software.github.io/CMSIS-DSP/main/transformbuffers.html)
- [CMSIS-DSP FFT coefficient tables](https://arm-software.github.io/CMSIS-DSP/main/group__RealFFT__Table.html)
- [STM32G474 datasheet](https://www.st.com/resource/en/datasheet/stm32g474ve.pdf)

## Reproduction

Run the notebook `ml/notebooks/02_classifier.ipynb` with the ignored CWRU files in `ml/data`, then run `pytest` and `pre-commit run --all-files`.
