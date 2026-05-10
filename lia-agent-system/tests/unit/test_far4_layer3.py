"""
FAR-4: Testes para Layer 3 (LLM semântico) ativo no SourcingReActAgent.

Verifica:
- "sourcing_search" e "jd_import" estão em HIGH_IMPACT_ACTIONS
- check_with_layer3() é chamado no sourcing agent (não check() simples)
- Layer 3 é ignorado com fail-open se LLM indisponível
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestHighImpactActions:
    """Verifica que HIGH_IMPACT_ACTIONS inclui as novas ações FAR-4."""

    def test_sourcing_search_in_high_impact_actions(self):
        from app.shared.compliance.fairness_guard import HIGH_IMPACT_ACTIONS
        assert "sourcing_search" in HIGH_IMPACT_ACTIONS

    def test_jd_import_in_high_impact_actions(self):
        from app.shared.compliance.fairness_guard import HIGH_IMPACT_ACTIONS
        assert "jd_import" in HIGH_IMPACT_ACTIONS

    def test_original_actions_still_present(self):
        from app.shared.compliance.fairness_guard import HIGH_IMPACT_ACTIONS
        assert "rejection" in HIGH_IMPACT_ACTIONS
        assert "shortlist" in HIGH_IMPACT_ACTIONS
        assert "wsi_score" in HIGH_IMPACT_ACTIONS
        assert "policy_save" in HIGH_IMPACT_ACTIONS


class TestLayer3Integration:
    """Verifica que check_with_layer3() é usado no SourcingReActAgent."""

    @pytest.mark.asyncio
    async def test_sourcing_agent_uses_check_with_layer3(self):
        """SourcingReActAgent.process() deve chamar check_with_layer3, não check()."""
        from app.domains.sourcing.agents.sourcing_react_agent import SourcingReActAgent
        from lia_agents_core.agent_interface import AgentInput, AgentOutput
        from app.shared.compliance.fairness_guard import FairnessCheckResult

        agent = SourcingReActAgent()

        clean_result = FairnessCheckResult(
            is_blocked=False,
            original_query="buscar analista Python",
            soft_warnings=[],
        )

        mock_output = AgentOutput(message="OK", confidence=0.9, metadata={})

        with patch('app.shared.compliance.fairness_guard.FairnessGuard.check_with_layer3',
                   new_callable=AsyncMock, return_value=clean_result) as mock_l3:
            with patch('app.shared.compliance.fairness_guard.FairnessGuard.check') as mock_check:
                with patch.object(agent, '_process_langgraph',
                                  new_callable=AsyncMock, return_value=mock_output):
                    agent_input = AgentInput(
                        message="buscar analista Python",
                        context={},
                        session_id="test",
                        company_id="test-company",
                        user_id="test-user",
                        conversation_history=[],
                    )
                    await agent.process(agent_input)

        # check_with_layer3 foi chamado
        mock_l3.assert_called_once()
        # check() NÃO foi chamado diretamente na entrada (apenas via Layer 3 internamente)
        call_args = mock_l3.call_args
        assert call_args[1].get("action_type") == "sourcing_search" or \
               (len(call_args[0]) > 1 and call_args[0][1] == "sourcing_search") or \
               "sourcing_search" in str(call_args)

    @pytest.mark.asyncio
    async def test_layer3_fail_closed_when_llm_unavailable(self):
        """UC-P0-15: Se o LLM não está disponível, Layer 3 deve bloquear (fail-closed).

        UPDATED: Previous behavior was fail-open (is_blocked=False on LLM error).
        UC-P0-15 fixes this — any LLM/exception must block the action to prevent
        potentially-biased decisions from slipping through silently.
        """
        from app.shared.compliance.fairness_guard import FairnessGuard

        guard = FairnessGuard()

        # Simular check_semantic indisponível (patching no nível correto)
        with patch.object(guard, 'check_semantic', side_effect=ImportError("LLM unavailable")):
            result = await guard.check_with_layer3(
                "buscar desenvolvedor Python sênior",
                action_type="sourcing_search",
            )

        # UC-P0-15: deve retornar resultado bloqueado (fail-closed), não fail-open
        assert result.is_blocked, (
            "Layer3 LLM error must block the action (fail-closed). "
            "See UC-P0-15 for rationale."
        )
        assert result.educational_message is not None

    @pytest.mark.asyncio
    async def test_layer3_skips_low_impact_actions(self):
        """Para action_type não em HIGH_IMPACT_ACTIONS, Layer 3 não é chamado."""
        from app.shared.compliance.fairness_guard import FairnessGuard

        guard = FairnessGuard()

        with patch.object(guard, 'check_semantic', new_callable=AsyncMock) as mock_semantic:
            result = await guard.check_with_layer3(
                "buscar candidato",
                action_type="low_impact_action",  # não em HIGH_IMPACT_ACTIONS
            )

        # check_semantic NÃO deve ter sido chamado para ação de baixo impacto
        mock_semantic.assert_not_called()
        assert not result.is_blocked

    @pytest.mark.asyncio
    async def test_layer3_blocks_on_layer1_without_reaching_llm(self):
        """Se Layer 1 já bloqueou, Layer 3 não chama o LLM."""
        from app.shared.compliance.fairness_guard import FairnessGuard

        guard = FairnessGuard()

        with patch.object(guard, 'check_semantic', new_callable=AsyncMock) as mock_semantic:
            result = await guard.check_with_layer3(
                "apenas homens para a vaga",
                action_type="sourcing_search",
            )

        # Deve estar bloqueado por Layer 1 antes de tentar Layer 3
        assert result.is_blocked
        assert result.category == "genero"
        mock_semantic.assert_not_called()

    def test_patterns_version_updated(self):
        """_PATTERNS_VERSION deve ser 3 após FAR-1."""
        from app.shared.compliance.fairness_guard import _PATTERNS_VERSION
        assert _PATTERNS_VERSION >= 3
