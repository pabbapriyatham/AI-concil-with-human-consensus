def deduplicate(claims):
    """Deduplicate within a response; do not erase independent model support."""
    seen, result = set(), []
    for claim in claims:
        key = (claim.response_id, claim.normalized_claim)
        if key not in seen:
            result.append(claim)
            seen.add(key)
    return result
