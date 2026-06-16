"""Add RLS deny-by-default for T4 — Audit/Compliance (11 tables) (migration 122).

Revision ID: 122_rls_t4_audit_compliance
Revises: 121_rls_t3_batch
Create Date: 2026-05-07

Sprint 5.9 RLS T4 — audit/compliance tables. Closes 11 RLS gaps.

11 tables protected; 4 have nullable company_id
(predicate fails-open on NULL to preserve existing reads, enforces tenant for non-NULL).

Pattern (canonical from 119/120/121):
- UUID `company_id` → `company_id::text = app_current_company_id()`
- VARCHAR `company_id` → `company_id = app_current_company_id()`
- NULLABLE → `(company_id IS NULL) OR (...)`

Idempotent: DROP POLICY IF EXISTS guards. Reversible downgrade.
"""
from alembic import op


revision = '122_rls_t4_audit_compliance'
down_revision = '121_rls_t3_batch'
depends_on = None

# (table_name, company_id_type, nullable)
TABLES = [
    ('admin_audit_logs', 'uuid', False),
    ('bias_audit_reports', 'uuid', False),
    ('bias_audit_snapshots', 'uuid', False),
    ('compliance_audits', 'uuid', False),
    ('compliance_controls', 'uuid', True),
    ('continuity_tests', 'uuid', False),
    ('data_access_logs', 'uuid', False),
    ('disaster_recovery_plans', 'uuid', False),
    ('fairness_audit_log', 'uuid', True),
    ('incident_reports', 'uuid', True),
    ('sox_audit_logs', 'uuid', True),
]


def _predicate(cid_type: str, nullable: bool) -> str:
    if cid_type == "uuid":
        core = "company_id::text = app_current_company_id()"
    elif cid_type == "varchar":
        core = "company_id = app_current_company_id()"
    else:
        raise ValueError(f"Unknown cid_type: {cid_type}")
    if nullable:
        return f"((company_id IS NULL) OR ({core}))"
    return core


def upgrade() -> None:
    for table, cid_type, nullable in TABLES:
        pred = _predicate(cid_type, nullable)

        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY;")

        for op_kind in ("select", "insert", "update", "delete"):
            op.execute(
                f"DROP POLICY IF EXISTS {table}_tenant_{op_kind} ON {table};"
            )

        op.execute(f"""
            CREATE POLICY {table}_tenant_select ON {table}
                FOR SELECT
                USING ({pred});
        """)
        op.execute(f"""
            CREATE POLICY {table}_tenant_insert ON {table}
                FOR INSERT
                WITH CHECK ({pred});
        """)
        op.execute(f"""
            CREATE POLICY {table}_tenant_update ON {table}
                FOR UPDATE
                USING ({pred});
        """)
        op.execute(f"""
            CREATE POLICY {table}_tenant_delete ON {table}
                FOR DELETE
                USING ({pred});
        """)

        op.execute(
            f"GRANT SELECT, INSERT, UPDATE, DELETE ON {table} TO lia_app;"
        )


def downgrade() -> None:
    for table, _, _ in reversed(TABLES):
        for op_kind in ("delete", "update", "insert", "select"):
            op.execute(
                f"DROP POLICY IF EXISTS {table}_tenant_{op_kind} ON {table};"
            )
        op.execute(f"ALTER TABLE {table} NO FORCE ROW LEVEL SECURITY;")
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY;")
        op.execute(
            f"REVOKE SELECT, INSERT, UPDATE, DELETE ON {table} FROM lia_app;"
        )
