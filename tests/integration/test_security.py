from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.api import get_store
from app.evidence import Evidence
from app.knowledge.store import Store
from app.validation import ReviewRequest
from backend import storage
from backend.main import app


def test_storage_path_and_metadata(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "DATA_DIR", str(tmp_path))
    with pytest.raises(ValueError):
        storage.get_conversation_path("../../secrets")
    identity = str(uuid4())
    storage.create_conversation(identity)
    storage.add_user_message(identity, "été")
    storage.add_assistant_message(identity, [], [], {"response": "reply"}, {"labels": {"A": "model"}})
    conversation = storage.get_conversation(identity)
    assert conversation["messages"][0]["content"] == "été"
    assert conversation["messages"][1]["metadata"]["labels"]["A"] == "model"
    assert not list(tmp_path.glob("*.tmp"))


def test_optional_auth_and_trace(monkeypatch):
    monkeypatch.setenv("API_TOKEN", "test-access-token")
    monkeypatch.setenv("DEV_MODE", "true")
    store = Store("sqlite:///:memory:", initialize=True)
    app.dependency_overrides[get_store] = lambda: store
    try:
        client = TestClient(app)
        assert client.get("/api/consensus/config").status_code == 401
        response = client.post(
            "/api/consensus/executions",
            headers={"Authorization": "Bearer test-access-token"},
            json={"question": "When was the Eiffel Tower completed?"},
        )
        assert response.status_code == 200
        assert response.headers["X-Request-ID"] == response.json()["request_id"]
    finally:
        app.dependency_overrides.clear()


def test_untrusted_memory_and_timezone_rejected():
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        ReviewRequest(
            action="ADD_EVIDENCE",
            expected_version=1,
            reviewer="r",
            explanation="reason",
            evidence=[
                Evidence(
                    text="Claim", source="fake", source_type="knowledge", provenance={"status": "VALIDATED"}
                )
            ],
        )
    with pytest.raises(ValidationError):
        Evidence(text="Claim", source="s", source_type="document", published_at="2020-01-01T00:00:00")
