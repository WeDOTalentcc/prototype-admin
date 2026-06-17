"""Sub-sprint 7A: add CustomAgent category fields + agent_quotas.max_agents.

Revision ID: 201
Revises: 200
Create Date: 2026-05-25

Plan canonical: ~/Documents/wedotalent_audit_2026-05-25/AGENT_STUDIO_SPRINT7_PLAN.md §2.5

Mudanças (defensivas — todas nullable/default seguro):
- custom_agents:
    + category VARCHAR(32) NULL
    + runtime_metrics JSONB NOT NULL DEFAULT {}
    + search_strategy JSONB NULL (sourcing-only payload)
    + preferences JSONB NULL (sourcing-only payload)
    + outreach_config JSONB NULL (sourcing-only payload)
    + legacy_sourcing_agent_id UUID NULL (back-reference)
- custom_agents idx_custom_agents_company_category (partial WHERE category NOT NULL)
- agent_quotas + max_agents INTEGER NOT NULL DEFAULT 5

NOTA: nome canonical da tabela quota é agent_quotas (plural) — não agent_quota.
Confirmado via information_schema 2026-05-25.

Sprint 8 (migration 204) virará category NOT NULL + DROP max_sourcing/max_custom.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "201"
down_revision = "200"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # custom_agents new columns
    op.add_column("custom_agents", sa.Column("category", sa.String(32), nullable=True))
    op.add_column(
        "custom_agents",
        sa.Column("runtime_metrics", JSONB(), nullable=False, server_default="{}"),
    )
    op.add_column("custom_agents", sa.Column("search_strategy", JSONB(), nullable=True))
    op.add_column("custom_agents", sa.Column("preferences", JSONB(), nullable=True))
    op.add_column("custom_agents", sa.Column("outreach_config", JSONB(), nullable=True))
    op.add_column(
        "custom_agents",
        sa.Column("legacy_sourcing_agent_id", UUID(as_uuid=True), nullable=True),
    )

    # Partial index — só linhas com category preenchido (acelera filter Sprint 7B)
    op.create_index(
        "idx_custom_agents_company_category",
        "custom_agents",
        ["company_id", "category"],
        postgresql_where=sa.text("category IS NOT NULL"),
    )

    # Unique index defesa contra duplo INSERT na 203 (idempotency belt-and-suspenders)
    op.create_index(
        "uq_custom_agents_legacy_sourcing",
        "custom_agents",
        ["legacy_sourcing_agent_id"],
        unique=True,
        postgresql_where=sa.text("legacy_sourcing_agent_id IS NOT NULL"),
    )

    # agent_quotas.max_agents (decisão Paulo 2026-05-25: soma transparente)
    op.add_column(
        "agent_quotas",
        sa.Column("max_agents", sa.Integer(), nullable=False, server_default="5"),
    )


def downgrade() -> None:
    op.drop_column("agent_quotas", "max_agents")
    op.drop_index("uq_custom_agents_legacy_sourcing", table_name="custom_agents")
    op.drop_index("idx_custom_agents_company_category", table_name="custom_agents")
    op.drop_column("custom_agents", "legacy_sourcing_agent_id")
    op.drop_column("custom_agents", "outreach_config")
    op.drop_column("custom_agents", "preferences")
    op.drop_column("custom_agents", "search_strategy")
    op.drop_column("custom_agents", "runtime_metrics")
    op.drop_column("custom_agents", "category")
