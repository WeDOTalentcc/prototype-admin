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
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from pydantic import BaseModel

from app.auth.dependencies import require_admin
from app.shared.resilience.dlq_service import KNOWN_QUEUES, dlq_service
from app.shared.security.require_company_id import require_company_id
from app.api.v1._path_patterns import DUAL_ID_PATH_PATTERN, reorder_collection_before_item

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin/dlq", tags=["admin-dlq"])


# ── schemas ───────────────────────────────────────────────────────────────────

class DLQEntry(BaseModel):
    entry_id: str
    task_name: str
    queue: str
    args: list[Any]
    kwargs: dict[str, Any]
    exception_type: str
    exception_msg: str
    traceback: str
    retries: int
    company_id: str | None
    failed_at: str


class DLQQueueSummary(BaseModel):
    queue: str
    entry_count: int


class DLQSummaryResponse(BaseModel):
    total_entries: int
    queues: dict[str, int]


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
company_id: str = Depends(require_company_id)):
    # multi-tenancy: admin/platform-level (admin_) — role-based access required
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


@router.get("/{queue}", response_model=list[DLQEntry])
async def list_dlq_entries(
    queue: str = Path(..., description="Nome da fila (ex: onboarding_low)"),
    limit: int = Query(50, ge=1, le=500, description="Máximo de entradas retornadas"),
    _: None = Depends(require_admin),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: admin/platform-level (admin_) — role-based access required
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
    return [DLQEntry.model_validate(e) for e in entries]


@router.post("/{queue}/requeue/{entry_id}", response_model=RequeueResponse)
async def requeue_entry(
    queue: str = Path(..., description="Nome da fila"),
    entry_id: str = Path(..., description="ID da entry a re-enfileirar", pattern=DUAL_ID_PATH_PATTERN),
    _: None = Depends(require_admin),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: admin/platform-level (admin_) — role-based access required
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
company_id: str = Depends(require_company_id)):
    # multi-tenancy: admin/platform-level (admin_) — role-based access required
    """
    Remove todas as entradas da DLQ de uma fila.

    Ação irreversível — use somente após investigar e resolver a causa raiz.
    """
    if queue not in KNOWN_QUEUES:
        raise HTTPException(status_code=404, detail=f"Fila '{queue}' desconhecida.")

    removed = await dlq_service.clear(queue)
    return ClearResponse(queue=queue, entries_removed=removed)

reorder_collection_before_item(router)
