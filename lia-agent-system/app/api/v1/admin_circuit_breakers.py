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
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Path

from app.auth.dependencies import require_admin
from app.shared.resilience.circuit_breaker import (
    ALL_CIRCUITS,
    _circuits,
    get_all_circuit_stats,
    get_all_circuits_status,
    reset_all_circuits,
    reset_circuit,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin/circuit-breakers", tags=["Admin - Circuit Breakers"])


def _get_combined_status() -> Dict[str, Any]:
    """
    Combina status da instância de classes (ALL_CIRCUITS) e
    da instância funcional (_circuits) em um único dict.
    """
    class_stats = get_all_circuit_stats()
    functional_status = get_all_circuits_status()

    combined: Dict[str, Any] = {}

    # Instâncias baseadas em classe
    for name, stats in class_stats.items():
        combined[name] = {
            "implementation": "class",
            **stats,
        }

    # Instâncias funcionais (podem ter nomes diferentes)
    for name, status in functional_status.items():
        if name not in combined:
            combined[name] = {
                "implementation": "functional",
                **status,
            }

    return combined


@router.get("", summary="Status de todos os circuit breakers")
async def list_circuit_breakers(_user=Depends(require_admin)) -> Dict[str, Any]:
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
    except Exception as exc:
        logger.error("[CircuitBreakerAdmin] Erro ao listar circuits: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/{circuit_name}/reset", summary="Reset manual de um circuit breaker")
async def reset_circuit_breaker(
    circuit_name: str = Path(..., description="Nome do circuit breaker"),
    _user=Depends(require_admin),
) -> Dict[str, Any]:
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


@router.post("/reset-all", summary="Reset de todos os circuit breakers")
async def reset_all_circuit_breakers(_user=Depends(require_admin)) -> Dict[str, Any]:
    """
    Força CLOSED em todos os circuit breakers (classe + funcionais).

    Operação de emergência — usar apenas quando se tem certeza de que
    os serviços externos estão operacionais.
    """
    reset_all_circuits()  # instâncias de classe
    for name in list(_circuits.keys()):
        reset_circuit(name)

    total = len(ALL_CIRCUITS) + len(_circuits)
    logger.warning(
        "[CircuitBreakerAdmin] Reset-all: %d circuits → CLOSED por user=%s",
        total, getattr(_user, "id", "admin"),
    )
    return {"action": "reset_all", "total_reset": total, "new_state": "closed"}
