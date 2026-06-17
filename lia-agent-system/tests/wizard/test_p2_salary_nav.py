"""TDD — set_salary, navigate_to_jobs, stage handoff (Paulo round 2)."""
from __future__ import annotations
import pytest
from app.domains.job_creation.orchestrator.wizard_tools import (
    ToolContext, _handle_set_salary, _handle_navigate_to_jobs, build_tool_registry,
)
from app.domains.job_creation.services.wizard_session_service import _derive_wizard_stage

CTX = ToolContext(company_id="c1")


@pytest.mark.easy
def test_set_salary_range():
    r = _handle_set_salary({}, {"salary_min": 12000, "salary_max": 18000}, CTX)
    assert not r.error
    assert r.state_updates["salary_min"] == 12000
    assert r.state_updates["salary_max"] == 18000
    assert r.state_updates["salary_range"] == {"min": 12000, "max": 18000, "currency": "BRL"}
    assert r.state_updates["salary_confirmed"] is True


@pytest.mark.easy
def test_set_salary_min_gt_max_rejected():
    r = _handle_set_salary({}, {"salary_min": 20000, "salary_max": 10000}, CTX)
    assert r.error


@pytest.mark.easy
def test_set_salary_non_numeric_rejected():
    r = _handle_set_salary({}, {"salary_min": "doze mil"}, CTX)
    assert r.error


@pytest.mark.easy
def test_set_salary_rejects_tenant_keys():
    r = _handle_set_salary({}, {"salary_min": 12000, "company_id": "x"}, CTX)
    assert r.error and "tenant" in r.llm_message.lower()


@pytest.mark.easy
def test_navigate_sets_flag():
    r = _handle_navigate_to_jobs({}, {}, CTX)
    assert not r.error
    assert r.state_updates["_navigate_to_jobs"] is True


@pytest.mark.easy
def test_derive_stage_handoff_on_navigate():
    assert _derive_wizard_stage({"_navigate_to_jobs": True}) == "handoff"


@pytest.mark.easy
def test_derive_stage_handoff_on_publish():
    assert _derive_wizard_stage({"job_id": 42}) == "handoff"


@pytest.mark.easy
def test_derive_stage_intake_default():
    assert _derive_wizard_stage({}) == "intake"


@pytest.mark.easy
def test_registry_has_new_tools():
    reg = build_tool_registry()
    assert "set_salary" in reg and "navigate_to_jobs" in reg


@pytest.mark.medium
def test_set_salary_decline_to_disclose_sets_skip_flag():
    """Recrutador opta por seguir sem divulgar → registra salary_skipped, sem min/max."""
    r = _handle_set_salary({}, {"decline_to_disclose": True}, CTX)
    assert not r.error
    assert r.state_updates.get("salary_skipped") is True
    assert "salary_min" not in r.state_updates


@pytest.mark.medium
def test_set_salary_decline_bypasses_min_max_requirement():
    """decline_to_disclose dispensa min/max (não exige a faixa)."""
    r = _handle_set_salary({}, {"decline_to_disclose": True}, CTX)
    assert not r.error  # sem 'Forneça ao menos salary_min ou salary_max'
