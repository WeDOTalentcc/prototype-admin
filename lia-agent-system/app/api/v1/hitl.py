"""
HITL (Human-In-The-Loop) API.

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
from app.shared.security.require_company_id import require_company_id
from app.shared.types import WeDoBaseModel
from typing import Annotated
from fastapi import Path
from app.api.v1._path_patterns import DUAL_ID_PATH_PATTERN, reorder_collection_before_item

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/hitl", tags=["hitl"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class ApprovalRequest(WeDoBaseModel):
    pending_id: str
    approved: bool
    comment: str | None = None


class HitlApprovalResponse(BaseModel):
    thread_id: str
    pending_id: str
    approved: bool
    comment: str | None
    timestamp: str


# Backward-compat alias for legacy contract tests (canonical name = HitlApprovalResponse)
ApprovalResponse = HitlApprovalResponse


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/{thread_id}/approve", response_model=HitlApprovalResponse)
async def approve_hitl_action(
    thread_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    body: ApprovalRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """
    Aprova ou rejeita uma ação pendente de agente HITL.

    O agente que está pausado aguardando aprovação será retomado após esta chamada.
    """
    try:
        # Onda 4.2d-P0-16 (2026-05-23): tenant guard via DB pre-check.
        # Antes user empresa A podia aprovar HITL pending de empresa B
        # (workflow IA continua execucao com aprovacao forjada — EU AI Act Art.14).
        from sqlalchemy import text as _text
        tenant_check = await db.execute(
            _text(
                "SELECT 1 FROM hitl_pending_actions "
                "WHERE pending_id = :pid AND company_id = :cid"
            ),
            {"pid": body.pending_id, "cid": company_id},
        )
        if not tenant_check.scalar():
            raise HTTPException(
                status_code=404,
                detail="HITL pending action not found",
            )

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

    return HitlApprovalResponse(
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
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
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
    thread_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    current_user: User = Depends(get_current_user),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Retorna a aprovação pendente mais recente para o thread, ou null."""
    try:
        pending = await hitl_service.get_pending(thread_id)
    except Exception as exc:
        logger.warning("[HITL] get_pending falhou thread=%s: %s", thread_id, exc)
        pending = None

    return {"thread_id": thread_id, "pending": pending}

reorder_collection_before_item(router)
