"""sox_audit_log client_id set NOT NULL

Revision ID: 72bb11ddbbaa
Revises: aefc81463fac
Create Date: 2026-05-02

UC-P0-06 Step 2/2: After backfill, enforce NOT NULL on client_id.
Requires migration 105_backfill_sox_audit_client_id to have run first.

Without NOT NULL, RLS cannot guarantee per-tenant audit log isolation.
"""
from alembic import op
import sqlalchemy as sa


revision = "72bb11ddbbaa"
down_revision = "aefc81463fac"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "sox_audit_logs",
        "client_id",
        existing_type=sa.String(255),
        nullable=False,
        server_default="system",
    )


def downgrade() -> None:
    op.alter_column(
        "sox_audit_logs",
        "client_id",
        existing_type=sa.String(255),
        nullable=True,
        server_default=None,
    )
