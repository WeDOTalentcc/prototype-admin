"""Sensor integracao (caminho federado): converter tee -> ui_action_sink.

Garante que ao converter uma ui tool via tool_definition_to_langchain_tool
(o que o recruiter_copilot._get_tools faz) e invoca-la, a diretiva ui_action
e teed no sink — de onde o LangGraphReActBase._process_langgraph drena pro
AgentOutput.metadata. Sem LangGraph (testa o elo tee->sink isoladamente).
"""
from __future__ import annotations

import pytest

from lia_agents_core.tool_adapter import tool_definition_to_langchain_tool
from app.shared.ui_action_sink import drain_sink, reset_sink
from app.domains.recruiter_assistant.agents.ui_tool_registry import get_ui_tools


@pytest.fixture(autouse=True)
def _clean():
    reset_sink()
    yield
    reset_sink()


@pytest.fixture
def _tenant():
    from app.middleware.auth_enforcement import _current_company_id
    tok = _current_company_id.set("test-company-uuid")
    yield
    _current_company_id.reset(tok)


def _get_tool(name):
    td = next(t for t in get_ui_tools() if t.name == name)
    return tool_definition_to_langchain_tool(td)


@pytest.mark.asyncio
async def test_apply_table_state_directive_teed_on_convert_and_invoke(_tenant):
    lc_tool = _get_tool("apply_table_state")
    # invoca como o LangGraph faria (coroutine)
    await lc_tool.coroutine(surface="candidates", sort_by="score", sort_order="desc")
    directive = drain_sink()
    assert directive is not None, "diretiva apply_table_state deveria estar no sink"
    assert directive["ui_action"] == "apply_table_state"
    assert directive["ui_action_params"]["surface"] == "candidates"
    assert directive["ui_action_params"]["patch"]["sortBy"] == "score"


@pytest.mark.asyncio
async def test_invalid_vocab_no_directive_teed(_tenant):
    # vocab invalido -> tool retorna success=False sem data.ui_action -> sink vazio
    lc_tool = _get_tool("apply_table_state")
    await lc_tool.coroutine(surface="candidates", sort_by="salario_invalido")
    assert drain_sink() is None
