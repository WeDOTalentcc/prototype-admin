"""C2.1 — Foreign keys on agent-studio tenant tables.

Revision ID: 219
Revises: 218
Create Date: 2026-05-29

Context (Fase 2.5 Onda C2.1 — AUDIT 6 P0-1):
  The 6 agent-studio tables had zero FKs, so tenant offboarding could not cascade
  and orphan rows could accumulate silently (LGPD erasure integrity gap). After
  C2.3 (mig 217) standardized company_id to varchar, the cross-type FKs to
  companies.id (varchar(255)) are now possible.

  ON DELETE semantics:
  - company_id -> companies.id  : CASCADE (tenant offboarding removes tenant data)
  - agent_id    -> custom_agents.id : CASCADE (deleting an agent removes its
    deployments + execution logs)
  - studio_agent_id -> custom_agents.id : SET NULL (historical consumption survives
    agent deletion — billing/audit trail must not vanish)
  - deployment_id -> agent_deployments.id : SET NULL (execution log keeps its
    history even if the deployment is later removed)

  ORPHAN HANDLING (validated 2026-05-29 against dev DB):
  - digital_twins / ai_consumption / ai_credits_balance / agent_deployments /
    agent_execution_logs : zero orphans (tables empty or clean) -> FK applied.
  - custom_agents.company_id : 42 of 50 rows are ephemeral test fixtures
    (company_id '00000000-0000-0000-0000-000000000001' + 'test-7c-*' from contract
    runs) with no matching companies row. The company_id FK on custom_agents is
    DEFERRED to avoid destroying data without authorization. Re-run after the dev
    DB is cleaned of test fixtures, then add this FK in a follow-up migration.
"""
from alembic import op

revision = "219"
down_revision = "218"
branch_labels = None
depends_on = None

# (constraint_name, table, column, ref_table, ref_column, on_delete)
_FKS = [
    (
        "digital_twins_company_id_fkey",
        "digital_twins", "company_id", "companies", "id", "CASCADE",
    ),
    (
        "ai_consumption_company_id_fkey",
        "ai_consumption", "company_id", "companies", "id", "CASCADE",
    ),
    (
        "ai_consumption_studio_agent_id_fkey",
        "ai_consumption", "studio_agent_id", "custom_agents", "id", "SET NULL",
    ),
    (
        "ai_credits_balance_company_id_fkey",
        "ai_credits_balance", "company_id", "companies", "id", "CASCADE",
    ),
    (
        "agent_deployments_company_id_fkey",
        "agent_deployments", "company_id", "companies", "id", "CASCADE",
    ),
    (
        "agent_deployments_agent_id_fkey",
        "agent_deployments", "agent_id", "custom_agents", "id", "CASCADE",
    ),
    (
        "agent_execution_logs_agent_id_fkey",
        "agent_execution_logs", "agent_id", "custom_agents", "id", "CASCADE",
    ),
    (
        "agent_execution_logs_deployment_id_fkey",
        "agent_execution_logs", "deployment_id", "agent_deployments", "id",
        "SET NULL",
    ),
]


def upgrade() -> None:
    for name, table, col, ref_table, ref_col, on_delete in _FKS:
        op.create_foreign_key(
            name, table, ref_table, [col], [ref_col], ondelete=on_delete
        )


def downgrade() -> None:
    for name, table, *_ in reversed(_FKS):
        op.drop_constraint(name, table, type_="foreignkey")
