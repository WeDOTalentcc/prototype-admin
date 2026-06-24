"""Sensor — circuit_breaker_call sincrono + CircuitBreakerOpenError no modulo canonico (audit 2026-06-05 P1).

Os consumidores (jd_enrichment.py:435 etc.) importam estes simbolos de
app.shared.services.circuit_breaker (shim que re-exporta o canonico). Antes nao
existiam => ImportError => except ImportError => LLM chamado direto SEM circuito.
"""
import pytest
from app.shared.services.circuit_breaker import (  # via shim -> canonical
    circuit_breaker_call,
    CircuitBreakerOpenError,
)
from app.shared.resilience.circuit_breaker import CircuitBreakerConfig


def test_circuit_breaker_call_retorna_resultado_da_func():
    assert circuit_breaker_call(lambda x: x * 2, 21, circuit_key="cb-ok") == 42


def test_circuit_breaker_abre_apos_threshold_e_protege_chamada():
    cfg = CircuitBreakerConfig(failure_threshold=3, recovery_timeout=999)

    def boom():
        raise ValueError("upstream down")

    for _ in range(3):
        with pytest.raises(ValueError):
            circuit_breaker_call(boom, circuit_key="cb-fail", config=cfg)

    # circuito agora ABERTO: proxima chamada deve raise CircuitBreakerOpenError
    # SEM nem invocar a func protegida
    called = []

    def watched():
        called.append(1)
        return "ok"

    with pytest.raises(CircuitBreakerOpenError):
        circuit_breaker_call(watched, circuit_key="cb-fail", config=cfg)
    assert called == [], "func nao pode ser chamada com o circuito aberto"
