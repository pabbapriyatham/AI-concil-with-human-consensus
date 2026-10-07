from typing import Literal

from pydantic import Field, model_validator

from app.evidence.schemas import Evidence
from app.schemas import StrictModel, now


class ReviewRequest(StrictModel):
    action: Literal["ACCEPT", "CORRECT", "REJECT", "MARK_UNCERTAIN", "ADD_EVIDENCE", "ADD_EXPLANATION"]
    expected_version: int = Field(ge=1)
    reviewer: str = Field(min_length=1, max_length=200)
    explanation: str = Field(min_length=1, max_length=10000)
    corrected_claim: str | None = Field(default=None, min_length=1, max_length=10000)
    evidence: list[Evidence] = Field(default_factory=list, max_length=20)

    @model_validator(mode="after")
    def check_action(self):
        if any(e.source_type == "knowledge" for e in self.evidence):
            raise ValueError("Knowledge evidence must come from validated stored history")
        if self.action == "CORRECT" and not self.corrected_claim:
            raise ValueError("A correction requires corrected_claim")
        if self.action == "ADD_EVIDENCE" and not self.evidence:
            raise ValueError("ADD_EVIDENCE requires evidence")
        return self


class ReviewService:
    def __init__(self, store):
        self.store = store

    def review(self, knowledge_id, request):
        old = self.store.current(knowledge_id)
        if old is None:
            raise KeyError(knowledge_id)
        changes = {}
        if request.action in {"ACCEPT", "CORRECT"}:
            changes.update(status="VALIDATED", validation_state="human-reviewed", confidence=0.9)
        elif request.action == "REJECT":
            changes.update(status="REJECTED", validation_state="human-rejected", confidence=0)
        elif request.action == "MARK_UNCERTAIN":
            changes.update(status="DISPUTED", validation_state="human-uncertain", confidence=0.25)
        if request.action == "CORRECT":
            changes["claim"] = request.corrected_claim
        if request.evidence:
            changes["evidence"] = old["evidence"] + [e.model_dump(mode="json") for e in request.evidence]
        audit = {
            "action": request.action,
            "reviewer": request.reviewer,
            "explanation": request.explanation,
            "timestamp": now().isoformat(),
            "expected_version": request.expected_version,
            "original_claim": old["claim"],
            "corrected_claim": request.corrected_claim,
            "evidence": [e.model_dump(mode="json") for e in request.evidence],
        }
        # Version update + validation audit share one transaction.
        result = self.store.append_version(
            knowledge_id, request.expected_version, changes, request.reviewer, request.explanation, audit
        )
        for item in request.evidence:
            self.store.add_evidence(item)
        return result
