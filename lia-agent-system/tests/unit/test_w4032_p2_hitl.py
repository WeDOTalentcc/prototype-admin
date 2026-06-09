"""W4-032 P2 + Sensor · TDD tests · HITL gate em talent + analytics + company.

Cobre os 3 últimos agents da matrix W4-032 + sensor canonical.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_talent_funnel_hitl_action_types():
    """W4-032 P2 · talent_funnel declara _HITL_ACTION_TYPES canonical."""
    from app.domains.recruiter_assistant.agents.talent_funnel_react_agent import (
        TalentFunnelReActAgent,
    )
    expected = {
        "bulk_shortlist", "bulk_sourcing_outreach",
        "import_external_candidates", "talent_pool_assignment",
        "auto_reject_funnel",
    }
    assert expected.issubset(set(TalentFunnelReActAgent._HITL_ACTION_TYPES))


def test_analytics_hitl_action_types():
    """W4-032 P2 · analytics declara _HITL_ACTION_TYPES canonical."""
    from app.domains.analytics.agents.analytics_react_agent import (
        AnalyticsReActAgent,
    )
    expected = {
        "export_report", "share_dashboard", "send_report_email",
        "export_candidates_csv", "schedule_recurring_export",
    }
    assert expected.issubset(set(AnalyticsReActAgent._HITL_ACTION_TYPES))


def test_company_settings_hitl_action_types():
    """W4-032 P2 · company_settings declara _HITL_ACTION_TYPES canonical."""
    from app.domains.company_settings.agents.company_react_agent import (
        CompanySettingsReActAgent,
    )
    expected = {
        "update_company_policy", "toggle_lia_field",
        "update_culture_profile", "update_hiring_policy",
        "delete_company_data",
    }
    assert expected.issubset(set(CompanySettingsReActAgent._HITL_ACTION_TYPES))


def test_p2_agents_import_helper():
    """W4-032 P2 · cada agent file importa o helper."""
    files = [
        "app/domains/recruiter_assistant/agents/talent_funnel_react_agent.py",
        "app/domains/analytics/agents/analytics_react_agent.py",
        "app/domains/company_settings/agents/company_react_agent.py",
    ]
    for f in files:
        src = (REPO_ROOT / f).read_text()
        assert "from app.shared.hitl.agent_gate import maybe_request_hitl_approval" in src, (
            f"{f} NÃO importa maybe_request_hitl_approval"
        )
        assert "if _hitl_response is not None:" in src, (
            f"{f} NÃO tem early return pattern do gate"
        )


def test_canonical_sensor_passes_blocking():
    """W4-032 · sensor canonical passa em modo --blocking (9/9 wired)."""
    sensor = REPO_ROOT / "scripts" / "check_agent_hitl_gates.py"
    result = subprocess.run(
        [sys.executable, str(sensor), "--blocking"],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )
    assert result.returncode == 0, (
        f"Sensor blocking failed: stdout={result.stdout}\nstderr={result.stderr}"
    )
    assert "8/8 W4-032 agents wired (100%)" in result.stdout


def test_helper_module_canonical_export():
    """W4-032 · helper exports canonical."""
    from app.shared.hitl.agent_gate import maybe_request_hitl_approval
    import inspect
    sig = inspect.signature(maybe_request_hitl_approval)
    params = set(sig.parameters.keys())
    required = {"agent_input", "domain", "action_types", "agent_name"}
    assert required.issubset(params), f"Missing params: {required - params}"


def test_all_9_agents_have_unique_action_sets():
    """W4-032 · cada agent tem actions distintas (smell check: no copy-paste)."""
    from app.domains.ats_integration.agents.ats_integration_react_agent import ATSIntegrationReActAgent
    from app.domains.recruiter_assistant.agents.kanban_react_agent import KanbanReActAgent
    from app.domains.recruiter_assistant.agents.jobs_mgmt_react_agent import JobsManagementReActAgent
    from app.domains.cv_screening.agents.pipeline_react_agent import PipelineReActAgent
    from app.domains.automation.agents.automation_react_agent import AutomationReActAgent
    from app.domains.recruiter_assistant.agents.talent_funnel_react_agent import TalentFunnelReActAgent
    from app.domains.analytics.agents.analytics_react_agent import AnalyticsReActAgent
    from app.domains.company_settings.agents.company_react_agent import CompanySettingsReActAgent

    agents = {
        "ats_integration": ATSIntegrationReActAgent,
        "kanban": KanbanReActAgent,
        "jobs_mgmt": JobsManagementReActAgent,
        "pipeline": PipelineReActAgent,
        "automation": AutomationReActAgent,
        "talent_funnel": TalentFunnelReActAgent,
        "analytics": AnalyticsReActAgent,
        "company_settings": CompanySettingsReActAgent,
    }

    # Each agent has at least 4 action_types
    for name, cls in agents.items():
        actions = set(cls._HITL_ACTION_TYPES)
        assert len(actions) >= 4, f"{name}: only {len(actions)} actions (min 4 expected)"

    # No 2 agents have identical action sets (smell check)
    seen: dict[frozenset, str] = {}
    for name, cls in agents.items():
        key = frozenset(cls._HITL_ACTION_TYPES)
        if key in seen:
            raise AssertionError(
                f"{name} has IDENTICAL _HITL_ACTION_TYPES to {seen[key]} — "
                "smell check: copy-paste?"
            )
        seen[key] = name
