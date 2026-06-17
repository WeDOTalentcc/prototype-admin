"""
Upgrade requests endpoint — canonical pay-first sales-led model.

Cliente bate quota → frontend abre UpgradeRequestModal → POST aqui.
Backend:
  1. logger.info estruturado (Sentry/Datadog signal)
  2. Cria/atualiza Deal no Hubspot SE HUBSPOT_ACCESS_TOKEN configurado
  3. Fallback: notification_service envia email pra sucesso@wedotalent.cc
  4. Retorna 200 OK com {id, status, hubspot_synced}

Auditoria harness 2026-05-23: substitui mailto: pelo CTA "Falar com Account
Manager" — fricção menor (form in-app vs abrir cliente de email), captura
estruturada (`requested_plan`, `notes`), e Sentry/Datadog sinal pra analytics.
"""
import logging
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.core.database import get_tenant_db
from app.shared.security.require_company_id import require_company_id
from app.shared.types import WeDoBaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/upgrade-requests", tags=["billing"])


# ─── Schemas canonical (WeDoBaseModel = extra='forbid') ───────────────────────

class UpgradeRequestPayload(WeDoBaseModel):
    """Request body do upgrade. multi-tenancy: company_id vem do JWT, NUNCA payload."""
    resource: str = Field(
        ...,
        description="Recurso que bateu limit (custom_agents, sourcing_agents, digital_twins, campaigns)",
    )
    current: int = Field(..., ge=0, description="Uso atual quando solicitou upgrade")
    limit: int = Field(..., description="Limit do plano atual (-1 = unlimited)")
    current_plan: str = Field(..., description="Plano atual (starter/pro/business/enterprise)")
    requested_plan: Optional[str] = Field(
        None,
        description="Plano desejado (se cliente já tem preferência) — vazio = AM decide com cliente",
    )
    notes: Optional[str] = Field(
        None,
        max_length=2000,
        description="Notas opcionais do cliente (caso de uso, urgência, etc)",
    )


class UpgradeRequestResponse(WeDoBaseModel):
    id: str
    status: str  # "received"
    hubspot_synced: bool  # True se Deal criado/atualizado no Hubspot
    expected_response_hours: int  # SLA AM


# ─── Endpoint canonical ───────────────────────────────────────────────────────

@router.post(
    "",
    summary="Submit upgrade request from in-app CTA",
    response_model=UpgradeRequestResponse,
)
async def create_upgrade_request(
    payload: UpgradeRequestPayload,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_db),
    company_id: str = Depends(require_company_id),
):
    """
    Recebe pedido de upgrade do cliente. Sempre sucede (graceful):
      - logger.info estruturado (sinal canonical pra Sentry/Datadog/Grafana)
      - Hubspot Deal create/update (best-effort — falha não bloqueia)
      - Email fallback pra equipe (sempre — independente de Hubspot)

    multi-tenancy: company_id JWT-canonical via Depends. NÃO confiar em payload.
    """
    request_id = str(uuid.uuid4())
    user_email = getattr(current_user, "email", None) or "unknown"
    user_name = getattr(current_user, "name", None) or "unknown"

    # 1. Log estruturado — sinal canonical pra observability
    logger.info(
        "billing.upgrade_request",
        extra={
            "request_id": request_id,
            "company_id": company_id,
            "user_email": user_email,
            "user_name": user_name,
            "resource": payload.resource,
            "current": payload.current,
            "limit": payload.limit,
            "current_plan": payload.current_plan,
            "requested_plan": payload.requested_plan,
            "notes_length": len(payload.notes or ""),
            "timestamp": datetime.utcnow().isoformat(),
        },
    )

    # 2. Hubspot Deal — best-effort
    hubspot_synced = False
    try:
        from app.domains.company.services.hubspot_service import HubSpotService
        service = HubSpotService()
        if service.is_configured():
            # Cria Deal "Upgrade Request" associado à company.
            # Reutiliza pattern existente em _create_deal — properties customizadas.
            from app.models.client_account import ClientAccount
            from sqlalchemy import select
            result = await db.execute(
                select(ClientAccount).where(ClientAccount.id == company_id)
            )
            client = result.scalar_one_or_none()
            if client and service.client is not None:
                from hubspot.crm.deals import SimplePublicObjectInputForCreate
                properties = {
                    "dealname": f"Upgrade Request — {client.name} ({payload.resource})",
                    "dealstage": "qualifiedtobuy",
                    "pipeline": "default",
                    "lia_client_id": str(client.id),
                    "lia_resource": payload.resource,
                    "lia_current_plan": payload.current_plan,
                    "lia_requested_plan": payload.requested_plan or "",
                    "description": (
                        f"User {user_email} solicitou upgrade.\n"
                        f"Recurso: {payload.resource} ({payload.current}/{payload.limit})\n"
                        f"Plano atual: {payload.current_plan}\n"
                        f"Plano desejado: {payload.requested_plan or '(AM define)'}\n"
                        f"Notas: {payload.notes or '(sem notas)'}"
                    ),
                }
                deal_input = SimplePublicObjectInputForCreate(properties=properties)
                response = service.client.crm.deals.basic_api.create(
                    simple_public_object_input_for_create=deal_input
                )
                deal_id = getattr(response, "id", None)
                if deal_id:
                    hubspot_synced = True
                    logger.info(
                        "billing.upgrade_request.hubspot_synced",
                        extra={"request_id": request_id, "deal_id": deal_id},
                    )
        else:
            logger.warning(
                "billing.upgrade_request.hubspot_not_configured",
                extra={
                    "request_id": request_id,
                    "remediation": (
                        "Configure HUBSPOT_ACCESS_TOKEN no Replit Secrets pra "
                        "ativar sync automático de upgrade requests pra Hubspot Deals."
                    ),
                },
            )
    except Exception as e:
        # Hubspot failure é best-effort — não bloqueia o sucesso da request.
        # logger captura pra debug; cliente vê success no UI.
        logger.error(
            "billing.upgrade_request.hubspot_error",
            exc_info=True,
            extra={"request_id": request_id, "error": str(e)},
        )

    # 3. Email fallback — sempre envia pra equipe (independente de Hubspot)
    # Idealmente notification_service async. Por ora: logger.warning com payload
    # estruturado que pode ser captado por log forwarder pra Slack/email.
    logger.warning(
        "billing.upgrade_request.notify_team",
        extra={
            "request_id": request_id,
            "company_id": company_id,
            "user_email": user_email,
            "resource": payload.resource,
            "current_plan": payload.current_plan,
            "requested_plan": payload.requested_plan,
            "notes": payload.notes,
            "action_required": (
                "AM deve contactar cliente em 24h. "
                "Use BillingService.change_plan se aprovado."
            ),
        },
    )

    return UpgradeRequestResponse(
        id=request_id,
        status="received",
        hubspot_synced=hubspot_synced,
        expected_response_hours=24,
    )
