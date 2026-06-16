"""Create tenant_llm_configs table for Choose Your AI.

Revision ID: 058_tenant_llm_configs
Revises: 057
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSON


revision = "058_tenant_llm_configs"
down_revision = "058"
depends_on = None


def upgrade() -> None:
    op.create_table(
        "tenant_llm_configs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("company_id", sa.String(255), nullable=False, unique=True, index=True),
        sa.Column("primary_provider", sa.String(50), default="gemini"),
        sa.Column("fallback_order", JSON, default=["gemini", "claude", "openai"]),
        sa.Column("providers", JSON, default={}),
        sa.Column("routing", JSON, default={}),
        sa.Column("config", JSON, default={}),
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column("created_at", sa.DateTime),
        sa.Column("updated_at", sa.DateTime),
        sa.Column("created_by", sa.String(255)),
    )


def downgrade() -> None:
    op.drop_table("tenant_llm_configs")
