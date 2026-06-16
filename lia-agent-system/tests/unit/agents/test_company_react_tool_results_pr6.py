"""PR6 (Task #1006) — Bridge IA→UI sensor.

Garante que `CompanySettingsReActAgent._state_to_output` extrai corretamente
`tool_results = [{tool_name, success, section?, field?}, ...]` de `state["messages"]`,
emparelhando `AIMessage.tool_calls` com `ToolMessage` por `tool_call_id`.

Esse `tool_results` é o que o WS handler (`agent_chat_ws.py:1078`) repassa via
`serialize_message(..., tool_results=...)` para o consumer FE
(`useChatTransport.handleParsedEvent`) disparar `lia:settings-updated` com
`detail.origin == "agent"`.

Fail-loud: sem essas assertivas o bridge IA→UI quebra silenciosamente e os cards
do hub MinhaEmpresa só atualizam após reload.
"""
from __future__ import annotations

import json
import types

import pytest

from lia_agents_core.agent_interface import AgentInput


@pytest.fixture(scope="module")
def agent():
    from app.domains.company_settings.agents.company_react_agent import (
        CompanySettingsReActAgent,
    )
    return CompanySettingsReActAgent.__new__(CompanySettingsReActAgent)


def _ai_msg(tool_calls: list[dict]):
    return types.SimpleNamespace(content="", tool_calls=tool_calls, tool_call_id=None)


def _tool_msg(tool_call_id: str, payload: dict | str):
    content = payload if isinstance(payload, str) else json.dumps(payload)
    return types.SimpleNamespace(content=content, tool_call_id=tool_call_id, tool_calls=[])


def _final_ai(text: str):
    return types.SimpleNamespace(content=text, tool_calls=[], tool_call_id=None)


def _input() -> AgentInput:
    return AgentInput(
        message="ok", company_id="c1", session_id="s1", user_id="u1",
    )


def test_extracts_tool_results_for_save_company_field(agent):
    state = {
        "messages": [
            _ai_msg([{
                "id": "tc-1",
                "name": "save_company_field",
                "args": {"section": "profile", "field": "name", "value": "ACME"},
            }]),
            _tool_msg("tc-1", {"success": True, "data": {"saved": True}}),
            _final_ai("Salvei o nome."),
        ]
    }
    out = agent._state_to_output(state, _input())
    assert out.tool_results, "tool_results MUST be populated for canonical saves"
    assert len(out.tool_results) == 1
    entry = out.tool_results[0]
    assert entry["tool_name"] == "save_company_field"
    assert entry["success"] is True
    assert entry["section"] == "profile"
    assert entry["field"] == "name"


def test_marks_failure_when_tool_returned_success_false(agent):
    state = {
        "messages": [
            _ai_msg([{
                "id": "tc-x",
                "name": "save_company_field",
                "args": {"section": "profile", "field": "name"},
            }]),
            _tool_msg("tc-x", {"success": False, "message": "fairness blocked"}),
            _final_ai("Bloqueado."),
        ]
    }
    out = agent._state_to_output(state, _input())
    assert out.tool_results[0]["success"] is False


def test_handles_multiple_tool_calls(agent):
    state = {
        "messages": [
            _ai_msg([
                {"id": "a", "name": "save_company_field", "args": {"section": "profile", "field": "name"}},
                {"id": "b", "name": "save_hiring_policy", "args": {}},
            ]),
            _tool_msg("a", {"success": True}),
            _tool_msg("b", {"success": True}),
            _final_ai("ok"),
        ]
    }
    out = agent._state_to_output(state, _input())
    names = sorted(r["tool_name"] for r in out.tool_results)
    assert names == ["save_company_field", "save_hiring_policy"]


def test_empty_when_no_tools_called(agent):
    state = {"messages": [_final_ai("Olá!")]}
    out = agent._state_to_output(state, _input())
    assert out.tool_results == []


def test_robust_to_non_json_tool_content(agent):
    """Tool content que não é JSON parseável → assume success=True (tool não falhou)."""
    state = {
        "messages": [
            _ai_msg([{"id": "tc", "name": "save_company_field", "args": {"section": "profile"}}]),
            _tool_msg("tc", "saved profile.name=ACME"),
            _final_ai("ok"),
        ]
    }
    out = agent._state_to_output(state, _input())
    assert out.tool_results[0]["success"] is True
