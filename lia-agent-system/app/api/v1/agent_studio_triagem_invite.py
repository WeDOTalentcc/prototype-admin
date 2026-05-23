"""
Agent Studio Triagem Invite — Workstream A 2026-05-23.

REST canonical para 4o toggle per-agent. Diferente dos 3 canais diretos
(voice/voip/whatsapp), ``triagem_invite_enabled`` e CAPABILITY: quando ativo,
o agente pode CRIAR convites de triagem (token unico + URL publica
``/triagem/{token}``) que serao entregues ao candidato via email ou WhatsApp.

Endpoints
─────────
- PATCH /api/v1/agent-studio/agents/{agent_id}/triagem-invite/enabled
- POST  /api/v1/agent-studio/agents/{agent_id}/triagem-invite/initiate

Pattern de origem: agent_studio_voice.py (Sprint 3.7 W4-1) +
agent_studio_whatsapp.py (T5a) + agent_studio_channels.py (W-Channels-A).

Defesa em camadas
─────────────────
1. JWT (AuthEnforcementMiddleware) → company_id verificado.
2. require_company_id dependency → 400/401 explicito.
3. _load_agent_for_company → tenant isolation no SELECT.
4. CustomAgent.triagem_invite_enabled gate (HTTP 403 quando OFF).
5. TriagemSessionService.create_session canonical (NAO duplica logic).
6. AuditService.log_decision → trail LGPD/SOX-equiv.

Multi-tenancy canonical: ``company_id`` SEMPRE vem do JWT, NUNCA do payload
(REGRA 2 Pydantic Conventions). Refs ADR-LGPD-001 + REGRA ZERO.
"""
from __future__ import annotations

import logging
import os

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.core.database import get_tenant_db
from app.shared.security.require_company_id import require_company_id
from app.shared.types import WeDoBaseModel
from lia_models.custom_agent import CustomAgent

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/agent-studio/agents",
    tags=["Agent Studio Triagem Invite"],
)


# ───────────────────────── Pydantic schemas (extra='forbid') ─────────────────


class TriagemInviteEnableRequest(WeDoBaseModel):
    """Toggle ``triagem_invite_enabled`` flag on a custom agent.

    REGRA 2 canonical: ``company_id`` NAO aparece aqui — vem do JWT via
    ``require_company_id``.
    """

    triagem_invite_enabled: bool


class TriagemInviteEnableResponse(WeDoBaseModel):
    agent_id: str
    triagem_invite_enabled: bool


class TriagemInviteInitiateRequest(WeDoBaseModel):
    """Payload para criar convite de triagem para candidato via agente.

    Espelha InviteRequest em /api/v1/triagem/invite, mas sem company_id
    (canonical via JWT) — agente delega para TriagemSessionService.create_session.
    """

    candidate_id: str = Field(..., min_length=1)
    job_id: str = Field(..., min_length=1)
    candidate_name: str | None = None
    candidate_email: str | None = None
    job_title: str | None = Field(None, max_length=256)
    company_name: str | None = Field(None, max_length=256)
    company_logo_url: str | None = None
    invite_channel: str = Field(default="email", max_length=32)
    expires_days: int = Field(default=7, ge=1, le=90)
    voice_mode: bool = False


class TriagemInviteInitiateResponse(WeDoBaseModel):
    """Resposta canonical do initiate. ``status`` drives UI."""

    agent_id: str
    agent_name: str | None = None
    status: str = Field(
        ...,
        description=(
            "Um de: invite_created | agent_triagem_invite_disabled | error"
        ),
    )
    token: str | None = None
    expires_at: str | None = None
    invite_url: str | None = None
    triagem_url: str | None = None
    session_id: str | None = None


# ───────────────────────── helpers internos ──────────────────────────────────


async def _load_agent_for_company(
    db: AsyncSession, *, agent_id: str, company_id: str
) -> CustomAgent:
    """Load CustomAgent + 404 if not found in this tenant.

    Delega ao CustomAgentRepository canonical (ADR-001).
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


def _resolve_frontend_base_url() -> str:
    """Resolve FRONTEND_URL via env (canonical) com fallback seguro."""
    return os.getenv("FRONTEND_URL", "https://ai.wedotalent.cc").rstrip("/")


# ───────────────────────────── endpoints ─────────────────────────────────────


@router.patch(
    "/{agent_id}/triagem-invite/enabled",
    response_model=TriagemInviteEnableResponse,
    summary="Habilitar/desabilitar capability 'criar convite triagem' num custom agent",
)
async def set_agent_triagem_invite_enabled(
    agent_id: str,
    payload: TriagemInviteEnableRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_db),
    company_id: str = Depends(require_company_id),
) -> TriagemInviteEnableResponse:
    """Toggle ``triagem_invite_enabled`` on a custom agent.

    Audit canonical logged via :class:`AuditService.log_decision`.
    """
    agent = await _load_agent_for_company(db, agent_id=agent_id, company_id=company_id)

    previous_value = bool(
        getattr(agent, "triagem_invite_enabled", False)
    )
    new_value = bool(payload.triagem_invite_enabled)

    if previous_value != new_value:
        from app.domains.agent_studio.repositories.custom_agent_repository import (
            CustomAgentRepository,
        )
        repo = CustomAgentRepository(db)
        await repo.update_channel_flag(
            agent_id=agent_id,
            company_id=company_id,
            channel="triagem_invite",
            enabled=new_value,
        )

    # Audit (best-effort — does not fail the request if AuditService is down).
    try:
        from app.shared.compliance.audit_service import AuditService

        await AuditService().log_decision(
            company_id=company_id,
            agent_name="agent_studio_admin",
            decision_type="custom_agent_triagem_invite_toggled",
            action="triagem_invite_enabled_set" if new_value else "triagem_invite_disabled_set",
            decision="approved",
            reasoning=[
                f"agent_id={agent_id}",
                f"previous_value={previous_value}",
                f"new_value={new_value}",
            ],
            criteria_used=["admin_authorization", "per_agent_triagem_invite_flag"],
            criteria_ignored=[],
            actor_user_id=str(current_user.id) if current_user else None,
            human_review_required=False,
        )
    except Exception as audit_exc:  # pragma: no cover — best-effort
        logger.warning(
            "[agent_studio_triagem_invite] audit log failed (non-blocking): agent=%s err=%s",
            agent_id, audit_exc,
        )

    return TriagemInviteEnableResponse(
        agent_id=str(agent.id),
        triagem_invite_enabled=new_value,
    )


@router.post(
    "/{agent_id}/triagem-invite/initiate",
    response_model=TriagemInviteInitiateResponse,
    summary="Criar convite de triagem para candidato via custom agent",
)
async def initiate_triagem_invite(
    agent_id: str,
    payload: TriagemInviteInitiateRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_db),
    company_id: str = Depends(require_company_id),
) -> TriagemInviteInitiateResponse:
    """Agente cria convite triagem candidato.

    Gates:
    1. Tenant isolation via _load_agent_for_company.
    2. ``triagem_invite_enabled = True`` (HTTP 403 quando OFF).

    Delega para :class:`TriagemSessionService.create_session` canonical
    (NAO duplica logic de geracao de token, expiracao, schema).
    """
    agent = await _load_agent_for_company(db, agent_id=agent_id, company_id=company_id)

    if not bool(getattr(agent, "triagem_invite_enabled", False)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "agent_triagem_invite_disabled",
                "agent_id": agent_id,
                "message": "Agent nao tem capability 'convite triagem' habilitada.",
            },
        )

    from app.domains.recruitment.services.triagem_session_service import (
        get_triagem_service,
    )

    triagem_svc = get_triagem_service()

    try:
        session = await triagem_svc.create_session(
            db=db,
            candidate_id=payload.candidate_id,
            job_id=payload.job_id,
            company_id=company_id,
            candidate_name=payload.candidate_name,
            candidate_email=payload.candidate_email,
            job_title=payload.job_title,
            company_name=payload.company_name,
            company_logo_url=payload.company_logo_url,
            invite_channel=payload.invite_channel,
            created_by=str(current_user.id) if current_user else f"agent_{agent_id}",
            expires_days=payload.expires_days,
            voice_mode=payload.voice_mode,
        )
    except Exception as exc:  # pragma: no cover — safety net
        logger.error(
            "[agent_studio_triagem_invite] create_session failed: agent=%s company=%s err=%s",
            agent_id, company_id, exc,
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"error": "triagem_invite_failed", "agent_id": agent_id},
        ) from exc

    triagem_url = f"/triagem/{session.token}"
    invite_url = f"{_resolve_frontend_base_url()}/pt{triagem_url}"

    # Audit canonical (best-effort).
    try:
        from app.shared.compliance.audit_service import AuditService

        await AuditService().log_decision(
            company_id=company_id,
            agent_name=f"agent_{agent_id}",
            decision_type="triagem_invite_created_by_agent",
            action="invite_dispatched",
            decision="approved",
            reasoning=[
                f"agent_id={agent_id}",
                f"candidate_id={payload.candidate_id}",
                f"job_id={payload.job_id}",
                f"token={session.token}",
                f"channel={payload.invite_channel}",
            ],
            criteria_used=["triagem_invite_enabled", "tenant_isolation"],
            criteria_ignored=[],
            candidate_id=payload.candidate_id,
            actor_user_id=str(current_user.id) if current_user else None,
            human_review_required=False,
        )
    except Exception as audit_exc:  # pragma: no cover — best-effort
        logger.warning(
            "[agent_studio_triagem_invite] audit log failed (non-blocking): agent=%s err=%s",
            agent_id, audit_exc,
        )

    return TriagemInviteInitiateResponse(
        agent_id=str(agent.id),
        agent_name=agent.name,
        status="invite_created",
        token=session.token,
        expires_at=session.expires_at.isoformat() if getattr(session, "expires_at", None) else None,
        invite_url=invite_url,
        triagem_url=triagem_url,
        session_id=str(session.id) if getattr(session, "id", None) else None,
    )
