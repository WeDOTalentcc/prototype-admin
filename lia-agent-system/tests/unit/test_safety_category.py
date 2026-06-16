"""Tests for UC-P2-09: SafetyCategory enum replaces GUARDRAIL_TOOLS list[str]."""
import pytest


def test_guardrail_tools_are_dict_pipeline_action():
    from app.domains.pipeline.agents.pipeline_action_tool_registry import GUARDRAIL_TOOLS
    from app.shared.compliance.safety_category import SafetyCategory
    assert isinstance(GUARDRAIL_TOOLS, dict)
    for k, v in GUARDRAIL_TOOLS.items():
        assert isinstance(k, str)
        assert isinstance(v, SafetyCategory)


def test_guardrail_tools_are_dict_pipeline():
    from app.domains.pipeline.agents.pipeline_tool_registry import GUARDRAIL_TOOLS
    from app.shared.compliance.safety_category import SafetyCategory
    assert isinstance(GUARDRAIL_TOOLS, dict)
    for k, v in GUARDRAIL_TOOLS.items():
        assert isinstance(k, str)
        assert isinstance(v, SafetyCategory)


def test_guardrail_tools_are_dict_kanban_action():
    from app.domains.recruiter_assistant.agents.kanban_action_tool_registry import GUARDRAIL_TOOLS
    from app.shared.compliance.safety_category import SafetyCategory
    assert isinstance(GUARDRAIL_TOOLS, dict)
    for k, v in GUARDRAIL_TOOLS.items():
        assert isinstance(k, str)
        assert isinstance(v, SafetyCategory)


def test_guardrail_tools_are_dict_kanban():
    from app.domains.recruiter_assistant.agents.kanban_tool_registry import GUARDRAIL_TOOLS
    from app.shared.compliance.safety_category import SafetyCategory
    assert isinstance(GUARDRAIL_TOOLS, dict)
    for k, v in GUARDRAIL_TOOLS.items():
        assert isinstance(k, str)
        assert isinstance(v, SafetyCategory)


def test_guardrail_tools_are_dict_talent():
    from app.domains.recruiter_assistant.agents.talent_tool_registry import GUARDRAIL_TOOLS
    from app.shared.compliance.safety_category import SafetyCategory
    assert isinstance(GUARDRAIL_TOOLS, dict)
    for k, v in GUARDRAIL_TOOLS.items():
        assert isinstance(k, str)
        assert isinstance(v, SafetyCategory)


def test_guardrail_tools_are_dict_sourcing_engagement():
    from app.domains.sourcing.agents.sourcing_engagement_tool_registry import GUARDRAIL_TOOLS
    from app.shared.compliance.safety_category import SafetyCategory
    assert isinstance(GUARDRAIL_TOOLS, dict)
    for k, v in GUARDRAIL_TOOLS.items():
        assert isinstance(k, str)
        assert isinstance(v, SafetyCategory)


def test_invalid_tool_not_in_guardrails():
    from app.domains.pipeline.agents.pipeline_action_tool_registry import GUARDRAIL_TOOLS
    assert "not_a_real_tool_xyz" not in GUARDRAIL_TOOLS


def test_in_operator_backward_compatible():
    """dict 'in' operator checks keys — backward compatible with list usage."""
    from app.domains.pipeline.agents.pipeline_action_tool_registry import GUARDRAIL_TOOLS
    assert "update_candidate_field" in GUARDRAIL_TOOLS
    assert "cancel_interview" in GUARDRAIL_TOOLS
    assert "reschedule_interview" in GUARDRAIL_TOOLS


def test_safety_category_values():
    from app.shared.compliance.safety_category import SafetyCategory
    assert SafetyCategory.OUTREACH == "outreach"
    assert SafetyCategory.PIPELINE_MOVE == "pipeline_move"
    assert SafetyCategory.BULK_ACTION == "bulk_action"
    assert SafetyCategory.PII_EXPORT == "pii_export"
    assert SafetyCategory.DESTRUCTIVE_WRITE == "destructive_write"
    assert SafetyCategory.OFFER == "offer"


def test_send_outreach_is_outreach_category():
    from app.domains.sourcing.agents.sourcing_engagement_tool_registry import GUARDRAIL_TOOLS
    from app.shared.compliance.safety_category import SafetyCategory
    assert GUARDRAIL_TOOLS["send_outreach"] == SafetyCategory.OUTREACH
