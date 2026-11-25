"""Prepare blinded review packets and score paired, adjudicated outcomes."""

import hashlib
import json
import math
import secrets
from collections import defaultdict
from typing import Literal

from pydantic import Field

from app.confidence.calibration import calibration_metrics
from app.schemas import StrictModel, uid

SYSTEMS = frozenset("ABCDEF")
COMPARISONS = (("F", "A"), ("F", "B"), ("F", "E"))
Verdict = Literal["CORRECT", "INCORRECT"]


class ReviewSubmission(StrictModel):
    study_id: str
    packet_sha256: str
    reviewer: str = Field(min_length=1, max_length=200, pattern=r"\S")
    verdicts: dict[str, Verdict]


def prepare_study(experiment):
    study_id = uid()
    tasks = []
    trials = {}
    by_example = defaultdict(dict)
    for row in experiment["records"]:
        example, system = row["example_id"], row["system"]
        question = row["question"]
        if system not in SYSTEMS or system in by_example[example]:
            raise ValueError("Study requires one result per example and system")
        by_example[example][system] = question
        candidate_id = uid()
        trials[candidate_id] = {
            "example_id": example,
            "question_sha256": hashlib.sha256(" ".join(question.casefold().split()).encode()).hexdigest(),
            "system": system,
            "system_error": row["system_error"],
            "answered": bool(row["answer_claims"]),
            "score": row["score"] if system in {"E", "F"} else None,
        }
        if not row["system_error"]:
            tasks.append({
                "candidate_id": candidate_id,
                "question": question,
                "claims": row["answer_claims"],
            })
    if not by_example or any(
        set(systems) != SYSTEMS or len(set(systems.values())) != 1 for systems in by_example.values()
    ):
        raise ValueError("Each example requires all six systems on the same question")
    secrets.SystemRandom().shuffle(tasks)
    packet = {"study_id": study_id, "candidates": tasks}
    digest = hashlib.sha256(json.dumps(packet, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
    packet["packet_sha256"] = digest
    key = {
        "study_id": study_id,
        "packet_sha256": digest,
        "experiment_id": experiment["experiment_id"],
        "dataset_sha256": experiment["dataset_sha256"],
        "configuration": experiment["configuration"],
        "trials": trials,
    }
    return packet, key


def submitted_verdicts(key, submission, expected_ids):
    if submission.study_id != key["study_id"] or submission.packet_sha256 != key["packet_sha256"]:
        raise ValueError("Review refers to a different study or packet")
    if set(submission.verdicts) != expected_ids:
        raise ValueError("Review must cover exactly the candidates assigned to that reviewer")
    return submission.verdicts


def accuracy_interval(correct, total):
    # Wilson 95% interval remains bounded for small samples and all-correct scores.
    rate = correct / total
    z = 1.959963984540054
    scale = 1 + z**2 / total
    midpoint = (rate + z**2 / (2 * total)) / scale
    radius = z * math.sqrt(rate * (1 - rate) / total + z**2 / (4 * total**2)) / scale
    return [max(0, midpoint - radius), min(1, midpoint + radius)]


def paired_comparison(treatment, control):
    wins = sum(treatment[example] and not control[example] for example in treatment)
    losses = sum(control[example] and not treatment[example] for example in treatment)
    discordant = wins + losses
    tail = sum(math.comb(discordant, i) for i in range(min(wins, losses) + 1))
    p_value = min(1, 2 * tail / (1 << discordant))
    return {
        "paired_examples": len(treatment),
        "treatment_only_correct": wins,
        "control_only_correct": losses,
        "accuracy_gain": (wins - losses) / len(treatment),
        "mcnemar_p_value": p_value,
        "bonferroni_p_value": min(1, p_value * len(COMPARISONS)),
    }


def score_study(key, first, second, adjudication=None):
    identities = [review.reviewer.strip().casefold() for review in (first, second, adjudication) if review]
    if len(identities) != len(set(identities)):
        raise ValueError("Submit separate reviews from distinct reviewers")
    trials = key["trials"]
    expected_ids = {candidate for candidate, trial in trials.items() if not trial["system_error"]}
    first_votes = submitted_verdicts(key, first, expected_ids)
    second_votes = submitted_verdicts(key, second, expected_ids)
    disagreements = {candidate for candidate in expected_ids if first_votes[candidate] != second_votes[candidate]}
    if adjudication is None and disagreements:
        return {
            "study_id": key["study_id"],
            "packet_sha256": key["packet_sha256"],
            "unresolved_candidate_ids": sorted(disagreements),
        }
    final_votes = {
        **first_votes,
        **(submitted_verdicts(key, adjudication, disagreements) if adjudication else {}),
    }
    grouped = defaultdict(list)
    for candidate, trial in trials.items():
        correct = final_votes.get(candidate) == "CORRECT"
        grouped[trial["system"]].append((trial, correct))

    summary = {}
    by_system = {}
    calibration_observations = {}
    for system, outcomes in sorted(grouped.items()):
        total = len(outcomes)
        correct = sum(correct for _, correct in outcomes)
        answered = [(trial, correct) for trial, correct in outcomes if trial["answered"] and not trial["system_error"]]
        scored = [(trial["score"], int(correct)) for trial, correct in answered if trial["score"] is not None]
        summary[system] = {
            "samples": total,
            "accuracy": correct / total,
            "accuracy_wilson_95": accuracy_interval(correct, total),
            "coverage": len(answered) / total,
            "answered_error_rate": 1 - sum(correct for _, correct in answered) / len(answered) if answered else None,
            "system_errors": sum(trial["system_error"] for trial, _ in outcomes),
            "raw_confidence_diagnostics": calibration_metrics(*map(list, zip(*scored))) if scored else None,
        }
        by_system[system] = {trial["example_id"]: correct for trial, correct in outcomes}
        if system in {"E", "F"}:
            calibration_observations[system] = [
                {
                    "id": trial["example_id"],
                    "question_sha256": trial["question_sha256"],
                    "score": trial["score"],
                    "correct": int(correct),
                }
                for trial, correct in answered if trial["score"] is not None
            ]
    return {
        "study_id": key["study_id"],
        "packet_sha256": key["packet_sha256"],
        "experiment_id": key["experiment_id"],
        "dataset_sha256": key["dataset_sha256"],
        "configuration": key["configuration"],
        "cases": [
            {"id": trial["example_id"], "question_sha256": trial["question_sha256"]}
            for trial in trials.values() if trial["system"] == "A"
        ],
        "reviewed_candidates": len(expected_ids),
        "initial_agreement": 1 - len(disagreements) / len(expected_ids) if expected_ids else None,
        "adjudicated_disagreements": len(disagreements),
        "summary": summary,
        "calibration_observations": calibration_observations,
        "paired_comparisons": {
            f"{treatment}_vs_{control}": paired_comparison(by_system[treatment], by_system[control])
            for treatment, control in COMPARISONS
        },
    }


def calibration_split(train, test, system):
    if not train["configuration"]["live"] or not test["configuration"]["live"]:
        raise ValueError("Calibration export requires two adjudicated live studies")
    if train["dataset_sha256"] == test["dataset_sha256"]:
        raise ValueError("Calibration studies must use distinct datasets")
    for field in (
        "models", "fallback", "prompt_version", "embedding_method", "nli_method", "memory_mode",
        "reviewed_memory_sha256",
    ):
        if train["configuration"].get(field) != test["configuration"].get(field):
            raise ValueError(f"Calibration system configuration differs on {field}")
    first = train["calibration_observations"][system]
    second = test["calibration_observations"][system]
    for field in ("id", "question_sha256"):
        if {row[field] for row in train["cases"]} & {row[field] for row in test["cases"]}:
            raise ValueError("Calibration studies overlap by example ID or question")
    if not first or not second:
        raise ValueError("Both calibration studies need scored answers")
    return [dict(row, split=split) for split, rows in (("train", first), ("test", second)) for row in rows]
