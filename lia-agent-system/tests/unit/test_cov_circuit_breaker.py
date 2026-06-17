"""Coverage tests for app/shared/resilience/circuit_breaker.py

Tests cover:
  - Data classes: CircuitBreakerConfig, CircuitBreakerStats
  - Exception: CircuitBreakerError
  - Enum: CircuitState
  - Class: CircuitBreaker (closed/open/half-open lifecycle)
  - Functions: get_slo, get_degraded_response, get_all_circuit_stats, reset_all_circuits
  - Decorator: circuit_breaker_decorator, with_circuit_breaker
"""
import asyncio
import pytest

from app.shared.resilience.circuit_breaker import (
    CircuitState,
    CircuitBreakerConfig,
    CircuitBreakerStats,
    CircuitBreakerError,
    CircuitBreaker,
    get_slo,
    get_degraded_response,
    get_all_circuit_stats,
    reset_all_circuits,
    with_circuit_breaker,
    circuit_breaker_decorator,
    CIRCUIT_BREAKER_SLOS,
    DEGRADED_MODE_RESPONSES,
)


# ---------------------------------------------------------------------------
# CircuitState enum
# ---------------------------------------------------------------------------

class TestCircuitState:
    def test_values(self):
        assert CircuitState.CLOSED == "closed"
        assert CircuitState.OPEN == "open"
        assert CircuitState.HALF_OPEN == "half_open"

    def test_is_str(self):
        assert isinstance(CircuitState.CLOSED, str)


# ---------------------------------------------------------------------------
# CircuitBreakerConfig
# ---------------------------------------------------------------------------

class TestCircuitBreakerConfig:
    def test_defaults(self):
        cfg = CircuitBreakerConfig()
        assert cfg.failure_threshold == 5
        assert cfg.recovery_timeout == 30.0
        assert cfg.success_threshold == 2
        assert cfg.timeout == 10.0
        assert cfg.exclude_exceptions == ()

    def test_custom(self):
        cfg = CircuitBreakerConfig(
            failure_threshold=3,
            recovery_timeout=15.0,
            success_threshold=1,
            timeout=5.0,
        )
        assert cfg.failure_threshold == 3
        assert cfg.recovery_timeout == 15.0


# ---------------------------------------------------------------------------
# CircuitBreakerStats
# ---------------------------------------------------------------------------

class TestCircuitBreakerStats:
    def test_defaults(self):
        s = CircuitBreakerStats()
        assert s.total_calls == 0
        assert s.successful_calls == 0
        assert s.failed_calls == 0
        assert s.rejected_calls == 0
        assert s.state_changes == 0
        assert s.last_failure_time is None
        assert s.last_success_time is None


# ---------------------------------------------------------------------------
# CircuitBreakerError
# ---------------------------------------------------------------------------

class TestCircuitBreakerError:
    def test_basic(self):
        e = CircuitBreakerError("anthropic", retry_after=25.3)
        assert e.name == "anthropic"
        assert e.retry_after == pytest.approx(25.3)
        assert "anthropic" in str(e)
        assert "25.3" in str(e)

    def test_is_exception(self):
        e = CircuitBreakerError("svc", retry_after=0.0)
        with pytest.raises(CircuitBreakerError):
            raise e


# ---------------------------------------------------------------------------
# CircuitBreaker — lifecycle tests (async)
# ---------------------------------------------------------------------------

class TestCircuitBreakerClosed:
    async def test_initial_state_closed(self):
        cb = CircuitBreaker("test-svc")
        assert cb.state == CircuitState.CLOSED

    async def test_successful_call_stays_closed(self):
        cb = CircuitBreaker("test-svc")
        async def succeeds():
            return "ok"
        result = await cb.call(succeeds)
        assert result == "ok"
        assert cb.state == CircuitState.CLOSED

    async def test_stats_after_success(self):
        cb = CircuitBreaker("test-svc")
        async def succeeds():
            return 42
        await cb.call(succeeds)
        stats = cb.get_stats()
        assert stats["stats"]["total_calls"] == 1
        assert stats["stats"]["successful_calls"] == 1

    async def test_failure_count_increments(self):
        cfg = CircuitBreakerConfig(failure_threshold=5)
        cb = CircuitBreaker("test-svc", cfg)
        async def fails():
            raise ValueError("boom")
        with pytest.raises(ValueError):
            await cb.call(fails)
        assert cb.failure_count == 1
        assert cb.state == CircuitState.CLOSED  # still closed (threshold not reached)

    async def test_circuit_opens_after_threshold(self):
        cfg = CircuitBreakerConfig(failure_threshold=3, recovery_timeout=60.0)
        cb = CircuitBreaker("test-open", cfg)
        async def fails():
            raise RuntimeError("connection refused")
        for _ in range(3):
            with pytest.raises(RuntimeError):
                await cb.call(fails)
        assert cb.state == CircuitState.OPEN

    async def test_open_rejects_calls(self):
        cfg = CircuitBreakerConfig(failure_threshold=2, recovery_timeout=60.0)
        cb = CircuitBreaker("reject-svc", cfg)
        async def fails():
            raise IOError("down")
        for _ in range(2):
            with pytest.raises(IOError):
                await cb.call(fails)
        # Now open
        assert cb.state == CircuitState.OPEN
        async def would_succeed():
            return "should not get here"
        with pytest.raises(CircuitBreakerError) as exc_info:
            await cb.call(would_succeed)
        assert exc_info.value.name == "reject-svc"

    async def test_reset_clears_state(self):
        cfg = CircuitBreakerConfig(failure_threshold=2, recovery_timeout=60.0)
        cb = CircuitBreaker("reset-svc", cfg)
        async def fails():
            raise IOError("down")
        for _ in range(2):
            with pytest.raises(IOError):
                await cb.call(fails)
        assert cb.state == CircuitState.OPEN
        cb.reset()
        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 0

    async def test_get_stats_structure(self):
        cb = CircuitBreaker("stats-svc", CircuitBreakerConfig(failure_threshold=5))
        stats = cb.get_stats()
        assert "name" in stats
        assert "state" in stats
        assert "failure_count" in stats
        assert "config" in stats
        assert "stats" in stats
        assert stats["name"] == "stats-svc"
        assert stats["state"] == "closed"


# ---------------------------------------------------------------------------
# with_circuit_breaker helper
# ---------------------------------------------------------------------------

class TestWithCircuitBreaker:
    async def test_success(self):
        cb = CircuitBreaker("helper-svc")
        async def returns_val():
            return "value"
        result = await with_circuit_breaker(cb, returns_val)
        assert result == "value"

    async def test_propagates_exception(self):
        cb = CircuitBreaker("helper-svc2")
        async def raises():
            raise KeyError("missing")
        with pytest.raises(KeyError):
            await with_circuit_breaker(cb, raises)


# ---------------------------------------------------------------------------
# circuit_breaker_decorator
# ---------------------------------------------------------------------------

class TestCircuitBreakerDecorator:
    async def test_decorates_async_function(self):
        cb = CircuitBreaker("dec-svc")

        @circuit_breaker_decorator(cb)
        async def my_func(x):
            return x * 2

        result = await my_func(5)
        assert result == 10

    async def test_decorated_propagates_exception(self):
        cb = CircuitBreaker("dec-err-svc")

        @circuit_breaker_decorator(cb)
        async def broken():
            raise ValueError("oops")

        with pytest.raises(ValueError):
            await broken()


# ---------------------------------------------------------------------------
# get_slo / get_degraded_response
# ---------------------------------------------------------------------------

class TestGetSlo:
    def test_known_service(self):
        # CIRCUIT_BREAKER_SLOS should have some entries
        if CIRCUIT_BREAKER_SLOS:
            service = next(iter(CIRCUIT_BREAKER_SLOS))
            result = get_slo(service)
            assert isinstance(result, dict)
        else:
            pytest.skip("CIRCUIT_BREAKER_SLOS is empty in this build")

    def test_unknown_service_returns_none(self):
        result = get_slo("totally_nonexistent_service_xyz")
        assert result is None

    def test_slo_dict_has_keys(self):
        for svc, slo in CIRCUIT_BREAKER_SLOS.items():
            assert isinstance(slo, dict)
            break  # just check first entry format


class TestGetDegradedResponse:
    def test_known_service_returns_string(self):
        if DEGRADED_MODE_RESPONSES:
            service = next(iter(DEGRADED_MODE_RESPONSES))
            result = get_degraded_response(service)
            assert isinstance(result, str)
            assert len(result) > 0
        else:
            pytest.skip("DEGRADED_MODE_RESPONSES is empty")

    def test_unknown_service_returns_fallback(self):
        result = get_degraded_response("zzz_nonexistent_xyz")
        assert isinstance(result, str)
        assert len(result) > 0


# ---------------------------------------------------------------------------
# get_all_circuit_stats / reset_all_circuits
# ---------------------------------------------------------------------------

class TestGlobalHelpers:
    def test_get_all_circuit_stats_returns_dict(self):
        result = get_all_circuit_stats()
        assert isinstance(result, dict)

    def test_reset_all_circuits_does_not_raise(self):
        reset_all_circuits()  # Should not raise
