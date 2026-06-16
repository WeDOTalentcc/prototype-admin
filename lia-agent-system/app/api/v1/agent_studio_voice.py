"""
Agent Studio Voice Endpoints — Sprint 3.7 W4-1.

REST API canonical para o cliente final ativar voz num custom agent,
iniciar chamadas com candidatos, e consultar status / transcript.

Camadas de defesa
─────────────────
1. JWT (AuthEnforcementMiddleware) → company_id verificado.
2. require_company_id dependency → 400/401 explícito por endpoint.
3. CustomAgent.voice_enabled (per-agent toggle) → cliente controla via UI.
4. Feature flag voice_screening_v2_enabled (per-tenant) → WeDOTalent controla.
5. CustomAgentRuntime._invoke_voice → gates internos (PII, fairness, etc).

Endpoints
─────────
- POST   /api/v1/agent-studio/agents/{agent_id}/voice/initiate
- GET    /api/v1/agent-studio/agents/{agent_id}/voice/sessions/{session_id}
- PATCH  /api/v1/agent-studio/agents/{agent_id}/voice/enabled

Refs
────
- Sprint 3.5 (CustomAgentRuntime channel='voice')
- Sprint 3.6 (StudioVoicePlugin)
- ADR-LGPD-001 + REGRA ZERO multi-tenancy via JWT
"""
from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import Field
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
    tags=["Agent Studio Voice"],
)


# ───────────────────────── Pydantic schemas (extra='forbid') ─────────────────


class VoiceInitiateRequest(WeDoBaseModel):
    """Payload para iniciar chamada de voz com candidato."""

    candidate_id: str = Field(..., min_length=1)
    candidate_phone: str | None = Field(
        None,
        description="Telefone E.164 (ex: +5511999999999). Se ausente → sessão VoIP/browser.",
    )
    candidate_name: str | None = Field(None, max_length=256)
    job_id: str | None = None
    job_title: str | None = Field(None, max_length=256)
    language: str | None = Field(default="pt-BR", max_length=16)


class VoiceInitiateResponse(WeDoBaseModel):
    """Resposta canonical do initiate. Status drives UI."""

    session_id: str
    call_sid: str | None = None
    is_voip: bool = False
    status: str = Field(
        ...,
        description=(
            "Um de: session_initiated | feature_not_enabled | agent_voice_disabled | "
            "agent_voip_disabled | session_resumed | feature_check_failed | error"
        ),
    )
    agent_id: str
    agent_name: str | None = None
    plugin_name: str | None = None


class VoiceSessionStatusResponse(WeDoBaseModel):
    """Status atual da sessão (polling friendly)."""

    session_id: str
    status: str = Field(
        ...,
        description="ringing | in_progress | completed | failed | unknown",
    )
    duration_seconds: int = 0
    transcript_segments_count: int = 0
    summary: str | None = None
    has_transcript: bool = False


class VoiceEnableRequest(WeDoBaseModel):
    """Toggle voice_enabled flag on a custom agent."""

    voice_enabled: bool


class VoiceEnableResponse(WeDoBaseModel):
    """Resultado do toggle."""

    agent_id: str
    voice_enabled: bool


# ───────────────────────────── helpers internos ──────────────────────────────


async def _load_agent_for_company(
    db: AsyncSession, *, agent_id: str, company_id: str
) -> CustomAgent:
    """Load CustomAgent + 404 if not found in this tenant.

    C.5 (2026-05-23): delegates to canonical CustomAgentRepository
    (ADR-001 compliant). Previously had inline select(CustomAgent) under
    the legacy exempt marker — repository now consolidates the pattern.
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


# ─────────────────────────────── endpoints ───────────────────────────────────


@router.post(
    "/{agent_id}/voice/initiate",
    response_model=VoiceInitiateResponse,
    summary="Iniciar chamada de voz com candidato via custom agent",
)
async def initiate_voice_session(
    agent_id: str,
    payload: VoiceInitiateRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_db),
    company_id: str = Depends(require_company_id),
) -> VoiceInitiateResponse:
    """Bootstrap a voice session for a candidate.

    Defense layers (in order):
    1. JWT + ``require_company_id`` → tenant isolation.
    2. ``CustomAgent.voice_enabled`` → cliente UI flag.
    3. Feature flag ``voice_screening_v2_enabled`` (per-tenant, checado dentro
       de ``CustomAgentRuntime._invoke_voice``).
    """
    agent = await _load_agent_for_company(db, agent_id=agent_id, company_id=company_id)

    # Layer 2: per-agent toggle — mode-aware (W-Channels-A 2026-05-23).
    # candidate_phone presente → modo PSTN (gate voice_enabled).
    # candidate_phone ausente → modo VoIP (gate voip_enabled).
    _intended_voip = not bool(payload.candidate_phone)
    _required_flag = "voip_enabled" if _intended_voip else "voice_enabled"
    if not bool(getattr(agent, _required_flag, False)):
        return VoiceInitiateResponse(
            session_id="",
            call_sid=None,
            is_voip=_intended_voip,
            status="agent_voip_disabled" if _intended_voip else "agent_voice_disabled",
            agent_id=str(agent.id),
            agent_name=agent.name,
            plugin_name=None,
        )

    from app.domains.agent_studio.custom_agent_runtime import get_or_create_runtime

    persona_config = None
    if isinstance(agent.config, dict):
        persona_config = agent.config.get("persona")

    runtime = get_or_create_runtime(
        agent_id=str(agent.id),
        agent_name=agent.name,
        system_prompt=agent.system_prompt,
        allowed_tools=list(agent.allowed_tools or []),
        company_id=company_id,
        max_steps=agent.max_steps or 8,
        temperature=agent.temperature or 0.7,
        model_override=agent.model_override,
        enable_memory=bool(agent.enable_memory) if agent.enable_memory is not None else True,
        excluded_tools=list(agent.excluded_tools or []),
        context_level=agent.context_level or "full",
        description=agent.description,
        persona=persona_config,
    )

    runtime_context: dict[str, Any] = {
        "candidate_id": payload.candidate_id,
        "candidate_name": payload.candidate_name or "Candidato",
        "language": payload.language or "pt-BR",
    }
    if payload.candidate_phone:
        runtime_context["candidate_phone"] = payload.candidate_phone
    if payload.job_id:
        runtime_context["job_id"] = payload.job_id
    if payload.job_title:
        runtime_context["job_title"] = payload.job_title

    try:
        output = await runtime.execute(
            message="",
            user_id=str(current_user.id) if current_user else "system",
            company_id=company_id,
            session_id="",
            context=runtime_context,
            channel="voip" if _intended_voip else "voice",
        )
    except Exception as exc:  # pragma: no cover — safety net
        logger.error(
            "[agent_studio_voice] initiate failed: agent=%s company=%s err=%s",
            agent_id, company_id, exc,
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"error": "voice_initiate_failed", "agent_id": agent_id},
        ) from exc

    metadata = output.metadata if hasattr(output, "metadata") and output.metadata else {}
    return VoiceInitiateResponse(
        session_id=str(metadata.get("voice_session_id") or metadata.get("session_id") or ""),
        call_sid=metadata.get("call_sid"),
        is_voip=bool(metadata.get("is_voip", False)),
        status=str(metadata.get("status") or "error"),
        agent_id=str(agent.id),
        agent_name=agent.name,
        plugin_name=metadata.get("plugin_name"),
    )


@router.get(
    "/{agent_id}/voice/sessions/{session_id}",
    response_model=VoiceSessionStatusResponse,
    summary="Status atual de uma sessão de voz (polling friendly)",
)
async def get_voice_session_status(
    agent_id: str,
    session_id: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_db),
    company_id: str = Depends(require_company_id),
) -> VoiceSessionStatusResponse:
    """Read current session state. Returns 404 when expired (TTL ~4h)."""
    # 404 antes de tocar Redis — confirma que o agente é do tenant.
    await _load_agent_for_company(db, agent_id=agent_id, company_id=company_id)

    from app.domains.voice.repositories.voice_session_redis_repository import (
        get_voice_session_repository,
    )

    repo = get_voice_session_repository()
    state = await repo.load_session_state(
        company_id=company_id,
        session_id=session_id,
    )
    if state is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "session_not_found",
                "session_id": session_id,
                "hint": "Session may have expired (TTL ~4h) or never existed in this tenant.",
            },
        )

    transcript_segments = state.get("transcript_segments") or state.get("transcript") or []
    summary = state.get("summary") or state.get("final_summary")
    return VoiceSessionStatusResponse(
        session_id=session_id,
        status=str(state.get("status") or "unknown"),
        duration_seconds=int(state.get("duration_seconds") or 0),
        transcript_segments_count=len(transcript_segments)
        if isinstance(transcript_segments, list)
        else 0,
        summary=summary if isinstance(summary, str) else None,
        has_transcript=bool(transcript_segments),
    )


@router.patch(
    "/{agent_id}/voice/enabled",
    response_model=VoiceEnableResponse,
    summary="Habilitar/desabilitar voz num custom agent (per-agent flag)",
)
async def set_agent_voice_enabled(
    agent_id: str,
    payload: VoiceEnableRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_db),
    company_id: str = Depends(require_company_id),
) -> VoiceEnableResponse:
    """Toggle ``voice_enabled`` on a custom agent.

    Audit canonical logged via :class:`AuditService.log_decision`.
    """
    agent = await _load_agent_for_company(db, agent_id=agent_id, company_id=company_id)

    previous_value = bool(agent.voice_enabled) if agent.voice_enabled is not None else False
    new_value = bool(payload.voice_enabled)

    if previous_value != new_value:
        agent.voice_enabled = new_value
        await db.commit()
        await db.refresh(agent)

    # Audit (best-effort — does not fail the request if AuditService is down).
    try:
        from app.shared.compliance.audit_service import AuditService

        await AuditService().log_decision(
            company_id=company_id,
            agent_name="agent_studio_admin",
            decision_type="custom_agent_voice_toggled",
            action="voice_enabled_set" if new_value else "voice_disabled_set",
            decision="approved",
            reasoning=[
                f"agent_id={agent_id}",
                f"previous_value={previous_value}",
                f"new_value={new_value}",
            ],
            criteria_used=["admin_authorization", "per_agent_voice_flag"],
            criteria_ignored=[],
            actor_user_id=str(current_user.id) if current_user else None,
            human_review_required=False,
        )
    except Exception as audit_exc:  # pragma: no cover — best-effort
        logger.warning(
            "[agent_studio_voice] audit log failed (non-blocking): agent=%s err=%s",
            agent_id, audit_exc,
        )

    return VoiceEnableResponse(
        agent_id=str(agent.id),
        voice_enabled=new_value,
    )
