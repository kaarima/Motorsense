import numpy as np
import pytest

from motorsense_ml.healthy_baseline import (
    HealthyBaselineDetector,
    leave_one_recording_out_scores,
)


def test_healthy_baseline_scores_healthy_rows_below_shifted_rows():
    healthy = np.asarray([[0.0, 1.0], [0.1, 0.9], [-0.1, 1.1], [0.05, 0.95]], dtype=float)
    detector = HealthyBaselineDetector().fit(healthy)

    scores = detector.decision_function([[0.0, 1.0], [2.0, 4.0]])

    assert scores[0] < scores[1]


def test_leave_one_recording_out_scores_return_one_score_per_window():
    features = np.asarray(
        [[0.0], [0.1], [0.05], [0.0], [-0.1], [-0.05], [0.02], [-0.02]],
        dtype=float,
    )
    recordings = np.repeat(["a", "b", "c", "d"], 2)

    scores = leave_one_recording_out_scores(features, recordings)

    assert scores.shape == (8,)
    assert np.all(np.isfinite(scores))


def test_leave_one_recording_out_requires_multiple_recordings():
    with pytest.raises(ValueError, match="at least two"):
        leave_one_recording_out_scores(np.asarray([[1.0], [1.1]]), np.asarray(["a", "a"]))


def test_baseline_requires_fit_and_valid_feature_shape():
    detector = HealthyBaselineDetector()
    with pytest.raises(ValueError, match="fit must be called"):
        detector.decision_function([[1.0]])
    with pytest.raises(ValueError, match="at least two rows"):
        detector.fit(np.asarray([[1.0]]))
