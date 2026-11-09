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


def envelope_scale_invariant_features(
    x: np.ndarray,
    fs: int,
    shaft_hz: float,
    carrier_band_hz: tuple[float, float] = (2_500, 3_500),
    bandwidth_hz: float = 2.0,
    harmonics: int = 3,
    total_band_hz: float = 500.0,
    neighbor_offset_hz: float = 6.0,
) -> np.ndarray:
    """Return fault-band energy ratios and envelope peak-to-neighbor ratios.

    The eight values are ordered as four energy ratios (BPFI, BPFO, BSF,
    FTF), then four fundamental peak-to-neighbor amplitude ratios in dB.
    Energy ratios normalize each fault-order band by total envelope-spectrum
    energy below ``total_band_hz``. The neighbor ratio compares the peak
    within ``bandwidth_hz`` of a fault order with the mean magnitude in the
    two bands offset by ``neighbor_offset_hz``.
    """
    if not np.isfinite(shaft_hz) or shaft_hz <= 0:
        raise ValueError("shaft_hz must be positive and finite")
    if not np.isfinite(bandwidth_hz) or bandwidth_hz <= 0:
        raise ValueError("bandwidth_hz must be positive and finite")
    if not isinstance(harmonics, int | np.integer) or harmonics < 1:
        raise ValueError("harmonics must be a positive integer")
    if not np.isfinite(total_band_hz) or total_band_hz <= 0:
        raise ValueError("total_band_hz must be positive and finite")
    if not np.isfinite(neighbor_offset_hz) or neighbor_offset_hz <= bandwidth_hz:
        raise ValueError("neighbor_offset_hz must be finite and greater than bandwidth_hz")

    frequencies, magnitudes = envelope_spectrum(x, fs, carrier_band_hz)
    total_mask = (frequencies > 0) & (frequencies <= total_band_hz)
    total_energy = max(float(np.sum(magnitudes[total_mask] ** 2)), np.finfo(float).tiny)
    energy_ratios = []
    peak_neighbor_ratios_db = []

    for order in DRIVE_END_FAULT_ORDERS.values():
        fault_hz = order * shaft_hz
        harmonic_mask = np.zeros(frequencies.shape, dtype=bool)
        for harmonic in range(1, harmonics + 1):
            center_hz = fault_hz * harmonic
            harmonic_mask |= np.abs(frequencies - center_hz) <= bandwidth_hz
        fault_energy = np.sum(magnitudes[harmonic_mask] ** 2)
        energy_ratios.append(float(fault_energy / total_energy))

        target_mask = np.abs(frequencies - fault_hz) <= bandwidth_hz
        neighbor_mask = (np.abs(frequencies - (fault_hz - neighbor_offset_hz)) <= bandwidth_hz) | (
            np.abs(frequencies - (fault_hz + neighbor_offset_hz)) <= bandwidth_hz
        )
        target_peak = float(np.max(magnitudes[target_mask], initial=0.0))
        neighbor_mean = float(np.mean(magnitudes[neighbor_mask])) if np.any(neighbor_mask) else 0.0
        floor = np.finfo(float).tiny
        peak_neighbor_ratios_db.append(
            20 * np.log10((target_peak + floor) / (neighbor_mean + floor))
        )

    return np.asarray([*energy_ratios, *peak_neighbor_ratios_db])
