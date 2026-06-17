"""
Admin — Circuit Breakers status e controle manual.

Endpoints:
  GET  /api/v1/admin/circuit-breakers         → status de todos os circuits
  POST /api/v1/admin/circuit-breakers/{name}/reset  → reset manual de um circuit
  POST /api/v1/admin/circuit-breakers/reset-all     → reset de todos os circuits

Acesso restrito a admins (require_admin).
Referência: app/shared/resilience/circuit_breaker.py
"""
import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Path

from app.auth.dependencies import require_admin
from app.shared.resilience.circuit_breaker import (
    ALL_CIRCUITS,
    CIRCUIT_BREAKER_SLOS,
    _circuits,
    get_all_circuit_stats,
    get_all_circuits_status,
    get_degraded_response,
    reset_all_circuits,
    reset_circuit,
)
from app.shared.security.require_company_id import require_company_id
from app.shared.errors import LIAError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin/circuit-breakers", tags=["Admin - Circuit Breakers"])


def _get_combined_status() -> dict[str, Any]:
    """
    Combina status da instância de classes (ALL_CIRCUITS) e
    da instância funcional (_circuits) em um único dict.
    """
    class_stats = get_all_circuit_stats()
    functional_status = get_all_circuits_status()

    combined: dict[str, Any] = {}

    # Instâncias baseadas em classe
    for name, stats in class_stats.items():
        slo = CIRCUIT_BREAKER_SLOS.get(name)
        combined[name] = {
            "implementation": "class",
            **stats,
            "slo": slo,
            "slo_status": _compute_slo_status(name, stats, slo),
            "degraded_mode_message": get_degraded_response(name),
        }

    # Instâncias funcionais (podem ter nomes diferentes)
    for name, status in functional_status.items():
        if name not in combined:
            slo = CIRCUIT_BREAKER_SLOS.get(name)
            combined[name] = {
                "implementation": "functional",
                **status,
                "slo": slo,
                "slo_status": _compute_slo_status(name, status, slo),
                "degraded_mode_message": get_degraded_response(name),
            }

    return combined


def _compute_slo_status(name: str, stats: dict, slo: dict | None) -> str:
    """
    Calcula se o circuit está dentro do SLO definido.
    Retorna: 'ok' | 'breached' | 'unknown'
    """
    if not slo:
        return "unknown"
    # Se o circuit está OPEN, SLO de disponibilidade está sendo violado
    if stats.get("state") == "open":
        return "breached"
    # Se falhas recentes > (1 - availability_target) * total_calls, SLO comprometido
    total = stats.get("total_calls", 0) or stats.get("total_calls", 0)
    failed = stats.get("failed_calls", 0) or stats.get("total_failures", 0)
    if total > 0:
        error_rate = failed / total
        budget = 1.0 - slo.get("availability_target", 0.999)
        if error_rate > budget:
            return "breached"
    return "ok"


@router.get("", summary="Status de todos os circuit breakers", response_model=None)
async def list_circuit_breakers(_user=Depends(require_admin), company_id: str = Depends(require_company_id)) -> dict[str, Any]:
    # multi-tenancy: admin/platform-level (admin_) — role-based access required
    """
    Retorna estado atual (CLOSED / OPEN / HALF_OPEN), contadores de falha
    e estatísticas de cada circuit breaker registrado na plataforma.

    Circuits monitorados: anthropic, openai, gemini, pearch, workos, merge,
    google_calendar + quaisquer circuits funcionais criados em runtime.
    """
    try:
        status = _get_combined_status()  # uses module-level imports
        return {
            "total": len(status),
            "open_count": sum(
                1 for v in status.values()
                if v.get("state") == "open"
            ),
            "circuits": status,
        }
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("[CircuitBreakerAdmin] Erro ao listar circuits: %s", exc)
        raise LIAError(message="Erro interno do servidor")


@router.post("/{circuit_name}/reset", summary="Reset manual de um circuit breaker", response_model=None)
async def reset_circuit_breaker(
    circuit_name: str = Path(..., description="Nome do circuit breaker"),
    _user=Depends(require_admin),
company_id: str = Depends(require_company_id)) -> dict[str, Any]:
    # multi-tenancy: admin/platform-level (admin_) — role-based access required
    """
    Força transição para CLOSED e zera o failure_count do circuit especificado.

    Usar com cautela: reseta o estado de proteção mesmo que o serviço
    subjacente ainda esteja com problemas.
    """
    # Tenta reset em instância de classe primeiro
    if circuit_name in ALL_CIRCUITS:
        ALL_CIRCUITS[circuit_name].reset()
        logger.warning(
            "[CircuitBreakerAdmin] Reset manual: circuit=%s por user=%s",
            circuit_name, getattr(_user, "id", "admin"),
        )
        return {"circuit": circuit_name, "action": "reset", "new_state": "closed"}

    # Tenta reset em instância funcional
    if circuit_name in _circuits:
        reset_circuit(circuit_name)
        return {"circuit": circuit_name, "action": "reset", "new_state": "closed"}

    raise HTTPException(
        status_code=404,
        detail=f"Circuit breaker '{circuit_name}' não encontrado. "
               f"Disponíveis: {sorted(list(ALL_CIRCUITS) + list(_circuits))}",
    )


@router.post("/reset-all", summary="Reset de todos os circuit breakers", response_model=None)
async def reset_all_circuit_breakers(_user=Depends(require_admin), company_id: str = Depends(require_company_id)) -> dict[str, Any]:
    # multi-tenancy: admin/platform-level (admin_) — role-based access required
    """
    Força CLOSED em todos os circuit breakers (classe + funcionais).

    Operação de emergência — usar apenas quando se tem certeza de que
    os serviços externos estão operacionais.
    """
    reset_all_circuits()  # instâncias de classe
    failed: list[str] = []
    for name in list(_circuits.keys()):
        try:
            reset_circuit(name)
        except Exception as exc:
            logger.warning(
                "[CircuitBreakerAdmin] Failed to reset functional circuit '%s': %s", name, exc
            )
            failed.append(name)

    total = len(ALL_CIRCUITS) + len(_circuits)
    logger.warning(
        "[CircuitBreakerAdmin] Reset-all: %d circuits → CLOSED por user=%s",
        total, getattr(_user, "id", "admin"),
    )
    return {
        "action": "reset_all",
        "total_reset": total - len(failed),
        "new_state": "closed",
        **({"failed_circuits": failed} if failed else {}),
    }
