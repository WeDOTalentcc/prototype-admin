"""POST /lia/suggestions/click — record suggestion click event (P1-3 Fase 2).

Append-only logging. Fire-and-forget do frontend (não bloqueia UX).
Multi-tenancy fail-closed: company_id vem do JWT.
"""
import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user_or_demo
from app.auth.models import User
from app.core.database import get_db
from app.shared.security.require_company_id import require_company_id
from app.shared.types import WeDoBaseModel
from lia_models.suggestion_click_event import SUGGESTION_SOURCES

logger = logging.getLogger(__name__)

router = APIRouter()


class SuggestionClickRequest(WeDoBaseModel):
    """Request body para registrar clique em sugestão.

    REGRA 1: extra='forbid' herdado de WeDoBaseModel.
    REGRA 2: NUNCA company_id no payload (vem do JWT).
    """
    suggestion_id: str = Field(..., min_length=1, max_length=100)
    suggestion_text: str = Field(..., min_length=1, max_length=500)
    suggestion_source: str = Field(..., min_length=1, max_length=50)
    page_context: str | None = Field(None, max_length=100)
    chat_mode: str | None = Field(None, max_length=20)
    click_metadata: dict[str, Any] | None = Field(default_factory=dict)


class SuggestionClickResponse(WeDoBaseModel):
    id: str
    created_at: str


@router.post(
    "/suggestions/click",
    response_model=SuggestionClickResponse,
    status_code=status.HTTP_201_CREATED,
)
async def record_suggestion_click(
    payload: SuggestionClickRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo),
    company_id: str = Depends(require_company_id),
):
    """Registra clique em sugestão pra alimentar pipeline de aprendizado.

    Onda 4-Fase8 P1-3 Fase 2 (2026-05-24): canonical endpoint pra capturar
    cliques de ChatSuggestionsPanel, ChatWorkflowReels, settings_chips,
    PromptSuggestionsPanel. Fire-and-forget — frontend NÃO espera resposta
    pra continuar UX (failure silenciosa registrada no log do server).

    Fase 3 (próxima sprint): /lia/suggestions ranqueia baseado nesses cliques.
    """
    # Allowlist enforce — defense-in-depth ao constraint do DB
    if payload.suggestion_source not in SUGGESTION_SOURCES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid suggestion_source. Must be one of: {sorted(SUGGESTION_SOURCES)}",
        )

    # Lazy import pra evitar circular
    from app.repositories.suggestion_click_repository import (
        SuggestionClickRepository,
    )

    repo = SuggestionClickRepository(db)
    try:
        event = await repo.record_click(
            company_id=company_id,
            user_id=str(current_user.id),
            suggestion_id=payload.suggestion_id,
            suggestion_text=payload.suggestion_text,
            suggestion_source=payload.suggestion_source,
            page_context=payload.page_context,
            chat_mode=payload.chat_mode,
            click_metadata=payload.click_metadata,
        )
    except Exception as exc:
        # Fail-loud em log, mas response degrada graciosamente pro frontend
        # (fire-and-forget — UI não precisa do detail). REGRA 5: NÃO retornar
        # str(exc) ao client.
        logger.error(
            "suggestion_click record failed",
            extra={
                "company_id": company_id,
                "suggestion_id": payload.suggestion_id,
                "source": payload.suggestion_source,
                "error": str(exc),
            },
            exc_info=True,
        )
        raise HTTPException(
            status_code=500,
            detail="Failed to record click. Please retry.",
        ) from exc

    return SuggestionClickResponse(
        id=str(event.id),
        created_at=event.created_at.isoformat(),
    )
