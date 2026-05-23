"""
Agent Studio Channel Toggles — W-Channels-A (2026-05-23).

REST canonical para o canal voip novo do mental model Paulo
(Opção B revisada 2026-05-23):

- ``voip_enabled``    — voz no navegador (Twilio VoIP SDK + Gemini Live)

Nota: ``in_app_enabled`` foi REVERTIDO (gap conceitual — audit
AUDIT_CANDIDATE_CHAT_PUBLIC_2026-05-23.md). Chat candidato público
canonical é /api/v1/triagem/ (handler dedicado).

Os outros dois canais já têm endpoints próprios:
- ``voice_enabled``   → app/api/v1/agent_studio_voice.py (PATCH /voice/enabled)
- ``whatsapp_enabled``→ app/api/v1/agent_studio_whatsapp.py (PATCH /whatsapp/enabled)

Espelha o pattern de ``agent_studio_voice.py`` (Sprint 3.7 W4-1) e
``agent_studio_whatsapp.py`` (T5a). Mesma defesa em camadas:

1. JWT (AuthEnforcementMiddleware) → company_id verificado.
2. require_company_id dependency → 400/401 explícito.
3. _load_agent_for_company → tenant isolation no SELECT.
4. AuditService.log_decision → trail LGPD/SOX-equiv.

Multi-tenancy canonical: ``company_id`` SEMPRE vem do JWT, NUNCA do payload
(REGRA 2 Pydantic Conventions canonical).

Refs
────
- W-Channels-A (Workstream A — Coerência canais Opção B, Paulo 2026-05-23)
- agent_studio_voice.py / agent_studio_whatsapp.py (pattern de origem)
- ADR-LGPD-001 + REGRA ZERO multi-tenancy via JWT
"""
from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.core.database import get_tenant_db
from app.shared.security.require_company_id import require_company_id
from app.shared.types import WeDoBaseModel
from lia_models.custom_agent import CustomAgent

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/agent-studio/agents",
    tags=["Agent Studio Channels"],
)


# ───────────────────────── Pydantic schemas (extra='forbid') ─────────────────


class VoipEnableRequest(WeDoBaseModel):
    """Toggle ``voip_enabled`` flag on a custom agent.

    REGRA 2 canonical: ``company_id`` NÃO aparece aqui — vem do JWT via
    ``require_company_id``.
    """

    voip_enabled: bool


class VoipEnableResponse(WeDoBaseModel):
    agent_id: str
    voip_enabled: bool


# ───────────────────────── Helpers ───────────────────────────────────────────


async def _load_agent_for_company(
    db: AsyncSession,
    *,
    agent_id: str,
    company_id: str,
) -> CustomAgent:
    """Fetch a custom agent scoped to ``company_id`` (multi-tenancy fail-closed).

    C.5 (2026-05-23): delegates to canonical CustomAgentRepository
    (ADR-001 compliant). Previously had local copy of `select(CustomAgent)`
    inline (mirror of voice/whatsapp endpoints) — repository consolidates
    the 3 sites now.
    """
    from app.domains.agent_studio.repositories.custom_agent_repository import (
        CustomAgentRepository,
    )
    repo = CustomAgentRepository(db)
    agent = await repo.get_by_id(agent_id=agent_id, company_id=company_id)
    if agent is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "agent_not_found", "agent_id": agent_id},
        )
    return agent


async def _audit_channel_toggle(
    *,
    company_id: str,
    agent_id: str,
    channel: str,
    previous_value: bool,
    new_value: bool,
    actor_user_id: str | None,
) -> None:
    """Best-effort audit log. Espelha o pattern dos outros 2 endpoints."""
    try:
        from app.shared.compliance.audit_service import AuditService

        await AuditService().log_decision(
            company_id=company_id,
            agent_name="agent_studio_admin",
            decision_type=f"custom_agent_{channel}_toggled",
            action=f"{channel}_enabled_set" if new_value else f"{channel}_disabled_set",
            decision="approved",
            reasoning=[
                f"agent_id={agent_id}",
                f"channel={channel}",
                f"previous_value={previous_value}",
                f"new_value={new_value}",
            ],
            criteria_used=["admin_authorization", f"per_agent_{channel}_flag"],
            criteria_ignored=[],
            actor_user_id=actor_user_id,
            human_review_required=False,
        )
    except Exception as audit_exc:  # pragma: no cover — best-effort
        logger.warning(
            "[agent_studio_channels] audit log failed (non-blocking): agent=%s channel=%s err=%s",
            agent_id, channel, audit_exc,
        )


# ───────────────────────── Endpoints ─────────────────────────────────────────


@router.patch(
    "/{agent_id}/voip/enabled",
    response_model=VoipEnableResponse,
    summary="Habilitar/desabilitar voz no navegador (VoIP) num custom agent",
)
async def set_agent_voip_enabled(
    agent_id: str,
    payload: VoipEnableRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_db),
    company_id: str = Depends(require_company_id),
) -> VoipEnableResponse:
    """Toggle ``voip_enabled`` on a custom agent.

    Independente de ``voice_enabled``: cliente pode habilitar PSTN sem VoIP
    e vice-versa. Audit canonical via :class:`AuditService.log_decision`.
    """
    agent = await _load_agent_for_company(db, agent_id=agent_id, company_id=company_id)

    previous_value = bool(getattr(agent, "voip_enabled", False))
    new_value = bool(payload.voip_enabled)

    if previous_value != new_value:
        agent.voip_enabled = new_value
        await db.commit()
        await db.refresh(agent)

    await _audit_channel_toggle(
        company_id=company_id,
        agent_id=agent_id,
        channel="voip",
        previous_value=previous_value,
        new_value=new_value,
        actor_user_id=str(current_user.id) if current_user else None,
    )

    return VoipEnableResponse(
        agent_id=str(agent.id),
        voip_enabled=new_value,
    )


