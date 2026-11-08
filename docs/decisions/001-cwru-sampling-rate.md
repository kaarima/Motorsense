# Decision 001: CWRU 97.mat sample rate

## Problem

The `97.mat` normal drive-end recording does not contain a sample-rate field.
Its strongest low-frequency line at about 0.0075 cycles/sample is ambiguous:
it could be the third shaft harmonic at 12 kHz or the twelfth at 48 kHz.

## Evidence

- CWRU lists `105.mat` in its 12 kHz drive-end fault table as the 0 HP,
  0.007 inch inner-race case, with an approximate motor speed of 1797 rpm.
- CWRU's normal-baseline table lists `97.mat` as the 0 HP baseline at about
  1797 rpm, but does not identify its sample rate per file.
- The MATLAB `RPM` variables report 1796 rpm for `97.mat` and 1797 rpm for
  `105.mat`.
- We calculated windowed spectra from 65,536 samples and detected independent
  local peaks with at least 6 dB prominence. On the common cycles/sample axis:

  | Recording and shaft order | Peak (cycles/sample) | Interpretation |
  |---|---:|---|
  | 97.mat 1x | 0.000626 | 48 kHz candidate fundamental: expected 0.000624 |
  | 97.mat 4x | 0.002502 | Near 105.mat 1x |
  | 97.mat 8x | 0.005005 | Near 105.mat 2x |
  | 97.mat 12x | 0.007492 | Near 105.mat 3x |
  | 105.mat 1x | 0.002487 | 12 kHz reference fundamental: expected 0.002496 |
  | 105.mat 2x | 0.004990 | Expected 0.004992 |
  | 105.mat 3x | 0.007477 | Expected 0.007487 |

  The `97.mat` 1x line is about one quarter of the `105.mat` 1x position.
  The corresponding 97.mat 4x, 8x, and 12x lines align with the 105.mat 1x,
  2x, and 3x lines. This is the expected relationship if 97.mat was sampled
  four times faster.

## Decision

Treat `97.mat` as a 48 kHz drive-end recording and resample it to 12 kHz before
comparing it with `105.mat` in time-domain analyses. The notebook uses
polyphase resampling, which applies an anti-aliasing filter before reducing
the rate by four.

The per-file rate is inferred from the harmonic comparison because CWRU's
normal-baseline table does not state it directly. Revisit if authoritative
per-file metadata becomes available or future analysis contradicts this
result.

## Why

For a shaft running at the same speed, a physical frequency appears at
one-quarter as many cycles/sample when the sample rate is four times higher.
Comparing the first shaft harmonics resolves the ambiguity left by the large
0.0075 cycles/sample peak, which can represent either 3x at 12 kHz or 12x at
48 kHz.

## Sources

- [CWRU normal baseline data](https://engineering.case.edu/bearingdatacenter/normal-baseline-data)
- [CWRU 12 kHz drive-end bearing fault data](https://engineering.case.edu/bearingdatacenter/12k-drive-end-bearing-fault-data)
- [CWRU download notes](https://engineering.case.edu/bearingdatacenter/download-data-file)
