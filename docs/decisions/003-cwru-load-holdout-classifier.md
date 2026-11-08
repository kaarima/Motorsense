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

## Expanded validation

The notebook now reports nested leave-one-load-out (LOLO) cross-validation.
Each outer fold holds out one complete load (0, 1, 2, or 3 HP). Within the
other three loads, three-fold stratified cross-validation groups by recording
and selects between the dummy, logistic-regression, and random-forest
pipelines. Each selected pipeline is fitted on the full outer training pool.
All 40 recordings appear in exactly one outer test fold; all 400 windows are
reported as window-level metrics, and the 40 recording-level scores average
window probabilities before classification.

| Held-out load | Selected model | Inner grouped CV balanced accuracy | Window accuracy | Window balanced accuracy | Recording accuracy / balanced accuracy |
|---:|---|---:|---:|---:|---:|
| 0 HP | Random forest | 0.989 | 0.990 | 0.992 | 1.000 / 1.000 |
| 1 HP | Random forest | 0.978 | 1.000 | 1.000 | 1.000 / 1.000 |
| 2 HP | Random forest | 0.975 | 0.990 | 0.992 | 1.000 / 1.000 |
| 3 HP | Random forest | 0.994 | 0.970 | 0.975 | 1.000 / 1.000 |
| **All four folds** | — | — | **0.988** | **0.990** | **1.000 / 1.000** |

The aggregate LOLO recording-level confusion matrix is unchanged from the
initial matrix above: one normal, three inner-race, three ball, and three
outer-race recordings were correctly classified at each held-out load.
Window-level accuracy is lower because some windows are misclassified even
though averaging their probabilities gives the correct recording label.

### Fault-size holdout

For a separate transfer test, training uses all normal recordings plus
0.007-inch and 0.014-inch faults at all loads. Testing uses only 0.021-inch
faults at all four loads. The split contains 28 training recordings (280
windows) and 12 held-out recordings (120 windows), with disjoint recording
IDs. Since normal recordings have no defect size, this test contains no
normal examples and measures classification among the three fault types,
not normal-versus-fault detection.

The inner grouped CV selected a random forest (balanced accuracy 0.981). On
the unseen 0.021-inch size, window accuracy and balanced accuracy were both
0.558; recording accuracy and balanced accuracy were both 0.750.

| Actual \\ Predicted | Normal | Inner race | Ball | Outer race |
|---|---:|---:|---:|---:|
| Normal | 0 | 0 | 0 | 0 |
| Inner race | 0 | 2 | 0 | 2 |
| Ball | 0 | 0 | 4 | 0 |
| Outer race | 0 | 0 | 1 | 3 |

The window-level confusion matrix for the same held-out size is:

| Actual \\ Predicted | Normal | Inner race | Ball | Outer race |
|---|---:|---:|---:|---:|
| Normal | 0 | 0 | 0 | 0 |
| Inner race | 0 | 9 | 0 | 31 |
| Ball | 0 | 0 | 39 | 1 |
| Outer race | 0 | 0 | 21 | 19 |

This size holdout is a useful warning: the model transfers well across these
loads, but does not yet reliably transfer to an unseen defect size. In
particular, inner-race and outer-race signatures overlap at 0.021 inch.

### Random-forest feature importance

The notebook fits a diagnostic random forest on the training recordings in
each LOLO fold and averages its impurity-based feature importances. Values
below are mean ± standard deviation across the four outer folds.

| Feature | Mean importance ± standard deviation |
|---|---:|
| RMS | 0.278 ± 0.011 |
| Log BPFI envelope energy | 0.235 ± 0.010 |
| Log BPFO envelope energy | 0.226 ± 0.011 |
| Log BSF envelope energy | 0.093 ± 0.012 |
| Log FTF envelope energy | 0.092 ± 0.005 |
| Kurtosis | 0.049 ± 0.002 |
| Crest factor | 0.026 ± 0.002 |

These values describe how the fitted trees use the features; they do not show
causation, and impurity importance can favor features with more possible split
points. The prominent RMS contribution also means amplitude/load variation
may be helping classification. Future checks should normalize amplitude or
add another motor before interpreting the envelope features as the main
signal.

## Decision and limits

Keep this as a first feature-based baseline. It shows that the selected
features separate these CWRU fault classes across held-out loads, but fault
size transfer is weaker and it is not evidence of broad field performance.
There is only one normal recording per load, the same fault sizes appear in
training for LOLO, and all recordings come from one test motor and setup. The
normal-file sampling-rate assumption should be revisited if authoritative
per-file metadata is found. Follow-up validation should include another
motor, sensor mounting, and fault sizes before making performance claims.

## Sources

- [CWRU normal baseline data](https://engineering.case.edu/bearingdatacenter/normal-baseline-data)
- [CWRU 12 kHz drive-end fault data](https://engineering.case.edu/bearingdatacenter/12k-drive-end-bearing-fault-data)
- [CWRU apparatus and procedures](https://engineering.case.edu/bearingdatacenter/apparatus-and-procedures) (collection sample rates)
- [CWRU bearing information](https://engineering.case.edu/bearingdatacenter/bearing-information) (bearing geometry and defect orders)
- [Decision 001: CWRU 97.mat sample rate](001-cwru-sampling-rate.md)
