"""external_api_consumption table for Apify/Pearch tracking

Revision ID: 075_external_api
Revises: 074_webhooks
Create Date: 2026-04-13
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "075_external_api"
down_revision = "074_webhooks"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "external_api_consumption",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("company_id", sa.String(100), nullable=False, index=True),
        sa.Column("user_id", sa.String(100), nullable=True, index=True),
        sa.Column("candidate_id", postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column("linkedin_url", sa.String(500), nullable=True),
        sa.Column("provider", sa.String(30), nullable=False, index=True),
        sa.Column("operation", sa.String(50), nullable=False, index=True),
        sa.Column("credits_consumed", sa.Integer, server_default="0", nullable=False),
        sa.Column("cost_usd", sa.Float, server_default="0.0", nullable=False),
        sa.Column("cost_brl", sa.Float, server_default="0.0", nullable=False),
        sa.Column("exchange_rate", sa.Float, server_default="5.50", nullable=False),
        sa.Column("success", sa.Boolean, server_default="false", nullable=False),
        sa.Column("result_status", sa.String(30), nullable=True),
        sa.Column("error_message", sa.String(500), nullable=True),
        sa.Column("response_time_ms", sa.Integer, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), index=True),
    )
    op.create_index(
        "ix_extapi_company_created",
        "external_api_consumption",
        ["company_id", "created_at"],
    )
    op.create_index(
        "ix_extapi_company_provider",
        "external_api_consumption",
        ["company_id", "provider"],
    )


def downgrade() -> None:
    op.drop_index("ix_extapi_company_provider", table_name="external_api_consumption")
    op.drop_index("ix_extapi_company_created", table_name="external_api_consumption")
    op.drop_table("external_api_consumption")
