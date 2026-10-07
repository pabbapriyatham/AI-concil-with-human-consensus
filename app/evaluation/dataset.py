from typing import Literal
from pydantic import Field
from app.schemas import StrictModel
from app.evidence import Evidence


class DatasetExample(StrictModel):
    id: str
    question: str
    ground_truth: str | None
    expected_claims: list[str]
    evidence: list[Evidence]
    difficulty: Literal["easy", "medium", "hard"]
    category: Literal["factual", "numerical", "temporal", "causal", "reasoning", "ambiguous", "conflicting-information"]
    domain: str = "synthetic-registry"
    fixture_responses: list[str] = Field(min_length=3, max_length=3)
    provenance: str
