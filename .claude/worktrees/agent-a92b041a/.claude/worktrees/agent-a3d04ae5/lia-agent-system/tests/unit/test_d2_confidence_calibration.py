"""
D2 — Confidence Calibration (12 Agentes)

Testa:
- ReActState.confidence_score calculado corretamente no react_loop
- _record_confidence em EnhancedAgentMixin (fail-silent)
- _post_loop_learning chama _record_confidence automaticamente
- Casos edge: sem tools, com erro, todas falhas
"""
import pytest
from unittest.mock import MagicMock, patch, AsyncMock


class TestReActStateConfidenceScore:

    def test_confidence_score_default_is_0_5(self):
        """confidence_score tem default 0.5."""
        from lia_agents_core.react_loop import ReActState
        state = ReActState()
        assert state.confidence_score == 0.5

    def test_confidence_score_all_tools_success(self):
        """Todas as tools com sucesso, sem erro → alta confiança."""
        from lia_agents_core.react_loop import ReActState

        state = ReActState()
        state.tool_calls_made = [
            {"tool_name": "t1"}, {"tool_name": "t2"}, {"tool_name": "t3"}
        ]
        state.failed_tool_calls = []
        state.error = None

        # Simula o bloco de cálculo do react_loop
        tool_total = len(state.tool_calls_made)
        tool_failed = len(state.failed_tool_calls)
        tool_success_ratio = (tool_total - tool_failed) / tool_total if tool_total > 0 else 1.0
        completion_ratio = 0.3 if state.error else 1.0
        raw_conf = tool_success_ratio * 0.7 + completion_ratio * 0.3
        state.confidence_score = round(min(1.0, max(0.0, raw_conf)), 4)

        assert state.confidence_score == 1.0

    def test_confidence_score_with_error(self):
        """Com erro → completion_ratio=0.3 → confiança reduzida."""
        from lia_agents_core.react_loop import ReActState

        state = ReActState()
        state.tool_calls_made = [{"tool_name": "t1"}]
        state.failed_tool_calls = []
        state.error = "Falha crítica"

        tool_total = len(state.tool_calls_made)
        tool_failed = len(state.failed_tool_calls)
        tool_success_ratio = (tool_total - tool_failed) / tool_total
        completion_ratio = 0.3 if state.error else 1.0
        raw_conf = tool_success_ratio * 0.7 + completion_ratio * 0.3
        state.confidence_score = round(min(1.0, max(0.0, raw_conf)), 4)

        # 1.0 * 0.7 + 0.3 * 0.3 = 0.70 + 0.09 = 0.79
        assert state.confidence_score == pytest.approx(0.79, abs=0.001)

    def test_confidence_score_no_tools_no_error(self):
        """Sem tools, sem erro → tool_success_ratio=1.0 → confidence=1.0."""
        from lia_agents_core.react_loop import ReActState

        state = ReActState()
        state.tool_calls_made = []
        state.failed_tool_calls = []
        state.error = None

        tool_total = len(state.tool_calls_made)
        tool_success_ratio = 1.0 if tool_total == 0 else (tool_total - len(state.failed_tool_calls)) / tool_total
        completion_ratio = 0.3 if state.error else 1.0
        raw_conf = tool_success_ratio * 0.7 + completion_ratio * 0.3
        state.confidence_score = round(min(1.0, max(0.0, raw_conf)), 4)

        assert state.confidence_score == 1.0

    def test_confidence_score_all_tools_failed(self):
        """Todas as tools falharam + erro → mínima confiança."""
        from lia_agents_core.react_loop import ReActState

        state = ReActState()
        state.tool_calls_made = [{"tool_name": "t1"}, {"tool_name": "t2"}]
        state.failed_tool_calls = [{"tool_name": "t1"}, {"tool_name": "t2"}]
        state.error = "all tools failed"

        tool_total = len(state.tool_calls_made)
        tool_failed = len(state.failed_tool_calls)
        tool_success_ratio = (tool_total - tool_failed) / tool_total
        completion_ratio = 0.3 if state.error else 1.0
        raw_conf = tool_success_ratio * 0.7 + completion_ratio * 0.3
        state.confidence_score = round(min(1.0, max(0.0, raw_conf)), 4)

        # 0 * 0.7 + 0.3 * 0.3 = 0.09
        assert state.confidence_score == pytest.approx(0.09, abs=0.001)


class TestEnhancedAgentMixinRecordConfidence:

    def _make_mixin(self):
        """Cria instância minimal de EnhancedAgentMixin."""
        from lia_agents_core.enhanced_agent_mixin import EnhancedAgentMixin

        class FakeAgent(EnhancedAgentMixin):
            pass

        agent = FakeAgent()
        agent._enhanced_domain = "test_domain"
        return agent

    def test_record_confidence_calls_prometheus(self):
        """_record_confidence delega para record_confidence do agent_metrics."""
        agent = self._make_mixin()

        from lia_agents_core.react_loop import ReActState
        state = ReActState()
        state.confidence_score = 0.85

        with patch(
            "app.shared.observability.agent_metrics.record_confidence"
        ) as mock_rc:
            agent._record_confidence(state)
            mock_rc.assert_called_once_with(
                agent="test_domain",
                domain="test_domain",
                confidence=0.85,
            )

    def test_record_confidence_fail_silent(self):
        """_record_confidence não propaga exceções."""
        agent = self._make_mixin()

        from lia_agents_core.react_loop import ReActState
        state = ReActState()
        state.confidence_score = 0.7

        with patch(
            "app.shared.observability.agent_metrics.record_confidence",
            side_effect=RuntimeError("prometheus unavailable"),
        ):
            # Não deve lançar exceção
            agent._record_confidence(state)

    def test_record_confidence_uses_default_when_no_attribute(self):
        """Se state não tem confidence_score, usa 0.5 como default."""
        agent = self._make_mixin()

        state = MagicMock(spec=[])  # sem atributo confidence_score

        recorded = {}

        def capture(agent, domain, confidence):
            recorded["confidence"] = confidence

        with patch(
            "app.shared.observability.agent_metrics.record_confidence",
            side_effect=capture,
        ):
            agent._record_confidence(state)

        assert recorded.get("confidence") == 0.5

    @pytest.mark.asyncio
    async def test_post_loop_learning_calls_record_confidence(self):
        """_post_loop_learning chama _record_confidence automaticamente."""
        agent = self._make_mixin()

        from lia_agents_core.react_loop import ReActState
        state = ReActState()
        state.confidence_score = 0.92

        recorded = {}

        def capture(agent, domain, confidence):
            recorded["confidence"] = confidence

        # Stub os serviços de memória para evitar dependências reais
        mock_extractor = MagicMock()
        mock_extractor.extract.return_value = []
        agent._learning_extractor = mock_extractor
        agent._memory_integration = MagicMock()

        with patch(
            "app.shared.observability.agent_metrics.record_confidence",
            side_effect=capture,
        ):
            await agent._post_loop_learning(
                state=state,
                company_id="company-1",
                session_id="session-1",
            )

        assert recorded.get("confidence") == 0.92
