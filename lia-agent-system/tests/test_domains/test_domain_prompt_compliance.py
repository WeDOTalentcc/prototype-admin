"""
UC-P0-01 — Smoke test: every domain must inject LGPD/fairness compliance blocks.

All 19 domain classes that extend ComplianceDomainPrompt must call
super().get_system_prompt(base_prompt=...) so that the compliance, fairness,
anti-hallucination, multi-tenancy and anti-sycophancy blocks reach the LLM.

This test was written BEFORE the fix (TDD) and must FAIL initially.
After fix all 19 cases must PASS.
"""
import pytest
from unittest.mock import MagicMock


# ---------------------------------------------------------------------------
# Minimal DomainContext stub so domains can be instantiated without DB/env
# ---------------------------------------------------------------------------
def _make_context(**kwargs):
    from app.domains.base import DomainContext
    return DomainContext(
        domain_id=kwargs.get("domain_id", "job_creation"),
        user_id=kwargs.get("user_id", "user-test"),
        tenant_id=kwargs.get("tenant_id", "company-test"),
        session_id=kwargs.get("session_id", "session-test"),
        metadata=kwargs.get("metadata", {"wizard_state": {"current_stage": "intake"}}),
    )


# ---------------------------------------------------------------------------
# Compliance markers that MUST appear in every system prompt after the fix.
# Sourced from app/prompts/shared/compliance_block.yaml (decision/operational)
# and the fallback strings in compliance_base.py.
# ---------------------------------------------------------------------------
COMPLIANCE_MARKERS = [
    # LGPD block (either YAML or fallback)
    "LGPD",
]

FULL_COMPLIANCE_MARKERS = [
    "LGPD",
    # Non-discrimination block
    "NÃO DISCRIMINAÇÃO",
]


# ---------------------------------------------------------------------------
# Domain test matrix — (domain_path, class_name, needs_context)
# needs_context=True for domains whose get_system_prompt accepts context arg
# ---------------------------------------------------------------------------
DOMAIN_CASES = [
    # (import_path, class_name, call_with_context)
    ("app.domains.pipeline.domain",              "PipelineTransitionDomain",  False),
    ("app.domains.hiring_policy.domain",         "HiringPolicyDomain",        False),
    ("app.domains.sourcing.domain",              "SourcingDomain",            False),
    ("app.domains.job_management.domain",        "JobManagementDomain",       False),
    ("app.domains.communication.domain",         "CommunicationDomain",       False),
    ("app.domains.analytics.domain",             "AnalyticsDomain",           False),
    ("app.domains.interview_scheduling.domain",  "InterviewSchedulingDomain", False),
    ("app.domains.ats_integration.domain",       "ATSIntegrationDomain",      False),
    ("app.domains.automation.domain",            "AutomationDomain",          False),
    ("app.domains.recruiter_assistant.domain",   "RecruiterAssistantDomain",  False),
    ("app.domains.agent_studio.domain",          "AgentStudioDomain",         False),
    ("app.domains.digital_twin.domain",          "DigitalTwinDomain",         False),
    ("app.domains.recruitment_campaign.domain",  "RecruitmentCampaignDomain", False),
    ("app.domains.talent_pool.domain",           "TalentPoolDomain",          False),
    ("app.domains.company_settings.domain",      "CompanySettingsDomain",     False),
    ("app.domains.candidate_self_service.domain","CandidateSelfServiceDomain",False),
    ("app.domains.offer.domain",                 "OfferDomain",               False),
    ("app.domains.job_creation.domain",          "JobCreationDomain",         True),
]


def _import_class(module_path: str, class_name: str):
    import importlib
    mod = importlib.import_module(module_path)
    return getattr(mod, class_name)


def _get_prompt(cls, call_with_context: bool) -> str:
    instance = cls()
    if call_with_context:
        ctx = _make_context()
        return instance.get_system_prompt(ctx)
    return instance.get_system_prompt()


# ---------------------------------------------------------------------------
# Parametrized tests
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("module_path,class_name,call_with_context", DOMAIN_CASES,
                         ids=[c[1] for c in DOMAIN_CASES])
def test_domain_prompt_contains_lgpd_marker(module_path, class_name, call_with_context):
    """Every domain.get_system_prompt() must contain the LGPD compliance marker."""
    cls = _import_class(module_path, class_name)
    prompt = _get_prompt(cls, call_with_context)

    assert isinstance(prompt, str), f"{class_name}.get_system_prompt() must return str"
    assert len(prompt) > 50, f"{class_name}.get_system_prompt() returned suspiciously short prompt"
    assert "LGPD" in prompt, (
        f"{class_name}.get_system_prompt() missing LGPD compliance block. "
        f"Fix: call super().get_system_prompt(base_prompt=<domain_specific>) and return its result. "
        f"See compliance_base.py:180 and UC-P0-01."
    )


@pytest.mark.parametrize("module_path,class_name,call_with_context", DOMAIN_CASES,
                         ids=[c[1] for c in DOMAIN_CASES])
def test_domain_prompt_contains_nondiscrimination_marker(module_path, class_name, call_with_context):
    """Every domain.get_system_prompt() must contain the non-discrimination block."""
    cls = _import_class(module_path, class_name)
    prompt = _get_prompt(cls, call_with_context)

    assert "NÃO DISCRIMINAÇÃO" in prompt or "NAO DISCRIMINACAO" in prompt or "discriminação" in prompt.lower(), (
        f"{class_name}.get_system_prompt() missing non-discrimination block. "
        f"Fix: call super().get_system_prompt(base_prompt=<domain_specific>). "
        f"See compliance_base.py:180."
    )
