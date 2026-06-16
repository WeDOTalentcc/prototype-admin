"""Add RLS policy for tasks table (company isolation).

Revision ID: 196
Revises: 195
Create Date: 2026-05-25

Context (P0 re-validation 2026-05-25):
  tasks.company_id is NOT NULL (added by migration 161 — WT-2022 P0.TASK fix).
  RLS was never applied, leaving defense-in-depth gap: only Python service layer
  enforced isolation. Any future raw-SQL path or new service that misses
  _require_company_id would leak cross-tenant data silently.

Pattern: mirrors job_vacancies RLS (4 policies, permissive, public role).
Function app_current_company_id() already exists from migration 040.
"""
from alembic import op

revision = "196"
down_revision = "195"
depends_on = None

TABLE = "tasks"


def upgrade() -> None:
    op.execute(f"ALTER TABLE {TABLE} ENABLE ROW LEVEL SECURITY;")
    op.execute(f"ALTER TABLE {TABLE} FORCE ROW LEVEL SECURITY;")

    op.execute(f"""
        CREATE POLICY {TABLE}_tenant_select ON {TABLE}
            FOR SELECT
            USING ((company_id)::text = app_current_company_id());
    """)

    op.execute(f"""
        CREATE POLICY {TABLE}_tenant_insert ON {TABLE}
            FOR INSERT
            WITH CHECK ((company_id)::text = app_current_company_id());
    """)

    op.execute(f"""
        CREATE POLICY {TABLE}_tenant_update ON {TABLE}
            FOR UPDATE
            USING ((company_id)::text = app_current_company_id());
    """)

    op.execute(f"""
        CREATE POLICY {TABLE}_tenant_delete ON {TABLE}
            FOR DELETE
            USING ((company_id)::text = app_current_company_id());
    """)


def downgrade() -> None:
    op.execute(f"DROP POLICY IF EXISTS {TABLE}_tenant_delete ON {TABLE};")
    op.execute(f"DROP POLICY IF EXISTS {TABLE}_tenant_update ON {TABLE};")
    op.execute(f"DROP POLICY IF EXISTS {TABLE}_tenant_insert ON {TABLE};")
    op.execute(f"DROP POLICY IF EXISTS {TABLE}_tenant_select ON {TABLE};")
    op.execute(f"ALTER TABLE {TABLE} DISABLE ROW LEVEL SECURITY;")
