"""Onda 5.3.a — Tool scoping via intent heuristic.

Producer-side canonical-fix. Tests cover:
  1. intent_heuristic.classify_intent signal fusion (context_page + regex)
  2. registry.get_tools_for_agents union logic
  3. agentic_loop.get_tool_schemas scoping + fallback
  4. main_orchestrator wiring (structural)
"""
from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import MagicMock

import pytest


# ---------------------------------------------------------------------------
# 1. intent_heuristic
# ---------------------------------------------------------------------------

def test_classify_intent_context_page_signal() -> None:
    from app.tools.intent_heuristic import classify_intent

    hints = classify_intent(None, "Candidatos")
    assert hints, "Candidatos page should produce hints"
    assert "sourcing" in hints
    # recruiter_assistant must NOT be in hints (by design — too broad)
    assert "recruiter_assistant" not in hints
    assert "orchestrator" not in hints


def test_classify_intent_regex_signal() -> None:
    from app.tools.intent_heuristic import classify_intent

    hints = classify_intent("criar vaga de desenvolvedor", None)
    assert "job_planner" in hints


def test_classify_intent_empty_returns_empty() -> None:
    from app.tools.intent_heuristic import classify_intent

    assert classify_intent(None, None) == []
    assert classify_intent("", "") == []
    assert classify_intent("oi", "general") == []


def test_classify_intent_no_broad_agents() -> None:
    """Regression: recruiter_assistant and orchestrator must never be in hints."""
    from app.tools.intent_heuristic import classify_intent

    queries = [
        ("quantas vagas", "Vagas"),
        ("candidatos parados", "Candidatos"),
        ("relatório do pipeline", "pipeline"),
        ("sourcing linkedin", "Sourcing"),
    ]
    for msg, page in queries:
        hints = classify_intent(msg, page)
        assert "recruiter_assistant" not in hints, (
            f"recruiter_assistant leaked into hints for {msg!r}"
        )
        assert "orchestrator" not in hints


# ---------------------------------------------------------------------------
# 2. registry.get_tools_for_agents (union)
# ---------------------------------------------------------------------------

def test_registry_get_tools_for_agents_empty_returns_empty() -> None:
    from app.tools.registry import ToolRegistry
    reg = ToolRegistry()
    assert reg.get_tools_for_agents([]) == []


def test_registry_union_deduplicates() -> None:
    from app.tools.registry import ToolDefinition, ToolRegistry

    reg = ToolRegistry()
    # Tool allowed for both agents — should appear once
    reg._tools["shared"] = ToolDefinition(
        name="shared",
        description="x",
        parameters_schema={},
        handler=lambda **kw: {},
        allowed_agents=["a", "b"],
    )
    reg._tools["only_a"] = ToolDefinition(
        name="only_a",
        description="x",
        parameters_schema={},
        handler=lambda **kw: {},
        allowed_agents=["a"],
    )
    result = reg.get_tools_for_agents(["a", "b"])
    names = {t.name for t in result}
    assert names == {"shared", "only_a"}


def test_registry_universal_tools_always_included() -> None:
    """Tools with no allowed_agents (universal) are included for any hint."""
    from app.tools.registry import ToolDefinition, ToolRegistry

    reg = ToolRegistry()
    reg._tools["universal"] = ToolDefinition(
        name="universal",
        description="x",
        parameters_schema={},
        handler=lambda **kw: {},
        allowed_agents=[],
    )
    result = reg.get_tools_for_agents(["sourcing"])
    assert any(t.name == "universal" for t in result)


# ---------------------------------------------------------------------------
# 3. agentic_loop.get_tool_schemas scoping + fallback
# ---------------------------------------------------------------------------

def test_agentic_loop_scoping_signature() -> None:
    """Structural: get_tool_schemas must accept agent_hints kwarg."""
    from app.orchestrator.agentic_loop import AgenticLoop
    import inspect

    sig = inspect.signature(AgenticLoop.get_tool_schemas)
    assert "agent_hints" in sig.parameters


def test_agentic_loop_run_signature_threads_hints() -> None:
    """Structural: run() must accept + thread agent_hints."""
    from app.orchestrator.agentic_loop import AgenticLoop
    import inspect

    sig = inspect.signature(AgenticLoop.run)
    assert "agent_hints" in sig.parameters


def test_agentic_loop_feature_flag_disables_scoping(monkeypatch) -> None:
    """When LIA_TOOL_SCOPING_ENABLED=false, scoping is bypassed."""
    from app.orchestrator.agentic_loop import AgenticLoop

    monkeypatch.setenv("LIA_TOOL_SCOPING_ENABLED", "false")
    loop = AgenticLoop()
    # Mock registry with 5 tools
    loop._tool_registry = MagicMock()
    loop._tool_registry.list_tools.return_value = ["t1", "t2", "t3", "t4", "t5"]
    loop._tool_registry.get_all_schemas.return_value = [{"n": "t" + str(i)} for i in range(5)]
    loop._tool_executor = MagicMock()
    loop._llm_service = MagicMock()
    loop._ToolExecutionContext = MagicMock()

    schemas = loop.get_tool_schemas("claude", agent_hints=["sourcing"])
    assert len(schemas) == 5  # full catalog despite hints
    loop._tool_registry.get_all_schemas.assert_called()


def test_agentic_loop_fallback_low_count(monkeypatch) -> None:
    """If scoped result < LIA_MIN_SCOPED_TOOLS, fall back to full."""
    from app.orchestrator.agentic_loop import AgenticLoop

    monkeypatch.setenv("LIA_TOOL_SCOPING_ENABLED", "true")
    monkeypatch.setenv("LIA_MIN_SCOPED_TOOLS", "5")
    loop = AgenticLoop()
    loop._tool_registry = MagicMock()
    loop._tool_registry.list_tools.return_value = ["t"] * 10
    loop._tool_registry.get_schemas_for_agents.return_value = [{"n": "only1"}, {"n": "only2"}]  # 2 < 5
    loop._tool_registry.get_all_schemas.return_value = [{"n": "full"}] * 10
    loop._tool_executor = MagicMock()
    loop._llm_service = MagicMock()
    loop._ToolExecutionContext = MagicMock()

    schemas = loop.get_tool_schemas("claude", agent_hints=["very_narrow_agent"])
    assert len(schemas) == 10  # fallback to full


def test_agentic_loop_scoping_active(monkeypatch) -> None:
    """With hints, scoping returns fewer tools."""
    from app.orchestrator.agentic_loop import AgenticLoop

    monkeypatch.setenv("LIA_TOOL_SCOPING_ENABLED", "true")
    monkeypatch.setenv("LIA_MIN_SCOPED_TOOLS", "3")
    loop = AgenticLoop()
    loop._tool_registry = MagicMock()
    loop._tool_registry.list_tools.return_value = ["t"] * 100
    loop._tool_registry.get_schemas_for_agents.return_value = [{"n": i} for i in range(20)]
    loop._tool_executor = MagicMock()
    loop._llm_service = MagicMock()
    loop._ToolExecutionContext = MagicMock()

    schemas = loop.get_tool_schemas("claude", agent_hints=["sourcing"])
    assert len(schemas) == 20
    loop._tool_registry.get_schemas_for_agents.assert_called_once()


# ---------------------------------------------------------------------------
# 4. main_orchestrator wiring (structural source check)
# ---------------------------------------------------------------------------

def _orchestrator_source() -> str:
    p = Path(__file__).resolve()
    for parent in p.parents:
        cand = parent / "app/orchestrator/main_orchestrator.py"
        if cand.exists():
            return cand.read_text(encoding="utf-8")
    raise RuntimeError("main_orchestrator.py not found")


def test_main_orchestrator_imports_classify_intent() -> None:
    src = _orchestrator_source()
    assert "classify_intent" in src, "main_orchestrator must invoke classify_intent"


def test_main_orchestrator_passes_agent_hints() -> None:
    src = _orchestrator_source()
    assert "agent_hints=_agent_hints" in src or "agent_hints=" in src, (
        "main_orchestrator must pass agent_hints to agentic_loop.run"
    )


def test_onda5_3a_marker_present() -> None:
    src = _orchestrator_source()
    assert "Onda 5.3.a" in src
