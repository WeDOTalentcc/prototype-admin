"""Add request_id and request_cost columns to audit_execution_metadata.

Revision ID: 065
Revises: 064
Create Date: 2026-04-11

Supports per-request cost tracking (Task #153).
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "065"
down_revision = "064_create_agent_quotas_recruitment_campaigns"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "audit_execution_metadata",
        sa.Column("request_id", sa.String(255), nullable=True),
    )
    op.add_column(
        "audit_execution_metadata",
        sa.Column("request_cost", JSONB, nullable=True),
    )
    op.create_index(
        "ix_audit_exec_request_id",
        "audit_execution_metadata",
        ["request_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_audit_exec_request_id", table_name="audit_execution_metadata")
    op.drop_column("audit_execution_metadata", "request_cost")
    op.drop_column("audit_execution_metadata", "request_id")
