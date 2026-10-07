import pytest

from app.knowledge.store import StaleVersion, Store


def test_versioning_and_stale_updates():
    store = Store("sqlite:///:memory:", initialize=True)
    item = store.create_knowledge("The event happened in 2020.")
    updated = store.append_version(
        item["knowledge_id"],
        1,
        {"claim": "The event happened in 2021.", "status": "VALIDATED"},
        "reviewer",
        "Official record",
    )
    assert updated["version"] == 2 and updated["previous_version"] == 1
    assert store.history(item["knowledge_id"])[0]["claim"].endswith("2020.")
    assert store.current(item["knowledge_id"])["status"] == "VALIDATED"
    with pytest.raises(StaleVersion):
        store.append_version(item["knowledge_id"], 1, {}, "reviewer", "stale")
    assert len(store.history(item["knowledge_id"])) == 2
