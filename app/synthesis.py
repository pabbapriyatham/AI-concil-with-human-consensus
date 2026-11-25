"""Deterministic synthesis from retrieved structured facts; no invented citations."""

from collections import defaultdict


def synthesize(claims, decisions, confidence, evidence, relations, review_reasons, assessments=()):
    by_id = {c.claim_id: c for c in claims}
    claim_confidence = {c["claim_id"]: c["raw_confidence"] for c in confidence["claims"]}
    supported, seen = [], set()
    for decision in sorted(decisions, key=lambda d: d.score, reverse=True):
        claim = by_id[decision.claim_id]
        if (
            decision.score >= 0.5
            and claim_confidence[claim.claim_id] >= 0.5
            and claim.normalized_claim not in seen
        ):
            supported.append((claim, decision))
            seen.add(claim.normalized_claim)
    lines = ["## Conclusion"]
    if supported:
        lines.extend(f"- {claim.claim_text}" for claim, _ in supported)
    else:
        lines.append(
            "The available evidence is insufficient to establish a conclusion. Human review is required."
        )
    lines.extend(
        ["", f"{confidence['label'].capitalize()}: {confidence['raw_confidence']:.0%} (uncalibrated)."]
    )
    contradictions = [r for r in relations if r.relation_type == "CONTRADICTION"]
    if contradictions:
        lines.extend(["", "## Disagreements"])
        for edge in contradictions[:10]:
            a, b = by_id[edge.source_claim], by_id[edge.target_claim]
            lines.append(f"- {a.model}: {a.claim_text} / {b.model}: {b.claim_text}")
    evidence_by_id = {item.evidence_id: item for item in evidence}
    assessments_by_claim = defaultdict(list)
    for assessment in assessments:
        if assessment.verdict != "INSUFFICIENT":
            assessments_by_claim[assessment.claim_id].append(assessment)
    cited = set()
    for claim, decision in supported:
        assessments_for_claim = [
            assessment
            for assessment in assessments_by_claim[claim.claim_id]
            if assessment.evidence_id in decision.evidence_ids
        ]
        if not assessments_for_claim:
            continue
        if not cited:
            lines.extend(["", "## Evidence by claim"])
        lines.extend(["", claim.claim_text])
        for assessment in assessments_for_claim:
            item = evidence_by_id[assessment.evidence_id]
            cited.add(item.evidence_id)
            label = item.source.replace("[", "(").replace("]", ")")
            source = f"[{label}]({item.url})" if item.url else label
            lines.append(f"- {assessment.verdict.title()} · {source} — {assessment.matched_text}")
    used_memory = [item for item in evidence if item.evidence_id in cited and item.source_type == "knowledge"]
    if used_memory:
        lines.extend(
            [
                "",
                "This conclusion is influenced by previously human-validated knowledge. Human validation can itself require revision.",
            ]
        )
    if review_reasons:
        lines.extend(["", "## Human review required", *[f"- {reason}" for reason in review_reasons]])
    lines.extend(
        [
            "",
            "Limitations: this is decision support. Agreement is not proof; retrieval, extraction and relation methods can miss or misinterpret information.",
        ]
    )
    return {
        "text": "\n".join(lines),
        "supporting_claim_ids": [c.claim_id for c, _ in supported],
        "evidence_ids": sorted(cited),
        "knowledge_used": [e.provenance for e in used_memory],
    }
