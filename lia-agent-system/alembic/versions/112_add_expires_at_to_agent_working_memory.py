"""Add expires_at to agent_working_memory

Revision ID: 112
Revises: 111
Create Date: 2026-05-03

UC-P2-02 — AgentWorkingMemory was missing an expires_at column.
Without TTL the table grows unbounded. This migration:
  1. Adds expires_at DateTime(timezone=True) NULLABLE with an index.
  2. Backfills existing rows: expires_at = created_at + 90 days.
The Celery Beat task agent_working_memory.cleanup deletes expired rows
daily at 03h UTC (added in compliance.py + celery_app.py beat_schedule).
"""
from alembic import op
import sqlalchemy as sa

revision = "112"
down_revision = "111"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "agent_working_memory",
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_agent_working_memory_expires_at",
        "agent_working_memory",
        ["expires_at"],
    )
    # Backfill: existing rows expire 90 days from created_at
    op.execute(
        "UPDATE agent_working_memory "
        "SET expires_at = created_at + INTERVAL '90 days' "
        "WHERE expires_at IS NULL"
    )


def downgrade():
    op.drop_index("ix_agent_working_memory_expires_at", table_name="agent_working_memory")
    op.drop_column("agent_working_memory", "expires_at")
