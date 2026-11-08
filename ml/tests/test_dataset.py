import numpy as np
import pytest

from motorsense_ml.dataset import segment_signal


def test_segment_signal_returns_non_overlapping_fixed_size_chunks():
    signal = np.arange(23)

    segments = segment_signal(signal, segment_samples=5)

    np.testing.assert_array_equal(
        segments,
        [[0, 1, 2, 3, 4], [5, 6, 7, 8, 9], [10, 11, 12, 13, 14], [15, 16, 17, 18, 19]],
    )


def test_segment_signal_selects_evenly_spaced_segments_deterministically():
    segments = segment_signal(np.arange(50), segment_samples=5, max_segments=3)

    np.testing.assert_array_equal(segments[:, 0], [0, 20, 45])


@pytest.mark.parametrize(
    ("signal", "segment_samples", "max_segments"),
    [([], 5, None), ([1, 2], 5, None), ([1, 2], 0, None), ([1, 2], 1, 0)],
)
def test_segment_signal_rejects_invalid_input(signal, segment_samples, max_segments):
    with pytest.raises(ValueError):
        segment_signal(signal, segment_samples, max_segments)
