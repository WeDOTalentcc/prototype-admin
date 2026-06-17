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
from app.shared.errors import LIAInternalError

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_active_user
from app.auth.models import User
from app.core.database import get_db, get_tenant_db
from app.domains.persona.services import ai_persona_service
from app.domains.persona.services.ai_persona_validator import (
    CANONICAL_AI_TONES,
    NAME_MAX_LEN,
    NAME_MIN_LEN,
    RESERVED_BRAND_TOKENS,
    TONE_INSTRUCTIONS,
    TONE_UI_METADATA,
)
from app.shared.security.require_company_id import require_company_id
from app.domains.ai.services.context_aggregator_service import context_aggregator

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


class ToneOption(BaseModel):
    """Catálogo de tom canonical para renderização da UI.

    Tudo PT-BR — frontend renderiza direto sem mapping adicional. Audit
    2026-05-24 F3.2: substituiu TONE_OPTIONS hardcoded em AiPersonaPanel.
    Adicionar campo novo aqui exige sync com TONE_UI_METADATA no validator.
    """
    model_config = ConfigDict(extra="forbid")

    value: str = Field(..., description="Enum canonical PT-BR (CANONICAL_AI_TONES)")
    label_pt: str = Field(..., description="Rótulo curto pro cartão de seleção")
    short_pt: str = Field(..., description="Subtítulo de 1 linha")
    instruction: str = Field(..., description="Texto da instrução completa que vai pro system prompt")
    preview_message_pt: str = Field(..., description="Exemplo do que a IA escreveria PARA o candidato")
    preview_chat_pt: str = Field(..., description="Exemplo do que a IA escreveria no chat lateral")


class NameConstraints(BaseModel):
    """Constraints de nome que o frontend usa para validar inline antes
    de submeter. Backend re-valida no PUT (defense-in-depth)."""
    model_config = ConfigDict(extra="forbid")

    min_length: int = Field(..., description="Comprimento mínimo (após strip)")
    max_length: int = Field(..., description="Comprimento máximo (após strip)")
    blocked_brand_tokens: list[str] = Field(
        ...,
        description=(
            "Substrings case-insensitive bloqueadas (Claude, GPT, etc.). "
            "Frontend usa para warning inline antes do submit; backend "
            "rejeita com 422 se algum entrar."
        ),
    )


class AiPersonaOptionsResponse(BaseModel):
    """Catálogo completo retornado por GET /options.

    Single source of truth para o frontend renderizar a UI da tab
    "Personalidade da IA". Adicionar tom novo no validator (CANONICAL_AI_TONES
    + TONE_INSTRUCTIONS + TONE_UI_METADATA + TONE_PT_TO_EN_LEGACY) propaga
    automaticamente — zero deploy frontend.
    """
    model_config = ConfigDict(extra="forbid")

    tones: list[ToneOption]
    name_constraints: NameConstraints


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
    db: AsyncSession = Depends(get_tenant_db),
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
        context_aggregator.clear_cache(str(company_id))
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
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        logger.exception("[ai_persona] unexpected error updating persona")
        await db.rollback()
        raise LIAInternalError("Erro interno ao atualizar persona. Tente novamente.") from exc
    return AiPersonaResponse(**result)


@router.get(
    "/options",
    response_model=AiPersonaOptionsResponse,
    summary="Catálogo canonical de tons + constraints de nome (UI)",
)
async def get_ai_persona_options(
    _user: User = Depends(get_current_active_user),
) -> AiPersonaOptionsResponse:
    """Catálogo completo para a UI da tab "Personalidade da IA".

    NÃO é per-tenant — é catálogo WeDOTalent-wide (mesmas opções de tom +
    constraints de nome para toda a plataforma). Por isso exige apenas
    autenticação (get_current_active_user), NÃO company_id.

    V2.1 fix (2026-06-01): removido require_company_id — era exigência indevida
    num catálogo tenant-agnóstico e quebrava o carregamento dos tons ("Não foi
    possível carregar as opções de tom") em sessões cujo JWT não resolve
    company_id. get_current_active_user já barra acesso anônimo.

    Audit 2026-05-24 F3.2: criado para eliminar drift backend↔frontend
    causado por TONE_OPTIONS hardcoded em AiPersonaPanel.tsx.
    """
    tones = [
        ToneOption(
            value=tone,
            label_pt=TONE_UI_METADATA[tone]["label_pt"],
            short_pt=TONE_UI_METADATA[tone]["short_pt"],
            instruction=TONE_INSTRUCTIONS[tone],
            preview_message_pt=TONE_UI_METADATA[tone]["preview_message_pt"],
            preview_chat_pt=TONE_UI_METADATA[tone]["preview_chat_pt"],
        )
        # Ordem canonical (mesma de CANONICAL_AI_TONES, não alfabética),
        # para preservar a ordem visual atual dos cards no frontend.
        for tone in CANONICAL_AI_TONES
    ]
    return AiPersonaOptionsResponse(
        tones=tones,
        name_constraints=NameConstraints(
            min_length=NAME_MIN_LEN,
            max_length=NAME_MAX_LEN,
            blocked_brand_tokens=sorted(RESERVED_BRAND_TOKENS),
        ),
    )
