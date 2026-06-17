"""Add RLS deny-by-default for T6 — Operational/Sessions/Agent (21 tables) (migration 124).

Revision ID: 124_rls_t6_operational
Revises: 123_rls_t5_learning_ml
Create Date: 2026-05-07

Sprint 5.9 RLS T6 — operational/session/agent tables. Closes 21 RLS gaps.

21 tables protected; 7 have nullable company_id
(predicate fails-open on NULL to preserve existing reads, enforces tenant for non-NULL).

Pattern (canonical from 119/120/121):
- UUID `company_id` → `company_id::text = app_current_company_id()`
- VARCHAR `company_id` → `company_id = app_current_company_id()`
- NULLABLE → `(company_id IS NULL) OR (...)`

Idempotent: DROP POLICY IF EXISTS guards. Reversible downgrade.
"""
from alembic import op


revision = '124_rls_t6_operational'
down_revision = '123_rls_t5_learning_ml'
depends_on = None

# (table_name, company_id_type, nullable)
TABLES = [
    ('activity_feed', 'varchar', True),
    ('agent_activities', 'varchar', True),
    ('agent_execution_logs', 'varchar', False),
    ('conversations', 'varchar', True),
    ('graph_sessions', 'uuid', False),
    ('hiring_plans', 'uuid', False),
    ('import_batches', 'uuid', False),
    ('interaction_feedback', 'uuid', False),
    ('job_templates', 'uuid', True),
    ('journey_blueprints', 'uuid', False),
    ('lia_field_toggles', 'uuid', False),
    ('manager_preferences', 'varchar', False),
    ('offer_proposals', 'varchar', False),
    ('proactive_actions', 'uuid', False),
    ('recruiter_decision_feedback', 'varchar', False),
    ('recruitment_templates', 'uuid', False),
    ('routing_feedback', 'varchar', False),
    ('teams_conversations', 'varchar', True),
    ('teams_feedback', 'varchar', True),
    ('technical_test_templates', 'uuid', True),
    ('template_usage_logs', 'uuid', False),
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
