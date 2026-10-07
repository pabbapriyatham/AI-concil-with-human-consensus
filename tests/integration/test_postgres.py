"""Opt-in checks against a dedicated PostgreSQL test database."""

import os

import pytest
from sqlalchemy import text

from app.knowledge.store import Store


@pytest.mark.skipif(not os.getenv("TEST_DATABASE_URL"), reason="Dedicated PostgreSQL service not configured")
def test_postgresql_migration_and_versions():
    store = Store(os.getenv("TEST_DATABASE_URL"), initialize=True)
    assert store.engine.dialect.name == "postgresql"
    item = store.create_knowledge("Integration fixture happened in 2020.")
    store.append_version(
        item["knowledge_id"], 1, {"status": "DISPUTED"}, "test reviewer", "integration check"
    )
    assert len(store.history(item["knowledge_id"])) == 2
    with store.engine.connect() as conn:
        assert conn.execute(text("select version_num from alembic_version")).scalar_one() == "0001"
