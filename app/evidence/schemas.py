from datetime import datetime
from typing import Literal
from pydantic import Field, HttpUrl
from app.schemas import StrictModel, uid, now


class Evidence(StrictModel):
    evidence_id: str = Field(default_factory=uid)
    text: str = Field(min_length=1, max_length=50000)
    source: str = Field(min_length=1, max_length=500)
    source_type: Literal["document", "dataset", "web", "knowledge", "human"]
    url: HttpUrl | None = None
    retrieval_time: datetime = Field(default_factory=now)
    published_at: datetime | None = None
    relevance_score: float = Field(default=0, ge=0, le=1)
    source_quality: float = Field(default=0.5, ge=0, le=1)
    provenance: dict = Field(default_factory=dict)


class EvidenceAssessment(StrictModel):
    claim_id: str
    evidence_id: str
    verdict: Literal["SUPPORTS", "CONTRADICTS", "INSUFFICIENT"]
    confidence: float = Field(ge=0, le=1)
    method: str
    matched_text: str
