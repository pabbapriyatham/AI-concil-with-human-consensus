"""Deterministic synthesis from retrieved structured facts; no invented citations."""


def synthesize(claims, decisions, confidence, evidence, relations, review_reasons):
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
    cited = {eid for _, d in supported for eid in d.evidence_ids}
    sources = [e for e in evidence if e.evidence_id in cited]
    if sources:
        lines.extend(["", "## Evidence actually retrieved"])
        for item in sources:
            label = item.source.replace("[", "(").replace("]", ")")
            lines.append(f"- [{label}]({item.url})" if item.url else f"- {label}")
    used_memory = [e for e in sources if e.source_type == "knowledge"]
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
