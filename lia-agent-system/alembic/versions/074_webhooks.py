"""Create webhooks table.

Revision ID: 074_webhooks
Revises: 073_agent_version_snapshots
Create Date: 2026-04-13
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ARRAY, UUID

revision = "074_webhooks"
down_revision = "073_agent_version_snapshots"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "studio_webhooks",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("company_id", sa.String(64), nullable=False, index=True),
        sa.Column("name", sa.String(256), nullable=False),
        sa.Column("url", sa.String(2048), nullable=False),
        sa.Column("events", ARRAY(sa.String()), nullable=False),
        sa.Column("secret", sa.String(256), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("total_deliveries", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_failures", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_delivery_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_status_code", sa.Integer(), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("created_by", sa.String(128), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade():
    op.drop_table("studio_webhooks")
