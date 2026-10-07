class ConfidenceEngine:
    """Transparent raw scores; no assertion of calibrated probability."""
    def claim(self, decision):
        f = decision.factors
        score = min(.98, decision.score)
        verified = max(f["evidence_support"], f["validated_support"])
        reasons = list(decision.reasons)
        if verified < .5:
            score = min(score, .49)
            reasons.append("Weak or absent supporting evidence: confidence capped below 0.5")
        if f["evidence_contradiction"] > .5 or f["validated_contradiction"] > .5:
            score = min(score, .2)
            reasons.append("Strong contrary evidence or validated knowledge")
        if f["claim_type"] in {"uncertain", "opinion", "recommendation"}:
            score = min(score, .5)
            reasons.append("Subjective or uncertain claim; score is not factual verification")
        return {"claim_id": decision.claim_id, "raw_confidence": max(0, score),
                "uncertainty": 1 - max(0, score), "label": "raw confidence", "reasons": reasons}

    def answer(self, decisions, successful_models, requested_models):
        claims = [self.claim(d) for d in decisions]
        selected = [c for c, d in zip(claims, decisions) if d.score >= .5]
        confidence = sum(c["raw_confidence"] for c in selected) / len(selected) if selected else 0
        coverage = successful_models / max(1, requested_models)
        confidence *= coverage
        return {"claims": claims, "raw_confidence": confidence, "uncertainty": 1 - confidence,
                "label": "raw confidence", "calibrated": False, "model_coverage": coverage,
                "explanation": "Mean raw confidence of supported candidate claims, multiplied by successful model coverage; not a calibrated correctness probability."}
