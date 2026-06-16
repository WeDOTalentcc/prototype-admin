"""Sensor — RRP blocks survive the LIVE domain-agent path (não só o federado).

Causa raiz (auditoria 2026-06-06): response_blocks só eram drenados pro
output.metadata no agente federado recruiter_copilot, que o CascadedRouter
nunca seleciona. Os domain agents (talent/jobs/kanban) rodavam sem tee nem
drain → response_blocks=null → FE sem cards/tabelas RRP.

Fix no produtor (1 lugar cada):
  - tee:   tool_definition_to_langchain_tool (converter único de TODOS os agentes)
  - drain: LangGraphReActBase._process_langgraph (método único que TODOS chamam)

Estes testes pinam o caminho ao vivo — substituem o false-green de
test_rrp_compare_candidates_wire (que injetava blocks à mão no frame).
"""
from __future__ import annotations

import asyncio

import pytest

from app.shared.rrp_block_sink import drain_sink, reset_sink
from lia_agents_core.tool_adapter import ToolDefinition, tool_definition_to_langchain_tool


# ── Fix 2a: o converter único tee response_blocks pro sink ──────────────────

def test_converter_tees_async_tool_into_sink() -> None:
    reset_sink()

    async def _rank(query: str) -> dict:
        return {"success": True, "data": {"response_blocks": [{"kind": "ranking_table"}]}}

    lc = tool_definition_to_langchain_tool(
        ToolDefinition(name="rank", description="rank candidates", function=_rank)
    )
    res = asyncio.run(lc.coroutine(query="diretor juridico"))
    # passthrough intacto (a tool segue retornando o dict pro ToolMessage)
    assert res["data"]["response_blocks"][0]["kind"] == "ranking_table"
    # teed: o bloco foi capturado ANTES da stringificação do StructuredTool
    drained = drain_sink()
    assert len(drained) == 1 and drained[0]["kind"] == "ranking_table"


def test_converter_tees_sync_tool_into_sink() -> None:
    reset_sink()

    def _view(candidate_id: str) -> dict:
        return {"data": {"response_blocks": [{"kind": "candidate_card"}]}}

    lc = tool_definition_to_langchain_tool(
        ToolDefinition(name="view", description="view profile", function=_view)
    )
    out = lc.func(candidate_id="abc")
    assert out["data"]["response_blocks"][0]["kind"] == "candidate_card"
    assert drain_sink()[0]["kind"] == "candidate_card"


def test_converter_no_blocks_does_not_pollute() -> None:
    reset_sink()

    async def _plain(x: str) -> dict:
        return {"success": True, "data": {"value": 42}}

    lc = tool_definition_to_langchain_tool(
        ToolDefinition(name="plain", description="no blocks", function=_plain)
    )
    asyncio.run(lc.coroutine(x="y"))
    assert drain_sink() == []


# ── Fix 2b: o método base único drena o sink pro output.metadata ────────────

@pytest.mark.asyncio
async def test_base_process_langgraph_drains_sink_into_metadata(monkeypatch) -> None:
    from unittest.mock import patch

    from lia_agents_core.agent_interface import AgentInput, AgentOutput
    from lia_agents_core.langgraph_react_base import LangGraphReActBase
    from app.shared.rrp_block_sink import append_from_result

    class _Stub(LangGraphReActBase):
        @property
        def domain_name(self) -> str:
            return "test_rrp_drain"

        @property
        def available_tools(self) -> list:
            return []

        def _get_tools(self) -> list:
            return []

        async def process(self, input) -> AgentOutput:
            return await self._process_langgraph(input)

        def _get_system_prompt(self, input) -> str:
            return "system"

        def _state_to_output(self, state, input) -> AgentOutput:
            return AgentOutput(message="ok", metadata={"source": "test"})

    with patch("lia_agents_core.langgraph_base.get_checkpointer", return_value=None):
        stub = _Stub()

    async def _fake_run_graph(**kwargs):
        # simula um tool tee'd no sink durante a execução do grafo
        append_from_result({"data": {"response_blocks": [{"kind": "funnel"}]}})
        return {"messages": []}

    monkeypatch.setattr(stub, "_run_graph", _fake_run_graph)

    out = await stub._process_langgraph(
        AgentInput(message="oi", session_id="s1", company_id="c1", user_id="u1")
    )
    assert out.metadata.get("response_blocks"), "base deve drenar o sink pro metadata"
    assert out.metadata["response_blocks"][0]["kind"] == "funnel"
