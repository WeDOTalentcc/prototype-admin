"""
Migration 055: Create talent_pools tables for FastAPI.

Mirror of Rails tables — used for embedding generation and AI search.
Only the fields needed by FastAPI are included (not full Rails schema).

Applies to: lia-agent-system (Replit)
Path: app/migrations/versions/055_create_talent_pools.py
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID, ARRAY
from pgvector.sqlalchemy import Vector


revision = "055"
down_revision = "054"
branch_labels = None
depends_on = None


def upgrade():
    # Talent pools — lightweight mirror for AI/search operations
    op.create_table(
        "talent_pools",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("company_id", sa.String(64), nullable=False, index=True),
        sa.Column("name", sa.String(256), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("status", sa.String(16), nullable=False, server_default="active"),
        sa.Column("archetype_id", sa.String(64), nullable=True),  # maps to ideal_profile_id in Rails

        # Screening config (Modo Compacto WSI)
        sa.Column("screening_questions", JSONB, server_default="[]"),
        sa.Column("screening_config", JSONB, server_default="{}"),

        # Agent config
        sa.Column("agent_sourcing_enabled", sa.Boolean, server_default="false"),
        sa.Column("agent_config", JSONB, server_default="{}"),

        # Archetype embedding (for semantic matching)
        sa.Column("archetype_embedding", Vector(768), nullable=True),

        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    op.create_index("idx_talent_pools_company_status", "talent_pools", ["company_id", "status"])

    # Talent pool candidates — links candidate to pool with AI metadata
    op.create_table(
        "talent_pool_candidates",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("talent_pool_id", UUID(as_uuid=True), sa.ForeignKey("talent_pools.id", ondelete="CASCADE"), nullable=False),
        sa.Column("candidate_id", sa.String(64), nullable=False),  # Rails candidate ID as string

        sa.Column("stage", sa.String(16), nullable=False, server_default="discovered"),
        sa.Column("origin", sa.String(16), nullable=False, server_default="manual"),
        sa.Column("fit_score", sa.Float, nullable=True),

        # AI-generated match data (populated by LIA during sourcing/calibration)
        sa.Column("match_criteria", JSONB, server_default="{}"),  # why matched
        sa.Column("screening_data", JSONB, server_default="{}"),  # answers + scores
        sa.Column("candidate_embedding", Vector(768), nullable=True),  # for similarity search within pool

        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    op.create_index(
        "idx_tpc_pool_candidate",
        "talent_pool_candidates",
        ["talent_pool_id", "candidate_id"],
        unique=True,
    )
    op.create_index("idx_tpc_stage", "talent_pool_candidates", ["talent_pool_id", "stage"])

    # HNSW index for candidate embedding similarity search within pools
    op.execute("""
        CREATE INDEX idx_tpc_candidate_embedding
        ON talent_pool_candidates
        USING hnsw (candidate_embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64)
    """)


def downgrade():
    op.drop_table("talent_pool_candidates")
    op.drop_table("talent_pools")
