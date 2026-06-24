"""Sensor: _process_langgraph emite reasoning_step understanding/composing.

Garante que TODOS os domain agents (recruiter_copilot, talent, kanban, etc.)
alimentam o multistep timeline ao inves de cair no fallback estatico Pensando.

Fase 2 (2026-06-13): composing usa emit_reasoning_step_async (await direto)
para garantir que o frame chega na sse_queue ANTES do _done — sem essa garantia
o frame seria perdido e a timeline mostraria apenas understanding.
"""
import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class FakeStreamingCb:
    """Minimal mock que captura emit_reasoning_step e emit_reasoning_step_async."""
    def __init__(self):
        self.steps = []
        self.async_steps = []

    def emit_reasoning_step(self, label, detail=""):
        self.steps.append(label)

    async def emit_reasoning_step_async(self, label, detail=""):
        self.async_steps.append(label)
        self.steps.append(label)  # também registra em steps pra retrocompat


@pytest.fixture
def fake_cb():
    return FakeStreamingCb()


def _make_agent():
    from lia_agents_core.langgraph_react_base import LangGraphReActBase

    class TestAgent(LangGraphReActBase):
        domain_name = "test"
        available_tools = []

        def _get_tools(self):
            return []

        async def process(self, inp):
            return await self._process_langgraph(inp)

    agent = TestAgent.__new__(TestAgent)
    agent.domain_name = "test"
    agent.available_tools = []
    return agent


def _make_input():
    from lia_agents_core.agent_interface import AgentInput
    return AgentInput(
        message="oi",
        session_id="s1",
        company_id="c1",
        user_id="u1",
    )


def _mock_context(agent, fake_cb):
    """Context managers comuns pra todos os testes."""
    return [
        patch.object(agent, "_run_graph",
                     side_effect=AsyncMock(return_value={
                         "messages": [MagicMock(content="ok", type="ai", tool_calls=None)]
                     })),
        patch.object(agent, "_get_system_prompt", return_value="sys"),
        patch.object(agent, "_sanitize_messages_pii",
                     new_callable=lambda: AsyncMock(side_effect=lambda m: m)),
        patch("lia_agents_core.streaming_callback.StreamingCallback", return_value=fake_cb),
    ]


@pytest.mark.asyncio
async def test_understanding_emitted_before_graph(fake_cb):
    """understanding deve ser emitido ANTES de _run_graph ser chamado."""
    agent = _make_agent()
    call_order = []

    async def mock_run_graph(**kwargs):
        call_order.append(("run_graph", list(fake_cb.steps)))
        return {"messages": [MagicMock(content="ok", type="ai", tool_calls=None)]}

    with patch.object(agent, "_run_graph", side_effect=mock_run_graph), \
         patch.object(agent, "_get_system_prompt", return_value="sys"), \
         patch.object(agent, "_sanitize_messages_pii",
                      new_callable=lambda: AsyncMock(side_effect=lambda m: m)), \
         patch("lia_agents_core.streaming_callback.StreamingCallback", return_value=fake_cb):
        try:
            await agent._process_langgraph(_make_input())
        except Exception:
            pass

    assert len(call_order) > 0, "_run_graph nunca foi chamado"
    steps_before_graph = call_order[0][1]
    assert "understanding" in steps_before_graph, (
        f"understanding deve ser emitido ANTES de _run_graph. "
        f"Steps no momento da chamada: {steps_before_graph}"
    )


@pytest.mark.asyncio
async def test_composing_uses_async_path(fake_cb):
    """composing DEVE usar emit_reasoning_step_async (await direto, não create_task).

    Isso garante que o frame chega na sse_queue ANTES do _done, evitando
    que a timeline mostre blank e perca o passo composing.
    """
    agent = _make_agent()

    with patch.object(agent, "_run_graph",
                      side_effect=AsyncMock(return_value={
                          "messages": [MagicMock(content="ok", type="ai", tool_calls=None)]
                      })), \
         patch.object(agent, "_get_system_prompt", return_value="sys"), \
         patch.object(agent, "_sanitize_messages_pii",
                      new_callable=lambda: AsyncMock(side_effect=lambda m: m)), \
         patch("lia_agents_core.streaming_callback.StreamingCallback", return_value=fake_cb):
        try:
            await agent._process_langgraph(_make_input())
        except Exception:
            pass

    assert "composing" in fake_cb.async_steps, (
        f"composing DEVE usar emit_reasoning_step_async (await direto). "
        f"async_steps: {fake_cb.async_steps}. "
        f"Se composing aparece só em steps mas não em async_steps, "
        f"o create_task race condition ainda existe."
    )


@pytest.mark.asyncio
async def test_composing_emitted_after_graph(fake_cb):
    """composing deve ser emitido DEPOIS que _run_graph retorna."""
    agent = _make_agent()

    with patch.object(agent, "_run_graph",
                      side_effect=AsyncMock(return_value={
                          "messages": [MagicMock(content="ok", type="ai", tool_calls=None)]
                      })), \
         patch.object(agent, "_get_system_prompt", return_value="sys"), \
         patch.object(agent, "_sanitize_messages_pii",
                      new_callable=lambda: AsyncMock(side_effect=lambda m: m)), \
         patch("lia_agents_core.streaming_callback.StreamingCallback", return_value=fake_cb):
        try:
            await agent._process_langgraph(_make_input())
        except Exception:
            pass

    assert "composing" in fake_cb.steps, (
        f"composing deve ser emitido após _run_graph. Steps: {fake_cb.steps}"
    )


@pytest.mark.asyncio
async def test_both_phases_in_order(fake_cb):
    """understanding vem antes de composing — ordem canônica das fases."""
    agent = _make_agent()

    with patch.object(agent, "_run_graph",
                      side_effect=AsyncMock(return_value={
                          "messages": [MagicMock(content="ok", type="ai", tool_calls=None)]
                      })), \
         patch.object(agent, "_get_system_prompt", return_value="sys"), \
         patch.object(agent, "_sanitize_messages_pii",
                      new_callable=lambda: AsyncMock(side_effect=lambda m: m)), \
         patch("lia_agents_core.streaming_callback.StreamingCallback", return_value=fake_cb):
        try:
            await agent._process_langgraph(_make_input())
        except Exception:
            pass

    assert "understanding" in fake_cb.steps and "composing" in fake_cb.steps, (
        f"Ambas as fases devem ser emitidas. Steps: {fake_cb.steps}"
    )
    u_idx = fake_cb.steps.index("understanding")
    c_idx = fake_cb.steps.index("composing")
    assert u_idx < c_idx, (
        f"understanding ({u_idx}) deve vir antes de composing ({c_idx}). Steps: {fake_cb.steps}"
    )


@pytest.mark.asyncio
async def test_no_crash_without_streaming_cb():
    """Sem StreamingCallback disponível, não há crash — degradação graceful."""
    agent = _make_agent()

    with patch.object(agent, "_run_graph",
                      side_effect=AsyncMock(return_value={
                          "messages": [MagicMock(content="ok", type="ai", tool_calls=None)]
                      })), \
         patch.object(agent, "_get_system_prompt", return_value="sys"), \
         patch.object(agent, "_sanitize_messages_pii",
                      new_callable=lambda: AsyncMock(side_effect=lambda m: m)), \
         patch("lia_agents_core.streaming_callback.StreamingCallback",
               side_effect=ImportError("no cb")):
        try:
            await agent._process_langgraph(_make_input())
        except ImportError:
            pytest.fail("Emissão de reasoning não deve crashar sem StreamingCallback")
        except Exception:
            pass  # outros erros downstream são aceitáveis
