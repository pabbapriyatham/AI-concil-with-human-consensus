"""Initial structured source of truth. Immutable schema snapshot."""
from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None


def upgrade():
    op.create_table("users", sa.Column("id", sa.String(36), primary_key=True), sa.Column("name", sa.String(200), nullable=False))
    op.create_table("questions", sa.Column("id", sa.String(36), primary_key=True), sa.Column("content", sa.String(), nullable=False), sa.Column("payload", sa.JSON(), nullable=False))
    op.create_table("executions", sa.Column("id", sa.String(36), primary_key=True), sa.Column("question_id", sa.String(36), sa.ForeignKey("questions.id"), nullable=False), sa.Column("payload", sa.JSON(), nullable=False))
    op.create_table("models", sa.Column("id", sa.String(200), primary_key=True), sa.Column("provider", sa.String(50), nullable=False), sa.Column("name", sa.String(200), nullable=False))
    for name in ["model_responses", "claim_relations"]:
        op.create_table(name, sa.Column("id", sa.String(36), primary_key=True), sa.Column("execution_id", sa.String(36), sa.ForeignKey("executions.id"), nullable=False), sa.Column("payload", sa.JSON(), nullable=False))
    op.create_table("claims", sa.Column("id", sa.String(36), primary_key=True), sa.Column("execution_id", sa.String(36), sa.ForeignKey("executions.id"), nullable=False), sa.Column("response_id", sa.String(36), sa.ForeignKey("model_responses.id"), nullable=False), sa.Column("payload", sa.JSON(), nullable=False))
    op.create_table("evidence", sa.Column("id", sa.String(36), primary_key=True), sa.Column("source", sa.String(500), nullable=False), sa.Column("payload", sa.JSON(), nullable=False))
    op.create_table("knowledge_items", sa.Column("id", sa.String(36), primary_key=True), sa.Column("current_version", sa.Integer(), nullable=False))
    op.create_table("knowledge_versions", sa.Column("id", sa.String(36), primary_key=True), sa.Column("knowledge_id", sa.String(36), sa.ForeignKey("knowledge_items.id"), nullable=False), sa.Column("version", sa.Integer(), nullable=False), sa.Column("status", sa.String(20), nullable=False), sa.Column("normalized_claim", sa.String(), nullable=False), sa.Column("payload", sa.JSON(), nullable=False), sa.UniqueConstraint("knowledge_id", "version", name="uq_knowledge_version"))
    op.create_table("validations", sa.Column("id", sa.String(36), primary_key=True), sa.Column("knowledge_id", sa.String(36), sa.ForeignKey("knowledge_items.id"), nullable=False), sa.Column("payload", sa.JSON(), nullable=False))
    op.create_table("experiments", sa.Column("id", sa.String(36), primary_key=True), sa.Column("payload", sa.JSON(), nullable=False))
    op.create_table("metrics", sa.Column("id", sa.String(36), primary_key=True), sa.Column("experiment_id", sa.String(36), sa.ForeignKey("experiments.id"), nullable=False), sa.Column("name", sa.String(100), nullable=False), sa.Column("value", sa.Float(), nullable=False))


def downgrade():
    for name in ["metrics", "experiments", "validations", "knowledge_versions", "knowledge_items",
                 "evidence", "claims", "claim_relations", "model_responses", "models", "executions", "questions", "users"]:
        op.drop_table(name)
