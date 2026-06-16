"""Contract sensor for the workforce headcount read tool federation (Track B).

Pins that:
  1. the workforce registry exposes get_workforce_plan_summary, and
  2. recruiter_copilot federates it (so the global chat can answer headcount
     questions). get_recruiter_copilot_tools() fails ALTO if the source map is
     misconfigured — this test catches a broken _FEDERATION_SPEC / _source_maps.
"""
from __future__ import annotations


def test_workforce_registry_exposes_summary_tool():
    from app.domains.workforce.agents.workforce_tool_registry import (
        get_workforce_tools,
    )
    names = {t.name for t in get_workforce_tools()}
    assert "get_workforce_plan_summary" in names


def test_copilot_federates_workforce_summary():
    from app.domains.recruiter_assistant.agents.recruiter_copilot_tool_registry import (
        get_recruiter_copilot_tool_names,
    )
    assert "get_workforce_plan_summary" in set(get_recruiter_copilot_tool_names())
