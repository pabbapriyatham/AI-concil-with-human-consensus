from app.claims.extractor import extract_claims, claim_type
from app.normalization import normalize_response
from app.providers.base import ProviderResult


def test_compound_atomic_and_dedup():
    response = normalize_response(ProviderResult("p", "m", "The Eiffel Tower was completed in 1889 and is located in Paris. The Eiffel Tower is located in Paris.", "r"), "q")
    claims = extract_claims(response)
    assert len(claims) == 2
    assert claims[0].claim_type == "temporal"
    assert claims[1].claim_text == "The Eiffel Tower is located in Paris."
    assert all(c.response_id == response.response_id for c in claims)


def test_subjectivity_and_qualifiers():
    assert claim_type("I think Paris is beautiful.") == "opinion"
    assert claim_type("It may have happened in 2020.") == "uncertain"
    assert claim_type("You should check the source.") == "recommendation"
