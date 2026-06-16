"""
Chaos Engineering Tests -- LLM Cascade Failure Scenarios.

Validates resilience behavior of the LLM provider fallback chain
under failure conditions: provider crashes, circuit breaker trips,
and rate limiter throttling.

Marker: @pytest.mark.hard (complex state, multiple mocks, ~100ms each).
"""
import time

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.shared.providers.llm_factory import (
    LLMProviderFactory,
    ProviderContainer,
    FALLBACK_ORDER,
)
from app.shared.resilience.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitBreakerError,
    CircuitState,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_response(text: str) -> MagicMock:
    """Create a mock LLMResponse with .text attribute."""
    resp = MagicMock()
    resp.text = text
    return resp


def _make_ok_provider(text: str = "ok") -> MagicMock:
    provider = MagicMock()
    provider.generate = AsyncMock(return_value=_make_response(text))
    provider.generate_with_system = AsyncMock(return_value=_make_response(text))
    return provider


def _make_failing_provider(exc: Exception) -> MagicMock:
    provider = MagicMock()
    provider.generate = AsyncMock(side_effect=exc)
    provider.generate_with_system = AsyncMock(side_effect=exc)
    return provider


# ---------------------------------------------------------------------------
# Scenario 1: Primary provider fails -> cascade to secondary
# ---------------------------------------------------------------------------

@pytest.mark.hard
class TestPrimaryFailsCascadeToSecondary:

    @pytest.mark.asyncio
    async def test_primary_gemini_fails_cascades_to_claude(self):
        """When the primary provider (gemini) raises, the next in FALLBACK_ORDER is called."""
        container = ProviderContainer(
            tenant_id="test-tenant",
            primary_provider="gemini",
            fallback_order=["gemini", "claude", "openai"],
        )

        gemini_provider = _make_failing_provider(RuntimeError("Gemini 503"))
        claude_provider = _make_ok_provider("claude response")
        openai_provider = _make_ok_provider("openai response")

        providers = {"gemini": gemini_provider, "claude": claude_provider, "openai": openai_provider}

        with patch.object(container, "get", side_effect=lambda name: providers[name]):
            result = await container.generate_with_fallback("test prompt")

        assert result == "claude response"
        gemini_provider.generate.assert_called_once()
        claude_provider.generate.assert_called_once()
        openai_provider.generate.assert_not_called()


# ---------------------------------------------------------------------------
# Scenario 2: All 3 providers fail -> degraded mode (graceful error)
# ---------------------------------------------------------------------------

@pytest.mark.hard
class TestAllProvidersFail:

    @pytest.mark.asyncio
    async def test_all_providers_fail_raises_with_details(self):
        """When all providers fail, a clear Exception is raised (not a crash/traceback)."""
        container = ProviderContainer(
            tenant_id="test-tenant",
            primary_provider="gemini",
            fallback_order=["gemini", "claude", "openai"],
        )

        providers = {
            "gemini": _make_failing_provider(RuntimeError("Gemini down")),
            "claude": _make_failing_provider(RuntimeError("Claude down")),
            "openai": _make_failing_provider(RuntimeError("OpenAI down")),
        }

        with patch.object(container, "get", side_effect=lambda name: providers[name]):
            with pytest.raises(Exception, match="All LLM providers failed"):
                await container.generate_with_fallback("test prompt")

    @pytest.mark.asyncio
    async def test_all_fail_error_includes_each_provider(self):
        """The aggregated error message includes details from every provider."""
        container = ProviderContainer(
            tenant_id="test-tenant",
            primary_provider="gemini",
            fallback_order=["gemini", "claude", "openai"],
        )

        providers = {
            "gemini": _make_failing_provider(ValueError("gemini_timeout")),
            "claude": _make_failing_provider(ValueError("claude_timeout")),
            "openai": _make_failing_provider(ValueError("openai_timeout")),
        }

        with patch.object(container, "get", side_effect=lambda name: providers[name]):
            with pytest.raises(Exception) as exc_info:
                await container.generate_with_fallback("test")

        msg = str(exc_info.value)
        assert "gemini" in msg
        assert "claude" in msg
        assert "openai" in msg


# ---------------------------------------------------------------------------
# Scenario 3: Circuit breaker opens after failure threshold
# ---------------------------------------------------------------------------

@pytest.mark.hard
class TestCircuitBreakerOpensAfterThreshold:

    @pytest.mark.asyncio
    async def test_circuit_opens_after_5_failures(self):
        """After 5 consecutive failures the circuit breaker transitions to OPEN."""
        cb = CircuitBreaker(
            "test-provider",
            CircuitBreakerConfig(failure_threshold=5, recovery_timeout=60.0, timeout=5.0),
        )

        failing_fn = AsyncMock(side_effect=RuntimeError("provider error"))

        for i in range(5):
            with pytest.raises(RuntimeError):
                await cb.call(failing_fn)

        assert cb.state == CircuitState.OPEN

    @pytest.mark.asyncio
    async def test_subsequent_calls_fail_fast_when_open(self):
        """Once OPEN, calls are rejected immediately with CircuitBreakerError."""
        cb = CircuitBreaker(
            "test-provider",
            CircuitBreakerConfig(failure_threshold=5, recovery_timeout=60.0, timeout=5.0),
        )

        failing_fn = AsyncMock(side_effect=RuntimeError("error"))
        for _ in range(5):
            with pytest.raises(RuntimeError):
                await cb.call(failing_fn)

        assert cb.state == CircuitState.OPEN

        # Next call should be rejected fast without calling the function
        ok_fn = AsyncMock(return_value="should not be called")
        with pytest.raises(CircuitBreakerError) as exc_info:
            await cb.call(ok_fn)

        assert exc_info.value.retry_after > 0
        ok_fn.assert_not_called()


# ---------------------------------------------------------------------------
# Scenario 4: Circuit breaker recovery (half-open)
# ---------------------------------------------------------------------------

@pytest.mark.hard
class TestCircuitBreakerRecovery:

    @pytest.mark.asyncio
    async def test_half_open_allows_one_test_call(self):
        """After recovery_timeout expires, the circuit enters HALF_OPEN and allows a test call."""
        cb = CircuitBreaker(
            "test-provider",
            CircuitBreakerConfig(
                failure_threshold=5,
                recovery_timeout=0.1,  # very short for testing
                timeout=5.0,
                success_threshold=1,
            ),
        )

        failing_fn = AsyncMock(side_effect=RuntimeError("error"))
        for _ in range(5):
            with pytest.raises(RuntimeError):
                await cb.call(failing_fn)

        assert cb.state == CircuitState.OPEN

        # Wait for recovery timeout
        time.sleep(0.15)

        # State should transition to HALF_OPEN on next access
        assert cb.state == CircuitState.HALF_OPEN

        # A successful call should close the circuit
        ok_fn = AsyncMock(return_value="recovered")
        result = await cb.call(ok_fn)
        assert result == "recovered"
        assert cb.state == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_half_open_failure_reopens_circuit(self):
        """A failure in HALF_OPEN state immediately re-opens the circuit."""
        cb = CircuitBreaker(
            "test-provider",
            CircuitBreakerConfig(
                failure_threshold=5,
                recovery_timeout=0.1,
                timeout=5.0,
            ),
        )

        failing_fn = AsyncMock(side_effect=RuntimeError("error"))
        for _ in range(5):
            with pytest.raises(RuntimeError):
                await cb.call(failing_fn)

        time.sleep(0.15)
        assert cb.state == CircuitState.HALF_OPEN

        # Fail again in half-open
        with pytest.raises(RuntimeError):
            await cb.call(failing_fn)

        assert cb.state == CircuitState.OPEN


# ---------------------------------------------------------------------------
# Scenario 5: Rate limiter throttle -> cascade
# ---------------------------------------------------------------------------

@pytest.mark.hard
class TestRateLimitCascade:

    @pytest.mark.asyncio
    async def test_rate_limit_on_primary_triggers_cascade(self):
        """When the primary provider hits a rate limit (CircuitBreakerError), cascade to secondary."""
        container = ProviderContainer(
            tenant_id="test-tenant",
            primary_provider="gemini",
            fallback_order=["gemini", "claude", "openai"],
        )

        rate_limit_error = CircuitBreakerError("gemini", retry_after=30.0)
        gemini_provider = _make_failing_provider(rate_limit_error)
        claude_provider = _make_ok_provider("claude fallback")
        openai_provider = _make_ok_provider("openai fallback")

        providers = {"gemini": gemini_provider, "claude": claude_provider, "openai": openai_provider}

        with patch.object(container, "get", side_effect=lambda name: providers[name]):
            result = await container.generate_with_fallback("test")

        assert result == "claude fallback"

    @pytest.mark.asyncio
    async def test_rate_limit_error_logged_with_retry_after(self, caplog):
        """Rate limit cascade logs the circuit open event with retry_after info."""
        import logging

        container = ProviderContainer(
            tenant_id="test-tenant",
            primary_provider="gemini",
            fallback_order=["gemini", "claude", "openai"],
        )

        rate_limit_error = CircuitBreakerError("gemini", retry_after=25.0)
        providers = {
            "gemini": _make_failing_provider(rate_limit_error),
            "claude": _make_ok_provider("ok"),
            "openai": _make_ok_provider("ok"),
        }

        with patch.object(container, "get", side_effect=lambda name: providers[name]):
            with caplog.at_level(logging.WARNING, logger="app.shared.providers.llm_factory"):
                await container.generate_with_fallback("test")

        assert any("circuit" in r.message.lower() for r in caplog.records)

    @pytest.mark.asyncio
    async def test_all_providers_rate_limited_raises(self):
        """When all providers are rate-limited (circuit open), a clear error is raised."""
        container = ProviderContainer(
            tenant_id="test-tenant",
            primary_provider="gemini",
            fallback_order=["gemini", "claude", "openai"],
        )

        providers = {
            "gemini": _make_failing_provider(CircuitBreakerError("gemini", retry_after=30.0)),
            "claude": _make_failing_provider(CircuitBreakerError("claude", retry_after=20.0)),
            "openai": _make_failing_provider(CircuitBreakerError("openai", retry_after=10.0)),
        }

        with patch.object(container, "get", side_effect=lambda name: providers[name]):
            with pytest.raises(Exception, match="All LLM providers failed"):
                await container.generate_with_fallback("test")
