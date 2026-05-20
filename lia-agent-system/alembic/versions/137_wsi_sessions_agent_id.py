"""Add agent_id column to wsi_sessions (SMOKE-#8 audit 2026-05-20).

Revision ID: 137_wsi_sessions_agent_id
Revises: 136_wsi_sessions_call_id
Create Date: 2026-05-20

Root cause (E2E audit smoke test 2026-05-20):
- ``app/domains/cv_screening/services/wsi_voice_orchestrator.py:721`` queries
  ``s.agent_id`` from ``wsi_sessions``.
- ``app/domains/cv_screening/services/wsi_voice_orchestrator.py:239`` also
  ``UPDATE wsi_sessions SET agent_id = :agent_id``.
- But ``wsi_sessions`` table never had an ``agent_id`` column →
  UndefinedColumnError → HTTP 500 on GET /api/wsi/voice-screening/{session_id}.

Adds ``agent_id VARCHAR(255)`` (nullable) — the orchestrator code falls back to
``"twilio"`` when no agent is provided, so it is always non-NULL after first
write. Index added since orchestrator may later filter sessions by agent.

Reversible.
"""
from alembic import op
import sqlalchemy as sa


revision = "137_wsi_sessions_agent_id"
down_revision = "136_wsi_sessions_call_id"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "wsi_sessions",
        sa.Column("agent_id", sa.String(length=255), nullable=True),
    )
    op.create_index(
        "ix_wsi_sessions_agent_id",
        "wsi_sessions",
        ["agent_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_wsi_sessions_agent_id", table_name="wsi_sessions")
    op.drop_column("wsi_sessions", "agent_id")
