from app.api.v1 import admin_persona
from app.api.v1 import company_ai_persona
"""
LIA Route Registry — all API routers registered here.
Called from app/main.py via register_all_routes(app).
"""
from fastapi import FastAPI

# ── Orchestrator / WSI umbrella routers ───────────────────────────────────────
from app.api import orchestrator_routes, wsi_endpoints

# ── Public routes ─────────────────────────────────────────────────────────────
from app.api.public import candidate_portal
from app.api.public import shared_searches as public_shared_searches

# ── Bulk import from app.api.v1 ──────────────────────────────────────────────
# ── Individual imports ────────────────────────────────────────────────────────
# ── Lazy imports (originally inline in main.py) ───────────────────────────────
from app.api.v1 import llm_config as llm_config_router_mod

from app.api.v1 import (
    ab_testing,
    ai_performance,
    jd_similar,
    learning_loops_config,
    activities,
    admin,
    admin_bias_audit,
    admin_compliance_fairness,
    admin_prompts,
    admin_settings,
    admin_templates,
    admin_platform,
    admin_token_budget,
    affirmative,
    agent_explainability,
    ai_transparency,
    agent_monitoring,
    ai_consumption,
    alerts,
    analysis,
    applications,
    approvals,
    async_endpoints,
    ats,
    attachments,
    audit_logs,
    auth,
    autocomplete,
    automation,
    automations,
    benefits,
    bias_audit,
    bias_audit_annual,
    big_five,
    billing,
    briefing,
    upgrade_requests,
    bulk_actions,
    cache,
    calendar,
    calibration,
    candidate_lists,
    candidate_search,
    candidates,
    chat,
    client_users,
    clients,
    communication,
    communication_matrix,
    communication_optout,
    communication_settings,
    communications,
    company,
    company_approvers,
    company_users,
    company_benefits,
    company_assessments,
    company_culture,
    company_culture_config,
    company_departments,
    compliance_controls,
    compliance_report,
    compliance_status,
    consent_management,
    conversations,
    consumption,
    credits,
    cv_parser,
    dashboard_data,
    data_request,
    data_subject_requests,
    default_templates,
    digest,
    drift,
    early_warning,
    email,
    email_templates,
    experience_highlights,
    external_webhooks,
    fairness_reports,
    mailgun_webhooks,
    file_analysis,
    finetuning_export,
    gemini_voice,
    voice_stream,
    global_policies,
    goals,
    guardrails,
    health_check,
    hiring_policy,
    integrations,
    integrations_hub,
    intelligence,
    interview_analysis,
    interview_notes,
    interviews,
    jd_generation,
    jd_import,
    job_analytics,
    job_board,
    job_drafts,
    job_embeddings,
    job_learning,
    job_qualification,
    job_status_webhooks,
    job_templates,
    job_vacancies,
    jobs_ws,
    journey_intelligence,
    journey_mapping,
    kanban_assistant,
    learning_outcomes,
    learning_patterns,
    lgpd_compliance,
    lia_assistant,
    lia_assistant_fasttrack,
    lia_assistant_flags,
    lia_assistant_learning,
    lia_assistant_vacancy,
    lia_assistant_wizard_stages,
    lia_field_toggles,
    eligibility_question_templates,
    integration_catalog,
    webhook_event_types,
    lia_profile_analysis,
    merge_webhooks,
    microsoft_graph,
    ml_predictions,
    modules,
    multi_channel,
    notifications,
    observability,
    opinions,
    orchestrated_job_chat,
    orchestrated_jobs_management,
    orchestrated_talent_chat,
    organization_catalog,
    pipeline,
    pipeline_prediction,
    pipeline_templates,
    pipeline_velocity,
    policies,
    policy_engine,
    predictive_analytics,
    recruiter_metrics,
    recruiter_profiles,
    recruitment_campaigns,
    recruitment_email_templates,
    recruitment_journey,
    recruitment_stages,
    reports,
    rubric_evaluation,
    saas_metrics,
    saturation,
    scheduling,
    screening,
    screening_questions,
    search_archetypes,
    search_assistant,
    search_feedback,
    self_scheduling_public,
    semantic_search,
    settings_progress,
    shared_searches,
    skills_catalog,
    sourcing,
    sourcing_pipeline,
    stage_transition_automation,
    suggestion_feedback,
    system_health,
    talent_funnel,
    talent_pools,
    talent_pool_agents,
    task_lifecycle,
    task_monitoring,
    task_planner,
    tasks,
    teams,
    technical_tests,
    test_activities,
    triagem,
    trust_center,
    openmic_webhook,
    twilio_voice,
    voice,
    webhooks,
    whatsapp,
    wizard_analytics,
    wizard_smart_orchestrator,
    wizard_suggestions,
    workforce,
    workforce_planning,
    workos,
    wsi_observability,
    wsi_question_adjust,
    wsi_questions,
    wsi_screening_pipeline_endpoint,
)
from app.api.v1 import wsi_async as wsi_async_v1
from app.api.v1.admin_agents import router as admin_agents_router
from app.api.v1.admin_external import router as admin_external_router
from app.api.v1.admin_circuit_breakers import router as admin_cb_router
from app.api.v1.admin_dlq import router as admin_dlq_router
from app.api.v1.admin_lgpd import router as admin_lgpd_router
from app.api.v1.admin_consent import router as admin_consent_router  # T-21c
from app.api.v1.incident_response import router as incident_response_router
from app.api.v1.agent_chat_ws import router as agent_chat_ws_router
from app.api.v1.agent_chat_sse import router as agent_chat_sse_router
from app.api.v1.agent_memory import router as agent_memory_router
from app.api.v1.agent_quality import router as agent_quality_router
from app.api.v1.agent_quality_dashboard import router as agent_quality_dashboard_router
from app.api.v1.ml_predictions_dashboard import router as ml_predictions_router
from app.api.v1.calibration_dashboard_v2 import router as calibration_dashboard_v2_router
from app.api.v1.agent_templates import router as agent_templates_router
from app.api.v1.agent_template_catalog import router as agent_template_catalog_router
from app.api.v1.sector_templates import router as sector_templates_router
from app.api.v1.custom_agents import router as custom_agents_router
from app.api.v1.agent_studio_voice import router as agent_studio_voice_router
from app.api.v1.agent_studio_whatsapp import router as agent_studio_whatsapp_router
from app.api.v1.agent_studio_channels import router as agent_studio_channels_router
from app.api.v1.agent_studio_triagem_invite import router as agent_studio_triagem_invite_router
from app.api.v1.agent_deployments import router as agent_deployments_router
from app.api.v1.agent_deployments import target_router as agent_deployments_target_router
from app.api.v1.agent_approvals import agent_router as agent_approvals_agent_router
from app.api.v1.agent_approvals import approvals_router as agent_approvals_approvals_router
from app.api.v1.webhooks import router as webhooks_router
from app.api.v1.custom_agents import marketplace_router as agent_marketplace_router
from app.api.v1.custom_agents import admin_marketplace_router
from app.api.v1.multi_strategy_search import router as multi_strategy_router
from app.api.v1.digital_twins import router as digital_twins_router
from app.api.v1.voice_screening import router as voice_screening_router
from app.api.v1.audit_timeline import router as audit_timeline_router
from app.api.v1.candidate_compare import router as candidate_compare_router
from app.api.v1.company_retention import router as company_retention_router
from app.api.v1.onboarding import router as onboarding_router
from app.api.v1.whatsapp_webhook import router as whatsapp_webhook_router
from app.api.v1.cultural_fit import router as cultural_fit_router
from app.api.v1.email_tracking import communication_webhook_router
from app.api.v1.email_tracking import router as email_tracking_router
from app.api.v1.event_history import router as event_history_router
from app.api.v1.granular_consent import router as granular_consent_router
from app.api.v1.health_langgraph import router as health_langgraph_router
from app.api.v1.hitl import router as hitl_router
from app.api.v1.ml_feedback import router as ml_feedback_router
from app.api.v1.navigation_intent import router as navigation_intent_router
from app.api.v1.pipeline_orchestrator import router as pipeline_orchestrator_router
from app.api.v1.pipeline_policy import router as pipeline_policy_router
from app.api.v1.proactive_actions import router as proactive_actions_router
from app.api.v1.proactive_hints import router as proactive_hints_router  # WT-2022
from app.api.v1.rag_search import router as rag_search_router
from app.api.v1.recruiter_behavior import router as recruiter_behavior_router
from app.api.v1.salary_benchmark import router as salary_benchmark_router
from app.api.v1.short_lists import router as short_lists_router
from app.api.v1.sourcing_orchestrator import router as sourcing_orchestrator_router
from app.api.v1.toon import router as toon_router
from app.api.v1.traces import router as traces_router
from app.api.v1.user_agent_preferences import router as user_prefs_router
from app.api.v1.wsi import router as wsi_router
from app.api.v1.rails_health import router as rails_health_router
from app.api.v1.rails_sync import router as rails_sync_router
from app.api.v1.llm_config import router as llm_config_router


def register_all_routes(app: FastAPI) -> None:
    """Register all API routers. Grouped by domain."""

    # ── Health / System ───────────────────────────────────────────────────────
    app.include_router(system_health.router, prefix="/api/v1")
    app.include_router(health_langgraph_router, prefix="/api/v1")
    app.include_router(health_check.router, prefix="/api/v1", tags=["health-check"])
    app.include_router(rails_health_router, prefix="/api/v1", tags=["rails-integration"])
    app.include_router(rails_sync_router, prefix="/api/v1", tags=["rails-sync"])

    # ── Internal LLM (used by Next.js frontend routes) ────────────────────────
    from app.api.v1 import internal_llm
    app.include_router(internal_llm.router, prefix="/api/v1")

    # Glossary (canonical term lookup for chat tooltips and /definir)
    from app.api.v1 import glossary as glossary_v1
    app.include_router(glossary_v1.router, prefix="/api/v1/glossary", tags=["glossary"])
    app.include_router(jd_similar.router, prefix="/api/v1", tags=["jd-similar"])
    app.include_router(learning_loops_config.router, prefix="/api/v1", tags=["learning-loops"])


    # ── Core / Navigation ─────────────────────────────────────────────────────
    app.include_router(navigation_intent_router, prefix="/api/v1")
    app.include_router(chat.router, prefix="/api/v1")
    # Sprint 3 G9 wire (2026-05-26): proactive context from Settings hub
    from app.api.v1 import proactive_context
    app.include_router(proactive_context.router, prefix="/api/v1", tags=["lia-proactive-context"])
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
    app.include_router(pipeline_templates.vacancy_apply_router, prefix="/api/v1", tags=["pipeline-templates", "vacancies"])
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
    app.include_router(talent_pools.router, prefix="/api/v1", tags=["talent-pools"])
    app.include_router(talent_pool_agents.router, prefix="/api/v1", tags=["talent-pool-agents"])
    app.include_router(recruitment_campaigns.router, prefix="/api/v1", tags=["recruitment-campaigns"])

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
    app.include_router(voice_stream.router, prefix="/api/v1", tags=["voice-stream"])
    app.include_router(openmic_webhook.router, prefix="/api/v1", tags=["openmic-voice"])
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
    app.include_router(company_approvers.router, prefix="/api/v1", tags=["company"])
    app.include_router(company_users.router, prefix="/api/v1", tags=["company"])
    app.include_router(lia_field_toggles.router, prefix="/api/v1", tags=["field-toggles"])
    app.include_router(eligibility_question_templates.router, prefix="/api/v1", tags=["eligibility-question-templates"])
    app.include_router(integration_catalog.router, prefix="/api/v1", tags=["integration-catalog"])
    app.include_router(webhook_event_types.router, prefix="/api/v1", tags=["webhook-event-types"])
    app.include_router(company_culture.router, prefix="/api/v1", tags=["company-culture"])
    # T2/#994 — legacy ``/company/{enrich,auto-enrich,profile/{id}/generate-evp,
    # analyze-culture}`` routes were relocated from ``company.py`` into
    # ``company_culture.py``. Public paths are preserved byte-for-byte
    # via this second router so the frontend sees zero change.
    app.include_router(company_culture.legacy_router, prefix="/api/v1", tags=["company-culture"])
    app.include_router(company_culture_config.router, prefix="/api/v1", tags=["company"])
    app.include_router(company_departments.router, prefix="/api/v1", tags=["company"])
    app.include_router(company_assessments.router, prefix="/api/v1", tags=["company"])
    app.include_router(company_benefits.router, prefix="/api/v1", tags=["company-benefits"])
    app.include_router(goals.router, prefix="/api/v1", tags=["goals"])
    app.include_router(benefits.router, prefix="/api/v1", tags=["benefits"])
    app.include_router(clients.router, prefix="/api/v1/clients", tags=["clients"])
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
    app.include_router(ai_performance.router, prefix="/api/v1", tags=["ai-performance"])
    app.include_router(finetuning_export.router, prefix="/api/v1", tags=["finetuning-export"])
    app.include_router(wizard_analytics.router, prefix="/api/v1", tags=["wizard-analytics"])

    # ── LLM Config (Choose Your AI) ──────────────────────────────────────────
    app.include_router(llm_config_router, prefix="/api/v1", tags=["llm-config"])

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
    app.include_router(consumption.router, prefix="/api/v1", tags=["consumption"])

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
    app.include_router(proactive_hints_router, prefix="/api/v1")  # WT-2022
    app.include_router(agent_memory_router, prefix="/api/v1")
    app.include_router(agent_explainability.router, prefix="/api/v1", tags=["agent-explainability"])

    from app.api.v1 import decision_explanation
    app.include_router(decision_explanation.router, prefix="/api/v1", tags=["decision-explanation"])

    from app.api.v1 import ai_config
    app.include_router(ai_config.router, prefix="/api/v1", tags=["ai-configuration"])

    from app.api.v1 import agent_studio_quality
    app.include_router(agent_studio_quality.router, prefix="/api/v1", tags=["agent-studio-quality"])
    app.include_router(agent_quality_router, prefix="/api/v1", tags=["agent-quality"])
    app.include_router(agent_quality_dashboard_router, prefix="/api/v1", tags=["agent-quality-dashboard"])
    # ml_predictions_router DELETED 2026-05-24 F10 — duplicate of ml_predictions.router included at L449
    app.include_router(calibration_dashboard_v2_router, prefix="/api/v1", tags=["calibration-dashboard"])
    app.include_router(agent_chat_ws_router)
    app.include_router(agent_chat_sse_router, prefix="/api/v1")

    # ── WebSocket ─────────────────────────────────────────────────────────────
    app.include_router(jobs_ws.router)

    # ── Compliance / LGPD ─────────────────────────────────────────────────────
    app.include_router(lgpd_compliance.router, prefix="/api/v1", tags=["lgpd-compliance"])
    app.include_router(compliance_controls.router, prefix="/api/v1", tags=["compliance-controls"])
    app.include_router(compliance_report.router, prefix="/api/v1", tags=["compliance-report"])
    app.include_router(compliance_status.router, prefix="/api/v1", tags=["compliance-status"])
    app.include_router(trust_center.router, prefix="/api/v1", tags=["trust-center"])
    app.include_router(audit_logs.router, prefix="/api/v1", tags=["audit-logs"])
    app.include_router(audit_timeline_router)
    app.include_router(data_subject_requests.router, prefix="/api/v1", tags=["data-subject-requests"])
    app.include_router(consent_management.router, prefix="/api/v1", tags=["consent-management"])
    app.include_router(granular_consent_router, prefix="/api/v1", tags=["granular-consent"])
    app.include_router(admin_consent_router, prefix="/api/v1", tags=["Admin - Consent"])  # T-21c
    app.include_router(data_request.router, prefix="/api/v1", tags=["data-requests"])
    app.include_router(admin_lgpd_router, prefix="/api/v1")
    app.include_router(incident_response_router, prefix="/api/v1")
    app.include_router(admin_compliance_fairness.router, prefix="/api/v1")
    app.include_router(bias_audit.router, prefix="/api/v1", tags=["bias-audit"])
    app.include_router(admin_bias_audit.router, prefix="/api/v1", tags=["bias-audit-admin"])
    app.include_router(bias_audit_annual.router, prefix="/api/v1", tags=["bias-audit-annual"])
    app.include_router(ai_transparency.router, prefix="/api/v1", tags=["ai-transparency"])
    app.include_router(guardrails.router, prefix="/api/v1", tags=["guardrails"])

    # ── Policy ────────────────────────────────────────────────────────────────
    app.include_router(policies.router, prefix="/api/v1", tags=["policies"])
    app.include_router(policy_engine.router, prefix="/api/v1", tags=["policy-engine"])
    app.include_router(global_policies.router, prefix="/api/v1", tags=["global-policies"])
    app.include_router(default_templates.router, prefix="/api/v1", tags=["default-templates"])
    app.include_router(hiring_policy.router, prefix="/api/v1", tags=["hiring-policy"])

    # ── LLM Config (Choose Your AI) ──────────────────────────────────────────
    app.include_router(llm_config_router_mod.router, prefix="/api/v1", tags=["llm-config"])

    # ── ATS / Integrations ────────────────────────────────────────────────────
    app.include_router(ats.router, prefix="/api/v1", tags=["ats"])
    app.include_router(webhooks.router, prefix="/api/v1", tags=["webhooks"])
    app.include_router(integrations.router, prefix="/api/v1", tags=["integrations"])
    app.include_router(integrations_hub.router, prefix="/api/v1", tags=["integration-hub"])
    app.include_router(external_webhooks.router, prefix="/api/v1", tags=["external-webhooks"])
    app.include_router(merge_webhooks.router, prefix="/api/v1", tags=["merge-webhooks"])
    app.include_router(mailgun_webhooks.router, prefix="/api/v1", tags=["mailgun-webhooks"])
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

    # ── Billing, Modules & SaaS ──────────────────────────────────────────────
    app.include_router(billing.router, prefix="/api/v1", tags=["billing"])
    app.include_router(upgrade_requests.router, prefix="/api/v1", tags=["billing"])
    app.include_router(modules.router, prefix="/api/v1", tags=["modules"])
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
    app.include_router(admin_platform.router, prefix="/api/v1", tags=["admin-platform"])
    app.include_router(admin_token_budget.router, prefix="/api/v1", tags=["admin-token-budget"])
    app.include_router(admin_prompts.router, prefix="/api/v1", tags=["admin-prompts"])
    app.include_router(admin_persona.router, prefix="/api/v1", tags=["admin-persona"])
    app.include_router(company_ai_persona.router, prefix="/api/v1", tags=["company-ai-persona"])
    app.include_router(admin_cb_router, prefix="/api/v1")
    app.include_router(admin_agents_router, prefix="/api/v1")
    app.include_router(admin_external_router, prefix="/api/v1", tags=["admin-external"])
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
    # NOTE: sector_templates_router DEVE ser registrado ANTES de agent_templates_router
    # para evitar colisão com GET /agent-templates/{template_id} — que captura "sectors"
    # como template_id e devolve 404. FastAPI resolve rotas na ordem de registro.
    app.include_router(sector_templates_router, prefix="/api/v1", tags=["sector-templates"])
    app.include_router(agent_templates_router, prefix="/api/v1", tags=["agent-templates"])
    app.include_router(agent_template_catalog_router, prefix="/api/v1", tags=["agent-template-catalog"])
    # — Phase 6: Agent Studio, Sourcing, Digital Twins, Voice Screening
    app.include_router(custom_agents_router, prefix="/api/v1", tags=["custom-agents"])
    app.include_router(agent_studio_voice_router, prefix="/api/v1", tags=["agent-studio-voice"])
    app.include_router(agent_studio_whatsapp_router, prefix="/api/v1", tags=["agent-studio-whatsapp"])
    app.include_router(agent_studio_channels_router, prefix="/api/v1", tags=["agent-studio-channels"])
    app.include_router(agent_studio_triagem_invite_router, prefix="/api/v1", tags=["agent-studio-triagem-invite"])
    app.include_router(agent_deployments_router, prefix="/api/v1")
    app.include_router(agent_deployments_target_router, prefix="/api/v1")
    app.include_router(agent_approvals_agent_router, prefix="/api/v1")
    app.include_router(agent_approvals_approvals_router, prefix="/api/v1")
    # webhooks_router DELETED 2026-05-24 F10 — duplicate of webhooks.router included at L569
    app.include_router(agent_marketplace_router, prefix="/api/v1", tags=["agent-marketplace"])
    app.include_router(admin_marketplace_router, prefix="/api/v1", tags=["admin-marketplace"])
    app.include_router(multi_strategy_router, prefix="/api/v1", tags=["multi-strategy"])
    app.include_router(digital_twins_router, prefix="/api/v1", tags=["digital-twins"])
    app.include_router(voice_screening_router, prefix="/api/v1", tags=["voice-screening"])
    app.include_router(onboarding_router, tags=["onboarding"])
    app.include_router(whatsapp_webhook_router, tags=["whatsapp"])

    # ── Public (no /api/v1 prefix) ────────────────────────────────────────────
    # ── Offer Proposals (PR-B) ──────────────────────────────────────────────
    from app.api.v1.offers import router as _offers_router
    app.include_router(_offers_router, prefix="/api/v1", tags=["offers"])

    app.include_router(candidate_portal.router, tags=["candidate-portal"])
    app.include_router(public_shared_searches.router, prefix="/api", tags=["public-shared-searches"])

    # ── Alert Rule Templates (Sprint 3 catalogos dinamicos 2026-05-21) ──────
    from app.api.v1.alert_rule_templates import router as _alert_rule_templates_router
    app.include_router(_alert_rule_templates_router, prefix="/api/v1", tags=["alert-rule-templates"])

    # ── Sprint 2 canonical (catalogos dinamicos) — pipeline_stage_templates ──
    from app.api.v1 import pipeline_stage_templates as _pipeline_stage_templates_router
    app.include_router(
        _pipeline_stage_templates_router.router,
        prefix="/api/v1",
        tags=["pipeline-stage-templates"],
    )
