from copy import deepcopy

import pytest

from app.evaluation.study import ReviewSubmission, calibration_split, prepare_study, score_study


def experiment():
    return {
        "experiment_id": "trial",
        "dataset_sha256": "dataset-1",
        "configuration": {"live": True, "models": ["model"], "prompt_version": "one"},
        "records": [
            {
                "example_id": f"case-{i}",
                "question": f"Question {i}",
                "system": system,
                "answer_claims": [] if system == "A" and not i else [f"Answer {i}"],
                "system_error": system == "A" and not i,
                "score": 0.8,
            }
            for i in range(2)
            for system in "ABCDEF"
        ],
    }


def submission(key, reviewer, verdicts):
    return ReviewSubmission(
        study_id=key["study_id"],
        packet_sha256=key["packet_sha256"],
        reviewer=reviewer,
        verdicts=verdicts,
    )


def test_blinded_review_requires_adjudication_and_counts_failed_trials():
    packet, key = prepare_study(experiment())
    candidates = {trial["candidate_id"] for trial in packet["candidates"]}
    assert len(candidates) == 11
    assert all(set(item) == {"candidate_id", "question", "claims"} for item in packet["candidates"])
    first = submission(key, "First", dict.fromkeys(candidates, "CORRECT"))
    disputed = next(candidate for candidate in candidates if key["trials"][candidate]["system"] == "F")
    second = submission(key, "Second", {**first.verdicts, disputed: "INCORRECT"})
    assert score_study(key, first, second)["unresolved_candidate_ids"] == [disputed]
    referee = submission(key, "Third", {disputed: "CORRECT"})
    report = score_study(key, first, second, referee)
    assert report["summary"]["A"]["system_errors"] == 1
    assert report["summary"]["A"]["accuracy"] == 0.5
    assert report["summary"]["F"]["accuracy"] == 1
    assert report["paired_comparisons"]["F_vs_A"]["accuracy_gain"] == 0.5
    assert report["paired_comparisons"]["F_vs_B"]["mcnemar_p_value"] == 1
    assert report["summary"]["F"]["raw_confidence_diagnostics"]["samples"] == 2
    with pytest.raises(ValueError, match="distinct reviewers"):
        score_study(key, first, first)
    with pytest.raises(ValueError, match="different study"):
        score_study(key, first, second.model_copy(update={"packet_sha256": "wrong"}))
    with pytest.raises(ValueError, match="exactly the candidates"):
        score_study(key, first, second, referee.model_copy(update={"verdicts": first.verdicts}))


def test_calibration_split_rejects_overlapping_questions_with_renamed_ids():
    _, key = prepare_study(experiment())
    votes = {trial: "CORRECT" for trial, item in key["trials"].items() if not item["system_error"]}
    train = score_study(key, submission(key, "First", votes), submission(key, "Second", votes))
    test = deepcopy(train)
    test["dataset_sha256"] = "dataset-2"
    for row in test["cases"] + test["calibration_observations"]["F"]:
        row["id"] += "-test"
    with pytest.raises(ValueError, match="overlap by example ID or question"):
        calibration_split(train, test, "F")
    for row in test["cases"] + test["calibration_observations"]["F"]:
        row["question_sha256"] += "-changed"
    assert [row["split"] for row in calibration_split(train, test, "F")] == ["train", "train", "test", "test"]
