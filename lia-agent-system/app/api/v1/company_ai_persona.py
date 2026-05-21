"""
Endpoint REST canonical para tab "Personalidade da IA" em Minha Empresa.

Registrado 2026-05-21 (E2.2). Surface mínima e estável:

  GET  /api/v1/company-ai-persona       → ler {name, tone} (sempre 200)
  PUT  /api/v1/company-ai-persona       → atualizar {name?, tone?} (200/422)

Diferente dos endpoints de tenant override (que exigem
``require_wedotalent_admin``), estes são consumidos pelo CLIENTE FINAL
(qualquer recrutador autenticado). Por isso o gate é
``require_company_id`` apenas (multi-tenancy via JWT).

## Por que NÃO usar o endpoint genérico de hiring-policy

``PATCH /api/v1/company-hiring-policy/{cid}/block`` existe e aceita
mutações arbitrárias em ``communication_rules`` — incluindo
``ai_persona``. Mas:

1. Não passa pelo validator canonical (cliente pode persistir nome
   inválido, ou tone fora do enum).
2. Não emite audit log com ``action='ai_persona_update'`` (perde
   trail dedicado).
3. UI teria que conhecer o shape interno de ``communication_rules`` —
   acoplamento desnecessário.

Endpoint dedicado é DRY + canonical fix: cliente envia ``{name, tone}``,
backend valida + persiste + audita atomicamente.
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_active_user
from app.auth.models import User
from app.core.database import get_db
from app.domains.persona.services import ai_persona_service
from app.shared.security.require_company_id import require_company_id

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/company-ai-persona", tags=["company-ai-persona"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class AiPersonaResponse(BaseModel):
    """Shape canonical retornado por GET e PUT.

    ``name``: nome atual da IA pro tenant (default ``"LIA"`` quando não
    customizado).
    ``tone``: tone canonical (um dos seis em ``CANONICAL_AI_TONES``).
    """
    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., min_length=1, max_length=20)
    tone: str = Field(..., min_length=1, max_length=32)


class AiPersonaUpdateRequest(BaseModel):
    """Body do PUT. Ambos campos opcionais — caller envia só o que muda.

    Se ambos forem ``None``, validator rejeita com ``code='no_change_requested'``.
    """
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, max_length=64,
                             description="Novo nome (2-20 chars). Omita para não alterar.")
    tone: str | None = Field(default=None, max_length=32,
                             description="Tone canonical. Omita para não alterar.")


# ---------------------------------------------------------------------------
# Handlers
# ---------------------------------------------------------------------------

@router.get(
    "",
    response_model=AiPersonaResponse,
    summary="Lê persona AI atual do tenant",
)
async def get_company_ai_persona(
    company_id: str = Depends(require_company_id),
    _user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> AiPersonaResponse:
    """Sempre retorna 200. Se tenant ainda não customizou, retorna defaults
    canonical (``LIA`` / ``profissional``).
    """
    persona = await ai_persona_service.get_ai_persona(company_id, db)
    return AiPersonaResponse(**persona)


@router.put(
    "",
    response_model=AiPersonaResponse,
    summary="Atualiza persona AI do tenant (validador-gated)",
)
async def update_company_ai_persona(
    payload: AiPersonaUpdateRequest,
    company_id: str = Depends(require_company_id),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> AiPersonaResponse:
    """Valida + persiste + audita atomicamente.

    Errors de validação retornam 422 com ``detail.errors`` (lista de
    ``{code, message, fix}``) — UI renderiza inline. Tudo o mais é 500
    com mensagem genérica (audit captura traceback).
    """
    try:
        result = await ai_persona_service.update_ai_persona(
            company_id, db,
            name=payload.name,
            tone=payload.tone,
            actor_user_id=str(current_user.id) if current_user else None,
        )
        await db.commit()
    except ValueError as val_exc:
        # Validator rejected — return structured errors for UI.
        errors = val_exc.args[0] if val_exc.args else []
        await db.rollback()
        raise HTTPException(
            status_code=422,
            detail={
                "code": "ai_persona_validation_failed",
                "message": "Não foi possível atualizar a persona da IA.",
                "errors": errors,
            },
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception("[ai_persona] unexpected error updating persona")
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Erro interno ao atualizar persona. Tente novamente.",
        ) from exc
    return AiPersonaResponse(**result)
