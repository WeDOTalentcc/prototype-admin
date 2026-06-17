"""
Agent Studio WhatsApp Endpoints — T5a UX Transformação 5 (audit 2026-05-23).

REST API canonical para o cliente final ativar WhatsApp num custom agent,
iniciar conversas com candidatos via WhatsApp, e consultar status.

Espelha o pattern de ``agent_studio_voice.py`` (Sprint 3.7 W4-1) com
adaptações para a semântica message-driven do WhatsApp (vs streaming
bidirectional de voice).

Camadas de defesa
─────────────────
1. JWT (AuthEnforcementMiddleware) → company_id verificado.
2. require_company_id dependency → 400/401 explícito por endpoint.
3. CustomAgent.whatsapp_enabled (per-agent toggle) → cliente controla via UI.
4. WhatsAppProviderFactory.get_provider → Meta ou Twilio devem estar configurados.
5. CustomAgentRuntime._invoke_whatsapp → gates internos (PII, fairness).

Endpoints
─────────
- POST   /api/v1/agent-studio/agents/{agent_id}/whatsapp/initiate
- PATCH  /api/v1/agent-studio/agents/{agent_id}/whatsapp/enabled

Refs
────
- T5a (UX_AUDIT_ESTUDIO_AGENTES_2026-05-21.md §4.5 Transformação 5)
- Sprint 3.7 W4-1 (voice endpoint pattern)
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
    tags=["Agent Studio WhatsApp"],
)


# ───────────────────────── Pydantic schemas (extra='forbid') ─────────────────


class WhatsAppInitiateRequest(WeDoBaseModel):
    """Payload para iniciar conversa WhatsApp com candidato.

    REGRA 2 canonical: ``company_id`` NÃO aparece aqui — vem do JWT via
    ``require_company_id``.
    """

    candidate_id: str = Field(..., min_length=1)
    candidate_phone: str = Field(
        ...,
        min_length=8,
        max_length=20,
        description="Telefone E.164 (ex: +5511999999999). Required para WhatsApp.",
    )
    candidate_name: str | None = Field(None, max_length=256)
    message: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="Mensagem inicial do recrutador (será processada pelo agente custom).",
    )
    job_id: str | None = None
    job_title: str | None = Field(None, max_length=256)
    session_id: str | None = Field(
        None,
        description="ID de sessão para continuação (opcional).",
    )


class WhatsAppInitiateResponse(WeDoBaseModel):
    """Resposta canonical do initiate. Status drives UI."""

    agent_id: str
    agent_name: str | None = None
    plugin_name: str | None = None
    status: str = Field(
        ...,
        description=(
            "Um de: message_sent | send_failed | agent_whatsapp_disabled | "
            "whatsapp_missing_company_id | whatsapp_missing_sender_phone | "
            "whatsapp_empty_message | error"
        ),
    )
    response_text: str | None = None
    delivery_status: str | None = None
    delivery_message_id: str | None = None
    delivery_error: str | None = None
    session_id: str | None = None


class WhatsAppEnableRequest(WeDoBaseModel):
    """Toggle whatsapp_enabled flag on a custom agent."""

    whatsapp_enabled: bool


class WhatsAppEnableResponse(WeDoBaseModel):
    """Resultado do toggle."""

    agent_id: str
    whatsapp_enabled: bool


# ───────────────────────────── helpers internos ──────────────────────────────


async def _load_agent_for_company(
    db: AsyncSession, *, agent_id: str, company_id: str
) -> CustomAgent:
    """Load CustomAgent + 404 if not found in this tenant.

    C.5 (2026-05-23): delegates to canonical CustomAgentRepository
    (ADR-001 compliant). Previously had inline select(CustomAgent) under
    the legacy exempt marker.
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
    "/{agent_id}/whatsapp/initiate",
    response_model=WhatsAppInitiateResponse,
    summary="Iniciar conversa WhatsApp com candidato via custom agent",
)
async def initiate_whatsapp_conversation(
    agent_id: str,
    payload: WhatsAppInitiateRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_db),
    company_id: str = Depends(require_company_id),
) -> WhatsAppInitiateResponse:
    """Send a WhatsApp message to a candidate through the custom agent.

    Defense layers (in order):
    1. JWT + ``require_company_id`` → tenant isolation.
    2. ``CustomAgent.whatsapp_enabled`` → cliente UI flag.
    3. ``WhatsAppProviderFactory.get_provider`` → Meta/Twilio configurados
       (checado dentro de ``WhatsAppChannelAdapter.send``).
    4. ``CustomAgentRuntime._invoke_whatsapp`` → channel handler completo.
    """
    agent = await _load_agent_for_company(db, agent_id=agent_id, company_id=company_id)

    # Layer 2: per-agent toggle.
    if not bool(getattr(agent, "whatsapp_enabled", False)):
        return WhatsAppInitiateResponse(
            agent_id=str(agent.id),
            agent_name=agent.name,
            plugin_name=None,
            status="agent_whatsapp_disabled",
            response_text=None,
            delivery_status=None,
            delivery_message_id=None,
            delivery_error=None,
            session_id=payload.session_id,
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
        "candidate_phone": payload.candidate_phone,
    }
    if payload.job_id:
        runtime_context["job_id"] = payload.job_id
    if payload.job_title:
        runtime_context["job_title"] = payload.job_title

    try:
        output = await runtime.execute(
            message=payload.message,
            user_id=str(current_user.id) if current_user else "system",
            company_id=company_id,
            session_id=payload.session_id or "",
            context=runtime_context,
            channel="whatsapp",
            sender_phone=payload.candidate_phone,
            db=db,
        )
    except Exception as exc:  # pragma: no cover — safety net
        logger.error(
            "[agent_studio_whatsapp] initiate failed: agent=%s company=%s err=%s",
            agent_id, company_id, exc,
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"error": "whatsapp_initiate_failed", "agent_id": agent_id},
        ) from exc

    metadata = output.metadata if hasattr(output, "metadata") and output.metadata else {}
    return WhatsAppInitiateResponse(
        agent_id=str(agent.id),
        agent_name=agent.name,
        plugin_name=metadata.get("plugin_name"),
        status=str(metadata.get("status") or "error"),
        response_text=metadata.get("response_text"),
        delivery_status=metadata.get("delivery_status"),
        delivery_message_id=metadata.get("delivery_message_id"),
        delivery_error=metadata.get("delivery_error"),
        session_id=metadata.get("session_id") or payload.session_id,
    )


@router.patch(
    "/{agent_id}/whatsapp/enabled",
    response_model=WhatsAppEnableResponse,
    summary="Habilitar/desabilitar WhatsApp num custom agent (per-agent flag)",
)
async def set_agent_whatsapp_enabled(
    agent_id: str,
    payload: WhatsAppEnableRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_db),
    company_id: str = Depends(require_company_id),
) -> WhatsAppEnableResponse:
    """Toggle ``whatsapp_enabled`` on a custom agent.

    Audit canonical logged via :class:`AuditService.log_decision`.
    """
    agent = await _load_agent_for_company(db, agent_id=agent_id, company_id=company_id)

    previous_value = bool(agent.whatsapp_enabled) if agent.whatsapp_enabled is not None else False
    new_value = bool(payload.whatsapp_enabled)

    if previous_value != new_value:
        agent.whatsapp_enabled = new_value
        await db.commit()
        await db.refresh(agent)

    # Audit (best-effort — does not fail the request if AuditService is down).
    try:
        from app.shared.compliance.audit_service import AuditService

        await AuditService().log_decision(
            company_id=company_id,
            agent_name="agent_studio_admin",
            decision_type="custom_agent_whatsapp_toggled",
            action="whatsapp_enabled_set" if new_value else "whatsapp_disabled_set",
            decision="approved",
            reasoning=[
                f"agent_id={agent_id}",
                f"previous_value={previous_value}",
                f"new_value={new_value}",
            ],
            criteria_used=["admin_authorization", "per_agent_whatsapp_flag"],
            criteria_ignored=[],
            actor_user_id=str(current_user.id) if current_user else None,
            human_review_required=False,
        )
    except Exception as audit_exc:  # pragma: no cover — best-effort
        logger.warning(
            "[agent_studio_whatsapp] audit log failed (non-blocking): agent=%s err=%s",
            agent_id, audit_exc,
        )

    return WhatsAppEnableResponse(
        agent_id=str(agent.id),
        whatsapp_enabled=new_value,
    )
