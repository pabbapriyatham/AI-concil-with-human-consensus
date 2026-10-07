import os
from pathlib import Path
from sqlalchemy import create_engine, MetaData, Table, Column, String, Integer, JSON, ForeignKey, Float, UniqueConstraint, event
from sqlalchemy.pool import StaticPool

metadata = MetaData()
users = Table("users", metadata, Column("id", String(36), primary_key=True), Column("name", String(200), nullable=False))
questions = Table("questions", metadata, Column("id", String(36), primary_key=True), Column("content", String, nullable=False), Column("payload", JSON, nullable=False))
executions = Table("executions", metadata, Column("id", String(36), primary_key=True), Column("question_id", ForeignKey("questions.id"), nullable=False), Column("payload", JSON, nullable=False))
models = Table("models", metadata, Column("id", String(200), primary_key=True), Column("provider", String(50), nullable=False), Column("name", String(200), nullable=False))
responses = Table("model_responses", metadata, Column("id", String(36), primary_key=True), Column("execution_id", ForeignKey("executions.id"), nullable=False), Column("payload", JSON, nullable=False))
claims = Table("claims", metadata, Column("id", String(36), primary_key=True), Column("execution_id", ForeignKey("executions.id"), nullable=False), Column("response_id", ForeignKey("model_responses.id"), nullable=False), Column("payload", JSON, nullable=False))
relations = Table("claim_relations", metadata, Column("id", String(36), primary_key=True), Column("execution_id", ForeignKey("executions.id"), nullable=False), Column("payload", JSON, nullable=False))
evidence = Table("evidence", metadata, Column("id", String(36), primary_key=True), Column("source", String(500), nullable=False), Column("payload", JSON, nullable=False))
knowledge_items = Table("knowledge_items", metadata, Column("id", String(36), primary_key=True), Column("current_version", Integer, nullable=False))
knowledge_versions = Table("knowledge_versions", metadata, Column("id", String(36), primary_key=True), Column("knowledge_id", ForeignKey("knowledge_items.id"), nullable=False), Column("version", Integer, nullable=False), Column("status", String(20), nullable=False), Column("normalized_claim", String, nullable=False), Column("payload", JSON, nullable=False), UniqueConstraint("knowledge_id", "version", name="uq_knowledge_version"))
validations = Table("validations", metadata, Column("id", String(36), primary_key=True), Column("knowledge_id", ForeignKey("knowledge_items.id"), nullable=False), Column("payload", JSON, nullable=False))
experiments = Table("experiments", metadata, Column("id", String(36), primary_key=True), Column("payload", JSON, nullable=False))
metrics = Table("metrics", metadata, Column("id", String(36), primary_key=True), Column("experiment_id", ForeignKey("experiments.id"), nullable=False), Column("name", String(100), nullable=False), Column("value", Float, nullable=False))


def make_engine(url=None):
    url = url or os.getenv("DATABASE_URL", "sqlite:///data/mahthildis.db")
    if url.startswith("sqlite:///") and url != "sqlite:///:memory:":
        Path(url.removeprefix("sqlite:///")).parent.mkdir(parents=True, exist_ok=True)
    kwargs = {"pool_pre_ping": True}
    if url == "sqlite:///:memory:":
        kwargs.update(poolclass=StaticPool, connect_args={"check_same_thread": False})
    engine = create_engine(url, **kwargs)
    if url.startswith("sqlite"):
        @event.listens_for(engine, "connect")
        def set_sqlite_pragmas(connection, _):
            connection.execute("PRAGMA foreign_keys=ON")
    return engine


def migrate(engine):
    """Use the same tracked Alembic migration in tests and development."""
    from alembic.config import Config
    from alembic import command
    config = Config(str(Path(__file__).resolve().parents[2] / "alembic.ini"))
    config.set_main_option("script_location", str(Path(__file__).resolve().parents[2] / "migrations"))
    with engine.begin() as connection:
        config.attributes["connection"] = connection
        command.upgrade(config, "head")
