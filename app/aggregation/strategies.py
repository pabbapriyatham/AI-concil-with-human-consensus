from abc import ABC, abstractmethod
from pydantic import Field
from app.schemas import StrictModel
from .reliability import ReliabilityProfiles


class ClaimDecision(StrictModel):
    claim_id: str
    score: float = Field(ge=0, le=1)
    supporting_models: list[str]
    contradicting_models: list[str]
    evidence_ids: list[str]
    factors: dict
    reasons: list[str]
    strategy: str


class AggregationStrategy(ABC):
    name = ""

    @abstractmethod
    def aggregate(self, claims, relations, evidence, assessments, reliability=None, domain="general", category="factual"):
        pass


def factors_for(claim, claims, relations, evidence, assessments, reliability, domain, category):
    by_id = {c.claim_id: c for c in claims}
    supporters, opponents = {claim.model}, set()
    for edge in relations:
        if claim.claim_id not in {edge.source_claim, edge.target_claim}:
            continue
        other = edge.target_claim if edge.source_claim == claim.claim_id else edge.source_claim
        if edge.relation_type in {"AGREEMENT", "DUPLICATE", "SUPPORT"} or (edge.relation_type == "ENTAILMENT" and edge.target_claim == claim.claim_id):
            supporters.add(by_id[other].model)
        elif edge.relation_type == "CONTRADICTION":
            opponents.add(by_id[other].model)
    models = {c.model for c in claims}
    weights = {m: reliability.profile(m, domain, category)["weight"] for m in models}
    total = sum(weights.values()) or 1
    agreement = sum(weights[m] for m in supporters) / total
    disagreement = sum(weights[m] for m in opponents) / total
    by_evidence = {e.evidence_id: e for e in evidence}
    support_sources, conflict_sources, memory_support, memory_conflict, ids = {}, {}, 0.0, 0.0, []
    for assessment in assessments:
        if assessment.claim_id != claim.claim_id or assessment.verdict == "INSUFFICIENT":
            continue
        item = by_evidence[assessment.evidence_id]
        strength = item.source_quality * assessment.confidence
        # Recency is transparent, mild, and only applied when publication time is known.
        if item.published_at:
            from app.schemas import now
            age_days = max(0, (now() - item.published_at).total_seconds() / 86400)
            strength *= max(.5, 1 / (1 + age_days / 3650))
        ids.append(item.evidence_id)
        validated = item.source_type == "knowledge" and item.provenance.get("status") == "VALIDATED"
        if validated:
            if assessment.verdict == "SUPPORTS":
                memory_support = max(memory_support, strength)
            else:
                memory_conflict = max(memory_conflict, strength)
        elif assessment.verdict == "SUPPORTS":
            support_sources[item.source] = max(support_sources.get(item.source, 0), strength)
        else:
            conflict_sources[item.source] = max(conflict_sources.get(item.source, 0), strength)
    return supporters, opponents, ids, {
        "agreement": agreement, "model_contradiction": disagreement,
        "support_count": len(supporters), "model_count": len(models),
        "evidence_support": max(support_sources.values(), default=0),
        "evidence_contradiction": max(conflict_sources.values(), default=0),
        "validated_support": memory_support, "validated_contradiction": memory_conflict,
        "reliability": [reliability.profile(m, domain, category) for m in sorted(models)],
        "claim_type": claim.claim_type,
    }


class ScoredStrategy(AggregationStrategy):
    def aggregate(self, claims, relations, evidence, assessments, reliability=None, domain="general", category="factual"):
        reliability = reliability or ReliabilityProfiles()
        decisions = []
        for claim in claims:
            supporters, opponents, ids, factors = factors_for(claim, claims, relations, evidence, assessments, reliability, domain, category)
            score = self.score(factors)
            reasons = [f"{len(supporters)} independent model(s) support this claim",
                       f"{len(opponents)} model(s) contradict it",
                       f"Evidence support {factors['evidence_support']:.2f}; contradiction {factors['evidence_contradiction']:.2f}",
                       f"Validated memory support {factors['validated_support']:.2f}; contradiction {factors['validated_contradiction']:.2f}"]
            decisions.append(ClaimDecision(claim_id=claim.claim_id, score=max(0, min(1, score)),
                supporting_models=sorted(supporters), contradicting_models=sorted(opponents),
                evidence_ids=ids, factors=factors, reasons=reasons, strategy=self.name))
        return decisions


class MajorityBaseline(ScoredStrategy):
    name = "majority"
    def score(self, f):
        return f["support_count"] / max(1, f["model_count"])


class WeightedAgreement(ScoredStrategy):
    name = "weighted"
    def score(self, f):
        return f["agreement"] - .3 * f["model_contradiction"]


class EvidenceAware(ScoredStrategy):
    name = "evidence"
    def score(self, f):
        return .15 + .25 * f["agreement"] + .6 * f["evidence_support"] - .6 * f["evidence_contradiction"] - .2 * f["model_contradiction"]


class KnowledgeAware(EvidenceAware):
    name = "knowledge"
    def score(self, f):
        return super().score(f) + .6 * f["validated_support"] - .8 * f["validated_contradiction"]


STRATEGIES = {s.name: s() for s in [MajorityBaseline, WeightedAgreement, EvidenceAware, KnowledgeAware]}
