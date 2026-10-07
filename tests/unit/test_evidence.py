from app.claims.schemas import Claim
from app.evidence import Evidence, EvidenceEngine


def test_support_contradict_insufficient():
    claim = Claim(
        response_id="r",
        model="m",
        claim_text="The event happened in 2020.",
        normalized_claim="the event happened in 2020",
        claim_type="temporal",
    )
    engine = EvidenceEngine()
    for text, expected in [
        ("The event happened in 2020.", "SUPPORTS"),
        ("The event happened in 2021.", "CONTRADICTS"),
        ("Bananas contain potassium.", "INSUFFICIENT"),
        ("The event happened in 2020. The event happened in 2021.", "INSUFFICIENT"),
    ]:
        evidence = Evidence(text=text, source="supplied file", source_type="document")
        result = engine.assess(claim, evidence)
        assert result.verdict == expected
        assert result.evidence_id == evidence.evidence_id
