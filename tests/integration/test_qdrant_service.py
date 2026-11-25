import os
from uuid import uuid4

import pytest

from app.evidence import Evidence
from app.knowledge.store import Store
from app.retrieval.service import RetrievalService
from app.retrieval.vectors import QdrantVectors
from app.validation import ReviewRequest, ReviewService


@pytest.mark.skipif(not os.getenv("TEST_QDRANT_URL"), reason="Dedicated Qdrant service not configured")
def test_qdrant_retrieves_current_versions_and_filters_retired_memory():
    store = Store("sqlite:///:memory:", initialize=True)
    service = RetrievalService(store)
    service.vectors = QdrantVectors(os.environ["TEST_QDRANT_URL"], service.embeddings.dimension)
    with service.vectors.client as client:
        suffix = uuid4().hex
        service.collections = {kind: f"mahthildis_test_{kind}_{suffix}" for kind in ("knowledge", "evidence")}
        claim = "The Eiffel Tower was completed in 1889."
        evidence = Evidence(text=claim, source="registry", source_type="document")
        store.add_evidence(evidence)
        item = store.create_knowledge(claim)
        review = ReviewService(store)
        try:
            review.review(
                item["knowledge_id"],
                ReviewRequest(action="ACCEPT", expected_version=1, reviewer="tester", explanation="Verified"),
            )
            first = service.retrieve(claim)
            assert {entry.source_type for entry in first} == {"document", "knowledge"}
            assert next(entry for entry in first if entry.source_type == "knowledge").provenance["version"] == 2
            review.review(
                item["knowledge_id"],
                ReviewRequest(action="RETIRE", expected_version=2, reviewer="tester", explanation="Outdated"),
            )
            assert [entry.evidence_id for entry in service.retrieve(claim)] == [evidence.evidence_id]
        finally:
            for collection in service.collections.values():
                client.delete(f"collections/{collection}").raise_for_status()
