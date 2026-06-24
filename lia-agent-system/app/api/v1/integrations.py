"""
External Integrations API endpoints.

Provides endpoints for:
- Microsoft Teams (Incoming Webhooks)
- Other external integrations
"""
import logging
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.core.database import get_db
from app.domains.communication.services.teams_service import (
    AlertSeverity,
    resolve_tenant_teams_webhook_url,
    teams_service,
)
from app.models.integration_hub import IntegrationConnection, IntegrationProvider, IntegrationStatus
from app.shared.security.require_company_id import require_company_id
from app.shared.security.url_validator import UnsafeOutboundURLError, safe_outbound_url
from app.shared.errors import LIAError, LIAInternalError
from app.shared.services.credentials_crypto import (
    CredentialsEncryptionError,
    decrypt_credentials,
    encrypt_credentials,
)
from app.shared.types import WeDoBaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/integrations", tags=["integrations"])

_TEAMS_PROVIDER_SLUG = "microsoft_teams"


async def _get_or_create_teams_provider(db: AsyncSession) -> IntegrationProvider:
    """Return the microsoft_teams IntegrationProvider row, creating it on first call."""
    result = await db.execute(
        select(IntegrationProvider).where(IntegrationProvider.slug == _TEAMS_PROVIDER_SLUG)
    )
    provider = result.scalar_one_or_none()
    if provider is None:
        provider = IntegrationProvider(
            id=uuid.uuid4(),
            name="Microsoft Teams",
            category="communication",
            slug=_TEAMS_PROVIDER_SLUG,
            description="Microsoft Teams integration for notifications and collaboration",
            logo_url="/logos/teams.png",
            supports_oauth=True,
            supports_api_key=False,
            supports_webhook=True,
            features=["notifications", "alerts", "candidate_updates", "scheduling"],
            is_active=True,
            is_premium=False,
        )
        db.add(provider)
        await db.flush()
    return provider


async def _get_tenant_teams_webhook_url(company_id: str, db: AsyncSession) -> tuple[str | None, str]:
    """Resolve Teams webhook URL for a tenant.

    Returns (url, source) where source is "db", "env", or "none".
    Priority: per-tenant DB record → global TEAMS_WEBHOOK_URL env var.

    Delegates to the canonical ``resolve_tenant_teams_webhook_url`` helper in
    ``teams_service`` so that the lookup logic lives in one place.
    """
    return await resolve_tenant_teams_webhook_url(company_id, db)


async def _upsert_teams_connection(company_id: str, webhook_url: str, db: AsyncSession) -> None:
    """Persist (upsert) the outbound Teams webhook URL for a tenant."""
    provider = await _get_or_create_teams_provider(db)
    result = await db.execute(
        select(IntegrationConnection).where(
            IntegrationConnection.company_id == company_id,
            IntegrationConnection.provider_id == provider.id,
        )
    )
    conn = result.scalar_one_or_none()
    encrypted = encrypt_credentials({"webhook_url": webhook_url})
    if conn is None:
        conn = IntegrationConnection(
            id=uuid.uuid4(),
            company_id=company_id,
            provider_id=provider.id,
            status=IntegrationStatus.CONNECTED,
            auth_type="webhook",
            credentials_encrypted=encrypted,
        )
        db.add(conn)
    else:
        conn.credentials_encrypted = encrypted
        conn.status = IntegrationStatus.CONNECTED
    await db.flush()


class TeamsOutboundConfigRequest(WeDoBaseModel):
    """Request model for saving the per-tenant Teams outbound webhook URL."""
    webhook_url: str


class TeamsSendMessageRequest(WeDoBaseModel):
    """Request model for sending a Teams message."""
    text: str
    title: str | None = None
    subtitle: str | None = None
    webhook_url: str | None = None


class TeamsSendAlertRequest(WeDoBaseModel):
    """Request model for sending a Teams alert."""
    title: str
    message: str
    severity: str = "info"
    facts: list[dict[str, str]] | None = None
    actions: list[dict[str, Any]] | None = None
    source: str | None = None
    webhook_url: str | None = None


class TeamsSendCardRequest(WeDoBaseModel):
    """Request model for sending a Teams adaptive card."""
    card: dict[str, Any]
    webhook_url: str | None = None


class TeamsCandidateNotificationRequest(WeDoBaseModel):
    """Request model for sending candidate notification to Teams."""
    candidate_name: str
    event: str
    job_title: str | None = None
    details: str | None = None
    action_url: str | None = None
    webhook_url: str | None = None


class TeamsTestRequest(WeDoBaseModel):
    """Request model for testing Teams connection."""
    webhook_url: str | None = None


@router.get("/teams/outbound-config", response_model=None)
async def get_teams_outbound_config(
    current_user: dict[str, Any] = Depends(get_current_user),
    company_id: str = Depends(require_company_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Get the per-tenant Teams outbound webhook URL configuration.

    Returns the configured URL (masked for display) and its source:
    - "db"  — saved by an admin via this settings page
    - "env" — falls back to the global TEAMS_WEBHOOK_URL environment variable
    - "none" — not configured; Teams messages will be logged only
    """
    url, source = await _get_tenant_teams_webhook_url(company_id, db)
    masked: str | None = None
    if url:
        masked = url[:45] + "..." if len(url) > 48 else url
    return {
        "configured": url is not None,
        "webhook_url_masked": masked,
        "source": source,
        "mode": "production" if url else "development",
    }


@router.put("/teams/outbound-config", response_model=None)
async def save_teams_outbound_config(
    request: TeamsOutboundConfigRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
    company_id: str = Depends(require_company_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Save the per-tenant Teams outbound webhook URL.

    The URL is validated (SSRF guard) and stored encrypted in the
    integration_connections table under the microsoft_teams provider.
    After saving, outbound Teams notifications for this tenant will use
    the persisted URL instead of the global TEAMS_WEBHOOK_URL env var.
    """
    try:
        validated_url = safe_outbound_url(request.webhook_url)
    except UnsafeOutboundURLError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    try:
        await _upsert_teams_connection(company_id, validated_url, db)
        await db.commit()
    except CredentialsEncryptionError as exc:
        await db.rollback()
        logger.error("teams outbound-config encrypt failed for %s: %s", company_id, exc)
        raise LIAError(message="Erro ao criptografar configuração") from exc
    except Exception as exc:
        await db.rollback()
        logger.error("teams outbound-config save failed for %s: %s", company_id, exc)
        raise LIAError(message="Erro ao salvar configuração") from exc

    masked = validated_url[:45] + "..." if len(validated_url) > 48 else validated_url
    logger.info("teams outbound webhook URL updated for company %s (source=db)", company_id)
    return {
        "success": True,
        "configured": True,
        "webhook_url_masked": masked,
        "source": "db",
        "mode": "production",
    }


@router.post("/teams/send", response_model=None)
async def send_teams_message(
    request: TeamsSendMessageRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
    company_id: str = Depends(require_company_id),
    db: AsyncSession = Depends(get_db),
):
    # multi-tenancy: resolves per-tenant Teams webhook URL
    """
    Send a message to Microsoft Teams via Incoming Webhook.

    Resolves the webhook URL in priority order:
    1. ``webhook_url`` from request body (explicit override)
    2. Per-tenant DB configuration (saved via Configurações → Integrações)
    3. Global ``TEAMS_WEBHOOK_URL`` environment variable
    4. Development mode (logged only, no HTTP delivery)
    """
    resolved_url = request.webhook_url
    if not resolved_url:
        resolved_url, _ = await _get_tenant_teams_webhook_url(company_id, db)

    result = await teams_service.send_message(
        text=request.text,
        title=request.title,
        subtitle=request.subtitle,
        webhook_url=resolved_url,
    )

    if not result.get("success"):
        raise LIAInternalError(result.get("error"))

    return result


@router.post("/teams/send-alert", response_model=None)
async def send_teams_alert(
    request: TeamsSendAlertRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
    company_id: str = Depends(require_company_id),
    db: AsyncSession = Depends(get_db),
):
    # multi-tenancy: resolves per-tenant Teams webhook URL
    """
    Send an alert with severity level to Microsoft Teams.

    Severity levels:
    - info: Informational message (blue)
    - success: Success message (green)
    - warning: Warning message (yellow)
    - error: Error message (orange)
    - critical: Critical alert (red)

    Optional facts can be provided as key-value pairs to display additional information.

    Resolves the webhook URL per-tenant when no explicit ``webhook_url`` is provided.
    """
    try:
        severity = AlertSeverity(request.severity)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid severity. Must be one of: {[s.value for s in AlertSeverity]}",
        )

    resolved_url = request.webhook_url
    if not resolved_url:
        resolved_url, _ = await _get_tenant_teams_webhook_url(company_id, db)

    result = await teams_service.send_alert(
        title=request.title,
        message=request.message,
        severity=severity,
        webhook_url=resolved_url,
        facts=request.facts,
        actions=request.actions,
        source=request.source,
    )

    if not result.get("success"):
        raise LIAInternalError(result.get("error"))

    return result


@router.post("/teams/send-card", response_model=None)
async def send_teams_card(
    request: TeamsSendCardRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
    company_id: str = Depends(require_company_id),
    db: AsyncSession = Depends(get_db),
):
    # multi-tenancy: resolves per-tenant Teams webhook URL
    """
    Send a custom Adaptive Card to Microsoft Teams.

    The card should follow Microsoft Adaptive Card schema.
    See: https://adaptivecards.io/

    Resolves the webhook URL per-tenant when no explicit ``webhook_url`` is provided.
    """
    resolved_url = request.webhook_url
    if not resolved_url:
        resolved_url, _ = await _get_tenant_teams_webhook_url(company_id, db)

    result = await teams_service.send_card(
        card=request.card,
        webhook_url=resolved_url,
    )

    if not result.get("success"):
        raise LIAInternalError(result.get("error"))

    return result


@router.post("/teams/send-candidate-notification", response_model=None)
async def send_teams_candidate_notification(
    request: TeamsCandidateNotificationRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
    company_id: str = Depends(require_company_id),
    db: AsyncSession = Depends(get_db),
):
    # multi-tenancy: resolves per-tenant Teams webhook URL
    """
    Send a candidate-related notification to Microsoft Teams.

    This is a convenience endpoint for sending formatted candidate updates.
    Resolves the webhook URL per-tenant when no explicit ``webhook_url`` is provided.
    """
    resolved_url = request.webhook_url
    if not resolved_url:
        resolved_url, _ = await _get_tenant_teams_webhook_url(company_id, db)

    result = await teams_service.send_candidate_notification(
        candidate_name=request.candidate_name,
        event=request.event,
        job_title=request.job_title,
        details=request.details,
        action_url=request.action_url,
        webhook_url=resolved_url,
    )

    if not result.get("success"):
        raise LIAInternalError(result.get("error"))

    return result


@router.post("/teams/test", response_model=None)
async def test_teams_connection(
    request: TeamsTestRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
    company_id: str = Depends(require_company_id),
    db: AsyncSession = Depends(get_db),
):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """
    Test Microsoft Teams webhook connection.

    Sends a test message to verify the webhook is configured correctly.
    If no webhook_url is provided, resolves the per-tenant DB config then
    falls back to the global TEAMS_WEBHOOK_URL environment variable.
    """
    url = request.webhook_url
    if not url:
        url, _ = await _get_tenant_teams_webhook_url(company_id, db)
    result = await teams_service.test_connection(webhook_url=url)
    return result


@router.get("/teams/status", response_model=None)
async def get_teams_status(
    current_user: dict[str, Any] = Depends(get_current_user),
    company_id: str = Depends(require_company_id),
    db: AsyncSession = Depends(get_db),
):
    # multi-tenancy: resolves per-tenant DB config
    """
    Get Microsoft Teams integration status.

    Returns whether Teams is configured and in what mode (production/development).
    Checks per-tenant DB configuration first, then falls back to the global env var.
    """
    url, source = await _get_tenant_teams_webhook_url(company_id, db)
    return {
        "configured": url is not None,
        "mode": "production" if url else "development",
        "webhook_url_set": url is not None,
        "source": source,
        "available_severity_levels": [s.value for s in AlertSeverity],
    }


@router.get("/status", response_model=None)
async def get_integrations_status(
    current_user: dict[str, Any] = Depends(get_current_user),
    company_id: str = Depends(require_company_id),
    db: AsyncSession = Depends(get_db),
):
    # multi-tenancy: resolves per-tenant Teams config from DB
    """
    Get status of all external integrations.

    Returns configuration status for Teams, Webhooks, and other integrations.
    """
    teams_url, teams_source = await _get_tenant_teams_webhook_url(company_id, db)
    return {
        "teams": {
            "configured": teams_url is not None,
            "mode": "production" if teams_url else "development",
            "source": teams_source,
        },
        "webhooks": {
            "available": True,
            "description": "External webhook notifications for recruitment events",
        },
        "available_integrations": [
            {
                "id": "teams",
                "name": "Microsoft Teams",
                "description": "Send notifications to Teams channels via Incoming Webhooks",
                "configured": teams_url is not None,
            },
            {
                "id": "webhooks",
                "name": "External Webhooks",
                "description": "Notify external systems when recruitment events occur",
                "configured": True,
            },
        ],
    }


@router.get("/health", response_model=None)
async def get_integrations_health(
    current_user: dict[str, Any] = Depends(get_current_user),
    company_id: str = Depends(require_company_id),
    db: AsyncSession = Depends(get_db),
):
    # multi-tenancy: Teams check resolves per-tenant config
    """
    Unified health check for all external business integrations.

    Returns structured status for:
    - WhatsApp (Meta and Twilio providers)
    - Microsoft Calendar / Teams (Azure Graph API)
    - Google Calendar (service account or OAuth 2.0)
    - LinkedIn (job posting via OAuth)
    - Indeed (direct API or XML feed fallback)
    - Pearch (candidate sourcing)
    - Slack (bot token or incoming webhook)

    Each integration returns one of:
    - connected:       credentials present
    - not_configured:  credentials absent (graceful fallback where available)
    """
    import os

    from app.domains.communication.services.whatsapp_meta_service import meta_whatsapp_service
    from app.domains.communication.services.whatsapp_twilio_service import twilio_whatsapp_service

    integrations: dict[str, Any] = {}

    # --- WhatsApp ---
    meta_ok = meta_whatsapp_service.is_configured
    twilio_ok = twilio_whatsapp_service.is_configured
    integrations["whatsapp"] = {
        "status": "connected" if (meta_ok or twilio_ok) else "not_configured",
        "configured": meta_ok or twilio_ok,
        "fallback_mode": "development_log" if not (meta_ok or twilio_ok) else None,
        "providers": {
            "meta": {
                "status": "connected" if meta_ok else "not_configured",
                "configured": meta_ok,
                "verify_token_set": bool(meta_whatsapp_service.verify_token),
                "app_secret_set": bool(meta_whatsapp_service.app_secret),
            },
            "twilio": {
                "status": "connected" if twilio_ok else "not_configured",
                "configured": twilio_ok,
            },
        },
    }

    # --- Microsoft Calendar / Teams (real health_check with token probe when configured) ---
    try:
        from app.domains.integrations_hub.services.microsoft_graph_service import MicrosoftGraphService
        _msgraph = MicrosoftGraphService()
        ms_health = await _msgraph.health_check()
    except Exception as _mse:
        ms_health = {"status": "disconnected", "configured": False, "message": str(_mse)[:200]}
    integrations["microsoft_calendar"] = {
        **ms_health,
        "provider": "microsoft_graph",
        "check_type": "config_and_token_probe" if ms_health.get("configured") else "config_only",
        "oauth_flow_url": "/api/v1/calendar/microsoft/auth-url",
        "oauth_status_url": "/api/v1/calendar/microsoft/oauth-status?company_id=<company_id>",
    }

    # --- Google Calendar ---
    gc_enabled = os.getenv("ENABLE_GOOGLE_CALENDAR", "false").lower() in ("1", "true", "yes")
    gc_sa = bool(os.getenv("GOOGLE_CALENDAR_SERVICE_ACCOUNT_JSON"))
    gc_oauth = bool(os.getenv("GOOGLE_CALENDAR_CLIENT_ID") and os.getenv("GOOGLE_CALENDAR_CLIENT_SECRET"))
    gc_ok = gc_enabled and (gc_sa or gc_oauth)
    integrations["google_calendar"] = {
        "status": "connected" if gc_ok else ("not_configured" if not gc_enabled else "disconnected"),
        "configured": gc_ok,
        "enabled": gc_enabled,
        "auth_method": "service_account" if gc_sa else ("oauth2" if gc_oauth else None),
        "oauth_flow_url": "/api/v1/calendar/google/auth-url" if gc_oauth else None,
        "oauth_status_url": "/api/v1/calendar/google/oauth-status?company_id=<company_id>" if gc_oauth else None,
        "check_type": "config_only",
        "message": None if gc_ok else (
            "Google Calendar disabled or credentials not configured. "
            "Set ENABLE_GOOGLE_CALENDAR=True and GOOGLE_CALENDAR_CLIENT_ID/SECRET."
        ),
    }

    # --- Pearch (uses real health_check from PearchService) ---
    try:
        from app.domains.sourcing.services.pearch_service import PearchService
        _pearch = PearchService()
        pearch_health = await _pearch.health_check()
    except Exception as _pe:
        pearch_health = {"status": "disconnected", "configured": False, "message": str(_pe)[:200]}
    integrations["pearch"] = {
        **pearch_health,
        "fallback": "local_rag_search" if not pearch_health.get("configured") else None,
        "check_type": "config_and_ping" if pearch_health.get("configured") else "config_only",
    }

    # --- LinkedIn / Indeed ---
    # LinkedIn: per-tenant IntegrationConnection (NOT env vars).
    try:
        from app.api.v1.linkedin_integration import _get_decrypted_credentials
        _li_creds = await _get_decrypted_credentials(company_id, db)
        _li_connected = _li_creds is not None
    except Exception as _li_exc:
        logger.warning("[integrations:health] LinkedIn check failed: %s", _li_exc)
        _li_connected = False
    integrations["linkedin"] = {
        "status": "connected" if _li_connected else "not_configured",
        "configured": _li_connected,
        "check_type": "per_tenant_connection",
        "message": None if _li_connected else (
            "LinkedIn nao configurado. "
            "Conecte em Configuracoes > Integracoes > Job Boards > LinkedIn."
        ),
    }
    try:
        from app.domains.job_management.services.job_board_service import JobBoardService
        _jbs = JobBoardService()
        job_board_health = _jbs.health_check()
    except Exception as _jbe:
        job_board_health = {
            "status": "not_configured",
            "platforms": {
                "indeed": {"status": "not_configured", "configured": False, "feed_available": True, "message": str(_jbe)[:200]},
            },
        }
    integrations["indeed"] = {
        **job_board_health["platforms"]["indeed"],
        "check_type": "config_only",
    }

    # --- Slack ---
    slack_token = os.getenv("SLACK_BOT_TOKEN")
    slack_webhook = os.getenv("SLACK_WEBHOOK_URL")
    slack_ok = bool(slack_token or slack_webhook)
    integrations["slack"] = {
        "status": "connected" if slack_ok else "not_configured",
        "configured": slack_ok,
        "auth_method": "bot_token" if slack_token else ("webhook" if slack_webhook else None),
        "message": None if slack_ok else "Configure SLACK_BOT_TOKEN ou SLACK_WEBHOOK_URL para habilitar notificações Slack.",
    }

    # --- Teams outbound (per-tenant: resolves DB config → global env fallback) ---
    _teams_url, _teams_source = await _get_tenant_teams_webhook_url(company_id, db)
    integrations["teams"] = {
        "status": "connected" if _teams_url else "not_configured",
        "configured": bool(_teams_url),
        "mode": "production" if _teams_url else "development",
        "source": _teams_source,
    }

    configured_count = sum(1 for v in integrations.values() if v.get("configured"))
    return {
        "status": "healthy" if configured_count > 0 else "not_configured",
        "configured_count": configured_count,
        "total": len(integrations),
        "integrations": integrations,
    }


# ---------------------------------------------------------------------------
# GET /integrations/summary — agrega 4 fetches em 1 (performance fix 2026-06-21)
# ---------------------------------------------------------------------------

class CalendarSummary(WeDoBaseModel):
    graph_configured: bool
    google_configured: bool


class TeamsSummary(WeDoBaseModel):
    configured: bool
    source: str


class LLMConfigSummary(WeDoBaseModel):
    company_id: str
    primary_provider: str
    fallback_order: list[str]
    providers: dict[str, dict]
    routing: dict[str, str]
    is_active: bool


class ATSConnectionSummary(WeDoBaseModel):
    provider: str
    is_active: bool


class IntegrationsSummaryResponse(WeDoBaseModel):
    calendar: CalendarSummary
    teams: TeamsSummary
    llm_config: LLMConfigSummary
    ats_connections: list[ATSConnectionSummary]


@router.get("/summary", response_model=IntegrationsSummaryResponse)
async def get_integrations_summary(
    current_user: dict = Depends(get_current_user),
    company_id: str = Depends(require_company_id),
    db: AsyncSession = Depends(get_db),
):
    # multi-tenancy: company_id via JWT Depends(require_company_id)
    """
    Aggregate summary of calendar health, teams status, LLM config and ATS
    connections. Runs all 4 queries in parallel via asyncio.gather — reduces
    4 serial roundtrips from the frontend to 1.

    Performance fix 2026-06-21: replaces 4 separate useQuery fetches in
    use-integrations-data.ts with a single call.
    """
    import asyncio
    import os

    from app.core.config import settings
    from app.domains.ai.repositories.llm_config_repository import LlmConfigRepository
    from app.domains.ats_integration.repositories.ats_repository import ATSRepository

    async def _get_calendar() -> dict:
        ms_ok = bool(
            getattr(settings, "AZURE_CLIENT_ID", None)
            and getattr(settings, "AZURE_CLIENT_SECRET", None)
            and getattr(settings, "AZURE_TENANT_ID", None)
        )
        gc_enabled = os.getenv("ENABLE_GOOGLE_CALENDAR", "false").lower() in ("1", "true", "yes")
        gc_configured = gc_enabled and bool(
            os.getenv("GOOGLE_CALENDAR_SERVICE_ACCOUNT_JSON")
            or (os.getenv("GOOGLE_CALENDAR_CLIENT_ID") and os.getenv("GOOGLE_CALENDAR_CLIENT_SECRET"))
        )
        return {"graph_configured": ms_ok, "google_configured": gc_configured}

    async def _get_teams() -> dict:
        url, source = await _get_tenant_teams_webhook_url(company_id, db)
        return {"configured": url is not None, "source": source}

    async def _get_llm_config() -> dict:
        repo = LlmConfigRepository(db)
        config = await repo.get_by_company_id(company_id)
        if not config:
            return {
                "company_id": company_id,
                "primary_provider": "gemini",
                "fallback_order": ["gemini", "claude", "openai"],
                "providers": {},
                "routing": {"chat": "gemini", "embedding": "gemini", "screening": "gemini", "voice": "gemini"},
                "is_active": True,
            }
        masked_providers: dict = {}
        for name, prov in (config.providers or {}).items():
            masked = dict(prov) if isinstance(prov, dict) else {}
            if "api_key" in masked and masked["api_key"]:
                key = masked["api_key"]
                masked["api_key"] = (key[:8] + "..." + key[-4:]) if len(key) > 12 else "••••••••"
            masked_providers[name] = masked
        return {
            "company_id": company_id,
            "primary_provider": config.primary_provider or "gemini",
            "fallback_order": config.fallback_order or ["gemini", "claude", "openai"],
            "providers": masked_providers,
            "routing": config.routing or {},
            "is_active": config.is_active,
        }

    async def _get_ats_connections() -> list:
        repo = ATSRepository(db)
        connections = await repo.get_active_connections_by_company(company_id)
        return [
            {"provider": conn.provider.value, "is_active": conn.is_active}
            for conn in connections
        ]

    calendar_data, teams_data, llm_data, ats_data = await asyncio.gather(
        _get_calendar(),
        _get_teams(),
        _get_llm_config(),
        _get_ats_connections(),
        return_exceptions=True,
    )

    # Fail-loud per REGRA 4 (CLAUDE.md) — nao retornar dados fabricados em erro
    for result_name, result in [("calendar", calendar_data), ("teams", teams_data), ("llm_config", llm_data), ("ats_connections", ats_data)]:
        if isinstance(result, Exception):
            logger.error("[integrations/summary] sub-query %s failed for company %s: %s", result_name, company_id, result)
            raise HTTPException(
                status_code=503,
                detail={
                    "error": f"integrations_summary_{result_name}_failed",
                    "message": f"Falha ao carregar dados de integracoes ({result_name}). Tente novamente.",
                    "section": result_name,
                },
            )

    return IntegrationsSummaryResponse(
        calendar=CalendarSummary(**calendar_data),
        teams=TeamsSummary(**teams_data),
        llm_config=LLMConfigSummary(**llm_data),
        ats_connections=[ATSConnectionSummary(**c) for c in ats_data],
    )
