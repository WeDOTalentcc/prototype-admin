"""Add user_preferences column to conversation_summaries (FIX 32).

Revision ID: 101_conv_summaries_user_preferences
Revises: 100_job_vacancy_benefits_jsonb
Create Date: 2026-04-21

Closes FIX 32 — schema drift blocking multi-turn conversation memory.

Root cause: ORM model `lia_models.conversation.ConversationSummary` declared
`user_preferences = Column(JSON, default=dict)` but the production DB schema
never added that column. Every chat turn logged:

  [MainOrchestrator] ConversationMemory setup failed — conversation history
  lost: column conversation_summaries.user_preferences does not exist

Consequence: `conversation_memory.get_context_for_llm()` raises, orchestrator
catches → conversation_history passed to LLM is always EMPTY. Multi-turn
context broken system-wide.

This migration adds the missing column (nullable JSON with default '{}'::json)
to align the DB with the ORM model. Idempotent — detects if column already
exists and skips.

Canonical-fix: producer = DB schema. Fix belongs here, not in model fallback.
"""
from alembic import op
import sqlalchemy as sa


revision = "101_conv_summaries_user_preferences"
down_revision = "100_job_vacancy_benefits_jsonb"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add user_preferences JSON column to conversation_summaries.

    Idempotent: if column already exists, skip without error.
    """
    bind = op.get_bind()
    # Detect whether the column already exists
    res = bind.execute(
        sa.text(
            """
            SELECT 1 FROM information_schema.columns
            WHERE table_name = 'conversation_summaries'
              AND column_name = 'user_preferences'
            """
        )
    ).scalar()

    if res is not None:
        print("FIX 32: conversation_summaries.user_preferences already exists — skipping")
        return

    op.add_column(
        "conversation_summaries",
        sa.Column(
            "user_preferences",
            sa.JSON(),
            nullable=True,
            server_default=sa.text("'{}'::json"),
        ),
    )
    print("FIX 32: added conversation_summaries.user_preferences (JSON, default {})")


def downgrade() -> None:
    """Drop user_preferences column — safe since ORM tolerates missing via
    previous error path (but do this only to roll back if needed)."""
    bind = op.get_bind()
    res = bind.execute(
        sa.text(
            """
            SELECT 1 FROM information_schema.columns
            WHERE table_name = 'conversation_summaries'
              AND column_name = 'user_preferences'
            """
        )
    ).scalar()
    if res is None:
        return
    op.drop_column("conversation_summaries", "user_preferences")
