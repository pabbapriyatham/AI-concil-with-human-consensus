from typing import Literal

from pydantic import Field, field_validator

from app.evidence import Evidence
from app.schemas import StrictModel


class DatasetExample(StrictModel):
    id: str
    question: str
    ground_truth: str | None
    expected_claims: list[str]
    fixture_contradiction_expected: bool | None = None
    evidence: list[Evidence]
    difficulty: Literal["easy", "medium", "hard"]
    category: Literal[
        "factual", "numerical", "temporal", "causal", "reasoning", "ambiguous", "conflicting-information"
    ]
    domain: str = "synthetic-registry"
    fixture_responses: list[str] | None = Field(default=None, min_length=3, max_length=3)
    provenance: str

    @field_validator("id", "question")
    @classmethod
    def require_text(cls, value):
        if not value.strip():
            raise ValueError("Evaluation ID and question must contain text")
        return value.strip()


class ReviewedMemory(StrictModel):
    claim: str = Field(min_length=1, max_length=10000)
    reviewer: str = Field(min_length=1, max_length=200)
    explanation: str = Field(min_length=1, max_length=10000)
    evidence: list[Evidence] = Field(min_length=1, max_length=20)

    @field_validator("evidence")
    @classmethod
    def require_source_material(cls, evidence):
        if any(item.source_type == "knowledge" for item in evidence):
            raise ValueError("Reviewed memory requires source evidence")
        return evidence
