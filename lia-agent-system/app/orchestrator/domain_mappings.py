"""
Centralized domain mappings — single source of truth for agent-type → domain resolution.

Used by CascadedRouter (Tier 5 LLM output mapping) and available for any module
that needs to resolve an agent type string to its canonical domain_id.
"""

AGENT_TYPE_TO_DOMAIN: dict[str, str] = {
    "job_planner": "job_management",
    "job_intake": "job_management",
    "sourcing": "sourcing",
    "cv_screening": "cv_screening",
    "screening": "cv_screening",
    "wsi_evaluator": "cv_screening",
    "interviewer": "interview_scheduling",
    "scheduling": "interview_scheduling",
    "analyst_feedback": "analytics",
    "analytics": "analytics",
    "communication": "communication",
    "ats_integrator": "ats_integration",
    "recruiter_assistant": "recruiter_assistant",
    "task_planner": "automation",
    "kanban_search": "kanban_search",
    "kanban_insight": "kanban_insight",
    "kanban_action": "kanban_action",
    "pipeline_context": "pipeline_context",
    "pipeline_decision": "pipeline_decision",
    "pipeline_action": "pipeline_action",
    "sourcing_planner": "sourcing_planner",
    "sourcing_search": "sourcing_search",
    "sourcing_enrich": "sourcing_enrich",
    "sourcing_engagement": "sourcing_engagement",
    "talent_pool": "talent_pool",
    "agent_studio": "agent_studio",
    "digital_twin": "digital_twin",
    "recruitment_campaign": "recruitment_campaign",
    "company_settings": "company_settings",
    "company_profile": "company_settings",
    "company_config": "company_settings",
    "multi_strategy": "agent_studio",
    "voice_screening": "talent_pool",
}

DEFAULT_DOMAIN = "recruiter_assistant"


def resolve_domain(intent: str) -> str:
    """Resolve an intent/agent-type string to its canonical domain_id."""
    intent_lower = str(intent).lower().strip()

    if intent_lower in AGENT_TYPE_TO_DOMAIN:
        return AGENT_TYPE_TO_DOMAIN[intent_lower]

    for agent_key, domain_id in AGENT_TYPE_TO_DOMAIN.items():
        if agent_key in intent_lower or intent_lower in agent_key:
            return domain_id

    return DEFAULT_DOMAIN


_mapping_cache: dict | None = None


def reset_mapping_cache() -> None:
    """Reset the AGENT_TYPE_TO_DOMAIN cache.

    Called by tests (via autouse fixture) to ensure a clean mapping state
    between test runs. In production the mapping is static; this is a no-op.
    """
    global _mapping_cache
    _mapping_cache = None
