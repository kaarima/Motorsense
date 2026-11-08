"""Time-domain vibration features used for motor health monitoring."""

import numpy as np

from motorsense_ml.envelope import envelope_spectrum

DRIVE_END_FAULT_ORDERS = {
    "bpfi": 5.4152,
    "bpfo": 3.5848,
    "bsf": 4.7135,
    "ftf": 0.39828,
}


def rms(x: np.ndarray) -> float:
    """Root mean square: overall vibration energy."""
    x = np.asarray(x, dtype=float)
    return float(np.sqrt(np.mean(x**2)))


def peak(x: np.ndarray) -> float:
    """Largest absolute amplitude."""
    return float(np.max(np.abs(np.asarray(x, dtype=float))))


def crest_factor(x: np.ndarray) -> float:
    """Peak / RMS: grows with impacts (e.g. early bearing damage)."""
    r = rms(x)
    return peak(x) / r if r > 0 else 0.0


def kurtosis(x: np.ndarray) -> float:
    """Pearson kurtosis (normal signal ~3): sensitive to impulsive faults."""
    x = np.asarray(x, dtype=float)
    centered = x - x.mean()
    var = np.mean(centered**2)
    if var == 0:
        return 0.0
    return float(np.mean(centered**4) / var**2)


def envelope_band_energies(
    x: np.ndarray,
    fs: int,
    shaft_hz: float,
    carrier_band_hz: tuple[float, float] = (2_500, 3_500),
    bandwidth_hz: float = 2.0,
    harmonics: int = 3,
) -> np.ndarray:
    """Return log envelope-spectrum energy near drive-end bearing defect orders.

    Values are ordered as BPFI, BPFO, BSF, and FTF. For each order, the
    squared single-sided envelope-spectrum magnitudes are summed around its
    first ``harmonics`` multiples and returned on a log10 scale.
    """
    if not np.isfinite(shaft_hz) or shaft_hz <= 0:
        raise ValueError("shaft_hz must be positive and finite")
    if not np.isfinite(bandwidth_hz) or bandwidth_hz <= 0:
        raise ValueError("bandwidth_hz must be positive and finite")
    if not isinstance(harmonics, int | np.integer) or harmonics < 1:
        raise ValueError("harmonics must be a positive integer")

    frequencies, magnitudes = envelope_spectrum(x, fs, carrier_band_hz)
    energies = []
    floor = np.finfo(float).tiny
    for order in DRIVE_END_FAULT_ORDERS.values():
        mask = np.zeros(frequencies.shape, dtype=bool)
        for harmonic in range(1, harmonics + 1):
            center_hz = order * shaft_hz * harmonic
            mask |= np.abs(frequencies - center_hz) <= bandwidth_hz
        energy = np.sum(magnitudes[mask] ** 2)
        energies.append(np.log10(max(float(energy), floor)))
    return np.asarray(energies)
