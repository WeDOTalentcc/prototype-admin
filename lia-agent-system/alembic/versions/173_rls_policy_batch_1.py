"""RLS deny-by-default batch 1 — close 9 remaining direct-`company_id` gaps.

Revision ID: 173_rls_policy_batch_1
Revises: 172_offer_proposal_department
Create Date: 2026-05-22

Closes the 9 RLS gaps that survived the T1-T8 + T-02 sprints (139). Live DB
inventory (cross-referenced with sensor 2026-05-22):
- 177 tables flagged by check_table_has_rls_policy.py
- 100 already have RLS+4 policies in DB live (sensor false positives — parser
  misses tuples `("table", "uuid")` in T-02b style migrations). These are
  documented in scripts/.rls_allowlist.txt with source migration.
- 68 lack the `company_id` column in DB live (model<>DB drift — out-of-scope
  for this batch; tracked separately in T-02b sprint plan).
- 9 truly need RLS — this migration's scope.

Pattern follows 139_t02_rls_high_priority verbatim:
- ENABLE + FORCE ROW LEVEL SECURITY
- 4 policies: tenant_<select|insert|update|delete>
- Cast `company_id::text = app_current_company_id()` for both UUID and VARCHAR
- Backfill NULLABLE columns with sentinel before SET NOT NULL

All 9 target tables are EMPTY in DB live (verified 2026-05-22). Apply risk: zero.

Compliance: LGPD Art. 37 (credentials access trail), Art. 6 II (consent),
EU AI Act Art. 10/12 (bandit experiment isolation), SOX-style audit
(eligibility_question_templates as tenant configuration).

Skills aplicadas: canonical-fix (template DRY), production-quality:canonical-standards,
harness-engineering (sensor BLOCKING ratchet), TDD (5 smoke tests in
tests/contract/test_rls_policy_enforces_isolation.py).

ADR: see ADR-030 v2 Postgres RLS Coverage.
"""
from alembic import op


# revision identifiers, used by Alembic
revision = "173_rls_policy_batch_1"
down_revision = "172_offer_proposal_department"
branch_labels = None
depends_on = None


# 2 tables NOT NULL — RLS direto sem backfill (rowcount=0 live)
BATCH_1_NOT_NULL = [
    # LGPD Art. 37: trilha de acesso a credenciais 3rd-party integrations
    ("credentials_access_logs", "uuid"),
    # LGPD Art. 6 II: consentimento de treinamento de modelo per-company
    ("company_training_consents", "uuid"),
]

# 7 tables NULLABLE — backfill UUID/varchar sentinel, then RLS
BATCH_1_NULLABLE_UUID = [
    # EU AI Act Art. 10: posteriores de bandit experiment per-tenant
    "bandit_posteriors",
]

BATCH_1_NULLABLE_VARCHAR = [
    # Tenant config templates (mismatch sensor: tem company_id NULLABLE)
    "alert_rule_templates",
    "eligibility_question_templates",
    "integration_catalog_entries",
    "pipeline_stage_templates",
    "recruiter_field_preferences",
    "webhook_event_types",
]

ALL_BATCH_1 = (
    [t for t, _ in BATCH_1_NOT_NULL]
    + BATCH_1_NULLABLE_UUID
    + BATCH_1_NULLABLE_VARCHAR
)

SENTINEL_UUID = "00000000-0000-0000-0000-000000000001"
SENTINEL_STRING = "demo_company"


def upgrade() -> None:
    """Apply RLS deny-by-default to 9 remaining tables."""

    # Step 1: Backfill UUID NULLABLE → SET NOT NULL
    for table in BATCH_1_NULLABLE_UUID:
        op.execute(
            f"UPDATE {table} SET company_id = '{SENTINEL_UUID}'::uuid "
            f"WHERE company_id IS NULL;"
        )
        op.execute(
            f"ALTER TABLE {table} ALTER COLUMN company_id SET NOT NULL;"
        )

    # Step 2: Backfill VARCHAR NULLABLE → SET NOT NULL
    for table in BATCH_1_NULLABLE_VARCHAR:
        op.execute(
            f"UPDATE {table} SET company_id = '{SENTINEL_STRING}' "
            f"WHERE company_id IS NULL;"
        )
        op.execute(
            f"ALTER TABLE {table} ALTER COLUMN company_id SET NOT NULL;"
        )

    # Step 3: ENABLE + FORCE RLS + 4 policies per table
    for table in ALL_BATCH_1:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY;")

        # Idempotente
        op.execute(
            f"DROP POLICY IF EXISTS {table}_tenant_select ON {table};"
        )
        op.execute(
            f"DROP POLICY IF EXISTS {table}_tenant_insert ON {table};"
        )
        op.execute(
            f"DROP POLICY IF EXISTS {table}_tenant_update ON {table};"
        )
        op.execute(
            f"DROP POLICY IF EXISTS {table}_tenant_delete ON {table};"
        )

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


def downgrade() -> None:
    """Reverse RLS + restore NULLABLE state (sentinel data preserved)."""
    for table in reversed(ALL_BATCH_1):
        op.execute(
            f"DROP POLICY IF EXISTS {table}_tenant_select ON {table};"
        )
        op.execute(
            f"DROP POLICY IF EXISTS {table}_tenant_insert ON {table};"
        )
        op.execute(
            f"DROP POLICY IF EXISTS {table}_tenant_update ON {table};"
        )
        op.execute(
            f"DROP POLICY IF EXISTS {table}_tenant_delete ON {table};"
        )
        op.execute(f"ALTER TABLE {table} NO FORCE ROW LEVEL SECURITY;")
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY;")

    for table in reversed(
        BATCH_1_NULLABLE_UUID + BATCH_1_NULLABLE_VARCHAR
    ):
        op.execute(
            f"ALTER TABLE {table} ALTER COLUMN company_id DROP NOT NULL;"
        )
