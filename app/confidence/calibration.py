"""Portable calibration fitting and held-out diagnostics; JSON artifacts only."""
import math
import numpy as np


def validate(scores, labels):
    if len(scores) != len(labels) or not scores:
        raise ValueError("Nonempty aligned scores/labels required")
    if any(not math.isfinite(p) or p < 0 or p > 1 for p in scores):
        raise ValueError("Scores must be finite values in [0,1]")
    if any(y not in {0, 1} for y in labels):
        raise ValueError("Binary labels required")


def calibration_metrics(scores, labels, bins=10):
    validate(scores, labels)
    if bins < 1:
        raise ValueError("Positive bin count required")
    curve = []
    ece = 0
    for index in range(bins):
        rows = [(p, y) for p, y in zip(scores, labels) if min(bins - 1, int(p * bins)) == index]
        if rows:
            confidence = sum(p for p, _ in rows) / len(rows)
            accuracy = sum(y for _, y in rows) / len(rows)
            ece += len(rows) / len(scores) * abs(confidence - accuracy)
            curve.append({"lower": index / bins, "upper": (index + 1) / bins,
                          "count": len(rows), "confidence": confidence, "accuracy": accuracy})
    return {"brier": sum((p - y)**2 for p, y in zip(scores, labels)) / len(scores),
            "ece": ece, "reliability_diagram": curve, "samples": len(scores)}


def fit_isotonic(scores, labels):
    validate(scores, labels)
    # Pool-adjacent-violators with grouped identical input scores.
    groups = {}
    for p, y in zip(scores, labels):
        groups.setdefault(p, []).append(y)
    blocks = []
    for p, ys in sorted(groups.items()):
        blocks.append({"xs": [p], "sum": sum(ys), "weight": len(ys)})
        while len(blocks) > 1 and blocks[-2]["sum"] / blocks[-2]["weight"] > blocks[-1]["sum"] / blocks[-1]["weight"]:
            right, left = blocks.pop(), blocks.pop()
            blocks.append({"xs": left["xs"] + right["xs"], "sum": left["sum"] + right["sum"],
                           "weight": left["weight"] + right["weight"]})
    x, y = [], []
    for block in blocks:
        x.extend(block["xs"])
        y.extend([block["sum"] / block["weight"]] * len(block["xs"]))
    return {"method": "isotonic-pav", "x": x, "y": y}


def fit_platt(scores, labels, iterations=2000):
    validate(scores, labels)
    if len(set(labels)) != 2:
        raise ValueError("Platt fit requires both outcome classes")
    logits = np.array([math.log(max(1e-6, p) / max(1e-6, 1 - p)) for p in scores])
    targets = np.array(labels)
    a, b = 1.0, 0.0
    for _ in range(iterations):
        pred = 1 / (1 + np.exp(-np.clip(a * logits + b, -40, 40)))
        error = pred - targets
        a -= .02 * float(np.mean(error * logits) + .001 * a)
        b -= .02 * float(np.mean(error))
    return {"method": "platt-logistic", "a": a, "b": b}


def predict_calibrated(artifact, scores):
    if artifact["method"] == "isotonic-pav":
        return np.interp(scores, artifact["x"], artifact["y"]).tolist()
    if artifact["method"] == "platt-logistic":
        logits = np.array([math.log(max(1e-6, p) / max(1e-6, 1 - p)) for p in scores])
        return (1 / (1 + np.exp(-np.clip(artifact["a"] * logits + artifact["b"], -40, 40)))).tolist()
    raise ValueError("Unknown calibrator")


def held_out_experiment(train, test, method="isotonic"):
    if len(train) < 10 or len(test) < 4:
        raise ValueError("At least 10 train and 4 held-out observations required")
    if {r["id"] for r in train} & {r["id"] for r in test}:
        raise ValueError("Calibration train/test IDs overlap")
    fit = {"isotonic": fit_isotonic, "platt": fit_platt}.get(method)
    if fit is None:
        raise ValueError("Unknown fit method")
    artifact = fit([r["score"] for r in train], [r["correct"] for r in train])
    scores, labels = [r["score"] for r in test], [r["correct"] for r in test]
    return {"artifact": artifact, "train_ids": [r["id"] for r in train], "test_ids": [r["id"] for r in test],
            "raw": calibration_metrics(scores, labels),
            "calibrated": calibration_metrics(predict_calibrated(artifact, scores), labels),
            "limitation": "Small development samples do not establish calibration or generalization."}


def reliability_svg(metrics):
    dots = "".join(f'<circle cx="{40 + 320 * r["confidence"]:.1f}" cy="{360 - 320 * r["accuracy"]:.1f}" r="5" fill="#2964b0"/>' for r in metrics["reliability_diagram"])
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="400" height="400"><rect width="400" height="400" fill="white"/><path d="M40 40V360H360 M40 360L360 40" stroke="#888" fill="none"/>{dots}<text x="100" y="390">Predicted confidence</text><text x="45" y="25">Observed accuracy</text></svg>'
