"""C2.2 — RLS on pool_agent_runs, pool_agent_assignments, agent_template_catalog.

Revision ID: 220
Revises: 219
Create Date: 2026-05-29

Context (Fase 2.5 Onda C2.2 — AUDIT 6 P0-2):
  pool_agent_runs (36 rows), pool_agent_assignments (32 rows) and
  agent_template_catalog (15 rows) had RLS OFF — the only tenant-data layer left
  without the Postgres defense-in-depth that the rest of the system already has.

  Canonical pattern (mirrors migration 196 tasks_rls_policy / job_vacancies):
  4 permissive policies (select/insert/update/delete) using the helper
  app_current_company_id() (reads current_setting('app.company_id')). ENABLE +
  FORCE so even table owners are subject to the policy.

  SPECIAL CASE — agent_template_catalog:
  All 15 rows have company_id IS NULL: this is the GLOBAL catalog (templates
  shared across all tenants; reads are "TENANT-EXEMPT" per
  agent_template_catalog_repository.py). A strict
  "(company_id)::text = app_current_company_id()" SELECT policy would make every
  global template invisible to every tenant (NULL is never equal), breaking the
  catalog feature. So the SELECT policy here also admits NULL-company rows
  (global templates visible to all), while INSERT/UPDATE/DELETE remain
  tenant-owned-only (a tenant cannot create or mutate a global template — that is
  reserved for the system/admin seed path, which runs outside RLS).
"""
from alembic import op

revision = "220"
down_revision = "219"
branch_labels = None
depends_on = None

# Tables that follow the standard 4-policy canonical pattern (all rows tenant-scoped).
_STANDARD = ("pool_agent_runs", "pool_agent_assignments")
# Global catalog: SELECT also admits company_id IS NULL (shared templates).
_GLOBAL_CATALOG = "agent_template_catalog"
_ALL = _STANDARD + (_GLOBAL_CATALOG,)


def _enable(table: str) -> None:
    op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;")
    op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY;")


def _standard_policies(table: str) -> None:
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


def _global_catalog_policies(table: str) -> None:
    # SELECT: global templates (company_id NULL) visible to all + tenant-owned.
    op.execute(
        f"CREATE POLICY {table}_tenant_select ON {table} "
        f"FOR SELECT USING "
        f"(company_id IS NULL OR (company_id)::text = app_current_company_id());"
    )
    # Writes: tenant-owned only. NULL company_id (global seed) is written by the
    # system/admin path which is not subject to RLS, so excluding NULL here is safe.
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


def _drop_policies(table: str) -> None:
    for cmd in ("delete", "update", "insert", "select"):
        op.execute(f"DROP POLICY IF EXISTS {table}_tenant_{cmd} ON {table};")


def upgrade() -> None:
    for table in _STANDARD:
        _enable(table)
        _standard_policies(table)
    _enable(_GLOBAL_CATALOG)
    _global_catalog_policies(_GLOBAL_CATALOG)


def downgrade() -> None:
    for table in _ALL:
        _drop_policies(table)
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY;")
