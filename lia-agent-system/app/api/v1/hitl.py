"""
HITL API — Human-in-the-Loop endpoints (André P9).

Permite que o frontend aprove ou rejeite ações pendentes de agentes.

POST /api/v1/hitl/{thread_id}/approve
"""
import logging
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.core.database import get_db
from app.domains.cv_screening.services.hitl_service import hitl_service
from app.api.v1._path_patterns import DUAL_ID_PATH_PATTERN
from typing import Annotated
from fastapi import Path

# Task #489 — UUID-or-digit constraint for dual-ID path params,
# preventing static sibling routes from being shadowed by
# item handlers (Task #455-class bug).
_DualId = Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)]

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/hitl", tags=["hitl"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class ApprovalRequest(BaseModel):
    pending_id: str
    approved: bool
    comment: str | None = None


class ApprovalResponse(BaseModel):
    thread_id: str
    pending_id: str
    approved: bool
    comment: str | None
    timestamp: str


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/{thread_id}/approve", response_model=ApprovalResponse)
async def approve_hitl_action(
    thread_id: _DualId,
    body: ApprovalRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Aprova ou rejeita uma ação pendente de agente HITL.

    O agente que está pausado aguardando aprovação será retomado após esta chamada.
    """
    try:
        await hitl_service.receive_approval(
            thread_id=thread_id,
            pending_id=body.pending_id,
            approved=body.approved,
            comment=body.comment,
        )
    except Exception as exc:
        logger.error("[HITL] Erro ao processar aprovação thread=%s: %s", thread_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao processar aprovação.",
        )

    logger.info(
        "[HITL] Aprovação via API user=%s thread=%s pending=%s approved=%s",
        current_user.id if hasattr(current_user, "id") else "unknown",
        thread_id,
        body.pending_id,
        body.approved,
    )

    return ApprovalResponse(
        thread_id=thread_id,
        pending_id=body.pending_id,
        approved=body.approved,
        comment=body.comment,
        timestamp=datetime.now(UTC).isoformat(),
    )


@router.get("/pending", response_model=None)
async def get_all_pending_approvals(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retorna todas as aprovações pendentes para a empresa do usuário autenticado."""
    company_id = getattr(current_user, "company_id", "") or ""
    if not company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuário sem empresa associada.",
        )

    # Reaproveita a sessão do request (evita esgotar pool em concorrência).
    # Exceções do service sobem para o handler global — não mascarar 500 como [].
    pending_list = await hitl_service.get_all_pending_by_company(company_id, db=db)

    return {
        "pending": pending_list,
        "count": len(pending_list),
    }


@router.get("/{thread_id}/pending", response_model=None)
async def get_pending_approval(
    thread_id: _DualId,
    current_user: User = Depends(get_current_user),
):
    """Retorna a aprovação pendente mais recente para o thread, ou null."""
    try:
        pending = await hitl_service.get_pending(thread_id)
    except Exception as exc:
        logger.warning("[HITL] get_pending falhou thread=%s: %s", thread_id, exc)
        pending = None

    return {"thread_id": thread_id, "pending": pending}

# Task #489 — Keep collection-scoped routes ahead of item-scoped
# routes so a static sibling segment cannot be silently shadowed
# by an {*_id} handler (the Task #455 routing-shadowing bug).
from app.api.v1._path_patterns import reorder_collection_before_item as _reorder_collection_before_item  # noqa: E402

_reorder_collection_before_item(router)
