"""Sensores do APIFY_CIRCUIT — is_open property + await record_failure/success.

Dois defeitos corrigidos:
1. CircuitBreaker nao tinha propriedade is_open (AttributeError em runtime)
2. record_failure/record_success sao async mas eram chamados sem await em
   contact_enrichment_service.py — coroutine nunca executava, contador nao incrementava.
"""
import pytest
from app.shared.resilience.circuit_breaker import CircuitBreaker, CircuitBreakerConfig, CircuitState


@pytest.fixture
def cb():
    return CircuitBreaker("test-apify-fix", CircuitBreakerConfig(failure_threshold=3, recovery_timeout=60))


def test_is_open_false_when_closed(cb):
    """is_open deve existir como property e retornar False quando circuit esta CLOSED."""
    assert cb.is_open is False


@pytest.mark.asyncio
async def test_is_open_true_after_enough_failures(cb):
    """is_open deve retornar True apos failure_threshold falhas."""
    for _ in range(cb.config.failure_threshold):
        await cb.record_failure()
    assert cb.is_open is True


@pytest.mark.asyncio
async def test_record_failure_increments_counter(cb):
    """await record_failure() deve incrementar _failure_count."""
    await cb.record_failure()
    assert cb.failure_count == 1


@pytest.mark.asyncio
async def test_record_success_decrements_counter(cb):
    """await record_success() deve decrementar _failure_count quando CLOSED."""
    await cb.record_failure()
    await cb.record_failure()
    await cb.record_success()
    assert cb.failure_count == 1


@pytest.mark.asyncio
async def test_state_transitions_to_open_at_threshold(cb):
    """Estado deve transitar para OPEN apos failure_threshold falhas."""
    for _ in range(cb.config.failure_threshold):
        await cb.record_failure()
    assert cb.state == CircuitState.OPEN
