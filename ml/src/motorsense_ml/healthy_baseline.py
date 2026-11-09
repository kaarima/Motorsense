"""Robust per-motor healthy-baseline anomaly scoring."""

import numpy as np


class HealthyBaselineDetector:
    """Score feature rows by robust distance from this motor's healthy data."""

    def fit(self, healthy_features: np.ndarray) -> "HealthyBaselineDetector":
        values = np.asarray(healthy_features, dtype=float)
        if values.ndim != 2 or values.shape[0] < 2 or values.shape[1] < 1:
            raise ValueError("healthy_features must be a 2D array with at least two rows")
        if not np.all(np.isfinite(values)):
            raise ValueError("healthy_features must contain only finite values")

        self.center_ = np.median(values, axis=0)
        mad = np.median(np.abs(values - self.center_), axis=0) * 1.4826
        floor = 1e-8 * np.maximum(1.0, np.abs(self.center_))
        self.scale_ = np.maximum(mad, floor)
        return self

    def decision_function(self, features: np.ndarray) -> np.ndarray:
        """Return robust standardized Euclidean distances; higher is stranger."""
        if not hasattr(self, "center_"):
            raise ValueError("fit must be called before decision_function")
        values = np.asarray(features, dtype=float)
        if values.ndim != 2 or values.shape[1] != self.center_.size:
            raise ValueError("features must be a 2D array with the fitted feature count")
        if not np.all(np.isfinite(values)):
            raise ValueError("features must contain only finite values")
        standardized = (values - self.center_) / self.scale_
        return np.sqrt(np.mean(standardized**2, axis=1))


def leave_one_recording_out_scores(
    healthy_features: np.ndarray,
    recording_ids: np.ndarray,
) -> np.ndarray:
    """Cross-fit healthy anomaly scores, never fitting on the scored recording."""
    values = np.asarray(healthy_features, dtype=float)
    groups = np.asarray(recording_ids)
    if values.ndim != 2 or values.shape[0] != groups.size:
        raise ValueError("recording_ids must contain one ID for each feature row")
    unique_groups = np.unique(groups)
    if unique_groups.size < 2:
        raise ValueError("at least two healthy recordings are required")

    scores = np.empty(values.shape[0], dtype=float)
    for group in unique_groups:
        heldout = groups == group
        detector = HealthyBaselineDetector().fit(values[~heldout])
        scores[heldout] = detector.decision_function(values[heldout])
    return scores
