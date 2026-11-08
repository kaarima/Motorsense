# Decision 003: CWRU classifier with a load-held-out test set

## Problem

Segments from the same recording are highly related. A random segment-level
split can put nearly identical vibration into both training and test sets and
make a classifier look better than it is. We need a first baseline that tests
transfer to a motor load not used for fitting.

## Data

- CWRU drive-end normal baseline: files 97–100, loads 0–3 HP.
- 12 kHz drive-end faults: inner race, ball, and centered outer race at
  0.007, 0.014, and 0.021 inch, each at loads 0–3 HP.
- The corresponding fault file IDs are listed on CWRU's official 12 kHz
  drive-end data page.
- We use the `X<file-id>_DE_time` signal and select the key that matches the
  filename. This matters for `99.mat`, which also contains an older
  `X098_DE_time` variable.
- The sample rate of `97.mat` was verified in Decision 001. CWRU's pages do
  not list a sample rate beside each normal file. We treat `98.mat`–`100.mat`
  as the same 48 kHz normal-baseline collection; their sample lengths are
  consistent with roughly 10 seconds at 48 kHz. This is a collection-level
  assumption, not independent per-file metadata. All normal recordings are
  resampled to 12 kHz before segmentation.

## Features and split

- Each file is divided into non-overlapping 0.5 second segments (6,000
  samples at 12 kHz). Ten evenly spaced segments are retained per recording.
- Features are RMS, Pearson kurtosis, crest factor, and log envelope-spectrum
  energy near the first three harmonics of BPFI, BPFO, BSF, and FTF. Envelope
  processing uses the 2.5–3.5 kHz carrier band and a ±2 Hz band around each
  predicted defect harmonic.
- The defect orders use CWRU's drive-end SKF 6205 bearing values: BPFI 5.4152,
  BPFO 3.5848, BSF 4.7135, and FTF 0.39828 times shaft speed.
- Loads 0–2 HP form training data (30 recordings, 300 segments). All 3 HP
  recordings are held out for final evaluation (10 recordings, 100 segments).
  The split is assigned by recording load, and the train/test recording ID
  sets are asserted to be disjoint.
- A stratified, three-fold cross-validation on the training pool also groups
  by recording. It compares a prior-only dummy, balanced logistic regression,
  and a class-balanced random forest. The better non-dummy model by mean
  cross-validation balanced accuracy is selected before evaluating 3 HP.

## Results

Grouped cross-validation balanced accuracy:

| Model | Fold scores | Mean |
|---|---|---:|
| Prior-only dummy | 0.250, 0.250, 0.250 | 0.250 |
| Logistic regression | 1.000, 0.825, 0.958 | 0.928 |
| Random forest | 1.000, 0.983, 1.000 | 0.994 |

The random forest was selected using training-only cross-validation. Its
recording-level confusion matrix on the untouched 3 HP files is:

| Actual \\ Predicted | Normal | Inner race | Ball | Outer race |
|---|---:|---:|---:|---:|
| Normal | 1 | 0 | 0 | 0 |
| Inner race | 0 | 3 | 0 | 0 |
| Ball | 0 | 0 | 3 | 0 |
| Outer race | 0 | 0 | 0 | 3 |

Recording-level balanced accuracy was 1.000 (10 of 10 recordings correct).
Segment probabilities are averaged within each recording before scoring, so
the 100 correlated test windows do not count as 100 independent test cases.

## Decision and limits

Keep this as a first feature-based baseline. It shows that the selected
features separate these CWRU fault classes across the chosen load split, but
it is not evidence of broad field performance. There is only one held-out
normal recording, the same fault sizes appear in training at other loads, and
all recordings come from one test motor and setup. The normal-file sampling
rate assumption should be revisited if authoritative per-file metadata is
found. Follow-up validation should include another motor, sensor mounting, or
held-out fault sizes before making performance claims.

## Sources

- [CWRU normal baseline data](https://engineering.case.edu/bearingdatacenter/normal-baseline-data)
- [CWRU 12 kHz drive-end fault data](https://engineering.case.edu/bearingdatacenter/12k-drive-end-bearing-fault-data)
- [CWRU apparatus and procedures](https://engineering.case.edu/bearingdatacenter/apparatus-and-procedures) (collection sample rates)
- [CWRU bearing information](https://engineering.case.edu/bearingdatacenter/bearing-information) (bearing geometry and defect orders)
- [Decision 001: CWRU 97.mat sample rate](001-cwru-sampling-rate.md)
