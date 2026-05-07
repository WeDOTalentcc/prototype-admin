"""Add RLS deny-by-default for T3 batch (Sprint 5.7 — 20 tables).

Revision ID: 121_rls_t3_batch
Revises: 120_rls_t2_lgpd_compliance
Create Date: 2026-05-07

Closes 20 direct-`company_id NOT NULL` RLS gaps. Continues the pattern
from 119/120: mix UUID + VARCHAR, mixed domain (billing/RBAC/analytics/
events). Apply risk minimal: 603 rows total across all 20 tables, all
with NOT NULL company_id.

Tables protected (20):
  Billing/usage (4 — 2 UUID + 2 VARCHAR):
    - ai_consumption (UUID)
    - ai_credits_balance (UUID)
    - external_api_consumption (VARCHAR — 540 rows, biggest)
    - feedback_events (VARCHAR)
  RBAC/approval (4 UUID):
    - approval_requests
    - approvers
    - client_users
    - admin_roles  (NOT included this batch — defer to T4)
    [actual: client_users + approvers + approval_requests + client_skill_catalogs]
  Workflow/queue (3 UUID):
    - background_jobs
    - business_processes
    - culture_analysis_jobs
  Org/membership (4 UUID):
    - departments
    - department_members
    - benefits
    - company_calendar_credentials
  Analytics/profiles (4 — 3 UUID + 1 VARCHAR):
    - company_culture_profiles (UUID)
    - culture_values (UUID)
    - conversation_memories (UUID)
    - bigfive_department_profiles (VARCHAR)
  Events (1 VARCHAR):
    - domain_events

Type mix: 16 UUID + 4 VARCHAR.

Pattern variants (canonical from 119/120):
- UUID `company_id` → `company_id::text = app_current_company_id()`
- VARCHAR `company_id` → `company_id = app_current_company_id()`
  (Postgres normalizes both to `((company_id)::text = ...)` at storage)

Idempotent: DROP POLICY IF EXISTS guards. Reversible downgrade.
"""
from alembic import op


revision = "121_rls_t3_batch"
down_revision = "120_rls_t2_lgpd_compliance"
depends_on = None

# (table_name, company_id type) — drives cast policy
TABLES = [
    # Billing/usage
    ("ai_consumption", "uuid"),
    ("ai_credits_balance", "uuid"),
    ("external_api_consumption", "varchar"),
    ("feedback_events", "varchar"),
    # RBAC/approval
    ("approval_requests", "uuid"),
    ("approvers", "uuid"),
    ("client_users", "uuid"),
    ("client_skill_catalogs", "uuid"),
    # Workflow/queue
    ("background_jobs", "uuid"),
    ("business_processes", "uuid"),
    ("culture_analysis_jobs", "uuid"),
    # Org/membership
    ("departments", "uuid"),
    ("department_members", "uuid"),
    ("benefits", "uuid"),
    ("company_calendar_credentials", "uuid"),
    # Analytics/profiles
    ("company_culture_profiles", "uuid"),
    ("culture_values", "uuid"),
    ("conversation_memories", "uuid"),
    ("bigfive_department_profiles", "varchar"),
    # Events
    ("domain_events", "varchar"),
]


def _company_id_predicate(cid_type: str) -> str:
    if cid_type == "uuid":
        return "company_id::text = app_current_company_id()"
    elif cid_type == "varchar":
        return "company_id = app_current_company_id()"
    else:
        raise ValueError(f"Unknown cid_type: {cid_type}")


def upgrade() -> None:
    for table, cid_type in TABLES:
        predicate = _company_id_predicate(cid_type)

        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY;")

        for op_kind in ("select", "insert", "update", "delete"):
            op.execute(
                f"DROP POLICY IF EXISTS {table}_tenant_{op_kind} ON {table};"
            )

        op.execute(f"""
            CREATE POLICY {table}_tenant_select ON {table}
                FOR SELECT
                USING ({predicate});
        """)
        op.execute(f"""
            CREATE POLICY {table}_tenant_insert ON {table}
                FOR INSERT
                WITH CHECK ({predicate});
        """)
        op.execute(f"""
            CREATE POLICY {table}_tenant_update ON {table}
                FOR UPDATE
                USING ({predicate});
        """)
        op.execute(f"""
            CREATE POLICY {table}_tenant_delete ON {table}
                FOR DELETE
                USING ({predicate});
        """)

        op.execute(
            f"GRANT SELECT, INSERT, UPDATE, DELETE ON {table} TO lia_app;"
        )


def downgrade() -> None:
    for table, _ in reversed(TABLES):
        for op_kind in ("delete", "update", "insert", "select"):
            op.execute(
                f"DROP POLICY IF EXISTS {table}_tenant_{op_kind} ON {table};"
            )
        op.execute(f"ALTER TABLE {table} NO FORCE ROW LEVEL SECURITY;")
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY;")
        op.execute(
            f"REVOKE SELECT, INSERT, UPDATE, DELETE ON {table} FROM lia_app;"
        )
