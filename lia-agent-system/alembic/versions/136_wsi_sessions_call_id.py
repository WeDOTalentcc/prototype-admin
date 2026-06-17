"""Add call_id column to wsi_sessions (SMOKE-#8+#9 audit 2026-05-20).

Revision ID: 134_wsi_sessions_call_id
Revises: 133_calibration_weights_company_id
Create Date: 2026-05-20

Root cause (E2E audit smoke test 2026-05-20):
- ``app/api/wsi_endpoints.py:817`` calls ``wsi_voice_orchestrator.get_session_by_call_id``
- That service queries ``SELECT id FROM wsi_sessions WHERE call_id = $1``
- But ``wsi_sessions`` table never had a ``call_id`` column → UndefinedColumnError → HTTP 500

Adds ``call_id VARCHAR(255)`` (nullable) + index for query performance.
FK to ``voice_screening_calls.call_id`` not enforced (loose coupling — sessions
may exist before a call lands).

Reversible.
"""
from alembic import op
import sqlalchemy as sa


revision = "136_wsi_sessions_call_id"
down_revision = "135_recruiter_field_preferences_company_id"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "wsi_sessions",
        sa.Column("call_id", sa.String(length=255), nullable=True),
    )
    op.create_index(
        "ix_wsi_sessions_call_id",
        "wsi_sessions",
        ["call_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_wsi_sessions_call_id", table_name="wsi_sessions")
    op.drop_column("wsi_sessions", "call_id")
