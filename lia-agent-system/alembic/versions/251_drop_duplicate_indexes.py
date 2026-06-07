"""drop duplicate indexes (redundant twins on identical columns)

Remove 105 índices redundantes que duplicavam exatamente as mesmas colunas de
um índice/constraint já existente. Cada par surgiu de declarar o índice duas
vezes (coluna ``index=True`` gera ``ix_<tbl>_<col>`` + ``Index('idx_...')``
explícito e/ou ``CREATE INDEX IF NOT EXISTS`` no boot). A duplicidade travava o
provisionamento do deploy (``CREATE UNIQUE INDEX ... already exists``).

Regra aplicada por par:
- pares ÚNICOS  -> mantém o índice único / a unique constraint, dropa o gêmeo;
- pares comuns  -> mantém o índice recriado no boot (``ensure_*``), dropa o outro.

Nenhum nome abaixo é uma constraint (todos são índices puros), portanto
``DROP INDEX IF EXISTS`` é seguro e idempotente. A unicidade de cada coluna
permanece garantida pelo índice/constraint mantido.

Revision ID: 251_drop_duplicate_indexes
Revises: 250
Create Date: 2026-06-07
"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "251_drop_duplicate_indexes"
down_revision = "250"
branch_labels = None
depends_on = None


# Índices redundantes a remover (gêmeos de um índice/constraint mantido).
DUPLICATE_INDEXES = [
    "idx_agent_quota_company",
    "idx_api_usage_tenant_date",
    "idx_chp_company_id",
    "idx_client_cnpj",
    "idx_company_workos_config_company",
    "idx_job_outcomes_job",
    "idx_job_vacancy_version",
    "idx_list_members_list_candidate",
    "idx_manager_prefs_company_email",
    "idx_pending_actions_conversation",
    "idx_sqs_job_version",
    "idx_template_popularity",
    "idx_users_workos_id",
    "idx_workos_groups_workos_id",
    "ix_agent_installations_installer_company_id",
    "ix_agent_marketplace_listings_publisher_company_id",
    "ix_ats_stage_mappings_wedotalent_stage_id",
    "ix_audit_execution_metadata_company_timestamp",
    "ix_audit_logs_agent_name",
    "ix_audit_logs_candidate_id",
    "ix_audit_logs_company_id",
    "ix_audit_logs_created_at",
    "ix_audit_logs_decision_type",
    "ix_audit_logs_job_vacancy_id",
    "ix_cache_entries_expires_at",
    "ix_candidate_list_members_candidate_id",
    "ix_candidate_list_members_list_id",
    "ix_candidate_lists_company_id",
    "ix_client_accounts_is_deleted",
    "ix_client_accounts_plan_id",
    "ix_client_accounts_status",
    "ix_client_health_metrics_client_id",
    "ix_client_saas_metrics_client_id",
    "ix_client_test_configs_client_id",
    "ix_client_test_configs_test_id",
    "ix_client_usage_metrics_client_id",
    "ix_client_users_company_id",
    "ix_client_users_is_deleted",
    "ix_client_users_status",
    "ix_company_training_consents_company_id",
    "ix_company_workos_config_workos_directory_id",
    "ix_credit_accounts_company",
    "ix_email_templates_origin_template_id",
    "ix_hiring_nps_token",
    "ix_imported_job_descriptions_import_batch_id",
    "ix_interaction_feedback_company_id",
    "ix_interaction_feedback_created_at",
    "ix_interaction_feedback_session_id",
    "ix_interaction_feedback_user_id",
    "ix_job_outcomes_company_id",
    "ix_job_outcomes_created_at",
    "ix_job_outcomes_job_id",
    "ix_job_outcomes_outcome",
    "ix_job_outcomes_role",
    "ix_job_outcomes_seniority",
    "ix_job_templates_category",
    "ix_job_templates_company_id",
    "ix_job_templates_created_at",
    "ix_job_templates_is_active",
    "ix_job_templates_is_system",
    "ix_job_templates_seniority",
    "ix_job_templates_subcategory",
    "ix_job_templates_title_normalized",
    "ix_job_vacancy_audit_logs_changed_at",
    "ix_learning_patterns_company_id",
    "ix_learning_patterns_created_at",
    "ix_learning_patterns_pattern_key",
    "ix_learning_patterns_pattern_type",
    "ix_lia_profile_analyses_analysis_type",
    "ix_lia_profile_analyses_candidate_id",
    "ix_lia_profile_analyses_company_id",
    "ix_lia_profile_analyses_is_active",
    "ix_manager_alignments_token",
    "ix_payment_history_client_id",
    "ix_payment_history_date",
    "ix_payment_history_status",
    "ix_recruitment_automations_company_id",
    "ix_recruitment_email_templates_is_active",
    "ix_recruitment_email_templates_is_default",
    "ix_recruitment_slas_company_id",
    "ix_recruitment_templates_company_id",
    "ix_screening_question_sets_job_vacancy_id",
    "ix_skill_suggestion_patterns_company_id",
    "ix_skill_usage_analytics_company_id",
    "ix_skill_usage_analytics_job_vacancy_id",
    "ix_sla_violations_company_id",
    "ix_sla_violations_job_id",
    "ix_sla_violations_sla_id",
    "ix_technical_tests_category",
    "ix_technical_tests_difficulty",
    "ix_technical_tests_is_active",
    "ix_technical_tests_is_global",
    "ix_technical_tests_subcategory",
    "ix_template_usage_logs_created_at",
    "ix_test_results_candidate_id",
    "ix_test_results_client_id",
    "ix_test_results_created_at",
    "ix_test_results_test_id",
    "ix_token_usage_logs_created_at",
    "ix_wizard_feedback_company_id",
    "ix_wizard_feedback_created_at",
    "ix_wizard_feedback_field_corrected",
    "ix_wizard_feedback_job_id",
    "ix_wizard_feedback_role",
    "ix_wizard_feedback_seniority",
]


def upgrade() -> None:
    for name in DUPLICATE_INDEXES:
        op.execute(f'DROP INDEX IF EXISTS "{name}"')


def downgrade() -> None:
    # No-op intencional: os índices removidos eram duplicatas redundantes de um
    # índice/constraint que permanece. Recriá-los reintroduziria exatamente o
    # conflito de provisionamento que esta migração corrige.
    pass
