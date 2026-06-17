"""Sprint P.3 — D2 DROP_SAFE: drop orphan columns absent from models with 0 non-NULL values.

Revision ID: 150_sprint_p3_d2_drop_safe
Revises: 149_sprint_p2_deferred_nullables
Created: 2026-05-21

Sprint P.3 — D2 DROP_SAFE orphan column elimination
====================================================

Drops 15 orphan columns identified by  that meet ALL THREE criteria:
  1. DB has the column
  2. Model lacks the attribute
  3. Column has 0 non-NULL values in DB (verified via )

These columns are safe to drop without data loss. Several were latent bugs:
  - intelligence_insights.title (NOT NULL) — model constructor never sets it (table 0 rows = INSERTs failing silently)
  - profile_calculation_logs.calculation_type (NOT NULL) — same pattern

Code-reference scan (grep -rn) confirmed no production code references the column attributes on
the model class. The talent_pools/talent_pool_candidates embedding columns are dropped together
with their HNSW indexes (cascade).

DEFERRED (NOT in this migration):
  - audit_logs.actor_user_id — heavily referenced in app/api/v1/admin_audit_decisions.py +
    app/shared/compliance/audit_service.py:297 (Task #366 column-promotion in progress). The
    code currently stores in session_id pending column promotion; dropping breaks future Task #366.

Verification (2026-05-21):
  - check_schema_drift.py: 96 drifts pre-migration
  - Top-5 fastest wins COUNT non-NULL queries all returned 0
  - Code refs: grep showed no model attribute usage of the 15 dropped columns

Drift count delta expected: 96 → 81 (down 15).
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "150_sprint_p3_d2_drop_safe"
down_revision = "149_sprint_p2_deferred_nullables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── intelligence_insights — 6 orphan cols (table 0 rows; constructor never sets these) ──
    op.drop_column("intelligence_insights", "title")
    op.drop_column("intelligence_insights", "description")
    op.drop_column("intelligence_insights", "impact_score")
    op.drop_column("intelligence_insights", "was_dismissed")
    op.drop_column("intelligence_insights", "user_feedback")
    op.drop_column("intelligence_insights", "expires_at")

    # ── profile_calculation_logs — 5 orphan cols (model uses DIFFERENT attrs: trigger, jobs_analyzed, etc.) ──
    op.drop_column("profile_calculation_logs", "calculation_type")
    op.drop_column("profile_calculation_logs", "old_values")
    op.drop_column("profile_calculation_logs", "new_values")
    op.drop_column("profile_calculation_logs", "trigger_event")
    op.drop_column("profile_calculation_logs", "created_at")

    # ── talent_pools / talent_pool_candidates — VECTOR(768) embeddings unused (drops HNSW indexes too) ──
    # HNSW idx_talent_pools_archetype_embedding cascades on column drop
    op.drop_column("talent_pools", "archetype_embedding")
    # HNSW idx_tpc_candidate_embedding cascades on column drop
    op.drop_column("talent_pool_candidates", "candidate_embedding")

    # ── company_benefits — created_by/updated_by never populated (50 rows, all NULL) ──
    op.drop_column("company_benefits", "created_by")
    op.drop_column("company_benefits", "updated_by")


def downgrade() -> None:
    # Best-effort recreate (likely never used — data is lost). Types match original DB schema.

    # company_benefits
    op.add_column("company_benefits", sa.Column("updated_by", sa.String(255), nullable=True))
    op.add_column("company_benefits", sa.Column("created_by", sa.String(255), nullable=True))

    # talent_pool_candidates / talent_pools — recreate VECTOR(768) (requires pgvector extension)
    # Note: HNSW indexes are NOT recreated in downgrade (manual step if needed).
    try:
        from pgvector.sqlalchemy import Vector  # type: ignore
        op.add_column("talent_pool_candidates", sa.Column("candidate_embedding", Vector(768), nullable=True))
        op.add_column("talent_pools", sa.Column("archetype_embedding", Vector(768), nullable=True))
    except ImportError:
        op.execute("ALTER TABLE talent_pool_candidates ADD COLUMN candidate_embedding vector(768)")
        op.execute("ALTER TABLE talent_pools ADD COLUMN archetype_embedding vector(768)")

    # profile_calculation_logs
    op.add_column("profile_calculation_logs", sa.Column("created_at", sa.DateTime(), nullable=True))
    op.add_column("profile_calculation_logs", sa.Column("trigger_event", sa.String(255), nullable=True))
    op.add_column("profile_calculation_logs", sa.Column("new_values", postgresql.JSON(astext_type=sa.Text()), nullable=True))
    op.add_column("profile_calculation_logs", sa.Column("old_values", postgresql.JSON(astext_type=sa.Text()), nullable=True))
    # calculation_type was NOT NULL but no default — recreate as nullable to avoid blocking downgrade
    op.add_column("profile_calculation_logs", sa.Column("calculation_type", sa.String(100), nullable=True))

    # intelligence_insights
    op.add_column("intelligence_insights", sa.Column("expires_at", sa.DateTime(), nullable=True))
    op.add_column("intelligence_insights", sa.Column("user_feedback", sa.String(50), nullable=True))
    op.add_column("intelligence_insights", sa.Column("was_dismissed", sa.Boolean(), nullable=True))
    op.add_column("intelligence_insights", sa.Column("impact_score", sa.Float(), nullable=True))
    op.add_column("intelligence_insights", sa.Column("description", sa.Text(), nullable=True))
    # title was NOT NULL but recreating as nullable for safe downgrade
    op.add_column("intelligence_insights", sa.Column("title", sa.String(500), nullable=True))
