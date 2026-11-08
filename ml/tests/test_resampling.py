import numpy as np
import pytest

from motorsense_ml.resampling import resample_signal


def test_downsampling_preserves_duration_and_tone_frequency():
    source_fs = 48_000
    target_fs = 12_000
    tone_hz = 1_200
    time = np.arange(source_fs) / source_fs
    signal = np.sin(2 * np.pi * tone_hz * time)

    resampled = resample_signal(signal, source_fs, target_fs)
    frequencies = np.fft.rfftfreq(resampled.size, d=1 / target_fs)
    spectrum = np.abs(np.fft.rfft(resampled))

    assert resampled.size == target_fs
    assert frequencies[np.argmax(spectrum[1:]) + 1] == pytest.approx(tone_hz)


def test_downsampling_attenuates_frequencies_above_new_nyquist():
    source_fs = 48_000
    target_fs = 12_000
    time = np.arange(source_fs) / source_fs
    signal = np.sin(2 * np.pi * 1_000 * time) + np.sin(2 * np.pi * 10_000 * time)

    resampled = resample_signal(signal, source_fs, target_fs)
    frequencies = np.fft.rfftfreq(resampled.size, d=1 / target_fs)
    spectrum = np.abs(np.fft.rfft(resampled))
    low_tone = spectrum[np.argmin(np.abs(frequencies - 1_000))]
    aliased_tone = spectrum[np.argmin(np.abs(frequencies - 2_000))]

    assert aliased_tone < low_tone * 0.01


def test_equal_rates_return_a_copy():
    signal = np.arange(8, dtype=float)

    result = resample_signal(signal, 12_000, 12_000)

    np.testing.assert_array_equal(result, signal)
    assert result is not signal


@pytest.mark.parametrize("source_fs,target_fs", [(0, 12_000), (48_000, -1)])
def test_non_positive_rates_are_rejected(source_fs, target_fs):
    with pytest.raises(ValueError, match="must be positive"):
        resample_signal(np.ones(8), source_fs, target_fs)


def test_non_integer_rates_are_rejected():
    with pytest.raises(TypeError, match="must be integers"):
        resample_signal(np.ones(8), 48_000.0, 12_000)


def test_non_vector_or_empty_signals_are_rejected():
    with pytest.raises(ValueError, match="one-dimensional"):
        resample_signal(np.ones((2, 4)), 48_000, 12_000)
    with pytest.raises(ValueError, match="one-dimensional"):
        resample_signal(np.array([]), 48_000, 12_000)
