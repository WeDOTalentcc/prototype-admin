"""Add agent_type enum and domains JSONB to custom_agents; make company_id nullable

Revision ID: 254
Revises: 253
Create Date: 2026-06-09

Fase A — Agent Studio Meta-Platform: first-party agent support.
- company_id is made NULLABLE to allow WeDo global agents (first_party) with no tenant.
- agent_type: new ENUM column ('custom' | 'first_party'). Default 'custom' — backward compat.
- domains: JSONB list of scope domains covered by the agent (filled in Fase B).
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "254"
down_revision = "253"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Create the enum type first (before column that uses it)
    agenttypeenum = sa.Enum("custom", "first_party", name="agenttypeenum")
    agenttypeenum.create(op.get_bind(), checkfirst=True)

    # 2. Make company_id nullable — first-party agents have no tenant
    op.alter_column(
        "custom_agents",
        "company_id",
        existing_type=sa.String(64),
        nullable=True,
    )

    # 3. Add agent_type column with server_default so NOT NULL works without a lock
    op.add_column(
        "custom_agents",
        sa.Column(
            "agent_type",
            sa.Enum("custom", "first_party", name="agenttypeenum", create_type=False),
            nullable=False,
            server_default="custom",
        ),
    )

    # 4. Add domains JSONB column
    op.add_column(
        "custom_agents",
        sa.Column(
            "domains",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="[]",
        ),
    )

    # 5. Index on agent_type for global first-party queries
    op.create_index("idx_custom_agents_agent_type", "custom_agents", ["agent_type"])


def downgrade() -> None:
    # Reverse in opposite order
    op.drop_index("idx_custom_agents_agent_type", table_name="custom_agents")
    op.drop_column("custom_agents", "domains")
    op.drop_column("custom_agents", "agent_type")

    # Restore company_id NOT NULL — note: any first_party rows with NULL company_id
    # must be removed manually before downgrade or this will fail.
    op.alter_column(
        "custom_agents",
        "company_id",
        existing_type=sa.String(64),
        nullable=False,
    )

    # Drop the enum type last
    agenttypeenum = sa.Enum("custom", "first_party", name="agenttypeenum")
    agenttypeenum.drop(op.get_bind(), checkfirst=True)
