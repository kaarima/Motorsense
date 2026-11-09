# Decision 002: CWRU inner-race envelope analysis

## Problem

An inner-race defect creates repeated impacts, but those impacts excite high-frequency structural vibration. Inspecting the raw spectrum alone can hide the lower-frequency repetition rate.

## Method

- Resample the 48 kHz `97.mat` normal recording to 12 kHz before comparing it with `105.mat`.
- Bandpass both drive-end signals from 2.5 to 3.5 kHz, then calculate the Hilbert amplitude envelope.
- Remove the envelope mean, apply a Hann window, and calculate its single-sided amplitude spectrum.
- CWRU lists the drive-end 6205 inner-race defect frequency as 5.4152 times shaft speed. At 1797 rpm, the predicted BPFI is approximately 162.2 Hz.

## Finding

In the first 60,000 samples at 12 kHz, the fault envelope spectrum has a peak near the predicted BPFI. The maximum spectrum amplitude within ±2 Hz of BPFI is about 131 times larger in `105.mat` than in the resampled normal segment. The fault spectrum also has visible peaks near BPFI harmonics.

## Decision

Use a 2.5–3.5 kHz carrier band as the initial envelope-analysis band for this CWRU comparison. Keep the band configurable: this result is specific to these recordings and should not be treated as a universal sensor setting.

Implement envelope demodulation with a Butterworth bandpass, zero-phase filtering, and the Hilbert transform. The reusable function returns the envelope; a second function returns its spectrum. Tests use a synthetic amplitude-modulated carrier so the expected modulation frequency is known.

## Concepts to understand

- The bandpass isolates a high-frequency carrier region that responds to repeated bearing impacts.
- The Hilbert transform forms an analytic signal; its magnitude is the amplitude envelope.
- A periodic impact train modulates the carrier, so the envelope spectrum shows the repetition frequency and its harmonics.
- The window reduces FFT leakage, and the predicted BPFI provides a physics-based place to inspect the spectrum.

## Sources

- [CWRU bearing information](https://engineering.case.edu/bearingdatacenter/bearing-information) lists the drive-end 6205 dimensions and defect-frequency orders.
- [CWRU 12 kHz drive-end data](https://engineering.case.edu/bearingdatacenter/12k-drive-end-bearing-fault-data) lists the 0 HP inner-race case and its approximate speed.
