"""Time-domain vibration features used for motor health monitoring."""

import numpy as np


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
