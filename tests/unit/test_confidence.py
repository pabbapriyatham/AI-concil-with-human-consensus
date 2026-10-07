from app.aggregation.strategies import ClaimDecision
from app.confidence import ConfidenceEngine


def decision(**changes):
    f = {
        "evidence_support": 0,
        "validated_support": 0,
        "evidence_contradiction": 0,
        "validated_contradiction": 0,
        "claim_type": "factual",
        **changes,
    }
    return ClaimDecision(
        claim_id="c",
        score=0.95,
        supporting_models=["m"],
        contradicting_models=[],
        evidence_ids=[],
        factors=f,
        reasons=[],
        strategy="knowledge",
    )


def test_raw_confidence_caps_and_coverage():
    engine = ConfidenceEngine()
    assert engine.claim(decision())["raw_confidence"] == 0.49
    strong = decision(evidence_support=0.9)
    assert engine.claim(strong)["raw_confidence"] == 0.95
    assert engine.claim(decision(evidence_support=0.9, evidence_contradiction=0.8))["raw_confidence"] == 0.2
    answer = engine.answer([strong], 1, 2)
    assert answer["raw_confidence"] == 0.475 and not answer["calibrated"]
