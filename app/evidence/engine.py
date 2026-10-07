import re
from app.comparison.relations import RelationEngine
from .schemas import EvidenceAssessment


class EvidenceEngine:
    def __init__(self, relations=None):
        self.relations = relations or RelationEngine()

    def assess(self, claim, evidence):
        candidates = []
        for sentence in re.split(r"(?<=[.!?])\s+|\n+", evidence.text):
            kind, confidence, method = self.relations.compare_text(sentence, claim.claim_text)
            verdict = ("SUPPORTS" if kind in {"AGREEMENT", "ENTAILMENT", "SUPPORT"}
                       else "CONTRADICTS" if kind == "CONTRADICTION" else "INSUFFICIENT")
            candidates.append((verdict, confidence, method, sentence))
        definite = [c for c in candidates if c[0] != "INSUFFICIENT"]
        # A source with internally conflicting evidence is insufficient.
        if len({c[0] for c in definite}) > 1:
            best = ("INSUFFICIENT", 0.0, "source-internal-conflict", evidence.text)
        else:
            best = max(definite or candidates, key=lambda c: c[1])
        return EvidenceAssessment(claim_id=claim.claim_id, evidence_id=evidence.evidence_id,
                                  verdict=best[0], confidence=best[1], method=best[2], matched_text=best[3])

    def verify(self, claims, evidence):
        return [self.assess(claim, item) for claim in claims for item in evidence]
