"""Sprint 3.2 — POST /api/v1/lia/proactive-context endpoint.

Frontend (settings-notify.ts debounced 1500ms) chama esse endpoint após
dispatch do CustomEvent `lia:settings-updated`. Persiste em Redis via
ProactiveContextStore com TTL 30min.

MainOrchestrator.process (Sprint 3.4) lê via list_recent() ao construir
o system_prompt e inclui o contexto recente, permitindo que LIA reaja
proativamente ("Vi que você ajustou X. Quer validar Y?") no próximo turn.

Multi-tenancy canonical: company_id via JWT (require_company_id), nunca
via payload. Schema WeDoBaseModel com extra='forbid'.
"""
from __future__ import annotations

import logging
import time

from fastapi import APIRouter, Depends
from pydantic import Field

from app.auth.dependencies import get_current_user_or_demo
from app.auth.models import User
from app.shared.security.require_company_id import require_company_id
from app.shared.services.proactive_context_store import ProactiveContextStore
from app.shared.types import WeDoBaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/lia/proactive-context", tags=["lia-proactive-context"])


class ProactiveContextNoteInput(WeDoBaseModel):
    """Input do POST. Mirror de SettingsUpdateDetail (frontend
    settings-notify.ts) sem campos derivados (source/ts vêm do servidor)."""
    actionId: str = Field(..., min_length=1, max_length=128)
    section: str = Field(..., min_length=1, max_length=64)
    field: str | None = Field(default=None, max_length=128)
    value: object | None = Field(default=None)


class ProactiveContextNoteResponse(WeDoBaseModel):
    """Output canonical. ok=False se Redis indisponível (fail-open client-side)."""
    ok: bool
    stored: bool


@router.post("", response_model=ProactiveContextNoteResponse)
async def post_proactive_context(
    payload: ProactiveContextNoteInput,
    current_user: User = Depends(get_current_user_or_demo),
    company_id: str = Depends(require_company_id),
) -> ProactiveContextNoteResponse:
    """Persiste 1 proactive context note no Redis (TTL 30min).

    Sprint 3 G9 wire (2026-05-26). Chamado por frontend quando user
    edita Configurações; backend MainOrchestrator próximo turn lê e
    inclui em system_prompt pra LIA reagir proativamente.

    Fail-open: Redis down → response {ok: False, stored: False}. Cliente
    não precisa retry (UX local com debounce já é resiliente).
    """
    user_id = str(current_user.id)
    stored = await ProactiveContextStore.put(
        company_id=company_id,
        user_id=user_id,
        action_id=payload.actionId,
        section=payload.section,
        field=payload.field,
        value=payload.value,
        ts_ms=int(time.time() * 1000),
    )
    if not stored:
        logger.debug(
            "[ProactiveContext] put returned False (Redis fail-open) "
            "company=%s user=%s action=%s section=%s",
            company_id, user_id, payload.actionId, payload.section,
        )
    return ProactiveContextNoteResponse(ok=True, stored=stored)
