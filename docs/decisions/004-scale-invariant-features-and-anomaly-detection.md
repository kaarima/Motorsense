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

The healthy-baseline detector reached **0.846 window balanced accuracy** and **0.861 recording balanced accuracy** across the same load folds. At the window level it correctly flagged 267/360 fault windows (74.2% sensitivity) and raised 2/40 false alarms on healthy windows (95.0% specificity). At the recording level it flagged 26/36 fault recordings and all 4/4 healthy recordings. The small number of independent healthy recordings makes the specificity estimate especially uncertain.

### Held-out 0.021-inch fault size

| Method | Window accuracy / balanced accuracy | Recording accuracy / balanced accuracy |
|---|---:|---:|
| Absolute classifier (random forest) | 0.558 / 0.558 | 0.750 / 0.750 |
| Scale-invariant classifier (logistic regression) | 0.425 / 0.425 | 0.417 / 0.417 |
| Healthy-baseline anomaly detector | 0.833 sensitivity | 0.833 sensitivity |

The absolute classifier correctly identified 9/12 fault recordings; the scale-invariant classifier correctly identified 5/12. The baseline detector flagged 10/12 fault recordings. Because there are no healthy examples in this size holdout, the detector's false-alarm rate on this split is unknown.

## Decision

Use **per-motor healthy-baseline anomaly detection as the primary product output** and fault-type classification as a secondary diagnostic. Keep the absolute-feature classifier as the current fault-type reference. Do not replace it with this scale-invariant feature classifier: it lowered held-out-size and held-out-load fault-type accuracy. The anomaly result is encouraging for detection, but it is an initial research result, not validated product performance.

A real installation must collect a representative healthy baseline for that particular motor, across its operating range. This experiment instead uses the available healthy recordings from one CWRU motor as training baselines. Before deployment claims, validate on multiple motors, sensor remounts, operating conditions, and held-out healthy periods; tune the alarm threshold against false-alarm costs and baseline drift.

## Concepts to understand

- A ratio such as fault-band energy / total envelope energy is unchanged by multiplying the whole signal by a constant, while an absolute energy changes by the square of that constant.
- Kurtosis and crest factor describe signal shape relative to its scale. Peak-to-neighbor dB compares a fault-order peak to its local spectral floor.
- An anomaly detector learns a description of normal data and asks “does this look unusual?” It can flag an unseen fault type, but by itself cannot name the fault.
- Median absolute deviation gives a robust feature scale. Leave-one-recording-out calibration prevents the threshold calibration score for a healthy recording from being computed by a baseline that already fitted that recording.
- Window-level measurements from one file are correlated. Recording-level results are the more meaningful independent-unit comparison here.

## Reproduction

Run the notebook `ml/notebooks/02_classifier.ipynb` with the ignored CWRU files in `ml/data`, then run `pytest` and `pre-commit run --all-files`.
