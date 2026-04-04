"""
FAR-3: Testes para soft_warnings visíveis ao recrutador.

Verifica que warnings de viés implícito são:
- Detectados pelo FairnessGuard Layer 2
- Propagados ao metadata do AgentOutput
- Incluídos no payload WS quando presentes
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestSoftWarningsPropagation:
    """Verifica propagação de soft_warnings no SourcingReActAgent e PipelineTransitionAgent."""

    @pytest.mark.asyncio
    async def test_sourcing_agent_propagates_soft_warnings_to_metadata(self):
        """Se a mensagem contém viés implícito, output.metadata deve ter fairness_warnings."""
        from app.domains.sourcing.agents.sourcing_react_agent import SourcingReActAgent
        from lia_agents_core.agent_interface import AgentInput, AgentOutput

        agent = SourcingReActAgent()

        # Simular output do ReAct loop
        mock_output = AgentOutput(
            message="Busca realizada com sucesso.",
            confidence=0.9,
            metadata={"duration_ms": 100.0},
        )

        with patch.object(agent, '_process_langgraph', new_callable=AsyncMock, return_value=mock_output):
            agent_input = AgentInput(
                message="buscar candidatos de bairros nobres para a vaga",
                context={},
                session_id="test-session",
                company_id="test-company",
                user_id="test-user",
                conversation_history=[],
            )
            result = await agent.process(agent_input)

        # O output deve ter fairness_warnings no metadata
        assert "fairness_warnings" in result.metadata
        assert len(result.metadata["fairness_warnings"]) > 0
        assert any("bairro" in w.lower() or "socioeconômica" in w.lower()
                   for w in result.metadata["fairness_warnings"])

    @pytest.mark.asyncio
    async def test_pipeline_agent_propagates_soft_warnings_to_metadata(self):
        """PipelineTransitionAgent também propaga soft_warnings."""
        from app.domains.pipeline.agents.pipeline_transition_agent import PipelineTransitionAgent
        from lia_agents_core.agent_interface import AgentInput, AgentOutput

        agent = PipelineTransitionAgent()

        mock_output = AgentOutput(
            message="Transição realizada.",
            confidence=0.9,
            metadata={},
        )

        with patch.object(agent, '_process_langgraph', new_callable=AsyncMock, return_value=mock_output):
            agent_input = AgentInput(
                message="mover candidatos de bairros nobres para próxima fase",
                context={"action_behavior": "passive"},
                session_id="test-session",
                company_id="test-company",
                user_id="test-user",
                conversation_history=[],
            )
            result = await agent.process(agent_input)

        assert "fairness_warnings" in result.metadata
        assert len(result.metadata["fairness_warnings"]) > 0

    @pytest.mark.asyncio
    async def test_no_warnings_when_query_is_neutral(self):
        """Query neutra não deve adicionar fairness_warnings ao metadata."""
        from app.domains.sourcing.agents.sourcing_react_agent import SourcingReActAgent
        from lia_agents_core.agent_interface import AgentInput, AgentOutput

        agent = SourcingReActAgent()

        mock_output = AgentOutput(
            message="Busca realizada.",
            confidence=0.9,
            metadata={},
        )

        with patch.object(agent, '_process_langgraph', new_callable=AsyncMock, return_value=mock_output):
            agent_input = AgentInput(
                message="buscar desenvolvedor Python sênior com 5 anos de experiência",
                context={},
                session_id="test-session",
                company_id="test-company",
                user_id="test-user",
                conversation_history=[],
            )
            result = await agent.process(agent_input)

        # Sem warnings, o campo pode estar ausente ou vazio
        warnings = result.metadata.get("fairness_warnings", []) if result.metadata else []
        assert len(warnings) == 0


class TestLogCheckSignatureFix:
    """Verifica que log_check() aceita db=None e context como dict."""

    @pytest.mark.asyncio
    async def test_log_check_accepts_dict_context(self):
        """log_check() deve aceitar context como dict sem lançar exceção."""
        from app.shared.compliance.fairness_guard import FairnessGuard, FairnessCheckResult

        guard = FairnessGuard()
        result = FairnessCheckResult(
            is_blocked=True,
            blocked_terms=["apenas homens"],
            category="genero",
            educational_message="Teste",
            original_query="apenas homens para a vaga",
            confidence=0.9,
        )

        # Não deve lançar exceção ao receber context como dict
        with patch('app.core.database.AsyncSessionLocal') as mock_session_factory:
            mock_session = AsyncMock()
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=None)
            mock_session.add = MagicMock()
            mock_session.flush = AsyncMock()
            mock_session.commit = AsyncMock()
            mock_session_factory.return_value = mock_session

            # Não deve lançar exceção
            await guard.log_check(
                result=result,
                context={"domain": "sourcing", "session_id": "test"},
                company_id="test-company",
            )

    @pytest.mark.asyncio
    async def test_log_check_accepts_input_text_kwarg(self):
        """log_check() deve ignorar input_text sem lançar exceção (retrocompatibilidade)."""
        from app.shared.compliance.fairness_guard import FairnessGuard, FairnessCheckResult

        guard = FairnessGuard()
        result = FairnessCheckResult(
            is_blocked=True,
            blocked_terms=["apenas homens"],
            category="genero",
            educational_message="Teste",
            original_query="apenas homens",
            confidence=0.9,
        )

        with patch('app.core.database.AsyncSessionLocal') as mock_session_factory:
            mock_session = AsyncMock()
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=None)
            mock_session.add = MagicMock()
            mock_session.flush = AsyncMock()
            mock_session.commit = AsyncMock()
            mock_session_factory.return_value = mock_session

            # input_text deve ser ignorado silenciosamente
            await guard.log_check(
                result=result,
                input_text="apenas homens",  # parâmetro obsoleto
                context="sourcing",
                company_id="test-company",
            )

    @pytest.mark.asyncio
    async def test_log_check_skips_clean_result(self):
        """Resultado limpo (não bloqueado, sem warnings) não deve gravar no DB."""
        from app.shared.compliance.fairness_guard import FairnessGuard, FairnessCheckResult

        guard = FairnessGuard()
        result = FairnessCheckResult(
            is_blocked=False,
            original_query="query neutra",
            soft_warnings=[],
        )

        with patch('app.core.database.AsyncSessionLocal') as mock_session_factory:
            await guard.log_check(result=result, context="sourcing")
            # Não deve ter chamado o factory
            mock_session_factory.assert_not_called()
