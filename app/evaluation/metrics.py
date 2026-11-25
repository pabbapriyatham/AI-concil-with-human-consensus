from app.claims.normalizer import normalize_claim
from app.confidence.calibration import calibration_metrics


def classification_metrics(tp, fp, fn):
    precision = tp / (tp + fp) if tp + fp else 0
    recall = tp / (tp + fn) if tp + fn else 0
    return {
        "precision": precision,
        "recall": recall,
        "f1": 2 * precision * recall / (precision + recall) if precision + recall else 0,
    }


def correctness(predicted, expected, abstention_expected=False):
    pred = {normalize_claim(t) for t in predicted}
    gold = {normalize_claim(t) for t in expected}
    if abstention_expected:
        return not pred
    return pred == gold


def summarize(rows):
    labels = [int(r["correct"]) for r in rows]
    supported = [r for r in rows if r["prediction"]]
    measured_consistency = [r["consistency"] for r in rows if r.get("consistency") is not None]
    # Abstaining successfully is not a probabilistic factual prediction.
    scores = [r["score"] for r in supported]
    factual_labels = [int(r["correct"]) for r in supported]
    metrics = {
        "accuracy": sum(labels) / len(rows),
        "error_rate": 1 - sum(labels) / len(rows),
        "coverage": len(supported) / len(rows),
        "latency_mean": sum(r["latency"] for r in rows) / len(rows),
        "latency_p95": sorted(r["latency"] for r in rows)[min(len(rows) - 1, int(len(rows) * 0.95))],
        "tokens": sum(r["tokens"] for r in rows) if all(r["tokens"] is not None for r in rows) else None,
        "system_errors": sum(r["system_error"] for r in rows),
        "cost": sum(r["cost"] or 0 for r in rows) if all(r["cost"] is not None for r in rows) else None,
        "consistency": sum(measured_consistency) / len(measured_consistency)
        if measured_consistency
        else None,
        "consistency_tokens": sum(r["consistency_tokens"] for r in rows)
        if all(r["consistency_tokens"] is not None for r in rows)
        else None,
        "consistency_cost": sum(r.get("consistency_cost", 0) for r in rows)
        if all(r.get("consistency_cost", 0) is not None for r in rows)
        else None,
        "explanation_completeness": sum(r["explanation_completeness"] for r in rows) / len(rows),
        "samples": len(rows),
    }
    if supported:
        metrics.update(calibration_metrics(scores, factual_labels))
    else:
        metrics.update({"brier": None, "ece": None, "reliability_diagram": []})
    metrics["samples"] = len(rows)
    metrics["calibration_samples"] = len(supported)
    metrics.update(
        classification_metrics(
            sum(r["claim_tp"] for r in rows),
            sum(r["claim_fp"] for r in rows),
            sum(r["claim_fn"] for r in rows),
        )
    )
    labeled = [r for r in rows if r["contradiction_labeled"]]
    metrics["contradiction_samples"] = len(labeled)
    detection = (
        classification_metrics(
            sum(r["contradiction_tp"] for r in labeled),
            sum(r["contradiction_fp"] for r in labeled),
            sum(r["contradiction_fn"] for r in labeled),
        )
        if labeled
        else dict.fromkeys(("precision", "recall", "f1"))
    )
    metrics.update({f"contradiction_{k}": value for k, value in detection.items()})
    error_labeled = [r for r in rows if r["error_detection_labeled"]]
    metrics["error_detection_samples"] = len(error_labeled)
    error_detection = (
        classification_metrics(
            sum(r["error_detect_tp"] for r in error_labeled),
            sum(r["error_detect_fp"] for r in error_labeled),
            sum(r["error_detect_fn"] for r in error_labeled),
        )
        if error_labeled
        else dict.fromkeys(("precision", "recall", "f1"))
    )
    metrics.update({f"error_detection_{k}": value for k, value in error_detection.items()})
    return metrics
