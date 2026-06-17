"""RLS deny-by-default for multi-tenant isolation.

Revision ID: 068_rls_deny_by_default
Revises: 067
Create Date: 2026-04-12

Replaces the broken migration 040 (which never executed and had IS NULL OR bug).
This migration:
1. Creates app_current_company_id() returning TEXT (not UUID)
2. Creates lia_app role (non-superuser) for RLS enforcement
3. Applies DENY-BY-DEFAULT RLS to all VARCHAR company_id tables
4. Backfills NULL company_id to 'demo_company' in nullable tables

Compatible with future Rails integration — RLS is enforced at DB level,
any client that does SET app.company_id gets isolation automatically.
"""
from alembic import op

revision = "068_rls_deny_by_default"
down_revision = "067"
depends_on = None

RLS_TABLES_NOT_NULL = [
    "ab_test_results",
    "affirmative_audit_logs",
    "agent_execution_records",
    "agent_feedback",
    "agent_long_term_memory",
    "agent_quality_evaluations",
    "agent_quotas",
    "ai_suggestions",
    "alert_preferences",
    "ats_stage_mappings",
    "audit_logs",
    "automation_execution_logs",
    "behavioral_competencies_catalog",
    "candidate_affirmative_documents",
    "candidate_attachments",
    "candidate_experience_highlights",
    "candidate_favorites",
    "candidate_hidden",
    "candidate_lists",
    "candidate_opt_outs",
    "candidate_quarantines",
    "candidate_stage_history",
    "communication_automations",
    "communication_history",
    "communication_logs",
    "communication_settings",
    "company_benefits",
    "company_hiring_policies",
    "company_modules",
    "company_patterns",
    "company_responsibilities",
    "company_retention_policies",
    "company_screening_questions",
    "company_skills",
    "company_skills_catalog",
    "company_workos_config",
    "correction_patterns",
    "credit_accounts",
    "credit_transactions",
    "credits_usage",
    "custom_agents",
    "digital_twins",
    "email_tracking_events",
    "external_candidate_profiles",
    "intelligence_insights",
    "job_drafts",
    "job_outcomes",
    "job_vacancies",
    "job_vacancy_audit_logs",
    "learning_analytics",
    "lgpd_consents",
    "lia_opinions",
    "lia_profile_analyses",
    "message_queue",
    "outcome_correlations",
    "pattern_cache",
    "pending_approvals",
    "personalization_events",
    "personalized_feedback_records",
    "pipeline_templates",
    "recruiter_profiles",
    "recruitment_campaigns",
    "recruitment_stages",
    "recruitment_sub_statuses",
    "screening_questions",
    "screening_tasks",
    "skill_suggestion_patterns",
    "skill_usage_analytics",
    "sourcing_agents",
    "sso_audit_logs",
    "stage_automation_rules",
    "stage_feedback",
    "success_profiles",
    "suggestion_feedback",
    "talent_pools",
    "tenant_llm_configs",
    "triagem_sessions",
    "user_agent_preferences",
    "users",
    "vacancy_candidates",
    "webhook_delivery_logs",
    "webhook_logs",
    "webhook_registrations",
    "webhooks",
    "whatsapp_conversations",
    "wizard_feedback",
    "workos_group_role_mappings",
]

RLS_TABLES_NULLABLE = [
    "agent_checkpoints",
    "agent_templates",
    "agent_working_memory",
    "alert_configs",
    "ats_connections",
    "communication_matrix_entries",
    "email_templates",
    "execution_plans",
    "feature_flags",
    "global_policies",
    "global_search_settings",
    "guardrails",
    "hitl_audit_trail",
    "hitl_pending_actions",
    "interviews",
    "pending_actions",
    "planned_tasks",
    "recruitment_email_templates",
    "search_archetypes",
    "teams_action_audit_logs",
]

ALL_RLS_TABLES = RLS_TABLES_NOT_NULL + RLS_TABLES_NULLABLE


def upgrade() -> None:
    op.execute("""
        CREATE OR REPLACE FUNCTION app_current_company_id() RETURNS TEXT AS $$
        BEGIN
            RETURN NULLIF(current_setting('app.company_id', true), '');
        END;
        $$ LANGUAGE plpgsql STABLE;
    """)

    op.execute("""
        COMMENT ON FUNCTION app_current_company_id() IS
        'Returns company_id from session config. Set by FastAPI/Rails middleware via SET app.company_id. Returns NULL if not set.';
    """)

    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'lia_app') THEN
                CREATE ROLE lia_app NOLOGIN NOSUPERUSER;
            END IF;
        END $$;
    """)

    op.execute("GRANT USAGE ON SCHEMA public TO lia_app;")
    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO lia_app;")
    op.execute("GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO lia_app;")
    op.execute("GRANT EXECUTE ON FUNCTION app_current_company_id() TO lia_app;")

    op.execute("ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO lia_app;")
    op.execute("ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO lia_app;")

    op.execute("""
        DO $$
        DECLARE
            app_user TEXT := current_user;
        BEGIN
            EXECUTE format('GRANT lia_app TO %I', app_user);
        END $$;
    """)

    for table in RLS_TABLES_NULLABLE:
        op.execute(f"UPDATE {table} SET company_id = 'demo_company' WHERE company_id IS NULL;")

    for table in ALL_RLS_TABLES:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY;")

        op.execute(f"""
            CREATE POLICY {table}_tenant_select ON {table}
                FOR SELECT
                USING (company_id = app_current_company_id());
        """)

        op.execute(f"""
            CREATE POLICY {table}_tenant_insert ON {table}
                FOR INSERT
                WITH CHECK (company_id = app_current_company_id());
        """)

        op.execute(f"""
            CREATE POLICY {table}_tenant_update ON {table}
                FOR UPDATE
                USING (company_id = app_current_company_id());
        """)

        op.execute(f"""
            CREATE POLICY {table}_tenant_delete ON {table}
                FOR DELETE
                USING (company_id = app_current_company_id());
        """)


def downgrade() -> None:
    for table in reversed(ALL_RLS_TABLES):
        op.execute(f"DROP POLICY IF EXISTS {table}_tenant_select ON {table};")
        op.execute(f"DROP POLICY IF EXISTS {table}_tenant_insert ON {table};")
        op.execute(f"DROP POLICY IF EXISTS {table}_tenant_update ON {table};")
        op.execute(f"DROP POLICY IF EXISTS {table}_tenant_delete ON {table};")
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY;")

    op.execute("DROP FUNCTION IF EXISTS app_current_company_id();")

    op.execute("ALTER DEFAULT PRIVILEGES IN SCHEMA public REVOKE SELECT, INSERT, UPDATE, DELETE ON TABLES FROM lia_app;")
    op.execute("ALTER DEFAULT PRIVILEGES IN SCHEMA public REVOKE USAGE, SELECT ON SEQUENCES FROM lia_app;")
    op.execute("REVOKE ALL ON ALL TABLES IN SCHEMA public FROM lia_app;")
    op.execute("REVOKE ALL ON ALL SEQUENCES IN SCHEMA public FROM lia_app;")
    op.execute("REVOKE USAGE ON SCHEMA public FROM lia_app;")

    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (SELECT FROM pg_roles WHERE rolname = 'lia_app') THEN
                DROP ROLE lia_app;
            END IF;
        END $$;
    """)
