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
| MCU transform target | 8,192-point float32 CMSIS-DSP real FFT, zero-padding each 6,000-sample window; 1.465 Hz bin spacing. The Python reference uses a 6,000-point FFT (2 Hz bins), so firmware parity and baseline recalibration are required before deployment. |
| Model | Per-motor robust healthy baseline: 10 feature medians + 10 MAD-derived scales; score `sqrt(mean(((x - median) / scale)^2))`; flag when score exceeds the 95th-percentile healthy calibration threshold |
| Model storage / scoring | 21 float32 values (84 bytes) for centers, scales, and threshold; O(10) feature normalizations and square-sum operations per window |

Feature-vector order is fixed as: `kurtosis`, `crest_factor`, `bpfi_energy_ratio`, `bpfo_energy_ratio`, `bsf_energy_ratio`, `ftf_energy_ratio`, `bpfi_peak_neighbor_db`, `bpfo_peak_neighbor_db`, `bsf_peak_neighbor_db`, `ftf_peak_neighbor_db`. The MAD scale is `max(1.4826 * MAD, 1e-8 * max(1, abs(median)))` for each feature. The total-energy denominator sums bins above DC through 500 Hz; each ratio numerator sums the first three harmonic bands.

The reference analytic envelope uses a Hilbert transform plus an envelope spectrum. The MCU estimate is one forward/inverse analytic-signal transform pair plus one envelope-spectrum real FFT per window, each targeting 8,192 points. The STM32 implementation must map those steps to CMSIS-DSP, preserve the 2.5–3.5 kHz filter and feature definitions, and compare Python/C feature values on identical inputs. An 8,192-point transform size is supported by CMSIS-DSP's real-FFT API; the STM32G474 family has 128 KB SRAM. RAM use, cycles per half-second window, and detection latency still need measurement on the board/target. The 95th-percentile threshold and per-motor centers/scales should be generated from healthy commissioning data and stored with the device configuration; commissioning duration and drift handling remain open engineering parameters.

The fault-type secondary model remains the Decision 003 absolute-feature random forest baseline: RMS, kurtosis, crest factor, and four log envelope energies (7 features). It is not part of this first frozen MCU anomaly path because its 0.021-inch fault-size recording balanced accuracy was 0.750 and it cannot flag fault types absent from training.

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

- [CMSIS-DSP real FFT API and supported sizes](https://arm-software.github.io/CMSIS-DSP/v1.14.2/group__RealFFT.html)
- [STM32G474 datasheet](https://www.st.com/resource/en/datasheet/stm32g474ve.pdf)

## Reproduction

Run the notebook `ml/notebooks/02_classifier.ipynb` with the ignored CWRU files in `ml/data`, then run `pytest` and `pre-commit run --all-files`.
