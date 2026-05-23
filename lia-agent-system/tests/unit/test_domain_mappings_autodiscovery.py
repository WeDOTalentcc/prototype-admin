"""Anti-drift tests for AGENT_TYPE_TO_DOMAIN auto-discovery (Task #584).

Guarantees:
1. Every entry in AGENT_TYPE_TO_DOMAIN points to a domain that is actually
   registered in DomainRegistry (no orphan agent-types).
2. Each domain's `domain_id` is in the mapping under its own key.
3. Aliases declared on a domain class via `agent_aliases` show up in the
   mapping pointing to that domain.
"""
from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _ensure_domains_loaded():
    # Import side-effect: registers all domains via @register_domain.
    import app.domains  # noqa: F401
    from app.orchestrator.routing.domain_mappings import reset_mapping_cache
    reset_mapping_cache()
    yield
    reset_mapping_cache()


def _registered_domain_ids() -> set[str]:
    from app.domains.registry import DomainRegistry
    return set(DomainRegistry().list_domains())


def test_no_orphan_agent_types():
    """Every alias in AGENT_TYPE_TO_DOMAIN must point to a registered domain."""
    from app.orchestrator.routing.domain_mappings import AGENT_TYPE_TO_DOMAIN

    registered = _registered_domain_ids()
    orphans = {
        alias: target
        for alias, target in AGENT_TYPE_TO_DOMAIN.items()
        if target not in registered
    }
    assert not orphans, (
        f"Orphan agent-type aliases (target domain not registered): {orphans}. "
        f"Registered domains: {sorted(registered)}"
    )


def test_every_domain_id_is_self_mapped():
    """Each registered domain must appear in the mapping under its own id."""
    from app.orchestrator.routing.domain_mappings import AGENT_TYPE_TO_DOMAIN

    missing = []
    for domain_id in _registered_domain_ids():
        if AGENT_TYPE_TO_DOMAIN.get(domain_id) != domain_id:
            missing.append(domain_id)
    assert not missing, f"Domain ids missing self-mapping: {missing}"


def test_declared_aliases_are_present():
    """Every alias declared via `agent_aliases` must resolve to its domain."""
    from app.domains.registry import _DOMAIN_REGISTRY
    from app.orchestrator.routing.domain_mappings import AGENT_TYPE_TO_DOMAIN

    mismatches: list[tuple[str, str, str | None]] = []
    for domain_id, cls in _DOMAIN_REGISTRY.items():
        for alias in cls.get_agent_aliases():
            actual = AGENT_TYPE_TO_DOMAIN.get(alias)
            if actual != domain_id:
                mismatches.append((alias, domain_id, actual))
    assert not mismatches, (
        f"Aliases not pointing to declaring domain: {mismatches}"
    )


# Frozen contract: aliases that existed in the hand-maintained dict before
# task #584. Auto-discovery must continue to cover all of these so callers
# emitting legacy agent-type strings keep resolving to the same domain.
LEGACY_ALIAS_CONTRACT: dict[str, str] = {
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
    "kanban_search": "pipeline_transition",
    "kanban_insight": "pipeline_transition",
    "kanban_action": "pipeline_transition",
    "pipeline_context": "pipeline_transition",
    "pipeline_decision": "pipeline_transition",
    "pipeline_action": "pipeline_transition",
    "sourcing_planner": "sourcing",
    "sourcing_search": "sourcing",
    "sourcing_enrich": "sourcing",
    "sourcing_engagement": "sourcing",
    "talent_pool": "talent_pool",
    "agent_studio": "agent_studio",
    "digital_twin": "digital_twin",
    "recruitment_campaign": "recruitment_campaign",
    "multi_strategy": "agent_studio",
    "voice_screening": "talent_pool",
    "candidate_self_service": "candidate_self_service",
    "candidate_status": "candidate_self_service",
    "candidate_portal": "candidate_self_service",
    "settings_config": "company_settings",
    "company_settings": "company_settings",
    "company_profile": "company_settings",
    "company_config": "company_settings",
}


def test_legacy_alias_contract_preserved():
    """No legacy agent-type alias may regress after the auto-discovery refactor."""
    from app.orchestrator.routing.domain_mappings import AGENT_TYPE_TO_DOMAIN, resolve_domain

    missing = {
        alias: expected
        for alias, expected in LEGACY_ALIAS_CONTRACT.items()
        if AGENT_TYPE_TO_DOMAIN.get(alias) != expected
    }
    assert not missing, (
        f"Legacy aliases regressed (alias: expected_domain): {missing}. "
        "Add the alias via `agent_aliases = (...)` on the owning domain."
    )

    # resolve_domain must agree (covers the substring fallback path too).
    for alias, expected in LEGACY_ALIAS_CONTRACT.items():
        assert resolve_domain(alias) == expected, (
            f"resolve_domain({alias!r}) != {expected!r}"
        )


def test_resolve_domain_uses_autodiscovered_mapping():
    """resolve_domain() should leverage the auto-built mapping."""
    from app.orchestrator.routing.domain_mappings import DEFAULT_DOMAIN, resolve_domain

    # Direct domain id resolves to itself when registered.
    assert resolve_domain("sourcing") == "sourcing"
    # Unknown intent falls back to default.
    assert resolve_domain("totally_unknown_intent_xyz") == DEFAULT_DOMAIN
