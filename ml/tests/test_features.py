import numpy as np
import pytest

from motorsense_ml.features import crest_factor, kurtosis, peak, rms


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
