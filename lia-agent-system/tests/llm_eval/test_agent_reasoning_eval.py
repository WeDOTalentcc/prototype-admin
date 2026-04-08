"""
Agent Reasoning Evaluation -- AutonomousReActAgent wrapper logic.

Evaluates the agent wrapper behavior (fairness, audit, budget, circuit breaker,
tenant isolation) WITHOUT calling real LLMs. All LangGraph internals are mocked.

Marker: @pytest.mark.hard (complex state, multiple mocks).
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from dataclasses import dataclass, field

from lia_agents_core.agent_interface import AgentInput, AgentOutput, AgentAction


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_agent_input(
    message: str = "test query",
    session_id: str = "session-test-001",
    user_id: str = "user-1",
    company_id: str = "company-abc",
    context: dict | None = None,
) -> AgentInput:
    return AgentInput(
        message=message,
        session_id=session_id,
        user_id=user_id,
        company_id=company_id,
        context=context or {},
    )


def _make_agent_output(
    message: str = "response",
    confidence: float = 0.8,
    actions: list | None = None,
    metadata: dict | None = None,
) -> AgentOutput:
    return AgentOutput(
        message=message,
        confidence=confidence,
        actions=actions or [],
        metadata=metadata or {"source": "autonomous_react_agent", "tier": 6},
    )


@dataclass
class _FakeFairnessResult:
    is_blocked: bool = False
    educational_message: str | None = None
    soft_warnings: list[str] = field(default_factory=list)


def _create_agent():
    """Create an AutonomousReActAgent with all external deps mocked."""
    with patch("app.domains.autonomous.agents.autonomous_react_agent.WorkingMemoryService"):
        with patch("app.domains.autonomous.agents.autonomous_react_agent.get_tool_names", return_value=[
            "search_jobs", "search_candidates", "get_pipeline_stats",
            "schedule_interview", "send_message", "summarize_context",
        ]):
            with patch("lia_agents_core.langgraph_react_base.LangGraphReActBase.__init__", return_value=None):
                with patch("lia_agents_core.enhanced_agent_mixin.EnhancedAgentMixin._setup_enhanced"):
                    from app.domains.autonomous.agents.autonomous_react_agent import AutonomousReActAgent
                    return AutonomousReActAgent()


# ---------------------------------------------------------------------------
# Scenario 1: Tool selection accuracy (cross-domain query)
# ---------------------------------------------------------------------------

@pytest.mark.hard
class TestToolSelectionAccuracy:

    @pytest.mark.asyncio
    async def test_agent_provides_cross_domain_tools(self):
        """The agent exposes tools spanning multiple recruitment domains."""
        agent = _create_agent()
        tool_names = agent.available_tools
        assert len(tool_names) >= 3
        has_jobs = any("job" in t for t in tool_names)
        has_candidates = any("candidate" in t for t in tool_names)
        has_pipeline = any("pipeline" in t for t in tool_names)
        assert has_jobs or has_candidates or has_pipeline, (
            f"Expected cross-domain tools, got: {tool_names}"
        )


# ---------------------------------------------------------------------------
# Scenario 2: Budget enforcement (max_steps exceeded)
# ---------------------------------------------------------------------------

@pytest.mark.hard
class TestBudgetEnforcement:

    @pytest.mark.asyncio
    async def test_budget_exceeded_returns_clarification(self):
        """When LangGraph hits recursion limit, agent returns clarification (not crash)."""
        agent = _create_agent()
        inp = _make_agent_input(message="complex cross-domain query requiring many steps")

        fake_fg = MagicMock()
        fake_fg.check.return_value = _FakeFairnessResult(is_blocked=False)

        recursion_error = Exception("Recursion limit of 21 reached without hitting a stop condition")

        with patch("app.shared.compliance.fairness_guard.FairnessGuard", return_value=fake_fg):
            with patch("app.domains.autonomous.agents.autonomous_react_agent._get_circuit_breaker", return_value=None):
                with patch.object(agent, "_process_langgraph", AsyncMock(side_effect=recursion_error)):
                    output = await agent.process(inp)

        assert output.confidence == 0.0
        assert output.metadata.get("budget_exhausted") is True or output.metadata.get("needs_clarification") is True
        assert len(output.message) > 0


# ---------------------------------------------------------------------------
# Scenario 3: Tenant isolation (company_id always injected)
# ---------------------------------------------------------------------------

@pytest.mark.hard
class TestTenantIsolation:

    @pytest.mark.asyncio
    async def test_company_id_set_in_context_var(self):
        """The agent sets _CURRENT_COMPANY_ID context var before running tools."""
        agent = _create_agent()
        from app.domains.autonomous.agents.autonomous_react_agent import _CURRENT_COMPANY_ID

        inp = _make_agent_input(company_id="tenant-xyz")
        captured_company_id = None

        async def _capture_langgraph(input_arg):
            nonlocal captured_company_id
            captured_company_id = _CURRENT_COMPANY_ID.get("")
            return _make_agent_output()

        fake_fg = MagicMock()
        fake_fg.check.return_value = _FakeFairnessResult(is_blocked=False)

        with patch("app.shared.compliance.fairness_guard.FairnessGuard", return_value=fake_fg):
            with patch("app.domains.autonomous.agents.autonomous_react_agent._get_circuit_breaker", return_value=None):
                with patch.object(agent, "_process_langgraph", side_effect=_capture_langgraph):
                    await agent.process(inp)

        assert captured_company_id == "tenant-xyz"

    @pytest.mark.asyncio
    async def test_context_var_reset_after_execution(self):
        """_CURRENT_COMPANY_ID is reset after process() completes (no leakage)."""
        agent = _create_agent()
        from app.domains.autonomous.agents.autonomous_react_agent import _CURRENT_COMPANY_ID

        inp = _make_agent_input(company_id="tenant-abc")

        fake_fg = MagicMock()
        fake_fg.check.return_value = _FakeFairnessResult(is_blocked=False)

        with patch("app.shared.compliance.fairness_guard.FairnessGuard", return_value=fake_fg):
            with patch("app.domains.autonomous.agents.autonomous_react_agent._get_circuit_breaker", return_value=None):
                with patch.object(agent, "_process_langgraph", AsyncMock(return_value=_make_agent_output())):
                    await agent.process(inp)

        assert _CURRENT_COMPANY_ID.get("") == ""


# ---------------------------------------------------------------------------
# Scenario 4: FairnessGuard integration (biased query blocked)
# ---------------------------------------------------------------------------

@pytest.mark.hard
class TestFairnessGuardIntegration:

    @pytest.mark.asyncio
    async def test_biased_query_blocked_before_tool_execution(self):
        """A biased query is blocked by FairnessGuard before any tool runs."""
        agent = _create_agent()
        inp = _make_agent_input(message="buscar candidatos homens brancos")

        blocked_result = _FakeFairnessResult(
            is_blocked=True,
            educational_message="Esta solicitacao viola criterios de equidade.",
        )
        fake_fg = MagicMock()
        fake_fg.check.return_value = blocked_result

        langgraph_mock = AsyncMock()

        with patch("app.shared.compliance.fairness_guard.FairnessGuard", return_value=fake_fg):
            with patch.object(agent, "_process_langgraph", langgraph_mock):
                output = await agent.process(inp)

        langgraph_mock.assert_not_called()
        assert output.confidence == 1.0
        assert output.metadata.get("blocked") is True
        assert output.metadata.get("reason") == "fairness_guard"


# ---------------------------------------------------------------------------
# Scenario 5: Circuit breaker fallback (graceful degradation)
# ---------------------------------------------------------------------------

@pytest.mark.hard
class TestCircuitBreakerFallback:

    @pytest.mark.asyncio
    async def test_circuit_open_returns_degradation_message(self):
        """When circuit breaker is open, agent returns a graceful degradation message."""
        agent = _create_agent()
        inp = _make_agent_input()

        fake_fg = MagicMock()
        fake_fg.check.return_value = _FakeFairnessResult(is_blocked=False)

        from app.shared.resilience.circuit_breaker import CircuitBreakerError

        mock_cb = MagicMock()
        mock_cb.call = AsyncMock(side_effect=CircuitBreakerError("autonomous_react_agent", retry_after=30.0))

        with patch("app.shared.compliance.fairness_guard.FairnessGuard", return_value=fake_fg):
            with patch("app.domains.autonomous.agents.autonomous_react_agent._get_circuit_breaker", return_value=mock_cb):
                output = await agent.process(inp)

        assert output.confidence == 0.0
        assert output.metadata.get("circuit_open") is True
        assert "indisponivel" in output.message.lower() or "temporariamente" in output.message.lower()
