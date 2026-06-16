"""Create agent_approval_requests table.

Revision ID: 072_agent_approvals
Revises: 071_agent_execution_logs
Create Date: 2026-04-13
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "072_agent_approvals"
down_revision = "071_agent_execution_logs"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "agent_approval_requests",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("agent_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("company_id", sa.String(64), nullable=False, index=True),
        sa.Column("requested_by", sa.String(128), nullable=False),
        sa.Column("reviewed_by", sa.String(128), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="pending", index=True),
        sa.Column("review_notes", sa.Text(), nullable=True),
        sa.Column("requested_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_check_constraint(
        "ck_agent_approval_status",
        "agent_approval_requests",
        "status IN ('pending', 'approved', 'rejected')",
    )

    # Add pending_approval to custom_agents.status check constraint
    # (If a CHECK constraint exists, we need to update it. For now, assume it's open.)


def downgrade():
    op.drop_constraint("ck_agent_approval_status", "agent_approval_requests", type_="check")
    op.drop_table("agent_approval_requests")
