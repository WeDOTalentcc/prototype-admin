"""Create agent_version_snapshots table.

Revision ID: 073_agent_version_snapshots
Revises: 072_agent_approvals
Create Date: 2026-04-13
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID

revision = "073_agent_version_snapshots"
down_revision = "072_agent_approvals"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "agent_version_snapshots",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("agent_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("company_id", sa.String(64), nullable=False, index=True),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("snapshot_data", JSONB, nullable=False),
        sa.Column("changed_fields", ARRAY(sa.String()), server_default="{}"),
        sa.Column("change_reason", sa.Text(), nullable=True),
        sa.Column("changed_by", sa.String(128), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index(
        "ix_agent_version_snapshots_agent_version",
        "agent_version_snapshots",
        ["agent_id", "version"],
        unique=True,
    )


def downgrade():
    op.drop_index("ix_agent_version_snapshots_agent_version", table_name="agent_version_snapshots")
    op.drop_table("agent_version_snapshots")
