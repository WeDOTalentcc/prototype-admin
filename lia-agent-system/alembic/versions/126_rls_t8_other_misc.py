"""Add RLS deny-by-default for T8 — Other/Misc (18 tables) (migration 126).

Revision ID: 126_rls_t8_other_misc
Revises: 125_rls_t7_admin_rbac
Create Date: 2026-05-07

Sprint 5.9 RLS T8 — final batch. Closes remaining 18 RLS gaps.

Mix of trust_center, salary_benchmarks, security_settings, wsi_*, workforce_*,
token_usage, technical_tests, recruitment_*. Manual triage already complete.

18 tables protected; 3 have nullable company_id
(predicate fails-open on NULL to preserve existing reads, enforces tenant for non-NULL).

Pattern (canonical from 119/120/121):
- UUID `company_id` → `company_id::text = app_current_company_id()`
- VARCHAR `company_id` → `company_id = app_current_company_id()`
- NULLABLE → `(company_id IS NULL) OR (...)`

Idempotent: DROP POLICY IF EXISTS guards. Reversible downgrade.
"""
from alembic import op


revision = '126_rls_t8_other_misc'
down_revision = '125_rls_t7_admin_rbac'
depends_on = None

# (table_name, company_id_type, nullable)
TABLES = [
    ('recruitment_automations', 'uuid', False),
    ('recruitment_slas', 'uuid', False),
    ('risk_entries', 'uuid', False),
    ('salary_benchmarks', 'uuid', False),
    ('security_settings', 'uuid', False),
    ('skill_clusters', 'uuid', False),
    ('sla_violations', 'uuid', False),
    ('sod_conflicts', 'uuid', False),
    ('studio_webhooks', 'varchar', False),
    ('technical_tests', 'varchar', True),
    ('token_usage_logs', 'varchar', False),
    ('trust_center_resources', 'uuid', False),
    ('trust_center_settings', 'uuid', False),
    ('trust_center_subprocessors', 'uuid', False),
    ('trust_center_updates', 'uuid', False),
    ('workforce_entries', 'uuid', True),
    ('wsi_question_effectiveness', 'varchar', False),
    ('wsi_responses', 'varchar', True),
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
