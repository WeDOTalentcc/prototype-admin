# Database Schema Ativo — Plataforma LIA (PostgreSQL)

> Contém apenas as tabelas efetivamente utilizadas no sistema.
> **Tabelas ativas: 271** de 301 definidas
> **Tabelas excluídas: 30** (sem uso em routers/services/lógica de negócio)

### Tabelas excluídas desta documentação

| Tabela | Classe | Status | Refs |
|--------|--------|--------|------|
| `agent_activities` | `AgentActivity` | Ref. mínima | 2 |
| `agent_long_term_memory` | `AgentLongTermMemory` | Sem uso | 0 |
| `agent_metrics_snapshots` | `AgentMetricsSnapshot` | Ref. mínima | 1 |
| `business_processes` | `BusinessProcess` | Ref. mínima | 2 |
| `candidate_merge_audit` | `CandidateMergeAudit` | Sem uso | 0 |
| `continuity_tests` | `ContinuityTest` | Ref. mínima | 2 |
| `dead_letter_queue` | `DeadLetterRecord` | Ref. mínima | 2 |
| `disaster_recovery_plans` | `DisasterRecoveryPlan` | Ref. mínima | 2 |
| `feedback_events` | `FeedbackEvent` | Ref. mínima | 2 |
| `insurance_claims` | `InsuranceClaim` | Ref. mínima | 2 |
| `insurance_coverages` | `InsuranceCoverage` | Ref. mínima | 2 |
| `insurance_documents` | `InsuranceDocument` | Ref. mínima | 2 |
| `insurance_policies` | `InsurancePolicy` | Ref. mínima | 2 |
| `integration_webhooks` | `IntegrationWebhook` | Ref. mínima | 2 |
| `job_vacancy_interview_stages` | `JobVacancyInterviewStage` | Ref. mínima | 2 |
| `job_vacancy_templates` | `JobVacancyTemplate` | Ref. mínima | 2 |
| `learning_analytics` | `LearningAnalytics` | Sem uso | 0 |
| `platform_policy_audit_logs` | `PlatformPolicyAuditLog` | Ref. mínima | 1 |
| `query_embeddings` | `QueryEmbedding` | Ref. mínima | 1 |
| `recruiter_decision_feedback` | `RecruiterDecisionFeedback` | Ref. mínima | 1 |
| `risk_entries` | `RiskEntry` | Ref. mínima | 2 |
| `risk_treatments` | `RiskTreatment` | Ref. mínima | 2 |
| `sod_conflicts` | `SoDConflict` | Ref. mínima | 2 |
| `sod_roles` | `SoDRole` | Ref. mínima | 2 |
| `sod_violations` | `SoDViolation` | Ref. mínima | 2 |
| `task_records` | `TaskRecord` | Ref. mínima | 2 |
| `task_schedules` | `TaskSchedule` | Ref. mínima | 2 |
| `teams_notifications` | `TeamsNotification` | Ref. mínima | 2 |
| `template_categories` | `TemplateCategory` | Ref. mínima | 2 |
| `token_usage_logs` | `TokenUsageLog` | Ref. mínima | 1 |

---

## Índice

- **ab_testing** — `ab_test_results`, `prompt_variants`
- **activity_feed** — `activity_feed`
- **admin_settings** — `admin_audit_logs`, `admin_roles`, `admin_user_roles`, `notification_policies`, `security_settings`
- **affirmative_audit** — `affirmative_audit_logs`, `candidate_affirmative_documents`
- **agent_approval** — `agent_approval_requests`
- **agent_checkpoint** — `agent_checkpoints`
- **agent_deployment** — `agent_deployments`
- **agent_execution_log** — `agent_execution_logs`
- **agent_quality_evaluation** — `agent_quality_evaluations`
- **agent_quota** — `agent_quotas`
- **agent_template** — `agent_templates`
- **agent_version_snapshot** — `agent_version_snapshots`
- **ai_consumption** — `ai_consumption`, `ai_credits_balance`
- **alert** — `alert_configs`, `alert_preferences`, `alert_rules`, `alerts`
- **approval** — `approval_requests`
- **archetype** — `search_archetypes`
- **ats_integration** — `ats_candidates`, `ats_connections`, `ats_job_mappings`, `ats_sync_jobs`, `ats_webhook_logs`
- **audit_log** — `audit_logs`
- **audit_logs** — `audit_retention_policies`, `sox_audit_logs`
- **automation** — `ai_suggestions`, `automation_execution_logs`, `communication_automations`, `stage_automation_rules`
- **background_jobs** — `background_jobs`, `proactive_actions`
- **bias_audit_snapshot** — `bias_audit_snapshots`
- **billing** — `company_modules`, `credit_accounts`, `credit_transactions`, `invoices`, `payment_methods`, `subscriptions`
- **calibration** — `calibration_events`, `calibration_feedback`, `calibration_sessions`, `calibration_suggestions`, `calibration_weights`
- **candidate** — `candidate_education`, `candidate_experiences`, `candidate_favorites`, `candidate_hidden`, `candidate_searches`, `candidate_sources`, `candidates`, `credits_usage`, `external_candidate_profiles`, `vacancy_candidates`, `viewed_candidates`
- **candidate_attachment** — `candidate_attachments`
- **candidate_feedback** — `candidate_feedbacks`
- **candidate_job** — `candidate_jobs`
- **candidate_list** — `candidate_list_members`, `candidate_lists`
- **client_account** — `client_accounts`
- **client_user** — `client_users`
- **communication_history** — `communication_history`
- **communication_matrix** — `communication_matrix_entries`
- **communication_settings** — `communication_settings`, `lgpd_consents`
- **company** — `approvers`, `benefit_templates`, `benefits`, `big_five_questions`, `big_five_role_profiles`, `company_profiles`, `culture_values`, `department_members`, `departments`, `global_search_settings`, `ideal_profiles`, `technical_questions`, `technical_test_templates`
- **company_benefit** — `company_benefits`
- **company_calendar_credentials** — `company_calendar_credentials`
- **company_culture** — `company_culture_profiles`, `culture_analysis_jobs`
- **company_hiring_policy** — `company_hiring_policies`
- **company_learning** — `agent_feedback`, `company_patterns`, `company_responsibilities`, `company_skills`, `feature_flags`, `stage_feedback`
- **compensation_policy** — `compensation_policies`
- **conversation** — `conversation_summaries`, `conversations`, `messages`
- **custom_agent** — `agent_installations`, `agent_marketplace_listings`, `custom_agents`
- **data_request** — `data_request_configs`, `data_request_fields`, `data_request_responses`, `data_request_templates`, `data_requests`, `vacancy_data_request_configs`
- **default_templates** — `default_templates`
- **digital_twin** — `digital_twins`, `twin_decisions`
- **email_template** — `email_logs`, `email_templates`
- **email_tracking** — `email_tracking_events`
- **evaluation_criteria** — `evaluation_criteria`
- **event_store** — `domain_events`
- **execution_log_store** — `agent_execution_records`
- **external_api_consumption** — `external_api_consumption`
- **fairness_audit** — `fairness_audit_log`
- **feedback** — `interaction_feedback`, `learning_patterns`
- **feedback_learning** — `job_outcomes`, `suggestion_feedback`, `wizard_feedback`
- **global_policies** — `platform_global_policies`
- **global_policy** — `global_policies`
- **goal** — `goal_templates`, `goals`
- **graph_session** — `graph_sessions`
- **guardrail** — `guardrails`
- **health_check** — `compliance_health_check_history`, `compliance_health_check_items`
- **hitl** — `hitl_audit_trail`, `hitl_pending_actions`
- **imported_job_description** — `client_skill_catalogs`, `import_batches`, `imported_job_descriptions`
- **integration_hub** — `integration_connections`, `integration_providers`, `integration_sync_logs`
- **intelligence_layer** — `correction_patterns`, `intelligence_insights`, `outcome_correlations`, `pattern_cache`, `success_profiles`
- **intelligent_cache** — `cache_entries`
- **interview** — `calendar_availability`, `interview_feedbacks`, `interview_notes`, `interviews`
- **job_draft** — `draft_field_history`, `job_drafts`
- **job_pattern** — `job_embeddings`, `job_patterns`, `salary_benchmarks`, `skill_clusters`
- **job_template** — `job_templates`, `template_usage_logs`
- **job_vacancy** — `job_vacancies`
- **job_vacancy_audit** — `job_vacancy_audit_logs`
- **journey_mapping** — `journey_blueprints`, `journey_integrations`, `journey_steps`
- **lia_field_toggles** — `lia_field_toggles`
- **lia_opinion** — `lia_opinions`
- **lia_profile_analysis** — `lia_profile_analyses`
- **memory** — `conversation_memories`, `knowledge_base`
- **message_queue** — `message_queue`
- **ml_model_registry** — `ml_model_registry`
- **notification_service** — `chat_notifications`, `notifications`
- **observability** — `ai_inference_logs`, `automated_decision_explanations`, `bias_audit_reports`, `breach_notifications`, `company_compliance_controls`, `compliance_audits`, `compliance_control_library`, `compliance_controls`, `consent_events`, `consent_records`, `consent_versions`, `data_access_logs`, `data_subject_requests`, `dpo_registry`, `incident_reports`, `model_evaluations`, `sox_controls`
- **pipeline_template** — `pipeline_templates`
- **planned_task** — `execution_plans`, `planned_tasks`
- **policy** — `business_rules`, `escalation_logs`, `escalation_rules`, `policy_evaluation_logs`, `rate_limit_counters`, `rate_limit_rules`
- **recruiter_profile** — `personalization_settings`, `profile_calculation_logs`, `recruiter_field_preferences`, `recruiter_profiles`
- **recruitment_campaign** — `recruitment_campaigns`
- **recruitment_email_template** — `recruitment_email_templates`
- **recruitment_journey** — `recruitment_automations`, `recruitment_slas`, `recruitment_templates`, `sla_violations`
- **recruitment_stages** — `ats_stage_mappings`, `candidate_stage_history`, `recruitment_stages`, `recruitment_sub_statuses`, `screening_questions`
- **retention_policy** — `company_retention_policies`
- **routing_feedback** — `routing_feedback`
- **rubric** — `job_requirements`, `rubric_evaluations`
- **saas_metrics** — `client_health_metrics`, `client_saas_metrics`, `client_usage_metrics`, `payment_history`
- **screening** — `screening_tasks`
- **screening_question** — `company_screening_questions`
- **screening_question_set** — `screening_question_sets`
- **search_feedback** — `search_feedbacks`
- **self_scheduling** — `interview_reminders`, `reschedule_history`, `self_scheduling_links`
- **shared_search** — `shared_search_access`, `shared_search_feedback`, `shared_searches`
- **skills_catalog** — `behavioral_competencies_catalog`, `company_skills_catalog`, `skill_suggestion_patterns`, `skill_usage_analytics`
- **sourcing_agent** — `sourcing_agent_signals`, `sourcing_agents`
- **talent_pool** — `talent_pool_candidates`, `talent_pools`
- **task** — `task_templates`, `tasks`
- **teams** — `teams_action_audit_logs`, `teams_conversations`, `teams_messages`
- **technical_tests** — `client_test_configs`, `technical_tests`, `test_results`
- **tenant_llm_config** — `tenant_llm_configs`
- **triagem** — `triagem_messages`, `triagem_sessions`
- **trust_center** — `trust_center_resources`, `trust_center_settings`, `trust_center_subprocessors`, `trust_center_updates`
- **user_agent_preference** — `user_agent_preferences`
- **voice_screening** — `voice_screening_analyses`, `voice_screening_calls`
- **webhook** — `studio_webhooks`, `webhook_logs`
- **webhook_registration** — `webhook_delivery_logs`, `webhook_registrations`
- **whatsapp_conversation** — `whatsapp_conversations`, `whatsapp_messages`
- **workforce** — `hiring_plans`, `import_jobs`, `planned_headcounts`, `workforce_entries`
- **working_memory** — `agent_working_memory`

---

## ab_testing
**Arquivo:** `lia-agent-system/libs/models/lia_models/ab_testing.py`

### `ab_test_results`
**Classe:** `ABTestResult` | **Herda:** `Base` | **Uso:** Routers/Services: 0 | Total refs: 3

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `test_name` | String(255) | NOT NULL, INDEX |
| `variant_name` | String(100) | NOT NULL |
| `session_id` | String(255) | NOT NULL |
| `company_id` | String(255) | NOT NULL, INDEX |
| `metric_name` | String(100) | NOT NULL |
| `metric_value` | Float | NOT NULL |
| `context` | JSON | — |
| `created_at` | DateTime | INDEX, default=datetime.utcnow |

### `prompt_variants`
**Classe:** `PromptVariant` | **Herda:** `Base` | **Uso:** Routers/Services: 0 | Total refs: 8

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `test_name` | String(255) | NOT NULL, INDEX |
| `variant_name` | String(100) | NOT NULL |
| `prompt_template` | Text | NOT NULL |
| `is_active` | Boolean | default=True |
| `traffic_percentage` | Float | default=50.0 |
| `created_at` | DateTime | default=datetime.utcnow |
| `updated_at` | DateTime | default=datetime.utcnow |

---

## activity_feed
**Arquivo:** `lia-agent-system/libs/models/lia_models/activity_feed.py`

### `activity_feed`
**Classe:** `ActivityFeed` | **Herda:** `Base` | **Uso:** Routers/Services: 4 | Total refs: 6

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | String(255) | PK, default=lambda: str(uuid.uuid4( |
| `activity_type` | String(50) | NOT NULL, INDEX |
| `extra_data` | JSON | default={} |
| `is_visible` | Boolean | INDEX, default=True |
| `created_at` | DateTime | INDEX, default=datetime.utcnow |
| `actor_id` | String(255) | INDEX |
| `target_id` | String(255) | NOT NULL, INDEX |
| `priority` | String(20) | INDEX, default="normal" |
| `action_url` | String(500) | INDEX, default=True |
| `visible_to` | DateTime | INDEX, default=[] |
| `created_by` | String(255) | — |

---

## admin_settings
**Arquivo:** `lia-agent-system/libs/models/lia_models/admin_settings.py`

### `admin_audit_logs`
**Classe:** `AdminAuditLog` | **Herda:** `Base` | **Uso:** Routers/Services: 1 | Total refs: 3

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `company_id` | UUID | NOT NULL |
| `user_id` | UUID | — |
| `user_email` | String(255) | — |
| `action` | String(100) | NOT NULL |
| `resource_type` | String(100) | — |
| `resource_id` | String(255) | — |
| `old_value` | JSON | default={} |
| `new_value` | JSON | default={} |
| `ip_address` | String(50) | — |
| `user_agent` | Text | — |
| `created_at` | DateTime | default=datetime.utcnow |

### `admin_roles`
**Classe:** `AdminRole` | **Herda:** `Base` | **Uso:** Routers/Services: 1 | Total refs: 3

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `company_id` | UUID | NOT NULL, FK → company_profiles.id |
| `name` | String(255) | NOT NULL |
| `description` | Text | — |
| `permissions` | JSON | default={} |
| `is_system_role` | Boolean | default=False |
| `is_active` | Boolean | default=True |
| `created_at` | DateTime | default=datetime.utcnow |
| `updated_at` | DateTime | default=datetime.utcnow |

### `admin_user_roles`
**Classe:** `AdminUserRole` | **Herda:** `Base` | **Uso:** Routers/Services: 1 | Total refs: 3

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `user_id` | UUID | NOT NULL |
| `role_id` | UUID | NOT NULL, FK → admin_roles.id |
| `company_id` | UUID | NOT NULL, FK → company_profiles.id |
| `assigned_at` | DateTime | default=datetime.utcnow |
| `assigned_by` | String(255) | — |

### `notification_policies`
**Classe:** `NotificationPolicy` | **Herda:** `Base` | **Uso:** Routers/Services: 1 | Total refs: 3

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `company_id` | UUID | NOT NULL, FK → company_profiles.id |
| `name` | String(255) | NOT NULL |
| `event_type` | String(100) | NOT NULL |
| `channels` | String | default=[] |
| `recipient_type` | String(50) | — |
| `recipients` | String | default=[] |
| `subject_template` | String(500) | — |
| `body_template` | Text | — |
| `is_enabled` | Boolean | default=True |
| `created_at` | DateTime | default=datetime.utcnow |
| `updated_at` | DateTime | default=datetime.utcnow |

### `security_settings`
**Classe:** `SecuritySetting` | **Herda:** `Base` | **Uso:** Routers/Services: 1 | Total refs: 3

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `company_id` | UUID | NOT NULL, UNIQUE, FK → company_profiles.id |
| `require_2fa` | Boolean | default=False |
| `session_timeout_minutes` | Integer | default=480 |
| `max_login_attempts` | Integer | default=5 |
| `password_min_length` | Integer | default=8 |
| `password_require_uppercase` | Boolean | default=True |
| `password_require_numbers` | Boolean | default=True |
| `password_require_special` | Boolean | default=False |
| `password_expiry_days` | Integer | default=90 |
| `ip_whitelist` | String | default=[] |
| `ip_blacklist` | String | default=[] |
| `audit_logging_enabled` | Boolean | default=True |
| `audit_retention_days` | Integer | default=365 |
| `data_export_allowed` | Boolean | default=True |
| `data_retention_days` | Integer | default=730 |
| `created_at` | DateTime | default=datetime.utcnow |
| `updated_at` | DateTime | default=datetime.utcnow |

---

## affirmative_audit
**Arquivo:** `lia-agent-system/libs/models/lia_models/affirmative_audit.py`

### `affirmative_audit_logs`
**Classe:** `AffirmativeAuditLog` | **Herda:** `Base` | **Uso:** Routers/Services: 1 | Total refs: 2

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `company_id` | String(255) | NOT NULL, INDEX |
| `vacancy_id` | UUID | INDEX, FK → job_vacancies.id |
| `candidate_id` | UUID | INDEX, FK → candidates.id |
| `action` | String(100) | NOT NULL, INDEX |
| `criteria_checked` | JSON | default={} |
| `result` | Boolean | — |
| `reason` | Text | — |
| `performed_by` | String(255) | — |
| `performed_by_type` | String(50) | default="system" |
| `action_metadata` | JSON | default={} |
| `created_at` | DateTime | INDEX, default=datetime.utcnow |

### `candidate_affirmative_documents`
**Classe:** `CandidateAffirmativeDocument` | **Herda:** `Base` | **Uso:** Routers/Services: 1 | Total refs: 2

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `candidate_id` | UUID | NOT NULL, INDEX, FK → candidates.id |
| `vacancy_id` | UUID | INDEX, FK → job_vacancies.id |
| `company_id` | String(255) | NOT NULL, INDEX |
| `document_type` | String(100) | NOT NULL |
| `document_url` | String(500) | NOT NULL |
| `original_filename` | String(255) | — |
| `criteria_type` | String(50) | NOT NULL |
| `status` | String(50) | INDEX, default="pending" |
| `verified_by_lia` | Boolean | default=False |
| `lia_verification_result` | JSON | — |
| `lia_verified_at` | DateTime | — |
| `verified_by_recruiter` | Boolean | default=False |
| `recruiter_email` | String(255) | — |
| `recruiter_verified_at` | DateTime | — |
| `recruiter_notes` | Text | — |
| `upload_deadline` | DateTime | — |
| `is_expired` | Boolean | default=False |
| `reminder_sent_at` | DateTime | — |
| `uploaded_at` | DateTime | default=datetime.utcnow |
| `created_at` | DateTime | INDEX, default=datetime.utcnow |
| `updated_at` | DateTime | default=datetime.utcnow |

---

## agent_approval
**Arquivo:** `lia-agent-system/libs/models/lia_models/agent_approval.py`

### `agent_approval_requests`
**Classe:** `AgentApprovalRequest` | **Herda:** `Base` | **Uso:** Routers/Services: 1 | Total refs: 2

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `agent_id` | UUID | NOT NULL, INDEX |
| `company_id` | String(64) | NOT NULL, INDEX |
| `requested_by` | String(128) | NOT NULL |
| `reviewed_by` | String(128) | — |
| `status` | String(32) | NOT NULL, INDEX, default="pending" |
| `review_notes` | Text | — |
| `requested_at` | DateTime | default=func.now(, server_default |
| `reviewed_at` | DateTime | — |

---

## agent_checkpoint
**Arquivo:** `lia-agent-system/libs/models/lia_models/agent_checkpoint.py`

### `agent_checkpoints`
**Classe:** `AgentCheckpoint` | **Herda:** `Base` | **Uso:** Routers/Services: 1 | Total refs: 3

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `session_id` | String(255) | NOT NULL, INDEX |
| `agent_type` | String(100) | NOT NULL |
| `company_id` | String(255) | INDEX |
| `state_json` | JSON | NOT NULL, default={} |
| `created_at` | DateTime | default=datetime.utcnow |
| `updated_at` | DateTime | default=datetime.utcnow |

---

## agent_deployment
**Arquivo:** `lia-agent-system/libs/models/lia_models/agent_deployment.py`

### `agent_deployments`
**Classe:** `AgentDeployment` | **Herda:** `Base` | **Uso:** Routers/Services: 1 | Total refs: 3

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `agent_id` | UUID | NOT NULL, INDEX |
| `company_id` | String(64) | NOT NULL, INDEX |
| `target_type` | String(32) | NOT NULL |
| `target_id` | UUID | NOT NULL, INDEX |
| `target_name` | String(512) | — |
| `trigger_mode` | String(32) | NOT NULL, default="manual" |
| `schedule_cron` | String(128) | — |
| `is_active` | Boolean | NOT NULL, default=True |
| `config_overrides` | JSON | default={} |
| `execution_count` | Integer | NOT NULL, default=0 |
| `last_execution_at` | DateTime | — |
| `candidates_processed` | Integer | NOT NULL, default=0 |
| `created_by` | String(128) | NOT NULL |
| `created_at` | DateTime | default=func.now(, server_default |
| `updated_at` | DateTime | default=func.now(, server_default |

---

## agent_execution_log
**Arquivo:** `lia-agent-system/libs/models/lia_models/agent_execution_log.py`

### `agent_execution_logs`
**Classe:** `AgentExecutionLog` | **Herda:** `Base` | **Uso:** Routers/Services: 1 | Total refs: 3

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `agent_id` | UUID | NOT NULL, INDEX |
| `deployment_id` | UUID | INDEX |
| `company_id` | String(64) | NOT NULL, INDEX |
| `user_id` | String(128) | NOT NULL |
| `input_message` | Text | NOT NULL |
| `output_message` | Text | NOT NULL, default="" |
| `confidence` | Float | default=0.0 |
| `tokens_input` | Integer | default=0 |
| `tokens_output` | Integer | default=0 |
| `model_used` | String(128) | default="" |
| `latency_ms` | Integer | default=0 |
| `credits_consumed` | Integer | default=0 |
| `tool_calls` | String | default=[] |
| `compliance_status` | String(32) | default="pass" |
| `created_at` | DateTime | default=func.now(, server_default |

---

## agent_quality_evaluation
**Arquivo:** `lia-agent-system/libs/models/lia_models/agent_quality_evaluation.py`

### `agent_quality_evaluations`
**Classe:** `AgentQualityEvaluation` | **Herda:** `Base` | **Uso:** Routers/Services: 2 | Total refs: 3

| Campo | Tipo | Restrições |
|-------|------|------------|
| `agent_id` | String(100) | NOT NULL |
| `company_id` | String(36) | NOT NULL |
| `session_id` | String(100) | — |
| `overall_score` | Float | NOT NULL |
| `scores` | JSON | NOT NULL |
| `id` | UUID | PK, default=uuid.uuid4 |
| `evaluated_at` | DateTime | NOT NULL, default=datetime.utcnow |

---

## agent_quota
**Arquivo:** `lia-agent-system/libs/models/lia_models/agent_quota.py`

### `agent_quotas`
**Classe:** `AgentQuota` | **Herda:** `Base` | **Uso:** Routers/Services: 2 | Total refs: 3

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `company_id` | String(64) | NOT NULL, UNIQUE, INDEX |
| `plan_code` | String(50) | NOT NULL, default="starter" |
| `max_sourcing_agents` | Integer | NOT NULL, default=2 |
| `max_custom_agents` | Integer | NOT NULL, default=2 |
| `max_digital_twins` | Integer | NOT NULL, default=1 |
| `max_campaigns` | Integer | NOT NULL, default=2 |
| `active_sourcing_agents` | Integer | NOT NULL, default=0 |
| `active_custom_agents` | Integer | NOT NULL, default=0 |
| `active_digital_twins` | Integer | NOT NULL, default=0 |
| `active_campaigns` | Integer | NOT NULL, default=0 |
| `created_at` | DateTime | default=datetime.utcnow |
| `updated_at` | DateTime | default=datetime.utcnow |

---

## agent_template
**Arquivo:** `lia-agent-system/libs/models/lia_models/agent_template.py`

### `agent_templates`
**Classe:** `AgentTemplate` | **Herda:** `Base` | **Uso:** Routers/Services: 5 | Total refs: 8

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | String(255) | PK |
| `company_id` | String(255) | — |
| `name` | String(500) | NOT NULL |
| `domain` | String(100) | NOT NULL |
| `system_prompt_yaml` | Text | NOT NULL |
| `version` | Integer | NOT NULL, default=1 |
| `created_by` | String(255) | NOT NULL |
| `published_at` | DateTime | — |
| `archived_at` | DateTime | — |
| `status` | String(50) | NOT NULL, default=AgentTemplateStatus.DRAFT |
| `base_template_id` | String(255) | FK → agent_templates.id |
| `created_at` | DateTime | NOT NULL, default=func.now(, server_default |

---

## agent_version_snapshot
**Arquivo:** `lia-agent-system/libs/models/lia_models/agent_version_snapshot.py`

### `agent_version_snapshots`
**Classe:** `AgentVersionSnapshot` | **Herda:** `Base` | **Uso:** Routers/Services: 1 | Total refs: 2

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `agent_id` | UUID | NOT NULL, INDEX |
| `company_id` | String(64) | NOT NULL, INDEX |
| `version` | Integer | NOT NULL |
| `snapshot_data` | JSON | NOT NULL |
| `changed_fields` | String | default=[] |
| `change_reason` | Text | — |
| `changed_by` | String(128) | NOT NULL |
| `created_at` | DateTime | default=func.now(, server_default |

---

## ai_consumption
**Arquivo:** `lia-agent-system/libs/models/lia_models/ai_consumption.py`

### `ai_consumption`
**Classe:** `AiConsumption` | **Herda:** `Base` | **Uso:** Routers/Services: 8 | Total refs: 9

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `company_id` | UUID | NOT NULL, INDEX |
| `user_id` | UUID | INDEX |
| `agent_type` | String(50) | NOT NULL, INDEX |
| `agent_category` | String(20) | NOT NULL, INDEX, default="core" |
| `operation` | String(100) | NOT NULL |
| `model` | String(50) | NOT NULL, INDEX |
| `studio_agent_id` | String(64) | INDEX |
| `input_tokens` | Integer | default=0 |
| `output_tokens` | Integer | default=0 |
| `total_tokens` | Integer | default=0 |
| `cost_cents` | Integer | default=0 |
| `candidate_id` | UUID | INDEX |
| `vacancy_id` | UUID | INDEX |
| `extra_data` | JSON | default=dict |
| `created_at` | DateTime | INDEX, default=func.now(, server_default |
| `scheduled_deletion_at` | DateTime | INDEX |

### `ai_credits_balance`
**Classe:** `AiCreditsBalance` | **Herda:** `Base` | **Uso:** Routers/Services: 4 | Total refs: 5

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `company_id` | UUID | NOT NULL, UNIQUE, INDEX |
| `monthly_limit` | Integer | default=100000 |
| `current_usage` | Integer | default=0 |
| `period_start` | Date | NOT NULL |
| `period_end` | Date | NOT NULL |
| `overage_allowed` | Boolean | default=False |
| `overage_rate_cents` | Integer | default=0 |
| `updated_at` | DateTime | default=func.now(, server_default |
| `created_at` | DateTime | default=func.now(, server_default |
| `Manages` | UUID | PK, default=uuid.uuid4 |

---

## alert
**Arquivo:** `lia-agent-system/libs/models/lia_models/alert.py`

### `alert_configs`
**Classe:** `AlertConfig` | **Herda:** `Base` | **Uso:** Routers/Services: 3 | Total refs: 3

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | String | PK, default=lambda: str(uuid.uuid4( |
| `company_id` | String | — |
| `user_id` | String | — |
| `alerts` | JSON | default=list |
| `briefing_frequency` | String(20) | default="daily" |
| `is_active` | Boolean | default=True |
| `created_at` | DateTime | default=datetime.utcnow |
| `updated_at` | DateTime | default=datetime.utcnow |

### `alert_preferences`
**Classe:** `AlertPreference` | **Herda:** `Base` | **Uso:** Routers/Services: 2 | Total refs: 2

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | String | PK, default=lambda: str(uuid.uuid4( |
| `company_id` | String | NOT NULL, INDEX |
| `user_id` | String | NOT NULL, INDEX |
| `alert_type` | String(100) | NOT NULL |
| `is_enabled` | Boolean | default=True |
| `threshold` | Integer | — |
| `channel_email` | Boolean | default=True |
| `channel_bell` | Boolean | default=True |
| `channel_teams` | Boolean | default=False |
| `channel_whatsapp` | Boolean | default=False |
| `cooldown_hours` | Integer | default=24 |
| `created_at` | DateTime | default=datetime.utcnow |
| `updated_at` | DateTime | default=datetime.utcnow |

### `alert_rules`
**Classe:** `AlertRule` | **Herda:** `Base` | **Uso:** Routers/Services: 1 | Total refs: 3

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | String | PK, default=lambda: str(uuid.uuid4( |
| `name` | String(255) | NOT NULL |
| `description` | Text | — |
| `alert_type` | Enum(AlertType) | NOT NULL |
| `severity` | Enum(AlertSeverity) | default=AlertSeverity.MEDIUM |
| `condition` | JSON | NOT NULL |
| `is_active` | Boolean | default=True |
| `check_interval_hours` | Integer | default=4 |
| `last_checked_at` | DateTime | — |
| `notification_channels` | JSON | default=list |
| `title_template` | String(255) | NOT NULL |
| `message_template` | Text | NOT NULL |
| `created_at` | DateTime | default=datetime.utcnow |
| `updated_at` | DateTime | default=datetime.utcnow |

### `alerts`
**Classe:** `Alert` | **Herda:** `Base` | **Uso:** Routers/Services: 14 | Total refs: 19

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | String | PK, default=lambda: str(uuid.uuid4( |
| `alert_type` | Enum(AlertType) | NOT NULL |
| `severity` | Enum(AlertSeverity) | default=AlertSeverity.MEDIUM |
| `status` | Enum(AlertStatus) | default=AlertStatus.ACTIVE |
| `title` | String(255) | NOT NULL |
| `message` | Text | NOT NULL |
| `user_id` | String | — |
| `job_id` | String | — |
| `candidate_id` | String | — |
| `context` | JSON | default=dict |
| `suggested_actions` | JSON | default=list |
| `acknowledged_at` | DateTime | — |
| `acknowledged_by` | String | — |
| `resolved_at` | DateTime | — |
| `resolved_by` | String | — |
| `expires_at` | DateTime | — |
| `notification_sent` | Boolean | default=False |
| `notification_channels` | JSON | default=list |
| `created_at` | DateTime | default=datetime.utcnow |
| `updated_at` | DateTime | default=datetime.utcnow |

---

## approval
**Arquivo:** `lia-agent-system/libs/models/lia_models/approval.py`

### `approval_requests`
**Classe:** `ApprovalRequest` | **Herda:** `Base` | **Uso:** Routers/Services: 3 | Total refs: 5

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `company_id` | UUID | NOT NULL, INDEX |
| `request_type` | String(50) | NOT NULL, default="vacancy_approval" |
| `requester_id` | UUID | — |
| `requester_name` | String(255) | NOT NULL |
| `requester_email` | String(255) | NOT NULL |
| `target_id` | UUID | — |
| `target_type` | String(50) | — |
| `target_name` | String(500) | NOT NULL |
| `target_description` | Text | — |
| `target_data` | JSON | default={} |
| `approver_id` | UUID | — |
| `approver_name` | String(255) | NOT NULL |
| `approver_email` | String(255) | NOT NULL |
| `approval_level` | Integer | default=1 |
| `status` | String(20) | NOT NULL, INDEX, default="pending" |
| `priority` | String(20) | default="normal" |
| `due_date` | DateTime | — |
| `approval_notes` | Text | — |
| `rejection_reason` | Text | — |
| `email_sent` | Boolean | default=False |
| `email_sent_at` | DateTime | — |
| `reminder_count` | Integer | default=0 |
| `last_reminder_at` | DateTime | — |
| `resolved_at` | DateTime | — |
| `resolved_by` | String(255) | — |
| `resource_type` | String(50) | — |
| `resource_id` | String(255) | — |
| `expires_at` | DateTime | — |
| `created_at` | DateTime | default=datetime.utcnow |
| `updated_at` | DateTime | default=datetime.utcnow |

---

## archetype
**Arquivo:** `lia-agent-system/libs/models/lia_models/archetype.py`

### `search_archetypes`
**Classe:** `SearchArchetype` | **Herda:** `Base` | **Uso:** Routers/Services: 2 | Total refs: 4

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | String(50) | PK |
| `name` | String(100) | NOT NULL, INDEX |
| `description` | Text | — |
| `emoji` | String(10) | default="🎯" |
| `query` | Text | NOT NULL |
| `filters` | JSON | default=dict |
| `tags` | JSON | default=list |
| `industry` | String(100) | INDEX |
| `seniority` | String(50) | INDEX |
| `is_default` | Boolean | INDEX, default=False |
| `is_active` | Boolean | INDEX, default=True |
| `usage_count` | Integer | default=0 |
| `company_id` | String(100) | INDEX |
| `created_by` | String(255) | — |
| `created_at` | DateTime | default=datetime.utcnow, server_default |
| `updated_at` | DateTime | default=datetime.utcnow |

---

## ats_integration
**Arquivo:** `lia-agent-system/libs/models/lia_models/ats_integration.py`

### `ats_candidates`
**Classe:** `ATSCandidate` | **Herda:** `Base` | **Uso:** Routers/Services: 8 | Total refs: 10

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `connection_id` | UUID | NOT NULL, INDEX |
| `provider` | Enum(ATSProvider) | NOT NULL, INDEX |
| `name` | String(255) | NOT NULL |
| `email` | String(255) | INDEX |
| `phone` | String(50) | — |
| `linkedin_url` | String(500) | — |
| `current_title` | String(255) | — |
| `current_company` | String(255) | — |
| `location` | String(255) | — |
| `applied_job_title` | String(255) | — |
| `application_date` | DateTime | — |
| `first_synced_at` | DateTime | INDEX, default=datetime.utcnow |
| `last_synced_at` | DateTime | default=datetime.utcnow |
| `is_active` | Boolean | default=True |
| `created_at` | DateTime | default=datetime.utcnow |
| `updated_at` | DateTime | default=datetime.utcnow |
| `ats_candidate_id` | UUID | NOT NULL, INDEX |
| `applied_job_id` | String(255) | — |
| `application_status` | String(100) | INDEX, default=[] |
| `sync_version` | Integer | default=1 |

### `ats_connections`
**Classe:** `ATSConnection` | **Herda:** `Base` | **Uso:** Routers/Services: 2 | Total refs: 4

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `provider` | Enum(ATSProvider) | NOT NULL, INDEX |
| `ats_company_name` | String(255) | — |
| `is_active` | Boolean | INDEX, default=True |
| `auto_sync_enabled` | Boolean | default=True |
| `sync_candidates` | Boolean | default=True |
| `sync_jobs` | Boolean | default=True |
| `sync_applications` | Boolean | default=True |
| `last_sync_at` | DateTime | — |
| `last_sync_status` | Enum(SyncStatus) | — |
| `last_sync_error` | Text | — |
| `total_syncs` | Integer | default=0 |
| `total_sync_errors` | Integer | default=0 |
| `total_candidates_synced` | Integer | default=0 |
| `total_jobs_synced` | Integer | default=0 |
| `total_applications_synced` | Integer | default=0 |
| `created_by` | String(255) | NOT NULL, default="admin" |
| `created_at` | DateTime | INDEX, default=datetime.utcnow |
| `updated_at` | DateTime | default=datetime.utcnow |
| `provider_name` | String(100) | NOT NULL |
| `sync_frequency_hours` | Integer | default=24 |
| `field_mappings` | String(1000) | default=[] |

### `ats_job_mappings`
**Classe:** `ATSJobMapping` | **Herda:** `Base` | **Uso:** Routers/Services: 2 | Total refs: 4

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `connection_id` | UUID | NOT NULL, INDEX |
| `provider` | Enum(ATSProvider) | NOT NULL |
| `ats_job_id` | String(255) | NOT NULL, INDEX |
| `lia_job_vacancy_id` | UUID | INDEX |
| `job_title` | String(255) | NOT NULL |
| `department` | String(255) | — |
| `location` | String(255) | — |
| `is_active` | Boolean | default=True |
| `last_synced_at` | DateTime | default=datetime.utcnow |
| `ats_raw_data` | JSON | default={} |
| `created_at` | DateTime | default=datetime.utcnow |
| `updated_at` | DateTime | default=datetime.utcnow |
| `employment_type` | String(100) | default=True |

### `ats_sync_jobs`
**Classe:** `ATSSyncJob` | **Herda:** `Base` | **Uso:** Routers/Services: 2 | Total refs: 4

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `connection_id` | UUID | NOT NULL, INDEX |
| `provider` | Enum(ATSProvider) | NOT NULL, INDEX |
| `status` | Enum(SyncStatus) | INDEX, default=SyncStatus.PENDING |
| `started_at` | DateTime | — |
| `completed_at` | DateTime | — |
| `duration_seconds` | Float | — |
| `total_records` | Integer | default=0 |
| `records_created` | Integer | default=0 |
| `records_updated` | Integer | default=0 |
| `records_skipped` | Integer | default=0 |
| `records_failed` | Integer | default=0 |
| `error_message` | Text | — |
| `error_details` | JSON | default={} |
| `retry_count` | Integer | default=0 |
| `max_retries` | Integer | default=3 |
| `created_at` | DateTime | INDEX, default=datetime.utcnow |
| `sync_type` | String(50) | NOT NULL, INDEX, default="import" |
| `filters_applied` | String(255) | INDEX, default={} |

### `ats_webhook_logs`
**Classe:** `ATSWebhookLog` | **Herda:** `Base` | **Uso:** Routers/Services: 2 | Total refs: 4

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `connection_id` | UUID | INDEX |
| `provider` | Enum(ATSProvider) | NOT NULL, INDEX |
| `processed` | Boolean | INDEX, default=False |
| `processed_at` | DateTime | — |
| `processing_error` | Text | — |
| `signature_valid` | Boolean | — |
| `signature` | String(500) | — |
| `received_at` | DateTime | INDEX, default=datetime.utcnow |
| `ip_address` | String(50) | — |
| `user_agent` | String(500) | — |
| `event_type` | String(100) | NOT NULL, INDEX, default={} |

---

## audit_log
**Arquivo:** `lia-agent-system/libs/models/lia_models/audit_log.py`

### `audit_logs`
**Classe:** `AuditLog` | **Herda:** `Base` | **Uso:** Routers/Services: 6 | Total refs: 9

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | String(255) | PK, default=lambda: str(uuid.uuid4( |
| `company_id` | String(255) | NOT NULL, INDEX |
| `agent_name` | String(255) | NOT NULL, INDEX |
| `decision_type` | String(100) | NOT NULL, INDEX |
| `action` | String(255) | NOT NULL |
| `candidate_id` | String(255) | INDEX |
| `job_vacancy_id` | String(255) | INDEX |
| `decision` | String(100) | NOT NULL |
| `score` | Float | — |
| `confidence` | Float | — |
| `reasoning` | JSON | NOT NULL, default=list |
| `criteria_used` | JSON | NOT NULL, default=list |
| `criteria_ignored` | JSON | NOT NULL, default=list |
| `human_review_required` | Boolean | default=False |
| `human_reviewed_by` | String(255) | — |
| `human_reviewed_at` | DateTime | — |
| `human_override` | String(255) | — |
| `created_at` | DateTime | INDEX, default=func.now(, server_default |
| `retention_until` | DateTime | — |
| `session_id` | String(255) | INDEX |
| `agent_used` | String(255) | — |
| `input_text` | Text | — |
| `output_text` | Text | — |
| `fairness_flags` | JSON | default=list |

---

## audit_logs
**Arquivo:** `lia-agent-system/libs/models/lia_models/audit_logs.py`

### `audit_retention_policies`
**Classe:** `AuditRetentionPolicy` | **Herda:** `Base` | **Uso:** Routers/Services: 1 | Total refs: 3

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `category` | String(50) | NOT NULL, UNIQUE, INDEX |
| `retention_months` | Integer | NOT NULL |
| `description` | Text | — |
| `is_sox_required` | Boolean | default=False |
| `legal_basis` | String(255) | — |
| `is_active` | Boolean | default=True |
| `created_at` | DateTime | default=func.now(, server_default |
| `updated_at` | DateTime | default=func.now(, server_default |

### `sox_audit_logs`
**Classe:** `SOXAuditLog` | **Herda:** `Base` | **Uso:** Routers/Services: 2 | Total refs: 4

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `timestamp` | DateTime | NOT NULL, INDEX, default=func.now(, server_default |
| `user_id` | String(255) | INDEX |
| `user_email` | String(255) | — |
| `client_id` | String(255) | INDEX |
| `client_name` | String(255) | — |
| `action` | String(255) | NOT NULL, INDEX |
| `action_category` | String(50) | NOT NULL, INDEX |
| `resource_type` | String(100) | INDEX |
| `resource_id` | String(255) | — |
| `ip_address` | String(45) | — |
| `user_agent` | String(500) | — |
| `status` | String(20) | NOT NULL, INDEX, default="success" |
| `details` | JSON | default=dict |
| `retention_years` | Integer | default=7 |
| `retention_until` | DateTime | — |
| `request_id` | String(255) | — |
| `session_id` | String(255) | — |
| `created_at` | DateTime | default=func.now(, server_default |

---

## automation
**Arquivo:** `lia-agent-system/libs/models/lia_models/automation.py`

### `ai_suggestions`
**Classe:** `AISuggestion` | **Herda:** `Base` | **Uso:** Routers/Services: 3 | Total refs: 6

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `company_id` | String(255) | NOT NULL, INDEX |
| `candidate_id` | String(255) | INDEX |
| `vacancy_id` | String(255) | INDEX |
| `suggestion_type` | String(50) | NOT NULL, INDEX |
| `action_type` | String(50) | NOT NULL |
| `action_config` | JSON | default=dict |
| `title` | String(255) | NOT NULL |
| `description` | Text | — |
| `confidence_score` | String(10) | — |
| `reasoning` | Text | — |
| `status` | String(20) | NOT NULL, INDEX, default="pending" |
| `reviewed_by` | String(255) | — |
| `reviewed_at` | DateTime | — |
| `rejection_reason` | Text | — |
| `expires_at` | DateTime | — |
| `extra_data` | JSON | default=dict |
| `created_at` | DateTime | INDEX, default=datetime.utcnow |
| `updated_at` | DateTime | default=datetime.utcnow |

### `automation_execution_logs`
**Classe:** `AutomationExecutionLog` | **Herda:** `Base` | **Uso:** Routers/Services: 5 | Total refs: 8

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `automation_id` | UUID | NOT NULL, INDEX |
| `company_id` | String(255) | NOT NULL, INDEX |
| `trigger_event` | String(100) | NOT NULL |
| `trigger_data` | JSON | default=dict |
| `candidate_id` | String(255) | INDEX |
| `vacancy_id` | String(255) | INDEX |
| `action_executed` | String(50) | NOT NULL |
| `action_result` | JSON | default=dict |
| `status` | String(20) | NOT NULL, default="success" |
| `error_message` | Text | — |
| `execution_time_ms` | String(10) | — |
| `executed_at` | DateTime | INDEX, default=datetime.utcnow |

### `communication_automations`
**Classe:** `CommunicationAutomation` | **Herda:** `Base` | **Uso:** Routers/Services: 2 | Total refs: 5

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `company_id` | String(255) | NOT NULL, INDEX |
| `name` | String(255) | NOT NULL |
| `description` | Text | — |
| `trigger_type` | String(50) | NOT NULL, INDEX |
| `trigger_config` | JSON | default=dict |
| `action_type` | String(50) | NOT NULL |
| `action_config` | JSON | default=dict |
| `conditions` | JSON | default=list |
| `is_active` | Boolean | INDEX, default=True |
| `priority` | String(20) | default="normal" |
| `cooldown_minutes` | String(10) | default="0" |
| `execution_count` | String(10) | default="0" |
| `last_executed_at` | DateTime | — |
| `created_by` | String(255) | — |
| `updated_by` | String(255) | — |
| `created_at` | DateTime | INDEX, default=datetime.utcnow |
| `updated_at` | DateTime | default=datetime.utcnow |

### `stage_automation_rules`
**Classe:** `StageAutomationRule` | **Herda:** `Base` | **Uso:** Routers/Services: 1 | Total refs: 4

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `company_id` | String(255) | NOT NULL, INDEX |
| `trigger_type` | String(100) | NOT NULL, INDEX |
| `is_active` | Boolean | INDEX, default=True |
| `auto_execute` | Boolean | default=False |
| `confidence_threshold` | String(10) | default="0.8" |
| `conditions` | JSON | default=dict |
| `actions` | JSON | default=list |
| `source_stage` | String(100) | — |
| `target_stage` | String(100) | — |
| `name` | String(255) | — |
| `description` | Text | — |
| `priority` | String(20) | default="normal" |
| `created_at` | DateTime | INDEX, default=datetime.utcnow |
| `updated_at` | DateTime | default=datetime.utcnow |
| `created_by` | String(255) | — |

---

## background_jobs
**Arquivo:** `lia-agent-system/libs/models/lia_models/background_jobs.py`

### `background_jobs`
**Classe:** `BackgroundJob` | **Herda:** `Base` | **Uso:** Routers/Services: 1 | Total refs: 3

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid4 |
| `company_id` | UUID | NOT NULL, INDEX |
| `job_type` | String(50) | NOT NULL, INDEX |
| `name` | String(255) | NOT NULL |
| `description` | Text | — |
| `status` | String(20) | INDEX, default=JobStatus.PENDING.value |
| `progress` | Integer | default=0 |
| `config` | JSON | default=dict |
| `schedule` | String(100) | — |
| `result` | JSON | — |
| `error_message` | Text | — |
| `started_at` | DateTime | — |
| `completed_at` | DateTime | — |
| `next_run_at` | DateTime | INDEX |
| `last_run_at` | DateTime | — |
| `run_count` | Integer | default=0 |
| `created_by` | String(100) | — |
| `created_at` | DateTime | default=datetime.utcnow |
| `updated_at` | DateTime | default=datetime.utcnow |
| `Supports` | UUID | PK, default=uuid4 |

### `proactive_actions`
**Classe:** `ProactiveAction` | **Herda:** `Base` | **Uso:** Routers/Services: 2 | Total refs: 4

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid4 |
| `company_id` | UUID | NOT NULL, INDEX |
| `action_type` | String(50) | NOT NULL |
| `title` | String(255) | NOT NULL |
| `description` | Text | — |
| `priority` | String(20) | default=ActionPriority.NORMAL.value |
| `related_job_id` | UUID | INDEX |
| `related_candidate_id` | UUID | INDEX |
| `trigger_reason` | Text | — |
| `suggested_action` | JSON | — |
| `auto_executable` | Boolean | default=False |
| `status` | String(20) | INDEX, default=ActionStatus.PENDING.value |
| `accepted_by` | String(100) | — |
| `accepted_at` | DateTime | — |
| `executed_at` | DateTime | — |
| `created_at` | DateTime | INDEX, default=datetime.utcnow |
| `expires_at` | DateTime | — |
| `Supports` | UUID | PK, default=uuid4 |

---

## bias_audit_snapshot
**Arquivo:** `lia-agent-system/libs/models/lia_models/bias_audit_snapshot.py`

### `bias_audit_snapshots`
**Classe:** `BiasAuditSnapshot` | **Herda:** `Base` | **Uso:** Routers/Services: 2 | Total refs: 3

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `company_id` | UUID | NOT NULL, INDEX |
| `job_id` | String(36) | NOT NULL, INDEX |
| `evaluated_at` | DateTime | NOT NULL, default=datetime.utcnow |
| `total_candidates` | Integer | NOT NULL, default=0 |
| `has_alerts` | Boolean | NOT NULL, default=False |
| `created_at` | DateTime | NOT NULL, default=datetime.utcnow |
| `dimensions_json` | Text | NOT NULL, default=datetime.utcnow |

---

## billing
**Arquivo:** `lia-agent-system/libs/models/lia_models/billing.py`

### `company_modules`
**Classe:** `CompanyModule` | **Herda:** `Base` | **Uso:** Routers/Services: 1 | Total refs: 1

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `company_id` | String(100) | NOT NULL, FK → credit_accounts.company_id |
| `module_name` | String(100) | NOT NULL |
| `status` | String(20) | NOT NULL, default=ModuleStatus.BETA.value |
| `tier` | String(20) | NOT NULL, default=ModuleTier.FREE.value |
| `activated_at` | DateTime | default=datetime.utcnow |
| `expires_at` | DateTime | — |
| `metadata_json` | JSON | default=dict |
| `created_at` | DateTime | default=datetime.utcnow |
| `updated_at` | DateTime | default=datetime.utcnow |

### `credit_accounts`
**Classe:** `CreditAccount` | **Herda:** `Base` | **Uso:** Routers/Services: 2 | Total refs: 2

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `company_id` | String(100) | NOT NULL, UNIQUE, INDEX |
| `plan_type` | String(50) | NOT NULL, default="free" |
| `balance` | Integer | NOT NULL, default=0 |
| `lifetime_purchased` | Integer | NOT NULL, default=0 |
| `lifetime_consumed` | Integer | NOT NULL, default=0 |
| `lifetime_bonus` | Integer | NOT NULL, default=0 |
| `low_balance_threshold` | Integer | NOT NULL, default=20 |
| `reset_date` | DateTime | — |
| `created_at` | DateTime | default=datetime.utcnow |
| `updated_at` | DateTime | default=datetime.utcnow |

### `credit_transactions`
**Classe:** `CreditTransaction` | **Herda:** `Base` | **Uso:** Routers/Services: 1 | Total refs: 1

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `company_id` | String(100) | NOT NULL, INDEX |
| `transaction_type` | String(30) | NOT NULL, INDEX |
| `action_type` | String(50) | INDEX |
| `amount` | Integer | NOT NULL |
| `balance_after` | Integer | NOT NULL |
| `description` | String(500) | — |
| `reference_type` | String(50) | — |
| `reference_id` | String(100) | — |
| `performed_by` | String(100) | — |
| `created_at` | DateTime | INDEX, default=datetime.utcnow |

### `invoices`
**Classe:** `Invoice` | **Herda:** `Base` | **Uso:** Routers/Services: 5 | Total refs: 10

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `subscription_id` | UUID | NOT NULL, INDEX, FK → subscriptions.id |
| `client_id` | UUID | NOT NULL, INDEX, FK → client_accounts.id |
| `external_id` | String(255) | INDEX |
| `provider` | String(50) | NOT NULL |
| `status` | String(50) | INDEX, default=InvoiceStatus.PENDING.value |
| `amount_cents` | Integer | NOT NULL, default=0 |
| `discount_cents` | Integer | default=0 |
| `total_cents` | Integer | NOT NULL, default=0 |
| `currency` | String(10) | default="BRL" |
| `due_date` | Date | INDEX |
| `paid_at` | DateTime | — |
| `invoice_url` | String(500) | — |
| `pdf_url` | String(500) | — |
| `boleto_url` | String(500) | — |
| `boleto_barcode` | String(100) | — |
| `pix_qrcode` | Text | — |
| `pix_qrcode_url` | String(500) | — |
| `payment_method` | String(50) | — |
| `description` | Text | — |
| `notes` | Text | — |
| `retry_count` | Integer | default=0 |
| `last_retry_at` | DateTime | — |
| `failure_reason` | Text | — |
| `extra_data` | Text | — |
| `created_at` | DateTime | INDEX, default=datetime.utcnow |
| `updated_at` | DateTime | default=datetime.utcnow |

### `payment_methods`
**Classe:** `PaymentMethod` | **Herda:** `Base` | **Uso:** Routers/Services: 3 | Total refs: 5

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `subscription_id` | UUID | NOT NULL, INDEX, FK → subscriptions.id |
| `client_id` | UUID | NOT NULL, INDEX, FK → client_accounts.id |
| `external_id` | String(255) | INDEX |
| `provider` | String(50) | NOT NULL |
| `type` | String(50) | NOT NULL |
| `is_default` | Boolean | default=False |
| `is_active` | Boolean | default=True |
| `card_brand` | String(50) | — |
| `card_last_digits` | String(4) | — |
| `card_holder_name` | String(255) | — |
| `card_expiry_month` | Integer | — |
| `card_expiry_year` | Integer | — |
| `billing_name` | String(255) | — |
| `billing_email` | String(255) | — |
| `billing_document` | String(20) | — |
| `billing_phone` | String(50) | — |
| `extra_data` | Text | — |
| `created_at` | DateTime | default=datetime.utcnow |
| `updated_at` | DateTime | default=datetime.utcnow |

### `subscriptions`
**Classe:** `Subscription` | **Herda:** `Base` | **Uso:** Routers/Services: 9 | Total refs: 13

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `client_id` | UUID | NOT NULL, INDEX, FK → client_accounts.id |
| `provider` | String(50) | NOT NULL, INDEX |
| `external_id` | String(255) | INDEX |
| `external_customer_id` | String(255) | — |
| `plan_code` | String(100) | NOT NULL, INDEX |
| `plan_name` | String(255) | — |
| `status` | String(50) | INDEX, default=SubscriptionStatus.PENDING.value |
| `current_period_start` | DateTime | — |
| `current_period_end` | DateTime | — |
| `trial_end` | DateTime | — |
| `price_cents` | Integer | NOT NULL, default=0 |
| `currency` | String(10) | default="BRL" |
| `billing_cycle` | String(20) | default="monthly" |
| `billing_day` | Integer | — |
| `cancelled_at` | DateTime | — |
| `cancellation_reason` | Text | — |
| `extra_data` | Text | — |
| `created_at` | DateTime | INDEX, default=datetime.utcnow |
| `updated_at` | DateTime | default=datetime.utcnow |

---

## calibration
**Arquivo:** `lia-agent-system/libs/models/lia_models/calibration.py`

### `calibration_events`
**Classe:** `CalibrationEvent` | **Herda:** `Base` | **Uso:** Routers/Services: 4 | Total refs: 7

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | String | PK, default=lambda: str(uuid.uuid4( |
| `feedback_type` | Enum(FeedbackType) | NOT NULL |
| `status` | Enum(CalibrationStatus) | default=CalibrationStatus.PENDING |
| `candidate_id` | String | NOT NULL |
| `job_id` | String | — |
| `user_id` | String | — |
| `lia_score` | Float | — |
| `lia_ranking` | Integer | — |
| `lia_recommendation` | String(100) | — |
| `recruiter_action` | String(100) | — |
| `recruiter_stage_from` | String(100) | — |
| `recruiter_stage_to` | String(100) | — |
| `feedback_reason` | Text | — |
| `score_delta` | Float | — |
| `context` | JSON | default=dict |
| `processed_at` | DateTime | — |
| `applied_at` | DateTime | — |
| `created_at` | DateTime | default=datetime.utcnow |
| `updated_at` | DateTime | default=datetime.utcnow |
| `company_id` | String | NOT NULL, INDEX |

### `calibration_feedback`
**Classe:** `CalibrationFeedback` | **Herda:** `Base` | **Uso:** Routers/Services: 3 | Total refs: 3

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | String | PK, default=lambda: str(uuid.uuid4( |
| `vacancy_id` | String | — |
| `search_session_id` | String | — |
| `candidate_id` | String | NOT NULL |
| `user_id` | String | NOT NULL, default="default_user" |
| `feedback` | String | NOT NULL |
| `reason` | String | — |
| `candidate_snapshot` | JSON | — |
| `created_at` | DateTime | default=func.now(, server_default |

### `calibration_sessions`
**Classe:** `CalibrationSession` | **Herda:** `Base` | **Uso:** Routers/Services: 2 | Total refs: 4

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | String | PK, default=lambda: str(uuid.uuid4( |
| `vacancy_id` | String | — |
| `user_id` | String | NOT NULL, default="default_user" |
| `search_criteria` | JSON | — |
| `status` | String | default="awaiting_feedback" |
| `total_shown` | Integer | default=0 |
| `likes_count` | Integer | default=0 |
| `dislikes_count` | Integer | default=0 |
| `learned_criteria` | JSON | — |
| `created_at` | DateTime | default=func.now(, server_default |
| `completed_at` | DateTime | — |
| `min_feedbacks_required` | Integer | default=5 |
| `sourcing_blocked` | Boolean | default=True |
| `confirmation_message` | Text | — |

### `calibration_suggestions`
**Classe:** `CalibrationSuggestion` | **Herda:** `Base` | **Uso:** Routers/Services: 2 | Total refs: 4

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | String | PK, default=lambda: str(uuid.uuid4( |
| `suggestion_type` | String(50) | NOT NULL |
| `dimension` | String(100) | — |
| `current_weight` | Float | — |
| `suggested_weight` | Float | — |
| `title` | String(255) | NOT NULL |
| `description` | Text | — |
| `rationale` | Text | — |
| `supporting_evidence` | JSON | default=list |
| `impact_score` | Float | — |
| `confidence` | Float | — |
| `status` | String(50) | default="pending" |
| `approved_by` | String | — |
| `approved_at` | DateTime | — |
| `rejected_by` | String | — |
| `rejected_at` | DateTime | — |
| `rejection_reason` | Text | — |
| `created_at` | DateTime | default=datetime.utcnow |
| `updated_at` | DateTime | default=datetime.utcnow |

### `calibration_weights`
**Classe:** `CalibrationWeight` | **Herda:** `Base` | **Uso:** Routers/Services: 6 | Total refs: 11

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | String | PK, default=lambda: str(uuid.uuid4( |
| `job_id` | String | — |
| `job_category` | String(100) | — |
| `dimension` | String(100) | NOT NULL |
| `base_weight` | Float | default=1.0 |
| `adjusted_weight` | Float | default=1.0 |
| `confidence` | Float | default=0.5 |
| `sample_size` | Integer | default=0 |
| `last_adjustment_reason` | Text | — |
| `adjustment_history` | JSON | default=list |
| `is_active` | Boolean | default=True |
| `created_at` | DateTime | default=datetime.utcnow |
| `updated_at` | DateTime | default=datetime.utcnow |
| `company_id` | String | INDEX |

---

## candidate
**Arquivo:** `lia-agent-system/libs/models/lia_models/candidate.py`

### `candidate_education`
**Classe:** `CandidateEducation` | **Herda:** `Base` | **Uso:** Routers/Services: 7 | Total refs: 9

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `candidate_id` | UUID | NOT NULL, INDEX, FK → candidates.id |
| `institution` | String(255) | NOT NULL, INDEX |
| `degree` | String(100) | — |
| `field_of_study` | String(255) | — |
| `start_date` | String(50) | — |
| `end_date` | String(50) | — |
| `is_completed` | Boolean | default=True |
| `description` | Text | — |
| `gpa` | String(20) | — |
| `location` | String(255) | — |
| `institution_city` | String(100) | — |
| `institution_state` | String(100) | — |
| `institution_country` | String(100) | INDEX |
| `institution_ranking` | Integer | — |
| `institution_tier` | String(50) | INDEX |
| `sequence_order` | Integer | default=0 |
| `created_at` | DateTime | default=datetime.utcnow |
| `updated_at` | DateTime | default=datetime.utcnow |

### `candidate_experiences`
**Classe:** `CandidateExperience` | **Herda:** `Base` | **Uso:** Routers/Services: 7 | Total refs: 9

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `candidate_id` | UUID | NOT NULL, INDEX, FK → candidates.id |
| `company_name` | String(255) | NOT NULL, INDEX |
| `company_linkedin_url` | String(500) | — |
| `company_domain` | String(255) | — |
| `title` | String(255) | — |
| `start_date` | String(50) | — |
| `end_date` | String(50) | — |
| `duration_years` | Float | — |
| `is_current` | Boolean | default=False |
| `description` | Text | — |
| `location` | String(255) | — |
| `industries` | String | INDEX, default=list |
| `company_size` | String(50) | — |
| `company_size_range` | String(50) | — |
| `technologies` | String | default=list |
| `is_startup` | Boolean | — |
| `company_founded_year` | Integer | — |
| `company_annual_revenue` | Float | — |
| `funding_stage` | String(50) | INDEX |
| `company_tags` | String | default=list |
| `company_hq_city` | String(100) | — |
| `company_hq_state` | String(100) | — |
| `company_hq_country` | String(100) | INDEX |
| `sequence_order` | Integer | default=0 |
| `created_at` | DateTime | default=datetime.utcnow |
| `updated_at` | DateTime | default=datetime.utcnow |

### `candidate_favorites`
**Classe:** `CandidateFavorite` | **Herda:** `Base` | **Uso:** Routers/Services: 3 | Total refs: 3

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `candidate_id` | String(255) | NOT NULL, INDEX |
| `user_id` | String(255) | NOT NULL, INDEX, default="default_user" |
| `company_id` | String(255) | NOT NULL, INDEX |
| `note` | Text | — |
| `is_pinned` | Boolean | default=False |
| `source` | String(50) | — |
| `created_at` | DateTime | INDEX, default=func.now(, server_default |
| `updated_at` | DateTime | default=func.now(, server_default |

### `candidate_hidden`
**Classe:** `CandidateHidden` | **Herda:** `Base` | **Uso:** Routers/Services: 3 | Total refs: 3

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `candidate_id` | String(255) | NOT NULL, INDEX |
| `user_id` | String(255) | NOT NULL, INDEX, default="default_user" |
| `company_id` | String(255) | NOT NULL, INDEX |
| `reason` | Text | — |
| `source` | String(50) | — |
| `created_at` | DateTime | INDEX, default=func.now(, server_default |

### `candidate_searches`
**Classe:** `CandidateSearch` | **Herda:** `Base` | **Uso:** Routers/Services: 3 | Total refs: 5

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `user_id` | String(255) | NOT NULL, INDEX |
| `total_results` | Integer | default=0 |
| `used_global_search` | Boolean | INDEX, default=False |
| `credits_consumed` | Integer | default=0 |
| `search_duration_ms` | Integer | — |
| `created_at` | DateTime | INDEX, default=datetime.utcnow |
| `conversation_id` | UUID | NOT NULL, INDEX, default={} |
| `search_source` | String(50) | default="local" |
| `candidates_clicked` | String | INDEX, default=list |

### `candidate_sources`
**Classe:** `CandidateSource` | **Herda:** `Base` | **Uso:** Routers/Services: 1 | Total refs: 1

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `candidate_id` | UUID | NOT NULL, INDEX, FK → candidates.id |
| `source` | String(50) | NOT NULL, INDEX |
| `source_profile_id` | String(255) | NOT NULL, INDEX |
| `linkedin_url` | String(500) | INDEX |
| `fingerprint_hash` | String(64) | INDEX |
| `is_primary` | Boolean | default=False |
| `external_profile_id` | UUID | INDEX |
| `created_at` | DateTime | INDEX, default=datetime.utcnow |
| `updated_at` | DateTime | default=datetime.utcnow |

### `candidates`
**Classe:** `Candidate` | **Herda:** `EncryptedFieldMixin, Base` | **Uso:** Routers/Services: 140 | Total refs: 186

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `name` | String(255) | NOT NULL, INDEX |
| `_email_raw` | String(255) | INDEX |
| `secondary_email` | String(255) | — |
| `_email_encrypted` | LargeBinary | — |
| `email_hash` | String(64) | INDEX |
| `phone` | String(50) | — |
| `mobile_phone` | String(50) | — |
| `secondary_phone` | String(50) | — |
| `linkedin_url` | String(500) | — |
| `github_url` | String(500) | — |
| `portfolio_url` | String(500) | — |
| `avatar_url` | String(500) | — |
| `date_of_birth` | Date | — |
| `gender` | String(50) | — |
| `nationality` | String(100) | — |
| `marital_status` | String(50) | — |
| `_cpf_raw` | String(14) | — |
| `_cpf_encrypted` | LargeBinary | — |
| `current_title` | String(255) | — |
| `current_company` | String(255) | — |
| `seniority_level` | String(50) | — |
| `years_of_experience` | Integer | — |
| `self_introduction` | Text | — |
| `technical_skills` | String | default=list |
| `soft_skills` | String | default=list |
| `languages` | JSON | default={} |
| `certifications` | String | default=list |
| `interests` | String | default=list |
| `location_city` | String(100) | INDEX |
| `location_state` | String(100) | — |
| `location_country` | String(100) | INDEX |
| `address_street` | String(255) | — |
| `address_number` | String(20) | — |
| `address_district` | String(100) | — |
| `address_zip` | String(20) | — |
| `address_complement` | String(255) | — |
| `timezone` | String(50) | INDEX |
| `past_locations` | JSON | default=[] |
| `is_remote` | Boolean | default=False |
| `willing_to_relocate` | Boolean | default=False |
| `mobility` | Boolean | default=False |
| `work_model_preference` | String(50) | — |
| `contract_type_preference` | String(50) | — |
| `current_salary` | Float | — |
| `salary_currency` | String(10) | default="BRL" |
| `desired_salary_min` | Float | — |
| `desired_salary_max` | Float | — |
| `salary_expectation_clt` | Float | — |
| `salary_expectation_pj` | Float | — |
| `salary_expectation_freelance` | Float | — |
| `resume_url` | String(500) | — |
| `resume_text` | Text | — |
| `cover_letter` | Text | — |
| `source` | String(50) | NOT NULL, INDEX |
| `ats_source_name` | String(100) | — |
| `ats_candidate_id` | String(255) | — |
| `pearch_profile_id` | String(255) | — |
| `is_open_to_work` | Boolean | — |
| `is_decision_maker` | Boolean | — |
| `is_top_universities` | Boolean | — |
| `is_hiring` | Boolean | — |
| `headline` | String(500) | — |
| `expertise` | String | default=list |
| `linkedin_followers_count` | Integer | — |
| `linkedin_connections_count` | Integer | — |
| `outreach_message` | Text | — |
| `lia_score` | Float | — |
| `lia_insights` | JSON | default={} |
| `skills_match_percentage` | Float | — |
| `status` | String(50) | INDEX, default="new" |
| `is_active` | Boolean | INDEX, default=True |
| `is_blacklisted` | Boolean | default=False |
| `blacklist_reason` | Text | — |
| `is_hired` | Boolean | NOT NULL, default=False, server_default |
| `hired_at` | DateTime | — |
| `hired_job_id` | String(255) | — |
| `hired_job_title` | String(500) | — |
| `blacklisted_by` | String(255) | — |
| `blacklisted_at` | DateTime | — |
| `preferred_contact_method` | String(50) | default="email" |
| `best_time_to_contact` | String(100) | — |
| `communication_consent` | Boolean | default=True |
| `completed_register` | Boolean | default=False |
| `accept_terms` | Boolean | default=False |
| `work_history` | JSON | default=[] |
| `tags` | String | default=list |
| `notes` | Text | — |
| `additional_data` | JSON | default={} |
| `created_at` | DateTime | INDEX, default=datetime.utcnow |
| `updated_at` | DateTime | default=datetime.utcnow |
| `last_contacted_at` | DateTime | — |
| `last_activity_at` | DateTime | — |
| `diversity_race_ethnicity` | String(50) | default=False |
| `pearch_insights` | Text | default={} |
| `best_personal_email` | String(255) | default=[] |
| `preferred_channels` | Boolean | default=lambda: ["email"] |
| `scheduled_deletion_at` | DateTime | INDEX |

### `credits_usage`
**Classe:** `CreditsUsage` | **Herda:** `Base` | **Uso:** Routers/Services: 1 | Total refs: 3

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `user_id` | String(255) | NOT NULL, INDEX |
| `credits_amount` | Integer | NOT NULL |
| `credits_balance_before` | Integer | NOT NULL |
| `credits_balance_after` | Integer | NOT NULL |
| `created_at` | DateTime | INDEX, default=datetime.utcnow |
| `company_id` | String(255) | NOT NULL, INDEX |
| `action_type` | String(50) | NOT NULL, INDEX |
| `search_id` | UUID | INDEX, default={} |

### `external_candidate_profiles`
**Classe:** `ExternalCandidateProfile` | **Herda:** `Base` | **Uso:** Routers/Services: 3 | Total refs: 4

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `company_id` | String(255) | NOT NULL, INDEX |
| `source` | String(50) | NOT NULL, INDEX |
| `source_profile_id` | String(255) | NOT NULL, INDEX |
| `linkedin_url` | String(500) | INDEX |
| `raw_payload` | JSON | default={} |
| `name` | String(255) | NOT NULL, INDEX |
| `normalized_name` | String(255) | INDEX |
| `first_name` | String(100) | — |
| `last_name` | String(100) | — |
| `email` | String(255) | INDEX |
| `phone` | String(50) | — |
| `avatar_url` | String(500) | — |
| `headline` | String(500) | — |
| `summary` | Text | — |
| `current_title` | String(255) | INDEX |
| `current_company` | String(255) | INDEX |
| `location_city` | String(100) | INDEX |
| `location_state` | String(100) | — |
| `location_country` | String(100) | INDEX |
| `location_raw` | String(255) | — |
| `years_of_experience` | Integer | — |
| `seniority_level` | String(50) | — |
| `skills` | String | default=list |
| `expertise` | String | default=list |
| `languages` | JSON | default={} |
| `experiences_snapshot` | JSON | default=[] |
| `education_snapshot` | JSON | default=[] |
| `is_open_to_work` | Boolean | — |
| `is_decision_maker` | Boolean | — |
| `is_top_universities` | Boolean | — |
| `is_hiring` | Boolean | — |
| `best_personal_email` | String(255) | — |
| `estimated_age` | Integer | — |
| `outreach_message` | Text | — |
| `linkedin_followers_count` | Integer | — |
| `linkedin_connections_count` | Integer | — |
| `has_email` | Boolean | INDEX, default=False |
| `has_phone` | Boolean | INDEX, default=False |
| `contact_revealed` | Boolean | INDEX, default=False |
| `fingerprint_hash` | String(64) | INDEX |
| `similarity_score` | Float | — |
| `status` | String(50) | INDEX, default="discovered" |
| `search_query` | Text | — |
| `discovered_by` | String(255) | — |
| `promoted_to_candidate_id` | UUID | INDEX |
| `promoted_at` | DateTime | — |
| `promoted_by` | String(255) | — |
| `created_at` | DateTime | INDEX, default=datetime.utcnow |
| `updated_at` | DateTime | default=datetime.utcnow |
| `best_business_email` | String(255) | default=[] |
| `middle_name` | String(100) | default=[] |
| `pearch_insights` | Integer | default={} |

### `vacancy_candidates`
**Classe:** `VacancyCandidate` | **Herda:** `Base` | **Uso:** Routers/Services: 39 | Total refs: 54

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `vacancy_id` | UUID | NOT NULL, INDEX |
| `candidate_id` | UUID | NOT NULL, INDEX |
| `company_id` | String(255) | NOT NULL, INDEX |
| `source` | String(50) | NOT NULL, default="local" |
| `origin` | String(50) | INDEX, default="web" |
| `lia_score` | Float | — |
| `match_percentage` | Float | — |
| `status` | String(50) | INDEX, default="sourced" |
| `stage` | String(50) | INDEX, default="initial" |
| `previous_status` | String(50) | — |
| `added_by` | String(255) | — |
| `notes` | Text | — |
| `additional_data` | JSON | default={} |
| `rejected_by_human` | Boolean | default=None |
| `human_reviewer_id` | String(255) | — |
| `created_at` | DateTime | INDEX, default=datetime.utcnow |
| `updated_at` | DateTime | default=datetime.utcnow |
| `scheduled_deletion_at` | DateTime | INDEX, default=datetime.utcnow |

### `viewed_candidates`
**Classe:** `ViewedCandidate` | **Herda:** `Base` | **Uso:** Routers/Services: 1 | Total refs: 3

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `candidate_id` | String(255) | NOT NULL, INDEX |
| `user_id` | String(255) | NOT NULL, INDEX, default="default_user" |
| `viewed_at` | DateTime | default=func.now(, server_default |
| `source` | String(50) | — |

---

## candidate_attachment
**Arquivo:** `lia-agent-system/libs/models/lia_models/candidate_attachment.py`

### `candidate_attachments`
**Classe:** `CandidateAttachment` | **Herda:** `Base` | **Uso:** Routers/Services: 1 | Total refs: 3

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | String | PK, default=lambda: str(uuid.uuid4( |
| `candidate_id` | String(255) | NOT NULL, INDEX |
| `candidate_name` | String(255) | NOT NULL |
| `file_name` | String(500) | NOT NULL |
| `file_type` | String(50) | NOT NULL, INDEX |
| `file_url` | String(1000) | NOT NULL |
| `file_size` | Integer | — |
| `mime_type` | String(100) | — |
| `upload_source` | String(50) | NOT NULL, INDEX |
| `related_entity_type` | String(50) | — |
| `related_entity_id` | String(255) | — |
| `description` | Text | — |
| `is_active` | Boolean | INDEX, default=True |
| `company_id` | String(255) | NOT NULL, INDEX |
| `uploaded_by` | String(255) | NOT NULL |
| `uploaded_by_name` | String(255) | — |
| `created_at` | DateTime | INDEX, default=datetime.utcnow |
| `updated_at` | DateTime | default=datetime.utcnow |

---

## candidate_feedback
**Arquivo:** `lia-agent-system/libs/models/lia_models/candidate_feedback.py`

### `candidate_feedbacks`
**Classe:** `CandidateFeedback` | **Herda:** `Base` | **Uso:** Routers/Services: 7 | Total refs: 11

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | String | PK, default=lambda: str(uuid.uuid4( |
| `candidate_id` | String | NOT NULL, INDEX |
| `vacancy_id` | String | NOT NULL, INDEX |
| `feedback_type` | String(50) | NOT NULL, INDEX |
| `adherence_score` | Float | — |
| `candidate_name` | String(255) | — |
| `candidate_email` | String(255) | — |
| `candidate_phone` | String(50) | — |
| `vacancy_title` | String(255) | — |
| `company_name` | String(255) | — |
| `channels_sent` | JSON | default=list |
| `channels_failed` | JSON | default=list |
| `message_subject` | String(500) | — |
| `message_preview` | Text | — |
| `email_sent` | Boolean | default=False |
| `email_sent_at` | DateTime | — |
| `email_opened` | Boolean | default=False |
| `email_opened_at` | DateTime | — |
| `email_clicked` | Boolean | default=False |
| `email_clicked_at` | DateTime | — |
| `whatsapp_sent` | Boolean | default=False |
| `whatsapp_sent_at` | DateTime | — |
| `whatsapp_delivered` | Boolean | default=False |
| `whatsapp_delivered_at` | DateTime | — |
| `whatsapp_read` | Boolean | default=False |
| `whatsapp_read_at` | DateTime | — |
| `resubmit_url` | String(500) | — |
| `resubmit_token` | String(100) | — |
| `resubmit_clicked` | Boolean | default=False |
| `resubmit_clicked_at` | DateTime | — |
| `resubmit_completed` | Boolean | default=False |
| `resubmit_completed_at` | DateTime | — |
| `new_adherence_score` | Float | — |
| `improvement_tips` | JSON | default=list |
| `missing_skills` | JSON | default=list |
| `matched_skills` | JSON | default=list |
| `sent_at` | DateTime | default=datetime.utcnow |
| `created_at` | DateTime | default=datetime.utcnow |
| `updated_at` | DateTime | default=datetime.utcnow |
| `sent_by` | String(100) | default="lia_system" |
| `triggered_by` | String(100) | — |
| `extra_data` | JSON | default=dict |

---

## candidate_job
**Arquivo:** `lia-agent-system/libs/models/lia_models/candidate_job.py`

### `candidate_jobs`
**Classe:** `CandidateJob` | **Herda:** `Base` | **Uso:** Routers/Services: 1 | Total refs: 3

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `candidate_id` | UUID | NOT NULL, INDEX |
| `job_vacancy_id` | UUID | NOT NULL, INDEX |
| `status` | String(50) | INDEX, default="Novo" |
| `applied_at` | DateTime | NOT NULL, default=datetime.utcnow |
| `created_at` | DateTime | INDEX, default=datetime.utcnow |
| `updated_at` | DateTime | default=datetime.utcnow |
| `source` | String(100) | NOT NULL, default=datetime.utcnow |

---

## candidate_list
**Arquivo:** `lia-agent-system/libs/models/lia_models/candidate_list.py`

### `candidate_list_members`
**Classe:** `CandidateListMember` | **Herda:** `Base` | **Uso:** Routers/Services: 3 | Total refs: 5

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `list_id` | UUID | NOT NULL, INDEX, FK → candidate_lists.id |
| `candidate_id` | UUID | NOT NULL, INDEX, FK → candidates.id |
| `added_by` | String(255) | NOT NULL |
| `added_at` | DateTime | INDEX, default=datetime.utcnow |
| `notes` | Text | — |
| `source` | String(50) | default="manual" |

### `candidate_lists`
**Classe:** `CandidateList` | **Herda:** `Base` | **Uso:** Routers/Services: 3 | Total refs: 6

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `company_id` | String(255) | NOT NULL, INDEX |
| `name` | String(255) | NOT NULL |
| `description` | Text | — |
| `color` | String(20) | — |
| `created_by` | String(255) | NOT NULL |
| `created_at` | DateTime | INDEX, default=datetime.utcnow |
| `updated_at` | DateTime | default=datetime.utcnow |
| `is_active` | Boolean | INDEX, default=True |

---

## client_account
**Arquivo:** `lia-agent-system/libs/models/lia_models/client_account.py`

### `client_accounts`
**Classe:** `ClientAccount` | **Herda:** `Base` | **Uso:** Routers/Services: 18 | Total refs: 20

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `name` | String(255) | NOT NULL |
| `trade_name` | String(255) | — |
| `cnpj` | String(20) | UNIQUE |
| `primary_email` | String(255) | — |
| `primary_phone` | String(50) | — |
| `website` | String(500) | — |
| `address` | JSON | default=dict |
| `status` | String(50) | INDEX, default=ClientStatus.PENDING_SETUP.value |
| `plan_id` | String(100) | INDEX |
| `contract_start_date` | DateTime | — |
| `contract_end_date` | DateTime | — |
| `user_limit` | Integer | default=10 |
| `job_limit` | Integer | default=50 |
| `ai_credits_monthly` | Integer | default=1000 |
| `settings` | JSON | default=dict |
| `features_enabled` | JSON | default=list |
| `account_manager_id` | String(255) | — |
| `implementation_manager_id` | String(255) | — |
| `logo_url` | String(500) | — |
| `industry` | String(100) | — |
| `company_size` | String(50) | — |
| `created_at` | DateTime | INDEX, default=datetime.utcnow |
| `updated_at` | DateTime | default=datetime.utcnow |
| `onboarding_completed_at` | DateTime | — |
| `welcome_email_sent` | Boolean | default=False |
| `welcome_email_sent_at` | DateTime | — |
| `workos_organization_created` | Boolean | default=False |
| `workos_organization_created_at` | DateTime | — |
| `sso_configured` | Boolean | default=False |
| `sso_configured_at` | DateTime | — |
| `is_deleted` | Boolean | INDEX, default=False |
| `deleted_at` | DateTime | — |
| `deleted_by` | String(255) | — |

---

## client_user
**Arquivo:** `lia-agent-system/libs/models/lia_models/client_user.py`

### `client_users`
**Classe:** `ClientUser` | **Herda:** `EncryptedFieldMixin, Base` | **Uso:** Routers/Services: 4 | Total refs: 6

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `company_id` | UUID | NOT NULL, INDEX, FK → client_accounts.id |
| `user_id` | UUID | — |
| `_email_raw` | String(255) | — |
| `_email_encrypted` | LargeBinary | — |
| `email_hash` | String(64) | INDEX |
| `name` | String(255) | NOT NULL |
| `role` | String(50) | NOT NULL, default=ClientUserRole.VIEWER.value |
| `permissions` | JSON | default=list |
| `status` | String(20) | INDEX, default=ClientUserStatus.PENDING.value |
| `invitation_token` | String(255) | INDEX |
| `invitation_expires_at` | DateTime | — |
| `invited_at` | DateTime | default=datetime.utcnow |
| `accepted_at` | DateTime | — |
| `last_login_at` | DateTime | — |
| `created_at` | DateTime | INDEX, default=datetime.utcnow |
| `updated_at` | DateTime | default=datetime.utcnow |
| `is_deleted` | Boolean | INDEX, default=False |
| `deleted_at` | DateTime | — |
| `deleted_by` | String(255) | — |

---

## communication_history
**Arquivo:** `lia-agent-system/libs/models/lia_models/communication_history.py`

### `communication_history`
**Classe:** `CommunicationHistory` | **Herda:** `Base` | **Uso:** Routers/Services: 2 | Total refs: 6

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | String | PK, default=lambda: str(uuid.uuid4( |
| `candidate_id` | String(255) | NOT NULL, INDEX |
| `candidate_name` | String(255) | NOT NULL |
| `candidate_email` | String(255) | — |
| `candidate_phone` | String(50) | — |
| `vacancy_id` | String(255) | INDEX |
| `vacancy_title` | String(255) | — |
| `communication_type` | String(50) | NOT NULL, INDEX |
| `channel` | String(20) | NOT NULL |
| `direction` | String(20) | NOT NULL |
| `subject` | String(500) | — |
| `message_content` | Text | NOT NULL |
| `message_preview` | String(500) | — |
| `template_id` | String(255) | — |
| `template_name` | String(255) | — |
| `status` | String(20) | NOT NULL, INDEX, default="pending" |
| `sent_at` | DateTime | — |
| `delivered_at` | DateTime | — |
| `read_at` | DateTime | — |
| `failed_at` | DateTime | — |
| `error_message` | Text | — |
| `extra_data` | JSON | default=dict |
| `attachments` | JSON | default=list |
| `sent_by` | String(255) | NOT NULL |
| `sent_by_name` | String(255) | — |
| `created_at` | DateTime | INDEX, default=datetime.utcnow |
| `updated_at` | DateTime | default=datetime.utcnow |
| `company_id` | String(255) | NOT NULL, INDEX |

---

## communication_matrix
**Arquivo:** `lia-agent-system/libs/models/lia_models/communication_matrix.py`

### `communication_matrix_entries`
**Classe:** `CommunicationMatrixEntry` | **Herda:** `Base` | **Uso:** Routers/Services: 3 | Total refs: 4

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `company_id` | String(255) | INDEX |
| `module` | String(50) | NOT NULL, INDEX |
| `trigger_name` | String(100) | NOT NULL, INDEX |
| `trigger_description` | Text | — |
| `recipient_type` | String(50) | NOT NULL |
| `channels` | JSON | default=list |
| `is_automatic` | Boolean | default=True |
| `template_id` | String(100) | — |
| `requires_approval` | Boolean | default=False |
| `is_active` | Boolean | INDEX, default=True |
| `display_order` | Integer | default=0 |
| `created_at` | DateTime | default=datetime.utcnow |
| `updated_at` | DateTime | default=datetime.utcnow |
| `Stores` | UUID | PK, default=uuid.uuid4 |

---

## communication_settings
**Arquivo:** `lia-agent-system/libs/models/lia_models/communication_settings.py`

### `communication_settings`
**Classe:** `CommunicationSettings` | **Herda:** `Base` | **Uso:** Routers/Services: 3 | Total refs: 5

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `company_id` | String(255) | NOT NULL, UNIQUE, INDEX |
| `signature` | Text | — |
| `signature_html` | Text | — |
| `sending_hours_start` | Integer | default=8 |
| `sending_hours_end` | Integer | default=20 |
| `respect_holidays` | Boolean | default=True |
| `respect_weekends` | Boolean | default=True |
| `timezone` | String(50) | default="America/Sao_Paulo" |
| `max_messages_per_day` | Integer | default=3 |
| `max_messages_per_candidate` | Integer | default=5 |
| `cooldown_hours_between_messages` | Integer | default=24 |
| `lgpd_compliant` | Boolean | default=True |
| `require_consent_before_contact` | Boolean | default=True |
| `auto_unsubscribe_after_days` | Integer | default=90 |
| `default_email_from_name` | String(255) | — |
| `default_reply_to` | String(255) | — |
| `mailgun_enabled` | Boolean | default=True |
| `twilio_enabled` | Boolean | default=False |
| `created_at` | DateTime | default=datetime.utcnow |
| `updated_at` | DateTime | default=datetime.utcnow |
| `Stores` | UUID | PK, default=uuid.uuid4 |

### `lgpd_consents`
**Classe:** `LGPDConsent` | **Herda:** `Base` | **Uso:** Routers/Services: 4 | Total refs: 6

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `company_id` | String(255) | NOT NULL, INDEX |
| `candidate_id` | String(255) | NOT NULL, INDEX |
| `candidate_email` | String(255) | — |
| `candidate_phone` | String(50) | — |
| `consent_type` | String(50) | NOT NULL, INDEX |
| `consent_given` | Boolean | default=False |
| `consent_date` | DateTime | — |
| `consent_source` | String(100) | — |
| `consent_text` | Text | — |
| `ip_address` | String(50) | — |
| `user_agent` | Text | — |
| `revoked_at` | DateTime | — |
| `revoked_by` | String(255) | — |
| `revoke_reason` | Text | — |
| `created_at` | DateTime | INDEX, default=datetime.utcnow |
| `updated_at` | DateTime | default=datetime.utcnow |

---

## company
**Arquivo:** `lia-agent-system/libs/models/lia_models/company.py`

### `approvers`
**Classe:** `Approver` | **Herda:** `Base` | **Uso:** Routers/Services: 3 | Total refs: 3

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `company_id` | UUID | NOT NULL, FK → company_profiles.id |
| `user_id` | UUID | — |
| `user_name` | String(255) | NOT NULL |
| `email` | String(255) | NOT NULL |
| `role` | String(255) | — |
| `level` | Integer | NOT NULL, default=1 |
| `is_active` | Boolean | default=True |
| `created_at` | DateTime | default=datetime.utcnow |
| `updated_at` | DateTime | default=datetime.utcnow |

### `benefit_templates`
**Classe:** `BenefitTemplate` | **Herda:** `Base` | **Uso:** Routers/Services: 2 | Total refs: 2

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `name` | String(255) | NOT NULL |
| `description` | Text | — |
| `category` | String(100) | NOT NULL |
| `is_popular` | Boolean | default=False |
| `is_active` | Boolean | default=True |
| `order` | Integer | default=0 |
| `created_at` | DateTime | default=datetime.utcnow |
| `updated_at` | DateTime | default=datetime.utcnow |

### `benefits`
**Classe:** `Benefit` | **Herda:** `Base` | **Uso:** Routers/Services: 11 | Total refs: 14

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `company_id` | UUID | NOT NULL, FK → company_profiles.id |
| `name` | String(255) | NOT NULL |
| `description` | Text | — |
| `category` | String(100) | NOT NULL |
| `icon` | String(50) | — |
| `value` | Float | — |
| `value_type` | String(50) | default="monetary" |
| `value_details` | Text | — |
| `percentage_value` | Float | — |
| `applicable_to` | String | default=[] |
| `seniority_levels` | String | default=[] |
| `contract_types` | String | default=[] |
| `departments` | JSON | default=[] |
| `waiting_period_days` | Integer | default=0 |
| `is_mandatory` | Boolean | default=False |
| `is_active` | Boolean | default=True |
| `is_highlighted` | Boolean | default=False |
| `is_discount` | Boolean | default=False |
| `order` | Integer | default=0 |
| `provider` | String(255) | — |
| `provider_contact` | String(255) | — |
| `created_at` | DateTime | default=datetime.utcnow |
| `updated_at` | DateTime | default=datetime.utcnow |
| `Supports` | UUID | PK, default=uuid.uuid4 |

### `big_five_questions`
**Classe:** `BigFiveQuestion` | **Herda:** `Base` | **Uso:** Routers/Services: 1 | Total refs: 3

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `text` | Text | NOT NULL |
| `text_en` | Text | — |
| `trait` | String(50) | NOT NULL |
| `facet` | String(100) | — |
| `polarity` | String(10) | default="positive" |
| `scale_min` | Integer | default=1 |
| `scale_max` | Integer | default=5 |
| `scale_labels` | JSON | default={} |
| `category` | String(100) | default="general" |
| `role_specific` | String | default=[] |
| `weight` | Float | default=1.0 |
| `is_active` | Boolean | default=True |
| `is_core` | Boolean | default=False |
| `validation_stats` | JSON | default={} |
| `ai_generated` | Boolean | default=False |
| `order` | Integer | default=0 |
| `created_at` | DateTime | default=datetime.utcnow |
| `updated_at` | DateTime | default=datetime.utcnow |

### `big_five_role_profiles`
**Classe:** `BigFiveRoleProfile` | **Herda:** `Base` | **Uso:** Routers/Services: 1 | Total refs: 3

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `company_id` | UUID | FK → company_profiles.id |
| `name` | String(255) | NOT NULL |
| `description` | Text | — |
| `role_category` | String(100) | — |
| `seniority_level` | String(50) | — |
| `openness_min` | Float | default=1.0 |
| `openness_max` | Float | default=5.0 |
| `openness_ideal` | Float | default=3.0 |
| `openness_weight` | Float | default=1.0 |
| `conscientiousness_min` | Float | default=1.0 |
| `conscientiousness_max` | Float | default=5.0 |
| `conscientiousness_ideal` | Float | default=3.0 |
| `conscientiousness_weight` | Float | default=1.0 |
| `extroversion_min` | Float | default=1.0 |
| `extroversion_max` | Float | default=5.0 |
| `extroversion_ideal` | Float | default=3.0 |
| `extroversion_weight` | Float | default=1.0 |
| `agreeableness_min` | Float | default=1.0 |
| `agreeableness_max` | Float | default=5.0 |
| `agreeableness_ideal` | Float | default=3.0 |
| `agreeableness_weight` | Float | default=1.0 |
| `neuroticism_min` | Float | default=1.0 |
| `neuroticism_max` | Float | default=5.0 |
| `neuroticism_ideal` | Float | default=3.0 |
| `neuroticism_weight` | Float | default=1.0 |
| `facet_requirements` | JSON | default={} |
| `is_active` | Boolean | default=True |
| `is_template` | Boolean | default=True |
| `usage_count` | Integer | default=0 |
| `created_at` | DateTime | default=datetime.utcnow |
| `updated_at` | DateTime | default=datetime.utcnow |
| `created_by` | String(255) | — |

### `company_profiles`
**Classe:** `CompanyProfile` | **Herda:** `Base` | **Uso:** Routers/Services: 22 | Total refs: 25

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `client_account_id` | UUID | UNIQUE, INDEX, FK → client_accounts.id |
| `name` | String(255) | NOT NULL |
| `trading_name` | String(255) | — |
| `website` | String(500) | — |
| `logo_url` | String(500) | — |
| `cnpj` | String(18) | — |
| `industry` | String(100) | — |
| `sector` | String(100) | — |
| `company_size` | String(50) | — |
| `founded_year` | Integer | — |
| `description` | Text | — |
| `short_description` | String(500) | — |
| `headquarters_city` | String(100) | — |
| `headquarters_state` | String(100) | — |
| `headquarters_country` | String(100) | default="Brasil" |
| `address` | Text | — |
| `main_phone` | String(50) | — |
| `hr_phone` | String(50) | — |
| `main_email` | String(255) | — |
| `hr_email` | String(255) | — |
| `linkedin_url` | String(500) | — |
| `glassdoor_url` | String(500) | — |
| `employee_count` | Integer | — |
| `revenue_range` | String(100) | — |
| `is_active` | Boolean | default=True |
| `is_default` | Boolean | default=False |
| `culture_analyzed` | Boolean | default=False |
| `culture_analysis_date` | DateTime | — |
| `culture_insights` | JSON | default={} |
| `ats_history_analyzed` | Boolean | default=False |
| `ats_analysis_date` | DateTime | — |
| `ats_insights` | JSON | default={} |
| `additional_data` | JSON | default={} |
| `created_at` | DateTime | default=datetime.utcnow |
| `updated_at` | DateTime | default=datetime.utcnow |
| `created_by` | String(255) | — |

### `culture_values`
**Classe:** `CultureValue` | **Herda:** `Base` | **Uso:** Routers/Services: 3 | Total refs: 5

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `company_id` | UUID | NOT NULL, FK → company_profiles.id |
| `name` | String(255) | NOT NULL |
| `description` | Text | — |
| `category` | String(100) | default="value" |
| `icon` | String(50) | — |
| `color` | String(20) | — |
| `behavioral_indicators` | String | default=[] |
| `interview_questions` | String | default=[] |
| `weight` | Float | default=1.0 |
| `is_active` | Boolean | default=True |
| `order` | Integer | default=0 |
| `ai_generated` | Boolean | default=False |
| `source` | String(100) | — |
| `created_at` | DateTime | default=datetime.utcnow |
| `updated_at` | DateTime | default=datetime.utcnow |

### `department_members`
**Classe:** `DepartmentMember` | **Herda:** `Base` | **Uso:** Routers/Services: 4 | Total refs: 4

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `department_id` | UUID | NOT NULL, FK → departments.id |
| `company_id` | UUID | NOT NULL, FK → company_profiles.id |
| `name` | String(255) | NOT NULL |
| `title` | String(255) | — |
| `email` | String(255) | — |
| `phone` | String(50) | — |
| `linkedin_url` | String(500) | — |
| `avatar_url` | String(500) | — |
| `level` | String(50) | default="outros" |
| `is_active` | Boolean | default=True |
| `order` | Integer | default=0 |
| `created_at` | DateTime | default=datetime.utcnow |
| `updated_at` | DateTime | default=datetime.utcnow |

### `departments`
**Classe:** `Department` | **Herda:** `Base` | **Uso:** Routers/Services: 24 | Total refs: 33

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `company_id` | UUID | NOT NULL, FK → company_profiles.id |
| `name` | String(255) | NOT NULL |
| `code` | String(50) | — |
| `description` | Text | — |
| `parent_id` | UUID | FK → departments.id |
| `manager_name` | String(255) | — |
| `manager_email` | String(255) | — |
| `manager_title` | String(255) | — |
| `manager_phone` | String(50) | — |
| `manager_id` | UUID | — |
| `headcount` | Integer | default=0 |
| `budget_annual` | Float | — |
| `cost_center` | String(100) | — |
| `location` | String(255) | — |
| `is_active` | Boolean | default=True |
| `order` | Integer | default=0 |
| `hiring_priority` | String(50) | default="normal" |
| `created_at` | DateTime | default=datetime.utcnow |
| `updated_at` | DateTime | default=datetime.utcnow |

### `global_search_settings`
**Classe:** `GlobalSearchSettings` | **Herda:** `Base` | **Uso:** Routers/Services: 2 | Total refs: 2

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `company_id` | String(255) | INDEX |
| `default_limit` | Integer | default=50 |
| `search_type` | String(20) | default='fast' |
| `show_emails` | Boolean | default=False |
| `show_phone_numbers` | Boolean | default=False |
| `high_freshness` | Boolean | default=False |
| `auto_expand_global` | Boolean | default=False |
| `confirm_before_search` | Boolean | default=True |
| `global_search_enabled` | Boolean | default=True |
| `created_at` | DateTime | default=datetime.utcnow |
| `updated_at` | DateTime | default=datetime.utcnow |

### `ideal_profiles`
**Classe:** `IdealProfile` | **Herda:** `Base` | **Uso:** Routers/Services: 1 | Total refs: 3

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `company_id` | UUID | NOT NULL, FK → company_profiles.id |
| `department_id` | UUID | FK → departments.id |
| `name` | String(255) | NOT NULL |
| `description` | Text | — |
| `role_type` | String(100) | — |
| `seniority_level` | String(50) | — |
| `technical_requirements` | JSON | default={} |
| `behavioral_requirements` | JSON | default={} |
| `experience_requirements` | JSON | default={} |
| `education_requirements` | JSON | default={} |
| `big_five_ideal` | JSON | default={} |
| `evaluation_weights` | JSON | default={} |
| `mandatory_skills` | String | default=[] |
| `preferred_skills` | String | default=[] |
| `languages` | JSON | default={} |
| `salary_range_min` | Float | — |
| `salary_range_max` | Float | — |
| `culture_fit_criteria` | JSON | default={} |
| `ai_generated` | Boolean | default=False |
| `ai_analysis_date` | DateTime | — |
| `ai_confidence` | Float | — |
| `validated` | Boolean | default=False |
| `validated_by` | String(255) | — |
| `validated_at` | DateTime | — |
| `is_active` | Boolean | default=True |
| `is_template` | Boolean | default=False |
| `usage_count` | Integer | default=0 |
| `success_rate` | Float | — |
| `created_at` | DateTime | default=datetime.utcnow |
| `updated_at` | DateTime | default=datetime.utcnow |
| `created_by` | String(255) | — |

### `technical_questions`
**Classe:** `TechnicalQuestion` | **Herda:** `Base` | **Uso:** Routers/Services: 1 | Total refs: 3

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `title` | String(500) | NOT NULL |
| `description` | Text | — |
| `question_type` | String(50) | NOT NULL |
| `difficulty` | String(20) | default="medium" |
| `estimated_time` | Integer | default=5 |
| `area` | String(100) | NOT NULL |
| `tags` | String | default=[] |
| `options` | JSON | default=[] |
| `correct_answer` | JSON | — |
| `explanation` | Text | — |
| `code_template` | Text | — |
| `code_solution` | Text | — |
| `code_language` | String(50) | — |
| `test_cases` | JSON | default=[] |
| `rubric` | JSON | default={} |
| `ai_generated` | Boolean | default=False |
| `ai_correction_enabled` | Boolean | default=True |
| `is_active` | Boolean | default=True |
| `is_public` | Boolean | default=False |
| `usage_count` | Integer | default=0 |
| `avg_score` | Float | — |
| `avg_time` | Float | — |
| `created_at` | DateTime | default=datetime.utcnow |
| `updated_at` | DateTime | default=datetime.utcnow |
| `created_by` | String(255) | — |

### `technical_test_templates`
**Classe:** `TechnicalTestTemplate` | **Herda:** `Base` | **Uso:** Routers/Services: 1 | Total refs: 3

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `company_id` | UUID | FK → company_profiles.id |
| `name` | String(255) | NOT NULL |
| `description` | Text | — |
| `area` | String(100) | — |
| `role_type` | String(100) | — |
| `seniority_level` | String(50) | — |
| `question_ids` | UUID | default=[] |
| `question_config` | JSON | default={} |
| `total_time` | Integer | default=60 |
| `passing_score` | Float | default=70.0 |
| `instructions` | Text | — |
| `instructions_en` | Text | — |
| `randomize_questions` | Boolean | default=True |
| `randomize_options` | Boolean | default=True |
| `show_score` | Boolean | default=True |
| `proctoring_enabled` | Boolean | default=False |
| `webcam_required` | Boolean | default=False |
| `ai_correction_enabled` | Boolean | default=True |
| `ai_correction_prompt` | Text | — |
| `is_active` | Boolean | default=True |
| `is_public` | Boolean | default=False |
| `usage_count` | Integer | default=0 |
| `avg_score` | Float | — |
| `completion_rate` | Float | — |
| `created_at` | DateTime | default=datetime.utcnow |
| `updated_at` | DateTime | default=datetime.utcnow |
| `created_by` | String(255) | — |

---

## company_benefit
**Arquivo:** `lia-agent-system/libs/models/lia_models/company_benefit.py`

### `company_benefits`
**Classe:** `CompanyBenefit` | **Herda:** `Base` | **Uso:** Routers/Services: 5 | Total refs: 6

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `company_id` | String(255) | NOT NULL, INDEX |
| `name` | String(255) | NOT NULL |
| `category` | String(100) | — |
| `description` | Text | — |
| `icon` | String(100) | — |
| `value` | Float | — |
| `value_type` | String(50) | default="informative" |
| `is_active` | Boolean | default=True |
| `is_highlighted` | Boolean | default=False |
| `order` | Integer | default=0 |
| `created_at` | DateTime | default=datetime.utcnow |
| `updated_at` | DateTime | default=datetime.utcnow |

---

## company_calendar_credentials
**Arquivo:** `lia-agent-system/libs/models/lia_models/company_calendar_credentials.py`

### `company_calendar_credentials`
**Classe:** `CompanyCalendarCredentials` | **Herda:** `Base` | **Uso:** Routers/Services: 3 | Total refs: 4

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `company_id` | UUID | NOT NULL, INDEX |
| `is_active` | Boolean | NOT NULL, default=True |
| `timezone` | String(100) | NOT NULL, default="America/Sao_Paulo" |
| `created_at` | DateTime | default=func.now(, server_default |
| `updated_at` | DateTime | default=func.now(, server_default |
| `Providers` | UUID | PK, default=uuid.uuid4 |
| `provider` | String(20) | NOT NULL |
| `encrypted_credentials` | Text | NOT NULL |

---

## company_culture
**Arquivo:** `lia-agent-system/libs/models/lia_models/company_culture.py`

### `company_culture_profiles`
**Classe:** `CompanyCultureProfile` | **Herda:** `Base` | **Uso:** Routers/Services: 3 | Total refs: 5

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `company_id` | UUID | NOT NULL, FK → company_profiles.id |
| `mission` | Text | — |
| `vision` | Text | — |
| `values` | String | default=[] |
| `evp_bullets` | String | default=[] |
| `culture_description` | Text | — |
| `website_url` | String(500) | NOT NULL |
| `linkedin_url` | String(500) | — |
| `analyzed_pages` | String | default=[] |
| `industry` | String(200) | — |
| `headquarters` | String(300) | — |
| `locations` | String | default=[] |
| `founded_year` | Integer | — |
| `growth_opportunities` | Text | — |
| `team_dynamics` | Text | — |
| `leadership_style` | Text | — |
| `dei_initiatives` | Text | — |
| `sustainability` | Text | — |
| `social_impact` | Text | — |
| `tech_stack` | String | default=[] |
| `engineering_culture` | Text | — |
| `default_languages` | JSON | default=list |
| `openness_score` | Integer | default=50 |
| `conscientiousness_score` | Integer | default=50 |
| `extraversion_score` | Integer | default=50 |
| `agreeableness_score` | Integer | default=50 |
| `stability_score` | Integer | default=50 |
| `source` | String(20) | default="auto" |
| `confidence_score` | Float | default=0.0 |
| `raw_llm_response` | Text | — |
| `last_analysis_at` | DateTime | default=datetime.utcnow |
| `created_at` | DateTime | default=datetime.utcnow |
| `updated_at` | DateTime | default=datetime.utcnow |
| `core_competencies` | String | default=[] |
| `employee_count` | String(50) | — |
| `work_model` | String(100) | — |

### `culture_analysis_jobs`
**Classe:** `CultureAnalysisJob` | **Herda:** `Base` | **Uso:** Routers/Services: 1 | Total refs: 3

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `company_id` | UUID | NOT NULL, FK → company_profiles.id |
| `website_url` | String(500) | NOT NULL |
| `status` | String(50) | default="pending" |
| `progress` | Integer | default=0 |
| `current_step` | String(100) | — |
| `error_message` | Text | — |
| `result_profile_id` | UUID | — |
| `pages_discovered` | Integer | default=0 |
| `pages_scraped` | Integer | default=0 |
| `started_at` | DateTime | — |
| `completed_at` | DateTime | — |
| `created_at` | DateTime | default=datetime.utcnow |

---

## company_hiring_policy
**Arquivo:** `lia-agent-system/libs/models/lia_models/company_hiring_policy.py`

### `company_hiring_policies`
**Classe:** `CompanyHiringPolicy` | **Herda:** `Base` | **Uso:** Routers/Services: 7 | Total refs: 17

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `company_id` | String(255) | NOT NULL, UNIQUE, INDEX |
| `pipeline_rules` | JSON | default=lambda: PIPELINE_RULES_DEFAULTS.copy( |
| `scheduling_rules` | JSON | default=lambda: SCHEDULING_RULES_DEFAULTS.copy( |
| `communication_rules` | JSON | — |
| `screening_rules` | JSON | default=lambda: SCREENING_RULES_DEFAULTS.copy( |
| `automation_rules` | JSON | default=lambda: AUTOMATION_RULES_DEFAULTS.copy( |
| `pipeline_templates` | JSON | default=lambda: [] |
| `learned_patterns` | JSON | default=lambda: [] |
| `answered_questions` | JSON | default=lambda: [] |
| `setup_progress` | Integer | default=0 |
| `setup_completed_at` | DateTime | — |
| `created_by` | String(255) | — |
| `updated_by` | String(255) | — |
| `created_at` | DateTime | INDEX, default=datetime.utcnow |
| `updated_at` | DateTime | default=datetime.utcnow |

---

## company_learning
**Arquivo:** `lia-agent-system/libs/models/lia_models/company_learning.py`

### `agent_feedback`
**Classe:** `AgentFeedback` | **Herda:** `Base` | **Uso:** Routers/Services: 1 | Total refs: 4

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `company_id` | String(255) | NOT NULL, INDEX |
| `job_id` | UUID | INDEX |
| `candidate_id` | UUID | — |
| `agent_name` | String(100) | NOT NULL, INDEX |
| `action_type` | String(100) | NOT NULL |
| `suggested_value` | JSON | — |
| `actual_value` | JSON | — |
| `accepted` | Boolean | NOT NULL, default=False |
| `context` | JSON | — |
| `feedback_reason` | Text | — |
| `processing_time_ms` | Integer | — |
| `created_at` | DateTime | INDEX, default=datetime.utcnow |
| `created_by` | String(255) | — |

### `company_patterns`
**Classe:** `CompanyPattern` | **Herda:** `Base` | **Uso:** Routers/Services: 3 | Total refs: 5

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `company_id` | String(255) | NOT NULL, INDEX |
| `pattern_type` | String(100) | NOT NULL, INDEX |
| `pattern_key` | String(255) | NOT NULL |
| `pattern_value` | JSON | NOT NULL |
| `sample_size` | Integer | default=0 |
| `confidence` | String(20) | default="low" |
| `last_calculated_at` | DateTime | default=datetime.utcnow |
| `expires_at` | DateTime | — |
| `created_at` | DateTime | default=datetime.utcnow |
| `updated_at` | DateTime | default=datetime.utcnow |
| `Examples` | UUID | PK, default=uuid.uuid4 |

### `company_responsibilities`
**Classe:** `CompanyResponsibility` | **Herda:** `Base` | **Uso:** Routers/Services: 4 | Total refs: 7

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `company_id` | String(255) | NOT NULL, INDEX |
| `description` | Text | NOT NULL |
| `category` | String(100) | — |
| `times_confirmed` | Integer | default=1 |
| `times_rejected` | Integer | default=0 |
| `times_used_in_jobs` | Integer | default=0 |
| `times_in_successful_hires` | Integer | default=0 |
| `source` | String(50) | default=LearningSource.WIZARD_CONFIRMED.value |
| `is_promoted` | Boolean | default=False |
| `promotion_threshold` | Integer | default=3 |
| `roles_associated` | JSON | default=list |
| `seniority_levels` | JSON | default=list |
| `confidence_score` | Float | default=0.5 |
| `last_used_at` | DateTime | — |
| `created_at` | DateTime | default=datetime.utcnow |
| `created_by` | String(255) | — |
| `description_hash` | String(64) | NOT NULL, INDEX |

### `company_skills`
**Classe:** `CompanySkill` | **Herda:** `Base` | **Uso:** Routers/Services: 9 | Total refs: 12

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `company_id` | String(255) | NOT NULL, INDEX |
| `skill_name` | String(255) | NOT NULL, INDEX |
| `skill_type` | String(50) | NOT NULL, default="technical" |
| `category` | String(100) | — |
| `times_confirmed` | Integer | default=1 |
| `times_rejected` | Integer | default=0 |
| `times_used_in_jobs` | Integer | default=0 |
| `times_in_successful_hires` | Integer | default=0 |
| `source` | String(50) | default=LearningSource.WIZARD_CONFIRMED.value |
| `is_promoted` | Boolean | default=False |
| `promotion_threshold` | Integer | default=3 |
| `roles_associated` | JSON | default=list |
| `seniority_levels` | JSON | default=list |
| `confidence_score` | Float | default=0.5 |
| `last_used_at` | DateTime | — |
| `created_at` | DateTime | default=datetime.utcnow |
| `created_by` | String(255) | — |

### `feature_flags`
**Classe:** `FeatureFlag` | **Herda:** `Base` | **Uso:** Routers/Services: 0 | Total refs: 3

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `flag_key` | String(100) | NOT NULL, INDEX |
| `company_id` | String(255) | INDEX |
| `is_enabled` | Boolean | default=False |
| `rollout_percentage` | Integer | default=100 |
| `description` | Text | — |
| `category` | String(50) | default="general" |
| `flag_metadata` | JSON | default=dict |
| `expires_at` | DateTime | — |
| `created_at` | DateTime | default=datetime.utcnow |
| `updated_at` | DateTime | default=datetime.utcnow |
| `created_by` | String(255) | — |

### `stage_feedback`
**Classe:** `StageFeedback` | **Herda:** `Base` | **Uso:** Routers/Services: 1 | Total refs: 1

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `company_id` | String(255) | NOT NULL, INDEX |
| `job_id` | UUID | INDEX |
| `stage_number` | Integer | NOT NULL, INDEX |
| `stage_name` | String(100) | — |
| `field_name` | String(100) | NOT NULL, INDEX |
| `suggested_value` | JSON | — |
| `accepted_value` | JSON | — |
| `was_accepted` | Boolean | default=True |
| `was_modified` | Boolean | default=False |
| `role` | String(255) | INDEX |
| `seniority` | String(50) | — |
| `confidence_before` | Float | — |
| `created_at` | DateTime | default=datetime.utcnow |
| `created_by` | String(255) | — |

---

## compensation_policy
**Arquivo:** `lia-agent-system/libs/models/lia_models/compensation_policy.py`

### `compensation_policies`
**Classe:** `CompensationPolicy` | **Herda:** `Base` | **Uso:** Routers/Services: 1 | Total refs: 3

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `company_id` | UUID | NOT NULL, FK → company_profiles.id |
| `name` | String(255) | NOT NULL |
| `department` | String(255) | — |
| `role_pattern` | String(255) | — |
| `seniority_level` | String(100) | — |
| `salary_min` | Float | — |
| `salary_max` | Float | — |
| `salary_target` | Float | — |
| `bonus_enabled` | Boolean | default=False |
| `bonus_type` | String(100) | — |
| `bonus_min_pct` | Float | — |
| `bonus_target_pct` | Float | — |
| `bonus_max_pct` | Float | — |
| `bonus_criteria` | JSON | default={} |
| `variable_compensation` | JSON | default={} |
| `total_comp_annual_min` | Float | — |
| `total_comp_annual_max` | Float | — |
| `is_active` | Boolean | default=True |
| `effective_from` | DateTime | — |
| `effective_until` | DateTime | — |
| `source` | String(255) | — |
| `created_at` | DateTime | default=datetime.utcnow |
| `updated_at` | DateTime | default=datetime.utcnow |
| `created_by` | String(255) | — |

---

## conversation
**Arquivo:** `lia-agent-system/libs/models/lia_models/conversation.py`

### `conversation_summaries`
**Classe:** `ConversationSummary` | **Herda:** `Base` | **Uso:** Routers/Services: 1 | Total refs: 3

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `conversation_id` | UUID | NOT NULL, INDEX, FK → conversations.id |
| `summary` | Text | NOT NULL |
| `message_count` | Integer | default=0 |
| `messages_start_id` | UUID | — |
| `messages_end_id` | UUID | — |
| `key_entities` | JSON | default=dict |
| `user_preferences` | JSON | default=dict |
| `created_at` | DateTime | default=datetime.utcnow |

### `conversations`
**Classe:** `Conversation` | **Herda:** `Base` | **Uso:** Routers/Services: 18 | Total refs: 22

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `user_id` | String(255) | NOT NULL, INDEX |
| `user_role` | String(50) | default="recruiter" |
| `session_id` | String(255) | INDEX |
| `context_type` | String(50) | INDEX, default="general" |
| `context_id` | String(255) | INDEX |
| `title` | String(500) | — |
| `summary` | Text | — |
| `intent` | String(100) | — |
| `workflow_type` | String(100) | — |
| `workflow_step` | Integer | default=0 |
| `workflow_data` | JSON | default=dict |
| `status` | String(50) | default="active" |
| `is_active` | Boolean | INDEX, default=True |
| `is_archived` | Boolean | default=False |
| `message_count` | Integer | default=0 |
| `last_summary_at_count` | Integer | default=0 |
| `conversation_metadata` | JSON | default=dict |
| `created_at` | DateTime | INDEX, default=datetime.utcnow |
| `updated_at` | DateTime | default=datetime.utcnow |
| `completed_at` | DateTime | — |

### `messages`
**Classe:** `Message` | **Herda:** `Base` | **Uso:** Routers/Services: 32 | Total refs: 45

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `conversation_id` | UUID | NOT NULL, INDEX, FK → conversations.id |
| `role` | String(20) | NOT NULL |
| `content` | Text | NOT NULL |
| `intent` | String(100) | — |
| `prompt_version` | String(16) | — |
| `tool_calls` | JSON | — |
| `message_metadata` | JSON | default=dict |
| `created_at` | DateTime | INDEX, default=datetime.utcnow |

---

## custom_agent
**Arquivo:** `lia-agent-system/libs/models/lia_models/custom_agent.py`

### `agent_installations`
**Classe:** `AgentInstallation` | **Herda:** `Base` | **Uso:** Routers/Services: 2 | Total refs: 3

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `installer_company_id` | String(64) | NOT NULL, INDEX |
| `installed_by` | String(64) | NOT NULL |
| `status` | String(20) | NOT NULL, default="active" |
| `version_at_install` | Integer | NOT NULL, default=1 |
| `total_executions` | Integer | default=0 |
| `total_credits_consumed` | Integer | default=0 |
| `installed_at` | DateTime | default=datetime.utcnow |
| `uninstalled_at` | DateTime | — |
| `source_agent_id` | UUID | NOT NULL, FK → custom_agents.id |
| `listing_id` | UUID | FK → agent_marketplace_listings.id |
| `installed_agent_id` | UUID | FK → custom_agents.id |

### `agent_marketplace_listings`
**Classe:** `AgentMarketplaceListing` | **Herda:** `Base` | **Uso:** Routers/Services: 2 | Total refs: 3

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `publisher_company_id` | String(64) | NOT NULL, INDEX |
| `title` | String(256) | NOT NULL |
| `short_description` | String(512) | — |
| `long_description` | Text | — |
| `category` | String(64) | NOT NULL, default="general" |
| `tags` | String | NOT NULL, default=list |
| `icon_url` | String(512) | — |
| `review_notes` | Text | — |
| `reviewed_by` | String(64) | — |
| `reviewed_at` | DateTime | — |
| `credits_per_execution` | Integer | NOT NULL, default=1 |
| `is_free` | Boolean | default=False |
| `install_count` | Integer | default=0 |
| `avg_rating` | Float | default=0.0 |
| `total_ratings` | Integer | default=0 |
| `published_at` | DateTime | — |
| `created_at` | DateTime | default=datetime.utcnow |
| `updated_at` | DateTime | default=datetime.utcnow |
| `agent_id` | UUID | NOT NULL, UNIQUE, FK → custom_agents.id |
| `status` | String(20) | NOT NULL |

### `custom_agents`
**Classe:** `CustomAgent` | **Herda:** `Base` | **Uso:** Routers/Services: 10 | Total refs: 13

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `company_id` | String(64) | NOT NULL, INDEX |
| `created_by` | String(64) | NOT NULL |
| `name` | String(256) | NOT NULL |
| `role` | String(256) | NOT NULL |
| `description` | Text | — |
| `system_prompt` | Text | NOT NULL |
| `allowed_tools` | String | NOT NULL, default=list |
| `domain` | String(64) | NOT NULL, default="general" |
| `icon` | String(10) | default="🤖" |
| `status` | String(20) | NOT NULL, default=CustomAgentStatus.DRAFT.value |
| `version` | Integer | NOT NULL, default=1 |
| `config` | JSON | NOT NULL, default=dict |
| `max_steps` | Integer | NOT NULL, default=8 |
| `temperature` | Float | NOT NULL, default=0.7 |
| `model_override` | String(64) | — |
| `enable_memory` | Boolean | NOT NULL, default=True, server_default |
| `context_level` | String(20) | NOT NULL, default="full", server_default |
| `excluded_tools` | String | NOT NULL, default=list, server_default |
| `total_executions` | Integer | default=0 |
| `avg_confidence` | Float | default=0.0 |
| `last_executed_at` | DateTime | — |
| `is_marketplace_published` | Boolean | default=False |
| `created_at` | DateTime | default=datetime.utcnow |
| `updated_at` | DateTime | default=datetime.utcnow |

---

## data_request
**Arquivo:** `lia-agent-system/libs/models/lia_models/data_request.py`

### `data_request_configs`
**Classe:** `DataRequestConfig` | **Herda:** `Base` | **Uso:** Routers/Services: 3 | Total refs: 5

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `company_id` | UUID | NOT NULL, UNIQUE, INDEX |
| `default_expiration_days` | Integer | default=7 |
| `require_otp` | Boolean | default=True |
| `otp_expiration_minutes` | Integer | default=10 |
| `max_otp_attempts` | Integer | default=3 |
| `send_email_notification` | Boolean | default=True |
| `send_whatsapp_notification` | Boolean | default=True |
| `auto_reminder_enabled` | Boolean | default=True |
| `reminder_days` | Integer | default=[2 |
| `max_reminders` | Integer | default=2 |
| `portal_logo_url` | String(500) | — |
| `portal_primary_color` | String(7) | default="#000000" |
| `portal_welcome_message` | Text | — |
| `portal_thank_you_message` | Text | — |
| `privacy_policy_url` | String(500) | — |
| `terms_url` | String(500) | — |
| `created_at` | DateTime | default=datetime.utcnow |
| `updated_at` | DateTime | default=datetime.utcnow |
| `collection_mode` | String(50) | default="portal_only" |

### `data_request_fields`
**Classe:** `DataRequestField` | **Herda:** `Base` | **Uso:** Routers/Services: 1 | Total refs: 3

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `company_id` | UUID | NOT NULL, INDEX |
| `name` | String(100) | NOT NULL |
| `label` | String(255) | NOT NULL |
| `label_en` | String(255) | — |
| `description` | Text | — |
| `field_type` | Enum(DataFieldType) | NOT NULL |
| `is_required` | Boolean | default=True |
| `validation_rules` | JSON | default=dict |
| `options` | JSON | default=list |
| `placeholder` | String(255) | — |
| `help_text` | String(500) | — |
| `max_file_size_mb` | Integer | default=10 |
| `allowed_file_types` | String | default=list |
| `order` | Integer | default=0 |
| `is_active` | Boolean | default=True |
| `created_at` | DateTime | default=datetime.utcnow |
| `updated_at` | DateTime | default=datetime.utcnow |

### `data_request_responses`
**Classe:** `DataRequestResponse` | **Herda:** `Base` | **Uso:** Routers/Services: 3 | Total refs: 5

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `data_request_id` | UUID | NOT NULL, INDEX, FK → data_requests.id |
| `field_name` | String(100) | NOT NULL, INDEX |
| `field_type` | Enum(DataFieldType) | NOT NULL |
| `value` | Text | — |
| `file_url` | String(1000) | — |
| `file_name` | String(255) | — |
| `file_size_bytes` | Integer | — |
| `file_mime_type` | String(100) | — |
| `is_valid` | Boolean | default=True |
| `validation_errors` | JSON | default=list |
| `submitted_at` | DateTime | default=datetime.utcnow |
| `updated_at` | DateTime | default=datetime.utcnow |
| `ip_address` | String(45) | — |
| `user_agent` | String(500) | — |

### `data_request_templates`
**Classe:** `DataRequestTemplate` | **Herda:** `Base` | **Uso:** Routers/Services: 2 | Total refs: 4

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `company_id` | UUID | NOT NULL, INDEX |
| `name` | String(255) | NOT NULL |
| `description` | Text | — |
| `trigger_stage` | String(100) | INDEX |
| `trigger_type` | Enum(TriggerType) | default=TriggerType.MANUAL |
| `is_blocking` | Boolean | default=False |
| `expiration_days` | Integer | default=7 |
| `fields` | JSON | default=list |
| `is_active` | Boolean | default=True |
| `is_default` | Boolean | default=False |
| `created_at` | DateTime | default=datetime.utcnow |
| `updated_at` | DateTime | default=datetime.utcnow |
| `created_by` | UUID | — |

### `data_requests`
**Classe:** `DataRequest` | **Herda:** `Base` | **Uso:** Routers/Services: 6 | Total refs: 8

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `candidate_id` | UUID | NOT NULL, INDEX, FK → candidates.id |
| `vacancy_id` | UUID | INDEX, FK → job_vacancies.id |
| `company_id` | UUID | NOT NULL, INDEX |
| `template_id` | UUID | FK → data_request_templates.id |
| `token` | String(64) | NOT NULL, UNIQUE, INDEX |
| `status` | Enum(DataRequestStatus) | INDEX, default=DataRequestStatus.PENDING |
| `fields_requested` | JSON | default=list |
| `fields_completed` | JSON | default=list |
| `trigger_type` | Enum(TriggerType) | default=TriggerType.MANUAL |
| `trigger_stage` | String(100) | — |
| `is_blocking` | Boolean | default=False |
| `expires_at` | DateTime | NOT NULL |
| `otp_code` | String(6) | — |
| `otp_expires_at` | DateTime | — |
| `otp_verified` | Boolean | default=False |
| `otp_attempts` | Integer | default=0 |
| `sent_via_email` | Boolean | default=False |
| `sent_via_whatsapp` | Boolean | default=False |
| `email_sent_at` | DateTime | — |
| `whatsapp_sent_at` | DateTime | — |
| `reminder_count` | Integer | default=0 |
| `last_reminder_at` | DateTime | — |
| `collection_method` | String(20) | — |
| `whatsapp_conversation_state` | JSON | default=dict |
| `first_accessed_at` | DateTime | — |
| `last_accessed_at` | DateTime | — |
| `completed_at` | DateTime | — |
| `created_at` | DateTime | default=datetime.utcnow |
| `updated_at` | DateTime | default=datetime.utcnow |
| `created_by` | UUID | — |

### `vacancy_data_request_configs`
**Classe:** `VacancyDataRequestConfig` | **Herda:** `Base` | **Uso:** Routers/Services: 4 | Total refs: 6

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `vacancy_id` | UUID | NOT NULL, UNIQUE, INDEX, FK → job_vacancies.id |
| `use_company_defaults` | Boolean | default=True |
| `custom_template_id` | UUID | FK → data_request_templates.id |
| `stage_configs` | JSON | default=dict |
| `created_at` | DateTime | default=datetime.utcnow |
| `updated_at` | DateTime | default=datetime.utcnow |

---

## default_templates
**Arquivo:** `lia-agent-system/libs/models/lia_models/default_templates.py`

### `default_templates`
**Classe:** `DefaultTemplate` | **Herda:** `Base` | **Uso:** Routers/Services: 2 | Total refs: 4

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `name` | String(255) | NOT NULL, INDEX |
| `category` | String(20) | NOT NULL, INDEX, default="email" |
| `subject` | String(500) | — |
| `body` | Text | NOT NULL |
| `variables` | JSON | default=list |
| `status` | String(20) | NOT NULL, INDEX, default="active" |
| `client_usage_count` | Integer | default=0 |
| `created_by` | String(255) | — |
| `created_at` | DateTime | INDEX, default=datetime.utcnow |
| `updated_at` | DateTime | default=datetime.utcnow |

---

## digital_twin
**Arquivo:** `lia-agent-system/libs/models/lia_models/digital_twin.py`

### `digital_twins`
**Classe:** `DigitalTwin` | **Herda:** `Base` | **Uso:** Routers/Services: 5 | Total refs: 7

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `company_id` | String(64) | NOT NULL, INDEX |
| `twin_name` | String(256) | NOT NULL |
| `sme_user_id` | String(64) | — |
| `specialties` | String | default=list |
| `description` | Text | — |
| `decision_count` | Integer | default=0 |
| `accuracy_pct` | Float | — |
| `is_active` | Boolean | default=True |
| `twin_embedding` | Vector | — |
| `created_at` | DateTime | default=datetime.utcnow |
| `updated_at` | DateTime | default=datetime.utcnow |

### `twin_decisions`
**Classe:** `TwinDecision` | **Herda:** `Base` | **Uso:** Routers/Services: 2 | Total refs: 3

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `twin_id` | UUID | NOT NULL, FK → digital_twins.id |
| `reasoning` | Text | NOT NULL |
| `candidate_snapshot` | JSON | — |
| `job_snapshot` | JSON | — |
| `embedding` | Vector | — |
| `source` | String(32) | default="ats_history" |
| `created_at` | DateTime | default=datetime.utcnow |
| `decision` | String(16) | NOT NULL |

---

## email_template
**Arquivo:** `lia-agent-system/libs/models/lia_models/email_template.py`

### `email_logs`
**Classe:** `EmailLog` | **Herda:** `Base` | **Uso:** Routers/Services: 5 | Total refs: 8

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `template_id` | UUID | INDEX, FK → email_templates.id |
| `candidate_id` | String(255) | INDEX |
| `recipient_email` | String(255) | NOT NULL, INDEX |
| `subject` | String(500) | NOT NULL |
| `body_html` | Text | — |
| `body_text` | Text | — |
| `status` | String(50) | NOT NULL, INDEX, default="pending" |
| `sent_at` | DateTime | — |
| `error_message` | Text | — |
| `variables_used` | JSON | default=dict |
| `created_at` | DateTime | INDEX, default=datetime.utcnow |
| `created_by` | String(255) | INDEX |

### `email_templates`
**Classe:** `EmailTemplate` | **Herda:** `Base` | **Uso:** Routers/Services: 12 | Total refs: 16

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `name` | String(255) | NOT NULL, INDEX |
| `subject` | String(500) | — |
| `body_html` | Text | NOT NULL |
| `body_text` | Text | — |
| `category` | String(50) | INDEX |
| `channel` | String(20) | NOT NULL, INDEX, default="email" |
| `situation` | String(50) | INDEX |
| `trigger_type` | String(20) | default="manual" |
| `used_in` | JSON | default=list |
| `priority` | String(10) | default="medium" |
| `variables` | JSON | default=list |
| `is_active` | Boolean | INDEX, default=True |
| `company_id` | String(255) | INDEX |
| `is_system_template` | Boolean | INDEX, default=False |
| `origin_template_id` | UUID | INDEX |
| `version` | Integer | default=1 |
| `created_by` | String(255) | — |
| `created_at` | DateTime | INDEX, default=datetime.utcnow |
| `updated_at` | DateTime | default=datetime.utcnow |
| `visibility` | UUID | NOT NULL, INDEX, default="recruiter" |

---

## email_tracking
**Arquivo:** `lia-agent-system/libs/models/lia_models/email_tracking.py`

### `email_tracking_events`
**Classe:** `EmailTrackingEvent` | **Herda:** `Base` | **Uso:** Routers/Services: 2 | Total refs: 4

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `notification_id` | String(255) | NOT NULL, INDEX |
| `company_id` | String(255) | NOT NULL, INDEX |
| `token` | String(255) | NOT NULL, UNIQUE, INDEX |
| `user_agent` | Text | — |
| `link_url` | Text | — |
| `occurred_at` | DateTime | default=func.now(, server_default |
| `metadata_` | JSON | — |
| `event_type` | String(50) | NOT NULL |

---

## evaluation_criteria
**Arquivo:** `lia-agent-system/libs/models/lia_models/evaluation_criteria.py`

### `evaluation_criteria`
**Classe:** `EvaluationCriteria` | **Herda:** `Base` | **Uso:** Routers/Services: 2 | Total refs: 4

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `name` | String(300) | NOT NULL, INDEX |
| `category` | String(50) | NOT NULL, INDEX |
| `subcategory` | String(100) | — |
| `positive_evidences` | JSON | NOT NULL, default=list |
| `negative_evidences` | JSON | NOT NULL, default=list |
| `evaluation_guidelines` | Text | — |
| `effectiveness_score` | Float | NOT NULL, default=0.5 |
| `usage_count` | Integer | NOT NULL, default=0 |
| `feedback_count` | Integer | NOT NULL, default=0 |
| `source` | String(50) | NOT NULL, default="seed" |
| `is_active` | Boolean | NOT NULL, default=True |
| `created_at` | DateTime | default=datetime.utcnow |
| `updated_at` | DateTime | default=datetime.utcnow |

---

## event_store
**Arquivo:** `lia-agent-system/libs/models/lia_models/event_store.py`

### `domain_events`
**Classe:** `DomainEvent` | **Herda:** `Base` | **Uso:** Routers/Services: 1 | Total refs: 3

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `event_data` | JSON | NOT NULL, default=dict |
| `company_id` | String(255) | NOT NULL |
| `created_at` | DateTime | NOT NULL, default=datetime.utcnow |
| `sequence_number` | Integer | NOT NULL, default=0 |
| `aggregate_type` | UUID | NOT NULL, default=dict |
| `created_by` | String(255) | NOT NULL, default=datetime.utcnow |

---

## execution_log_store
**Arquivo:** `lia-agent-system/libs/agents-core/lia_agents_core/execution_log_store.py`

### `agent_execution_records`
**Classe:** `AgentExecutionRecord` | **Herda:** `Base` | **Uso:** Routers/Services: 1 | Total refs: 1

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `session_id` | String(255) | NOT NULL, INDEX |
| `company_id` | String(255) | NOT NULL, INDEX |
| `user_id` | String(255) | NOT NULL |
| `domain` | String(100) | NOT NULL |
| `agent_class` | String(255) | NOT NULL |
| `user_message` | Text | — |
| `agent_response` | Text | — |
| `total_duration_ms` | Float | default=0 |
| `total_iterations` | Integer | default=0 |
| `tools_called` | JSON | default=list |
| `tools_succeeded` | Integer | default=0 |
| `tools_failed` | Integer | default=0 |
| `final_confidence` | Float | default=0 |
| `reasoning_chain` | JSON | default=list |
| `stage_before` | String(100) | — |
| `stage_after` | String(100) | — |
| `stage_transitioned` | Boolean | default=False |
| `model_provider` | String(100) | default="claude" |
| `created_at` | DateTime | default=lambda: datetime.now(timezone.utc |
| `metadata_` | JSON | — |

---

## external_api_consumption
**Arquivo:** `lia-agent-system/libs/models/lia_models/external_api_consumption.py`

### `external_api_consumption`
**Classe:** `ExternalApiConsumption` | **Herda:** `Base` | **Uso:** Routers/Services: 2 | Total refs: 3

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `company_id` | String(100) | NOT NULL, INDEX |
| `user_id` | String(100) | INDEX |
| `candidate_id` | UUID | INDEX |
| `linkedin_url` | String(500) | — |
| `provider` | String(30) | NOT NULL, INDEX |
| `operation` | String(50) | NOT NULL, INDEX |
| `pipeline_id` | UUID | — |
| `search_session_id` | String(100) | — |
| `actor_id` | String(200) | — |
| `tokens_input` | Integer | — |
| `tokens_output` | Integer | — |
| `model_name` | String(100) | — |
| `credits_consumed` | Integer | NOT NULL, default=0 |
| `cost_usd` | Float | NOT NULL, default=0.0 |
| `cost_brl` | Float | NOT NULL, default=0.0 |
| `exchange_rate` | Float | NOT NULL, default=5.50 |
| `success` | Boolean | NOT NULL, default=False |
| `result_status` | String(30) | — |
| `error_message` | String(500) | — |
| `response_time_ms` | Integer | default=0 |
| `created_at` | DateTime | INDEX, default=func.now(, server_default |

---

## fairness_audit
**Arquivo:** `lia-agent-system/libs/models/lia_models/fairness_audit.py`

### `fairness_audit_log`
**Classe:** `FairnessAuditLog` | **Herda:** `Base` | **Uso:** Routers/Services: 2 | Total refs: 4

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `company_id` | UUID | INDEX |
| `recruiter_id` | UUID | — |
| `job_id` | UUID | — |
| `candidate_id` | UUID | — |
| `query_hash` | String(64) | NOT NULL |
| `category` | String(50) | INDEX |
| `blocked_terms` | JSON | — |
| `confidence` | Float | — |
| `is_blocked` | Boolean | NOT NULL, INDEX, default=False |
| `context` | String(100) | — |
| `soft_warnings` | JSON | — |
| `created_at` | DateTime | NOT NULL, INDEX, default=text("now(, server_default |

---

## feedback
**Arquivo:** `lia-agent-system/libs/models/lia_models/feedback.py`

### `interaction_feedback`
**Classe:** `InteractionFeedback` | **Herda:** `Base` | **Uso:** Routers/Services: 2 | Total refs: 4

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid4 |
| `session_id` | String(100) | NOT NULL, INDEX |
| `company_id` | UUID | NOT NULL, INDEX |
| `user_id` | String(100) | NOT NULL, INDEX |
| `message_id` | String(100) | — |
| `user_message` | Text | — |
| `lia_response` | Text | — |
| `intent` | String(50) | — |
| `stage` | String(50) | — |
| `rating` | Integer | — |
| `thumbs` | String(10) | — |
| `correction` | Text | — |
| `feedback_text` | Text | — |
| `feedback_category` | String(50) | — |
| `response_time_ms` | Integer | — |
| `tools_used` | JSON | default=list |
| `confidence_score` | Float | — |
| `processed` | Boolean | default=False |
| `incorporated_to_rag` | Boolean | default=False |
| `created_at` | DateTime | INDEX, default=datetime.utcnow |

### `learning_patterns`
**Classe:** `LearningPattern` | **Herda:** `Base` | **Uso:** Routers/Services: 1 | Total refs: 5

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid4 |
| `company_id` | UUID | NOT NULL, INDEX |
| `pattern_type` | String(50) | NOT NULL, INDEX |
| `pattern_key` | String(255) | NOT NULL, INDEX |
| `trigger_phrases` | JSON | default=list |
| `expected_response_style` | Text | — |
| `preferred_tools` | JSON | default=list |
| `example_good_responses` | JSON | default=list |
| `example_bad_responses` | JSON | default=list |
| `pattern_value` | JSON | — |
| `positive_feedback_count` | Integer | default=0 |
| `negative_feedback_count` | Integer | default=0 |
| `success_rate` | Float | default=0.0 |
| `sample_size` | Integer | default=1 |
| `acceptance_rate` | Float | default=1.0 |
| `is_active` | Boolean | default=True |
| `confidence` | Float | default=0.5 |
| `confidence_score` | Float | default=0.5 |
| `role_filter` | String(255) | INDEX |
| `seniority_filter` | String(100) | — |
| `department_filter` | String(100) | — |
| `location_filter` | String(255) | — |
| `expires_at` | DateTime | — |
| `last_applied_at` | DateTime | — |
| `last_confirmed_at` | DateTime | — |
| `created_at` | DateTime | INDEX, default=datetime.utcnow |
| `updated_at` | DateTime | default=datetime.utcnow |

---

## feedback_learning
**Arquivo:** `lia-agent-system/libs/models/lia_models/feedback_learning.py`

### `job_outcomes`
**Classe:** `JobOutcome` | **Herda:** `Base` | **Uso:** Routers/Services: 14 | Total refs: 17

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `company_id` | String(255) | NOT NULL, INDEX |
| `job_id` | UUID | NOT NULL, UNIQUE, INDEX |
| `time_to_fill_days` | Integer | — |
| `salary_initial_min` | Float | — |
| `salary_initial_max` | Float | — |
| `salary_final` | Float | — |
| `candidate_count_total` | Integer | — |
| `candidate_count_screened` | Integer | — |
| `candidate_count_interviewed` | Integer | — |
| `candidate_count_offered` | Integer | — |
| `satisfaction_score` | Float | — |
| `role` | String(255) | INDEX |
| `seniority` | String(50) | INDEX |
| `department` | String(100) | — |
| `location` | String(255) | — |
| `work_model` | String(50) | — |
| `skills_used` | JSON | default=list |
| `notes` | Text | — |
| `closed_at` | DateTime | — |
| `created_at` | DateTime | INDEX, default=datetime.utcnow |
| `created_by` | String(255) | — |
| `Tracks` | UUID | PK, default=uuid.uuid4 |
| `outcome` | Enum(JobOutcomeType, name="job_outcome_type") | NOT NULL, INDEX |

### `suggestion_feedback`
**Classe:** `SuggestionFeedback` | **Herda:** `Base` | **Uso:** Routers/Services: 3 | Total refs: 6

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `company_id` | String(255) | NOT NULL, INDEX |
| `field_name` | String(100) | NOT NULL, INDEX |
| `suggested_value` | JSON | — |
| `actual_value` | JSON | — |
| `created_at` | DateTime | INDEX, default=datetime.utcnow |
| `created_by` | String(255) | — |
| `Example` | UUID | PK, default=uuid.uuid4 |
| `accepted` | Integer | NOT NULL, INDEX, default=0 |

### `wizard_feedback`
**Classe:** `WizardFeedback` | **Herda:** `Base` | **Uso:** Routers/Services: 4 | Total refs: 7

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `company_id` | String(255) | NOT NULL, INDEX |
| `job_id` | UUID | NOT NULL, INDEX |
| `field_corrected` | String(100) | NOT NULL, INDEX |
| `original_value` | JSON | — |
| `corrected_value` | JSON | — |
| `stage` | String(100) | — |
| `role` | String(255) | INDEX |
| `seniority` | String(50) | INDEX |
| `department` | String(100) | — |
| `location` | String(255) | — |
| `correction_reason` | Text | — |
| `created_at` | DateTime | INDEX, default=datetime.utcnow |
| `created_by` | String(255) | — |
| `Example` | UUID | PK, default=uuid.uuid4 |

---

## global_policies
**Arquivo:** `lia-agent-system/libs/models/lia_models/global_policies.py`

### `platform_global_policies`
**Classe:** `PlatformPolicy` | **Herda:** `Base` | **Uso:** Routers/Services: 1 | Total refs: 2

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `name` | String(100) | NOT NULL, UNIQUE, INDEX |
| `description` | Text | — |
| `category` | String(50) | NOT NULL, INDEX |
| `value_type` | String(20) | NOT NULL |
| `current_value` | String(500) | NOT NULL |
| `unit` | String(50) | — |
| `min_value` | Numeric(20, 4) | — |
| `max_value` | Numeric(20, 4) | — |
| `options` | JSON | — |
| `is_active` | Boolean | INDEX, default=True |
| `updated_at` | DateTime | default=func.now(, server_default |
| `updated_by` | UUID | — |
| `created_at` | DateTime | default=func.now(, server_default |

---

## global_policy
**Arquivo:** `lia-agent-system/libs/models/lia_models/global_policy.py`

### `global_policies`
**Classe:** `GlobalPolicy` | **Herda:** `Base` | **Uso:** Routers/Services: 2 | Total refs: 3

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `company_id` | String(255) | INDEX |
| `name` | String(255) | NOT NULL |
| `description` | Text | — |
| `policy_type` | String(50) | NOT NULL, INDEX |
| `value` | JSON | NOT NULL, default=dict |
| `scope` | String(20) | NOT NULL, INDEX, default=PolicyScope.COMPANY.value |
| `is_active` | Boolean | INDEX, default=True |
| `created_by` | String(255) | — |
| `updated_by` | String(255) | — |
| `created_at` | DateTime | INDEX, default=datetime.utcnow |
| `updated_at` | DateTime | default=datetime.utcnow |

---

## goal
**Arquivo:** `lia-agent-system/libs/models/lia_models/goal.py`

### `goal_templates`
**Classe:** `GoalTemplate` | **Herda:** `Base` | **Uso:** Routers/Services: 1 | Total refs: 2

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `company_id` | UUID | FK → company_profiles.id |
| `name` | String(255) | NOT NULL |
| `description` | Text | — |
| `category` | String(50) | NOT NULL, default="recruitment" |
| `default_target` | Float | NOT NULL, default=0 |
| `unit` | String(100) | — |
| `period` | String(50) | NOT NULL, default="monthly" |
| `is_active` | Boolean | default=True |
| `is_system` | Boolean | default=False |
| `template_metadata` | JSON | default={} |
| `created_at` | DateTime | default=datetime.utcnow |
| `updated_at` | DateTime | default=datetime.utcnow |

### `goals`
**Classe:** `Goal` | **Herda:** `Base` | **Uso:** Routers/Services: 2 | Total refs: 3

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `user_id` | String(255) | NOT NULL, INDEX |
| `company_id` | UUID | FK → company_profiles.id |
| `template_id` | String(255) | — |
| `name` | String(255) | NOT NULL |
| `description` | Text | — |
| `target` | Float | NOT NULL, default=0 |
| `current` | Float | NOT NULL, default=0 |
| `unit` | String(100) | — |
| `period` | String(50) | NOT NULL, default="monthly" |
| `category` | String(50) | NOT NULL, default="recruitment" |
| `status` | String(50) | NOT NULL, default="pending" |
| `start_date` | DateTime | — |
| `end_date` | DateTime | — |
| `progress` | Float | NOT NULL, default=0 |
| `is_custom` | Boolean | default=False |
| `is_active` | Boolean | default=True |
| `goal_metadata` | JSON | default={} |
| `created_at` | DateTime | default=datetime.utcnow |
| `updated_at` | DateTime | default=datetime.utcnow |

---

## graph_session
**Arquivo:** `lia-agent-system/libs/models/lia_models/graph_session.py`

### `graph_sessions`
**Classe:** `GraphSession` | **Herda:** `Base` | **Uso:** Routers/Services: 1 | Total refs: 3

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid4 |
| `session_id` | String(100) | NOT NULL, UNIQUE, INDEX |
| `company_id` | UUID | NOT NULL, INDEX |
| `user_id` | String(100) | NOT NULL, INDEX |
| `current_stage` | String(50) | default="initial" |
| `job_draft` | JSON | default=dict |
| `confidence_scores` | JSON | default=dict |
| `messages` | JSON | default=list |
| `reasoning_steps` | JSON | default=list |
| `tool_calls` | JSON | default=list |
| `tool_results` | JSON | default=list |
| `extracted_fields` | JSON | default=dict |
| `last_response` | String | — |
| `last_intent` | String(50) | — |
| `error` | String | — |
| `is_complete` | Boolean | default=False |
| `is_active` | Boolean | default=True |
| `execution_count` | String | default="0" |
| `created_at` | DateTime | default=datetime.utcnow |
| `updated_at` | DateTime | default=datetime.utcnow |
| `last_activity_at` | DateTime | default=datetime.utcnow |

---

## guardrail
**Arquivo:** `lia-agent-system/libs/models/lia_models/guardrail.py`

### `guardrails`
**Classe:** `Guardrail` | **Herda:** `Base` | **Uso:** Routers/Services: 2 | Total refs: 7

| Campo | Tipo | Restrições |
|-------|------|------------|
| `rule` | Text | NOT NULL |
| `blocking_message` | Text | NOT NULL |
| `is_active` | Boolean | NOT NULL, default=True |
| `updated_by` | String(36) | NOT NULL, default="system" |
| `updated_at` | DateTime | NOT NULL, default=datetime.utcnow |
| `created_at` | DateTime | NOT NULL, default=datetime.utcnow |
| `Campos` | UUID | PK, NOT NULL, default=uuid.uuid4 |
| `level` | String(20) | NOT NULL, default="primary" |
| `company_id` | String(36) | NOT NULL, default="system" |

---

## health_check
**Arquivo:** `lia-agent-system/libs/models/lia_models/health_check.py`

### `compliance_health_check_history`
**Classe:** `ComplianceHealthCheckHistory` | **Herda:** `Base` | **Uso:** Routers/Services: 1 | Total refs: 2

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `item_id` | UUID | NOT NULL, INDEX, FK → compliance_health_check_items.id |
| `old_status` | String(20) | — |
| `new_status` | String(20) | NOT NULL |
| `changed_by_id` | UUID | — |
| `changed_by_name` | String(255) | — |
| `comments` | Text | — |
| `created_at` | DateTime | INDEX, default=func.now(, server_default |

### `compliance_health_check_items`
**Classe:** `ComplianceHealthCheckItem` | **Herda:** `Base` | **Uso:** Routers/Services: 1 | Total refs: 2

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `framework` | String(50) | NOT NULL, INDEX |
| `category` | String(100) | NOT NULL, INDEX |
| `req_id` | String(50) | NOT NULL, UNIQUE, INDEX |
| `requirement` | String(500) | NOT NULL |
| `evidence` | String(500) | — |
| `gap_observation` | Text | — |
| `status` | String(20) | NOT NULL, default="not_checked" |
| `last_checked_at` | DateTime | — |
| `checked_by_id` | UUID | — |
| `checked_by_name` | String(255) | — |
| `next_review_date` | DateTime | — |
| `review_frequency` | String(20) | default="monthly" |
| `check_comments` | Text | — |
| `priority` | String(20) | default="medium" |
| `reference_url` | String(500) | — |
| `reference_label` | String(100) | — |
| `created_at` | DateTime | default=func.now(, server_default |
| `updated_at` | DateTime | default=func.now(, server_default |
| `evidence_details` | Text | default=[] |

---

## hitl
**Arquivo:** `lia-agent-system/libs/models/lia_models/hitl.py`

### `hitl_audit_trail`
**Classe:** `HITLAuditTrail` | **Herda:** `Base` | **Uso:** Routers/Services: 1 | Total refs: 2

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `company_id` | String(255) | INDEX |
| `thread_id` | String(255) | NOT NULL |
| `pending_id` | String(255) | NOT NULL |
| `domain` | String(100) | NOT NULL |
| `action` | String(255) | NOT NULL |
| `approved` | Boolean | NOT NULL |
| `comment` | Text | — |
| `resolved_by` | String(255) | — |
| `resolved_at` | DateTime | NOT NULL, default=lambda: datetime.now(UTC |

### `hitl_pending_actions`
**Classe:** `HITLPendingAction` | **Herda:** `Base` | **Uso:** Routers/Services: 1 | Total refs: 2

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `company_id` | String(255) | INDEX |
| `thread_id` | String(255) | NOT NULL |
| `pending_id` | String(255) | NOT NULL, UNIQUE |
| `domain` | String(100) | NOT NULL |
| `action` | String(255) | NOT NULL |
| `description` | Text | — |
| `data` | JSON | default=dict |
| `agent_input` | JSON | default=dict |
| `ws_session_id` | String(255) | — |
| `status` | String(20) | NOT NULL, default="pending" |
| `approved` | Boolean | — |
| `comment` | Text | — |
| `resolved_by` | String(255) | — |
| `created_at` | DateTime | NOT NULL, default=lambda: datetime.now(UTC |
| `expires_at` | DateTime | NOT NULL |
| `resolved_at` | DateTime | — |

---

## imported_job_description
**Arquivo:** `lia-agent-system/libs/models/lia_models/imported_job_description.py`

### `client_skill_catalogs`
**Classe:** `ClientSkillCatalog` | **Herda:** `Base` | **Uso:** Routers/Services: 2 | Total refs: 4

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid4 |
| `company_id` | UUID | NOT NULL, INDEX |
| `skill_name` | String(255) | NOT NULL |
| `skill_name_normalized` | String(255) | NOT NULL, INDEX |
| `skill_type` | String(50) | default="technical" |
| `frequency` | Integer | default=1 |
| `associated_titles` | String | default=list |
| `associated_departments` | String | default=list |
| `associated_seniorities` | String | default=list |
| `typical_level` | String(50) | — |
| `source_jds` | String | default=list |
| `success_rate` | Float | — |
| `is_active` | Boolean | default=True |
| `created_at` | DateTime | default=datetime.utcnow |
| `updated_at` | DateTime | default=datetime.utcnow |

### `import_batches`
**Classe:** `ImportBatch` | **Herda:** `Base` | **Uso:** Routers/Services: 1 | Total refs: 3

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid4 |
| `company_id` | UUID | NOT NULL, INDEX |
| `source` | String(50) | NOT NULL |
| `source_connection_id` | UUID | — |
| `status` | String(50) | default=ImportStatus.PENDING.value |
| `total_records` | Integer | default=0 |
| `processed_records` | Integer | default=0 |
| `successful_records` | Integer | default=0 |
| `failed_records` | Integer | default=0 |
| `skipped_records` | Integer | default=0 |
| `import_config` | JSON | default=dict |
| `errors` | JSON | default=list |
| `warnings` | JSON | default=list |
| `started_at` | DateTime | — |
| `completed_at` | DateTime | — |
| `created_by` | String(255) | — |
| `created_at` | DateTime | INDEX, default=datetime.utcnow |
| `Enables` | UUID | PK, default=uuid4 |

### `imported_job_descriptions`
**Classe:** `ImportedJobDescription` | **Herda:** `Base` | **Uso:** Routers/Services: 2 | Total refs: 4

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid4 |
| `company_id` | UUID | NOT NULL, INDEX |
| `external_id` | String(255) | INDEX |
| `source` | String(50) | NOT NULL, default=ImportSource.MANUAL_UPLOAD.value |
| `import_batch_id` | UUID | INDEX |
| `job_title_original` | String(500) | NOT NULL |
| `job_title_normalized` | String(255) | INDEX |
| `department` | String(100) | INDEX |
| `area` | String(100) | — |
| `team` | String(100) | — |
| `seniority` | String(50) | INDEX |
| `seniority_confidence` | Float | default=0.0 |
| `employment_type` | String(50) | — |
| `work_model` | String(50) | — |
| `location` | String(255) | — |
| `description_raw` | Text | — |
| `description_parsed` | Text | — |
| `responsibilities` | String | default=list |
| `responsibilities_raw` | Text | — |
| `technical_skills` | JSON | default=list |
| `behavioral_competencies` | JSON | default=list |
| `requirements_mandatory` | String | default=list |
| `requirements_desirable` | String | default=list |
| `salary_min` | Float | — |
| `salary_max` | Float | — |
| `salary_currency` | String(10) | default="BRL" |
| `salary_period` | String(20) | default="monthly" |
| `salary_confidential` | Boolean | default=False |
| `benefits` | String | default=list |
| `benefits_details` | JSON | default=dict |
| `hiring_manager` | String(255) | — |
| `hiring_manager_email` | String(255) | — |
| `recruiter` | String(255) | — |
| `headcount` | Integer | default=1 |
| `job_status` | String(50) | — |
| `was_filled` | Boolean | — |
| `candidates_count` | Integer | — |
| `time_to_fill_days` | Integer | — |
| `hired_candidate_id` | String(255) | — |
| `created_date_original` | DateTime | — |
| `closed_date_original` | DateTime | — |
| `processing_status` | String(50) | default=ProcessingStatus.RAW.value |
| `parsing_confidence` | Float | default=0.0 |
| `parsing_errors` | JSON | default=list |
| `metadata_raw` | JSON | default=dict |
| `is_used_for_learning` | Boolean | default=True |
| `times_used_as_template` | Integer | default=0 |
| `created_at` | DateTime | INDEX, default=datetime.utcnow |
| `updated_at` | DateTime | default=datetime.utcnow |
| `processed_at` | DateTime | — |

---

## integration_hub
**Arquivo:** `lia-agent-system/libs/models/lia_models/integration_hub.py`

### `integration_connections`
**Classe:** `IntegrationConnection` | **Herda:** `Base` | **Uso:** Routers/Services: 2 | Total refs: 4

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `company_id` | UUID | NOT NULL, FK → company_profiles.id |
| `provider_id` | UUID | NOT NULL, FK → integration_providers.id |
| `status` | String(50) | default="not_connected" |
| `auth_type` | String(50) | — |
| `credentials` | JSON | default={} |
| `sync_enabled` | Boolean | default=True |
| `sync_direction` | String(50) | default="bidirectional" |
| `sync_frequency` | String(50) | default="realtime" |
| `last_sync_at` | DateTime | — |
| `last_sync_status` | String(50) | — |
| `last_sync_error` | Text | — |
| `field_mappings` | JSON | default={} |
| `health_score` | Float | default=100.0 |
| `error_count` | Integer | default=0 |
| `created_at` | DateTime | default=datetime.utcnow |
| `updated_at` | DateTime | default=datetime.utcnow |
| `created_by` | String(255) | — |

### `integration_providers`
**Classe:** `IntegrationProvider` | **Herda:** `Base` | **Uso:** Routers/Services: 1 | Total refs: 3

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `name` | String(255) | NOT NULL |
| `category` | String(100) | NOT NULL |
| `slug` | String(100) | NOT NULL, UNIQUE |
| `description` | Text | — |
| `logo_url` | String(500) | — |
| `supports_oauth` | Boolean | default=False |
| `supports_api_key` | Boolean | default=False |
| `supports_webhook` | Boolean | default=False |
| `features` | String | default=[] |
| `setup_instructions` | Text | — |
| `documentation_url` | String(500) | — |
| `is_active` | Boolean | default=True |
| `is_premium` | Boolean | default=False |
| `created_at` | DateTime | default=datetime.utcnow |

### `integration_sync_logs`
**Classe:** `IntegrationSyncLog` | **Herda:** `Base` | **Uso:** Routers/Services: 1 | Total refs: 3

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `connection_id` | UUID | NOT NULL, FK → integration_connections.id |
| `sync_type` | String(50) | NOT NULL |
| `direction` | String(50) | — |
| `status` | String(50) | NOT NULL |
| `records_processed` | Integer | default=0 |
| `records_created` | Integer | default=0 |
| `records_updated` | Integer | default=0 |
| `records_failed` | Integer | default=0 |
| `error_message` | Text | — |
| `error_details` | JSON | default={} |
| `started_at` | DateTime | default=datetime.utcnow |
| `completed_at` | DateTime | — |
| `duration_seconds` | Float | — |
| `sync_metadata` | JSON | default={} |

---

## intelligence_layer
**Arquivo:** `lia-agent-system/libs/models/lia_models/intelligence_layer.py`

### `correction_patterns`
**Classe:** `CorrectionPattern` | **Herda:** `Base` | **Uso:** Routers/Services: 4 | Total refs: 6

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `company_id` | String(255) | NOT NULL, INDEX |
| `field` | String(100) | NOT NULL, INDEX |
| `pattern_type` | String(100) | INDEX |
| `seniority` | String(50) | INDEX |
| `department` | String(100) | — |
| `original_value_pattern` | String(255) | — |
| `corrected_value_pattern` | String(255) | — |
| `adjustment_direction` | String(20) | — |
| `adjustment_magnitude` | Float | — |
| `occurrence_count` | Integer | — |
| `sample_size` | Integer | default=0 |
| `confidence` | Float | default=0.0 |
| `is_active` | Boolean | default=True |
| `created_at` | DateTime | default=datetime.utcnow |
| `updated_at` | DateTime | default=datetime.utcnow |

### `intelligence_insights`
**Classe:** `IntelligenceInsight` | **Herda:** `Base` | **Uso:** Routers/Services: 1 | Total refs: 3

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `company_id` | String(255) | NOT NULL, INDEX |
| `job_id` | UUID | INDEX |
| `recruiter_id` | String(255) | INDEX |
| `insight_type` | String(50) | NOT NULL, INDEX |
| `field` | String(100) | INDEX |
| `original_value` | JSON | — |
| `suggested_value` | JSON | — |
| `confidence` | Float | NOT NULL, default=0.0 |
| `source` | String(50) | — |
| `reasoning` | Text | — |
| `was_applied` | Boolean | — |
| `was_accepted` | Boolean | — |
| `final_value` | JSON | — |
| `insight_metadata` | JSON | default=dict |
| `created_at` | DateTime | INDEX, default=datetime.utcnow |

### `outcome_correlations`
**Classe:** `OutcomeCorrelation` | **Herda:** `Base` | **Uso:** Routers/Services: 2 | Total refs: 4

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `company_id` | String(255) | NOT NULL, INDEX |
| `factor` | String(100) | NOT NULL, INDEX |
| `outcome_metric` | String(100) | NOT NULL, INDEX |
| `role_pattern` | String(200) | — |
| `seniority` | String(50) | — |
| `correlation` | Float | NOT NULL |
| `significance` | Float | — |
| `direction` | String(20) | — |
| `recommendation` | Text | — |
| `sample_size` | Integer | NOT NULL, default=0 |
| `factor_values` | JSON | default=dict |
| `outcome_values` | JSON | default=dict |
| `created_at` | DateTime | default=datetime.utcnow |
| `updated_at` | DateTime | default=datetime.utcnow |
| `Example` | UUID | PK, default=uuid.uuid4 |

### `pattern_cache`
**Classe:** `PatternCache` | **Herda:** `Base` | **Uso:** Routers/Services: 2 | Total refs: 4

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `company_id` | String(255) | NOT NULL, INDEX |
| `pattern_type` | String(50) | NOT NULL, INDEX |
| `pattern_key` | String(200) | NOT NULL, INDEX |
| `pattern_data` | JSON | NOT NULL, default=dict |
| `sample_size` | Integer | NOT NULL, default=0 |
| `confidence` | Float | NOT NULL, default=0.0 |
| `calculated_at` | DateTime | NOT NULL, default=datetime.utcnow |
| `expires_at` | DateTime | — |
| `created_at` | DateTime | default=datetime.utcnow |
| `updated_at` | DateTime | default=datetime.utcnow |

### `success_profiles`
**Classe:** `SuccessProfile` | **Herda:** `Base` | **Uso:** Routers/Services: 3 | Total refs: 5

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `company_id` | String(255) | NOT NULL, INDEX |
| `seniority` | String(50) | INDEX |
| `department` | String(100) | — |
| `role_family` | String(200) | INDEX |
| `avg_time_to_fill_days` | Integer | — |
| `avg_salary` | Float | — |
| `salary_range_min` | Float | — |
| `salary_range_max` | Float | — |
| `common_skills` | JSON | default=list |
| `common_requirements` | JSON | default=list |
| `preferred_work_model` | String(100) | — |
| `avg_satisfaction_score` | Float | — |
| `sample_size` | Integer | default=0 |
| `created_at` | DateTime | default=datetime.utcnow |
| `updated_at` | DateTime | default=datetime.utcnow |

---

## intelligent_cache
**Arquivo:** `lia-agent-system/libs/models/lia_models/intelligent_cache.py`

### `cache_entries`
**Classe:** `CacheEntry` | **Herda:** `Base` | **Uso:** Routers/Services: 3 | Total refs: 5

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `cache_key` | String(512) | NOT NULL, UNIQUE, INDEX |
| `namespace` | String(100) | NOT NULL, INDEX |
| `company_id` | String(255) | INDEX |
| `value` | JSON | NOT NULL |
| `value_type` | String(50) | default="json" |
| `ttl_seconds` | Integer | NOT NULL, default=86400 |
| `expires_at` | DateTime | NOT NULL, INDEX |
| `hit_count` | Integer | default=0 |
| `last_hit_at` | DateTime | — |
| `source` | String(100) | — |
| `confidence` | Float | — |
| `tags` | String | default=[] |
| `created_at` | DateTime | default=datetime.utcnow |
| `updated_at` | DateTime | default=datetime.utcnow |
| `Example` | UUID | PK, default=uuid.uuid4 |

---

## interview
**Arquivo:** `lia-agent-system/libs/models/lia_models/interview.py`

### `calendar_availability`
**Classe:** `CalendarAvailability` | **Herda:** `Base` | **Uso:** Routers/Services: 0 | Total refs: 3

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `user_email` | String(255) | NOT NULL, INDEX |
| `user_name` | String(255) | NOT NULL |
| `timezone` | String(100) | default="America/Sao_Paulo" |
| `is_active` | Boolean | default=True |
| `max_interviews_per_day` | Integer | default=4 |
| `created_at` | DateTime | default=datetime.utcnow |
| `updated_at` | DateTime | default=datetime.utcnow |
| `day_of_week` | String(10) | NOT NULL, default="America/Sao_Paulo" |
| `buffer_minutes` | Integer | default=15 |

### `interview_feedbacks`
**Classe:** `InterviewFeedback` | **Herda:** `Base` | **Uso:** Routers/Services: 2 | Total refs: 5

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `interview_id` | UUID | NOT NULL, INDEX |
| `interviewer_name` | String(255) | NOT NULL |
| `interviewer_email` | String(255) | NOT NULL |
| `technical_skills_rating` | Float | — |
| `communication_rating` | Float | — |
| `cultural_fit_rating` | Float | — |
| `overall_rating` | Float | — |
| `notes` | Text | — |
| `recommendation` | String(50) | — |
| `next_steps_suggested` | Text | — |
| `created_at` | DateTime | default=datetime.utcnow |
| `updated_at` | DateTime | default=datetime.utcnow |
| `interviewer_role` | String(100) | — |
| `strengths` | Text | default=[] |

### `interview_notes`
**Classe:** `InterviewNote` | **Herda:** `Base` | **Uso:** Routers/Services: 3 | Total refs: 6

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `company_id` | UUID | NOT NULL, INDEX |
| `candidate_id` | UUID | NOT NULL, INDEX |
| `candidate_name` | String(255) | — |
| `job_id` | UUID | INDEX |
| `job_title` | String(255) | — |
| `scheduled_interview_id` | String(255) | INDEX |
| `interviewer_id` | String(255) | — |
| `recruiter_name` | String(255) | — |
| `interview_date` | DateTime | — |
| `general_notes` | Text | — |
| `transcription` | Text | — |
| `lia_parecer` | Text | — |
| `lia_parecer_editado` | Boolean | default=False |
| `wsi_score` | JSON | — |
| `next_stage` | String(100) | — |
| `feedback_sent` | Boolean | default=False |
| `feedback_scheduled_for` | DateTime | — |
| `created_by` | String(255) | NOT NULL, default="system" |
| `created_at` | DateTime | INDEX, default=datetime.utcnow |
| `updated_at` | DateTime | default=datetime.utcnow |
| `interview_type` | String(50) | default="structured" |
| `questions` | Text | default=[] |
| `transcription_source` | String(50) | — |
| `recommendation` | String(50) | — |
| `status` | String(20) | NOT NULL, INDEX, default="draft" |

### `interviews`
**Classe:** `Interview` | **Herda:** `Base` | **Uso:** Routers/Services: 61 | Total refs: 88

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `company_id` | String(255) | INDEX |
| `title` | String(255) | NOT NULL |
| `description` | Text | — |
| `interview_type` | String(50) | NOT NULL |
| `interview_mode` | String(50) | default="video" |
| `candidate_id` | UUID | — |
| `candidate_name` | String(255) | NOT NULL |
| `candidate_email` | String(255) | NOT NULL |
| `interviewer_name` | String(255) | NOT NULL |
| `interviewer_email` | String(255) | NOT NULL |
| `additional_interviewers` | JSON | default=[] |
| `start_time` | DateTime | NOT NULL |
| `end_time` | DateTime | NOT NULL |
| `timezone` | String(100) | default="America/Sao_Paulo" |
| `duration_minutes` | Integer | default=60 |
| `location` | String(500) | — |
| `meeting_url` | String(1000) | — |
| `meeting_platform` | String(50) | — |
| `meeting_id` | String(255) | — |
| `graph_event_id` | String(255) | INDEX |
| `graph_calendar_id` | String(255) | — |
| `graph_organizer_email` | String(255) | — |
| `is_synced_to_calendar` | Boolean | default=False |
| `calendar_sync_error` | Text | — |
| `last_synced_at` | DateTime | — |
| `google_event_id` | String(255) | INDEX |
| `google_meet_link` | String(500) | — |
| `status` | String(50) | INDEX, default="scheduled" |
| `confirmation_status` | String(50) | default="pending" |
| `reminder_sent` | Boolean | default=False |
| `reminder_sent_at` | DateTime | — |
| `confirmation_request_sent` | Boolean | default=False |
| `confirmation_request_sent_at` | DateTime | — |
| `job_vacancy_id` | UUID | — |
| `job_title` | String(255) | — |
| `application_stage` | String(100) | — |
| `recruitment_stage_id` | UUID | INDEX |
| `feedback` | JSON | default={} |
| `interviewer_notes` | Text | — |
| `recording_url` | String(1000) | — |
| `transcript` | Text | — |
| `transcript_language` | String(10) | default="pt-BR" |
| `transcribed_at` | DateTime | — |
| `lia_preparation_notes` | JSON | default={} |
| `lia_suggested_questions` | JSON | default=[] |
| `interview_metadata` | JSON | default={} |
| `created_by` | String(255) | NOT NULL, default="system" |
| `created_at` | DateTime | INDEX, default=datetime.utcnow |
| `updated_at` | DateTime | default=datetime.utcnow |
| `completed_at` | DateTime | — |
| `cancelled_at` | DateTime | — |
| `cancellation_reason` | Text | — |
| `transcript_source` | String(50) | — |

---

## job_draft
**Arquivo:** `lia-agent-system/libs/models/lia_models/job_draft.py`

### `draft_field_history`
**Classe:** `DraftFieldHistory` | **Herda:** `Base` | **Uso:** Routers/Services: 3 | Total refs: 5

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `field_name` | String(100) | NOT NULL, INDEX |
| `old_value` | JSON | — |
| `new_value` | JSON | — |
| `confidence_at_change` | Float | — |
| `source` | String(100) | — |
| `reason` | Text | — |
| `created_at` | DateTime | NOT NULL, default=datetime.utcnow |
| `created_by` | String(255) | — |
| `draft_id` | UUID | NOT NULL, INDEX, FK → job_drafts.id |
| `change_type` | Enum(ChangeType, name="draft_change_type", create_type=True) | NOT NULL, INDEX |

### `job_drafts`
**Classe:** `JobDraft` | **Herda:** `Base` | **Uso:** Routers/Services: 6 | Total refs: 9

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `company_id` | String(255) | NOT NULL, INDEX |
| `recruiter_id` | String(255) | NOT NULL, INDEX |
| `conversation_id` | UUID | INDEX |
| `current_step` | String(100) | default="input" |
| `raw_input` | Text | — |
| `imported_jd` | Text | — |
| `detected_language` | String(10) | default="pt-BR" |
| `job_title` | String(255) | — |
| `department` | String(100) | — |
| `seniority` | String(50) | — |
| `location` | String(255) | — |
| `work_model` | String(50) | — |
| `hybrid_days` | Integer | — |
| `employment_type` | String(50) | — |
| `salary_min` | Float | — |
| `salary_max` | Float | — |
| `currency` | String(10) | default="BRL" |
| `country` | String(100) | default="Brasil" |
| `pj_rate` | Float | — |
| `is_affirmative` | Boolean | default=False |
| `affirmative_criteria_primary` | String(100) | — |
| `affirmative_criteria_secondary` | String(100) | — |
| `manager` | String(255) | — |
| `manager_email` | String(255) | — |
| `skills` | String | default=list |
| `benefits` | String | default=list |
| `languages` | String | default=list |
| `behavioral_competencies` | JSON | default=list |
| `screening_questions` | JSON | default=list |
| `pipeline_stages` | JSON | default=list |
| `generated_jd` | Text | — |
| `inferred_fields` | JSON | default=dict |
| `confirmed_fields` | JSON | default=dict |
| `company_defaults_used` | JSON | default=dict |
| `confidence_map` | JSON | default=dict |
| `insights` | JSON | default=list |
| `warnings` | JSON | default=list |
| `estimated_ttf` | Integer | — |
| `job_complexity` | String(50) | — |
| `created_at` | DateTime | NOT NULL, default=datetime.utcnow |
| `updated_at` | DateTime | NOT NULL, default=datetime.utcnow |
| `structured_at` | DateTime | — |
| `reviewed_at` | DateTime | — |
| `published_at` | DateTime | — |
| `status` | Enum(JobDraftStatus, name="job_draft_status", create_type=True) | NOT NULL, INDEX, default=JobDraftStatus.DRAFT |
| `published_job_id` | UUID | FK → job_vacancies.id |

---

## job_pattern
**Arquivo:** `lia-agent-system/libs/models/lia_models/job_pattern.py`

### `job_embeddings`
**Classe:** `JobEmbedding` | **Herda:** `Base` | **Uso:** Routers/Services: 1 | Total refs: 4

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid4 |
| `company_id` | UUID | NOT NULL, INDEX |
| `job_id` | UUID | NOT NULL, UNIQUE, INDEX |
| `draft_id` | UUID | INDEX |
| `job_title` | String(255) | NOT NULL |
| `job_title_normalized` | String(255) | INDEX |
| `department` | String(100) | — |
| `seniority` | String(50) | — |
| `location` | String(255) | — |
| `work_model` | String(50) | — |
| `description_summary` | Text | — |
| `skills` | String | default=list |
| `behavioral_competencies` | String | default=list |
| `embedding` | Vector | — |
| `embedding_text` | Text | — |
| `embedding_provider` | String(50) | — |
| `embedding_model` | String(100) | — |
| `outcome_status` | String(50) | — |
| `time_to_fill_days` | Integer | — |
| `hire_quality_score` | Float | — |
| `metadata_json` | JSON | default=dict |
| `is_template` | Boolean | default=False |
| `is_active` | Boolean | default=True |
| `created_at` | DateTime | INDEX, default=datetime.utcnow |
| `updated_at` | DateTime | default=datetime.utcnow |
| `Enables` | UUID | PK, default=uuid4 |

### `job_patterns`
**Classe:** `JobPattern` | **Herda:** `Base` | **Uso:** Routers/Services: 3 | Total refs: 6

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid4 |
| `company_id` | UUID | NOT NULL, INDEX |
| `pattern_type` | String(50) | NOT NULL, INDEX |
| `pattern_key` | String(255) | NOT NULL, INDEX |
| `job_title_normalized` | String(255) | INDEX |
| `department` | String(100) | INDEX |
| `seniority` | String(50) | — |
| `location` | String(255) | — |
| `work_model` | String(50) | — |
| `sample_count` | Integer | default=0 |
| `success_count` | Integer | default=0 |
| `success_rate` | Float | default=0.0 |
| `avg_salary_min` | Float | — |
| `avg_salary_max` | Float | — |
| `salary_percentile_25` | Float | — |
| `salary_percentile_75` | Float | — |
| `common_skills` | String | default=list |
| `skill_frequency` | JSON | default=dict |
| `common_behavioral` | String | default=list |
| `behavioral_frequency` | JSON | default=dict |
| `avg_time_to_fill` | Integer | — |
| `median_time_to_fill` | Integer | — |
| `time_to_fill_samples` | JSON | default=list |
| `common_benefits` | String | default=list |
| `common_languages` | String | default=list |
| `success_profiles` | JSON | default=list |
| `embedding` | Vector | — |
| `is_active` | Boolean | default=True |
| `confidence` | Float | default=0.3 |
| `created_at` | DateTime | INDEX, default=datetime.utcnow |
| `updated_at` | DateTime | default=datetime.utcnow |
| `last_sample_at` | DateTime | — |

### `salary_benchmarks`
**Classe:** `SalaryBenchmark` | **Herda:** `Base` | **Uso:** Routers/Services: 4 | Total refs: 7

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid4 |
| `company_id` | UUID | NOT NULL, INDEX |
| `job_title_normalized` | String(255) | NOT NULL, INDEX |
| `department` | String(100) | — |
| `seniority` | String(50) | INDEX |
| `location` | String(255) | — |
| `work_model` | String(50) | — |
| `sample_count` | Integer | default=0 |
| `min_salary` | Float | — |
| `max_salary` | Float | — |
| `avg_salary` | Float | — |
| `median_salary` | Float | — |
| `percentile_10` | Float | — |
| `percentile_25` | Float | — |
| `percentile_50` | Float | — |
| `percentile_75` | Float | — |
| `percentile_90` | Float | — |
| `salary_samples` | JSON | default=list |
| `currency` | String(10) | default="BRL" |
| `last_updated` | DateTime | default=datetime.utcnow |
| `created_at` | DateTime | default=datetime.utcnow |
| `Provides` | UUID | PK, default=uuid4 |

### `skill_clusters`
**Classe:** `SkillCluster` | **Herda:** `Base` | **Uso:** Routers/Services: 0 | Total refs: 3

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid4 |
| `company_id` | UUID | NOT NULL, INDEX |
| `cluster_name` | String(255) | NOT NULL |
| `cluster_type` | String(50) | NOT NULL |
| `core_skills` | String | default=list |
| `related_skills` | String | default=list |
| `skill_cooccurrence` | JSON | default=dict |
| `job_titles` | String | default=list |
| `departments` | String | default=list |
| `sample_count` | Integer | default=0 |
| `is_active` | Boolean | default=True |
| `created_at` | DateTime | default=datetime.utcnow |
| `updated_at` | DateTime | default=datetime.utcnow |
| `Enables` | UUID | PK, default=uuid4 |

---

## job_template
**Arquivo:** `lia-agent-system/libs/models/lia_models/job_template.py`

### `job_templates`
**Classe:** `JobTemplate` | **Herda:** `Base` | **Uso:** Routers/Services: 2 | Total refs: 4

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid4 |
| `company_id` | UUID | INDEX |
| `parent_template_id` | UUID | FK → job_templates.id |
| `category` | String(50) | NOT NULL, INDEX |
| `subcategory` | String(50) | NOT NULL, INDEX |
| `title` | String(200) | NOT NULL |
| `title_normalized` | String(200) | NOT NULL, INDEX |
| `title_alternatives` | String | default=list |
| `seniority` | String(20) | NOT NULL, INDEX |
| `default_description` | Text | — |
| `default_responsibilities` | String | default=list |
| `default_requirements` | Text | — |
| `default_nice_to_have` | Text | — |
| `default_education` | String | default=list |
| `default_certifications` | String | default=list |
| `default_languages` | String | default=list |
| `default_skills` | JSON | default=list |
| `default_behavioral` | JSON | default=list |
| `salary_range_min` | Integer | — |
| `salary_range_max` | Integer | — |
| `salary_currency` | String(3) | default="BRL" |
| `work_model` | String(20) | default="hybrid" |
| `employment_type` | String(20) | default="clt" |
| `experience_years_min` | Integer | — |
| `experience_years_max` | Integer | — |
| `is_system` | Boolean | INDEX, default=False |
| `is_active` | Boolean | INDEX, default=True |
| `usage_count` | Integer | default=0 |
| `last_used_at` | DateTime | — |
| `popularity_score` | Float | default=0.0 |
| `quality_score` | Float | default=0.0 |
| `template_metadata` | JSON | default=dict |
| `created_at` | DateTime | INDEX, default=datetime.utcnow |
| `updated_at` | DateTime | default=datetime.utcnow |
| `created_by` | UUID | — |

### `template_usage_logs`
**Classe:** `TemplateUsageLog` | **Herda:** `Base` | **Uso:** Routers/Services: 1 | Total refs: 2

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid4 |
| `template_id` | UUID | NOT NULL, INDEX, FK → job_templates.id |
| `company_id` | UUID | NOT NULL, INDEX |
| `user_id` | UUID | — |
| `job_id` | UUID | INDEX |
| `action` | String(50) | NOT NULL |
| `fields_modified` | String | default=list |
| `modifications_count` | Integer | default=0 |
| `time_to_complete_seconds` | Integer | — |
| `completion_rate` | Float | — |
| `feedback_rating` | Integer | — |
| `feedback_text` | Text | — |
| `session_data` | JSON | default=dict |
| `created_at` | DateTime | INDEX, default=datetime.utcnow |
| `Tracks` | UUID | PK, default=uuid4 |

---

## job_vacancy
**Arquivo:** `lia-agent-system/libs/models/lia_models/job_vacancy.py`

### `job_vacancies`
**Classe:** `JobVacancy` | **Herda:** `Base` | **Uso:** Routers/Services: 82 | Total refs: 101

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `company_id` | String(255) | NOT NULL, INDEX |
| `title` | String(255) | NOT NULL, INDEX |
| `department` | String(100) | — |
| `location` | String(255) | — |
| `description` | Text | — |
| `requirements` | String | default=list |
| `benefits` | String | default=list |
| `open_date` | DateTime | — |
| `deadline` | DateTime | — |
| `manager` | String(255) | — |
| `manager_email` | String(255) | — |
| `recruiter` | String(255) | — |
| `recruiter_email` | String(255) | — |
| `disabled_eligibility_question_ids` | JSON | default=list |
| `published_linkedin` | Boolean | default=False |
| `published_website` | Boolean | default=False |
| `published_indeed` | Boolean | default=False |
| `linkedin_post_id` | String(255) | — |
| `indeed_job_id` | String(255) | — |
| `last_published_at` | DateTime | — |
| `is_affirmative` | Boolean | default=False |
| `affirmative_description` | Text | — |
| `visibility` | String(50) | INDEX, default="public" |
| `access_list` | String | default=list |
| `masked_company_name` | String(255) | — |
| `exclude_from_sync` | Boolean | default=False |
| `budget` | Float | — |
| `budget_used` | Float | default=0.0 |
| `approval_requested_at` | DateTime | — |
| `approval_requested_by` | String(255) | — |
| `approved_by` | String(255) | — |
| `approved_at` | DateTime | — |
| `rejection_reason` | Text | — |
| `tags` | String | default=list |
| `target_audience` | String(500) | — |
| `nps` | Integer | — |
| `next_actions` | String | default=list |
| `eligibility_questions` | JSON | default=list |
| `confidentiality_config` | JSON | — |
| `enriched_jd` | JSON | — |
| `pipeline_config` | JSON | — |
| `is_pipeline_customized` | Boolean | NOT NULL, default=False |
| `qualification_classified_at` | DateTime | — |
| `created_at` | DateTime | INDEX, default=datetime.utcnow |
| `updated_at` | DateTime | default=datetime.utcnow |
| `published_at` | DateTime | — |
| `closed_at` | DateTime | — |
| `conversation_id` | UUID | INDEX, FK → conversations.id |
| `job_id` | String(50) | NOT NULL, INDEX |
| `work_model` | String(50) | — |
| `technical_requirements` | String(100) | default=list |
| `status` | String(50) | INDEX, default="Rascunho" |
| `deadline_screening` | String(255) | — |
| `created_by` | String(255) | — |
| `interview_stages` | JSON | default=list |
| `screening_questions` | JSON | default=list |
| `is_confidential` | Boolean | default=False |
| `affirmative_criteria_primary` | String(50) | — |
| `affirmative_document_required` | String | default=True |
| `public_slug` | String(100) | UNIQUE, INDEX |
| `whatsapp_template_type` | String(50) | — |
| `approval_status` | String(50) | default="pendente" |
| `hiring_process` | String(500) | default=list |
| `target_sector` | String(255) | — |
| `funnel_data` | String | default={} |
| `timeline` | JSON | — |
| `governance_rules` | JSON | — |
| `screening_config` | JSON | default=list |
| `additional_data` | JSON | default={} |
| `qualification_level` | String(20) | INDEX, default=False |

---

## job_vacancy_audit
**Arquivo:** `lia-agent-system/libs/models/lia_models/job_vacancy_audit.py`

### `job_vacancy_audit_logs`
**Classe:** `JobVacancyAuditLog` | **Herda:** `Base` | **Uso:** Routers/Services: 1 | Total refs: 3

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `job_vacancy_id` | UUID | NOT NULL, INDEX, FK → job_vacancies.id |
| `company_id` | String(255) | NOT NULL, INDEX |
| `action` | String(50) | NOT NULL, INDEX |
| `field_changed` | String(255) | — |
| `old_value` | JSON | — |
| `new_value` | JSON | — |
| `changed_by` | String(255) | NOT NULL |
| `changed_at` | DateTime | NOT NULL, INDEX, default=datetime.utcnow |
| `ip_address` | String(45) | — |
| `user_agent` | Text | — |
| `extra_data` | JSON | default=dict |

---

## journey_mapping
**Arquivo:** `lia-agent-system/libs/models/lia_models/journey_mapping.py`

### `journey_blueprints`
**Classe:** `JourneyBlueprint` | **Herda:** `Base` | **Uso:** Routers/Services: 2 | Total refs: 4

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `company_id` | UUID | NOT NULL, FK → company_profiles.id |
| `name` | String(255) | default="Jornada Principal" |
| `description` | Text | — |
| `status` | String(50) | default="draft" |
| `wizard_step` | Integer | default=1 |
| `wizard_completed` | Boolean | default=False |
| `wizard_data` | JSON | default={} |
| `ai_summary` | Text | — |
| `ai_recommendations` | JSON | default=[] |
| `vacancy_origin` | String(100) | — |
| `has_external_wfp` | Boolean | default=False |
| `has_internal_wfp` | Boolean | default=False |
| `created_at` | DateTime | default=datetime.utcnow |
| `updated_at` | DateTime | default=datetime.utcnow |
| `created_by` | String(255) | — |

### `journey_integrations`
**Classe:** `JourneyIntegration` | **Herda:** `Base` | **Uso:** Routers/Services: 2 | Total refs: 4

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `blueprint_id` | UUID | NOT NULL, FK → journey_blueprints.id |
| `name` | String(255) | NOT NULL |
| `integration_type` | String(100) | NOT NULL |
| `provider` | String(100) | — |
| `is_enabled` | Boolean | default=False |
| `is_connected` | Boolean | default=False |
| `connection_config` | JSON | default={} |
| `field_mappings` | JSON | default={} |
| `sync_direction` | String(50) | default="bidirectional" |
| `sync_frequency` | String(50) | default="realtime" |
| `last_sync_at` | DateTime | — |
| `sync_status` | String(50) | default="pending" |
| `created_at` | DateTime | default=datetime.utcnow |
| `updated_at` | DateTime | default=datetime.utcnow |

### `journey_steps`
**Classe:** `JourneyStep` | **Herda:** `Base` | **Uso:** Routers/Services: 2 | Total refs: 4

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `blueprint_id` | UUID | NOT NULL, FK → journey_blueprints.id |
| `name` | String(255) | NOT NULL |
| `description` | Text | — |
| `step_type` | String(100) | NOT NULL |
| `order` | Integer | default=0 |
| `is_enabled` | Boolean | default=True |
| `is_required` | Boolean | default=True |
| `config` | JSON | default={} |
| `sla_days` | Integer | — |
| `responsible_role` | String(100) | — |
| `automation_enabled` | Boolean | default=False |
| `automation_config` | JSON | default={} |
| `ai_enabled` | Boolean | default=False |
| `ai_config` | JSON | default={} |
| `created_at` | DateTime | default=datetime.utcnow |
| `updated_at` | DateTime | default=datetime.utcnow |

---

## lia_field_toggles
**Arquivo:** `lia-agent-system/libs/models/lia_models/lia_field_toggles.py`

### `lia_field_toggles`
**Classe:** `LiaFieldToggle` | **Herda:** `Base` | **Uso:** Routers/Services: 2 | Total refs: 5

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `company_id` | UUID | NOT NULL, INDEX, FK → company_profiles.id |
| `field_key` | String(100) | NOT NULL, INDEX |
| `is_active` | Boolean | NOT NULL, default=True |
| `comment` | Text | — |
| `updated_at` | DateTime | default=datetime.utcnow |
| `updated_by` | String(255) | — |
| `created_at` | DateTime | default=datetime.utcnow |

---

## lia_opinion
**Arquivo:** `lia-agent-system/libs/models/lia_models/lia_opinion.py`

### `lia_opinions`
**Classe:** `LiaOpinion` | **Herda:** `Base` | **Uso:** Routers/Services: 6 | Total refs: 8

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `candidate_id` | UUID | NOT NULL, INDEX, FK → candidates.id |
| `opinion_type` | String(50) | NOT NULL, INDEX, default="general" |
| `source` | String(50) | NOT NULL, default="cv_analysis" |
| `job_vacancy_id` | UUID | INDEX, FK → job_vacancies.id |
| `wsi_screening_id` | UUID | INDEX |
| `score` | Float | — |
| `wsi_score` | Float | — |
| `recommendation` | String(50) | — |
| `summary` | Text | — |
| `archetype` | String(100) | — |
| `archetype_match_score` | Float | — |
| `score_breakdown` | JSON | default={} |
| `technical_analysis` | JSON | default={} |
| `behavioral_analysis` | JSON | default={} |
| `cultural_fit` | JSON | default={} |
| `strengths` | JSON | default=[] |
| `concerns` | JSON | default=[] |
| `gaps` | JSON | default=[] |
| `matched_skills` | JSON | default=[] |
| `missing_skills` | JSON | default=[] |
| `next_steps` | Text | — |
| `recruiter_notes` | Text | — |
| `recruiter_override` | String(50) | — |
| `recruiter_override_reason` | Text | — |
| `recruiter_override_by` | String(255) | — |
| `recruiter_override_at` | DateTime | — |
| `is_current` | Boolean | INDEX, default=True |
| `version` | Integer | default=1 |
| `created_at` | DateTime | default=datetime.utcnow |
| `updated_at` | DateTime | default=datetime.utcnow |
| `created_by` | String(255) | — |
| `company_id` | String(100) | NOT NULL, INDEX |

---

## lia_profile_analysis
**Arquivo:** `lia-agent-system/libs/models/lia_models/lia_profile_analysis.py`

### `lia_profile_analyses`
**Classe:** `LiaProfileAnalysis` | **Herda:** `Base` | **Uso:** Routers/Services: 2 | Total refs: 3

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `candidate_id` | String(255) | NOT NULL, INDEX |
| `analysis_type` | String(50) | NOT NULL, INDEX |
| `content` | Text | NOT NULL |
| `candidate_name` | String(255) | — |
| `is_active` | Boolean | INDEX, default=True |
| `created_at` | DateTime | default=datetime.utcnow |
| `created_by` | String(255) | — |
| `company_id` | String(100) | NOT NULL, INDEX |

---

## memory
**Arquivo:** `lia-agent-system/libs/models/lia_models/memory.py`

### `conversation_memories`
**Classe:** `ConversationMemory` | **Herda:** `Base` | **Uso:** Routers/Services: 5 | Total refs: 11

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `company_id` | UUID | NOT NULL, INDEX |
| `session_id` | String(100) | NOT NULL, INDEX |
| `user_id` | String(100) | NOT NULL, INDEX |
| `content` | Text | NOT NULL |
| `created_at` | DateTime | INDEX, default=datetime.utcnow |
| `role` | String(20) | NOT NULL |
| `embedding` | DateTime | INDEX, default={} |

### `knowledge_base`
**Classe:** `KnowledgeBase` | **Herda:** `Base` | **Uso:** Routers/Services: 1 | Total refs: 3

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `company_id` | UUID | NOT NULL, INDEX |
| `title` | String(255) | NOT NULL |
| `content` | Text | NOT NULL |
| `source` | String(255) | — |
| `created_at` | DateTime | INDEX, default=datetime.utcnow |
| `updated_at` | DateTime | default=datetime.utcnow |
| `document_type` | String(50) | NOT NULL, INDEX |
| `embedding` | String(255) | — |
| `chunk_index` | UUID | INDEX, default={} |

---

## message_queue
**Arquivo:** `lia-agent-system/libs/models/lia_models/message_queue.py`

### `message_queue`
**Classe:** `MessageQueue` | **Herda:** `Base` | **Uso:** Routers/Services: 1 | Total refs: 6

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | String | PK, default=lambda: str(uuid.uuid4( |
| `company_id` | String(255) | NOT NULL, INDEX |
| `candidate_id` | String(255) | NOT NULL, INDEX |
| `candidate_name` | String(255) | NOT NULL |
| `candidate_email` | String(255) | — |
| `candidate_phone` | String(50) | — |
| `vacancy_id` | String(255) | INDEX |
| `vacancy_title` | String(255) | — |
| `channel` | String(20) | NOT NULL, INDEX |
| `message_type` | String(50) | NOT NULL, INDEX |
| `priority` | Integer | INDEX, default=MessagePriority.NORMAL |
| `subject` | String(500) | — |
| `body_html` | Text | — |
| `body_text` | Text | — |
| `template_id` | String(255) | — |
| `template_name` | String(255) | — |
| `template_variables` | JSON | default=dict |
| `status` | String(20) | NOT NULL, INDEX, default=MessageStatus.PENDING |
| `retry_count` | Integer | default=0 |
| `max_retries` | Integer | default=3 |
| `next_retry_at` | DateTime | INDEX |
| `last_retry_at` | DateTime | — |
| `provider_message_id` | String(255) | — |
| `provider_response` | JSON | default=dict |
| `error_message` | Text | — |
| `consent_verified` | Boolean | default=False |
| `consent_type` | String(50) | — |
| `consent_verified_at` | DateTime | — |
| `bulk_id` | String(255) | INDEX |
| `bulk_sequence` | Integer | — |
| `scheduled_at` | DateTime | INDEX |
| `sent_at` | DateTime | — |
| `delivered_at` | DateTime | — |
| `read_at` | DateTime | — |
| `failed_at` | DateTime | — |
| `created_by` | String(255) | NOT NULL |
| `created_at` | DateTime | INDEX, default=datetime.utcnow |
| `updated_at` | DateTime | default=datetime.utcnow |
| `extra_data` | JSON | default=dict |
| `Features` | String | PK, default=lambda: str(uuid.uuid4( |

---

## ml_model_registry
**Arquivo:** `lia-agent-system/libs/models/lia_models/ml_model_registry.py`

### `ml_model_registry`
**Classe:** `MLModelRegistryRecord` | **Herda:** `Base` | **Uso:** Routers/Services: 1 | Total refs: 2

| Campo | Tipo | Restrições |
|-------|------|------------|
| `model_id` | String(64) | NOT NULL, UNIQUE |
| `name` | String(100) | NOT NULL |
| `version` | String(20) | NOT NULL |
| `description` | String(500) | — |
| `model_path` | String(500) | — |
| `created_by` | String(100) | NOT NULL, default="system" |
| `is_default` | Boolean | NOT NULL, default=False |
| `metrics` | JSON | — |
| `parameters` | JSON | — |
| `features` | JSON | — |
| `predictions_count` | Integer | NOT NULL, default=0 |
| `correct_predictions` | Integer | NOT NULL, default=0 |
| `total_error` | Float | NOT NULL, default=0.0 |
| `training_samples` | Integer | — |
| `company_id` | String(36) | — |
| `id` | UUID | PK, default=uuid.uuid4 |
| `status` | String(20) | NOT NULL, default="active" |
| `last_evaluated` | DateTime | — |
| `created_at` | DateTime | NOT NULL, default=datetime.utcnow |
| `updated_at` | DateTime | NOT NULL, default=datetime.utcnow |

---

## notification_service
**Arquivo:** `lia-agent-system/libs/messaging/lia_messaging/notification_service.py`

### `chat_notifications`
**Classe:** `ChatNotification` | **Herda:** `Base` | **Uso:** Routers/Services: 1 | Total refs: 1

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | String | PK, default=lambda: str(uuid.uuid4( |
| `user_id` | String | NOT NULL |
| `thread_id` | String | — |
| `title` | String(255) | NOT NULL |
| `message` | Text | NOT NULL |
| `notification_type` | String(50) | default="info" |
| `proactive_type` | String(50) | — |
| `priority` | String(20) | default="normal" |
| `related_job_id` | String | — |
| `related_candidate_id` | String | — |
| `suggested_actions` | JSON | default=list |
| `extra_data` | JSON | default=dict |
| `is_delivered` | Boolean | default=False |
| `delivered_at` | DateTime | — |
| `created_at` | DateTime | default=datetime.utcnow |

### `notifications`
**Classe:** `Notification` | **Herda:** `Base` | **Uso:** Routers/Services: 20 | Total refs: 26

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | String | PK, default=lambda: str(uuid.uuid4( |
| `user_id` | String | NOT NULL |
| `title` | String(255) | NOT NULL |
| `message` | Text | — |
| `notification_type` | String(50) | default="info" |
| `proactive_type` | String(50) | — |
| `category` | String(50) | — |
| `priority` | String(20) | default="normal" |
| `source_agent` | String(50) | — |
| `source_trigger` | String(100) | — |
| `related_job_id` | String | — |
| `related_candidate_id` | String | — |
| `related_task_id` | String | — |
| `action_url` | String(500) | — |
| `action_label` | String(100) | — |
| `is_read` | Boolean | default=False |
| `read_at` | DateTime | — |
| `is_dismissed` | Boolean | default=False |
| `dismissed_at` | DateTime | — |
| `channels` | JSON | default=list |
| `channels_sent` | JSON | default=list |
| `extra_data` | JSON | default=dict |
| `created_at` | DateTime | default=datetime.utcnow |
| `expires_at` | DateTime | — |

---

## observability
**Arquivo:** `lia-agent-system/libs/models/lia_models/observability.py`

### `ai_inference_logs`
**Classe:** `AIInferenceLog` | **Herda:** `Base` | **Uso:** Routers/Services: 3 | Total refs: 5

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `company_id` | UUID | NOT NULL, INDEX |
| `agent_type` | String(50) | NOT NULL, INDEX |
| `candidate_id` | UUID | INDEX |
| `vacancy_id` | UUID | INDEX |
| `model_version` | String(20) | — |
| `input_hash` | String(64) | — |
| `input_preview` | Text | — |
| `output_summary` | JSON | default=dict |
| `decision_type` | String(50) | — |
| `confidence_score` | Numeric(5, 4) | — |
| `latency_ms` | Integer | — |
| `tokens_used` | Integer | — |
| `human_override` | Boolean | default=False |
| `override_reason` | Text | — |
| `override_by` | UUID | — |
| `feature_attributions` | JSON | default=dict |
| `bias_flags` | JSON | default=list |
| `created_at` | DateTime | INDEX, default=func.now(, server_default |

### `automated_decision_explanations`
**Classe:** `AutomatedDecisionExplanation` | **Herda:** `Base` | **Uso:** Routers/Services: 1 | Total refs: 1

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `company_id` | UUID | NOT NULL, INDEX |
| `decision_type` | String(50) | NOT NULL, INDEX |
| `candidate_id` | UUID | INDEX |
| `vacancy_id` | UUID | INDEX |
| `ai_model_used` | String(100) | — |
| `input_criteria` | JSON | default=dict |
| `decision_criteria` | JSON | default=dict |
| `explanation_text` | Text | — |
| `explanation_requested_at` | DateTime | — |
| `explanation_provided_at` | DateTime | — |
| `human_review_requested` | Boolean | default=False |
| `human_review_completed_at` | DateTime | — |
| `human_review_decision` | Text | — |
| `human_reviewer_id` | UUID | — |
| `created_at` | DateTime | INDEX, default=func.now(, server_default |

### `bias_audit_reports`
**Classe:** `BiasAuditReport` | **Herda:** `Base` | **Uso:** Routers/Services: 5 | Total refs: 5

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `company_id` | UUID | NOT NULL, INDEX |
| `audit_type` | String(20) | NOT NULL, INDEX |
| `audit_date` | Date | NOT NULL, INDEX |
| `sample_size` | Integer | — |
| `auditor` | String(20) | NOT NULL |
| `auditor_name` | String(255) | — |
| `auditor_organization` | String(255) | — |
| `bias_results` | JSON | NOT NULL, default=dict |
| `overall_score` | Numeric(5, 2) | — |
| `clear_count` | Integer | default=0 |
| `consider_count` | Integer | default=0 |
| `concern_count` | Integer | default=0 |
| `compliance_frameworks` | String | default=list |
| `report_url` | String(500) | — |
| `is_public` | Boolean | default=False |
| `notes` | Text | — |
| `recommendations` | String | default=list |
| `created_by` | UUID | — |
| `created_at` | DateTime | INDEX, default=func.now(, server_default |
| `updated_at` | DateTime | default=func.now(, server_default |

### `breach_notifications`
**Classe:** `BreachNotification` | **Herda:** `Base` | **Uso:** Routers/Services: 1 | Total refs: 1

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `company_id` | UUID | NOT NULL, INDEX |
| `breach_detected_at` | DateTime | NOT NULL |
| `breach_description` | Text | NOT NULL |
| `affected_data_types` | String | default=list |
| `affected_count` | Integer | — |
| `severity` | String(20) | NOT NULL, INDEX, default="medium" |
| `notification_sent_to_anpd` | Boolean | default=False |
| `anpd_notification_at` | DateTime | — |
| `notification_sent_to_subjects` | Boolean | default=False |
| `subjects_notification_at` | DateTime | — |
| `remediation_actions` | String | default=list |
| `status` | String(20) | NOT NULL, INDEX, default="detected" |
| `created_by` | UUID | — |
| `created_at` | DateTime | INDEX, default=func.now(, server_default |
| `updated_at` | DateTime | default=func.now(, server_default |
| `resolved_at` | DateTime | — |

### `company_compliance_controls`
**Classe:** `CompanyComplianceControl` | **Herda:** `Base` | **Uso:** Routers/Services: 1 | Total refs: 1

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `company_id` | UUID | NOT NULL, INDEX |
| `control_library_id` | UUID | NOT NULL, INDEX |
| `status` | String(30) | NOT NULL, INDEX, default="not_started" |
| `implementation_date` | Date | — |
| `last_review_date` | Date | — |
| `next_review_date` | Date | — |
| `owner_name` | String(255) | — |
| `owner_email` | String(255) | — |
| `notes` | Text | — |
| `evidence_files` | JSON | default=list |
| `effectiveness_rating` | Integer | — |
| `auditor_notes` | Text | — |
| `created_at` | DateTime | INDEX, default=func.now(, server_default |
| `updated_at` | DateTime | default=func.now(, server_default |

### `compliance_audits`
**Classe:** `ComplianceAudit` | **Herda:** `Base` | **Uso:** Routers/Services: 1 | Total refs: 1

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `company_id` | UUID | NOT NULL, INDEX |
| `framework` | String(50) | NOT NULL, INDEX |
| `audit_type` | String(30) | NOT NULL, INDEX |
| `auditor_organization` | String(255) | — |
| `auditor_name` | String(255) | — |
| `audit_start_date` | Date | — |
| `audit_end_date` | Date | — |
| `scope_description` | Text | — |
| `findings_count` | Integer | default=0 |
| `critical_findings` | Integer | default=0 |
| `high_findings` | Integer | default=0 |
| `medium_findings` | Integer | default=0 |
| `low_findings` | Integer | default=0 |
| `overall_result` | String(30) | — |
| `certificate_url` | String(500) | — |
| `report_url` | String(500) | — |
| `valid_until` | Date | — |
| `created_at` | DateTime | INDEX, default=func.now(, server_default |

### `compliance_control_library`
**Classe:** `ComplianceControlLibrary` | **Herda:** `Base` | **Uso:** Routers/Services: 3 | Total refs: 3

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `framework` | String(50) | NOT NULL, INDEX |
| `control_id` | String(50) | NOT NULL, INDEX |
| `control_name` | String(500) | NOT NULL |
| `control_description` | Text | — |
| `control_category` | String(100) | INDEX |
| `domain` | String(100) | — |
| `is_mandatory` | Boolean | default=True |
| `implementation_guidance` | Text | — |
| `evidence_requirements` | JSON | default=list |
| `related_controls` | JSON | default=list |
| `created_at` | DateTime | INDEX, default=func.now(, server_default |

### `compliance_controls`
**Classe:** `ComplianceControl` | **Herda:** `Base` | **Uso:** Routers/Services: 3 | Total refs: 5

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `company_id` | UUID | INDEX |
| `framework` | String(50) | NOT NULL, INDEX |
| `control_id` | String(50) | NOT NULL, INDEX |
| `control_name` | String(255) | NOT NULL |
| `description` | Text | — |
| `status` | String(20) | NOT NULL, default="not_implemented" |
| `evidence_url` | String(500) | — |
| `evidence_notes` | Text | — |
| `last_reviewed_at` | DateTime | — |
| `next_review_at` | DateTime | — |
| `reviewed_by` | UUID | — |
| `owner` | String(255) | — |
| `owner_email` | String(255) | — |
| `risk_level` | String(20) | — |
| `priority` | Integer | default=0 |
| `created_at` | DateTime | INDEX, default=func.now(, server_default |
| `updated_at` | DateTime | default=func.now(, server_default |

### `consent_events`
**Classe:** `ConsentEvent` | **Herda:** `Base` | **Uso:** Routers/Services: 4 | Total refs: 8

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `company_id` | UUID | NOT NULL, INDEX |
| `consent_version_id` | UUID | NOT NULL, INDEX |
| `subject_id` | UUID | INDEX |
| `subject_email` | String(255) | NOT NULL, INDEX |
| `subject_identifier` | String(50) | NOT NULL, INDEX |
| `event_type` | String(20) | NOT NULL, INDEX |
| `consent_given` | Boolean | NOT NULL |
| `ip_address` | String(45) | — |
| `user_agent` | String(500) | — |
| `device_info` | JSON | default=dict |
| `location_country` | String(100) | — |
| `channel` | String(50) | NOT NULL, default="web" |
| `proof_hash` | String(64) | NOT NULL, INDEX |
| `expires_at` | DateTime | INDEX |
| `created_at` | DateTime | INDEX, default=func.now(, server_default |

### `consent_records`
**Classe:** `ConsentRecord` | **Herda:** `Base` | **Uso:** Routers/Services: 2 | Total refs: 4

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `company_id` | UUID | NOT NULL, INDEX |
| `candidate_id` | UUID | NOT NULL, INDEX |
| `consent_type` | String(50) | NOT NULL, INDEX |
| `version` | String(10) | — |
| `granted_at` | DateTime | NOT NULL |
| `expires_at` | DateTime | — |
| `revoked_at` | DateTime | — |
| `ip_address` | String(45) | — |
| `source` | String(50) | — |
| `legal_basis` | String(50) | — |
| `consent_text` | Text | — |
| `is_active` | Boolean | default=True |
| `created_at` | DateTime | INDEX, default=func.now(, server_default |

### `consent_versions`
**Classe:** `ConsentVersion` | **Herda:** `Base` | **Uso:** Routers/Services: 2 | Total refs: 5

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `company_id` | UUID | NOT NULL, INDEX |
| `consent_type` | String(50) | NOT NULL, INDEX |
| `version` | String(20) | NOT NULL |
| `title` | String(500) | NOT NULL |
| `content_html` | Text | NOT NULL |
| `content_text` | Text | NOT NULL |
| `hash` | String(64) | NOT NULL, INDEX |
| `effective_from` | DateTime | NOT NULL, INDEX |
| `effective_until` | DateTime | — |
| `is_current` | Boolean | INDEX, default=True |
| `requires_explicit_consent` | Boolean | default=True |
| `renewal_period_days` | Integer | — |
| `created_by` | UUID | — |
| `created_at` | DateTime | INDEX, default=func.now(, server_default |
| `updated_at` | DateTime | default=func.now(, server_default |

### `data_access_logs`
**Classe:** `DataAccessLog` | **Herda:** `Base` | **Uso:** Routers/Services: 1 | Total refs: 3

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `company_id` | UUID | NOT NULL, INDEX |
| `user_id` | UUID | NOT NULL, INDEX |
| `data_subject_id` | UUID | INDEX |
| `data_type` | String(50) | NOT NULL |
| `operation` | String(20) | NOT NULL |
| `pii_fields` | String | default=list |
| `purpose` | String(100) | — |
| `legal_basis` | String(50) | — |
| `ip_address` | String(45) | — |
| `user_agent` | String(500) | — |
| `created_at` | DateTime | INDEX, default=func.now(, server_default |

### `data_subject_requests`
**Classe:** `DataSubjectRequest` | **Herda:** `Base` | **Uso:** Routers/Services: 1 | Total refs: 3

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `company_id` | UUID | NOT NULL, INDEX |
| `request_type` | String(20) | NOT NULL, INDEX |
| `status` | String(20) | NOT NULL, INDEX, default="pending" |
| `subject_name` | String(255) | NOT NULL |
| `subject_email` | String(255) | NOT NULL, INDEX |
| `subject_phone` | String(50) | — |
| `subject_identifier` | String(50) | NOT NULL, INDEX |
| `identity_verified` | Boolean | default=False |
| `identity_verification_method` | String(50) | — |
| `identity_verified_at` | DateTime | — |
| `description` | Text | NOT NULL |
| `response` | Text | — |
| `data_categories` | String | default=list |
| `legal_basis` | String(50) | — |
| `assigned_to` | UUID | INDEX |
| `sla_deadline` | DateTime | NOT NULL |
| `sla_met` | Boolean | — |
| `completed_at` | DateTime | — |
| `rejection_reason` | Text | — |
| `evidence_files` | JSON | default=list |
| `audit_trail` | JSON | default=list |
| `source_channel` | String(20) | NOT NULL, default="portal" |
| `created_at` | DateTime | INDEX, default=func.now(, server_default |
| `updated_at` | DateTime | default=func.now(, server_default |
| `SLA` | UUID | PK, default=uuid.uuid4 |

### `dpo_registry`
**Classe:** `DPORegistry` | **Herda:** `Base` | **Uso:** Routers/Services: 1 | Total refs: 1

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `company_id` | UUID | NOT NULL, UNIQUE, INDEX |
| `dpo_name` | String(255) | NOT NULL |
| `dpo_email` | String(255) | NOT NULL |
| `dpo_phone` | String(50) | — |
| `appointment_date` | Date | NOT NULL |
| `is_active` | Boolean | default=True |
| `public_contact_url` | String(500) | — |
| `created_at` | DateTime | INDEX, default=func.now(, server_default |
| `updated_at` | DateTime | default=func.now(, server_default |

### `incident_reports`
**Classe:** `IncidentReport` | **Herda:** `Base` | **Uso:** Routers/Services: 2 | Total refs: 4

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `company_id` | UUID | INDEX |
| `incident_type` | String(50) | NOT NULL, INDEX |
| `severity` | String(20) | NOT NULL, INDEX |
| `description` | Text | NOT NULL |
| `affected_resources` | JSON | default=list |
| `detected_at` | DateTime | NOT NULL |
| `resolved_at` | DateTime | — |
| `root_cause` | Text | — |
| `remediation_actions` | String | default=list |
| `notified_parties` | String | default=list |
| `created_by` | UUID | — |
| `assigned_to` | UUID | — |
| `status` | String(20) | INDEX, default="open" |
| `created_at` | DateTime | INDEX, default=func.now(, server_default |
| `updated_at` | DateTime | default=func.now(, server_default |

### `model_evaluations`
**Classe:** `ModelEvaluation` | **Herda:** `Base` | **Uso:** Routers/Services: 1 | Total refs: 3

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `company_id` | UUID | INDEX |
| `model_version` | String(20) | NOT NULL, INDEX |
| `evaluation_type` | String(50) | NOT NULL, INDEX |
| `dimension` | String(50) | — |
| `metric_name` | String(50) | NOT NULL |
| `metric_value` | Numeric(10, 6) | — |
| `threshold` | Numeric(10, 6) | — |
| `passed` | Boolean | — |
| `sample_size` | Integer | — |
| `confidence_interval` | JSON | — |
| `evaluation_date` | Date | NOT NULL |
| `evaluated_by` | UUID | — |
| `details` | JSON | default=dict |
| `recommendations` | String | default=list |
| `created_at` | DateTime | INDEX, default=func.now(, server_default |

### `sox_controls`
**Classe:** `SOXControl` | **Herda:** `Base` | **Uso:** Routers/Services: 1 | Total refs: 1

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `company_id` | UUID | NOT NULL, INDEX |
| `section` | String(10) | NOT NULL, INDEX |
| `control_id` | String(50) | NOT NULL, INDEX |
| `control_name` | String(500) | NOT NULL |
| `control_objective` | Text | — |
| `key_control` | Boolean | default=False |
| `frequency` | String(20) | — |
| `control_owner` | String(255) | — |
| `last_test_date` | Date | — |
| `test_result` | String(20) | default="not_tested" |
| `test_evidence` | Text | — |
| `remediation_plan` | Text | — |
| `remediation_due_date` | Date | — |
| `segregation_of_duties_verified` | Boolean | default=False |
| `audit_trail_enabled` | Boolean | default=False |
| `created_at` | DateTime | INDEX, default=func.now(, server_default |
| `updated_at` | DateTime | default=func.now(, server_default |

---

## pipeline_template
**Arquivo:** `lia-agent-system/libs/models/lia_models/pipeline_template.py`

### `pipeline_templates`
**Classe:** `PipelineTemplate` | **Herda:** `Base` | **Uso:** Routers/Services: 3 | Total refs: 5

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `company_id` | String(255) | NOT NULL, INDEX |
| `name` | String(255) | NOT NULL |
| `description` | Text | — |
| `stages` | JSON | default=list |
| `is_default` | Boolean | default=False |
| `is_active` | Boolean | default=True |
| `usage_count` | Integer | default=0 |
| `created_by` | String(255) | — |
| `created_at` | DateTime | INDEX, default=datetime.utcnow |
| `updated_at` | DateTime | default=datetime.utcnow |

---

## planned_task
**Arquivo:** `lia-agent-system/libs/models/lia_models/planned_task.py`

### `execution_plans`
**Classe:** `ExecutionPlan` | **Herda:** `Base` | **Uso:** Routers/Services: 1 | Total refs: 11

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | String | PK, default=lambda: str(uuid.uuid4( |
| `name` | String(255) | NOT NULL |
| `description` | Text | — |
| `goal_id` | String | — |
| `root_task_id` | String | FK → planned_tasks.id |
| `task_ids` | String | default=list |
| `execution_levels` | JSON | default=list |
| `total_estimated_duration` | Integer | — |
| `parallel_execution_time` | Integer | — |
| `status` | String(50) | default="pending" |
| `company_id` | String | — |
| `created_by` | String | — |
| `plan_metadata` | JSON | default=dict |
| `created_at` | DateTime | default=datetime.utcnow |
| `updated_at` | DateTime | default=datetime.utcnow |

### `planned_tasks`
**Classe:** `PlannedTask` | **Herda:** `Base` | **Uso:** Routers/Services: 1 | Total refs: 4

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | String | PK, default=lambda: str(uuid.uuid4( |
| `title` | String(500) | NOT NULL |
| `description` | Text | — |
| `agent_type` | String(50) | — |
| `priority` | Enum(PlannedTaskPriority) | default=PlannedTaskPriority.MEDIUM |
| `priority_score` | Float | default=0.0 |
| `status` | Enum(PlannedTaskStatus) | default=PlannedTaskStatus.PENDING |
| `parent_task_id` | String | FK → planned_tasks.id |
| `dependencies` | String | default=list |
| `estimated_duration` | Integer | — |
| `actual_duration` | Integer | — |
| `deadline` | DateTime | — |
| `execution_level` | Integer | default=0 |
| `goal_id` | String | — |
| `goal_criticality` | Float | default=0.5 |
| `related_job_id` | String | — |
| `related_candidate_id` | String | — |
| `company_id` | String | — |
| `context` | JSON | default=dict |
| `result` | JSON | — |
| `error_message` | Text | — |
| `chain_of_thought` | JSON | default=list |
| `created_by` | String | — |
| `assigned_to_user_id` | String | — |
| `started_at` | DateTime | — |
| `completed_at` | DateTime | — |
| `created_at` | DateTime | default=datetime.utcnow |
| `updated_at` | DateTime | default=datetime.utcnow |
| `Supports` | String | PK, default=lambda: str(uuid.uuid4( |

---

## policy
**Arquivo:** `lia-agent-system/libs/models/lia_models/policy.py`

### `business_rules`
**Classe:** `BusinessRule` | **Herda:** `Base` | **Uso:** Routers/Services: 4 | Total refs: 6

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `company_id` | UUID | INDEX |
| `name` | String(255) | NOT NULL |
| `description` | Text | — |
| `rule_type` | String(50) | NOT NULL, default="allow" |
| `conditions` | JSON | NOT NULL, default={} |
| `actions` | String | NOT NULL, default=[] |
| `priority` | Integer | NOT NULL, default=100 |
| `approval_config` | JSON | — |
| `is_active` | Boolean | INDEX, default=True |
| `rule_metadata` | JSON | — |
| `created_at` | DateTime | default=func.now(, server_default |
| `updated_at` | DateTime | default=func.now(, server_default |
| `created_by` | UUID | — |

### `escalation_logs`
**Classe:** `EscalationLog` | **Herda:** `Base` | **Uso:** Routers/Services: 2 | Total refs: 4

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `company_id` | UUID | INDEX |
| `escalation_rule_id` | UUID | FK → escalation_rules.id |
| `trigger_reason` | Text | NOT NULL |
| `trigger_context` | JSON | — |
| `action_taken` | String(50) | NOT NULL |
| `action_result` | JSON | — |
| `escalated_to` | String | default=[] |
| `notification_sent` | Boolean | default=False |
| `resolved` | Boolean | default=False |
| `resolved_at` | DateTime | — |
| `resolved_by` | UUID | — |
| `resolution_notes` | Text | — |
| `created_at` | DateTime | INDEX, default=func.now(, server_default |

### `escalation_rules`
**Classe:** `EscalationRule` | **Herda:** `Base` | **Uso:** Routers/Services: 4 | Total refs: 6

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `company_id` | UUID | INDEX |
| `name` | String(255) | NOT NULL |
| `description` | Text | — |
| `trigger_type` | String(50) | NOT NULL |
| `condition` | JSON | NOT NULL, default={} |
| `escalate_to` | String | NOT NULL, default=[] |
| `escalation_action` | String(50) | NOT NULL, default="notify_manager" |
| `notification_template` | Text | — |
| `cooldown_seconds` | Integer | default=3600 |
| `last_triggered` | DateTime | — |
| `is_active` | Boolean | INDEX, default=True |
| `priority` | Integer | default=100 |
| `created_at` | DateTime | default=func.now(, server_default |
| `updated_at` | DateTime | default=func.now(, server_default |

### `policy_evaluation_logs`
**Classe:** `PolicyEvaluationLog` | **Herda:** `Base` | **Uso:** Routers/Services: 2 | Total refs: 4

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `company_id` | UUID | INDEX |
| `agent_name` | String(100) | — |
| `action` | String(255) | NOT NULL |
| `context` | JSON | — |
| `result` | String(50) | NOT NULL |
| `rules_evaluated` | JSON | default=[] |
| `matching_rule_id` | UUID | — |
| `matching_rule_name` | String(255) | — |
| `rate_limit_checked` | Boolean | default=False |
| `rate_limit_result` | Boolean | — |
| `escalation_triggered` | Boolean | default=False |
| `escalation_rule_id` | UUID | — |
| `evaluation_time_ms` | Float | — |
| `user_id` | UUID | — |
| `created_at` | DateTime | INDEX, default=func.now(, server_default |

### `rate_limit_counters`
**Classe:** `RateLimitCounter` | **Herda:** `Base` | **Uso:** Routers/Services: 1 | Total refs: 3

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `rule_id` | UUID | NOT NULL, INDEX, FK → rate_limit_rules.id |
| `target_key` | String(500) | NOT NULL, INDEX |
| `count` | Integer | default=0 |
| `window_start` | DateTime | NOT NULL |
| `window_end` | DateTime | NOT NULL |
| `created_at` | DateTime | default=func.now(, server_default |
| `updated_at` | DateTime | default=func.now(, server_default |

### `rate_limit_rules`
**Classe:** `RateLimitRule` | **Herda:** `Base` | **Uso:** Routers/Services: 3 | Total refs: 5

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `company_id` | UUID | INDEX |
| `name` | String(255) | NOT NULL |
| `description` | Text | — |
| `target_type` | String(50) | NOT NULL |
| `target_id` | String(255) | INDEX |
| `action_pattern` | String(255) | — |
| `limit_value` | Integer | NOT NULL |
| `window_seconds` | Integer | NOT NULL |
| `current_count` | Integer | default=0 |
| `window_start` | DateTime | — |
| `burst_limit` | Integer | — |
| `is_active` | Boolean | INDEX, default=True |
| `created_at` | DateTime | default=func.now(, server_default |
| `updated_at` | DateTime | default=func.now(, server_default |

---

## recruiter_profile
**Arquivo:** `lia-agent-system/libs/models/lia_models/recruiter_profile.py`

### `personalization_settings`
**Classe:** `PersonalizationSettings` | **Herda:** `Base` | **Uso:** Routers/Services: 1 | Total refs: 3

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `recruiter_id` | String(255) | NOT NULL, UNIQUE, INDEX |
| `enable_personalization` | Boolean | default=True |
| `use_correction_history` | Boolean | default=True |
| `use_preference_detection` | Boolean | default=True |
| `use_outcome_data` | Boolean | default=True |
| `show_confidence_indicators` | Boolean | default=True |
| `explain_suggestions` | Boolean | default=True |
| `auto_approve_high_confidence` | Boolean | default=True |
| `high_confidence_threshold` | Float | default=0.90 |
| `data_retention_months` | Integer | default=24 |
| `created_at` | DateTime | default=datetime.utcnow |
| `updated_at` | DateTime | default=datetime.utcnow |

### `profile_calculation_logs`
**Classe:** `ProfileCalculationLog` | **Herda:** `Base` | **Uso:** Routers/Services: 1 | Total refs: 3

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `recruiter_profile_id` | UUID | NOT NULL, INDEX |
| `trigger` | String(50) | NOT NULL |
| `jobs_analyzed` | Integer | default=0 |
| `corrections_analyzed` | Integer | default=0 |
| `outcomes_analyzed` | Integer | default=0 |
| `changes_detected` | JSON | default=list |
| `previous_profile_snapshot` | JSON | — |
| `new_profile_snapshot` | JSON | — |
| `calculated_at` | DateTime | default=datetime.utcnow |
| `calculation_time_ms` | Integer | — |

### `recruiter_field_preferences`
**Classe:** `RecruiterFieldPreference` | **Herda:** `Base` | **Uso:** Routers/Services: 2 | Total refs: 5

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `recruiter_id` | String(255) | NOT NULL, INDEX |
| `recruiter_profile_id` | UUID | — |
| `company_id` | String(255) | INDEX |
| `field_name` | String(100) | NOT NULL |
| `correction_count` | Integer | default=0 |
| `total_encounters` | Integer | default=0 |
| `correction_rate` | Float | default=0.0 |
| `typical_corrections` | JSON | default=list |
| `preferred_values` | JSON | default=list |
| `value_range` | JSON | — |
| `custom_threshold` | Float | — |
| `always_ask` | Boolean | default=False |
| `remind_me_empty_field` | Boolean | default=True |
| `last_reminded_at` | DateTime | — |
| `snooze_until` | DateTime | — |
| `times_reminded` | Integer | default=0 |
| `times_filled_with_lia` | Integer | default=0 |
| `last_reminder_action` | String(50) | — |
| `last_correction_at` | DateTime | — |
| `created_at` | DateTime | default=datetime.utcnow |
| `updated_at` | DateTime | default=datetime.utcnow |

### `recruiter_profiles`
**Classe:** `RecruiterProfile` | **Herda:** `Base` | **Uso:** Routers/Services: 3 | Total refs: 5

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `recruiter_id` | String(255) | NOT NULL, UNIQUE, INDEX |
| `company_id` | String(255) | NOT NULL, INDEX |
| `total_jobs_created` | Integer | default=0 |
| `total_corrections_made` | Integer | default=0 |
| `avg_completion_time_seconds` | Float | — |
| `preferred_seniorities` | JSON | default=list |
| `preferred_departments` | JSON | default=list |
| `correction_patterns` | JSON | default=dict |
| `confidence_threshold_adjustment` | Float | default=0.0 |
| `wizard_mode` | String(50) | — |
| `experience_level` | String(50) | — |
| `profile_version` | Integer | default=1 |
| `created_at` | DateTime | default=datetime.utcnow |
| `updated_at` | DateTime | default=datetime.utcnow |
| `last_activity_at` | DateTime | — |
| `Tracks` | UUID | PK, default=uuid.uuid4 |

---

## recruitment_campaign
**Arquivo:** `lia-agent-system/libs/models/lia_models/recruitment_campaign.py`

### `recruitment_campaigns`
**Classe:** `RecruitmentCampaign` | **Herda:** `Base` | **Uso:** Routers/Services: 2 | Total refs: 4

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `company_id` | String(64) | NOT NULL, INDEX |
| `created_by` | String(64) | NOT NULL |
| `name` | String(256) | NOT NULL |
| `description` | Text | — |
| `job_id` | String(64) | INDEX |
| `talent_pool_id` | String(64) | — |
| `status` | String(20) | NOT NULL, default=CampaignStatus.ACTIVE.value |
| `stages` | JSON | NOT NULL, default=list |
| `current_stage_index` | Integer | NOT NULL, default=0 |
| `automation_level` | String(20) | NOT NULL, default="semi" |
| `total_candidates` | Integer | default=0 |
| `candidates_screened` | Integer | default=0 |
| `candidates_contacted` | Integer | default=0 |
| `candidates_interviewed` | Integer | default=0 |
| `candidates_offered` | Integer | default=0 |
| `candidates_hired` | Integer | default=0 |
| `stage_history` | JSON | NOT NULL, default=list |
| `created_at` | DateTime | default=datetime.utcnow |
| `updated_at` | DateTime | default=datetime.utcnow |

---

## recruitment_email_template
**Arquivo:** `lia-agent-system/libs/models/lia_models/recruitment_email_template.py`

### `recruitment_email_templates`
**Classe:** `RecruitmentEmailTemplate` | **Herda:** `Base` | **Uso:** Routers/Services: 3 | Total refs: 4

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `company_id` | String(255) | INDEX |
| `stage_name` | String(50) | NOT NULL, INDEX |
| `template_type` | String(20) | NOT NULL, INDEX, default="candidate" |
| `name` | String(255) | NOT NULL |
| `description` | Text | — |
| `subject` | String(500) | NOT NULL |
| `body_html` | Text | NOT NULL |
| `body_text` | Text | — |
| `variables` | JSON | default=list |
| `is_active` | Boolean | INDEX, default=True |
| `is_default` | Boolean | INDEX, default=False |
| `is_system` | Boolean | INDEX, default=False |
| `version` | Integer | default=1 |
| `created_by` | String(255) | — |
| `created_at` | DateTime | INDEX, default=datetime.utcnow |
| `updated_at` | DateTime | default=datetime.utcnow |

---

## recruitment_journey
**Arquivo:** `lia-agent-system/libs/models/lia_models/recruitment_journey.py`

### `recruitment_automations`
**Classe:** `RecruitmentAutomation` | **Herda:** `Base` | **Uso:** Routers/Services: 2 | Total refs: 4

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `company_id` | UUID | NOT NULL, INDEX, FK → company_profiles.id |
| `name` | String(255) | NOT NULL |
| `description` | Text | — |
| `automation_type` | String(100) | NOT NULL |
| `trigger_event` | String(100) | NOT NULL |
| `trigger_conditions` | JSON | default=dict |
| `action_config` | JSON | default=dict |
| `is_enabled` | Boolean | default=True |
| `execution_count` | Integer | default=0 |
| `last_executed_at` | DateTime | — |
| `created_at` | DateTime | default=datetime.utcnow |
| `updated_at` | DateTime | default=datetime.utcnow |

### `recruitment_slas`
**Classe:** `RecruitmentSLA` | **Herda:** `Base` | **Uso:** Routers/Services: 2 | Total refs: 4

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `company_id` | UUID | NOT NULL, INDEX, FK → company_profiles.id |
| `name` | String(255) | NOT NULL |
| `description` | Text | — |
| `stage_id` | UUID | — |
| `stage_name` | String(100) | — |
| `target_days` | Integer | NOT NULL |
| `warning_days` | Integer | — |
| `critical_days` | Integer | — |
| `applies_to_job_types` | String | default=list |
| `applies_to_priority` | String | default=list |
| `warning_action` | JSON | default=dict |
| `critical_action` | JSON | default=dict |
| `is_active` | Boolean | default=True |
| `created_at` | DateTime | default=datetime.utcnow |
| `updated_at` | DateTime | default=datetime.utcnow |

### `recruitment_templates`
**Classe:** `RecruitmentTemplate` | **Herda:** `Base` | **Uso:** Routers/Services: 2 | Total refs: 4

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `company_id` | UUID | NOT NULL, INDEX, FK → company_profiles.id |
| `name` | String(255) | NOT NULL |
| `description` | Text | — |
| `template_type` | String(100) | default="technical" |
| `stages_config` | JSON | default=list |
| `required_fields` | String | default=list |
| `optional_fields` | String | default=list |
| `default_priority` | String(50) | default="normal" |
| `default_sla_days` | Integer | default=30 |
| `ai_screening_enabled` | Boolean | default=True |
| `ai_matching_enabled` | Boolean | default=True |
| `ai_config` | JSON | default=dict |
| `is_default` | Boolean | default=False |
| `is_active` | Boolean | default=True |
| `created_at` | DateTime | default=datetime.utcnow |
| `updated_at` | DateTime | default=datetime.utcnow |
| `created_by` | String(255) | — |

### `sla_violations`
**Classe:** `SLAViolation` | **Herda:** `Base` | **Uso:** Routers/Services: 1 | Total refs: 3

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `sla_id` | UUID | NOT NULL, INDEX, FK → recruitment_slas.id |
| `job_id` | UUID | NOT NULL, INDEX |
| `candidate_id` | UUID | INDEX |
| `company_id` | UUID | NOT NULL, INDEX |
| `violation_type` | String(50) | — |
| `stage_name` | String(100) | — |
| `days_elapsed` | Integer | — |
| `target_days` | Integer | — |
| `resolved` | Boolean | default=False |
| `resolved_at` | DateTime | — |
| `resolution_notes` | Text | — |
| `created_at` | DateTime | default=datetime.utcnow |

---

## recruitment_stages
**Arquivo:** `lia-agent-system/libs/models/lia_models/recruitment_stages.py`

### `ats_stage_mappings`
**Classe:** `ATSStageMapping` | **Herda:** `Base` | **Uso:** Routers/Services: 2 | Total refs: 5

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `company_id` | String(255) | NOT NULL, INDEX |
| `ats_type` | String(50) | NOT NULL, INDEX |
| `ats_stage_id` | String(255) | — |
| `ats_stage_name` | String(255) | NOT NULL |
| `ats_stage_order` | Integer | — |
| `wedotalent_stage_id` | UUID | NOT NULL, INDEX, FK → recruitment_stages.id |
| `wedotalent_sub_status_id` | UUID | FK → recruitment_sub_statuses.id |
| `mapping_direction` | String(20) | NOT NULL, default="both" |
| `is_default_for_sync` | Boolean | default=False |
| `ats_stage_group_id` | String(255) | — |
| `priority` | Integer | default=0 |
| `transformation_rules` | JSON | — |
| `is_active` | Boolean | default=True |
| `notes` | Text | — |
| `created_at` | DateTime | default=datetime.utcnow |
| `updated_at` | DateTime | default=datetime.utcnow |
| `created_by` | String(255) | — |
| `Supports` | UUID | PK, default=uuid.uuid4 |

### `candidate_stage_history`
**Classe:** `CandidateStageHistory` | **Herda:** `Base` | **Uso:** Routers/Services: 6 | Total refs: 9

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `vacancy_candidate_id` | UUID | NOT NULL, INDEX |
| `vacancy_id` | UUID | NOT NULL, INDEX |
| `candidate_id` | UUID | NOT NULL, INDEX |
| `company_id` | String(255) | NOT NULL, INDEX |
| `from_stage_id` | UUID | FK → recruitment_stages.id |
| `from_stage_name` | String(100) | — |
| `from_sub_status_id` | UUID | FK → recruitment_sub_statuses.id |
| `from_sub_status_name` | String(100) | — |
| `to_stage_id` | UUID | NOT NULL, FK → recruitment_stages.id |
| `to_stage_name` | String(100) | NOT NULL |
| `to_sub_status_id` | UUID | FK → recruitment_sub_statuses.id |
| `to_sub_status_name` | String(100) | — |
| `transition_type` | String(50) | NOT NULL, default="manual" |
| `triggered_by` | String(100) | NOT NULL |
| `triggered_by_user_id` | String(255) | — |
| `source_agent` | String(100) | — |
| `reason` | Text | — |
| `notes` | Text | — |
| `ats_sync_triggered` | Boolean | default=False |
| `ats_sync_result` | String(50) | — |
| `ats_sync_details` | JSON | — |
| `time_in_previous_stage_hours` | Float | — |
| `context` | JSON | default=lambda: {} |
| `created_at` | DateTime | INDEX, default=datetime.utcnow |

### `recruitment_stages`
**Classe:** `RecruitmentStage` | **Herda:** `Base` | **Uso:** Routers/Services: 7 | Total refs: 13

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `company_id` | String(255) | NOT NULL, INDEX |
| `name` | String(100) | NOT NULL |
| `display_name` | String(100) | NOT NULL |
| `description` | Text | — |
| `stage_order` | Integer | NOT NULL, default=0 |
| `color` | String(20) | — |
| `icon` | String(50) | — |
| `stage_type` | String(50) | NOT NULL, default="active" |
| `is_initial` | Boolean | default=False |
| `is_final` | Boolean | default=False |
| `is_rejection` | Boolean | default=False |
| `is_hired` | Boolean | default=False |
| `allowed_transitions` | JSON | default=lambda: [] |
| `auto_advance_rules` | JSON | — |
| `sla_hours` | Integer | — |
| `is_active` | Boolean | default=True |
| `is_system` | Boolean | default=False |
| `stage_category` | String(20) | NOT NULL, default="custom" |
| `action_behavior` | String(30) | NOT NULL, default="passive" |
| `default_channel` | String(30) | NOT NULL, default="email" |
| `stage_metadata` | JSON | default=lambda: {} |
| `created_at` | DateTime | default=datetime.utcnow |
| `updated_at` | DateTime | default=datetime.utcnow |
| `created_by` | String(255) | — |

### `recruitment_sub_statuses`
**Classe:** `RecruitmentSubStatus` | **Herda:** `Base` | **Uso:** Routers/Services: 2 | Total refs: 6

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `stage_id` | UUID | NOT NULL, INDEX, FK → recruitment_stages.id |
| `company_id` | String(255) | NOT NULL, INDEX |
| `name` | String(100) | NOT NULL |
| `display_name` | String(150) | NOT NULL |
| `description` | Text | — |
| `sub_status_order` | Integer | NOT NULL, default=0 |
| `color` | String(20) | — |
| `icon` | String(50) | — |
| `is_default` | Boolean | default=False |
| `is_waiting` | Boolean | default=False |
| `waiting_for` | String(100) | — |
| `sla_hours` | Integer | — |
| `auto_actions` | JSON | — |
| `is_active` | Boolean | default=True |
| `sub_status_metadata` | JSON | default=lambda: {} |
| `created_at` | DateTime | default=datetime.utcnow |
| `updated_at` | DateTime | default=datetime.utcnow |

### `screening_questions`
**Classe:** `ScreeningQuestion` | **Herda:** `Base` | **Uso:** Routers/Services: 8 | Total refs: 15

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `company_id` | String(255) | NOT NULL, INDEX |
| `question` | Text | NOT NULL |
| `question_type` | String(50) | NOT NULL, default="text" |
| `is_required` | Boolean | default=True |
| `order` | Integer | NOT NULL, default=0 |
| `is_default` | Boolean | default=False |
| `options` | JSON | default=lambda: [] |
| `is_active` | Boolean | default=True |
| `created_at` | DateTime | default=datetime.utcnow |
| `updated_at` | DateTime | default=datetime.utcnow |

---

## retention_policy
**Arquivo:** `lia-agent-system/libs/models/lia_models/retention_policy.py`

### `company_retention_policies`
**Classe:** `CompanyRetentionPolicy` | **Herda:** `Base` | **Uso:** Routers/Services: 1 | Total refs: 3

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | String(255) | PK |
| `retention_months` | Integer | NOT NULL, default=24 |
| `auto_anonymize` | Boolean | NOT NULL, default=False |
| `activated_at` | DateTime | — |
| `activated_by` | String(255) | — |
| `last_cleanup_at` | DateTime | — |
| `last_cleanup_count` | Integer | — |
| `Compliance` | String(255) | PK |
| `company_id` | String(255) | NOT NULL, UNIQUE, INDEX |
| `created_at` | DateTime | NOT NULL, default=func.now(, server_default |
| `updated_at` | DateTime | NOT NULL, default=func.now(, server_default |

---

## routing_feedback
**Arquivo:** `lia-agent-system/libs/models/lia_models/routing_feedback.py`

### `routing_feedback`
**Classe:** `RoutingFeedback` | **Herda:** `Base` | **Uso:** Routers/Services: 1 | Total refs: 4

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `company_id` | String(255) | NOT NULL, INDEX |
| `session_id` | String(255) | — |
| `corrected_at` | DateTime | default=datetime.utcnow |
| `message_hash` | String(64) | NOT NULL, default=datetime.utcnow |

---

## rubric
**Arquivo:** `lia-agent-system/libs/models/lia_models/rubric.py`

### `job_requirements`
**Classe:** `JobRequirement` | **Herda:** `Base` | **Uso:** Routers/Services: 16 | Total refs: 17

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `job_vacancy_id` | UUID | NOT NULL, INDEX, FK → job_vacancies.id |
| `requirement` | String(500) | NOT NULL |
| `description` | Text | — |
| `priority` | String(50) | NOT NULL, default=RequirementPriority.IMPORTANT.value |
| `created_at` | DateTime | default=datetime.utcnow |
| `updated_at` | DateTime | default=datetime.utcnow |
| `category` | String(100) | default=datetime.utcnow |

### `rubric_evaluations`
**Classe:** `RubricEvaluation` | **Herda:** `Base` | **Uso:** Routers/Services: 4 | Total refs: 5

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `candidate_id` | UUID | NOT NULL, INDEX, FK → candidates.id |
| `job_vacancy_id` | UUID | NOT NULL, INDEX, FK → job_vacancies.id |
| `strengths` | JSON | NOT NULL, default=list |
| `concerns` | JSON | NOT NULL, default=list |
| `reasoning` | Text | — |
| `evaluated_at` | DateTime | default=datetime.utcnow |
| `created_at` | DateTime | default=datetime.utcnow |
| `updated_at` | DateTime | default=datetime.utcnow |
| `score` | Float | NOT NULL, default=list |
| `evaluated_by` | String(100) | default=datetime.utcnow |

---

## saas_metrics
**Arquivo:** `lia-agent-system/libs/models/lia_models/saas_metrics.py`

### `client_health_metrics`
**Classe:** `ClientHealthMetrics` | **Herda:** `Base` | **Uso:** Routers/Services: 1 | Total refs: 2

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `client_id` | UUID | NOT NULL, INDEX, FK → client_accounts.id |
| `churn_risk` | String(20) | default=ChurnRisk.LOW.value |
| `health_score` | Integer | default=100 |
| `last_login` | DateTime | — |
| `days_since_login` | Integer | default=0 |
| `nps_score` | Integer | — |
| `csat_score` | Numeric(3, 2) | — |
| `support_tickets_open` | Integer | default=0 |
| `support_tickets_total` | Integer | default=0 |
| `avg_response_time_hours` | Numeric(8, 2) | — |
| `engagement_level` | String(20) | default=EngagementLevel.MEDIUM.value |
| `feature_adoption_rate` | Numeric(5, 2) | default=0 |
| `logins_last_30_days` | Integer | default=0 |
| `actions_last_30_days` | Integer | default=0 |
| `risk_factors` | Text | — |
| `created_at` | DateTime | INDEX, default=datetime.utcnow |
| `updated_at` | DateTime | default=datetime.utcnow |

### `client_saas_metrics`
**Classe:** `ClientSaasMetrics` | **Herda:** `Base` | **Uso:** Routers/Services: 1 | Total refs: 2

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `client_id` | UUID | NOT NULL, INDEX, FK → client_accounts.id |
| `mrr` | Numeric(12, 2) | NOT NULL, default=0 |
| `arr` | Numeric(14, 2) | NOT NULL, default=0 |
| `ltv` | Numeric(14, 2) | — |
| `cac` | Numeric(12, 2) | — |
| `payback_months` | Numeric(6, 2) | — |
| `contract_start` | Date | — |
| `contract_end` | Date | — |
| `plan_name` | String(100) | — |
| `billing_cycle` | String(20) | default=BillingCycle.MONTHLY.value |
| `discount_percent` | Numeric(5, 2) | default=0 |
| `currency` | String(10) | default="BRL" |
| `created_at` | DateTime | INDEX, default=datetime.utcnow |
| `updated_at` | DateTime | default=datetime.utcnow |

### `client_usage_metrics`
**Classe:** `ClientUsageMetrics` | **Herda:** `Base` | **Uso:** Routers/Services: 1 | Total refs: 2

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `client_id` | UUID | NOT NULL, INDEX, FK → client_accounts.id |
| `ai_credits_used` | Integer | default=0 |
| `ai_credits_limit` | Integer | default=1000 |
| `users_active` | Integer | default=0 |
| `users_limit` | Integer | default=10 |
| `jobs_active` | Integer | default=0 |
| `jobs_limit` | Integer | default=50 |
| `storage_used_mb` | Numeric(12, 2) | default=0 |
| `storage_limit_mb` | Numeric(12, 2) | default=5120 |
| `api_calls_month` | Integer | default=0 |
| `api_calls_limit` | Integer | default=10000 |
| `period_start` | Date | — |
| `period_end` | Date | — |
| `created_at` | DateTime | INDEX, default=datetime.utcnow |
| `updated_at` | DateTime | default=datetime.utcnow |

### `payment_history`
**Classe:** `PaymentHistory` | **Herda:** `Base` | **Uso:** Routers/Services: 2 | Total refs: 3

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `client_id` | UUID | NOT NULL, INDEX, FK → client_accounts.id |
| `date` | Date | NOT NULL, INDEX |
| `amount` | Numeric(12, 2) | NOT NULL |
| `currency` | String(10) | default="BRL" |
| `status` | String(20) | INDEX, default=PaymentStatus.PENDING.value |
| `method` | String(20) | default=PaymentMethod.CARD.value |
| `invoice_id` | String(255) | — |
| `external_transaction_id` | String(255) | — |
| `description` | Text | — |
| `notes` | Text | — |
| `failure_reason` | Text | — |
| `retry_count` | Integer | default=0 |
| `paid_at` | DateTime | — |
| `created_at` | DateTime | INDEX, default=datetime.utcnow |
| `updated_at` | DateTime | default=datetime.utcnow |

---

## screening
**Arquivo:** `lia-agent-system/libs/models/lia_models/screening.py`

### `screening_tasks`
**Classe:** `ScreeningTask` | **Herda:** `Base` | **Uso:** Routers/Services: 2 | Total refs: 4

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `candidate_id` | String(255) | NOT NULL, INDEX |
| `job_id` | String(255) | NOT NULL, INDEX |
| `company_id` | String(255) | NOT NULL, INDEX |
| `status` | String(50) | NOT NULL, INDEX, default="pending" |
| `source` | String(50) | NOT NULL |
| `resume_text` | Text | — |
| `resume_url` | String(1024) | — |
| `created_at` | DateTime | INDEX, default=datetime.utcnow |
| `updated_at` | DateTime | default=datetime.utcnow |

---

## screening_question
**Arquivo:** `lia-agent-system/libs/models/lia_models/screening_question.py`

### `company_screening_questions`
**Classe:** `CompanyScreeningQuestion` | **Herda:** `Base` | **Uso:** Routers/Services: 4 | Total refs: 6

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `company_id` | String(255) | NOT NULL, INDEX |
| `question_text` | Text | NOT NULL |
| `is_required` | Boolean | default=True |
| `is_eliminatory` | Boolean | default=False |
| `order` | Integer | default=0 |
| `is_active` | Boolean | default=True |
| `created_at` | DateTime | default=datetime.utcnow |
| `updated_at` | DateTime | default=datetime.utcnow |
| `question_type` | String(50) | default="text" |
| `expected_answer` | String(255) | default=0 |

---

## screening_question_set
**Arquivo:** `lia-agent-system/libs/models/lia_models/screening_question_set.py`

### `screening_question_sets`
**Classe:** `ScreeningQuestionSet` | **Herda:** `Base` | **Uso:** Routers/Services: 1 | Total refs: 2

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `job_vacancy_id` | String(255) | NOT NULL, INDEX |
| `version` | Integer | NOT NULL |
| `questions_hash` | String(64) | NOT NULL |
| `questions_snapshot` | JSON | NOT NULL |
| `questions_count` | Integer | NOT NULL |
| `block_distribution` | JSON | — |
| `extra_metadata` | JSON | — |
| `source` | String(50) | NOT NULL |
| `created_by` | String(255) | — |
| `is_active` | Boolean | default=True |
| `difficulty_coefficient` | Float | — |
| `created_at` | DateTime | INDEX, default=datetime.utcnow |
| `updated_at` | DateTime | default=datetime.utcnow |

---

## search_feedback
**Arquivo:** `lia-agent-system/libs/models/lia_models/search_feedback.py`

### `search_feedbacks`
**Classe:** `SearchFeedback` | **Herda:** `Base` | **Uso:** Routers/Services: 3 | Total refs: 5

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | String | PK, default=lambda: str(uuid.uuid4( |
| `candidate_id` | String | NOT NULL, INDEX |
| `job_id` | String | INDEX |
| `user_id` | String | NOT NULL, INDEX |
| `search_query` | String | — |
| `feedback_type` | String(20) | NOT NULL |
| `candidate_score` | Float | — |
| `candidate_name` | String(255) | — |
| `reason` | Text | — |
| `created_at` | DateTime | default=datetime.utcnow |
| `updated_at` | DateTime | default=datetime.utcnow |

---

## self_scheduling
**Arquivo:** `lia-agent-system/libs/models/lia_models/self_scheduling.py`

### `interview_reminders`
**Classe:** `InterviewReminder` | **Herda:** `Base` | **Uso:** Routers/Services: 0 | Total refs: 3

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `interview_id` | UUID | NOT NULL, INDEX |
| `reminder_type` | String(50) | NOT NULL |
| `recipient_email` | String(255) | NOT NULL |
| `recipient_type` | String(50) | NOT NULL |
| `scheduled_for` | DateTime | NOT NULL, INDEX |
| `hours_before` | Integer | NOT NULL |
| `status` | String(50) | INDEX, default="pending" |
| `sent_at` | DateTime | — |
| `send_error` | Text | — |
| `channels` | JSON | default=["email"] |
| `created_at` | DateTime | default=datetime.utcnow |

### `reschedule_history`
**Classe:** `RescheduleHistory` | **Herda:** `Base` | **Uso:** Routers/Services: 0 | Total refs: 3

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `interview_id` | UUID | NOT NULL, INDEX |
| `candidate_id` | UUID | INDEX |
| `job_vacancy_id` | UUID | — |
| `original_start_time` | DateTime | NOT NULL |
| `original_end_time` | DateTime | NOT NULL |
| `new_start_time` | DateTime | NOT NULL |
| `new_end_time` | DateTime | NOT NULL |
| `reason` | Text | — |
| `requested_by` | String(50) | NOT NULL |
| `reschedule_number` | Integer | default=1 |
| `created_at` | DateTime | default=datetime.utcnow |

### `self_scheduling_links`
**Classe:** `SelfSchedulingLink` | **Herda:** `Base` | **Uso:** Routers/Services: 1 | Total refs: 4

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `token` | String(64) | NOT NULL, UNIQUE, INDEX |
| `candidate_id` | UUID | — |
| `candidate_name` | String(255) | NOT NULL |
| `candidate_email` | String(255) | NOT NULL |
| `job_vacancy_id` | UUID | — |
| `job_title` | String(255) | — |
| `interviewer_emails` | JSON | default=[] |
| `organizer_email` | String(255) | — |
| `interview_type` | String(50) | default="hr" |
| `interview_mode` | String(50) | default="video" |
| `duration_minutes` | Integer | default=60 |
| `available_slots` | JSON | default=[] |
| `selected_slot` | JSON | — |
| `interview_id` | UUID | — |
| `status` | String(50) | INDEX, default="pending" |
| `expires_at` | DateTime | NOT NULL |
| `max_uses` | Integer | default=1 |
| `use_count` | Integer | default=0 |
| `notes` | Text | — |
| `extra_data` | JSON | default={} |
| `created_by` | String(255) | NOT NULL, default="system" |
| `created_at` | DateTime | INDEX, default=datetime.utcnow |
| `updated_at` | DateTime | default=datetime.utcnow |

---

## shared_search
**Arquivo:** `lia-agent-system/libs/models/lia_models/shared_search.py`

### `shared_search_access`
**Classe:** `SharedSearchAccess` | **Herda:** `Base` | **Uso:** Routers/Services: 3 | Total refs: 5

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `shared_search_id` | UUID | NOT NULL, INDEX, FK → shared_searches.id |
| `email` | String(255) | NOT NULL, INDEX |
| `name` | String(255) | — |
| `role` | String(50) | NOT NULL, default="hiring_manager" |
| `access_token` | String(255) | NOT NULL, UNIQUE, INDEX |
| `otp_hash` | String(255) | — |
| `otp_expires_at` | DateTime | — |
| `first_accessed_at` | DateTime | — |
| `last_accessed_at` | DateTime | — |
| `total_views` | Integer | NOT NULL, default=0 |
| `created_at` | DateTime | INDEX, default=datetime.utcnow |

### `shared_search_feedback`
**Classe:** `SharedSearchFeedback` | **Herda:** `Base` | **Uso:** Routers/Services: 2 | Total refs: 4

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `shared_search_id` | UUID | NOT NULL, INDEX, FK → shared_searches.id |
| `candidate_id` | UUID | NOT NULL, INDEX |
| `reviewer_email` | String(255) | NOT NULL, INDEX |
| `decision` | Enum(FeedbackDecision) | NOT NULL |
| `rating` | Integer | — |
| `comment` | Text | — |
| `created_at` | DateTime | INDEX, default=datetime.utcnow |
| `updated_at` | DateTime | default=datetime.utcnow |

### `shared_searches`
**Classe:** `SharedSearch` | **Herda:** `Base` | **Uso:** Routers/Services: 3 | Total refs: 5

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `company_id` | UUID | NOT NULL, INDEX |
| `created_by_user_id` | UUID | NOT NULL, INDEX |
| `share_type` | Enum(ShareType) | NOT NULL, default=ShareType.search |
| `source_query` | Text | — |
| `source_list_id` | UUID | INDEX |
| `title` | String(255) | NOT NULL |
| `description` | Text | — |
| `expires_at` | DateTime | INDEX |
| `status` | Enum(SharedSearchStatus) | NOT NULL, INDEX, default=SharedSearchStatus.active |
| `snapshot_payload` | JSON | NOT NULL, default=dict |
| `can_comment` | Boolean | NOT NULL, default="true", server_default |
| `can_rate` | Boolean | NOT NULL, default="true", server_default |
| `created_at` | DateTime | INDEX, default=datetime.utcnow |
| `updated_at` | DateTime | default=datetime.utcnow |

---

## skills_catalog
**Arquivo:** `lia-agent-system/libs/models/lia_models/skills_catalog.py`

### `behavioral_competencies_catalog`
**Classe:** `BehavioralCompetencyCatalog` | **Herda:** `Base` | **Uso:** Routers/Services: 1 | Total refs: 2

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `company_id` | String(255) | NOT NULL, INDEX |
| `name` | String(255) | NOT NULL |
| `description` | Text | — |
| `justification` | Text | — |
| `default_weight` | Integer | default=3 |
| `category` | String(100) | — |
| `usage_count` | Integer | default=0 |
| `acceptance_rate` | Float | default=0.0 |
| `last_used_at` | DateTime | — |
| `wsi_questions` | JSON | default=[] |
| `evaluation_criteria` | JSON | default={} |
| `source` | String(50) | default="manual" |
| `is_active` | Boolean | default=True |
| `created_at` | DateTime | default=datetime.utcnow |
| `updated_at` | DateTime | default=datetime.utcnow |
| `created_by` | String(255) | — |

### `company_skills_catalog`
**Classe:** `CompanySkillsCatalog` | **Herda:** `Base` | **Uso:** Routers/Services: 2 | Total refs: 3

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `company_id` | String(255) | NOT NULL, INDEX |
| `skill_name` | String(255) | NOT NULL |
| `category` | String(50) | NOT NULL |
| `subcategory` | String(100) | — |
| `default_weight` | Integer | default=3 |
| `default_level` | String(50) | default="Intermediário" |
| `is_required_default` | Boolean | default=False |
| `description` | Text | — |
| `aliases` | String | default=[] |
| `usage_count` | Integer | default=0 |
| `acceptance_rate` | Float | default=0.0 |
| `last_used_at` | DateTime | — |
| `source` | String(50) | default="manual" |
| `is_active` | Boolean | default=True |
| `created_at` | DateTime | default=datetime.utcnow |
| `updated_at` | DateTime | default=datetime.utcnow |
| `created_by` | String(255) | — |

### `skill_suggestion_patterns`
**Classe:** `SkillSuggestionPattern` | **Herda:** `Base` | **Uso:** Routers/Services: 2 | Total refs: 4

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `company_id` | String(255) | NOT NULL, INDEX |
| `pattern_type` | String(50) | NOT NULL |
| `context_key` | String(255) | NOT NULL |
| `skill_name` | String(255) | NOT NULL |
| `skill_category` | String(50) | — |
| `suggested_weight` | Integer | — |
| `suggested_level` | String(50) | — |
| `is_typically_required` | Boolean | default=False |
| `sample_size` | Integer | default=0 |
| `acceptance_rate` | Float | default=0.0 |
| `confidence_score` | Float | default=0.0 |
| `context_data` | JSON | default={} |
| `is_promoted` | Boolean | default=False |
| `last_computed_at` | DateTime | default=datetime.utcnow |
| `created_at` | DateTime | default=datetime.utcnow |
| `updated_at` | DateTime | default=datetime.utcnow |

### `skill_usage_analytics`
**Classe:** `SkillUsageAnalytics` | **Herda:** `Base` | **Uso:** Routers/Services: 2 | Total refs: 4

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `company_id` | String(255) | NOT NULL, INDEX |
| `skill_name` | String(255) | NOT NULL |
| `skill_type` | String(50) | NOT NULL |
| `category` | String(50) | — |
| `job_vacancy_id` | UUID | INDEX |
| `job_draft_id` | UUID | INDEX |
| `job_title` | String(255) | — |
| `department` | String(100) | — |
| `seniority` | String(50) | — |
| `source` | String(50) | NOT NULL |
| `outcome` | String(20) | NOT NULL |
| `original_weight` | Integer | — |
| `final_weight` | Integer | — |
| `original_level` | String(50) | — |
| `final_level` | String(50) | — |
| `was_required` | Boolean | — |
| `suggestion_confidence` | Float | — |
| `suggestion_reasoning` | Text | — |
| `created_at` | DateTime | default=datetime.utcnow |

---

## sourcing_agent
**Arquivo:** `lia-agent-system/libs/models/lia_models/sourcing_agent.py`

### `sourcing_agent_signals`
**Classe:** `SourcingAgentSignal` | **Herda:** `Base` | **Uso:** Routers/Services: 1 | Total refs: 2

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `agent_id` | UUID | NOT NULL, FK → sourcing_agents.id |
| `candidate_id` | String(64) | — |
| `reason` | Text | NOT NULL |
| `criteria_extracted` | String | default=list |
| `created_at` | DateTime | default=datetime.utcnow |
| `signal_type` | String(16) | NOT NULL |

### `sourcing_agents`
**Classe:** `SourcingAgent` | **Herda:** `Base` | **Uso:** Routers/Services: 8 | Total refs: 11

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `company_id` | String(64) | NOT NULL, INDEX |
| `job_id` | String(64) | — |
| `talent_pool_id` | UUID | — |
| `agent_template_id` | String(255) | FK → agent_templates.id |
| `agent_name` | String(256) | NOT NULL |
| `calibration_v` | Integer | NOT NULL, default=0 |
| `search_strategy` | JSON | NOT NULL, default=dict |
| `preferences` | JSON | NOT NULL, default=dict |
| `outreach_config` | JSON | NOT NULL, default=dict |
| `profiles_viewed` | Integer | default=0 |
| `profiles_approved` | Integer | default=0 |
| `profiles_rejected` | Integer | default=0 |
| `emails_sent` | Integer | default=0 |
| `created_at` | DateTime | default=datetime.utcnow |
| `updated_at` | DateTime | default=datetime.utcnow |
| `status` | String(16) | NOT NULL, default="active" |

---

## talent_pool
**Arquivo:** `lia-agent-system/libs/models/lia_models/talent_pool.py`

### `talent_pool_candidates`
**Classe:** `TalentPoolCandidate` | **Herda:** `Base` | **Uso:** Routers/Services: 1 | Total refs: 3

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `candidate_id` | Integer | NOT NULL, INDEX |
| `candidate_uuid` | UUID | INDEX |
| `fit_score` | Float | — |
| `screening_data` | JSON | default=dict |
| `match_criteria` | JSON | default=dict |
| `moved_to_job_id` | Integer | — |
| `moved_to_job_uuid` | UUID | INDEX |
| `moved_at` | DateTime | — |
| `moved_to_stage` | String | — |
| `notes` | Text | — |
| `created_at` | DateTime | default=func.now(, server_default |
| `updated_at` | DateTime | default=func.now(, server_default |
| `talent_pool_id` | UUID | NOT NULL, INDEX, FK → talent_pools.id |
| `stage` | String | NOT NULL, default="discovered" |

### `talent_pools`
**Classe:** `TalentPool` | **Herda:** `Base` | **Uso:** Routers/Services: 2 | Total refs: 5

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `company_id` | String | NOT NULL, INDEX |
| `name` | String | NOT NULL |
| `description` | Text | — |
| `status` | String | NOT NULL, default="active" |
| `archetype_id` | String | — |
| `screening_questions` | JSON | default=list |
| `screening_config` | JSON | default=dict |
| `agent_sourcing_enabled` | Boolean | default=False |
| `agent_config` | JSON | default=dict |
| `candidates_count` | Integer | default=0 |
| `screened_count` | Integer | default=0 |
| `ready_count` | Integer | default=0 |
| `created_at` | DateTime | default=func.now(, server_default |
| `updated_at` | DateTime | default=func.now(, server_default |

---

## task
**Arquivo:** `lia-agent-system/libs/models/lia_models/task.py`

### `task_templates`
**Classe:** `TaskTemplate` | **Herda:** `Base` | **Uso:** Routers/Services: 1 | Total refs: 4

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | String | PK, default=lambda: str(uuid.uuid4( |
| `name` | String(255) | NOT NULL |
| `description` | Text | — |
| `task_type` | Enum(TaskType) | default=TaskType.GENERAL |
| `default_priority` | Enum(TaskPriority) | default=TaskPriority.MEDIUM |
| `title_template` | String(255) | NOT NULL |
| `description_template` | Text | — |
| `default_due_days` | Integer | — |
| `assigned_agent` | String(50) | — |
| `is_active` | Boolean | default=True |
| `context_schema` | JSON | — |
| `created_at` | DateTime | default=datetime.utcnow |
| `updated_at` | DateTime | default=datetime.utcnow |

### `tasks`
**Classe:** `Task` | **Herda:** `Base` | **Uso:** Routers/Services: 32 | Total refs: 78

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | String | PK, default=lambda: str(uuid.uuid4( |
| `title` | String(255) | NOT NULL |
| `description` | Text | — |
| `task_type` | Enum(TaskType) | default=TaskType.GENERAL |
| `priority` | Enum(TaskPriority) | default=TaskPriority.MEDIUM |
| `status` | Enum(TaskStatus) | default=TaskStatus.PENDING |
| `created_by_agent` | String(50) | — |
| `assigned_to_agent` | String(50) | — |
| `assigned_to_user_id` | String | — |
| `related_job_id` | String | — |
| `related_candidate_id` | String | — |
| `due_date` | DateTime | — |
| `completed_at` | DateTime | — |
| `context` | JSON | default=dict |
| `result` | JSON | — |
| `error_message` | Text | — |
| `is_automated` | Boolean | default=False |
| `requires_confirmation` | Boolean | default=False |
| `reminder_sent` | Boolean | default=False |
| `reminder_count` | Integer | default=0 |
| `confirmed_by` | String | — |
| `confirmed_at` | DateTime | — |
| `rejected_by` | String | — |
| `rejected_at` | DateTime | — |
| `rejection_reason` | Text | — |
| `escalated_to` | String | — |
| `escalated_at` | DateTime | — |
| `escalation_reason` | Text | — |
| `escalation_level` | Integer | default=0 |
| `created_at` | DateTime | default=datetime.utcnow |
| `updated_at` | DateTime | default=datetime.utcnow |

---

## teams
**Arquivo:** `lia-agent-system/libs/models/lia_models/teams.py`

### `teams_action_audit_logs`
**Classe:** `TeamsActionAuditLog` | **Herda:** `Base` | **Uso:** Routers/Services: 2 | Total refs: 2

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | String(255) | PK |
| `source` | String(100) | default="teams_adaptive_card" |
| `actor_id` | String(255) | INDEX |
| `actor_name` | String(255) | — |
| `candidate_id` | String(255) | INDEX |
| `vacancy_id` | String(255) | INDEX |
| `company_id` | String(255) | INDEX |
| `details` | JSON | NOT NULL, default={} |
| `created_at` | DateTime | INDEX, default=datetime.utcnow |
| `action` | String(100) | NOT NULL, INDEX, default="teams_adaptive_card" |
| `result` | String(50) | NOT NULL, INDEX |

### `teams_conversations`
**Classe:** `TeamsConversation` | **Herda:** `Base` | **Uso:** Routers/Services: 4 | Total refs: 6

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `conversation_id` | String(255) | NOT NULL, UNIQUE, INDEX |
| `service_url` | String(500) | NOT NULL |
| `tenant_id` | String(255) | — |
| `channel_id` | String(255) | — |
| `user_id` | String(255) | NOT NULL, INDEX |
| `user_name` | String(255) | — |
| `user_aad_object_id` | String(255) | — |
| `conversation_reference` | JSON | NOT NULL |
| `internal_conversation_id` | UUID | — |
| `created_at` | DateTime | default=datetime.utcnow |
| `updated_at` | DateTime | default=datetime.utcnow |
| `last_message_at` | DateTime | — |
| `is_active` | Boolean | default=True |

### `teams_messages`
**Classe:** `TeamsMessage` | **Herda:** `Base` | **Uso:** Routers/Services: 2 | Total refs: 4

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `teams_conversation_id` | UUID | NOT NULL, INDEX |
| `activity_id` | String(255) | — |
| `text` | Text | — |
| `from_id` | String(255) | NOT NULL |
| `from_name` | String(255) | — |
| `activity_data` | JSON | — |
| `created_at` | DateTime | INDEX, default=datetime.utcnow |
| `message_type` | String(50) | NOT NULL |
| `direction` | String(20) | NOT NULL |

---

## technical_tests
**Arquivo:** `lia-agent-system/libs/models/lia_models/technical_tests.py`

### `client_test_configs`
**Classe:** `ClientTestConfig` | **Herda:** `Base` | **Uso:** Routers/Services: 2 | Total refs: 3

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `client_id` | UUID | NOT NULL, INDEX |
| `test_id` | UUID | NOT NULL, INDEX, FK → technical_tests.id |
| `is_enabled` | Boolean | default=True |
| `custom_time_limit` | Integer | — |
| `custom_passing_score` | Float | — |
| `custom_instructions` | Text | — |
| `custom_max_attempts` | Integer | — |
| `priority` | Integer | default=0 |
| `required_for_roles` | JSON | default=list |
| `created_at` | DateTime | default=datetime.utcnow |
| `updated_at` | DateTime | default=datetime.utcnow |

### `technical_tests`
**Classe:** `TechnicalTest` | **Herda:** `Base` | **Uso:** Routers/Services: 2 | Total refs: 3

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `name` | String(255) | NOT NULL |
| `category` | String(50) | NOT NULL, INDEX |
| `subcategory` | String(50) | INDEX |
| `description` | Text | — |
| `duration_minutes` | Integer | default=30 |
| `difficulty` | String(20) | INDEX, default=TestDifficulty.MEDIUM.value |
| `passing_score` | Float | default=70.0 |
| `max_attempts` | Integer | default=3 |
| `instructions` | Text | — |
| `questions_config` | JSON | default=dict |
| `is_global` | Boolean | INDEX, default=True |
| `is_active` | Boolean | INDEX, default=True |
| `created_by` | String(255) | — |
| `created_at` | DateTime | INDEX, default=datetime.utcnow |
| `updated_at` | DateTime | default=datetime.utcnow |

### `test_results`
**Classe:** `TestResult` | **Herda:** `Base` | **Uso:** Routers/Services: 1 | Total refs: 2

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `client_id` | UUID | NOT NULL, INDEX |
| `test_id` | UUID | NOT NULL, INDEX, FK → technical_tests.id |
| `candidate_id` | UUID | NOT NULL, INDEX |
| `started_at` | DateTime | NOT NULL, default=datetime.utcnow |
| `completed_at` | DateTime | — |
| `score` | Float | — |
| `passed` | Boolean | — |
| `attempt_number` | Integer | default=1 |
| `answers` | JSON | default=dict |
| `time_taken_seconds` | Integer | — |
| `feedback` | Text | — |
| `reviewed_by` | String(255) | — |
| `reviewed_at` | DateTime | — |
| `created_at` | DateTime | INDEX, default=datetime.utcnow |

---

## tenant_llm_config
**Arquivo:** `lia-agent-system/libs/models/lia_models/tenant_llm_config.py`

### `tenant_llm_configs`
**Classe:** `TenantLLMConfig` | **Herda:** `Base` | **Uso:** Routers/Services: 1 | Total refs: 2

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `company_id` | String(255) | NOT NULL, UNIQUE, INDEX |
| `fallback_order` | JSON | default=["gemini" |
| `providers` | JSON | default={} |
| `routing` | JSON | default={} |
| `config` | JSON | default={} |
| `is_active` | Boolean | default=True |
| `created_at` | DateTime | default=datetime.utcnow |
| `updated_at` | DateTime | default=datetime.utcnow |
| `created_by` | String(255) | — |
| `primary_provider` | String(50) | default="gemini" |

---

## triagem
**Arquivo:** `lia-agent-system/libs/models/lia_models/triagem.py`

### `triagem_messages`
**Classe:** `TriagemMessage` | **Herda:** `Base` | **Uso:** Routers/Services: 5 | Total refs: 7

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `session_id` | UUID | NOT NULL, INDEX |
| `sender` | String(20) | NOT NULL |
| `content` | Text | NOT NULL |
| `message_type` | String(50) | NOT NULL, default="text" |
| `wsi_block` | Integer | — |
| `wsi_question_id` | String(255) | — |
| `score` | Float | — |
| `audio_base64` | Text | — |
| `metadata_json` | JSON | default=dict |
| `created_at` | DateTime | INDEX, default=datetime.utcnow |

### `triagem_sessions`
**Classe:** `TriagemSession` | **Herda:** `Base` | **Uso:** Routers/Services: 5 | Total refs: 8

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `token` | String(255) | NOT NULL, UNIQUE, INDEX |
| `candidate_id` | String(255) | NOT NULL, INDEX |
| `candidate_name` | String(255) | — |
| `candidate_email` | String(255) | — |
| `job_id` | String(255) | NOT NULL, INDEX |
| `job_title` | String(500) | — |
| `company_id` | String(255) | NOT NULL, INDEX |
| `company_name` | String(255) | — |
| `company_logo_url` | String(1024) | — |
| `status` | String(50) | NOT NULL, INDEX, default="invited" |
| `current_block` | Integer | NOT NULL, default=0 |
| `total_blocks` | Integer | NOT NULL, default=7 |
| `wsi_final_score` | Float | — |
| `recommendation` | String(50) | — |
| `feedback_draft` | Text | — |
| `invite_channel` | String(50) | default="email" |
| `voice_mode` | Boolean | NOT NULL, default=False |
| `expires_at` | DateTime | NOT NULL |
| `started_at` | DateTime | — |
| `completed_at` | DateTime | — |
| `created_at` | DateTime | INDEX, default=datetime.utcnow |
| `updated_at` | DateTime | default=datetime.utcnow |
| `created_by` | String(255) | — |
| `metadata_json` | JSON | default=dict |

---

## trust_center
**Arquivo:** `lia-agent-system/libs/models/lia_models/trust_center.py`

### `trust_center_resources`
**Classe:** `TrustCenterResource` | **Herda:** `Base` | **Uso:** Routers/Services: 1 | Total refs: 2

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `company_id` | UUID | NOT NULL, INDEX |
| `title` | String(255) | NOT NULL |
| `description` | Text | — |
| `category` | String(50) | NOT NULL, default="other" |
| `file_url` | String(500) | NOT NULL |
| `is_public` | Boolean | default=True |
| `requires_nda` | Boolean | default=False |
| `download_count` | Integer | default=0 |
| `created_at` | DateTime | default=func.now(, server_default |

### `trust_center_settings`
**Classe:** `TrustCenterSettings` | **Herda:** `Base` | **Uso:** Routers/Services: 1 | Total refs: 2

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `company_id` | UUID | NOT NULL, UNIQUE, INDEX |
| `company_slug` | String(100) | NOT NULL, UNIQUE, INDEX |
| `company_name` | String(255) | NOT NULL |
| `company_description` | Text | — |
| `logo_url` | String(500) | — |
| `primary_color` | String(20) | default="#6366F1" |
| `is_public` | Boolean | default=False |
| `custom_domain` | String(255) | — |
| `show_certifications` | Boolean | default=True |
| `show_controls` | Boolean | default=True |
| `show_bias_audits` | Boolean | default=True |
| `show_subprocessors` | Boolean | default=True |
| `contact_email` | String(255) | — |
| `privacy_policy_url` | String(500) | — |
| `terms_url` | String(500) | — |
| `created_at` | DateTime | default=func.now(, server_default |
| `updated_at` | DateTime | default=func.now(, server_default |

### `trust_center_subprocessors`
**Classe:** `Subprocessor` | **Herda:** `Base` | **Uso:** Routers/Services: 1 | Total refs: 2

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `company_id` | UUID | NOT NULL, INDEX |
| `name` | String(255) | NOT NULL |
| `category` | String(50) | NOT NULL, default="other" |
| `description` | Text | — |
| `country` | String(100) | — |
| `data_processed` | Text | — |
| `is_public` | Boolean | default=True |
| `created_at` | DateTime | default=func.now(, server_default |

### `trust_center_updates`
**Classe:** `TrustCenterUpdate` | **Herda:** `Base` | **Uso:** Routers/Services: 1 | Total refs: 2

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `company_id` | UUID | NOT NULL, INDEX |
| `title` | String(255) | NOT NULL |
| `content` | Text | NOT NULL |
| `category` | String(50) | NOT NULL, default="general" |
| `published_at` | DateTime | — |
| `is_published` | Boolean | default=False |
| `created_at` | DateTime | default=func.now(, server_default |

---

## user_agent_preference
**Arquivo:** `lia-agent-system/libs/models/lia_models/user_agent_preference.py`

### `user_agent_preferences`
**Classe:** `UserAgentPreference` | **Herda:** `Base` | **Uso:** Routers/Services: 1 | Total refs: 2

| Campo | Tipo | Restrições |
|-------|------|------------|
| `user_id` | String(36) | NOT NULL |
| `company_id` | String(36) | NOT NULL |
| `domain` | String(50) | NOT NULL |
| `action_type` | String(100) | NOT NULL |
| `auto_confirm` | Boolean | NOT NULL, default=False |
| `id` | UUID | PK, default=uuid.uuid4 |
| `updated_at` | DateTime | NOT NULL, default=datetime.utcnow |

---

## voice_screening
**Arquivo:** `lia-agent-system/libs/models/lia_models/voice_screening.py`

### `voice_screening_analyses`
**Classe:** `VoiceScreeningAnalysis` | **Herda:** `Base` | **Uso:** Routers/Services: 2 | Total refs: 4

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `screening_call_id` | UUID | NOT NULL, UNIQUE, INDEX, FK → voice_screening_calls.id |
| `analysis_method` | String(100) | default="lia_ai_deep_analysis" |
| `basic_skills_mentioned` | JSON | default=[] |
| `tech_skills_mentioned` | JSON | default=[] |
| `tech_skills_matched` | JSON | default=[] |
| `tech_skills_missing` | JSON | default=[] |
| `tech_experience_years` | String(50) | — |
| `tech_projects_mentioned` | JSON | default=[] |
| `comm_notes` | Text | — |
| `fit_motivation` | Text | — |
| `fit_work_preferences` | Text | — |
| `fit_red_flags` | JSON | default=[] |
| `fit_green_flags` | JSON | default=[] |
| `key_strengths` | JSON | default=[] |
| `key_concerns` | JSON | default=[] |
| `next_steps` | Text | — |
| `full_analysis_payload` | JSON | — |
| `error_message` | Text | — |
| `created_at` | DateTime | default=datetime.utcnow |
| `updated_at` | DateTime | default=datetime.utcnow |
| `analysis_model` | String(100) | default="lia_ai_deep_analysis" |
| `basic_overall_score` | String(50) | — |
| `tech_score` | Integer | — |
| `comm_clarity` | String(20) | — |
| `fit_score` | Integer | — |
| `overall_score` | String(50) | NOT NULL, INDEX, default=[] |
| `summary` | Text | — |
| `analysis_status` | String(50) | default="completed" |

### `voice_screening_calls`
**Classe:** `VoiceScreeningCall` | **Herda:** `Base` | **Uso:** Routers/Services: 2 | Total refs: 4

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `call_id` | String(255) | NOT NULL, UNIQUE, INDEX |
| `agent_id` | String(255) | — |
| `from_number` | String(50) | — |
| `to_number` | String(50) | — |
| `start_timestamp` | DateTime | — |
| `end_timestamp` | DateTime | — |
| `duration_seconds` | Integer | — |
| `disconnection_reason` | String(100) | — |
| `candidate_name` | String(255) | NOT NULL, INDEX |
| `candidate_id` | String(255) | INDEX |
| `candidate_email` | String(255) | — |
| `job_title` | String(500) | NOT NULL, INDEX |
| `job_description` | Text | — |
| `transcript` | Text | — |
| `webhook_timestamp` | DateTime | — |
| `is_analyzed` | Boolean | default=False |
| `created_at` | DateTime | INDEX, default=datetime.utcnow |
| `updated_at` | DateTime | default=datetime.utcnow |
| `call_type` | String(50) | NOT NULL |
| `candidate_phone` | String(50) | — |
| `required_skills` | Text | default=[] |
| `transcript_object` | String(100) | default=[] |
| `webhook_payload` | String(50) | default="pending" |

---

## webhook
**Arquivo:** `lia-agent-system/libs/models/lia_models/webhook.py`

### `studio_webhooks`
**Classe:** `Webhook` | **Herda:** `Base` | **Uso:** Routers/Services: 32 | Total refs: 41

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `company_id` | String(64) | NOT NULL, INDEX |
| `name` | String(256) | NOT NULL |
| `url` | String(2048) | NOT NULL |
| `events` | String | NOT NULL |
| `secret` | String(256) | NOT NULL |
| `is_active` | Boolean | NOT NULL, default=True |
| `total_deliveries` | Integer | NOT NULL, default=0 |
| `total_failures` | Integer | NOT NULL, default=0 |
| `last_delivery_at` | DateTime | — |
| `last_status_code` | Integer | — |
| `last_error` | Text | — |
| `created_by` | String(128) | NOT NULL |
| `created_at` | DateTime | default=func.now(, server_default |
| `updated_at` | DateTime | default=func.now(, server_default |

### `webhook_logs`
**Classe:** `WebhookLog` | **Herda:** `Base` | **Uso:** Routers/Services: 1 | Total refs: 3

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `webhook_id` | UUID | NOT NULL, INDEX, FK → webhooks.id |
| `event` | String(128) | NOT NULL |
| `status` | Enum(WebhookStatus) | NOT NULL, default=WebhookStatus.PENDING |
| `status_code` | Integer | — |
| `request_body` | JSON | — |
| `response_body` | Text | — |
| `error` | Text | — |
| `attempt` | Integer | NOT NULL, default=1 |
| `duration_ms` | Integer | — |
| `created_at` | DateTime | default=func.now(, server_default |

---

## webhook_registration
**Arquivo:** `lia-agent-system/libs/models/lia_models/webhook_registration.py`

### `webhook_delivery_logs`
**Classe:** `WebhookDeliveryLog` | **Herda:** `Base` | **Uso:** Routers/Services: 3 | Total refs: 5

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `webhook_id` | UUID | NOT NULL, INDEX |
| `company_id` | String(255) | NOT NULL, INDEX |
| `event_type` | String(100) | NOT NULL |
| `payload` | JSON | NOT NULL |
| `status` | String(50) | default="pending" |
| `status_code` | Integer | — |
| `response_body` | Text | — |
| `error_message` | Text | — |
| `attempt_number` | Integer | default=1 |
| `triggered_at` | DateTime | INDEX, default=datetime.utcnow |
| `completed_at` | DateTime | — |
| `duration_ms` | Integer | — |

### `webhook_registrations`
**Classe:** `WebhookRegistration` | **Herda:** `Base` | **Uso:** Routers/Services: 3 | Total refs: 5

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `company_id` | String(255) | NOT NULL, INDEX |
| `name` | String(255) | NOT NULL |
| `description` | Text | — |
| `url` | String(2000) | NOT NULL |
| `event_types` | JSON | default=list |
| `secret_key` | String(255) | — |
| `headers` | JSON | default=dict |
| `is_active` | Boolean | INDEX, default=True |
| `retry_count` | Integer | default=3 |
| `timeout_seconds` | Integer | default=30 |
| `last_triggered_at` | DateTime | — |
| `last_success_at` | DateTime | — |
| `last_failure_at` | DateTime | — |
| `last_failure_reason` | Text | — |
| `total_triggers` | Integer | default=0 |
| `total_successes` | Integer | default=0 |
| `total_failures` | Integer | default=0 |
| `created_by` | String(255) | — |
| `created_at` | DateTime | INDEX, default=datetime.utcnow |
| `updated_at` | DateTime | default=datetime.utcnow |

---

## whatsapp_conversation
**Arquivo:** `lia-agent-system/libs/models/lia_models/whatsapp_conversation.py`

### `whatsapp_conversations`
**Classe:** `WhatsAppConversation` | **Herda:** `Base` | **Uso:** Routers/Services: 4 | Total refs: 5

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `phone_number` | String(20) | NOT NULL, INDEX |
| `whatsapp_id` | String(100) | — |
| `company_id` | String(255) | NOT NULL, INDEX |
| `job_vacancy_id` | UUID | FK → job_vacancies.id |
| `candidate_id` | UUID | FK → candidates.id |
| `current_question_index` | Integer | default=0 |
| `lgpd_accepted` | Boolean | default=False |
| `lgpd_accepted_at` | DateTime | — |
| `lgpd_ip_address` | String(50) | — |
| `cv_received` | Boolean | default=False |
| `cv_received_at` | DateTime | — |
| `cv_file_url` | Text | — |
| `cv_file_type` | String(50) | — |
| `cv_parsed_data` | JSON | — |
| `candidate_name` | String(255) | — |
| `candidate_email` | String(255) | — |
| `candidate_linkedin` | String(500) | — |
| `screening_answers` | JSON | — |
| `lia_score` | String(10) | — |
| `lia_opinion` | Text | — |
| `pre_qualification_score` | Integer | — |
| `pre_qualification_result` | String(50) | — |
| `pre_qualification_matched` | JSON | — |
| `pre_qualification_missing` | JSON | — |
| `pre_qualification_decision` | String(50) | — |
| `pre_qualification_at` | DateTime | — |
| `eligibility_answers` | JSON | — |
| `eligibility_question_index` | Integer | default=0 |
| `reconsideration_count` | Integer | default=0 |
| `reconsideration_context` | JSON | — |
| `had_reconsiderations` | Boolean | default=False |
| `is_existing_candidate` | Boolean | default=False |
| `existing_candidate_since` | DateTime | — |
| `message_count` | Integer | default=0 |
| `last_message_at` | DateTime | — |
| `last_message_direction` | String(10) | — |
| `created_at` | DateTime | default=func.now(, server_default |
| `updated_at` | DateTime | default=func.now(, server_default |
| `completed_at` | DateTime | — |
| `expires_at` | DateTime | — |
| `extra_data` | JSON | — |
| `state` | Enum(ConversationState, name="conversation_state_enum") | NOT NULL, default=ConversationState.INITIAL |

### `whatsapp_messages`
**Classe:** `WhatsAppMessage` | **Herda:** `Base` | **Uso:** Routers/Services: 1 | Total refs: 2

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `conversation_id` | UUID | NOT NULL, INDEX, FK → whatsapp_conversations.id |
| `whatsapp_message_id` | String(100) | — |
| `direction` | String(10) | NOT NULL |
| `message_type` | String(20) | NOT NULL, default="text" |
| `content` | Text | — |
| `media_url` | Text | — |
| `media_type` | String(50) | — |
| `status` | String(20) | default="sent" |
| `status_updated_at` | DateTime | — |
| `error_code` | String(50) | — |
| `error_message` | Text | — |
| `created_at` | DateTime | default=func.now(, server_default |
| `extra_data` | JSON | — |

---

## workforce
**Arquivo:** `lia-agent-system/libs/models/lia_models/workforce.py`

### `hiring_plans`
**Classe:** `HiringPlan` | **Herda:** `Base` | **Uso:** Routers/Services: 1 | Total refs: 3

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `company_id` | UUID | NOT NULL, FK → company_profiles.id |
| `fiscal_year` | Integer | NOT NULL |
| `name` | String(255) | NOT NULL |
| `description` | Text | — |
| `status` | String(50) | default="draft" |
| `owner_name` | String(255) | — |
| `owner_email` | String(255) | — |
| `total_headcount` | Integer | default=0 |
| `total_budget` | Float | — |
| `currency` | String(10) | default="BRL" |
| `ai_source_metadata` | JSON | default={} |
| `is_active` | Boolean | default=True |
| `created_at` | DateTime | default=datetime.utcnow |
| `updated_at` | DateTime | default=datetime.utcnow |
| `created_by` | String(255) | — |

### `import_jobs`
**Classe:** `ImportJob` | **Herda:** `Base` | **Uso:** Routers/Services: 1 | Total refs: 3

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `hiring_plan_id` | UUID | NOT NULL, FK → hiring_plans.id |
| `file_name` | String(500) | NOT NULL |
| `file_type` | String(50) | NOT NULL |
| `status` | String(50) | default="pending" |
| `total_rows` | Integer | default=0 |
| `imported_rows` | Integer | default=0 |
| `error_rows` | Integer | default=0 |
| `errors` | JSON | default=[] |
| `column_mapping` | JSON | default={} |
| `ai_suggestions` | JSON | default={} |
| `created_at` | DateTime | default=datetime.utcnow |
| `updated_at` | DateTime | default=datetime.utcnow |
| `created_by` | String(255) | — |

### `planned_headcounts`
**Classe:** `PlannedHeadcount` | **Herda:** `Base` | **Uso:** Routers/Services: 1 | Total refs: 3

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `hiring_plan_id` | UUID | NOT NULL, FK → hiring_plans.id |
| `department_id` | UUID | FK → departments.id |
| `ideal_profile_id` | UUID | FK → ideal_profiles.id |
| `target_month` | Integer | NOT NULL |
| `target_year` | Integer | NOT NULL |
| `title` | String(255) | NOT NULL |
| `level` | String(100) | — |
| `contract_type` | String(100) | — |
| `salary_min` | Float | — |
| `salary_max` | Float | — |
| `salary_currency` | String(10) | default="BRL" |
| `headcount` | Integer | default=1 |
| `justification` | Text | — |
| `hiring_manager_name` | String(255) | — |
| `hiring_manager_email` | String(255) | — |
| `technical_profile` | JSON | default={} |
| `behavioral_profile` | JSON | default={} |
| `job_description` | Text | — |
| `priority` | String(50) | default="medium" |
| `hiring_window_start` | Date | — |
| `hiring_window_end` | Date | — |
| `status` | String(50) | default="planned" |
| `linked_vacancy_id` | UUID | — |
| `notes` | Text | — |
| `ai_generated` | Boolean | default=False |
| `is_active` | Boolean | default=True |
| `created_at` | DateTime | default=datetime.utcnow |
| `updated_at` | DateTime | default=datetime.utcnow |

### `workforce_entries`
**Classe:** `WorkforceEntry` | **Herda:** `Base` | **Uso:** Routers/Services: 2 | Total refs: 2

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `company_id` | UUID | — |
| `year` | Integer | NOT NULL |
| `month` | String(10) | NOT NULL |
| `department` | String(100) | NOT NULL |
| `planned` | Integer | default=0 |
| `actual` | Integer | default=0 |
| `ai_suggestion` | Integer | — |
| `notes` | Text | — |
| `is_active` | Boolean | default=True |
| `created_at` | DateTime | default=datetime.utcnow |
| `updated_at` | DateTime | default=datetime.utcnow |

---

## working_memory
**Arquivo:** `lia-agent-system/libs/agents-core/lia_agents_core/working_memory.py`

### `agent_working_memory`
**Classe:** `AgentWorkingMemory` | **Herda:** `Base` | **Uso:** Routers/Services: 2 | Total refs: 3

| Campo | Tipo | Restrições |
|-------|------|------------|
| `id` | UUID | PK, default=uuid.uuid4 |
| `session_id` | String(255) | NOT NULL, INDEX |
| `domain` | String(100) | NOT NULL |
| `current_stage` | String(100) | — |
| `collected_fields` | JSON | default=dict |
| `current_plan` | JSON | default=list |
| `pending_actions` | JSON | default=list |
| `adjustment_history` | JSON | default=list |
| `parecer_data` | JSON | default=dict |
| `accepted_suggestions` | JSON | default=list |
| `rejected_suggestions` | JSON | default=list |
| `agent_notes` | Text | — |
| `iteration_count` | Integer | default=0 |
| `last_intent` | String(100) | — |
| `last_confidence` | Float | — |
| `created_at` | DateTime | default=lambda: datetime.utcnow( |
| `company_id` | String(255) | NOT NULL |
| `user_id` | String(255) | NOT NULL |
| `updated_at` | DateTime | default=lambda: datetime.utcnow( |

---
