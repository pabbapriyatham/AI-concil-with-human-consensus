import os
from typing import Literal

from pydantic import Field, field_validator

from app.evidence.schemas import Evidence
from app.schemas import StrictModel


class ModelSpec(StrictModel):
    provider: Literal["openai", "gemini", "anthropic", "openrouter", "mock"]
    model: str = Field(min_length=1, max_length=200, pattern=r"^[a-zA-Z0-9._:/-]+$")

    @property
    def key(self):
        return f"{self.provider}:{self.model}"


def configured_models():
    value = os.getenv(
        "MAHTHILDIS_MODELS", "openai:gpt-5.1,gemini:gemini-3-pro-preview,anthropic:claude-sonnet-4-5"
    )
    return [
        ModelSpec(provider=entry.split(":", 1)[0], model=entry.split(":", 1)[1]) for entry in value.split(",")
    ]


class ConsensusRequest(StrictModel):
    question: str = Field(min_length=1, max_length=20000)
    context: str = Field(default="", max_length=50000)
    models: list[ModelSpec] | None = Field(default=None, min_length=1, max_length=8)
    mode: Literal["CHEAP", "BALANCED", "HIGH_ACCURACY"] = "BALANCED"
    aggregation: Literal["majority", "weighted", "evidence", "knowledge"] = "knowledge"
    evidence: list[Evidence] = Field(default_factory=list, max_length=30)
    domain: str = Field(default="general", min_length=1, max_length=100)
    category: str = Field(default="factual", min_length=1, max_length=100)
    allow_escalation: bool = True
    timeout: float = Field(default=60, ge=1, le=180)

    @field_validator("question")
    @classmethod
    def nonblank(cls, value):
        if not value.strip():
            raise ValueError("Question must contain text")
        return value.strip()

    @field_validator("models")
    @classmethod
    def unique_models(cls, value):
        if value and len({m.key for m in value}) != len(value):
            raise ValueError("Duplicate model selections")
        return value

    @field_validator("evidence")
    @classmethod
    def no_forged_memory(cls, value):
        if any(e.source_type == "knowledge" for e in value):
            raise ValueError("Validated knowledge must be retrieved from stored review history")
        return value
