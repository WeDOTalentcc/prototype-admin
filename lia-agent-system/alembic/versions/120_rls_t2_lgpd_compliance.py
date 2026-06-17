"""Add RLS deny-by-default for T2 LGPD/Compliance/Agent Studio (Sprint 5.3 batch).

Revision ID: 120_rls_t2_lgpd_compliance
Revises: 119_rls_t1_lgpd_pii
Create Date: 2026-05-07

Closes 14 direct-`company_id NOT NULL` RLS gaps. Pre-flight verified:
- 0 FK cascade risk
- 17 total rows (15 in company_compliance_controls + 2 in
  data_subject_requests; rest empty) — near-zero apply risk
- Mixed UUID + VARCHAR types validate both code paths

Tables protected (14):
  LGPD/data (8 — 7 UUID + 1 VARCHAR):
    - consent_versions
    - data_requests
    - data_subject_requests
    - data_request_configs
    - data_request_fields
    - data_request_templates
    - dpo_registry
    - data_incidents (VARCHAR)
  Compliance/SOX (2 UUID):
    - sox_controls
    - company_compliance_controls
  Agent Studio (3 VARCHAR):
    - agent_approval_requests
    - agent_deployments
    - agent_version_snapshots
  PII (1 UUID):
    - interview_notes

DEFERRED to Sprint 5.5+ (require `cross_tenant_session` for known
background writers): admin_audit_logs, bias_audit_reports,
bias_audit_snapshots, data_access_logs, agent_execution_logs,
compliance_audits.

Pattern variants applied:
- UUID `company_id` → `company_id::text = app_current_company_id()`
- VARCHAR `company_id` → `company_id = app_current_company_id()`

Idempotent: DROP POLICY IF EXISTS guards. Reversible downgrade.
"""
from alembic import op


revision = "120_rls_t2_lgpd_compliance"
down_revision = "119_rls_t1_lgpd_pii"
depends_on = None

# (table_name, company_id type) — drives cast policy
TABLES = [
    # LGPD/data — UUID
    ("consent_versions", "uuid"),
    ("data_requests", "uuid"),
    ("data_subject_requests", "uuid"),
    ("data_request_configs", "uuid"),
    ("data_request_fields", "uuid"),
    ("data_request_templates", "uuid"),
    ("dpo_registry", "uuid"),
    # LGPD/data — VARCHAR
    ("data_incidents", "varchar"),
    # Compliance/SOX — UUID
    ("sox_controls", "uuid"),
    ("company_compliance_controls", "uuid"),
    # Agent Studio — VARCHAR
    ("agent_approval_requests", "varchar"),
    ("agent_deployments", "varchar"),
    ("agent_version_snapshots", "varchar"),
    # PII — UUID
    ("interview_notes", "uuid"),
]


def _company_id_predicate(cid_type: str) -> str:
    """Generate the WHERE/CHECK predicate based on column type."""
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

        # Idempotent re-run safety
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
