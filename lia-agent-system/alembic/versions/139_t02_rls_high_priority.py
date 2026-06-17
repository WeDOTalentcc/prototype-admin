"""T-02 RLS HIGH priority tables (27 tabelas com company_id no DB live).

Revision ID: 139_t02_rls_high_priority
Revises: 143_p2_nullable_batch_canonical
Create Date: 2026-05-20

Aplica RLS deny-by-default em 27 tabelas HIGH-priority que JA TEM company_id
no DB live (validado via information_schema query).

Plano: PLANO_ACAO_REPLIT_V3 T-02 (escopo corrigido pos auditoria DB live).
Pattern: 068_rls_deny_by_default.py (canonical multi-tenant).

Sensor: scripts/check_table_has_rls_policy.py
- Baseline: 176 GAPS
- Apos esta migration: 149 GAPS (-27)

Compliance: LGPD Art. 6/11/20 + EU AI Act Annex III item 4.

T-02b sprint 2 enderecara 24 tabelas com drift modelo<->DB (precisam ADD COLUMN):
ats_candidates, big_five_questions, calibration_feedback, calibration_sessions,
calibration_suggestions, candidate_education, candidate_experiences,
candidate_list_members, candidate_merge_audit, candidate_searches, candidate_sources,
conversation_summaries, data_request_responses, email_logs, interview_feedbacks,
profile_calculation_logs, prompt_variants, talent_pool_candidates, teams_messages,
teams_notifications, triagem_messages, twin_decisions, viewed_candidates,
whatsapp_messages.

Subset NULLABLE backfilled:
- UUID type: '00000000-0000-0000-0000-000000000001'::uuid (sentinel)
- character varying: 'demo_company' (alinhado com 068)

Policy usa cast `company_id::text = app_current_company_id()` para suportar
ambos uuid e varchar column types sem branching.
"""
from alembic import op


# revision identifiers
revision = "139_t02_rls_high_priority"
down_revision = "143_p2_nullable_batch_canonical"
branch_labels = None
depends_on = None


# 18 tabelas NOT NULL no DB live — RLS direto sem backfill
HIGH_TABLES_NOT_NULL = [
    "bias_audit_reports",                # uuid
    "bigfive_department_profiles",       # varchar
    "consent_versions",                  # uuid
    "conversation_memories",             # uuid
    "data_access_logs",                  # uuid
    "data_incidents",                    # varchar
    "data_requests",                     # uuid
    "data_subject_requests",             # uuid
    "dpo_registry",                      # uuid
    "ideal_profiles",                    # uuid
    "import_batches",                    # uuid
    "imported_job_descriptions",         # uuid
    "interaction_feedback",              # uuid
    "interview_notes",                   # uuid
    "learning_patterns",                 # uuid
    "recruiter_decision_feedback",       # varchar
    "routing_feedback",                  # varchar
    "wsi_question_effectiveness",        # varchar
]

# 4 tabelas NULLABLE UUID — backfill UUID sentinel
HIGH_TABLES_NULLABLE_UUID = [
    "big_five_role_profiles",
    "fairness_audit_log",
    "incident_reports",
    "model_evaluations",
]

# 5 tabelas NULLABLE varchar — backfill 'demo_company'
HIGH_TABLES_NULLABLE_VARCHAR = [
    "calibration_events",
    "calibration_weights",
    "conversations",
    "ml_model_registry",
    "teams_conversations",
]

ALL_HIGH = (
    HIGH_TABLES_NOT_NULL
    + HIGH_TABLES_NULLABLE_UUID
    + HIGH_TABLES_NULLABLE_VARCHAR
)

SENTINEL_UUID = "00000000-0000-0000-0000-000000000001"
SENTINEL_STRING = "demo_company"


def upgrade() -> None:
    """Apply RLS deny-by-default to 27 HIGH priority tables."""

    # Step 1: Backfill UUID NULLABLE
    for table in HIGH_TABLES_NULLABLE_UUID:
        op.execute(
            f"UPDATE {table} SET company_id = '{SENTINEL_UUID}'::uuid "
            f"WHERE company_id IS NULL;"
        )
        op.execute(f"ALTER TABLE {table} ALTER COLUMN company_id SET NOT NULL;")

    # Step 2: Backfill varchar NULLABLE
    for table in HIGH_TABLES_NULLABLE_VARCHAR:
        op.execute(
            f"UPDATE {table} SET company_id = '{SENTINEL_STRING}' "
            f"WHERE company_id IS NULL;"
        )
        op.execute(f"ALTER TABLE {table} ALTER COLUMN company_id SET NOT NULL;")

    # Step 3: RLS + 4 policies por tabela
    for table in ALL_HIGH:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY;")

        # Idempotente
        op.execute(f"DROP POLICY IF EXISTS {table}_tenant_select ON {table};")
        op.execute(f"DROP POLICY IF EXISTS {table}_tenant_insert ON {table};")
        op.execute(f"DROP POLICY IF EXISTS {table}_tenant_update ON {table};")
        op.execute(f"DROP POLICY IF EXISTS {table}_tenant_delete ON {table};")

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
    for table in reversed(ALL_HIGH):
        op.execute(f"DROP POLICY IF EXISTS {table}_tenant_select ON {table};")
        op.execute(f"DROP POLICY IF EXISTS {table}_tenant_insert ON {table};")
        op.execute(f"DROP POLICY IF EXISTS {table}_tenant_update ON {table};")
        op.execute(f"DROP POLICY IF EXISTS {table}_tenant_delete ON {table};")
        op.execute(f"ALTER TABLE {table} NO FORCE ROW LEVEL SECURITY;")
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY;")

    for table in reversed(
        HIGH_TABLES_NULLABLE_UUID + HIGH_TABLES_NULLABLE_VARCHAR
    ):
        op.execute(
            f"ALTER TABLE {table} ALTER COLUMN company_id DROP NOT NULL;"
        )
