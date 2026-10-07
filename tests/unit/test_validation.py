import pytest
from pydantic import ValidationError
from sqlalchemy import select

from app.knowledge.database import validations
from app.knowledge.store import Store
from app.validation import ReviewRequest, ReviewService


def test_complete_review_history():
    store = Store("sqlite:///:memory:", initialize=True)
    item = store.create_knowledge("The event happened in 2020.")
    service = ReviewService(store)
    corrected = service.review(
        item["knowledge_id"],
        ReviewRequest(
            action="CORRECT",
            expected_version=1,
            reviewer="human",
            explanation="Official record confirms 2021",
            corrected_claim="The event happened in 2021.",
        ),
    )
    assert corrected["status"] == "VALIDATED" and corrected["version"] == 2
    assert store.history(item["knowledge_id"])[0]["claim"].endswith("2020.")
    rejected = service.review(
        item["knowledge_id"],
        ReviewRequest(
            action="REJECT", expected_version=2, reviewer="human", explanation="New source disputes this"
        ),
    )
    assert rejected["status"] == "REJECTED"
    with store.engine.connect() as conn:
        audits = list(conn.execute(select(validations.c.payload)).scalars())
    assert len(audits) == 2 and audits[0]["original_claim"].endswith("2020.")


def test_required_correction():
    with pytest.raises(ValidationError):
        ReviewRequest(action="CORRECT", expected_version=1, reviewer="human", explanation="reason")
