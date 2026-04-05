"""
LIA Route Registry — all API routers registered here.
Called from app/main.py via register_all_routes(app).
"""
from fastapi import FastAPI

# ── Bulk import from app.api.v1 ──────────────────────────────────────────────
from app.api.v1 import (
    chat, teams, calendar, candidates, voice, activities, test_activities,
    job_vacancies, job_drafts, credits, interviews, ats, auth, email_templates,
    bulk_actions, cv_parser, tasks, task_lifecycle, alerts, reports,
    sourcing_pipeline, admin, briefing, notifications, automation, pipeline,
    agent_monitoring, predictive_analytics, calibration, candidate_search,
    company, workforce, applications, recruitment_stages, company_culture,
    goals, benefits, search_assistant, candidate_lists, analysis, email,
    scheduling, communications, attachments, approvals, kanban_assistant,
    file_analysis, autocomplete, opinions, journey_mapping, integrations_hub,
    recruitment_journey, admin_settings, settings_progress, screening,
    search_archetypes, dashboard_data, automations, webhooks, integrations,
    communication_settings, communication, admin_templates, policies,
    communication_matrix, clients, billing, observability, client_users,
    ai_consumption, saas_metrics, lgpd_compliance, compliance_controls,
    trust_center, audit_logs, default_templates, global_policies,
    technical_tests, workforce_planning, big_five, experience_highlights,
    lia_profile_analysis, data_subject_requests, consent_management,
    insurance, risk_register, sod_matrix, continuity, health_check,
    rubric_evaluation, task_planner, policy_engine, semantic_search, workos,
    interview_notes, external_webhooks, automation_rules, merge_webhooks,
    whatsapp, company_benefits, screening_questions, pipeline_templates,
    sourcing, job_board, job_status_webhooks, recruitment_email_templates,
    interview_analysis, data_request, lia_assistant, job_analytics,
    orchestrated_job_chat, orchestrated_talent_chat,
    orchestrated_jobs_management, shared_searches, lia_field_toggles,
    organization_catalog, intelligence, recruiter_profiles, microsoft_graph,
    cache, ml_predictions, affirmative, conversations, skills_catalog,
    multi_channel, admin_token_budget,
)

# ── Individual imports ────────────────────────────────────────────────────────
from app.api.v1 import communication_optout
from app.api.v1 import twilio_voice
from app.api.v1 import gemini_voice
from app.api.v1 import digest
from app.api.v1 import task_monitoring
from app.api.v1 import fairness_reports
from app.api.v1 import search_feedback
from app.api.v1 import job_qualification
from app.api.v1 import talent_funnel
from app.api.v1.wsi import router as wsi_router
from app.api.v1 import wsi_async as wsi_async_v1
from app.api.v1 import stage_transition_automation
from app.api.v1 import job_learning, wizard_analytics, job_embeddings, job_templates
from app.api.v1 import wsi_questions
from app.api.v1 import wsi_screening_pipeline_endpoint
from app.api.v1 import wsi_question_adjust
from app.api.v1 import jd_import
from app.api.v1 import wizard_suggestions
from app.api.v1 import wizard_smart_orchestrator
from app.api.v1 import jd_generation
from app.api.v1 import hiring_policy
from app.api.v1 import learning_outcomes, suggestion_feedback, learning_patterns
from app.api.v1 import (
    lia_assistant_learning, lia_assistant_flags, lia_assistant_wizard_stages,
    lia_assistant_vacancy, lia_assistant_fasttrack, lia_assistant_graph,
)
from app.api.v1 import triagem
from app.api.v1 import wsi_observability
from app.api.v1 import agent_explainability
from app.api.v1 import drift
from app.api.v1 import bias_audit
from app.api.v1 import admin_bias_audit
from app.api.v1 import guardrails
from app.api.v1 import async_endpoints
from app.api.v1 import jobs_ws
from app.api.v1 import saturation
from app.api.v1 import system_health
from app.api.v1 import finetuning_export, ab_testing
from app.api.v1 import (
    pipeline_velocity, self_scheduling_public, recruiter_metrics,
    early_warning, journey_intelligence, pipeline_prediction,
)
from app.api.v1.pipeline_policy import router as pipeline_policy_router
from app.api.v1.proactive_actions import router as proactive_actions_router
from app.api.v1.agent_memory import router as agent_memory_router
from app.api.v1.pipeline_orchestrator import router as pipeline_orchestrator_router
from app.api.v1.sourcing_orchestrator import router as sourcing_orchestrator_router
from app.api.v1.audit_timeline import router as audit_timeline_router
from app.api.v1.agent_chat_ws import router as agent_chat_ws_router
from app.api.v1.health_langgraph import router as health_langgraph_router
from app.api.v1.navigation_intent import router as navigation_intent_router
from app.api.v1.toon import router as toon_router

# ── Lazy imports (originally inline in main.py) ───────────────────────────────
from app.api.v1 import admin_prompts
from app.api.v1.granular_consent import router as granular_consent_router
from app.api.v1.candidate_compare import router as candidate_compare_router
from app.api.v1.ml_feedback import router as ml_feedback_router
from app.api.v1.hitl import router as hitl_router
from app.api.v1.short_lists import router as short_lists_router
from app.api.v1.rag_search import router as rag_search_router
from app.api.v1.agent_quality import router as agent_quality_router
from app.api.v1.user_agent_preferences import router as user_prefs_router
from app.api.v1.admin_lgpd import router as admin_lgpd_router
from app.api.v1.email_tracking import router as email_tracking_router, communication_webhook_router
from app.api.v1.admin_circuit_breakers import router as admin_cb_router
from app.api.v1.admin_agents import router as admin_agents_router
from app.api.v1.admin_dlq import router as admin_dlq_router
from app.api.v1.traces import router as traces_router
from app.api.v1.recruiter_behavior import router as recruiter_behavior_router
from app.api.v1.salary_benchmark import router as salary_benchmark_router
from app.api.v1.cultural_fit import router as cultural_fit_router
from app.api.v1.event_history import router as event_history_router
from app.api.v1.company_retention import router as company_retention_router
from app.api.v1.agent_templates import router as agent_templates_router

# ── Public routes ─────────────────────────────────────────────────────────────
from app.api.public import candidate_portal
from app.api.public import shared_searches as public_shared_searches

# ── Orchestrator / WSI umbrella routers ───────────────────────────────────────
from app.api import orchestrator_routes, wsi_endpoints


def register_all_routes(app: FastAPI) -> None:
    """Register all API routers. Grouped by domain."""

    # ── Health / System ───────────────────────────────────────────────────────
    app.include_router(system_health.router, prefix="/api/v1")
    app.include_router(health_langgraph_router, prefix="/api/v1")
    app.include_router(health_check.router, prefix="/api/v1", tags=["health-check"])

    # ── Core / Navigation ─────────────────────────────────────────────────────
    app.include_router(navigation_intent_router, prefix="/api/v1")
    app.include_router(chat.router, prefix="/api/v1")
    app.include_router(teams.router, prefix="/api/v1")
    app.include_router(calendar.router, prefix="/api/v1")

    # ── Auth ──────────────────────────────────────────────────────────────────
    app.include_router(auth.router, prefix="/api/v1")
    app.include_router(workos.router, prefix="/api/v1", tags=["workos"])
    app.include_router(workos.scim_router, prefix="/api/v1", tags=["workos-scim"])
    app.include_router(workos.auth_router, prefix="/api/v1", tags=["workos-auth"])
    app.include_router(workos.webhook_router, prefix="/api/v1", tags=["workos-webhooks"])
    app.include_router(workos.public_auth_router, prefix="/api/v1", tags=["auth-public"])

    # ── Candidates ────────────────────────────────────────────────────────────
    app.include_router(candidates.router, prefix="/api/v1/candidates", tags=["candidates"])
    app.include_router(toon_router, prefix="/api/v1", tags=["toon"])
    app.include_router(candidate_search.router, prefix="/api/v1", tags=["candidate-search"])
    app.include_router(candidate_lists.router, prefix="/api/v1/candidate-lists", tags=["candidate-lists"])
    app.include_router(communications.candidate_communications_router, prefix="/api/v1", tags=["candidates"])
    app.include_router(attachments.candidate_attachments_router, prefix="/api/v1", tags=["candidates"])
    app.include_router(candidate_compare_router, prefix="/api/v1", tags=["candidate-compare"])
    app.include_router(cv_parser.router, prefix="/api/v1", tags=["cv-parser"])
    app.include_router(lia_profile_analysis.router, prefix="/api/v1", tags=["lia-profile-analysis"])
    app.include_router(experience_highlights.router, prefix="/api/v1", tags=["experience-highlights"])
    app.include_router(big_five.router, prefix="/api/v1", tags=["big-five"])
    app.include_router(affirmative.router, prefix="/api/v1", tags=["affirmative"])

    # ── Jobs ──────────────────────────────────────────────────────────────────
    app.include_router(job_vacancies.router, prefix="/api/v1", tags=["job_vacancies"])
    app.include_router(job_vacancies.router_public, prefix="/api/v1/public-vacancies", tags=["public_vacancies"])
    app.include_router(job_drafts.router, prefix="/api/v1", tags=["job_drafts"])
    app.include_router(job_analytics.router, prefix="/api/v1", tags=["job-analytics"])
    app.include_router(job_board.router, prefix="/api/v1", tags=["job-boards"])
    app.include_router(job_status_webhooks.router, prefix="/api/v1", tags=["job-status-webhooks"])
    app.include_router(job_learning.router, prefix="/api/v1", tags=["job-learning"])
    app.include_router(job_embeddings.router, prefix="/api/v1", tags=["job-embeddings"])
    app.include_router(job_templates.router, prefix="/api/v1", tags=["job-templates"])
    app.include_router(jd_import.router, prefix="/api/v1/learning", tags=["learning-loop"])
    app.include_router(jd_generation.router, prefix="/api/v1", tags=["jd-generation"])
    app.include_router(job_qualification.router, prefix="/api/v1", tags=["job-qualification"])

    # ── Pipeline ──────────────────────────────────────────────────────────────
    app.include_router(pipeline.router, prefix="/api/v1/pipeline", tags=["pipeline"])
    app.include_router(applications.router, prefix="/api/v1", tags=["applications"])
    app.include_router(recruitment_stages.router, prefix="/api/v1/recruitment-stages", tags=["recruitment-stages"])
    app.include_router(recruitment_stages.screening_questions_router, prefix="/api/v1", tags=["screening-questions"])
    app.include_router(pipeline_templates.router, prefix="/api/v1", tags=["pipeline-templates"])
    app.include_router(pipeline_policy_router, prefix="/api/v1")
    app.include_router(pipeline_orchestrator_router, prefix="/api/v1")
    app.include_router(pipeline_velocity.router, prefix="/api/v1", tags=["pipeline-velocity"])
    app.include_router(pipeline_prediction.router, prefix="/api/v1", tags=["pipeline-prediction"])
    app.include_router(stage_transition_automation.router, prefix="/api/v1/stage-automation", tags=["stage-transition-automation"])
    app.include_router(kanban_assistant.router, prefix="/api/v1", tags=["kanban-assistant"])
    app.include_router(early_warning.router, prefix="/api/v1", tags=["early-warning"])
    app.include_router(journey_intelligence.router, prefix="/api/v1", tags=["journey-intelligence"])

    # ── Sourcing ──────────────────────────────────────────────────────────────
    app.include_router(sourcing_pipeline.router, prefix="/api/v1", tags=["sourcing-pipeline"])
    app.include_router(sourcing.router, prefix="/api/v1", tags=["sourcing"])
    app.include_router(sourcing_orchestrator_router, prefix="/api/v1")
    app.include_router(talent_funnel.router, prefix="/api/v1", tags=["talent-funnel"])

    # ── Interviews & Scheduling ───────────────────────────────────────────────
    app.include_router(interviews.router, prefix="/api/v1", tags=["interviews"])
    app.include_router(scheduling.router, prefix="/api/v1", tags=["scheduling"])
    app.include_router(interview_notes.router, prefix="/api/v1", tags=["interview-notes"])
    app.include_router(interview_analysis.router, prefix="/api/v1", tags=["interview-analysis"])
    app.include_router(self_scheduling_public.router, prefix="/api/v1", tags=["self-scheduling"])
    app.include_router(calibration.router, prefix="/api/v1", tags=["calibration"])
    app.include_router(rubric_evaluation.router, prefix="/api/v1/rubrics", tags=["rubric-evaluation"])
    app.include_router(technical_tests.router, prefix="/api/v1", tags=["technical-tests"])

    # ── Voice / Communication Channels ───────────────────────────────────────
    app.include_router(voice.router, prefix="/api/v1", tags=["voice"])
    app.include_router(twilio_voice.router, prefix="/api/v1", tags=["twilio-voice"])
    app.include_router(gemini_voice.router, prefix="/api/v1", tags=["gemini-voice"])
    app.include_router(whatsapp.router, prefix="/api/v1", tags=["whatsapp"])
    app.include_router(multi_channel.router, prefix="/api/v1", tags=["multi-channel"])

    # ── Communication ─────────────────────────────────────────────────────────
    app.include_router(communications.router, prefix="/api/v1", tags=["communications"])
    app.include_router(communication.router, prefix="/api/v1", tags=["communication"])
    app.include_router(communication_settings.router, prefix="/api/v1", tags=["company"])
    app.include_router(communication_matrix.router, prefix="/api/v1", tags=["communication-matrix"])
    app.include_router(communication_optout.router, prefix="/api/v1", tags=["communication-optout"])
    app.include_router(email.router, prefix="/api/v1", tags=["email"])
    app.include_router(email_templates.router, prefix="/api/v1", tags=["email-templates"])
    app.include_router(recruitment_email_templates.router, prefix="/api/v1", tags=["recruitment-email-templates"])
    app.include_router(email_tracking_router, prefix="/api/v1", tags=["email-tracking"])
    app.include_router(communication_webhook_router, prefix="/api/v1", tags=["email-tracking"])
    app.include_router(notifications.router, prefix="/api/v1", tags=["notifications"])
    app.include_router(digest.router, prefix="/api/v1", tags=["digest"])

    # ── Company ───────────────────────────────────────────────────────────────
    app.include_router(company.router, prefix="/api/v1", tags=["company"])
    app.include_router(lia_field_toggles.router, prefix="/api/v1", tags=["field-toggles"])
    app.include_router(company_culture.router, prefix="/api/v1", tags=["company-culture"])
    app.include_router(company_benefits.router, prefix="/api/v1", tags=["company-benefits"])
    app.include_router(goals.router, prefix="/api/v1", tags=["goals"])
    app.include_router(benefits.router, prefix="/api/v1", tags=["benefits"])
    app.include_router(clients.router, prefix="/api/v1", tags=["clients"])
    app.include_router(client_users.router, prefix="/api/v1", tags=["client-users"])
    app.include_router(client_users.invitation_router, prefix="/api/v1", tags=["invitations"])
    app.include_router(organization_catalog.router, prefix="/api/v1", tags=["organization-catalog"])

    # ── Tasks & Automation ────────────────────────────────────────────────────
    app.include_router(tasks.router, prefix="/api/v1", tags=["tasks"])
    app.include_router(task_lifecycle.router, prefix="/api/v1", tags=["task-lifecycle"])
    app.include_router(task_planner.router, prefix="/api/v1", tags=["task-planner"])
    app.include_router(task_monitoring.router, prefix="/api/v1", tags=["task-monitoring"])
    app.include_router(automation.router, prefix="/api/v1", tags=["automation"])
    app.include_router(automations.router, prefix="/api/v1", tags=["automations"])
    app.include_router(automation_rules.router, prefix="/api/v1", tags=["automation-rules"])
    app.include_router(async_endpoints.router, prefix="/api/v1", tags=["async-jobs"])

    # ── Search & Discovery ────────────────────────────────────────────────────
    app.include_router(search_assistant.router, prefix="/api/v1", tags=["search-assistant"])
    app.include_router(search_archetypes.router, prefix="/api/v1", tags=["search-archetypes"])
    app.include_router(search_feedback.router, prefix="/api/v1", tags=["search-feedback"])
    app.include_router(semantic_search.router, prefix="/api/v1", tags=["semantic-search"])
    app.include_router(rag_search_router, prefix="/api/v1", tags=["rag-search"])
    app.include_router(shared_searches.router, prefix="/api/v1/shared-searches", tags=["shared-searches"])
    app.include_router(autocomplete.router, prefix="/api/v1", tags=["autocomplete"])

    # ── AI / ML / Analytics ───────────────────────────────────────────────────
    app.include_router(ml_predictions.router, prefix="/api/v1", tags=["ml-predictions"])
    app.include_router(ml_feedback_router, prefix="/api/v1", tags=["ml-feedback"])
    app.include_router(predictive_analytics.router, prefix="/api/v1", tags=["predictive-analytics"])
    app.include_router(analysis.router, prefix="/api/v1", tags=["analysis"])
    app.include_router(intelligence.router, prefix="/api/v1/intelligence", tags=["intelligence-layer"])
    app.include_router(drift.router, prefix="/api/v1", tags=["model-drift"])
    app.include_router(ab_testing.router, prefix="/api/v1", tags=["ab-testing"])
    app.include_router(finetuning_export.router, prefix="/api/v1", tags=["finetuning-export"])
    app.include_router(wizard_analytics.router, prefix="/api/v1", tags=["wizard-analytics"])

    # ── Reports & Dashboard ───────────────────────────────────────────────────
    app.include_router(reports.router, prefix="/api/v1", tags=["reports"])
    app.include_router(dashboard_data.router, prefix="/api/v1", tags=["dashboard"])
    app.include_router(alerts.router, prefix="/api/v1", tags=["alerts"])
    app.include_router(agent_monitoring.router, prefix="/api/v1", tags=["agent-monitoring"])
    app.include_router(saturation.router, prefix="/api/v1", tags=["saturation"])
    app.include_router(fairness_reports.router, prefix="/api/v1", tags=["fairness-reports"])
    app.include_router(recruiter_metrics.router, prefix="/api/v1", tags=["recruiter-metrics"])
    app.include_router(recruiter_profiles.router, prefix="/api/v1/recruiter-profiles", tags=["recruiter-profiles"])
    app.include_router(recruiter_behavior_router, prefix="/api/v1")

    # ── Workforce ─────────────────────────────────────────────────────────────
    app.include_router(workforce.router, prefix="/api/v1", tags=["workforce"])
    app.include_router(workforce_planning.router, prefix="/api/v1", tags=["workforce-planning"])
    app.include_router(credits.router, prefix="/api/v1", tags=["credits"])

    # ── WSI / Triagem ─────────────────────────────────────────────────────────
    app.include_router(wsi_endpoints.router, tags=["wsi"])
    app.include_router(wsi_router, tags=["wsi-v1"])
    app.include_router(wsi_async_v1.router, prefix="/api/v1", tags=["wsi-async"])
    app.include_router(wsi_questions.router, prefix="/api/v1", tags=["wsi-questions"])
    app.include_router(wsi_screening_pipeline_endpoint.router, prefix="/api/v1", tags=["wsi-screening-pipeline"])
    app.include_router(wsi_question_adjust.router, prefix="/api/v1", tags=["wsi-question-adjust"])
    app.include_router(wsi_observability.router, prefix="/api/v1", tags=["wsi-observability"])
    app.include_router(triagem.router, prefix="/api/v1", tags=["triagem"])
    app.include_router(screening.router, prefix="/api/v1", tags=["screening"])
    app.include_router(screening_questions.router, prefix="/api/v1", tags=["company-screening-questions"])

    # ── LIA Assistant ─────────────────────────────────────────────────────────
    app.include_router(lia_assistant.router, prefix="/api/v1", tags=["lia-assistant"])
    app.include_router(lia_assistant_learning.router, prefix="/api/v1", tags=["lia-learning"])
    app.include_router(lia_assistant_flags.router, prefix="/api/v1", tags=["lia-feature-flags"])
    app.include_router(lia_assistant_wizard_stages.router, prefix="/api/v1", tags=["lia-wizard-stages"])
    app.include_router(lia_assistant_vacancy.router, prefix="/api/v1", tags=["lia-vacancy"])
    app.include_router(lia_assistant_fasttrack.router, prefix="/api/v1", tags=["lia-fasttrack"])
    app.include_router(lia_assistant_graph.router, prefix="/api/v1/lia-assistant", tags=["lia-graph"])

    # ── Wizard ────────────────────────────────────────────────────────────────
    app.include_router(wizard_suggestions.router, prefix="/api/v1/wizard", tags=["wizard-suggestions"])
    app.include_router(wizard_smart_orchestrator.router, prefix="/api/v1/wizard", tags=["wizard-smart-orchestrator"])

    # ── Orchestrator ──────────────────────────────────────────────────────────
    app.include_router(orchestrator_routes.router)
    app.include_router(orchestrated_job_chat.router, prefix="/api/v1", tags=["orchestrated-job-chat"])
    app.include_router(orchestrated_talent_chat.router, prefix="/api/v1/orchestrator", tags=["orchestrated-talent-chat"])
    app.include_router(orchestrated_jobs_management.router, prefix="/api/v1/orchestrator", tags=["orchestrated-jobs-management"])

    # ── HITL ──────────────────────────────────────────────────────────────────
    app.include_router(hitl_router, prefix="/api/v1", tags=["hitl"])
    app.include_router(proactive_actions_router, prefix="/api/v1")
    app.include_router(agent_memory_router, prefix="/api/v1")
    app.include_router(agent_explainability.router, prefix="/api/v1", tags=["agent-explainability"])
    app.include_router(agent_quality_router, prefix="/api/v1", tags=["agent-quality"])
    app.include_router(agent_chat_ws_router)

    # ── WebSocket ─────────────────────────────────────────────────────────────
    app.include_router(jobs_ws.router)

    # ── Compliance / LGPD ─────────────────────────────────────────────────────
    app.include_router(lgpd_compliance.router, prefix="/api/v1", tags=["lgpd-compliance"])
    app.include_router(compliance_controls.router, prefix="/api/v1", tags=["compliance-controls"])
    app.include_router(trust_center.router, prefix="/api/v1", tags=["trust-center"])
    app.include_router(audit_logs.router, prefix="/api/v1", tags=["audit-logs"])
    app.include_router(audit_timeline_router)
    app.include_router(data_subject_requests.router, prefix="/api/v1", tags=["data-subject-requests"])
    app.include_router(consent_management.router, prefix="/api/v1", tags=["consent-management"])
    app.include_router(granular_consent_router, prefix="/api/v1", tags=["granular-consent"])
    app.include_router(data_request.router, prefix="/api/v1", tags=["data-requests"])
    app.include_router(admin_lgpd_router, prefix="/api/v1")
    app.include_router(bias_audit.router, prefix="/api/v1", tags=["bias-audit"])
    app.include_router(admin_bias_audit.router, prefix="/api/v1", tags=["bias-audit-admin"])
    app.include_router(guardrails.router, prefix="/api/v1", tags=["guardrails"])
    app.include_router(insurance.router, prefix="/api/v1", tags=["insurance"])
    app.include_router(risk_register.router, prefix="/api/v1", tags=["risk-register"])
    app.include_router(sod_matrix.router, prefix="/api/v1", tags=["sod-matrix"])
    app.include_router(continuity.router, prefix="/api/v1", tags=["continuity"])

    # ── Policy ────────────────────────────────────────────────────────────────
    app.include_router(policies.router, prefix="/api/v1", tags=["policies"])
    app.include_router(policy_engine.router, prefix="/api/v1", tags=["policy-engine"])
    app.include_router(global_policies.router, prefix="/api/v1", tags=["global-policies"])
    app.include_router(default_templates.router, prefix="/api/v1", tags=["default-templates"])
    app.include_router(hiring_policy.router, prefix="/api/v1", tags=["hiring-policy"])

    # ── ATS / Integrations ────────────────────────────────────────────────────
    app.include_router(ats.router, prefix="/api/v1", tags=["ats"])
    app.include_router(webhooks.router, prefix="/api/v1", tags=["webhooks"])
    app.include_router(integrations.router, prefix="/api/v1", tags=["integrations"])
    app.include_router(integrations_hub.router, prefix="/api/v1", tags=["integration-hub"])
    app.include_router(external_webhooks.router, prefix="/api/v1", tags=["external-webhooks"])
    app.include_router(merge_webhooks.router, prefix="/api/v1", tags=["merge-webhooks"])
    app.include_router(microsoft_graph.router, prefix="/api/v1", tags=["microsoft-graph"])

    # ── Learning ──────────────────────────────────────────────────────────────
    app.include_router(learning_outcomes.router, prefix="/api/v1", tags=["learning-outcomes"])
    app.include_router(suggestion_feedback.router, prefix="/api/v1", tags=["suggestion-feedback"])
    app.include_router(learning_patterns.router, prefix="/api/v1", tags=["learning-patterns"])
    app.include_router(skills_catalog.router, prefix="/api/v1", tags=["skills-catalog"])
    app.include_router(conversations.router, prefix="/api/v1", tags=["conversations"])
    app.include_router(journey_mapping.router, prefix="/api/v1", tags=["journey-mapping"])
    app.include_router(recruitment_journey.router, prefix="/api/v1", tags=["recruitment-journey"])

    # ── Misc / Operational ────────────────────────────────────────────────────
    app.include_router(activities.router, prefix="/api/v1", tags=["activities"])
    app.include_router(test_activities.router, prefix="/api/v1", tags=["testing"])
    app.include_router(bulk_actions.router, prefix="/api/v1", tags=["bulk-actions"])
    app.include_router(approvals.router, prefix="/api/v1", tags=["approvals"])
    app.include_router(attachments.router, prefix="/api/v1", tags=["attachments"])
    app.include_router(file_analysis.router, prefix="/api/v1", tags=["file-analysis"])
    app.include_router(opinions.router, prefix="/api/v1", tags=["opinions"])
    app.include_router(admin_settings.router, prefix="/api/v1", tags=["admin-settings"])
    app.include_router(settings_progress.router, prefix="/api/v1", tags=["settings-progress"])
    app.include_router(briefing.router, prefix="/api/v1", tags=["briefing"])

    # ── Billing & SaaS ────────────────────────────────────────────────────────
    app.include_router(billing.router, prefix="/api/v1", tags=["billing"])
    app.include_router(ai_consumption.router, prefix="/api/v1", tags=["ai-consumption"])
    app.include_router(ai_consumption.ai_usage_router, prefix="/api/v1", tags=["ai-usage"])
    app.include_router(saas_metrics.router, prefix="/api/v1", tags=["saas-metrics"])

    # ── Observability ─────────────────────────────────────────────────────────
    app.include_router(observability.router, prefix="/api/v1", tags=["observability"])
    app.include_router(cache.router, prefix="/api/v1", tags=["cache"])
    app.include_router(traces_router, prefix="/api/v1")

    # ── Admin ─────────────────────────────────────────────────────────────────
    app.include_router(admin.router, prefix="/api/v1", tags=["admin"])
    app.include_router(admin_templates.router, prefix="/api/v1", tags=["admin-templates"])
    app.include_router(admin_token_budget.router, prefix="/api/v1", tags=["admin-token-budget"])
    app.include_router(admin_prompts.router, prefix="/api/v1", tags=["admin-prompts"])
    app.include_router(admin_cb_router, prefix="/api/v1")
    app.include_router(admin_agents_router, prefix="/api/v1")
    app.include_router(admin_dlq_router, prefix="/api/v1")

    # ── Short Lists / RAG ─────────────────────────────────────────────────────
    app.include_router(short_lists_router, prefix="/api/v1", tags=["short-lists"])

    # ── Salary & Cultural ─────────────────────────────────────────────────────
    app.include_router(salary_benchmark_router, prefix="/api/v1", tags=["salary-benchmark"])
    app.include_router(cultural_fit_router, prefix="/api/v1", tags=["cultural-fit"])

    # ── Event Sourcing ────────────────────────────────────────────────────────
    app.include_router(event_history_router, prefix="/api/v1", tags=["event-sourcing"])

    # ── User Preferences ──────────────────────────────────────────────────────
    app.include_router(user_prefs_router, prefix="/api/v1", tags=["user-preferences"])

    # ── Agent Studio / Retention (Etapa 4 & 8) ───────────────────────────────
    app.include_router(company_retention_router, prefix="/api/v1", tags=["company-retention"])
    app.include_router(agent_templates_router, prefix="/api/v1", tags=["agent-templates"])

    # ── Public (no /api/v1 prefix) ────────────────────────────────────────────
    app.include_router(candidate_portal.router, tags=["candidate-portal"])
    app.include_router(public_shared_searches.router, prefix="/api", tags=["public-shared-searches"])
