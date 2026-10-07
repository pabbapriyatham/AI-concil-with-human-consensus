from app.aggregation import STRATEGIES
from app.aggregation.reliability import ReliabilityProfiles
from app.claims.schemas import Claim
from app.comparison.relations import RelationEngine
from app.evidence import Evidence, EvidenceEngine


def test_evidence_overrides_majority():
    claims = [
        Claim(
            response_id=m,
            model=m,
            claim_text=f"The event happened in {year}.",
            normalized_claim=f"event {year}",
            claim_type="temporal",
        )
        for m, year in [("a", 2020), ("b", 2020), ("c", 2021)]
    ]
    relations = RelationEngine().graph(claims)
    evidence = [
        Evidence(
            text="The event happened in 2021.",
            source="official fixture",
            source_type="document",
            source_quality=1,
        )
    ]
    assessments = EvidenceEngine().verify(claims, evidence)
    majority = STRATEGIES["majority"].aggregate(claims, relations, evidence, assessments)
    aware = STRATEGIES["evidence"].aggregate(claims, relations, evidence, assessments)
    assert max(majority, key=lambda d: d.score).claim_id == claims[0].claim_id
    assert max(aware, key=lambda d: d.score).claim_id == claims[2].claim_id


def test_empirical_reliability():
    profiles = ReliabilityProfiles()
    assert profiles.profile("unknown")["accuracy"] is None
    for correct in [True, True, False]:
        profiles.observe("model", "history", "temporal", correct)
    profile = profiles.profile("model", "history", "temporal")
    assert profile["samples"] == 3 and profile["accuracy"] == 2 / 3
