"""Helpers for making fixed-length, recording-aware vibration segments."""

import numpy as np


def segment_signal(
    signal: np.ndarray,
    segment_samples: int,
    max_segments: int | None = None,
) -> np.ndarray:
    """Split one recording into equal, non-overlapping segments.

    Any trailing partial segment is dropped. When ``max_segments`` is given,
    a deterministic, evenly spaced subset is selected from the recording.
    Keeping this operation on one recording at a time makes it straightforward
    to assign all resulting segments to the same train or test partition.
    """
    samples = np.asarray(signal, dtype=float)
    if samples.ndim != 1 or samples.size == 0:
        raise ValueError("signal must be a non-empty one-dimensional array")
    if not isinstance(segment_samples, int | np.integer) or segment_samples <= 0:
        raise ValueError("segment_samples must be a positive integer")
    if max_segments is not None and (
        not isinstance(max_segments, int | np.integer) or max_segments <= 0
    ):
        raise ValueError("max_segments must be a positive integer")

    count = samples.size // segment_samples
    if count == 0:
        raise ValueError("signal must contain at least one complete segment")
    starts = np.arange(count) * segment_samples
    if max_segments is not None and count > max_segments:
        selected = np.linspace(0, count - 1, max_segments, dtype=int)
        starts = starts[selected]
    return np.stack([samples[start : start + segment_samples] for start in starts])
