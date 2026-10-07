from app.claims.normalizer import normalize_claim
from app.confidence.calibration import calibration_metrics


def classification_metrics(tp, fp, fn):
    precision = tp / (tp + fp) if tp + fp else 0
    recall = tp / (tp + fn) if tp + fn else 0
    return {"precision": precision, "recall": recall,
            "f1": 2 * precision * recall / (precision + recall) if precision + recall else 0}


def correctness(predicted, expected, abstention_expected=False):
    pred = {normalize_claim(t) for t in predicted}
    gold = {normalize_claim(t) for t in expected}
    if abstention_expected:
        return not pred
    return pred == gold


def summarize(rows):
    scores, labels = [r["score"] for r in rows], [int(r["correct"]) for r in rows]
    supported = [r for r in rows if r["prediction"]]
    metrics = {"accuracy": sum(labels) / len(rows), "error_rate": 1 - sum(labels) / len(rows),
               "coverage": len(supported) / len(rows),
               "latency_mean": sum(r["latency"] for r in rows) / len(rows),
               "latency_p95": sorted(r["latency"] for r in rows)[min(len(rows) - 1, int(len(rows) * .95))],
               "tokens": sum(r["tokens"] for r in rows),
               "cost": sum(r["cost"] or 0 for r in rows) if all(r["cost"] is not None for r in rows) else None,
               "consistency": sum(r.get("consistency", 0) for r in rows) / len(rows),
               "explanation_completeness": sum(r["explanation_completeness"] for r in rows) / len(rows),
               "samples": len(rows)}
    metrics.update(calibration_metrics(scores, labels))
    metrics.update(classification_metrics(sum(r["claim_tp"] for r in rows),
                                         sum(r["claim_fp"] for r in rows), sum(r["claim_fn"] for r in rows)))
    detection = classification_metrics(sum(r["contradiction_tp"] for r in rows),
                                       sum(r["contradiction_fp"] for r in rows), sum(r["contradiction_fn"] for r in rows))
    metrics.update({f"contradiction_{k}": value for k, value in detection.items()})
    error_detection = classification_metrics(sum(r["error_detect_tp"] for r in rows),
                                            sum(r["error_detect_fp"] for r in rows), sum(r["error_detect_fn"] for r in rows))
    metrics.update({f"error_detection_{k}": value for k, value in error_detection.items()})
    return metrics
