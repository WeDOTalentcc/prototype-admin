"""
Sensor: get_candidate_bigfive tool must exist, be registered, and have multi-tenancy gate.
P2-2 regression prevention.

Data source: lia_opinions.behavioral_analysis.ocean_traits (JSON, 0-1 float per trait).
Written by triagem completion (completion.py bloc 2.4) after WSI triagem.
"""
import pytest


def test_get_candidate_bigfive_tool_exists_in_talent_registry():
    """Tool must be in TOOL_DEFINITIONS (via get_talent_tools) in talent_tool_registry."""
    try:
        from app.domains.recruiter_assistant.agents.talent_tool_registry import get_talent_tools
        tools = get_talent_tools()
        tool_names = [t.name if hasattr(t, "name") else str(t) for t in tools]
        assert "get_candidate_bigfive" in tool_names, (
            "get_candidate_bigfive NOT in talent_tool_registry.get_talent_tools(). "
            "Fix: add get_candidate_bigfive_tool via TOOL_DEFINITIONS.append(...) "
            "in app/domains/recruiter_assistant/agents/talent_tool_registry.py. "
            "BigFive/OCEAN data exists in lia_opinions.behavioral_analysis.ocean_traits "
            "but is inaccessible from chat."
        )
    except ImportError as e:
        pytest.skip(f"Module not importable in test env: {e}")


def test_get_candidate_bigfive_in_federation_spec():
    """Tool must be in _FEDERATION_SPEC for federado recruiter_copilot to dispatch it."""
    try:
        from app.domains.recruiter_assistant.agents.recruiter_copilot_tool_registry import _FEDERATION_SPEC
        spec_tools = [t[1] if isinstance(t, tuple) else str(t) for t in _FEDERATION_SPEC]
        assert "get_candidate_bigfive" in spec_tools, (
            "get_candidate_bigfive NOT in _FEDERATION_SPEC. "
            "Fix: adicionar (talent, get_candidate_bigfive) ao _FEDERATION_SPEC "
            "em app/domains/recruiter_assistant/agents/recruiter_copilot_tool_registry.py"
        )
    except ImportError as e:
        pytest.skip(f"Module not importable in test env: {e}")


def test_bigfive_tool_requires_company_id():
    """Tool must declare requires_company_id=True for multi-tenancy gate."""
    try:
        from app.domains.recruiter_assistant.agents.talent_tool_registry import get_talent_tools
        tools = get_talent_tools()
        bigfive_tool = next(
            (t for t in tools if hasattr(t, "name") and t.name == "get_candidate_bigfive"),
            None,
        )
        if bigfive_tool is None:
            pytest.skip("Tool not yet registered — run test_get_candidate_bigfive_tool_exists first")
        assert getattr(bigfive_tool, "requires_company_id", False), (
            "get_candidate_bigfive must have requires_company_id=True. "
            "Multi-tenancy gate: company_id must come from JWT context, never from LLM payload. "
            "Fix: add requires_company_id=True to the ToolDefinition."
        )
    except ImportError as e:
        pytest.skip(f"Module not importable in test env: {e}")


def test_bigfive_tool_has_function():
    """Tool ToolDefinition must reference the actual handler function."""
    try:
        from app.domains.recruiter_assistant.agents.talent_tool_registry import get_talent_tools
        tools = get_talent_tools()
        bigfive_tool = next(
            (t for t in tools if hasattr(t, "name") and t.name == "get_candidate_bigfive"),
            None,
        )
        if bigfive_tool is None:
            pytest.skip("Tool not yet registered")
        assert callable(getattr(bigfive_tool, "function", None)), (
            "get_candidate_bigfive ToolDefinition.function must be callable. "
            "Check that _wrap_get_candidate_bigfive is assigned."
        )
    except ImportError as e:
        pytest.skip(f"Module not importable in test env: {e}")
