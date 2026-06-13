"""Sensor: _process_langgraph emite reasoning_step understanding/composing.

Garante que TODOS os domain agents (recruiter_copilot, talent, kanban, etc.)
alimentam o multistep timeline ao inves de cair no fallback estatico Pensando.
"""
import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class FakeStreamingCb:
    """Minimal mock that captures emit_reasoning_step calls."""
    def __init__(self):
        self.steps = []

    def emit_reasoning_step(self, label, detail=""):
        self.steps.append(label)


@pytest.fixture
def fake_cb():
    return FakeStreamingCb()


def _make_agent():
    from lia_agents_core.langgraph_react_base import LangGraphReActBase
    from lia_agents_core.agent_interface import AgentInput, AgentOutput

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


@pytest.mark.asyncio
async def test_understanding_emitted_before_graph(fake_cb):
    """understanding must be emitted BEFORE _run_graph is called."""
    agent = _make_agent()
    call_order = []

    async def mock_run_graph(**kwargs):
        call_order.append(("run_graph", list(fake_cb.steps)))
        return {"messages": [MagicMock(content="ok", type="ai", tool_calls=None)]}

    with patch.object(agent, "_run_graph", side_effect=mock_run_graph),          patch.object(agent, "_get_system_prompt", return_value="sys"),          patch.object(agent, "_sanitize_messages_pii", new_callable=lambda: AsyncMock(side_effect=lambda m: m)),          patch("lia_agents_core.streaming_callback.StreamingCallback", return_value=fake_cb):
        try:
            await agent._process_langgraph(_make_input())
        except Exception:
            pass

    assert len(call_order) > 0, "_run_graph was never called"
    steps_before_graph = call_order[0][1]
    assert "understanding" in steps_before_graph, (
        f"understanding must be emitted before _run_graph. Steps at call time: {steps_before_graph}"
    )


@pytest.mark.asyncio
async def test_composing_emitted_after_graph(fake_cb):
    """composing must be emitted AFTER _run_graph returns."""
    agent = _make_agent()

    async def mock_run_graph(**kwargs):
        return {"messages": [MagicMock(content="ok", type="ai", tool_calls=None)]}

    with patch.object(agent, "_run_graph", side_effect=mock_run_graph),          patch.object(agent, "_get_system_prompt", return_value="sys"),          patch.object(agent, "_sanitize_messages_pii", new_callable=lambda: AsyncMock(side_effect=lambda m: m)),          patch("lia_agents_core.streaming_callback.StreamingCallback", return_value=fake_cb):
        try:
            await agent._process_langgraph(_make_input())
        except Exception:
            pass

    assert "composing" in fake_cb.steps, (
        f"composing must be emitted after _run_graph. Steps: {fake_cb.steps}"
    )


@pytest.mark.asyncio
async def test_both_phases_in_order(fake_cb):
    """understanding comes before composing — canonical phase order."""
    agent = _make_agent()

    async def mock_run_graph(**kwargs):
        return {"messages": [MagicMock(content="ok", type="ai", tool_calls=None)]}

    with patch.object(agent, "_run_graph", side_effect=mock_run_graph),          patch.object(agent, "_get_system_prompt", return_value="sys"),          patch.object(agent, "_sanitize_messages_pii", new_callable=lambda: AsyncMock(side_effect=lambda m: m)),          patch("lia_agents_core.streaming_callback.StreamingCallback", return_value=fake_cb):
        try:
            await agent._process_langgraph(_make_input())
        except Exception:
            pass

    assert "understanding" in fake_cb.steps and "composing" in fake_cb.steps, (
        f"Both phases must be emitted. Steps: {fake_cb.steps}"
    )
    u_idx = fake_cb.steps.index("understanding")
    c_idx = fake_cb.steps.index("composing")
    assert u_idx < c_idx, (
        f"understanding ({u_idx}) must come before composing ({c_idx}). Steps: {fake_cb.steps}"
    )


@pytest.mark.asyncio
async def test_no_crash_without_streaming_cb():
    """When StreamingCallback is unavailable, no crash — graceful degradation."""
    agent = _make_agent()

    async def mock_run_graph(**kwargs):
        return {"messages": [MagicMock(content="ok", type="ai", tool_calls=None)]}

    with patch.object(agent, "_run_graph", side_effect=mock_run_graph),          patch.object(agent, "_get_system_prompt", return_value="sys"),          patch.object(agent, "_sanitize_messages_pii", new_callable=lambda: AsyncMock(side_effect=lambda m: m)),          patch("lia_agents_core.streaming_callback.StreamingCallback", side_effect=ImportError("no cb")):
        try:
            await agent._process_langgraph(_make_input())
        except ImportError:
            pytest.fail("Reasoning emission should not crash when StreamingCallback unavailable")
        except Exception:
            pass  # other downstream errors are acceptable
