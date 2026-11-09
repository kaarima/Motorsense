import numpy as np
import pytest

from motorsense_ml.features import (
    crest_factor,
    envelope_band_energies,
    envelope_scale_invariant_features,
    kurtosis,
    peak,
    rms,
)


def test_rms_of_sine_is_amplitude_over_sqrt2():
    t = np.linspace(0, 1, 10_000, endpoint=False)
    x = 2.0 * np.sin(2 * np.pi * 50 * t)
    assert rms(x) == pytest.approx(2.0 / np.sqrt(2), rel=1e-3)


def test_peak_and_crest_factor_of_sine():
    t = np.linspace(0, 1, 10_000, endpoint=False)
    x = np.sin(2 * np.pi * 50 * t)
    assert peak(x) == pytest.approx(1.0, rel=1e-3)
    assert crest_factor(x) == pytest.approx(np.sqrt(2), rel=1e-3)


def test_kurtosis_of_gaussian_noise_is_about_3():
    rng = np.random.default_rng(0)
    assert kurtosis(rng.normal(size=200_000)) == pytest.approx(3.0, abs=0.05)


def test_impulses_raise_kurtosis():
    rng = np.random.default_rng(0)
    x = rng.normal(size=10_000)
    y = x.copy()
    y[::500] += 15.0
    assert kurtosis(y) > kurtosis(x) + 1


def test_zero_signal_is_safe():
    z = np.zeros(100)
    assert rms(z) == 0.0
    assert crest_factor(z) == 0.0
    assert kurtosis(z) == 0.0


def test_envelope_band_energies_detect_modulation_at_fault_order():
    fs = 12_000
    shaft_hz = 30.0
    fault_hz = 5.4152 * shaft_hz
    time = np.arange(fs * 2) / fs
    signal = (1 + 0.8 * np.cos(2 * np.pi * fault_hz * time)) * np.cos(2 * np.pi * 3_000 * time)

    energies = envelope_band_energies(signal, fs, shaft_hz)

    assert energies.shape == (4,)
    assert energies[0] > energies[1] + 1


def test_envelope_band_energies_reject_invalid_rotational_parameters():
    with pytest.raises(ValueError, match="shaft_hz"):
        envelope_band_energies(np.ones(12_000), 12_000, 0)


def test_scale_invariant_envelope_features_preserve_fault_order_and_ignore_gain():
    fs = 12_000
    shaft_hz = 30.0
    fault_hz = 5.4152 * shaft_hz
    time = np.arange(fs * 2) / fs
    signal = (1 + 0.8 * np.cos(2 * np.pi * fault_hz * time)) * np.cos(2 * np.pi * 3_000 * time)

    features = envelope_scale_invariant_features(signal, fs, shaft_hz)
    scaled_features = envelope_scale_invariant_features(17 * signal, fs, shaft_hz)

    assert features.shape == (8,)
    assert features[0] > features[1]
    assert features[4] > 10
    np.testing.assert_allclose(features, scaled_features, rtol=1e-7, atol=1e-7)


def test_scale_invariant_features_reject_invalid_neighbour_offset():
    with pytest.raises(ValueError, match="neighbor_offset_hz"):
        envelope_scale_invariant_features(np.ones(12_000), 12_000, 30, neighbor_offset_hz=2)
