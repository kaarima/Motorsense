import numpy as np
import pytest

from motorsense_ml.envelope import envelope, envelope_spectrum


def amplitude_modulated_carrier(fs=12_000, duration=2.0, mod_hz=120):
    time = np.arange(int(fs * duration)) / fs
    return (1 + 0.5 * np.cos(2 * np.pi * mod_hz * time)) * np.cos(2 * np.pi * 2_000 * time)


def test_envelope_is_nonnegative_and_preserves_length():
    fs = 12_000
    signal = amplitude_modulated_carrier(fs=fs)

    result = envelope(signal, fs, (1_500, 2_500))

    assert result.shape == signal.shape
    assert np.all(result >= 0)


def test_envelope_spectrum_recovers_modulation_frequency():
    fs = 12_000
    signal = amplitude_modulated_carrier(fs=fs)

    frequencies, magnitude = envelope_spectrum(signal, fs, (1_500, 2_500))
    peak_hz = frequencies[np.argmax(magnitude)]

    assert peak_hz == pytest.approx(120, abs=1)


@pytest.mark.parametrize("band_hz", [(0, 2_000), (1_000, 6_000), (2_500, 1_500)])
def test_invalid_band_is_rejected(band_hz):
    with pytest.raises(ValueError, match="band_hz"):
        envelope(np.ones(100), 12_000, band_hz)


def test_short_signals_are_rejected_by_filtering():
    with pytest.raises(ValueError):
        envelope(np.ones(4), 12_000, (1_500, 2_500))
