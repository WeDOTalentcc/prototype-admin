"""
Admin — Dead Letter Queue (DLQ) de tasks Celery.

Endpoints:
  GET    /api/v1/admin/dlq                              → resumo de todas as filas
  GET    /api/v1/admin/dlq/{queue}                      → entradas de uma fila
  POST   /api/v1/admin/dlq/{queue}/requeue/{entry_id}   → re-enfileira uma entry
  DELETE /api/v1/admin/dlq/{queue}                      → limpa fila

Acesso restrito a admins (require_admin).
"""
import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from pydantic import BaseModel

from app.auth.dependencies import require_admin
from app.shared.resilience.dlq_service import KNOWN_QUEUES, dlq_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin/dlq", tags=["admin-dlq"])


# ── schemas ───────────────────────────────────────────────────────────────────

class DLQEntry(BaseModel):
    entry_id: str
    task_name: str
    queue: str
    args: List[Any]
    kwargs: Dict[str, Any]
    exception_type: str
    exception_msg: str
    traceback: str
    retries: int
    company_id: Optional[str]
    failed_at: str


class DLQQueueSummary(BaseModel):
    queue: str
    entry_count: int


class DLQSummaryResponse(BaseModel):
    total_entries: int
    queues: Dict[str, int]


class RequeueResponse(BaseModel):
    success: bool
    entry_id: str
    queue: str
    message: str


class ClearResponse(BaseModel):
    queue: str
    entries_removed: int


# ── endpoints ─────────────────────────────────────────────────────────────────

@router.get("", response_model=DLQSummaryResponse)
async def get_dlq_summary(
    _: None = Depends(require_admin),
):
    """
    Resumo de todas as filas com entradas na DLQ.

    Retorna total de entradas e contagem por fila.
    Use para monitorar saúde dos workers Celery.
    """
    result = await dlq_service.summary()
    return DLQSummaryResponse(
        total_entries=result["total_entries"],
        queues=result["queues"],
    )


@router.get("/{queue}", response_model=List[DLQEntry])
async def list_dlq_entries(
    queue: str = Path(..., description="Nome da fila (ex: onboarding_low)"),
    limit: int = Query(50, ge=1, le=500, description="Máximo de entradas retornadas"),
    _: None = Depends(require_admin),
):
    """
    Lista as últimas N entradas da DLQ de uma fila.

    Entradas são ordenadas da mais recente para a mais antiga.
    """
    if queue not in KNOWN_QUEUES:
        raise HTTPException(
            status_code=404,
            detail=f"Fila '{queue}' desconhecida. Filas válidas: {KNOWN_QUEUES}",
        )
    entries = await dlq_service.list_entries(queue, limit=limit)
    return [DLQEntry(**e) for e in entries]


@router.post("/{queue}/requeue/{entry_id}", response_model=RequeueResponse)
async def requeue_entry(
    queue: str = Path(..., description="Nome da fila"),
    entry_id: str = Path(..., description="ID da entry a re-enfileirar"),
    _: None = Depends(require_admin),
):
    """
    Re-enfileira uma task da DLQ na fila original.

    A entry é removida da DLQ após o re-enfileiramento bem-sucedido.
    Use com cuidado: a task será executada novamente com os mesmos parâmetros.
    """
    if queue not in KNOWN_QUEUES:
        raise HTTPException(status_code=404, detail=f"Fila '{queue}' desconhecida.")

    success = await dlq_service.requeue(queue, entry_id)
    if not success:
        raise HTTPException(
            status_code=404,
            detail=f"Entry '{entry_id}' não encontrada na DLQ da fila '{queue}'.",
        )

    return RequeueResponse(
        success=True,
        entry_id=entry_id,
        queue=queue,
        message=f"Task re-enfileirada em '{queue}' com sucesso.",
    )


@router.delete("/{queue}", response_model=ClearResponse)
async def clear_dlq_queue(
    queue: str = Path(..., description="Nome da fila a limpar"),
    _: None = Depends(require_admin),
):
    """
    Remove todas as entradas da DLQ de uma fila.

    Ação irreversível — use somente após investigar e resolver a causa raiz.
    """
    if queue not in KNOWN_QUEUES:
        raise HTTPException(status_code=404, detail=f"Fila '{queue}' desconhecida.")

    removed = await dlq_service.clear(queue)
    return ClearResponse(queue=queue, entries_removed=removed)
