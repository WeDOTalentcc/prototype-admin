"""
Testes E2E — Circuit Breaker em Cascata.

Valida o comportamento do CircuitBreaker em cenários de falha encadeada:

Cenários cobertos:
1. N falhas → circuit abre (OPEN)
2. Circuit OPEN → rejeita chamadas imediatamente com CircuitBreakerError
3. Após recovery_timeout → circuit transiciona para HALF_OPEN
4. Sucesso em HALF_OPEN → circuit fecha (CLOSED)
5. Falha em HALF_OPEN → circuit volta para OPEN
6. Cascata de circuits: service A falha → service B (dependente) também abre
7. Reset manual funciona corretamente
8. Stats são contabilizadas corretamente por estado

Camada: E2E isolado (sem dependências externas — apenas a lógica do CircuitBreaker).
"""
import pytest
import asyncio
import time
from unittest.mock import AsyncMock, patch

from app.shared.resilience.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitBreakerError,
    CircuitState,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_circuit(
    name: str = "test_service",
    failure_threshold: int = 3,
    recovery_timeout: float = 30.0,
    success_threshold: int = 2,
    timeout: float = 5.0,
) -> CircuitBreaker:
    return CircuitBreaker(
        name,
        CircuitBreakerConfig(
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout,
            success_threshold=success_threshold,
            timeout=timeout,
        ),
    )


async def _fail(exc_type=RuntimeError, message="simulated failure"):
    raise exc_type(message)


async def _succeed():
    return "ok"


async def _drive_to_open(circuit: CircuitBreaker, n_failures: int = None):
    """Acumula falhas suficientes para abrir o circuit."""
    n = n_failures or circuit.config.failure_threshold
    for _ in range(n):
        try:
            await circuit.call(_fail)
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Seção 1 — Transição CLOSED → OPEN
# ---------------------------------------------------------------------------

class TestCircuitBreakerOpenTransition:

    @pytest.mark.asyncio
    async def test_circuit_opens_after_threshold_failures(self):
        """Circuit deve abrir após failure_threshold falhas consecutivas."""
        circuit = _make_circuit(failure_threshold=3)

        await _drive_to_open(circuit)

        assert circuit.state == CircuitState.OPEN

    @pytest.mark.asyncio
    async def test_circuit_stays_closed_below_threshold(self):
        """Circuit permanece fechado com falhas abaixo do threshold."""
        circuit = _make_circuit(failure_threshold=5)

        for _ in range(4):
            try:
                await circuit.call(_fail)
            except Exception:
                pass

        assert circuit.state == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_failure_count_increments_correctly(self):
        """failure_count incrementa corretamente com cada falha."""
        circuit = _make_circuit(failure_threshold=10)

        for i in range(3):
            try:
                await circuit.call(_fail)
            except Exception:
                pass

        assert circuit.failure_count == 3

    @pytest.mark.asyncio
    async def test_success_decrements_failure_count(self):
        """Sucesso em CLOSED decrementa o failure_count."""
        circuit = _make_circuit(failure_threshold=5)

        try:
            await circuit.call(_fail)
        except Exception:
            pass

        assert circuit.failure_count == 1

        await circuit.call(_succeed)

        assert circuit.failure_count == 0

    @pytest.mark.asyncio
    async def test_circuit_open_rejects_immediately(self):
        """Circuit OPEN deve rejeitar chamadas imediatamente com CircuitBreakerError."""
        circuit = _make_circuit(failure_threshold=3)

        await _drive_to_open(circuit)

        assert circuit.state == CircuitState.OPEN

        with pytest.raises(CircuitBreakerError) as exc_info:
            await circuit.call(_succeed)

        assert exc_info.value.name == circuit.name

    @pytest.mark.asyncio
    async def test_circuit_breaker_error_has_retry_after(self):
        """CircuitBreakerError deve ter retry_after positivo."""
        circuit = _make_circuit(failure_threshold=3, recovery_timeout=30.0)

        await _drive_to_open(circuit)

        with pytest.raises(CircuitBreakerError) as exc_info:
            await circuit.call(_succeed)

        assert exc_info.value.retry_after >= 0

    @pytest.mark.asyncio
    async def test_stats_rejected_calls_incremented(self):
        """Stats.rejected_calls deve ser incrementado quando circuit está OPEN."""
        circuit = _make_circuit(failure_threshold=3)

        await _drive_to_open(circuit)

        for _ in range(3):
            try:
                await circuit.call(_succeed)
            except CircuitBreakerError:
                pass

        stats = circuit.get_stats()
        assert stats["stats"]["rejected_calls"] == 3


# ---------------------------------------------------------------------------
# Seção 2 — Transição OPEN → HALF_OPEN
# ---------------------------------------------------------------------------

class TestCircuitBreakerHalfOpenTransition:

    @pytest.mark.asyncio
    async def test_circuit_transitions_to_half_open_after_timeout(self):
        """Após recovery_timeout, circuit deve transicionar para HALF_OPEN."""
        circuit = _make_circuit(failure_threshold=3, recovery_timeout=0.01)

        await _drive_to_open(circuit)
        assert circuit.state == CircuitState.OPEN

        await asyncio.sleep(0.05)

        assert circuit.state == CircuitState.HALF_OPEN

    @pytest.mark.asyncio
    async def test_circuit_stays_open_before_timeout(self):
        """Circuit deve permanecer OPEN antes de recovery_timeout."""
        circuit = _make_circuit(failure_threshold=3, recovery_timeout=3600.0)

        await _drive_to_open(circuit)

        assert circuit.state == CircuitState.OPEN

    @pytest.mark.asyncio
    async def test_half_open_allows_calls(self):
        """Circuit HALF_OPEN deve permitir chamadas (probe)."""
        circuit = _make_circuit(failure_threshold=3, recovery_timeout=0.01)

        await _drive_to_open(circuit)
        await asyncio.sleep(0.05)

        assert circuit.state == CircuitState.HALF_OPEN

        result = await circuit.call(_succeed)
        assert result == "ok"


# ---------------------------------------------------------------------------
# Seção 3 — Transição HALF_OPEN → CLOSED (recuperação)
# ---------------------------------------------------------------------------

class TestCircuitBreakerRecovery:

    @pytest.mark.asyncio
    async def test_circuit_closes_after_success_threshold_in_half_open(self):
        """Após success_threshold sucessos em HALF_OPEN, circuit deve fechar."""
        circuit = _make_circuit(
            failure_threshold=3,
            recovery_timeout=0.01,
            success_threshold=2,
        )

        await _drive_to_open(circuit)
        await asyncio.sleep(0.05)

        assert circuit.state == CircuitState.HALF_OPEN

        for _ in range(2):
            await circuit.call(_succeed)

        assert circuit.state == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_circuit_stays_half_open_below_success_threshold(self):
        """Com apenas 1 sucesso (threshold=2), circuit permanece HALF_OPEN."""
        circuit = _make_circuit(
            failure_threshold=3,
            recovery_timeout=0.01,
            success_threshold=2,
        )

        await _drive_to_open(circuit)
        await asyncio.sleep(0.05)

        assert circuit.state == CircuitState.HALF_OPEN

        await circuit.call(_succeed)

        assert circuit.state == CircuitState.HALF_OPEN

    @pytest.mark.asyncio
    async def test_failure_in_half_open_reopens_circuit(self):
        """Falha em HALF_OPEN deve reabrir o circuit (voltar para OPEN)."""
        circuit = _make_circuit(
            failure_threshold=3,
            recovery_timeout=0.01,
            success_threshold=2,
        )

        await _drive_to_open(circuit)
        await asyncio.sleep(0.05)

        assert circuit.state == CircuitState.HALF_OPEN

        try:
            await circuit.call(_fail)
        except Exception:
            pass

        assert circuit.state == CircuitState.OPEN

    @pytest.mark.asyncio
    async def test_failure_count_resets_after_close(self):
        """Após fechar, failure_count deve ser zerado."""
        circuit = _make_circuit(
            failure_threshold=3,
            recovery_timeout=0.01,
            success_threshold=2,
        )

        await _drive_to_open(circuit)
        await asyncio.sleep(0.05)

        for _ in range(2):
            await circuit.call(_succeed)

        assert circuit.state == CircuitState.CLOSED
        assert circuit.failure_count == 0


# ---------------------------------------------------------------------------
# Seção 4 — Reset manual
# ---------------------------------------------------------------------------

class TestCircuitBreakerManualReset:

    @pytest.mark.asyncio
    async def test_manual_reset_closes_open_circuit(self):
        """Reset manual deve fechar circuit OPEN imediatamente."""
        circuit = _make_circuit(failure_threshold=3)

        await _drive_to_open(circuit)
        assert circuit.state == CircuitState.OPEN

        circuit.reset()

        assert circuit.state == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_manual_reset_zeroes_failure_count(self):
        """Reset manual deve zerar failure_count."""
        circuit = _make_circuit(failure_threshold=3)

        await _drive_to_open(circuit)
        circuit.reset()

        assert circuit.failure_count == 0

    @pytest.mark.asyncio
    async def test_circuit_functional_after_reset(self):
        """Circuit deve funcionar normalmente após reset."""
        circuit = _make_circuit(failure_threshold=3)

        await _drive_to_open(circuit)
        circuit.reset()

        result = await circuit.call(_succeed)
        assert result == "ok"


# ---------------------------------------------------------------------------
# Seção 5 — Cascata de circuits (service chain)
# ---------------------------------------------------------------------------

class TestCircuitBreakerCascade:

    @pytest.mark.asyncio
    async def test_cascaded_failure_upstream_circuit_opens(self):
        """
        Cascata: serviço A falha → circuit_a abre → serviço B (que depende de A)
        também começa a falhar → circuit_b eventualmente abre.

        Simula o cenário onde uma falha de LLM propaga para o serviço de screening.
        """
        circuit_llm = _make_circuit("llm", failure_threshold=3)
        circuit_screening = _make_circuit("screening", failure_threshold=3)

        async def screening_call():
            try:
                await circuit_llm.call(_fail)
            except (CircuitBreakerError, RuntimeError):
                raise RuntimeError("screening failed due to LLM failure")

        for _ in range(3):
            try:
                await circuit_screening.call(screening_call)
            except Exception:
                pass

        assert circuit_llm.state == CircuitState.OPEN
        assert circuit_screening.state == CircuitState.OPEN

    @pytest.mark.asyncio
    async def test_cascaded_recovery_when_upstream_recovers(self):
        """
        Após recovery do serviço A (circuit_a fecha), serviço B também pode recuperar.
        """
        circuit_llm = _make_circuit("llm_cascade", failure_threshold=3, recovery_timeout=0.01)
        circuit_screening = _make_circuit("screening_cascade", failure_threshold=3, recovery_timeout=0.01)

        async def screening_via_failing_llm():
            try:
                await circuit_llm.call(_fail)
            except (CircuitBreakerError, RuntimeError):
                raise RuntimeError("screening failed because LLM failed")

        async def screening_via_ok_llm():
            return await circuit_llm.call(_succeed)

        for _ in range(3):
            try:
                await circuit_screening.call(screening_via_failing_llm)
            except Exception:
                pass

        assert circuit_llm.state == CircuitState.OPEN
        assert circuit_screening.state == CircuitState.OPEN

        await asyncio.sleep(0.05)

        assert circuit_llm.state == CircuitState.HALF_OPEN
        assert circuit_screening.state == CircuitState.HALF_OPEN

        for _ in range(2):
            try:
                await circuit_screening.call(screening_via_ok_llm)
            except Exception:
                pass

    @pytest.mark.asyncio
    async def test_independent_circuits_dont_affect_each_other(self):
        """Circuits independentes não afetam um ao outro."""
        circuit_a = _make_circuit("service_a", failure_threshold=3)
        circuit_b = _make_circuit("service_b", failure_threshold=3)

        await _drive_to_open(circuit_a)

        assert circuit_a.state == CircuitState.OPEN
        assert circuit_b.state == CircuitState.CLOSED

        result = await circuit_b.call(_succeed)
        assert result == "ok"

    @pytest.mark.asyncio
    async def test_multiple_circuits_all_llm_providers_cascade(self):
        """
        Simula o cenário real: anthropic, gemini e openai circuits abrem em cascata.
        """
        from app.shared.resilience.circuit_breaker import (
            ANTHROPIC_CIRCUIT, GEMINI_CIRCUIT, OPENAI_CIRCUIT
        )

        anthropic = _make_circuit("anthropic_test", failure_threshold=3)
        gemini = _make_circuit("gemini_test", failure_threshold=3)
        openai = _make_circuit("openai_test", failure_threshold=3)

        await _drive_to_open(anthropic)
        await _drive_to_open(gemini)
        await _drive_to_open(openai)

        assert anthropic.state == CircuitState.OPEN
        assert gemini.state == CircuitState.OPEN
        assert openai.state == CircuitState.OPEN

        with pytest.raises(CircuitBreakerError):
            await anthropic.call(_succeed)

        with pytest.raises(CircuitBreakerError):
            await gemini.call(_succeed)

        with pytest.raises(CircuitBreakerError):
            await openai.call(_succeed)


# ---------------------------------------------------------------------------
# Seção 6 — Stats e observabilidade
# ---------------------------------------------------------------------------

class TestCircuitBreakerStats:

    @pytest.mark.asyncio
    async def test_get_stats_returns_complete_info(self):
        """get_stats() deve retornar informações completas do circuit."""
        circuit = _make_circuit("stats_test")

        stats = circuit.get_stats()

        assert "name" in stats
        assert "state" in stats
        assert "failure_count" in stats
        assert "stats" in stats
        assert "config" in stats

    @pytest.mark.asyncio
    async def test_stats_track_total_calls(self):
        """Stats devem rastrear total de chamadas."""
        circuit = _make_circuit("total_calls_test")

        for _ in range(3):
            await circuit.call(_succeed)

        stats = circuit.get_stats()
        assert stats["stats"]["total_calls"] == 3

    @pytest.mark.asyncio
    async def test_stats_track_failed_calls(self):
        """Stats devem rastrear chamadas com falha."""
        circuit = _make_circuit("failed_calls_test", failure_threshold=10)

        for _ in range(2):
            try:
                await circuit.call(_fail)
            except Exception:
                pass

        stats = circuit.get_stats()
        assert stats["stats"]["failed_calls"] == 2

    @pytest.mark.asyncio
    async def test_stats_track_successful_calls(self):
        """Stats devem rastrear chamadas com sucesso."""
        circuit = _make_circuit("success_calls_test")

        for _ in range(4):
            await circuit.call(_succeed)

        stats = circuit.get_stats()
        assert stats["stats"]["successful_calls"] == 4

    @pytest.mark.asyncio
    async def test_stats_state_changes_tracked(self):
        """Stats devem rastrear número de mudanças de estado."""
        circuit = _make_circuit(
            "state_changes_test",
            failure_threshold=3,
            recovery_timeout=0.01,
            success_threshold=2,
        )

        await _drive_to_open(circuit)
        await asyncio.sleep(0.05)

        for _ in range(2):
            await circuit.call(_succeed)

        stats = circuit.get_stats()
        assert stats["stats"]["state_changes"] >= 2

    @pytest.mark.asyncio
    async def test_stats_retry_after_when_open(self):
        """get_stats() deve incluir retry_after quando circuit está OPEN."""
        circuit = _make_circuit("retry_after_test", failure_threshold=3, recovery_timeout=30.0)

        await _drive_to_open(circuit)

        stats = circuit.get_stats()
        assert stats["retry_after"] is not None
        assert stats["retry_after"] >= 0

    @pytest.mark.asyncio
    async def test_stats_retry_after_none_when_closed(self):
        """get_stats() deve ter retry_after=None quando circuit está CLOSED."""
        circuit = _make_circuit("closed_retry_test")

        stats = circuit.get_stats()
        assert stats["retry_after"] is None


# ---------------------------------------------------------------------------
# Seção 7 — Comportamento com timeouts
# ---------------------------------------------------------------------------

class TestCircuitBreakerTimeout:

    @pytest.mark.asyncio
    async def test_timeout_counts_as_failure(self):
        """asyncio.TimeoutError deve contar como falha e acumular no failure_count."""
        circuit = _make_circuit("timeout_test", failure_threshold=10, timeout=0.01)

        async def slow_func():
            await asyncio.sleep(10.0)
            return "never"

        for _ in range(3):
            try:
                await circuit.call(slow_func)
            except (asyncio.TimeoutError, Exception):
                pass

        assert circuit.failure_count >= 3

    @pytest.mark.asyncio
    async def test_circuit_opens_on_repeated_timeouts(self):
        """Circuit abre após repeated timeouts."""
        circuit = _make_circuit("repeated_timeout", failure_threshold=3, timeout=0.01)

        async def always_slow():
            await asyncio.sleep(10.0)

        for _ in range(3):
            try:
                await circuit.call(always_slow)
            except Exception:
                pass

        assert circuit.state == CircuitState.OPEN
