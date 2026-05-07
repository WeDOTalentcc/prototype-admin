"""Add RLS deny-by-default for T7 — Admin/RBAC/Infra (12 tables) (migration 125).

Revision ID: 125_rls_t7_admin_rbac
Revises: 124_rls_t6_operational
Create Date: 2026-05-07

Sprint 5.9 RLS T7 — admin/RBAC/infra tables. Closes 12 RLS gaps.

IMPORTANT: admin_roles, admin_user_roles, sod_roles are RBAC tables.
Any admin tooling that queries cross-tenant must use a session-bypass mechanism
or service role; this migration enforces strict tenant scope.

12 tables protected; 6 have nullable company_id
(predicate fails-open on NULL to preserve existing reads, enforces tenant for non-NULL).

Pattern (canonical from 119/120/121):
- UUID `company_id` → `company_id::text = app_current_company_id()`
- VARCHAR `company_id` → `company_id = app_current_company_id()`
- NULLABLE → `(company_id IS NULL) OR (...)`

Idempotent: DROP POLICY IF EXISTS guards. Reversible downgrade.
"""
from alembic import op


revision = '125_rls_t7_admin_rbac'
down_revision = '124_rls_t6_operational'
depends_on = None

# (table_name, company_id_type, nullable)
TABLES = [
    ('admin_roles', 'uuid', False),
    ('admin_user_roles', 'uuid', False),
    ('business_rules', 'uuid', True),
    ('cache_entries', 'varchar', True),
    ('escalation_logs', 'uuid', True),
    ('escalation_rules', 'uuid', True),
    ('insurance_policies', 'uuid', False),
    ('integration_connections', 'uuid', False),
    ('notification_policies', 'uuid', False),
    ('policy_evaluation_logs', 'uuid', True),
    ('rate_limit_rules', 'uuid', True),
    ('sod_roles', 'uuid', False),
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
