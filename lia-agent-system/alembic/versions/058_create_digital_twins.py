"""
Migration 058: Create digital_twins and twin_decisions tables.

Digital Twins capture the decision-making reasoning of a Subject Matter Expert (SME)
and use it to evaluate new candidates via RAG few-shot prompting.

Based on Eightfold Project Andromeda pattern.

Applies to: lia-agent-system (Replit)
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID, ARRAY
from pgvector.sqlalchemy import Vector


revision = "058"
down_revision = "057"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "digital_twins",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("company_id", sa.String(64), nullable=False, index=True),
        sa.Column("twin_name", sa.String(256), nullable=False),  # "Ana Costa — Eng. Sênior"
        sa.Column("sme_user_id", sa.String(64), nullable=True),  # user who this twin models

        sa.Column("specialties", ARRAY(sa.String), server_default="{}"),  # ["backend", "data", "cloud"]
        sa.Column("description", sa.Text, nullable=True),

        # Performance metrics
        sa.Column("decision_count", sa.Integer, server_default="0"),
        sa.Column("accuracy_pct", sa.Float, nullable=True),  # calibrated over time
        sa.Column("is_active", sa.Boolean, server_default="true"),

        # Aggregated embedding of all decisions (centroid of decision space)
        sa.Column("twin_embedding", Vector(768), nullable=True),

        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    op.create_index("idx_twins_company", "digital_twins", ["company_id", "is_active"])

    op.create_table(
        "twin_decisions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("twin_id", UUID(as_uuid=True), sa.ForeignKey("digital_twins.id", ondelete="CASCADE"), nullable=False),

        sa.Column("decision", sa.String(16), nullable=False),  # approved, rejected, maybe
        sa.Column("reasoning", sa.Text, nullable=False),  # SME's explanation of why

        sa.Column("candidate_snapshot", JSONB, nullable=True),  # profile at time of decision
        sa.Column("job_snapshot", JSONB, nullable=True),  # job context at time of decision

        # Embedding of reasoning+profile combined (for K-NN retrieval)
        sa.Column("embedding", Vector(768), nullable=True),

        sa.Column("source", sa.String(32), server_default="'ats_history'"),  # ats_history, audio, manual
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )

    op.create_index("idx_twin_decisions_twin", "twin_decisions", ["twin_id", "decision"])

    # HNSW index for semantic similarity search across twin decisions
    op.execute("""
        CREATE INDEX idx_twin_decisions_embedding
        ON twin_decisions
        USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64)
    """)


def downgrade():
    op.drop_table("twin_decisions")
    op.drop_table("digital_twins")
