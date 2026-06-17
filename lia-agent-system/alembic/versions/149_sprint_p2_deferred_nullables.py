"""Sprint P.2 — deferred nullable canonical columns (webhook_logs / pattern_cache / recruiter_field_preferences).

Revision ID: 149_sprint_p2_deferred_nullables
Revises: 148_sprint_p1_deferred_tables
Create Date: 2026-05-21

Picks up the canonical nullable adds explicitly deferred by Sprint 140/143:

  - webhook_logs                (Sprint F.8 skip-list)        +4 cols  [0 rows]
  - pattern_cache               (Sprint F+G skip-list)        +1 col   [0 rows]
  - recruiter_field_preferences (Sprint F+G skip-list)        +14 cols [0 rows]

Total: 19 columns. All target tables have 0 rows (audited 2026-05-21 via
inspect()), so server_defaults are pure formality but kept for parity with
the canonical model defaults declared in libs/models/lia_models/*.py.

Selection criteria honored:
  - All cols nullable in DB (we add nullable=True even where model says
    nullable=False, because columns are added on existing tables with 0 rows
    and follow-up P0 batch will tighten NOT NULL where needed). The single
    exception is webhook_logs.attempt: model says nullable=False default=1,
    and DB has 0 rows, so we add NOT NULL DEFAULT 1 directly — safe.
  - No FK columns added.
  - No tables >100k rows.
  - Tables already covered by 143 (ats_connections, intelligence_insights,
    personalization_settings, etc.) intentionally NOT included.
  - Tables claimed by Sprint P.1 (whatsapp_conversations, profile_calculation_logs,
    ai_consumption) intentionally NOT included even though P.1 migration 148
    shipped as a no-op claim.

Expected drift reduction: 96 -> ~77 (−19).
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "149_sprint_p2_deferred_nullables"
down_revision = "148_sprint_p1_deferred_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ---------------------------------------------------------------------
    # 1. webhook_logs (0 rows) — 4 canonical cols missing
    # Model: libs/models/lia_models/webhook.py:91 WebhookLog
    # ---------------------------------------------------------------------
    op.add_column(
        "webhook_logs",
        sa.Column("request_body", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.add_column(
        "webhook_logs",
        sa.Column("error", sa.Text(), nullable=True),
    )
    # Model: attempt = Column(Integer, default=1, nullable=False)
    # Table has 0 rows -> safe to add NOT NULL with server_default.
    op.add_column(
        "webhook_logs",
        sa.Column("attempt", sa.Integer(), nullable=False, server_default="1"),
    )
    # Model: created_at = Column(DateTime(timezone=True), server_default=func.now())
    op.add_column(
        "webhook_logs",
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=True,
            server_default=sa.text("now()"),
        ),
    )

    # ---------------------------------------------------------------------
    # 2. pattern_cache (0 rows) — 1 col missing (140 added the NOT NULL ones)
    # Model: libs/models/lia_models/intelligence_layer.py:98 PatternCache
    # updated_at = Column(DateTime, default=datetime.utcnow, onupdate=...)
    # ---------------------------------------------------------------------
    op.add_column(
        "pattern_cache",
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=True,
            server_default=sa.text("now()"),
        ),
    )

    # ---------------------------------------------------------------------
    # 3. recruiter_field_preferences (0 rows) — 14 canonical cols missing
    # Model: libs/models/lia_models/recruiter_profile.py:118
    # All nullable=True in this migration (table empty; P0 NOT NULL tightening
    # deferred). recruiter_id is nullable=False in model but we ADD nullable=True
    # to be safe across future loaders; P0 sprint can tighten with backfill.
    # ---------------------------------------------------------------------
    op.add_column(
        "recruiter_field_preferences",
        sa.Column("recruiter_id", sa.String(255), nullable=True),
    )
    op.add_column(
        "recruiter_field_preferences",
        sa.Column("total_encounters", sa.Integer(), nullable=True, server_default="0"),
    )
    op.add_column(
        "recruiter_field_preferences",
        sa.Column("typical_corrections", sa.JSON(), nullable=True, server_default="[]"),
    )
    op.add_column(
        "recruiter_field_preferences",
        sa.Column("preferred_values", sa.JSON(), nullable=True, server_default="[]"),
    )
    op.add_column(
        "recruiter_field_preferences",
        sa.Column("value_range", sa.JSON(), nullable=True),
    )
    op.add_column(
        "recruiter_field_preferences",
        sa.Column("custom_threshold", sa.Float(), nullable=True),
    )
    op.add_column(
        "recruiter_field_preferences",
        sa.Column("always_ask", sa.Boolean(), nullable=True, server_default=sa.false()),
    )
    op.add_column(
        "recruiter_field_preferences",
        sa.Column(
            "remind_me_empty_field",
            sa.Boolean(),
            nullable=True,
            server_default=sa.true(),
        ),
    )
    op.add_column(
        "recruiter_field_preferences",
        sa.Column("last_reminded_at", sa.DateTime(), nullable=True),
    )
    op.add_column(
        "recruiter_field_preferences",
        sa.Column("snooze_until", sa.DateTime(), nullable=True),
    )
    op.add_column(
        "recruiter_field_preferences",
        sa.Column("times_reminded", sa.Integer(), nullable=True, server_default="0"),
    )
    op.add_column(
        "recruiter_field_preferences",
        sa.Column(
            "times_filled_with_lia",
            sa.Integer(),
            nullable=True,
            server_default="0",
        ),
    )
    op.add_column(
        "recruiter_field_preferences",
        sa.Column("last_reminder_action", sa.String(50), nullable=True),
    )
    op.add_column(
        "recruiter_field_preferences",
        sa.Column("last_correction_at", sa.DateTime(), nullable=True),
    )


def downgrade() -> None:
    # recruiter_field_preferences
    op.drop_column("recruiter_field_preferences", "last_correction_at")
    op.drop_column("recruiter_field_preferences", "last_reminder_action")
    op.drop_column("recruiter_field_preferences", "times_filled_with_lia")
    op.drop_column("recruiter_field_preferences", "times_reminded")
    op.drop_column("recruiter_field_preferences", "snooze_until")
    op.drop_column("recruiter_field_preferences", "last_reminded_at")
    op.drop_column("recruiter_field_preferences", "remind_me_empty_field")
    op.drop_column("recruiter_field_preferences", "always_ask")
    op.drop_column("recruiter_field_preferences", "custom_threshold")
    op.drop_column("recruiter_field_preferences", "value_range")
    op.drop_column("recruiter_field_preferences", "preferred_values")
    op.drop_column("recruiter_field_preferences", "typical_corrections")
    op.drop_column("recruiter_field_preferences", "total_encounters")
    op.drop_column("recruiter_field_preferences", "recruiter_id")

    # pattern_cache
    op.drop_column("pattern_cache", "updated_at")

    # webhook_logs
    op.drop_column("webhook_logs", "created_at")
    op.drop_column("webhook_logs", "attempt")
    op.drop_column("webhook_logs", "error")
    op.drop_column("webhook_logs", "request_body")
