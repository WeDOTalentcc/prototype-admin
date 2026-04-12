"""Agent Studio parity: enable_memory, context_level, excluded_tools.

Revision ID: 069_agent_studio_parity
Revises: 068_rls_deny_by_default
Create Date: 2026-04-12
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ARRAY

revision = "069_agent_studio_parity"
down_revision = "068_rls_deny_by_default"
branch_labels = None
depends_on = None


def upgrade():
    # Add new columns with defaults (zero downtime, no data loss)
    op.add_column(
        "custom_agents",
        sa.Column("enable_memory", sa.Boolean(), nullable=False, server_default="true"),
    )
    op.add_column(
        "custom_agents",
        sa.Column("context_level", sa.String(20), nullable=False, server_default="full"),
    )
    op.add_column(
        "custom_agents",
        sa.Column("excluded_tools", ARRAY(sa.String()), nullable=False, server_default="{}"),
    )

    # Fix NULL/empty domain values
    op.execute("UPDATE custom_agents SET domain = 'general' WHERE domain IS NULL OR domain = ''")

    # Add CHECK constraints
    op.create_check_constraint(
        "ck_custom_agents_context_level",
        "custom_agents",
        "context_level IN ('minimal', 'standard', 'full')",
    )
    op.create_check_constraint(
        "ck_custom_agents_domain",
        "custom_agents",
        "domain IN ('sourcing', 'screening', 'pipeline', 'analytics', "
        "'communication', 'job_management', 'automation', 'onboarding', 'general', 'custom')",
    )


def downgrade():
    op.drop_constraint("ck_custom_agents_domain", "custom_agents", type_="check")
    op.drop_constraint("ck_custom_agents_context_level", "custom_agents", type_="check")
    op.drop_column("custom_agents", "excluded_tools")
    op.drop_column("custom_agents", "context_level")
    op.drop_column("custom_agents", "enable_memory")
