"""Envelope demodulation tools for bearing vibration signals."""

import numpy as np
from scipy.signal import butter, hilbert, sosfiltfilt


def _validate_signal(signal: np.ndarray, fs: int) -> np.ndarray:
    if not isinstance(fs, int | np.integer) or fs <= 0:
        raise ValueError("fs must be a positive integer")
    samples = np.asarray(signal, dtype=float)
    if samples.ndim != 1 or samples.size == 0:
        raise ValueError("signal must be a non-empty one-dimensional array")
    return samples


def envelope(
    signal: np.ndarray,
    fs: int,
    band_hz: tuple[float, float],
    order: int = 4,
) -> np.ndarray:
    """Bandpass a signal and return its Hilbert amplitude envelope."""
    samples = _validate_signal(signal, fs)
    if len(band_hz) != 2:
        raise ValueError("band_hz must contain low and high cutoff frequencies")
    low_hz, high_hz = band_hz
    if not 0 < low_hz < high_hz < fs / 2:
        raise ValueError("band_hz must satisfy 0 < low < high < Nyquist")
    if not isinstance(order, int | np.integer) or order < 1:
        raise ValueError("order must be a positive integer")

    sos = butter(order, band_hz, btype="bandpass", fs=fs, output="sos")
    filtered = sosfiltfilt(sos, samples)
    return np.abs(hilbert(filtered))


def envelope_spectrum(
    signal: np.ndarray,
    fs: int,
    band_hz: tuple[float, float],
    order: int = 4,
) -> tuple[np.ndarray, np.ndarray]:
    """Return frequency and single-sided amplitude spectrum of a band envelope."""
    amplitude_envelope = envelope(signal, fs, band_hz, order)
    window = np.hanning(amplitude_envelope.size)
    centered = amplitude_envelope - amplitude_envelope.mean()
    magnitude = np.abs(np.fft.rfft(centered * window))
    magnitude *= 2 / window.sum()
    magnitude[0] *= 0.5
    if amplitude_envelope.size % 2 == 0:
        magnitude[-1] *= 0.5
    frequencies = np.fft.rfftfreq(amplitude_envelope.size, d=1 / fs)
    return frequencies, magnitude
