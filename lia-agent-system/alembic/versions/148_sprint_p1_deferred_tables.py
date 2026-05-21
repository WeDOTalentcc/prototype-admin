"""Sprint P.1 — deferred tables from Sprint G migration 143.

Revision ID: 148_sprint_p1_deferred_tables
Revises: 147_t19_b2_bandit_posterior
Create Date: 2026-05-21

Adds 24 nullable columns deferred by Sprint G across 3 tables:

1. whatsapp_conversations (13 cols) — pre-qualification + eligibility + reconsideration
   + existing-candidate detection fields. All nullable / have defaults.

2. profile_calculation_logs (9 cols) — recruiter profile recalculation audit fields.
   Adds trigger (NOT NULL, no server_default safe because table is empty;
   existing legacy column trigger_event kept untouched).

3. ai_consumption (2 cols) — agent_category (NOT NULL, server_default=core
   to allow safe migration over existing rows) + studio_agent_id (nullable),
   both indexed per canonical model declaration.

Tables verified empty at migration time (row_count=0 each), so NOT NULL adds are safe
even without server_default. Server defaults applied where model declares default=
to preserve canonical semantics.

REGRA ZERO: Replit-only, branch feat/benefits-prv-canonical. No GitHub push.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "148_sprint_p1_deferred_tables"
down_revision = "147_t19_b2_bandit_posterior"
branch_labels = None
depends_on = None


def upgrade():
    # ===== whatsapp_conversations =====
    # Pre-qualification (rubric) fields — Phase 1 PRE_QUALIFICATION state
    op.add_column("whatsapp_conversations", sa.Column("pre_qualification_score", sa.Integer(), nullable=True))
    op.add_column("whatsapp_conversations", sa.Column("pre_qualification_result", sa.String(length=50), nullable=True))
    op.add_column("whatsapp_conversations", sa.Column("pre_qualification_matched", sa.JSON(), nullable=True))
    op.add_column("whatsapp_conversations", sa.Column("pre_qualification_missing", sa.JSON(), nullable=True))
    op.add_column("whatsapp_conversations", sa.Column("pre_qualification_decision", sa.String(length=50), nullable=True))
    op.add_column("whatsapp_conversations", sa.Column("pre_qualification_at", sa.DateTime(timezone=True), nullable=True))

    # Eligibility check + reconsideration flow fields
    op.add_column("whatsapp_conversations", sa.Column("eligibility_answers", sa.JSON(), nullable=True))
    op.add_column("whatsapp_conversations", sa.Column("eligibility_question_index", sa.Integer(), nullable=True, server_default="0"))
    op.add_column("whatsapp_conversations", sa.Column("reconsideration_count", sa.Integer(), nullable=True, server_default="0"))
    op.add_column("whatsapp_conversations", sa.Column("reconsideration_context", sa.JSON(), nullable=True))
    op.add_column("whatsapp_conversations", sa.Column("had_reconsiderations", sa.Boolean(), nullable=True, server_default=sa.false()))

    # Existing-candidate detection fields
    op.add_column("whatsapp_conversations", sa.Column("is_existing_candidate", sa.Boolean(), nullable=True, server_default=sa.false()))
    op.add_column("whatsapp_conversations", sa.Column("existing_candidate_since", sa.DateTime(timezone=True), nullable=True))

    # ===== profile_calculation_logs =====
    # Trigger + analysis counters (table empty, NOT NULL safe)
    op.add_column("profile_calculation_logs", sa.Column("trigger", sa.String(length=50), nullable=False, server_default="manual"))
    op.add_column("profile_calculation_logs", sa.Column("jobs_analyzed", sa.Integer(), nullable=True, server_default="0"))
    op.add_column("profile_calculation_logs", sa.Column("corrections_analyzed", sa.Integer(), nullable=True, server_default="0"))
    op.add_column("profile_calculation_logs", sa.Column("outcomes_analyzed", sa.Integer(), nullable=True, server_default="0"))

    # Changes + snapshots (audit trail)
    op.add_column("profile_calculation_logs", sa.Column("changes_detected", sa.JSON(), nullable=True))
    op.add_column("profile_calculation_logs", sa.Column("previous_profile_snapshot", sa.JSON(), nullable=True))
    op.add_column("profile_calculation_logs", sa.Column("new_profile_snapshot", sa.JSON(), nullable=True))

    # Timing fields
    op.add_column("profile_calculation_logs", sa.Column("calculated_at", sa.DateTime(), nullable=True, server_default=sa.func.now()))
    op.add_column("profile_calculation_logs", sa.Column("calculation_time_ms", sa.Integer(), nullable=True))

    # Drop server_default for trigger after backfill (canonical: model has no default,
    # server_default was only a migration scaffold for tables that might have rows).
    # Table verified empty, but defensive ALTER kept for consistency.
    op.alter_column("profile_calculation_logs", "trigger", server_default=None)

    # ===== ai_consumption =====
    # agent_category NOT NULL with server_default=core (canonical model has default=core).
    # Server default kept so future INSERTs without explicit value work (matches ORM behavior).
    op.add_column(
        "ai_consumption",
        sa.Column("agent_category", sa.String(length=20), nullable=False, server_default="core"),
    )
    op.add_column("ai_consumption", sa.Column("studio_agent_id", sa.String(length=64), nullable=True))

    # Indexes — both cols are index=True in model
    op.create_index("ix_ai_consumption_agent_category", "ai_consumption", ["agent_category"])
    op.create_index("ix_ai_consumption_studio_agent_id", "ai_consumption", ["studio_agent_id"])


def downgrade():
    # ===== ai_consumption (reverse order) =====
    op.drop_index("ix_ai_consumption_studio_agent_id", table_name="ai_consumption")
    op.drop_index("ix_ai_consumption_agent_category", table_name="ai_consumption")
    op.drop_column("ai_consumption", "studio_agent_id")
    op.drop_column("ai_consumption", "agent_category")

    # ===== profile_calculation_logs (reverse order) =====
    op.drop_column("profile_calculation_logs", "calculation_time_ms")
    op.drop_column("profile_calculation_logs", "calculated_at")
    op.drop_column("profile_calculation_logs", "new_profile_snapshot")
    op.drop_column("profile_calculation_logs", "previous_profile_snapshot")
    op.drop_column("profile_calculation_logs", "changes_detected")
    op.drop_column("profile_calculation_logs", "outcomes_analyzed")
    op.drop_column("profile_calculation_logs", "corrections_analyzed")
    op.drop_column("profile_calculation_logs", "jobs_analyzed")
    op.drop_column("profile_calculation_logs", "trigger")

    # ===== whatsapp_conversations (reverse order) =====
    op.drop_column("whatsapp_conversations", "existing_candidate_since")
    op.drop_column("whatsapp_conversations", "is_existing_candidate")
    op.drop_column("whatsapp_conversations", "had_reconsiderations")
    op.drop_column("whatsapp_conversations", "reconsideration_context")
    op.drop_column("whatsapp_conversations", "reconsideration_count")
    op.drop_column("whatsapp_conversations", "eligibility_question_index")
    op.drop_column("whatsapp_conversations", "eligibility_answers")
    op.drop_column("whatsapp_conversations", "pre_qualification_at")
    op.drop_column("whatsapp_conversations", "pre_qualification_decision")
    op.drop_column("whatsapp_conversations", "pre_qualification_missing")
    op.drop_column("whatsapp_conversations", "pre_qualification_matched")
    op.drop_column("whatsapp_conversations", "pre_qualification_result")
    op.drop_column("whatsapp_conversations", "pre_qualification_score")
