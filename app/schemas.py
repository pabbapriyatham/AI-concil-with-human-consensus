from datetime import datetime, timezone
from uuid import uuid4
from pydantic import BaseModel, ConfigDict, Field


def uid():
    return str(uuid4())


def now():
    return datetime.now(timezone.utc)


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class TokenUsage(StrictModel):
    input_tokens: int | None = Field(default=None, ge=0)
    output_tokens: int | None = Field(default=None, ge=0)


class ModelResponse(StrictModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    response_id: str = Field(default_factory=uid)
    question_id: str
    provider: str
    model: str
    raw_text: str
    normalized_text: str
    timestamp: datetime = Field(default_factory=now)
    latency: float = Field(ge=0)
    token_usage: TokenUsage
    cost: float | None = Field(default=None, ge=0)
    metadata: dict = Field(default_factory=dict)
