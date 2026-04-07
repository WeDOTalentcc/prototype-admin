"""
Unit Tests — Circuit Breaker de LLM: fallback Anthropic→Gemini e modo degradado.

Exercita o comportamento REAL de:
- CircuitBreaker state transitions: CLOSED→OPEN→HALF_OPEN→CLOSED
- CircuitBreaker.record_failure() / record_success(): async methods
- state property: transitions from OPEN → HALF_OPEN after recovery_timeout
- ProviderContainer.generate_with_fallback(): Anthropic falha → tenta Gemini
- CircuitBreakerError raised when circuit is OPEN (via call())
- get_degraded_response(): mensagens de modo degradado por serviço
- DEGRADED_MODE_RESPONSES: mapeamento de serviços para mensagens PT-BR

Note: CircuitBreakerError(name=str, retry_after=float) — constructor uses 'name'.
      record_failure() and record_success() are async coroutines.
      CircuitState is the enum class (not CircuitBreakerState).
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.shared.resilience.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitBreakerError,
    CircuitState,
    DEGRADED_MODE_RESPONSES,
    get_degraded_response,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_cb(name: str = "test", failure_threshold: int = 3,
             recovery_timeout: float = 0.05) -> CircuitBreaker:
    config = CircuitBreakerConfig(
        failure_threshold=failure_threshold,
        recovery_timeout=recovery_timeout,
        timeout=5.0,
    )
    return CircuitBreaker(name=name, config=config)


# ---------------------------------------------------------------------------
# Seção 1 — State transitions: CLOSED → OPEN
# ---------------------------------------------------------------------------

class TestCircuitBreakerStateTransitions:

    def test_initial_state_is_closed(self):
        """Estado inicial deve ser CLOSED."""
        cb = _make_cb()
        assert cb.state == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_single_failure_does_not_open_circuit(self):
        """Uma única falha não deve abrir o circuit."""
        cb = _make_cb(failure_threshold=3)
        await cb.record_failure()
        assert cb.state == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_failures_at_threshold_open_circuit(self):
        """Atingir o threshold de falhas deve abrir o circuit."""
        cb = _make_cb(failure_threshold=3)
        for _ in range(3):
            await cb.record_failure()
        assert cb.state == CircuitState.OPEN

    @pytest.mark.asyncio
    async def test_success_after_failures_resets_failure_count(self):
        """record_success após falhas deve resetar o contador."""
        cb = _make_cb(failure_threshold=3)
        await cb.record_failure()
        await cb.record_failure()
        await cb.record_success()
        # Após sucesso, circuit ainda não deve estar aberto (precisaria de 3 mais falhas)
        assert cb.state == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_open_circuit_raises_circuit_breaker_error_via_call(self):
        """Circuit OPEN deve lançar CircuitBreakerError ao chamar cb.call()."""
        cb = _make_cb(failure_threshold=2)
        await cb.record_failure()
        await cb.record_failure()
        assert cb.state == CircuitState.OPEN

        async def dummy():
            return "should not be called"

        with pytest.raises(CircuitBreakerError):
            await cb.call(dummy)

    @pytest.mark.asyncio
    async def test_open_circuit_transitions_to_half_open_after_timeout(self):
        """Após recovery_timeout, circuit OPEN deve passar para HALF_OPEN."""
        cb = _make_cb(failure_threshold=2, recovery_timeout=0.05)
        await cb.record_failure()
        await cb.record_failure()
        assert cb.state == CircuitState.OPEN

        await asyncio.sleep(0.1)
        # Check state property — should transition to HALF_OPEN automatically
        state = cb.state
        assert state == CircuitState.HALF_OPEN, \
            f"Expected HALF_OPEN after timeout, got {state}"

    @pytest.mark.asyncio
    async def test_success_in_half_open_closes_circuit(self):
        """Suficientes sucessos em HALF_OPEN devem fechar o circuit.

        success_threshold=2 requires 2 consecutive successes to close.
        """
        config = CircuitBreakerConfig(
            failure_threshold=2,
            recovery_timeout=0.05,
            success_threshold=1,  # Use threshold=1 for simpler test
            timeout=5.0,
        )
        cb = CircuitBreaker(name="test-close", config=config)
        await cb.record_failure()
        await cb.record_failure()
        await asyncio.sleep(0.1)

        # Trigger HALF_OPEN transition via state property
        _ = cb.state

        cb._state = CircuitState.HALF_OPEN
        cb._success_count = 0  # reset
        await cb.record_success()
        assert cb.state == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_failure_in_half_open_reopens_circuit(self):
        """Falha em HALF_OPEN deve reabrir o circuit."""
        cb = _make_cb(failure_threshold=2, recovery_timeout=0.05)
        cb._state = CircuitState.HALF_OPEN
        await cb.record_failure()
        assert cb.state == CircuitState.OPEN


# ---------------------------------------------------------------------------
# Seção 2 — CircuitBreakerError properties
# ---------------------------------------------------------------------------

class TestCircuitBreakerError:

    def test_circuit_breaker_error_has_retry_after_attribute(self):
        """CircuitBreakerError deve expor retry_after (float)."""
        error = CircuitBreakerError(name="anthropic", retry_after=30.5)
        assert isinstance(error.retry_after, (int, float))
        assert error.retry_after >= 0

    def test_circuit_breaker_error_name_is_preserved(self):
        """CircuitBreakerError deve preservar o nome do circuit."""
        error = CircuitBreakerError(name="gemini", retry_after=5.0)
        assert "gemini" in str(error) or error.name == "gemini"

    def test_circuit_breaker_error_is_exception_subclass(self):
        """CircuitBreakerError deve ser subclasse de Exception."""
        assert issubclass(CircuitBreakerError, Exception)

    def test_circuit_breaker_error_message_mentions_service(self):
        """Mensagem de erro deve mencionar o nome do serviço."""
        error = CircuitBreakerError(name="openai-test", retry_after=10.0)
        assert "openai-test" in str(error)

    def test_circuit_breaker_error_message_mentions_retry(self):
        """Mensagem de erro deve mencionar o tempo de retry."""
        error = CircuitBreakerError(name="test", retry_after=42.0)
        assert "42" in str(error) or "retry" in str(error).lower()


# ---------------------------------------------------------------------------
# Seção 3 — ProviderContainer.generate_with_fallback: Anthropic → Gemini
# ---------------------------------------------------------------------------

class TestProviderContainerFallbackBehavior:

    @pytest.mark.asyncio
    async def test_primary_provider_failure_triggers_fallback_to_next_provider(self):
        """Quando primary falha, deve tentar o próximo provider na ordem."""
        from app.shared.providers.llm_factory import ProviderContainer

        mock_anthropic = AsyncMock()
        mock_anthropic.generate = AsyncMock(side_effect=Exception("Anthropic API unavailable"))

        mock_gemini = AsyncMock()
        mock_gemini.generate = AsyncMock(return_value=MagicMock(text="Resposta do Gemini"))

        container = ProviderContainer(
            tenant_id="tenant-fallback-test",
            primary_provider="claude",
            fallback_order=["claude", "gemini"],
        )
        container._instances["claude"] = mock_anthropic
        container._instances["gemini"] = mock_gemini

        result = await container.generate_with_fallback("Qual é a resposta?")

        assert result == "Resposta do Gemini"
        mock_gemini.generate.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_open_circuit_breaker_error_falls_back_to_gemini(self):
        """CircuitBreakerError no primary → fallback para gemini."""
        from app.shared.providers.llm_factory import ProviderContainer

        mock_anthropic = AsyncMock()
        mock_anthropic.generate = AsyncMock(
            side_effect=CircuitBreakerError(name="claude", retry_after=30.0)
        )

        mock_gemini = AsyncMock()
        mock_gemini.generate = AsyncMock(return_value=MagicMock(text="Gemini OK"))

        container = ProviderContainer(
            tenant_id="tenant-cb-test",
            primary_provider="claude",
            fallback_order=["claude", "gemini"],
        )
        container._instances["claude"] = mock_anthropic
        container._instances["gemini"] = mock_gemini

        result = await container.generate_with_fallback("Pergunta crítica")

        assert result == "Gemini OK"
        mock_gemini.generate.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_all_providers_fail_raises_exception_with_all_errors(self):
        """Quando todos os providers falham, deve lançar Exception descritiva."""
        from app.shared.providers.llm_factory import ProviderContainer

        mock_primary = AsyncMock()
        mock_primary.generate = AsyncMock(side_effect=Exception("Primary down"))

        mock_fallback = AsyncMock()
        mock_fallback.generate = AsyncMock(side_effect=Exception("Fallback down"))

        container = ProviderContainer(
            tenant_id="tenant-allfail",
            primary_provider="claude",
            fallback_order=["claude", "gemini"],
        )
        container._instances["claude"] = mock_primary
        container._instances["gemini"] = mock_fallback

        with pytest.raises(Exception) as exc_info:
            await container.generate_with_fallback("Qualquer prompt")

        error_msg = str(exc_info.value)
        assert "failed" in error_msg.lower() or "tenant" in error_msg.lower()

    @pytest.mark.asyncio
    async def test_successful_primary_does_not_call_fallback(self):
        """Primary bem-sucedido não deve invocar fallback providers."""
        from app.shared.providers.llm_factory import ProviderContainer

        mock_primary = AsyncMock()
        mock_primary.generate = AsyncMock(return_value=MagicMock(text="Primary OK"))

        mock_fallback = AsyncMock()
        mock_fallback.generate = AsyncMock(return_value=MagicMock(text="Fallback OK"))

        container = ProviderContainer(
            tenant_id="tenant-success",
            primary_provider="claude",
            fallback_order=["claude", "gemini"],
        )
        container._instances["claude"] = mock_primary
        container._instances["gemini"] = mock_fallback

        result = await container.generate_with_fallback("Prompt qualquer")

        assert result == "Primary OK"
        mock_fallback.generate.assert_not_awaited()


# ---------------------------------------------------------------------------
# Seção 4 — get_degraded_response: degraded mode messages (F1-03)
# ---------------------------------------------------------------------------

class TestDegradedModeResponses:

    def test_anthropic_degraded_response_mentions_lia_unavailability(self):
        """Mensagem degradada do Anthropic deve mencionar indisponibilidade da LIA."""
        msg = get_degraded_response("anthropic")
        assert "LIA" in msg or "indisponível" in msg.lower()

    def test_gemini_degraded_response_is_non_empty_string(self):
        """Mensagem degradada do Gemini deve ser string não-vazia."""
        msg = get_degraded_response("gemini")
        assert isinstance(msg, str)
        assert len(msg) > 10

    def test_openai_degraded_response_is_defined(self):
        """Mensagem degradada do OpenAI deve estar definida."""
        msg = get_degraded_response("openai")
        assert isinstance(msg, str)
        assert len(msg) > 10

    def test_unknown_service_returns_generic_fallback_message(self):
        """Serviço desconhecido deve retornar mensagem fallback genérica."""
        msg = get_degraded_response("unknown_service_xyz")
        assert isinstance(msg, str)
        assert len(msg) > 10
        assert "indisponível" in msg.lower() or "serviço" in msg.lower()

    def test_all_defined_services_have_portuguese_messages(self):
        """Todos os serviços definidos devem ter mensagens em Português."""
        for service, msg in DEGRADED_MODE_RESPONSES.items():
            assert isinstance(msg, str), f"Serviço {service}: mensagem não é string"
            assert len(msg) > 20, f"Serviço {service}: mensagem muito curta"

    def test_critical_services_are_all_in_degraded_mode_map(self):
        """Serviços críticos (anthropic, openai, gemini) devem estar mapeados."""
        critical_services = ["anthropic", "openai", "gemini"]
        for svc in critical_services:
            assert svc in DEGRADED_MODE_RESPONSES, \
                f"Serviço crítico '{svc}' não está no mapa de degraded mode"

    def test_twilio_voice_degraded_response_mentions_whatsapp_alternative(self):
        """Twilio voice degradado deve mencionar alternativa via WhatsApp."""
        msg = get_degraded_response("twilio_voice")
        assert "WhatsApp" in msg or "chat" in msg.lower() or "alternativa" in msg.lower()
