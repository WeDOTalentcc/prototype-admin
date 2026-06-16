"""Sub-sprint 7A: pool_agent_assignments + sourcing_agent_signals.custom_agent_id.

Revision ID: 202
Revises: 201
Create Date: 2026-05-25

Plan canonical: ~/Documents/wedotalent_audit_2026-05-25/AGENT_STUDIO_SPRINT7_PLAN.md §1.1.2 + §1.1.3

Mudancas:
- CREATE TABLE pool_agent_assignments (M2M talent_pools <-> custom_agents).
  - company_id redundante (ADR-LGPD-001): queries cross-pool sem JOIN.
  - schedule_type/schedule_config (sub-sprint 7C usara).
  - UNIQUE (talent_pool_id, custom_agent_id) — defense contra dup assignment.
- ADD sourcing_agent_signals.custom_agent_id UUID NULL (populado em 203 via JOIN).
- ADD sourcing_agent_signals.assignment_id UUID NULL (nao populado em 7A, reservado 7C).

agent_id FK legacy preservada (DROP adiado pra Sprint 8 — rollback safety).
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "202"
down_revision = "201"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # pool_agent_assignments
    op.create_table(
        "pool_agent_assignments",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("company_id", sa.String(36), nullable=False),
        sa.Column(
            "talent_pool_id",
            UUID(as_uuid=True),
            sa.ForeignKey("talent_pools.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "custom_agent_id",
            UUID(as_uuid=True),
            sa.ForeignKey("custom_agents.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("status", sa.String(16), nullable=False, server_default="active"),
        sa.Column("config_overrides", JSONB(), nullable=False, server_default="{}"),
        sa.Column("schedule_type", sa.String(16), nullable=False, server_default="on_demand"),
        sa.Column("schedule_config", JSONB(), nullable=False, server_default="{}"),
        sa.Column("last_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_run_status", sa.String(16), nullable=True),
        sa.Column("runtime_metrics", JSONB(), nullable=False, server_default="{}"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("created_by", sa.String(36), nullable=False),
        sa.UniqueConstraint("talent_pool_id", "custom_agent_id", name="uq_pool_agent"),
        sa.CheckConstraint(
            "schedule_type IN ('on_demand','cron','event_driven')",
            name="chk_paa_schedule_type",
        ),
        sa.CheckConstraint(
            "status IN ('active','paused','completed','error')",
            name="chk_paa_status",
        ),
    )

    op.create_index("idx_paa_company", "pool_agent_assignments", ["company_id"])
    op.create_index("idx_paa_pool", "pool_agent_assignments", ["talent_pool_id"])
    op.create_index("idx_paa_agent", "pool_agent_assignments", ["custom_agent_id"])
    op.create_index(
        "idx_paa_schedule_active",
        "pool_agent_assignments",
        ["schedule_type", "status"],
        postgresql_where=sa.text("schedule_type IN ('cron','event_driven')"),
    )

    # sourcing_agent_signals additions
    op.add_column(
        "sourcing_agent_signals",
        sa.Column(
            "custom_agent_id",
            UUID(as_uuid=True),
            sa.ForeignKey("custom_agents.id", ondelete="CASCADE"),
            nullable=True,
        ),
    )
    op.add_column(
        "sourcing_agent_signals",
        sa.Column(
            "assignment_id",
            UUID(as_uuid=True),
            sa.ForeignKey("pool_agent_assignments.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.create_index(
        "idx_sas_custom_agent",
        "sourcing_agent_signals",
        ["custom_agent_id"],
        postgresql_where=sa.text("custom_agent_id IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index("idx_sas_custom_agent", table_name="sourcing_agent_signals")
    op.drop_column("sourcing_agent_signals", "assignment_id")
    op.drop_column("sourcing_agent_signals", "custom_agent_id")

    op.drop_index("idx_paa_schedule_active", table_name="pool_agent_assignments")
    op.drop_index("idx_paa_agent", table_name="pool_agent_assignments")
    op.drop_index("idx_paa_pool", table_name="pool_agent_assignments")
    op.drop_index("idx_paa_company", table_name="pool_agent_assignments")
    op.drop_table("pool_agent_assignments")
