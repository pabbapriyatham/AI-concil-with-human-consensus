import pytest

from app.confidence.calibration import (
    calibration_metrics,
    fit_isotonic,
    fit_platt,
    held_out_experiment,
    predict_calibrated,
)


def test_metrics_boundaries():
    assert calibration_metrics([0, 1], [0, 1])["brier"] == 0
    assert calibration_metrics([0, 1], [1, 0])["brier"] == 1
    assert calibration_metrics([0.5, 0.5], [0, 1])["ece"] == 0
    with pytest.raises(ValueError):
        calibration_metrics([float("nan")], [1])


def test_fits_and_leakage():
    artifact = fit_isotonic([0.1, 0.2, 0.3, 0.4], [0, 1, 0, 1])
    predicted = predict_calibrated(artifact, [0.1, 0.2, 0.3, 0.4])
    assert predicted == [0, 0.5, 0.5, 1]
    platt = fit_platt([0.1, 0.2, 0.8, 0.9], [0, 0, 1, 1])
    assert predict_calibrated(platt, [0.1])[0] < predict_calibrated(platt, [0.9])[0]
    rows = [{"id": str(i), "score": i / 20, "correct": int(i > 10)} for i in range(20)]
    result = held_out_experiment(rows[:14], rows[14:])
    assert result["raw"]["samples"] == 6
    with pytest.raises(ValueError, match="overlap"):
        held_out_experiment(rows[:14], rows[10:])
