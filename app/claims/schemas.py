from typing import Literal
from pydantic import Field
from app.schemas import StrictModel, uid

ClaimType = Literal["factual", "numerical", "temporal", "causal", "opinion",
                    "recommendation", "procedural", "uncertain"]


class Claim(StrictModel):
    claim_id: str = Field(default_factory=uid)
    response_id: str
    model: str
    claim_text: str = Field(min_length=1, max_length=10000)
    normalized_claim: str
    claim_type: ClaimType
    provenance: dict = Field(default_factory=dict)
