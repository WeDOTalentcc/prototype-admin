"""Add RLS deny-by-default for T1 LGPD/PII tables (Sprint 5.2 batch 1).

Revision ID: 119_rls_t1_lgpd_pii
Revises: 118_rls_candidates
Create Date: 2026-05-07

Closes 6 direct-company_id RLS gaps in LGPD-critical tables identified
by Sprint 5.2 column-level narrowing of Audit I's T1 list:
- consent_records (LGPD Art. 8 — consent registry)
- consent_events (LGPD Art. 8 — consent state changes)
- breach_notifications (LGPD Art. 48 — incident response)
- automated_decision_explanations (LGPD Art. 20 — human review trail)
- ai_inference_logs (PII surface — model decisions traceability)
- shared_searches (demo UUID pattern; 0 rows in dev DB)

UUID pattern (NOT in 068's coverage which uses VARCHAR):
- All 6 tables use `company_id UUID NOT NULL`
- `app_current_company_id()` returns TEXT — must cast `company_id::text`
- 068 used `company_id = app_current_company_id()` (varchar = text, no cast)
- 119 uses `company_id::text = app_current_company_id()` for UUID

Idempotent: DROP POLICY IF EXISTS guards. Reversible downgrade.
"""
from alembic import op


revision = "119_rls_t1_lgpd_pii"
down_revision = "118_rls_candidates"
depends_on = None

TABLES = [
    "consent_records",
    "consent_events",
    "breach_notifications",
    "automated_decision_explanations",
    "ai_inference_logs",
    "shared_searches",
]


def upgrade() -> None:
    for table in TABLES:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY;")

        # Idempotent re-run safety
        for op_kind in ("select", "insert", "update", "delete"):
            op.execute(
                f"DROP POLICY IF EXISTS {table}_tenant_{op_kind} ON {table};"
            )

        # UUID company_id requires explicit ::text cast for comparison with
        # app_current_company_id() (which returns text from current_setting)
        op.execute(f"""
            CREATE POLICY {table}_tenant_select ON {table}
                FOR SELECT
                USING (company_id::text = app_current_company_id());
        """)

        op.execute(f"""
            CREATE POLICY {table}_tenant_insert ON {table}
                FOR INSERT
                WITH CHECK (company_id::text = app_current_company_id());
        """)

        op.execute(f"""
            CREATE POLICY {table}_tenant_update ON {table}
                FOR UPDATE
                USING (company_id::text = app_current_company_id());
        """)

        op.execute(f"""
            CREATE POLICY {table}_tenant_delete ON {table}
                FOR DELETE
                USING (company_id::text = app_current_company_id());
        """)

        # Grant lia_app role minimal access (mirrors 068/118 pattern)
        op.execute(
            f"GRANT SELECT, INSERT, UPDATE, DELETE ON {table} TO lia_app;"
        )


def downgrade() -> None:
    for table in reversed(TABLES):
        for op_kind in ("delete", "update", "insert", "select"):
            op.execute(
                f"DROP POLICY IF EXISTS {table}_tenant_{op_kind} ON {table};"
            )
        op.execute(f"ALTER TABLE {table} NO FORCE ROW LEVEL SECURITY;")
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY;")
        op.execute(
            f"REVOKE SELECT, INSERT, UPDATE, DELETE ON {table} FROM lia_app;"
        )
