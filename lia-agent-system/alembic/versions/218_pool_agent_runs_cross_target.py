"""C1.4 — pool_agent_runs cross-target: add deployment_id, relax assignment_id, CHECK.

Revision ID: 218
Revises: 217
Create Date: 2026-05-29

Context (Fase 2.5 Onda C1.4 — plano C1.4):
  The unified execution engine (Onda C1) makes agent_deployments the canonical
  junction agent<->surface. A run must be linkable to EITHER a legacy
  pool_agent_assignment OR an agent_deployment (during the Opção A migration), so:

  - add pool_agent_runs.deployment_id UUID NULL, FK -> agent_deployments.id
    ON DELETE CASCADE (deployment offboarding removes its runs).
  - drop NOT NULL on assignment_id (a deployment-sourced run has no assignment).
    The existing assignment_id FK (ON DELETE CASCADE) is preserved.
  - CHECK constraint chk_par_source_present: at least one of (assignment_id,
    deployment_id) is non-null. Fail-closed: no orphan runs with neither source.
  - index on deployment_id for the last_execution_id lookup of deployment runs.

  Existing rows (36 in dev) all have assignment_id set, so the CHECK holds and the
  new nullable column defaults to NULL. No data migration here (C1.5 backfills
  deployment_id when assignments migrate to deployments).
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "218"
down_revision = "217"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "pool_agent_runs",
        sa.Column("deployment_id", UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "pool_agent_runs_deployment_id_fkey",
        "pool_agent_runs",
        "agent_deployments",
        ["deployment_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index(
        "idx_pool_agent_runs_deployment",
        "pool_agent_runs",
        ["deployment_id", "created_at"],
    )
    op.alter_column(
        "pool_agent_runs",
        "assignment_id",
        existing_type=UUID(as_uuid=True),
        nullable=True,
    )
    # Fail-closed: a run is sourced from an assignment OR a deployment, never neither.
    op.create_check_constraint(
        "chk_par_source_present",
        "pool_agent_runs",
        "(assignment_id IS NOT NULL) OR (deployment_id IS NOT NULL)",
    )


def downgrade() -> None:
    op.drop_constraint(
        "chk_par_source_present", "pool_agent_runs", type_="check"
    )
    # Restore NOT NULL — only safe if no deployment-only rows exist.
    op.alter_column(
        "pool_agent_runs",
        "assignment_id",
        existing_type=UUID(as_uuid=True),
        nullable=False,
    )
    op.drop_index("idx_pool_agent_runs_deployment", table_name="pool_agent_runs")
    op.drop_constraint(
        "pool_agent_runs_deployment_id_fkey", "pool_agent_runs", type_="foreignkey"
    )
    op.drop_column("pool_agent_runs", "deployment_id")
