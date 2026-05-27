"""Contract test: CustomAgentRuntime._state_to_output popula reasoning_trace.

Onda 1 B2 — sensor + test em camadas:
- sensor (B5.1) garante AST shape (recidiva proibida)
- este teste garante runtime behavior (output.reasoning_trace populated)
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


class _FakeAIMessage:
    def __init__(self, content="", tool_calls=None):
        self.content = content
        self.tool_calls = tool_calls or []


def _make_runtime():
    """Helper: monta CustomAgentRuntime mockando boot pesado de enhanced mixin."""
    from app.domains.agent_studio.custom_agent_runtime import CustomAgentRuntime

    with patch.object(CustomAgentRuntime, "_setup_enhanced", return_value=None):
        rt = CustomAgentRuntime(
            agent_id="agent-1",
            agent_name="TestAgent",
            system_prompt="você é teste",
            allowed_tools=["search_candidates"],
            company_id="comp-1",
        )
    return rt


def _make_input():
    from lia_agents_core.agent_interface import AgentInput

    return AgentInput(
        message="Olá",
        session_id="s1",
        company_id="comp-1",
        user_id="u-1",
    )


def test_state_to_output_populates_reasoning_trace_with_thought():
    """AIMessage só com content → step thought populated."""
    rt = _make_runtime()
    state = {"messages": [_FakeAIMessage(content="Vou processar")]}
    out = rt._state_to_output(state, _make_input())
    assert out.reasoning_trace is not None
    assert len(out.reasoning_trace) >= 1
    assert any(s.step_type == "thought" for s in out.reasoning_trace)


def test_state_to_output_with_tool_call_emits_action():
    """AIMessage com tool_calls → step action + data_fields_accessed."""
    rt = _make_runtime()
    msg = _FakeAIMessage(
        content="",
        tool_calls=[{"name": "search_candidates", "args": {"candidate_id": "c1"}}],
    )
    out = rt._state_to_output({"messages": [msg]}, _make_input())
    assert out.reasoning_trace is not None
    actions = [s for s in out.reasoning_trace if s.step_type == "action"]
    assert len(actions) == 1
    assert "email" in actions[0].data_fields_accessed
    assert "nome" in actions[0].data_fields_accessed


def test_state_to_output_empty_messages_returns_empty_trace():
    """Empty messages → trace=[] (não None)."""
    rt = _make_runtime()
    out = rt._state_to_output({"messages": []}, _make_input())
    assert out.reasoning_trace == []


def test_state_to_output_lgpd_invariant_in_action_step():
    """Mesmo com tool_input contendo 'cpf', data_fields_accessed strip."""
    rt = _make_runtime()
    msg = _FakeAIMessage(
        content="",
        tool_calls=[{"name": "any_tool", "args": {"cpf": "12345678901"}}],
    )
    out = rt._state_to_output({"messages": [msg]}, _make_input())
    for step in out.reasoning_trace or []:
        assert "cpf" not in step.data_fields_accessed
        assert "raca" not in step.data_fields_accessed
