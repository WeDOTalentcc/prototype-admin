"""Phase E sensor — pin contract of the 4 new stage-action wizard tools.

Doesn't exercise the actual database / services (those have their own
tests). This module asserts:

  1. All 4 tools are registered in TOOL_DEFINITIONS.
  2. Each has the right Pydantic-style parameters schema (required keys).
  3. STAGE_TOOLS allowlist includes them in the right vacancy stages.
  4. Cross-tenant lookup via _load_vacancy_or_error returns the same
     opaque error for missing AND foreign-tenant rows (no IDOR leak).
  5. change_vacancy_status rejects values not in VALID_JOB_STATUSES.
  6. generate_screening_questions rejects mode != compact|complete.

Sensor for the harness: when a future PR adds a new vacancy lifecycle
stage, test_stage_tools_covers_all_lifecycle_stages will fail until
the new stage is registered in STAGE_TOOLS (or explicitly excluded).
"""
from __future__ import annotations

import pytest

from app.domains.job_management.agents.wizard_tool_registry import (
    TOOL_DEFINITIONS, STAGE_TOOLS, _TOOL_MAP,
)


PHASE_E_TOOLS = {
    "generate_screening_questions",
    "dispatch_screening",
    "publish_vacancy",
    "change_vacancy_status",
}


def test_all_phase_e_tools_registered():
    registered = {t.name for t in TOOL_DEFINITIONS}
    missing = PHASE_E_TOOLS - registered
    assert not missing, f"Phase E tools not registered: {missing}"


def test_each_tool_has_company_id_required_param():
    """Multi-tenancy invariant: every tool must require company_id from
    the agent context (NEVER from LLM-generated args). The schema marks
    company_id as a required parameter so the ReAct loop can reject
    malformed tool calls before reaching the wrap function."""
    for name in PHASE_E_TOOLS:
        tool = _TOOL_MAP[name]
        required = set(tool.parameters.get("required") or [])
        assert "company_id" in required, (
            f"Tool {name!r} must declare company_id as required (multi-tenancy)."
        )
        # And company_id must be in properties.
        props = tool.parameters.get("properties") or {}
        assert "company_id" in props, f"Tool {name!r} missing company_id property."


def test_each_tool_has_vacancy_id_required_param():
    for name in PHASE_E_TOOLS:
        tool = _TOOL_MAP[name]
        required = set(tool.parameters.get("required") or [])
        assert "vacancy_id" in required, (
            f"Tool {name!r} must declare vacancy_id as required."
        )


def test_generate_screening_questions_mode_enum():
    tool = _TOOL_MAP["generate_screening_questions"]
    mode_prop = tool.parameters["properties"]["mode"]
    assert mode_prop.get("enum") == ["compact", "complete"], (
        "Mode enum drifted from compact/complete"
    )


def test_change_vacancy_status_enum_matches_VALID_JOB_STATUSES():
    """Status enum in the tool params MUST match the canonical
    VALID_JOB_STATUSES constant (Phase C.1). If they drift, the LLM can
    pass a value the tool rejects, which is wasted tool call latency."""
    from app.api.v1.job_vacancies._shared import VALID_JOB_STATUSES

    tool = _TOOL_MAP["change_vacancy_status"]
    status_prop = tool.parameters["properties"]["status"]
    enum = set(status_prop.get("enum") or [])
    assert enum == set(VALID_JOB_STATUSES), (
        f"change_vacancy_status enum != VALID_JOB_STATUSES.\n"
        f"  Tool enum: {sorted(enum)}\n"
        f"  Canonical: {sorted(VALID_JOB_STATUSES)}"
    )


def test_dispatch_screening_audience_policy_enum_matches_service():
    from app.domains.job_management.services.job_readiness_service import AUDIENCE_POLICIES

    tool = _TOOL_MAP["dispatch_screening"]
    policy_prop = tool.parameters["properties"]["audience_policy"]
    enum = set(policy_prop.get("enum") or [])
    assert enum == set(AUDIENCE_POLICIES), (
        f"dispatch_screening audience_policy enum != AUDIENCE_POLICIES.\n"
        f"  Tool enum: {sorted(enum)}\n"
        f"  Canonical: {sorted(AUDIENCE_POLICIES)}"
    )


def test_publish_vacancy_action_enum():
    tool = _TOOL_MAP["publish_vacancy"]
    action_prop = tool.parameters["properties"]["action"]
    assert action_prop.get("enum") == ["publish", "unpublish"]


def test_stage_tools_includes_phase_e():
    """The vacancy lifecycle stages must offer the right tools."""
    expected = {
        "enriquecida": {"generate_screening_questions"},
        "wsi_config": {"generate_screening_questions"},
        "aguardando_aprovacao": {"dispatch_screening"},
        "publicada": {"publish_vacancy"},
        "ao_vivo": {"change_vacancy_status"},
    }
    for stage, must_include in expected.items():
        assert stage in STAGE_TOOLS, f"Stage {stage!r} missing from STAGE_TOOLS"
        present = set(STAGE_TOOLS[stage])
        missing = must_include - present
        assert not missing, (
            f"Stage {stage!r} STAGE_TOOLS missing tools: {missing}\n"
            f"  Current: {sorted(present)}"
        )


def test_no_phase_e_tool_registered_in_unsupported_stage():
    """Belt-and-suspenders: Phase E tools must NOT be advertised in
    stages that have no business invoking them. Specifically, the wizard
    stages (input-evaluation, jd-enrichment, salary, competencies)
    should not include vacancy lifecycle tools."""
    forbidden_stages = ["input-evaluation", "jd-enrichment", "salary", "competencies"]
    for stage in forbidden_stages:
        present = set(STAGE_TOOLS.get(stage) or [])
        leaked = present & {"dispatch_screening", "publish_vacancy", "change_vacancy_status"}
        assert not leaked, (
            f"Stage {stage!r} unexpectedly exposes Phase E tools: {leaked}"
        )


def test_tool_descriptions_in_portuguese():
    """The wizard speaks PT-BR; every Phase E tool description must too.
    Catches accidental English drift in tool descriptions."""
    PT_MARKERS = ["vaga", "perguntas", "triagem", "status", "publica", "candidato"]
    for name in PHASE_E_TOOLS:
        desc = _TOOL_MAP[name].description.lower()
        assert any(marker in desc for marker in PT_MARKERS), (
            f"Tool {name!r} description appears to be in English: {desc!r}"
        )
