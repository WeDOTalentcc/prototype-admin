"""
Tests — F1-03: SLOs e Degraded Mode no Circuit Breaker.

Cobre:
  1. CIRCUIT_BREAKER_SLOS contém todos os circuits críticos
  2. DEGRADED_MODE_RESPONSES contém todos os circuits de SLOS
  3. get_degraded_response retorna mensagem específica para circuit conhecido
  4. get_degraded_response retorna fallback genérico para circuit desconhecido
  5. get_slo retorna SLO correto para anthropic
  6. get_slo retorna None para service desconhecido
  7. _compute_slo_status retorna 'breached' quando circuit OPEN
  8. _compute_slo_status retorna 'ok' quando circuit CLOSED sem falhas
  9. _compute_slo_status retorna 'unknown' sem SLO definido
 10. _compute_slo_status retorna 'breached' quando error_rate > budget
 11. SLOs de circuits críticos têm availability >= 99.9%
 12. Admin endpoint retorna campo slo_status (smoke test via _get_combined_status)
"""
import pytest
from app.shared.resilience.circuit_breaker import (
    CIRCUIT_BREAKER_SLOS,
    DEGRADED_MODE_RESPONSES,
    get_degraded_response,
    get_slo,
)


# -------------------------------------------------------------------
# 1. SLOs contém circuits críticos
# -------------------------------------------------------------------
def test_slos_contains_critical_circuits():
    critical = ["anthropic", "openai", "workos", "mailgun"]
    for name in critical:
        assert name in CIRCUIT_BREAKER_SLOS, f"SLO não definido para circuit crítico: {name}"


def test_slos_contains_all_all_circuits():
    from app.shared.resilience.circuit_breaker import ALL_CIRCUITS
    for name in ALL_CIRCUITS:
        assert name in CIRCUIT_BREAKER_SLOS, f"SLO faltando para circuit registrado: {name}"


# -------------------------------------------------------------------
# 2. DEGRADED_MODE_RESPONSES cobre todos os SLOs
# -------------------------------------------------------------------
def test_degraded_responses_cover_all_slos():
    for name in CIRCUIT_BREAKER_SLOS:
        assert name in DEGRADED_MODE_RESPONSES, (
            f"Mensagem de modo degradado faltando para: {name}"
        )


# -------------------------------------------------------------------
# 3. get_degraded_response — circuit conhecido
# -------------------------------------------------------------------
def test_get_degraded_response_known():
    msg = get_degraded_response("anthropic")
    assert "LIA" in msg or "Anthropic" in msg or "indisponível" in msg


def test_get_degraded_response_pearch():
    msg = get_degraded_response("pearch")
    assert "candidatos" in msg.lower()


# -------------------------------------------------------------------
# 4. get_degraded_response — fallback genérico
# -------------------------------------------------------------------
def test_get_degraded_response_unknown():
    msg = get_degraded_response("servico_inexistente_xyz")
    assert "indisponível" in msg.lower()
    assert len(msg) > 10


# -------------------------------------------------------------------
# 5. get_slo — anthropic
# -------------------------------------------------------------------
def test_get_slo_anthropic():
    slo = get_slo("anthropic")
    assert slo is not None
    assert slo["availability_target"] >= 0.999
    assert slo["tier"] == "critical"
    assert "latency_p95_ms" in slo


# -------------------------------------------------------------------
# 6. get_slo — serviço desconhecido
# -------------------------------------------------------------------
def test_get_slo_unknown_returns_none():
    assert get_slo("servico_inexistente") is None


# -------------------------------------------------------------------
# 7. _compute_slo_status — OPEN → breached
# -------------------------------------------------------------------
def test_compute_slo_status_open_is_breached():
    from app.api.v1.admin_circuit_breakers import _compute_slo_status
    slo = CIRCUIT_BREAKER_SLOS["anthropic"]
    stats = {"state": "open", "total_calls": 100, "failed_calls": 10}
    assert _compute_slo_status("anthropic", stats, slo) == "breached"


# -------------------------------------------------------------------
# 8. _compute_slo_status — CLOSED sem falhas → ok
# -------------------------------------------------------------------
def test_compute_slo_status_closed_ok():
    from app.api.v1.admin_circuit_breakers import _compute_slo_status
    slo = CIRCUIT_BREAKER_SLOS["anthropic"]
    stats = {"state": "closed", "total_calls": 1000, "failed_calls": 0}
    assert _compute_slo_status("anthropic", stats, slo) == "ok"


# -------------------------------------------------------------------
# 9. _compute_slo_status — sem SLO → unknown
# -------------------------------------------------------------------
def test_compute_slo_status_no_slo():
    from app.api.v1.admin_circuit_breakers import _compute_slo_status
    stats = {"state": "closed", "total_calls": 100, "failed_calls": 1}
    assert _compute_slo_status("servico_sem_slo", stats, None) == "unknown"


# -------------------------------------------------------------------
# 10. _compute_slo_status — error_rate > budget → breached
# -------------------------------------------------------------------
def test_compute_slo_status_high_error_rate():
    from app.api.v1.admin_circuit_breakers import _compute_slo_status
    # anthropic: error_budget_pct=0.1 → budget=0.001 (0.1%)
    # 5 falhas em 100 chamadas = 5% → breached
    slo = CIRCUIT_BREAKER_SLOS["anthropic"]
    stats = {"state": "closed", "total_calls": 100, "failed_calls": 5, "total_failures": 5}
    assert _compute_slo_status("anthropic", stats, slo) == "breached"


# -------------------------------------------------------------------
# 11. SLOs críticos têm availability >= 99.9%
# -------------------------------------------------------------------
def test_critical_circuits_have_high_availability():
    for name, slo in CIRCUIT_BREAKER_SLOS.items():
        if slo.get("tier") == "critical":
            assert slo["availability_target"] >= 0.999, (
                f"Circuit crítico '{name}' tem SLO de disponibilidade abaixo de 99.9%"
            )


# -------------------------------------------------------------------
# 12. Admin endpoint — smoke test de _get_combined_status
# -------------------------------------------------------------------
def test_combined_status_includes_slo_fields():
    from unittest.mock import patch, MagicMock
    from app.api.v1.admin_circuit_breakers import _get_combined_status

    mock_class_stats = {
        "anthropic": {"state": "closed", "total_calls": 50, "failed_calls": 0},
    }
    mock_functional_status = {}

    with patch("app.api.v1.admin_circuit_breakers.get_all_circuit_stats", return_value=mock_class_stats), \
         patch("app.api.v1.admin_circuit_breakers.get_all_circuits_status", return_value=mock_functional_status):
        combined = _get_combined_status()

    assert "anthropic" in combined
    entry = combined["anthropic"]
    assert "slo" in entry
    assert "slo_status" in entry
    assert "degraded_mode_message" in entry
    assert entry["slo_status"] in ("ok", "breached", "unknown")
    assert len(entry["degraded_mode_message"]) > 10
