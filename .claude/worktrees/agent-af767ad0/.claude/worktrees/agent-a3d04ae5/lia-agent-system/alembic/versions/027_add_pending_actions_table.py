"""Add pending_actions table for closed-loop action execution state.

Revision ID: 027_add_pending_actions_table
Revises: 026_add_langgraph_checkpoint_columns
Create Date: 2026-03-07

Context:
  The ciclo fechado (closed-loop execution) requires persisting multi-turn
  conversation state across requests. When LIA needs to collect parameters
  or wait for user confirmation before executing an action, the pending state
  must survive process restarts.

  PendingActionStore (app/orchestrator/pending_action.py) already has the
  SQL inline — this migration creates the backing table.

  company_id is included for multi-tenant isolation and LGPD compliance.
  expires_at (default 5 min TTL) limits PII retention for LGPD.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


revision = "027_add_pending_actions_table"
down_revision = "026_add_langgraph_checkpoint_columns"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "pending_actions",
        sa.Column("conversation_id", sa.Text(), nullable=False),
        sa.Column("pending_id", sa.Text(), nullable=False),
        sa.Column("company_id", sa.Text(), nullable=True),
        sa.Column("intent", sa.Text(), nullable=False),
        sa.Column("action_id", sa.Text(), nullable=False),
        sa.Column("domain_id", sa.Text(), nullable=False),
        sa.Column("collected_params", JSONB(), nullable=True),
        sa.Column("missing_params", JSONB(), nullable=True),
        sa.Column("awaiting_confirmation", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("confirmation_summary", JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("expires_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW() + INTERVAL '5 minutes'")),
        sa.PrimaryKeyConstraint("conversation_id"),
    )

    # Índice para cleanup periódico de registros expirados
    op.create_index(
        "ix_pending_actions_expires_at",
        "pending_actions",
        ["expires_at"],
    )

    # Índice para isolamento multi-tenant
    op.create_index(
        "ix_pending_actions_company_id",
        "pending_actions",
        ["company_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_pending_actions_company_id", table_name="pending_actions")
    op.drop_index("ix_pending_actions_expires_at", table_name="pending_actions")
    op.drop_table("pending_actions")
