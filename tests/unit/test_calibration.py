import pytest
from app.confidence.calibration import calibration_metrics, fit_isotonic, predict_calibrated, fit_platt, held_out_experiment


def test_metrics_boundaries():
    assert calibration_metrics([0, 1], [0, 1])["brier"] == 0
    assert calibration_metrics([0, 1], [1, 0])["brier"] == 1
    assert calibration_metrics([.5, .5], [0, 1])["ece"] == 0
    with pytest.raises(ValueError):
        calibration_metrics([float("nan")], [1])


def test_fits_and_leakage():
    artifact = fit_isotonic([.1, .2, .3, .4], [0, 1, 0, 1])
    predicted = predict_calibrated(artifact, [.1, .2, .3, .4])
    assert predicted == [0, .5, .5, 1]
    platt = fit_platt([.1, .2, .8, .9], [0, 0, 1, 1])
    assert predict_calibrated(platt, [.1])[0] < predict_calibrated(platt, [.9])[0]
    rows = [{"id": str(i), "score": i / 20, "correct": int(i > 10)} for i in range(20)]
    result = held_out_experiment(rows[:14], rows[14:])
    assert result["raw"]["samples"] == 6
    with pytest.raises(ValueError, match="overlap"):
        held_out_experiment(rows[:14], rows[10:])
