import asyncio

import pytest
from fastapi.testclient import TestClient

from app.api import get_store
from app.evidence import Evidence
from app.knowledge.store import Store
from app.orchestration import ConsensusEngine, ConsensusRequest
from app.orchestration.schemas import ModelSpec
from app.retrieval import RetrievalService
from app.validation import ReviewRequest, ReviewService
from backend.main import app


def test_end_to_end_and_memory(monkeypatch):
    monkeypatch.setenv("DEV_MODE", "true")
    store = Store("sqlite:///:memory:", initialize=True)
    request = ConsensusRequest(
        question="When was the Eiffel Tower completed?",
        evidence=[
            Evidence(
                text="The Eiffel Tower was completed in 1889. The Eiffel Tower is located in Paris.",
                source="supplied test record",
                source_type="document",
                source_quality=1,
            )
        ],
    )
    result = asyncio.run(ConsensusEngine(store).run(request))
    assert len(result["responses"]) == 3
    assert any(r["relation_type"] == "CONTRADICTION" for r in result["relations"])
    assert "1889" in result["synthesis"]["text"]
    assert "Supports · supplied test record" in result["synthesis"]["text"]
    assert result["review"]["required"] and store.execution(result["request_id"]) == result
    assert result["execution"]["total_cost"] == 0
    wrong = next(k for k in result["review"]["items"] if "1888" in k["claim"])
    ReviewService(store).review(
        wrong["knowledge_id"],
        ReviewRequest(
            action="CORRECT",
            expected_version=1,
            reviewer="human",
            explanation="Corrected from official record",
            corrected_claim="The Eiffel Tower was completed in 1889.",
        ),
    )
    future = asyncio.run(ConsensusEngine(store).run(request))
    assert future["synthesis"]["knowledge_used"]
    assert "previously human-validated" in future["synthesis"]["text"]


def test_api_input_and_review(monkeypatch):
    monkeypatch.setenv("DEV_MODE", "true")
    store = Store("sqlite:///:memory:", initialize=True)
    app.dependency_overrides[get_store] = lambda: store
    try:
        client = TestClient(app)
        assert client.post("/api/consensus/executions", json={"question": " "}).status_code == 422
        response = client.post(
            "/api/consensus/executions", json={"question": "When was the Eiffel Tower completed?"}
        )
        assert response.status_code == 200
        item = response.json()["review"]["items"][0]
        url = f"/api/consensus/knowledge/{item['knowledge_id']}/review"
        data = {
            "action": "ACCEPT",
            "expected_version": 1,
            "reviewer": "human",
            "explanation": "Checked source",
        }
        assert client.post(url, json=data).status_code == 200
        assert client.post(url, json=data).status_code == 409
        assert len(client.get(f"/api/consensus/knowledge/{item['knowledge_id']}/history").json()) == 2
    finally:
        app.dependency_overrides.clear()


def test_escalation_bounded(monkeypatch):
    monkeypatch.setenv("DEV_MODE", "true")
    store = Store("sqlite:///:memory:", initialize=True)
    request = ConsensusRequest(
        question="Unknown question",
        mode="CHEAP",
        models=[ModelSpec(provider="mock", model=f"m{i}") for i in range(5)],
    )
    result = asyncio.run(ConsensusEngine(store).run(request))
    assert len(result["execution"]["models_consulted"]) == 3
    assert result["review"]["required"]
    assert result["confidence"]["raw_confidence"] < 0.5
    assert "insufficient" in result["synthesis"]["text"]


def test_request_evidence_stays_out_of_document_corpus(monkeypatch):
    monkeypatch.setenv("DEV_MODE", "true")
    store = Store("sqlite:///:memory:", initialize=True)
    retrieval = RetrievalService(store)
    statement = "The Eiffel Tower was completed in 1889."
    old_context = retrieval.ingest(statement, "request context 11111111-1111-1111-1111-111111111111")[0]
    durable = retrieval.ingest(statement, "Reviewed reference")[0]
    attached = Evidence(text=statement, source="One-off attachment", source_type="document")
    request = ConsensusRequest(question=statement, context=statement, evidence=[attached])

    result = asyncio.run(ConsensusEngine(store).run(request))
    current_sources = {item["source"] for item in result["evidence"]}
    assert "One-off attachment" in current_sources
    assert any(source.startswith("request context ") for source in current_sources)
    assert {item.evidence_id for item in retrieval.retrieve(statement)} == {durable.evidence_id}
    assert {item["evidence_id"] for item in store.list_evidence()} == {
        old_context.evidence_id,
        durable.evidence_id,
    }


def test_startup_rejects_invalid_price_configuration(monkeypatch):
    monkeypatch.setenv("MODEL_PRICES_JSON", "not JSON")
    with pytest.raises(ValueError, match="^MODEL_PRICES_JSON must map"):
        with TestClient(app):
            pytest.fail("Server started with invalid pricing configuration")
