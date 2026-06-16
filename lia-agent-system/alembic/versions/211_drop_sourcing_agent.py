"""Sprint 8: DROP SourcingAgent class + sourcing_agents table + legacy_sourcing_agent_id column.

Backfill Sprint 7A (migration 203) preservou rollback safety; Sprint 8 fecha
SourcingAgent → CustomAgent migration 100%. Confirmado empiricamente pre-execucao
(2026-05-26):
- 2 sourcing_agents rows = 2 custom_agents.legacy_sourcing_agent_id NOT NULL match
- 0 orphans, referential integrity OK
- Empirical query: SELECT COUNT(*) FROM sourcing_agents s LEFT JOIN custom_agents c
  ON c.legacy_sourcing_agent_id = s.id WHERE c.id IS NULL → 0

Ordem de DROP (FKs primeiro, depois colunas/tabela):
1. DROP FK sourcing_agent_signals_agent_id_fkey
2. DROP coluna sourcing_agent_signals.agent_id (preserva canonical custom_agent_id NOT NULL)
3. DROP unique index uq_custom_agents_legacy_sourcing
4. DROP coluna custom_agents.legacy_sourcing_agent_id
5. DROP tabela sourcing_agents (RLS policies + talent_pool_id FK caem em cascata)

Downgrade re-cria estrutura mas NAO restaura dados (rollback estrutural apenas).

Refs:
- AGENT_STUDIO_SPRINT7_PLAN.md Sprint 8
- AGENT_STUDIO_GAP_ANALYSIS_2026-05-26.md
- Migration 201 (criou legacy_sourcing_agent_id + uq_custom_agents_legacy_sourcing)
- Migration 203 (data backfill SourcingAgent -> CustomAgent)
- Migration 209 (relaxed sourcing_agent_signals.agent_id NOT NULL -> NULLABLE)
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB


revision = "211"
down_revision = "210"
branch_labels = None
depends_on = None


def upgrade():
    # 1. Drop FK constraint: sourcing_agent_signals.agent_id -> sourcing_agents.id
    op.drop_constraint(
        "sourcing_agent_signals_agent_id_fkey",
        "sourcing_agent_signals",
        type_="foreignkey",
    )

    # 2. Drop coluna sourcing_agent_signals.agent_id (canonical eh custom_agent_id NOT NULL)
    op.drop_column("sourcing_agent_signals", "agent_id")

    # 3. Drop unique partial index em custom_agents.legacy_sourcing_agent_id
    op.drop_index(
        "uq_custom_agents_legacy_sourcing",
        table_name="custom_agents",
    )

    # 4. Drop coluna custom_agents.legacy_sourcing_agent_id
    op.drop_column("custom_agents", "legacy_sourcing_agent_id")

    # 5. Drop tabela sourcing_agents (RLS policies + FK talent_pool_id caem em cascata)
    op.drop_table("sourcing_agents")


def downgrade():
    # ATENCAO: downgrade re-cria estrutura mas NAO restaura dados.
    # Rollback estrutural apenas pra alembic test (sem dados, sem RLS policies).

    # 5'. Re-create tabela sourcing_agents (schema canonical pre-DROP)
    op.create_table(
        "sourcing_agents",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("company_id", sa.String(64), nullable=False),
        sa.Column("job_id", sa.String(64), nullable=True),
        sa.Column("talent_pool_id", UUID(as_uuid=True), sa.ForeignKey("talent_pools.id"), nullable=True),
        sa.Column("agent_template_id", sa.String(255), sa.ForeignKey("agent_templates.id", ondelete="SET NULL"), nullable=True),
        sa.Column("agent_name", sa.String(256), nullable=False),
        sa.Column("status", sa.String(16), nullable=False, server_default="active"),
        sa.Column("calibration_v", sa.Integer, nullable=False, server_default="0"),
        sa.Column("search_strategy", JSONB, nullable=False, server_default="{}"),
        sa.Column("preferences", JSONB, nullable=False, server_default="{}"),
        sa.Column("outreach_config", JSONB, nullable=False, server_default="{}"),
        sa.Column("profiles_viewed", sa.Integer, server_default="0"),
        sa.Column("profiles_approved", sa.Integer, server_default="0"),
        sa.Column("profiles_rejected", sa.Integer, server_default="0"),
        sa.Column("emails_sent", sa.Integer, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "sourcing_agents_company_id_idx",
        "sourcing_agents",
        ["company_id"],
    )

    # 4'. Re-create custom_agents.legacy_sourcing_agent_id
    op.add_column(
        "custom_agents",
        sa.Column("legacy_sourcing_agent_id", UUID(as_uuid=True), nullable=True),
    )

    # 3'. Re-create unique partial index
    op.create_index(
        "uq_custom_agents_legacy_sourcing",
        "custom_agents",
        ["legacy_sourcing_agent_id"],
        unique=True,
        postgresql_where=sa.text("legacy_sourcing_agent_id IS NOT NULL"),
    )

    # 2'. Re-create sourcing_agent_signals.agent_id (nullable per Sprint 7B-3a Part 1.5 v2)
    op.add_column(
        "sourcing_agent_signals",
        sa.Column("agent_id", UUID(as_uuid=True), nullable=True),
    )

    # 1'. Re-create FK constraint
    op.create_foreign_key(
        "sourcing_agent_signals_agent_id_fkey",
        "sourcing_agent_signals",
        "sourcing_agents",
        ["agent_id"],
        ["id"],
        ondelete="CASCADE",
    )
