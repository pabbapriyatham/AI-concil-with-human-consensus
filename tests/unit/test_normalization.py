import pytest
from pydantic import ValidationError

from app.normalization import normalize_response
from app.providers.base import ProviderResult


def test_raw_provenance_and_immutability():
    result = ProviderResult("p", "m", "  raw   text\n ", "source-id", metadata={"x": [1]})
    response = normalize_response(result, "q")
    assert response.raw_text == result.text
    assert response.normalized_text == "raw text"
    assert response.metadata["provider_response_id"] == "source-id"
    assert response.response_id != result.response_id
    result.metadata["x"].append(2)
    assert response.metadata["x"] == [1]
    with pytest.raises(ValidationError):
        response.raw_text = "changed"
