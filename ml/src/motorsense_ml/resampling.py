"""Signal resampling helpers."""

from math import gcd

import numpy as np
from scipy.signal import resample_poly


def resample_signal(signal: np.ndarray, source_fs: int, target_fs: int) -> np.ndarray:
    """Resample a one-dimensional signal with polyphase anti-alias filtering."""
    if not isinstance(source_fs, int | np.integer) or not isinstance(target_fs, int | np.integer):
        raise TypeError("source_fs and target_fs must be integers")
    if source_fs <= 0 or target_fs <= 0:
        raise ValueError("source_fs and target_fs must be positive")

    samples = np.asarray(signal, dtype=float)
    if samples.ndim != 1 or samples.size == 0:
        raise ValueError("signal must be a non-empty one-dimensional array")

    if source_fs == target_fs:
        return samples.copy()

    divisor = gcd(source_fs, target_fs)
    up = target_fs // divisor
    down = source_fs // divisor
    return resample_poly(samples, up=up, down=down)
