"""C2.3 — Fix type mismatch: ai_consumption + ai_credits_balance company_id uuid -> varchar(64).

Revision ID: 217
Revises: 216
Create Date: 2026-05-29

Context (Fase 2.5 Onda C2.3 — AUDIT 6 P0-6):
  companies.id is varchar(255). Every agent-studio tenant table stores company_id
  as varchar (custom_agents/agent_deployments/pool_agent_runs use varchar(64)).
  Only ai_consumption.company_id and ai_credits_balance.company_id were declared as
  uuid, breaking JOINs to companies (CAST required) and blocking the company_id FKs
  added in migration 218 (C2.1). This migration standardizes both columns to
  varchar(64), matching the dominant canonical convention.

  Safe conversion: ai_consumption has 0 rows, ai_credits_balance has 1 row.
  USING company_id::text preserves the canonical 36-char UUID-string representation.

  Both tables already have RLS (ENABLE + FORCE, 4 policies each) that reference
  company_id, so Postgres refuses ALTER COLUMN TYPE while the policies exist
  (FeatureNotSupportedError: cannot alter type of a column used in a policy).
  We drop the 4 canonical policies per table, alter the type, then recreate the
  policies identically (same canonical pattern: (company_id)::text =
  app_current_company_id(), permissive, public role). RLS ENABLE/FORCE flags on
  the table are untouched by dropping policies.
"""
from alembic import op

revision = "217"
down_revision = "216"
branch_labels = None
depends_on = None

# Tables whose company_id is converted uuid -> varchar(64). They already carry the
# canonical 4-policy RLS set, dropped+recreated around the ALTER.
_TABLES = ("ai_consumption", "ai_credits_balance")


def _drop_policies(table: str) -> None:
    for cmd in ("select", "insert", "update", "delete"):
        op.execute(f"DROP POLICY IF EXISTS {table}_tenant_{cmd} ON {table};")


def _create_policies(table: str) -> None:
    op.execute(
        f"CREATE POLICY {table}_tenant_select ON {table} "
        f"FOR SELECT USING ((company_id)::text = app_current_company_id());"
    )
    op.execute(
        f"CREATE POLICY {table}_tenant_insert ON {table} "
        f"FOR INSERT WITH CHECK ((company_id)::text = app_current_company_id());"
    )
    op.execute(
        f"CREATE POLICY {table}_tenant_update ON {table} "
        f"FOR UPDATE USING ((company_id)::text = app_current_company_id());"
    )
    op.execute(
        f"CREATE POLICY {table}_tenant_delete ON {table} "
        f"FOR DELETE USING ((company_id)::text = app_current_company_id());"
    )


def upgrade() -> None:
    for table in _TABLES:
        _drop_policies(table)
    op.execute(
        "ALTER TABLE ai_consumption "
        "ALTER COLUMN company_id TYPE varchar(64) USING company_id::text;"
    )
    op.execute(
        "ALTER TABLE ai_credits_balance "
        "ALTER COLUMN company_id TYPE varchar(64) USING company_id::text;"
    )
    for table in _TABLES:
        _create_policies(table)


def downgrade() -> None:
    for table in _TABLES:
        _drop_policies(table)
    op.execute(
        "ALTER TABLE ai_credits_balance "
        "ALTER COLUMN company_id TYPE uuid USING company_id::uuid;"
    )
    op.execute(
        "ALTER TABLE ai_consumption "
        "ALTER COLUMN company_id TYPE uuid USING company_id::uuid;"
    )
    for table in _TABLES:
        _create_policies(table)
