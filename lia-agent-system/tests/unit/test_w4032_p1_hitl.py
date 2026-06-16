"""W4-032 P1 · TDD tests · HITL gate em jobs_mgmt + pipeline + automation."""
from __future__ import annotations

from pathlib import Path

import pytest


def test_jobs_mgmt_hitl_action_types():
    """W4-032 P1 · jobs_management declara _HITL_ACTION_TYPES canonical."""
    from app.domains.recruiter_assistant.agents.jobs_mgmt_react_agent import (
        JobsManagementReActAgent,
    )
    expected = {
        "publish_vacancy", "unpublish_vacancy", "duplicate_vacancy",
        "bulk_vacancy_status_change", "delete_vacancy",
    }
    assert expected.issubset(set(JobsManagementReActAgent._HITL_ACTION_TYPES))


def test_pipeline_hitl_action_types():
    """W4-032 P1 · pipeline declara _HITL_ACTION_TYPES canonical."""
    from app.domains.cv_screening.agents.pipeline_react_agent import (
        PipelineReActAgent,
    )
    expected = {
        "bulk_move_candidates", "bulk_reject_candidates",
        "auto_advance_stage", "auto_reject_low_score", "pipeline_transition",
    }
    assert expected.issubset(set(PipelineReActAgent._HITL_ACTION_TYPES))


def test_automation_hitl_action_types():
    """W4-032 P1 · automation declara _HITL_ACTION_TYPES canonical."""
    from app.domains.automation.agents.automation_react_agent import (
        AutomationReActAgent,
    )
    expected = {
        "activate_automation", "deactivate_automation", "delete_automation",
        "bulk_trigger_automation", "schedule_recurring_task",
    }
    assert expected.issubset(set(AutomationReActAgent._HITL_ACTION_TYPES))


def test_p1_agents_import_helper():
    """W4-032 P1 · cada agent file importa o helper."""
    files = [
        "app/domains/recruiter_assistant/agents/jobs_mgmt_react_agent.py",
        "app/domains/cv_screening/agents/pipeline_react_agent.py",
        "app/domains/automation/agents/automation_react_agent.py",
    ]
    repo_root = Path(__file__).resolve().parents[2]
    for f in files:
        src = (repo_root / f).read_text()
        assert "from app.shared.hitl.agent_gate import maybe_request_hitl_approval" in src, (
            f"{f} NÃO importa maybe_request_hitl_approval"
        )
        assert "if _hitl_response is not None:" in src or "if hitl_response is not None:" in src, (
            f"{f} NÃO tem early return pattern do gate"
        )


def test_jobs_mgmt_fairness_check_preserved():
    """W4-032 P1 · jobs_mgmt mantém fairness check ANTES do HITL gate."""
    repo_root = Path(__file__).resolve().parents[2]
    src = (
        repo_root
        / "app/domains/recruiter_assistant/agents/jobs_mgmt_react_agent.py"
    ).read_text()
    # Fairness check + HITL gate ambos presentes
    assert "_fairness_pre_check" in src
    assert "maybe_request_hitl_approval" in src
    # Fairness vem ANTES do HITL (ordering canonical: fairness > hitl > tool)
    fairness_pos = src.find("_fairness_pre_check(input.message")
    hitl_pos = src.find("maybe_request_hitl_approval")
    assert fairness_pos < hitl_pos, (
        "fairness check deve preceder HITL gate (REGRA 3 + W4-032 ordering)"
    )
