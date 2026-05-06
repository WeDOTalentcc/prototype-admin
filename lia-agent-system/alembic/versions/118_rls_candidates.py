"""Add RLS deny-by-default to candidates table (ADR-030 v2 Sprint 4A).

Revision ID: 118_rls_candidates
Revises: 30c0e47d1f56
Create Date: 2026-05-06

Closes the highest-value RLS gap identified in audit D 2026-05-06: the
`candidates` table has direct `company_id NOT NULL` but was never added
to migration 068's RLS coverage list. Candidates carries PII (name,
email, CPF, etc.) — the most sensitive surface of the platform.

Pattern follows 068_rls_deny_by_default verbatim:
- ENABLE + FORCE ROW LEVEL SECURITY
- 4 policies: tenant_select / tenant_insert / tenant_update / tenant_delete
- Predicate: `company_id = app_current_company_id()`

The 4 transitively-isolated tables (wsi_sessions, wsi_results,
screening_question_sets, messages) are deferred to a follow-up
migration. They lack direct `company_id` column — RLS would require
subquery on parent tables (job_vacancies / candidates / conversations),
which has performance implications that warrant separate testing.

Compatibility: idempotent (uses IF NOT EXISTS-style guards). Safe to
re-run after partial application. Downgrade fully reversible.
"""
from alembic import op


revision = "118_rls_candidates"
down_revision = "30c0e47d1f56"
depends_on = None

TABLE = "candidates"


def upgrade() -> None:
    # ENABLE + FORCE RLS (FORCE ensures even table owner is subject to policies)
    op.execute(f"ALTER TABLE {TABLE} ENABLE ROW LEVEL SECURITY;")
    op.execute(f"ALTER TABLE {TABLE} FORCE ROW LEVEL SECURITY;")

    # Drop policies first (idempotent re-run safety)
    for op_kind in ("select", "insert", "update", "delete"):
        op.execute(
            f"DROP POLICY IF EXISTS {TABLE}_tenant_{op_kind} ON {TABLE};"
        )

    op.execute(f"""
        CREATE POLICY {TABLE}_tenant_select ON {TABLE}
            FOR SELECT
            USING (company_id = app_current_company_id());
    """)

    op.execute(f"""
        CREATE POLICY {TABLE}_tenant_insert ON {TABLE}
            FOR INSERT
            WITH CHECK (company_id = app_current_company_id());
    """)

    op.execute(f"""
        CREATE POLICY {TABLE}_tenant_update ON {TABLE}
            FOR UPDATE
            USING (company_id = app_current_company_id());
    """)

    op.execute(f"""
        CREATE POLICY {TABLE}_tenant_delete ON {TABLE}
            FOR DELETE
            USING (company_id = app_current_company_id());
    """)

    # Grant lia_app role minimal access (mirrors 068 pattern)
    op.execute(f"GRANT SELECT, INSERT, UPDATE, DELETE ON {TABLE} TO lia_app;")


def downgrade() -> None:
    for op_kind in ("delete", "update", "insert", "select"):
        op.execute(
            f"DROP POLICY IF EXISTS {TABLE}_tenant_{op_kind} ON {TABLE};"
        )
    op.execute(f"ALTER TABLE {TABLE} NO FORCE ROW LEVEL SECURITY;")
    op.execute(f"ALTER TABLE {TABLE} DISABLE ROW LEVEL SECURITY;")
    op.execute(f"REVOKE SELECT, INSERT, UPDATE, DELETE ON {TABLE} FROM lia_app;")
