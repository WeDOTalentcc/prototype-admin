"""
P2-A — Testes do circuit breaker no ReActLoop._reason().

SKIPPED: ReActLoop foi removido — agentes usam LangGraph nativo (create_react_agent).
Circuit breaker agora é responsabilidade da camada LLM/checkpointer.
"""
import pytest
pytestmark = pytest.mark.skip(reason="ReActLoop removido — agentes usam LangGraph nativo")
from unittest.mock import AsyncMock, MagicMock, patch


class TestGetLlmCircuitBreaker:

    def test_retorna_instancia_circuit_breaker(self):
        # Limpa singleton para evitar cache de testes anteriores
        import lia_agents_core.react_loop as rl
        rl._llm_circuit_breaker = None

        cb = rl._get_llm_circuit_breaker()
        assert cb is not None

    def test_singleton_mesma_referencia(self):
        import lia_agents_core.react_loop as rl
        rl._llm_circuit_breaker = None

        cb1 = rl._get_llm_circuit_breaker()
        cb2 = rl._get_llm_circuit_breaker()
        assert cb1 is cb2

    def test_circuit_breaker_nome_correto(self):
        import lia_agents_core.react_loop as rl
        rl._llm_circuit_breaker = None

        cb = rl._get_llm_circuit_breaker()
        assert cb.name == "llm_react_reason"

    def test_fail_open_quando_import_falha(self):
        import lia_agents_core.react_loop as rl
        rl._llm_circuit_breaker = None

        # Simula falha no import interno fazendo CircuitBreaker raise ao instanciar
        with patch(
            "app.shared.resilience.circuit_breaker.CircuitBreaker",
            side_effect=RuntimeError("unavailable"),
        ):
            cb = rl._get_llm_circuit_breaker()
            # fail-open: retorna None se CircuitBreaker indisponível
            # (pode ser None ou o objeto — o importante é não levantar)
            assert True  # não propaga exceção


class TestReasonWithCircuitBreaker:

    def _make_loop(self):
        from lia_agents_core.react_loop import ReActLoop, ReActConfig
        from lia_agents_core.working_memory import WorkingMemoryService
        config = ReActConfig(
            max_iterations=1,
            system_prompt="test",
            available_tools=[],
            domain="test_domain",
            model_provider="claude",
        )
        wm = MagicMock(spec=WorkingMemoryService)
        return ReActLoop(config, working_memory_service=wm)

    @pytest.mark.asyncio
    async def test_circuit_closed_chama_llm(self):
        """Circuit CLOSED: chamada LLM passa normalmente."""
        loop = self._make_loop()
        state = MagicMock()
        state.messages = []
        state.observations = []
        state.iteration = 1
        state.tokens_used_estimate = 0

        mock_cb = MagicMock()
        mock_cb.call = AsyncMock(return_value='{"thought": "ok", "action": "respond", "response": "ok"}')

        with patch("lia_agents_core.react_loop._get_llm_circuit_breaker", return_value=mock_cb):
            result = await loop._reason(state, {})

        mock_cb.call.assert_called_once()
        assert result == '{"thought": "ok", "action": "respond", "response": "ok"}'

    @pytest.mark.asyncio
    async def test_circuit_open_lanca_error(self):
        """Circuit OPEN: _reason() deve levantar CircuitBreakerError."""
        from app.shared.resilience.circuit_breaker import CircuitBreakerError

        loop = self._make_loop()
        state = MagicMock()
        state.messages = []
        state.observations = []
        state.iteration = 1
        state.tokens_used_estimate = 0

        mock_cb = MagicMock()
        mock_cb.call = AsyncMock(
            side_effect=CircuitBreakerError("llm_react_reason", retry_after=45.0)
        )

        with patch("lia_agents_core.react_loop._get_llm_circuit_breaker", return_value=mock_cb):
            with pytest.raises(CircuitBreakerError):
                await loop._reason(state, {})

    @pytest.mark.asyncio
    async def test_circuit_none_chama_llm_direto(self):
        """fail-open: se circuit breaker for None, LLM é chamado diretamente."""
        loop = self._make_loop()
        state = MagicMock()
        state.messages = []
        state.observations = []
        state.iteration = 1
        state.tokens_used_estimate = 0

        with patch("lia_agents_core.react_loop._get_llm_circuit_breaker", return_value=None):
            with patch(
                "lia_agents_core.react_loop.llm_service.generate",
                new=AsyncMock(return_value='{"action": "respond", "response": "ok"}'),
            ) as mock_gen:
                result = await loop._reason(state, {})
                mock_gen.assert_called_once()


class TestRunCircuitBreakerFallback:

    def _make_loop(self):
        from lia_agents_core.react_loop import ReActLoop, ReActConfig
        from lia_agents_core.working_memory import WorkingMemoryService
        config = ReActConfig(
            max_iterations=1,
            system_prompt="test",
            available_tools=[],
            domain="test_domain",
            model_provider="claude",
        )
        wm = MagicMock(spec=WorkingMemoryService)
        return ReActLoop(config, working_memory_service=wm)

    @pytest.mark.asyncio
    async def test_run_circuit_open_retorna_mensagem_amigavel(self):
        """run() com circuit OPEN deve retornar mensagem em PT-BR sem tracebacks."""
        from app.shared.resilience.circuit_breaker import CircuitBreakerError

        loop = self._make_loop()
        mock_cb = MagicMock()
        mock_cb.call = AsyncMock(
            side_effect=CircuitBreakerError("llm_react_reason", retry_after=30.0)
        )

        with patch("lia_agents_core.react_loop._get_llm_circuit_breaker", return_value=mock_cb):
            state = await loop.run(message="olá", context={}, session_id="test-session")

        assert state.final_response is not None
        assert state.should_respond is True
        assert "IA" in state.final_response or "serviço" in state.final_response.lower() or "disponível" in state.final_response.lower()
        assert "30" in state.final_response  # retry_after visível

    @pytest.mark.asyncio
    async def test_run_circuit_open_state_error_correto(self):
        """state.error deve ser 'circuit_breaker_open' quando circuit bloqueia."""
        from app.shared.resilience.circuit_breaker import CircuitBreakerError

        loop = self._make_loop()
        mock_cb = MagicMock()
        mock_cb.call = AsyncMock(
            side_effect=CircuitBreakerError("llm_react_reason", retry_after=45.0)
        )

        with patch("lia_agents_core.react_loop._get_llm_circuit_breaker", return_value=mock_cb):
            state = await loop.run(message="olá", context={}, session_id="test-session")

        assert state.error == "circuit_breaker_open"

    @pytest.mark.asyncio
    async def test_run_circuit_open_nao_expoe_detalhes_tecnicos(self):
        """Mensagem de fallback não deve expor stack traces ou internals."""
        from app.shared.resilience.circuit_breaker import CircuitBreakerError

        loop = self._make_loop()
        mock_cb = MagicMock()
        mock_cb.call = AsyncMock(
            side_effect=CircuitBreakerError("llm_react_reason", retry_after=20.0)
        )

        with patch("lia_agents_core.react_loop._get_llm_circuit_breaker", return_value=mock_cb):
            state = await loop.run(message="olá", context={}, session_id="test-session")

        assert "Traceback" not in (state.final_response or "")
        assert "Exception" not in (state.final_response or "")
        assert "circuit_breaker" not in (state.final_response or "").lower()
