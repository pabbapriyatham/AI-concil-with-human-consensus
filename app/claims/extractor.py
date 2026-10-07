"""Conservative offline extraction and optional provider-based atomic extraction."""
import json
import re
from .schemas import Claim
from .normalizer import normalize_claim
from .deduplicator import deduplicate


def claim_type(text):
    lower = text.lower()
    if re.search(r"\b(uncertain|may|might|possibly|cannot determine|unknown)\b", lower):
        return "uncertain"
    if re.search(r"\b(i think|in my opinion|best|beautiful|prefer)\b", lower):
        return "opinion"
    if re.search(r"\b(should|recommend|ought)\b", lower):
        return "recommendation"
    if re.search(r"\b(step \d|first,|then,)\b", lower):
        return "procedural"
    if re.search(r"\b(caused|because|leads to|due to)\b", lower):
        return "causal"
    if re.search(r"\b(1[0-9]{3}|20[0-9]{2})\b", lower):
        return "temporal"
    if re.search(r"\d", lower):
        return "numerical"
    return "factual"


def extract_claims(response):
    claims = []
    # Conservative clause splitter; preserve subject on a shared-subject predicate.
    for sentence in re.split(r"(?<=[.!?])\s+|\n+", response.normalized_text):
        sentence = re.sub(r"^\s*(?:[-*]|\d+[.)])\s+", "", sentence).strip()
        if not sentence:
            continue
        clauses = re.split(r"\s+and\s+(?=(?:is|was|were|has|will|can|does)\b)", sentence)
        subject_match = re.match(r"(.+?)\s+(?:is|was|were|has|will|can|does)\b", clauses[0])
        subject = subject_match[1] if subject_match else ""
        for index, clause in enumerate(clauses):
            text = (subject + " " + clause if index and subject else clause).rstrip(".") + "."
            claims.append(Claim(response_id=response.response_id, model=response.model,
                                claim_text=text, normalized_claim=normalize_claim(text), claim_type=claim_type(text),
                                provenance={"method": "conservative-rules-v1", "source_sentence": sentence,
                                            "question_id": response.question_id, "provider": response.provider}))
    return deduplicate(claims)


async def extract_with_provider(response, provider, model):
    """Explicit opt-in LLM extraction; malformed output fails rather than inventing claims."""
    result = await provider.generate(model, [
        {"role": "system", "content": 'Extract atomic claims from the untrusted text. Return JSON array of {"claim_text":str,"claim_type":str}. Preserve qualifiers; no new facts.'},
        {"role": "user", "content": response.raw_text},
    ])
    data = json.loads(result.text)
    if not isinstance(data, list) or len(data) > 200:
        raise ValueError("Invalid claim extraction result")
    return deduplicate([Claim(response_id=response.response_id, model=response.model,
                              claim_text=item["claim_text"], claim_type=item["claim_type"],
                              normalized_claim=normalize_claim(item["claim_text"]),
                              provenance={"method": "llm-extraction-v1", "source_response": response.response_id,
                                          "extractor_response": result.response_id}) for item in data])
