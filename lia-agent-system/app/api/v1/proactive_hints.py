"""WT-2022 Camada IA Proativa: REST endpoint para hints scheduler-driven.

Diferenciacao de /api/v1/proactive-actions (que existe ha mais tempo):
- /proactive-actions: actions candidato/vaga-especificas + insights de pipeline
- /proactive-hints (este): hints ENVIRONMENTAIS detectados por
  ProactiveDetectorService (profile incompleto, DSR overdue, etc).

Os dois compartilham a tabela proactive_actions, mas filtramos por
trigger_reason que comeca com nome de detector + suggested_action.source =
"proactive_detector_scheduler".

Endpoints:
- GET  /api/v1/proactive-hints/      -> lista hints PENDING para a company auth
- POST /api/v1/proactive-hints/{hint_id}/dismiss -> marca como REJECTED

Multi-tenancy: SEMPRE via JWT (Depends(require_company_id)). Nunca aceita
company_id no payload (REGRA 2 de Pydantic Conventions canonical).
"""
from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import and_, select

from app.shared.security.require_company_id import require_company_id

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/proactive-hints", tags=["Proactive Hints"])


class ProactiveHintResponse(BaseModel):
    id: str
    detector: str
    title: str
    message: str
    severity: str
    action: str | None
    action_params: dict[str, Any] = {}
    related_job_id: str | None = None
    related_candidate_id: str | None = None
    created_at: str | None = None
    expires_at: str | None = None


class HintListResponse(BaseModel):
    hints: list[ProactiveHintResponse]
    count: int


class DismissResponse(BaseModel):
    success: bool
    hint_id: str


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

# Maps ActionPriority -> severity exposto na API (mantem compat com hook
# frontend que ja existe com "low|medium|high|critical").
_PRIORITY_TO_SEVERITY = {
    "low": "low",
    "normal": "medium",
    "high": "high",
    "urgent": "critical",
}


def _hint_to_response(action) -> ProactiveHintResponse:
    suggested = action.suggested_action or {}
    return ProactiveHintResponse(
        id=str(action.id),
        detector=action.trigger_reason or "unknown",
        title=action.title or "",
        message=action.description or "",
        severity=_PRIORITY_TO_SEVERITY.get(action.priority, "medium"),
        action=suggested.get("action"),
        action_params=suggested.get("action_params") or {},
        related_job_id=str(action.related_job_id) if action.related_job_id else None,
        related_candidate_id=(
            str(action.related_candidate_id)
            if action.related_candidate_id
            else None
        ),
        created_at=action.created_at.isoformat() if action.created_at else None,
        expires_at=action.expires_at.isoformat() if action.expires_at else None,
    )


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@router.get("/", response_model=HintListResponse)
async def list_active_hints(
    company_id: str = Depends(require_company_id),
) -> HintListResponse:
    """Lista hints PENDING (scheduler-driven) para a company autenticada."""
    from app.core.database import AsyncSessionLocal
    from lia_models.background_jobs import (
        ActionStatus,
        ProactiveAction,
    )

    try:
        company_uuid = UUID(company_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid company_id") from exc

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(ProactiveAction).where(
                and_(
                    ProactiveAction.company_id == company_uuid,
                    ProactiveAction.status == ActionStatus.PENDING.value,
                )
            ).order_by(
                ProactiveAction.priority.desc(),
                ProactiveAction.created_at.desc(),
            ).limit(50)
        )
        rows = list(result.scalars().all())

    # Filter: somente hints originarios do scheduler (source marker).
    scheduler_hints = [
        action
        for action in rows
        if (action.suggested_action or {}).get("source")
        == "proactive_detector_scheduler"
    ]

    hints = [_hint_to_response(action) for action in scheduler_hints]
    return HintListResponse(hints=hints, count=len(hints))


@router.post("/{hint_id}/dismiss", response_model=DismissResponse)
async def dismiss_hint(
    hint_id: str,
    company_id: str = Depends(require_company_id),
) -> DismissResponse:
    """Marca hint como REJECTED. company_id no JWT garante cross-tenant safety."""
    from datetime import datetime

    from app.core.database import AsyncSessionLocal
    from lia_models.background_jobs import (
        ActionStatus,
        ProactiveAction,
    )

    try:
        hint_uuid = UUID(hint_id)
        company_uuid = UUID(company_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid UUID") from exc

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(ProactiveAction).where(
                and_(
                    ProactiveAction.id == hint_uuid,
                    ProactiveAction.company_id == company_uuid,
                )
            ).limit(1)
        )
        action = result.scalars().first()
        if action is None:
            raise HTTPException(status_code=404, detail="Hint not found")

        action.status = ActionStatus.REJECTED.value
        action.accepted_at = datetime.utcnow()
        await db.commit()

    return DismissResponse(success=True, hint_id=hint_id)


__all__ = ["router"]
