"""
SEG-2 — Testes de integração do FairnessGuard nos agentes ReAct.

Cobre:
  1. Mensagem limpa → processo normal (sourcing)
  2. Mensagem discriminatória → bloqueada com educational_message (sourcing)
  3. FairnessGuard falha → agente continua sem crash (fail-safe)
  4. Mensagem limpa → processo normal (pipeline)
  5. Mensagem discriminatória → bloqueada (pipeline)
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch




# ---------------------------------------------------------------------------
# Autouse fixture: prevent checkpointer init error + tenant strict mode
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _patch_checkpointer_and_tenant():
    from unittest.mock import patch as _patch, AsyncMock as _AsyncMock
    with (
        _patch("lia_agents_core.langgraph_base.get_checkpointer", return_value=None),
        _patch(
            "app.shared.agents.tenant_aware_agent.TenantAwareAgentMixin._get_tenant_context_snippet",
            new_callable=_AsyncMock,
            return_value="",
        ),
    ):
        yield

class FairnessCheckResultStub:
    def __init__(self, is_blocked=False, category=None, blocked_terms=None,
                 educational_message=None, soft_warnings=None):
        self.is_blocked = is_blocked
        self.category = category
        self.blocked_terms = blocked_terms or []
        self.educational_message = educational_message
        self.soft_warnings = soft_warnings or []


def _make_agent_input(message: str, company_id: str = "co-1"):
    from lia_agents_core.agent_interface import AgentInput
    return AgentInput(
        message=message,
        context={},
        session_id="sess-1",
        company_id=company_id,
        user_id="user-1",
        conversation_history=[],
    )


class TestSourcingFairnessGuard:
    """FairnessGuard no SourcingReActAgent."""

    @pytest.mark.asyncio
    async def test_clean_message_not_blocked(self):
        """Mensagem limpa deve passar pelo FairnessGuard sem bloqueio."""
        from app.domains.sourcing.agents.sourcing_react_agent import SourcingReActAgent
        agent = SourcingReActAgent()
        inp = _make_agent_input("Buscar candidatos com experiência em Python")

        clean_result = FairnessCheckResultStub(is_blocked=False)
        expected_output = MagicMock(
            message="ok", confidence=0.9, metadata={}, actions=[], navigation=None,
            state_updates={}, error=None, reasoning_steps=[], tool_results=[])

        with patch("app.shared.compliance.fairness_guard.FairnessGuard") as MockFG, \
             patch.object(agent, "_process_langgraph", new=AsyncMock(return_value=expected_output)):
            MockFG.return_value.check.return_value = clean_result
            MockFG.return_value.check_implicit_bias.return_value = []
            MockFG.return_value.log_check = AsyncMock()

            result = await agent.process(inp)

        assert not result.metadata.get("fairness_blocked", False)

    @pytest.mark.asyncio
    async def test_discriminatory_message_blocked(self):
        """Mensagem com viés discriminatório deve ser bloqueada."""
        from app.domains.sourcing.agents.sourcing_react_agent import SourcingReActAgent
        agent = SourcingReActAgent()
        inp = _make_agent_input("Prefiro candidatos do sexo masculino com menos de 30 anos")

        blocked_result = FairnessCheckResultStub(
            is_blocked=True,
            category="gender",
            blocked_terms=["masculino"],
            educational_message="Esta solicitação contém critérios discriminatórios."
        )

        with patch("app.shared.compliance.fairness_guard.FairnessGuard") as MockFG:
            MockFG.return_value.check.return_value = blocked_result
            MockFG.return_value.log_check = AsyncMock()

            result = await agent.process(inp)

        assert result.metadata.get("fairness_blocked", False)
        assert result.metadata.get("fairness_category") == "gender"
        assert "discriminatório" in result.message.lower()

    @pytest.mark.asyncio
    async def test_fairness_guard_failure_is_silent(self):
        """Falha no FairnessGuard não deve crashar o agente."""
        from app.domains.sourcing.agents.sourcing_react_agent import SourcingReActAgent
        agent = SourcingReActAgent()
        inp = _make_agent_input("Buscar candidatos seniors")

        expected_output = MagicMock(
            message="Resultado", confidence=0.8, metadata={}, actions=[],
            navigation=None, state_updates={}, error=None, reasoning_steps=[], tool_results=[])

        with patch("app.shared.compliance.fairness_guard.FairnessGuard") as MockFG, \
             patch.object(agent, "_process_langgraph", new=AsyncMock(return_value=expected_output)):
            MockFG.side_effect = Exception("FairnessGuard unavailable")

            result = await agent.process(inp)

        assert result is not None


class TestPipelineFairnessGuard:
    """FairnessGuard no PipelineTransitionAgent."""

    def _make_input(self, message: str):
        from lia_agents_core.agent_interface import AgentInput
        return AgentInput(
            message=message,
            context={"action_behavior": "passive"},
            session_id="sess-2",
            company_id="co-2",
            user_id="user-2",
            conversation_history=[],
        )

    @pytest.mark.asyncio
    async def test_clean_message_continues(self):
        """Mensagem limpa deve continuar para o processamento normal."""
        from app.domains.pipeline.agents.pipeline_transition_agent import PipelineTransitionAgent
        agent = PipelineTransitionAgent()
        inp = self._make_input("Quero avançar o candidato João para entrevista técnica")

        clean_result = FairnessCheckResultStub(is_blocked=False)
        expected = MagicMock(
            message="Candidato avançado", confidence=0.9, metadata={}, actions=[],
            navigation=None, state_updates={}, error=None, reasoning_steps=[], tool_results=[])

        with patch("app.shared.compliance.fairness_guard.FairnessGuard") as MockFG, \
             patch.object(agent, "_process_langgraph", new=AsyncMock(return_value=expected)):
            MockFG.return_value.check.return_value = clean_result
            MockFG.return_value.check_implicit_bias.return_value = []

            result = await agent.process(inp)

        assert not result.metadata.get("fairness_blocked", False)

    @pytest.mark.asyncio
    async def test_discriminatory_pipeline_message_blocked(self):
        """Critério discriminatório em transição deve ser bloqueado."""
        from app.domains.pipeline.agents.pipeline_transition_agent import PipelineTransitionAgent
        agent = PipelineTransitionAgent()
        inp = self._make_input("Rejeitar candidatos negros e mais velhos")

        blocked_result = FairnessCheckResultStub(
            is_blocked=True,
            category="race",
            blocked_terms=["negros"],
            educational_message="Critérios discriminatórios detectados."
        )

        with patch("app.shared.compliance.fairness_guard.FairnessGuard") as MockFG:
            MockFG.return_value.check.return_value = blocked_result
            MockFG.return_value.log_check = AsyncMock()

            result = await agent.process(inp)

        assert result.metadata.get("fairness_blocked", False)
        assert result.metadata.get("fairness_category") == "race"
