"""Audit and identify legacy company_id values for tenant migration.

Phase 1 (this migration): Identifies and reports records with legacy
company_id values ('default', 'demo_company', null UUID, deprecated UUID)
across all multi-tenant tables. No data is modified — this is an audit step.

Phase 2 (manual/follow-up): Once real tenant UUIDs are determined by business
stakeholders, a follow-up migration should UPDATE these records to their
correct tenant and add NOT NULL constraints where appropriate.

Tables audited:
- lia_profile_analyses, lia_opinions, job_vacancies, candidates
- vacancy_candidates, candidate_favorites, candidate_hidden
- external_candidate_profiles, interview_notes, audit_decision_log
- task_records, task_schedules, dead_letter_queue
- sso_audit_logs, consent_events, communication_log
"""

revision = '059'
down_revision = '058_tenant_llm_configs'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa

LEGACY_STRING_VALUES = ("default", "demo_company", "unknown")
NULL_UUID = "00000000-0000-0000-0000-000000000000"
DEPRECATED_UUID = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"

TABLES_WITH_COMPANY_ID = [
    "lia_profile_analyses",
    "lia_opinions",
    "job_vacancies",
    "candidates",
    "vacancy_candidates",
    "candidate_favorites",
    "candidate_hidden",
    "external_candidate_profiles",
    "interview_notes",
    "audit_decision_log",
    "sso_audit_logs",
    "consent_events",
    "communication_log",
]

TABLES_WITH_TENANT_ID = [
    "task_records",
    "task_schedules",
    "dead_letter_queue",
]


def upgrade():
    conn = op.get_bind()
    total_legacy = 0
    total_null = 0

    for table in TABLES_WITH_COMPANY_ID:
        has_table = conn.execute(sa.text(
            "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = :t)"
        ), {"t": table}).scalar()
        if not has_table:
            continue

        col_info = conn.execute(sa.text(
            "SELECT data_type FROM information_schema.columns "
            "WHERE table_name = :t AND column_name = 'company_id'"
        ), {"t": table}).fetchone()
        if not col_info:
            continue

        is_uuid = col_info[0] in ("uuid",)

        if is_uuid:
            count = conn.execute(sa.text(f"""
                SELECT COUNT(*) FROM {table}
                WHERE company_id IN (
                    '{NULL_UUID}'::uuid,
                    '{DEPRECATED_UUID}'::uuid
                )
            """)).scalar() or 0
            if count > 0:
                print(f"[059] AUDIT: {table}: {count} rows with legacy UUID company_id (need reassignment)")
                total_legacy += count
        else:
            placeholders = ", ".join(f"'{v}'" for v in LEGACY_STRING_VALUES)
            count = conn.execute(sa.text(f"""
                SELECT COUNT(*) FROM {table}
                WHERE company_id IN ({placeholders})
                   OR company_id = '{NULL_UUID}'
                   OR company_id = '{DEPRECATED_UUID}'
            """)).scalar() or 0
            if count > 0:
                print(f"[059] AUDIT: {table}: {count} rows with legacy string company_id (need reassignment)")
                total_legacy += count

        null_count = conn.execute(sa.text(f"""
            SELECT COUNT(*) FROM {table} WHERE company_id IS NULL
        """)).scalar() or 0
        if null_count > 0:
            print(f"[059] AUDIT: {table}: {null_count} rows with NULL company_id (need reassignment)")
            total_null += null_count

    for table in TABLES_WITH_TENANT_ID:
        has_table = conn.execute(sa.text(
            "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = :t)"
        ), {"t": table}).scalar()
        if not has_table:
            continue

        col_info = conn.execute(sa.text(
            "SELECT data_type FROM information_schema.columns "
            "WHERE table_name = :t AND column_name = 'tenant_id'"
        ), {"t": table}).fetchone()
        if not col_info:
            continue

        placeholders = ", ".join(f"'{v}'" for v in LEGACY_STRING_VALUES)
        count = conn.execute(sa.text(f"""
            SELECT COUNT(*) FROM {table}
            WHERE tenant_id IN ({placeholders})
               OR tenant_id = '{NULL_UUID}'
               OR tenant_id = '{DEPRECATED_UUID}'
        """)).scalar() or 0
        if count > 0:
            print(f"[059] AUDIT: {table}: {count} rows with legacy tenant_id (need reassignment)")
            total_legacy += count

        null_count = conn.execute(sa.text(f"""
            SELECT COUNT(*) FROM {table} WHERE tenant_id IS NULL
        """)).scalar() or 0
        if null_count > 0:
            print(f"[059] AUDIT: {table}: {null_count} rows with NULL tenant_id (need reassignment)")
            total_null += null_count

    print(f"[059] AUDIT SUMMARY: {total_legacy} legacy + {total_null} NULL = {total_legacy + total_null} total rows requiring tenant reassignment")
    if total_legacy + total_null == 0:
        print("[059] All company_id/tenant_id values are already valid tenant UUIDs. No action needed.")


def downgrade():
    pass
