"""
Task #470 — Generalised routing invariant for dual-ID entities.

Background
----------
Task #455 fixed a shadowing bug on ``/job-vacancies/{job_vacancy_id}``: a
``str``-typed item parameter silently captured the static sibling segment
``lifecycle-overview`` and the handler returned a misleading 404. The fix
combined router ordering with a regex-constrained path parameter
(``JOB_ID_PATH_PATTERN``).

ADR 003 (`docs/adr/003-id-strategy-lia-vs-rails.md`) extended the rule:
the *same* shape of route exists for **candidates**, **applications**, and
**interview/recruitment stages**, all of which are dual-ID entities (UUID
*or* Rails bigint). Today none of the static sibling routes on those
families have actually collided with item routes, but the trap is open —
adding ``/candidates/search`` next to ``GET /candidates/{candidate_id}``
without the regex would reproduce Task #455 verbatim.

This test fails the build whenever any new ``{*_id}`` path parameter on
those dual-ID routers is left as unconstrained ``str``. It complements
the original ``test_item_path_parameters_are_uuid_or_int_constrained``
which still guards ``/job-vacancies`` specifically.
"""
from __future__ import annotations

from uuid import UUID

import pytest
from fastapi.routing import APIRoute

from app.api.v1._path_patterns import DUAL_ID_PATH_PATTERN
from app.api.v1.applications import router as applications_router
from app.api.v1.candidates import router as candidates_router
from app.api.v1.lgpd_compliance import router as lgpd_compliance_router
from app.api.v1.policy_engine import router as policy_engine_router
from app.api.v1.proactive_actions import router as proactive_actions_router
from app.api.v1.recruitment_stages import (
    router as recruitment_stages_router,
    screening_questions_router,
)
from app.api.v1.wizard_analytics import router as wizard_analytics_router


# Each entry: (router, scope_label).
#
# The check auto-discovers any path parameter whose name ends in ``_id``
# rather than relying on a hardcoded allow-list — this is what makes the
# guard "generalised": a future ``{interview_id}`` or ``{note_id}`` added
# to one of these routers is automatically protected without anyone
# needing to remember to update this test.
#
# Task #458 extends the coverage to the remaining single-file ``/api/v1``
# routers that previously had unconstrained ``{*_id}: str`` path
# parameters: proactive-actions, wizard-analytics, lgpd, policy-engine.
DUAL_ID_ROUTERS = [
    pytest.param(candidates_router, "candidates", id="candidates"),
    pytest.param(applications_router, "applications", id="applications"),
    pytest.param(
        recruitment_stages_router, "recruitment-stages", id="recruitment-stages"
    ),
    pytest.param(
        screening_questions_router,
        "screening-questions",
        id="screening-questions",
    ),
    pytest.param(
        proactive_actions_router, "proactive-actions", id="proactive-actions"
    ),
    pytest.param(
        wizard_analytics_router, "wizard-analytics", id="wizard-analytics"
    ),
    pytest.param(lgpd_compliance_router, "lgpd", id="lgpd"),
    pytest.param(policy_engine_router, "policy-engine", id="policy-engine"),
]


# Task #458 — Routers where collection-before-item ordering is enforced
# in-module via ``reorder_collection_before_item``. The structural test
# below asserts that within each router every collection-scoped APIRoute
# (no ``{`` in path) is registered before any item-scoped APIRoute, so a
# future static sibling cannot be silently shadowed.
COLLECTION_BEFORE_ITEM_ROUTERS = [
    pytest.param(
        proactive_actions_router, "proactive-actions", id="proactive-actions"
    ),
    pytest.param(
        wizard_analytics_router, "wizard-analytics", id="wizard-analytics"
    ),
    pytest.param(lgpd_compliance_router, "lgpd", id="lgpd"),
    pytest.param(policy_engine_router, "policy-engine", id="policy-engine"),
]


def _api_routes(router) -> list[APIRoute]:
    return [r for r in router.routes if isinstance(r, APIRoute)]


def _param_pattern(param) -> str | None:
    """Pull the ``pattern=`` regex off a Pydantic v2 path parameter.

    Pydantic v2 attaches the regex via ``field_info.metadata`` as a
    ``_PydanticGeneralMetadata(pattern=...)`` entry rather than as a
    top-level attribute on FieldInfo, so we have to walk both shapes.
    """
    field_info = getattr(param, "field_info", None)
    if field_info is None:
        return None
    pattern = getattr(field_info, "pattern", None)
    if pattern:
        return pattern
    for meta in getattr(field_info, "metadata", None) or []:
        meta_pattern = getattr(meta, "pattern", None)
        if meta_pattern:
            return meta_pattern
    return None



# ---------------------------------------------------------------------------
# Task #489 — Sweep of remaining single-file ``/api/v1`` routers.
# Each module below previously had at least one ``{*_id}: str`` path
# parameter without the dual-ID regex constraint, exposing it to the
# Task #455-class shadowing bug. The blindagem is now applied at the
# signature level — every dual-ID path parameter is annotated with
# ``Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)]`` and each module
# calls ``reorder_collection_before_item(router)`` at its bottom. The
# two parametrize tests above run against every router below.
# ---------------------------------------------------------------------------
from app.api.v1.activities import router as _t489_activities_router
from app.api.v1.admin_audit_decisions import router as _t489_admin_audit_decisions_router
from app.api.v1.admin_bias_audit import router as _t489_admin_bias_audit_router
from app.api.v1.admin_dlq import router as _t489_admin_dlq_router
from app.api.v1.admin_external import router as _t489_admin_external_router
from app.api.v1.admin_settings import router as _t489_admin_settings_router
from app.api.v1.admin_templates import router as _t489_admin_templates_router
from app.api.v1.admin_token_budget import router as _t489_admin_token_budget_router
from app.api.v1.affirmative import router as _t489_affirmative_router
from app.api.v1.agent_chat_sse import router as _t489_agent_chat_sse_router
from app.api.v1.agent_deployments import router as _t489_agent_deployments_router
from app.api.v1.agent_explainability import router as _t489_agent_explainability_router
from app.api.v1.agent_memory import router as _t489_agent_memory_router
from app.api.v1.agent_monitoring import router as _t489_agent_monitoring_router
from app.api.v1.agent_quality import router as _t489_agent_quality_router
from app.api.v1.agent_studio_quality import router as _t489_agent_studio_quality_router
from app.api.v1.agent_templates import router as _t489_agent_templates_router
from app.api.v1.ai_consumption import router as _t489_ai_consumption_router
from app.api.v1.alerts import router as _t489_alerts_router
from app.api.v1.approvals import router as _t489_approvals_router
from app.api.v1.async_endpoints import router as _t489_async_endpoints_router
from app.api.v1.ats import router as _t489_ats_router
from app.api.v1.attachments import router as _t489_attachments_router
from app.api.v1.audit_logs import router as _t489_audit_logs_router
from app.api.v1.audit_timeline import router as _t489_audit_timeline_router
from app.api.v1.automations import router as _t489_automations_router
from app.api.v1.bias_audit import router as _t489_bias_audit_router
from app.api.v1.big_five import router as _t489_big_five_router
from app.api.v1.billing import router as _t489_billing_router
from app.api.v1.cache import router as _t489_cache_router
from app.api.v1.calibration import router as _t489_calibration_router
from app.api.v1.candidate_lists import router as _t489_candidate_lists_router
from app.api.v1.client_users import router as _t489_client_users_router
from app.api.v1.communication_matrix import router as _t489_communication_matrix_router
from app.api.v1.communications import router as _t489_communications_router
from app.api.v1.company_users import router as _t489_company_users_router
from app.api.v1.compliance_controls import router as _t489_compliance_controls_router
from app.api.v1.consent_management import router as _t489_consent_management_router
from app.api.v1.consumption import router as _t489_consumption_router
from app.api.v1.conversations import router as _t489_conversations_router
from app.api.v1.cultural_fit import router as _t489_cultural_fit_router
from app.api.v1.custom_agents import router as _t489_custom_agents_router
from app.api.v1.data_subject_requests import router as _t489_data_subject_requests_router
from app.api.v1.decision_explanation import router as _t489_decision_explanation_router
from app.api.v1.digital_twins import router as _t489_digital_twins_router
from app.api.v1.email import router as _t489_email_router
from app.api.v1.email_templates import router as _t489_email_templates_router
from app.api.v1.email_tracking import router as _t489_email_tracking_router
from app.api.v1.event_history import router as _t489_event_history_router
from app.api.v1.experience_highlights import router as _t489_experience_highlights_router
from app.api.v1.fairness_reports import router as _t489_fairness_reports_router
# Task #306 — finetuning_export no longer has any ``{*_id}`` path params
# (company_id is now derived from the JWT, not the URL), so it is no
# longer subject to the dual-ID shadowing invariant.
from app.api.v1.gemini_voice import router as _t489_gemini_voice_router
from app.api.v1.global_policies import router as _t489_global_policies_router
from app.api.v1.goals import router as _t489_goals_router
from app.api.v1.granular_consent import router as _t489_granular_consent_router
from app.api.v1.guardrails import router as _t489_guardrails_router
from app.api.v1.health_check import router as _t489_health_check_router
from app.api.v1.hiring_policy import router as _t489_hiring_policy_router
from app.api.v1.hitl import router as _t489_hitl_router
from app.api.v1.integrations_hub import router as _t489_integrations_hub_router
from app.api.v1.interview_analysis import router as _t489_interview_analysis_router
from app.api.v1.interview_notes import router as _t489_interview_notes_router
from app.api.v1.interviews import router as _t489_interviews_router
from app.api.v1.job_analytics import router as _t489_job_analytics_router
from app.api.v1.job_embeddings import router as _t489_job_embeddings_router
from app.api.v1.job_learning import router as _t489_job_learning_router
from app.api.v1.job_qualification import router as _t489_job_qualification_router
from app.api.v1.job_templates import router as _t489_job_templates_router
from app.api.v1.learning_outcomes import router as _t489_learning_outcomes_router
from app.api.v1.learning_patterns import router as _t489_learning_patterns_router
from app.api.v1.lia_field_toggles import router as _t489_lia_field_toggles_router
from app.api.v1.lia_profile_analysis import router as _t489_lia_profile_analysis_router
from app.api.v1.microsoft_graph import router as _t489_microsoft_graph_router
from app.api.v1.ml_predictions import router as _t489_ml_predictions_router
from app.api.v1.modules import router as _t489_modules_router
from app.api.v1.multi_channel import router as _t489_multi_channel_router
from app.api.v1.notifications import router as _t489_notifications_router
from app.api.v1.observability import router as _t489_observability_router
from app.api.v1.onboarding import router as _t489_onboarding_router
from app.api.v1.organization_catalog import router as _t489_organization_catalog_router
from app.api.v1.pipeline_policy import router as _t489_pipeline_policy_router
from app.api.v1.pipeline_templates import router as _t489_pipeline_templates_router
from app.api.v1.policies import router as _t489_policies_router
from app.api.v1.predictive_analytics import router as _t489_predictive_analytics_router
from app.api.v1.rails_sync import router as _t489_rails_sync_router
from app.api.v1.recruiter_behavior import router as _t489_recruiter_behavior_router
from app.api.v1.recruiter_metrics import router as _t489_recruiter_metrics_router
from app.api.v1.recruitment_campaigns import router as _t489_recruitment_campaigns_router
from app.api.v1.recruitment_email_templates import router as _t489_recruitment_email_templates_router
from app.api.v1.recruitment_journey import router as _t489_recruitment_journey_router
from app.api.v1.reports import router as _t489_reports_router
from app.api.v1.saas_metrics import router as _t489_saas_metrics_router
from app.api.v1.scheduling import router as _t489_scheduling_router
from app.api.v1.screening import router as _t489_screening_router
from app.api.v1.screening_questions import router as _t489_screening_questions_router
from app.api.v1.search_feedback import router as _t489_search_feedback_router
from app.api.v1.shared_searches import router as _t489_shared_searches_router
from app.api.v1.short_lists import router as _t489_short_lists_router
from app.api.v1.sourcing import router as _t489_sourcing_router
from app.api.v1.sourcing_agents import router as _t489_sourcing_agents_router
from app.api.v1.sourcing_pipeline import router as _t489_sourcing_pipeline_router
from app.api.v1.suggestion_feedback import router as _t489_suggestion_feedback_router
from app.api.v1.task_lifecycle import router as _t489_task_lifecycle_router
from app.api.v1.task_monitoring import router as _t489_task_monitoring_router
from app.api.v1.task_planner import router as _t489_task_planner_router
from app.api.v1.tasks import router as _t489_tasks_router
from app.api.v1.technical_tests import router as _t489_technical_tests_router
from app.api.v1.toon import router as _t489_toon_router
from app.api.v1.triagem import router as _t489_triagem_router
from app.api.v1.twilio_voice import router as _t489_twilio_voice_router
from app.api.v1.voice_screening import router as _t489_voice_screening_router
from app.api.v1.webhooks import router as _t489_webhooks_router
from app.api.v1.workforce_planning import router as _t489_workforce_planning_router
from app.api.v1.workos import router as _t489_workos_router
from app.api.v1.wsi_observability import router as _t489_wsi_observability_router

_TASK_489_DUAL_ID_PARAMS = [
    pytest.param(_t489_activities_router, "activities", id="activities"),
    pytest.param(_t489_admin_audit_decisions_router, "admin-audit-decisions", id="admin-audit-decisions"),
    pytest.param(_t489_admin_bias_audit_router, "admin-bias-audit", id="admin-bias-audit"),
    pytest.param(_t489_admin_dlq_router, "admin-dlq", id="admin-dlq"),
    pytest.param(_t489_admin_external_router, "admin-external", id="admin-external"),
    pytest.param(_t489_admin_settings_router, "admin-settings", id="admin-settings"),
    pytest.param(_t489_admin_templates_router, "admin-templates", id="admin-templates"),
    pytest.param(_t489_admin_token_budget_router, "admin-token-budget", id="admin-token-budget"),
    pytest.param(_t489_affirmative_router, "affirmative", id="affirmative"),
    pytest.param(_t489_agent_chat_sse_router, "agent-chat-sse", id="agent-chat-sse"),
    pytest.param(_t489_agent_deployments_router, "agent-deployments", id="agent-deployments"),
    pytest.param(_t489_agent_explainability_router, "agent-explainability", id="agent-explainability"),
    pytest.param(_t489_agent_memory_router, "agent-memory", id="agent-memory"),
    pytest.param(_t489_agent_monitoring_router, "agent-monitoring", id="agent-monitoring"),
    pytest.param(_t489_agent_quality_router, "agent-quality", id="agent-quality"),
    pytest.param(_t489_agent_studio_quality_router, "agent-studio-quality", id="agent-studio-quality"),
    pytest.param(_t489_agent_templates_router, "agent-templates", id="agent-templates"),
    pytest.param(_t489_ai_consumption_router, "ai-consumption", id="ai-consumption"),
    pytest.param(_t489_alerts_router, "alerts", id="alerts"),
    pytest.param(_t489_approvals_router, "approvals", id="approvals"),
    pytest.param(_t489_async_endpoints_router, "async-endpoints", id="async-endpoints"),
    pytest.param(_t489_ats_router, "ats", id="ats"),
    pytest.param(_t489_attachments_router, "attachments", id="attachments"),
    pytest.param(_t489_audit_logs_router, "audit-logs", id="audit-logs"),
    pytest.param(_t489_audit_timeline_router, "audit-timeline", id="audit-timeline"),
    pytest.param(_t489_automations_router, "automations", id="automations"),
    pytest.param(_t489_bias_audit_router, "bias-audit", id="bias-audit"),
    pytest.param(_t489_big_five_router, "big-five", id="big-five"),
    pytest.param(_t489_billing_router, "billing", id="billing"),
    pytest.param(_t489_cache_router, "cache", id="cache"),
    pytest.param(_t489_calibration_router, "calibration", id="calibration"),
    pytest.param(_t489_candidate_lists_router, "candidate-lists", id="candidate-lists"),
    pytest.param(_t489_client_users_router, "client-users", id="client-users"),
    pytest.param(_t489_communication_matrix_router, "communication-matrix", id="communication-matrix"),
    pytest.param(_t489_communications_router, "communications", id="communications"),
    pytest.param(_t489_company_users_router, "company-users", id="company-users"),
    pytest.param(_t489_compliance_controls_router, "compliance-controls", id="compliance-controls"),
    pytest.param(_t489_consent_management_router, "consent-management", id="consent-management"),
    pytest.param(_t489_consumption_router, "consumption", id="consumption"),
    pytest.param(_t489_conversations_router, "conversations", id="conversations"),
    pytest.param(_t489_cultural_fit_router, "cultural-fit", id="cultural-fit"),
    pytest.param(_t489_custom_agents_router, "custom-agents", id="custom-agents"),
    pytest.param(_t489_data_subject_requests_router, "data-subject-requests", id="data-subject-requests"),
    pytest.param(_t489_decision_explanation_router, "decision-explanation", id="decision-explanation"),
    pytest.param(_t489_digital_twins_router, "digital-twins", id="digital-twins"),
    pytest.param(_t489_email_router, "email", id="email"),
    pytest.param(_t489_email_templates_router, "email-templates", id="email-templates"),
    pytest.param(_t489_email_tracking_router, "email-tracking", id="email-tracking"),
    pytest.param(_t489_event_history_router, "event-history", id="event-history"),
    pytest.param(_t489_experience_highlights_router, "experience-highlights", id="experience-highlights"),
    pytest.param(_t489_fairness_reports_router, "fairness-reports", id="fairness-reports"),
    pytest.param(_t489_gemini_voice_router, "gemini-voice", id="gemini-voice"),
    pytest.param(_t489_global_policies_router, "global-policies", id="global-policies"),
    pytest.param(_t489_goals_router, "goals", id="goals"),
    pytest.param(_t489_granular_consent_router, "granular-consent", id="granular-consent"),
    pytest.param(_t489_guardrails_router, "guardrails", id="guardrails"),
    pytest.param(_t489_health_check_router, "health-check", id="health-check"),
    pytest.param(_t489_hiring_policy_router, "hiring-policy", id="hiring-policy"),
    pytest.param(_t489_hitl_router, "hitl", id="hitl"),
    pytest.param(_t489_integrations_hub_router, "integrations-hub", id="integrations-hub"),
    pytest.param(_t489_interview_analysis_router, "interview-analysis", id="interview-analysis"),
    pytest.param(_t489_interview_notes_router, "interview-notes", id="interview-notes"),
    pytest.param(_t489_interviews_router, "interviews", id="interviews"),
    pytest.param(_t489_job_analytics_router, "job-analytics", id="job-analytics"),
    pytest.param(_t489_job_embeddings_router, "job-embeddings", id="job-embeddings"),
    pytest.param(_t489_job_learning_router, "job-learning", id="job-learning"),
    pytest.param(_t489_job_qualification_router, "job-qualification", id="job-qualification"),
    pytest.param(_t489_job_templates_router, "job-templates", id="job-templates"),
    pytest.param(_t489_learning_outcomes_router, "learning-outcomes", id="learning-outcomes"),
    pytest.param(_t489_learning_patterns_router, "learning-patterns", id="learning-patterns"),
    pytest.param(_t489_lia_field_toggles_router, "lia-field-toggles", id="lia-field-toggles"),
    pytest.param(_t489_lia_profile_analysis_router, "lia-profile-analysis", id="lia-profile-analysis"),
    pytest.param(_t489_microsoft_graph_router, "microsoft-graph", id="microsoft-graph"),
    pytest.param(_t489_ml_predictions_router, "ml-predictions", id="ml-predictions"),
    pytest.param(_t489_modules_router, "modules", id="modules"),
    pytest.param(_t489_multi_channel_router, "multi-channel", id="multi-channel"),
    pytest.param(_t489_notifications_router, "notifications", id="notifications"),
    pytest.param(_t489_observability_router, "observability", id="observability"),
    pytest.param(_t489_onboarding_router, "onboarding", id="onboarding"),
    pytest.param(_t489_organization_catalog_router, "organization-catalog", id="organization-catalog"),
    pytest.param(_t489_pipeline_policy_router, "pipeline-policy", id="pipeline-policy"),
    pytest.param(_t489_pipeline_templates_router, "pipeline-templates", id="pipeline-templates"),
    pytest.param(_t489_policies_router, "policies", id="policies"),
    pytest.param(_t489_predictive_analytics_router, "predictive-analytics", id="predictive-analytics"),
    pytest.param(_t489_rails_sync_router, "rails-sync", id="rails-sync"),
    pytest.param(_t489_recruiter_behavior_router, "recruiter-behavior", id="recruiter-behavior"),
    pytest.param(_t489_recruiter_metrics_router, "recruiter-metrics", id="recruiter-metrics"),
    pytest.param(_t489_recruitment_campaigns_router, "recruitment-campaigns", id="recruitment-campaigns"),
    pytest.param(_t489_recruitment_email_templates_router, "recruitment-email-templates", id="recruitment-email-templates"),
    pytest.param(_t489_recruitment_journey_router, "recruitment-journey", id="recruitment-journey"),
    pytest.param(_t489_reports_router, "reports", id="reports"),
    pytest.param(_t489_saas_metrics_router, "saas-metrics", id="saas-metrics"),
    pytest.param(_t489_scheduling_router, "scheduling", id="scheduling"),
    pytest.param(_t489_screening_router, "screening", id="screening"),
    pytest.param(_t489_screening_questions_router, "screening-questions", id="screening-questions"),
    pytest.param(_t489_search_feedback_router, "search-feedback", id="search-feedback"),
    pytest.param(_t489_shared_searches_router, "shared-searches", id="shared-searches"),
    pytest.param(_t489_short_lists_router, "short-lists", id="short-lists"),
    pytest.param(_t489_sourcing_router, "sourcing", id="sourcing"),
    pytest.param(_t489_sourcing_agents_router, "sourcing-agents", id="sourcing-agents"),
    pytest.param(_t489_sourcing_pipeline_router, "sourcing-pipeline", id="sourcing-pipeline"),
    pytest.param(_t489_suggestion_feedback_router, "suggestion-feedback", id="suggestion-feedback"),
    pytest.param(_t489_task_lifecycle_router, "task-lifecycle", id="task-lifecycle"),
    pytest.param(_t489_task_monitoring_router, "task-monitoring", id="task-monitoring"),
    pytest.param(_t489_task_planner_router, "task-planner", id="task-planner"),
    pytest.param(_t489_tasks_router, "tasks", id="tasks"),
    pytest.param(_t489_technical_tests_router, "technical-tests", id="technical-tests"),
    pytest.param(_t489_toon_router, "toon", id="toon"),
    pytest.param(_t489_triagem_router, "triagem", id="triagem"),
    pytest.param(_t489_twilio_voice_router, "twilio-voice", id="twilio-voice"),
    pytest.param(_t489_voice_screening_router, "voice-screening", id="voice-screening"),
    pytest.param(_t489_webhooks_router, "webhooks", id="webhooks"),
    pytest.param(_t489_workforce_planning_router, "workforce-planning", id="workforce-planning"),
    pytest.param(_t489_workos_router, "workos", id="workos"),
    pytest.param(_t489_wsi_observability_router, "wsi-observability", id="wsi-observability"),
]

DUAL_ID_ROUTERS = DUAL_ID_ROUTERS + _TASK_489_DUAL_ID_PARAMS
COLLECTION_BEFORE_ITEM_ROUTERS = COLLECTION_BEFORE_ITEM_ROUTERS + _TASK_489_DUAL_ID_PARAMS


@pytest.mark.parametrize(("router", "scope_label"), DUAL_ID_ROUTERS)
def test_dual_id_path_parameters_are_constrained(
    router, scope_label: str
) -> None:
    """Every ``{*_id}`` path parameter on a dual-ID router must reject
    anything that is not a UUID or a decimal integer.

    Without this constraint, a sibling static route added in the future
    (e.g. ``/candidates/search``) could be silently captured by an item
    handler and return 404 instead of being routed to its real handler —
    the exact failure mode of Task #455.

    The check is structural and self-updating: it auto-discovers any
    path parameter whose name ends in ``_id``, so a new ``{interview_id}``
    or ``{note_id}`` added to one of these routers is automatically
    protected without anyone needing to remember to update this test.
    The parameter must either be typed as ``UUID`` (FastAPI
    auto-validates) OR carry an explicit ``pattern`` attached via
    ``Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)]``.
    """
    offenders: list[str] = []

    for r in _api_routes(router):
        if "{" not in r.path:
            continue
        for param in r.dependant.path_params:
            if not param.name.endswith("_id"):
                continue
            annotation = getattr(param, "type_", None)
            if annotation is UUID:
                continue
            if annotation is int:
                continue
            pattern = _param_pattern(param)
            if not pattern:
                offenders.append(f"{r.path}:{param.name}")

    assert not offenders, (
        f"The following item-route path parameters in the {scope_label!r} "
        f"router are unconstrained `str` and would silently shadow any "
        f"new static sibling route (Task #455-class bug):\n  - "
        + "\n  - ".join(offenders)
        + "\nConstrain them with "
        "`Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)]` from "
        "`app.api.v1._path_patterns`."
    )


@pytest.mark.parametrize(
    ("router", "scope_label"), COLLECTION_BEFORE_ITEM_ROUTERS
)
def test_collection_routes_precede_item_routes(router, scope_label: str) -> None:
    """Within each single-file router that opted into the Task #458
    blindagem, every collection-scoped ``APIRoute`` must be registered
    before any item-scoped ``APIRoute``.

    FastAPI uses first-match routing, so the position of a route in
    ``router.routes`` is the source of truth. The
    ``reorder_collection_before_item`` helper is invoked at the bottom
    of each opted-in module to guarantee this; this test breaks the
    build if either the helper call is removed or new routes are
    appended after it without re-running it.
    """
    routes = _api_routes(router)
    # Index of the LAST collection-scoped route, then the FIRST item-
    # scoped route. The first must come before the second.
    last_collection_idx = -1
    first_item_idx = None
    for idx, r in enumerate(routes):
        if "{" in r.path:
            if first_item_idx is None:
                first_item_idx = idx
        else:
            last_collection_idx = idx

    if first_item_idx is None or last_collection_idx == -1:
        # Router has only one kind of route — invariant trivially holds.
        return

    assert last_collection_idx < first_item_idx, (
        f"In the {scope_label!r} router, a collection-scoped route at "
        f"index {last_collection_idx} is registered AFTER an item-scoped "
        f"route at index {first_item_idx}. This reintroduces the Task "
        f"#455 routing-shadowing bug — the static collection segment "
        f"will be silently captured by the item handler. Make sure "
        f"``reorder_collection_before_item(router)`` runs at the bottom "
        f"of the module after all routes are declared."
    )


def test_dual_id_path_pattern_accepts_uuid_and_bigint() -> None:
    """Sanity-check the regex itself: it must accept UUIDs and decimal
    integers, and reject anything else (so static sibling segments stay
    safe from item-route capture).
    """
    import re

    rx = re.compile(DUAL_ID_PATH_PATTERN)
    # accept
    assert rx.match("550e8400-e29b-41d4-a716-446655440000")
    assert rx.match("12345")
    assert rx.match("1")
    # reject — these are the segments most at risk of shadowing
    assert not rx.match("search")
    assert not rx.match("lifecycle-overview")
    assert not rx.match("favorites")
    assert not rx.match("hidden")
    assert not rx.match("viewed")
    assert not rx.match("health")
    assert not rx.match("12345abc")
    assert not rx.match("")


# =============================================
# Task #476 — Whole-app structural guard
# =============================================
#
# The router-by-router check above is precise but it relies on someone
# remembering to add a new dual-ID router to ``DUAL_ID_ROUTERS`` whenever
# one is created. That's exactly the human-memory step that burned us in
# Tasks #455, #459, and #468 (a new endpoint shipped that skipped the ID
# safety rule, and nobody noticed until production).
#
# The test below does NOT rely on that allow-list. It imports the real
# FastAPI app, walks every registered route, and fails the build the
# moment a route under one of the dual-ID URL spaces declared in ADR 003
# (``/api/v1/job-vacancies``, ``/api/v1/public-vacancies``,
# ``/api/v1/candidates``, ``/api/v1/applications``,
# ``/api/v1/recruitment-stages``) carries an item-route path parameter
# whose name ends in ``_id`` and is typed as bare ``str`` (no UUID
# annotation, no ``pattern=DUAL_ID_PATH_PATTERN``).
#
# This is the "structural test that fails the build when somebody adds a
# new ``{*_id}: str`` path parameter on a dual-ID resource without the
# dual-ID regex" called for by the ID Boundary Policy
# (`docs/architecture/id-boundary-policy.md`, §3 and §8).

# Every URL-space that ADR 003 designates as dual-ID. Adding a new
# dual-ID resource here is a one-line opt-in; the rest of the check is
# automatic. The list intentionally lives next to the test rather than
# next to the routers themselves so this file remains the single source
# of truth — the policy check shouldn't be silently disabled by editing
# the router being checked.
DUAL_ID_URL_PREFIXES: tuple[str, ...] = (
    "/api/v1/job-vacancies",
    "/api/v1/public-vacancies",
    "/api/v1/candidates",
    "/api/v1/applications",
    "/api/v1/recruitment-stages",
)


def test_every_dual_id_route_constrains_id_path_params() -> None:
    """Walk every route registered on the real FastAPI app and fail if
    any path parameter ending in ``_id`` on a dual-ID resource is typed
    as bare ``str`` without the dual-ID regex.

    This is the *generalised* version of
    ``test_item_path_parameters_are_uuid_or_int_constrained`` (which
    covers ``/job-vacancies`` only) and the per-router parametrised
    check above (which covers a hand-maintained list of routers).

    Why a third check? Because both of the existing checks rely on a
    human remembering to extend an allow-list. This one does not — it
    starts from the real ``app.routes`` and only asks whether each route
    falls under a dual-ID URL space (per ADR 003, see
    ``DUAL_ID_URL_PREFIXES`` above). A new endpoint added under any of
    those spaces is policed automatically; if it skips the safety rule,
    the build fails with a message that points at the policy.
    """
    from app.main import app  # noqa: PLC0415 — heavy import, kept lazy

    offenders: list[str] = []

    for route in app.routes:
        if not isinstance(route, APIRoute):
            continue
        path = route.path
        if not any(path.startswith(prefix) for prefix in DUAL_ID_URL_PREFIXES):
            continue
        if "{" not in path:
            continue
        for param in route.dependant.path_params:
            if not param.name.endswith("_id"):
                continue
            annotation = getattr(param, "type_", None)
            if annotation is UUID:
                continue
            pattern = _param_pattern(param)
            # The contract is the dual-ID regex specifically — any other
            # regex (e.g. a tighter UUID-only one, or a free-form match)
            # would either be too narrow to accept Rails bigints or too
            # loose to reject sibling static segments. Require equality
            # so the policy can't be silently weakened.
            if pattern == DUAL_ID_PATH_PATTERN:
                continue
            methods = ",".join(sorted(route.methods or {"?"}))
            suffix = f" (current pattern: {pattern!r})" if pattern else ""
            offenders.append(f"{methods} {path}:{param.name}{suffix}")

    assert not offenders, (
        "The following routes live under a dual-ID URL space (per ADR "
        "003) but declare a `{*_id}` path parameter as unconstrained "
        "`str`. This is a Task #455-class bug: a sibling static segment "
        "(e.g. `/candidates/search`) can be silently captured by the "
        "item handler and surface as a misleading 404.\n  - "
        + "\n  - ".join(sorted(offenders))
        + "\n\nFix: type the parameter as `UUID`, OR declare it as "
        "`Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)]` from "
        "`app.api.v1._path_patterns`. See the ID Boundary Policy: "
        "`docs/architecture/id-boundary-policy.md` §3 and the checklist "
        "in §8."
    )


def test_dual_id_constraint_rejects_garbage_at_runtime() -> None:
    """End-to-end behavioural check that the signature-level
    ``Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)]`` constraint
    actually causes FastAPI to return a 422 for a non-UUID, non-digit
    path segment — proving the structural test corresponds to real
    routing behaviour and not a no-op metadata attribute.

    Uses ``activities`` as a representative sweep router because it is
    one of the simpler modules touched by Task #489 and has a
    ``GET /{activity_id}`` item route.
    """
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from app.api.v1.activities import router as activities_router

    app = FastAPI()
    app.include_router(activities_router, prefix="/api/v1")
    client = TestClient(app, raise_server_exceptions=False)

    # Garbage segment must be rejected by the path-param regex BEFORE
    # any handler / dependency runs.
    resp = client.get("/api/v1/activities/not-a-valid-id")
    assert resp.status_code == 422, (
        f"Expected 422 for non-UUID/non-digit activity_id, got "
        f"{resp.status_code}: {resp.text[:200]}"
    )

    # And a real-shaped UUID must at least pass the regex (it can
    # subsequently 4xx/5xx for downstream reasons — we only care that
    # the constraint did not reject it).
    resp_uuid = client.get(
        "/api/v1/activities/00000000-0000-0000-0000-000000000000"
    )
    assert resp_uuid.status_code != 422, (
        f"UUID activity_id should not be rejected by path-param "
        f"regex; got 422: {resp_uuid.text[:200]}"
    )


def test_job_id_path_pattern_alias_still_exported() -> None:
    """``JOB_ID_PATH_PATTERN`` is kept as an alias of
    ``DUAL_ID_PATH_PATTERN`` for backward compatibility with existing
    job-vacancy handlers. Removing the alias would silently drop the
    constraint everywhere it's still imported by name.
    """
    from app.api.v1.job_vacancies._shared import JOB_ID_PATH_PATTERN

    assert JOB_ID_PATH_PATTERN == DUAL_ID_PATH_PATTERN
