"""
External Integrations API endpoints.

Provides endpoints for:
- Microsoft Teams (Incoming Webhooks)
- Other external integrations
"""
import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.auth.dependencies import get_current_user
from app.domains.communication.services.teams_service import AlertSeverity, teams_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/integrations", tags=["integrations"])


class TeamsSendMessageRequest(BaseModel):
    """Request model for sending a Teams message."""
    text: str
    title: str | None = None
    subtitle: str | None = None
    webhook_url: str | None = None


class TeamsSendAlertRequest(BaseModel):
    """Request model for sending a Teams alert."""
    title: str
    message: str
    severity: str = "info"
    facts: list[dict[str, str]] | None = None
    actions: list[dict[str, Any]] | None = None
    source: str | None = None
    webhook_url: str | None = None


class TeamsSendCardRequest(BaseModel):
    """Request model for sending a Teams adaptive card."""
    card: dict[str, Any]
    webhook_url: str | None = None


class TeamsCandidateNotificationRequest(BaseModel):
    """Request model for sending candidate notification to Teams."""
    candidate_name: str
    event: str
    job_title: str | None = None
    details: str | None = None
    action_url: str | None = None
    webhook_url: str | None = None


class TeamsTestRequest(BaseModel):
    """Request model for testing Teams connection."""
    webhook_url: str | None = None


@router.post("/teams/send", response_model=None)
async def send_teams_message(
    request: TeamsSendMessageRequest,
    current_user: dict[str, Any] = Depends(get_current_user)
):
    """
    Send a message to Microsoft Teams via Incoming Webhook.
    
    This endpoint sends a simple text message to a Teams channel.
    If no webhook_url is provided, uses the default TEAMS_WEBHOOK_URL environment variable.
    
    In development mode (no webhook configured), messages are logged instead of sent.
    """
    result = await teams_service.send_message(
        text=request.text,
        title=request.title,
        subtitle=request.subtitle,
        webhook_url=request.webhook_url
    )
    
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error"))
    
    return result


@router.post("/teams/send-alert", response_model=None)
async def send_teams_alert(
    request: TeamsSendAlertRequest,
    current_user: dict[str, Any] = Depends(get_current_user)
):
    """
    Send an alert with severity level to Microsoft Teams.
    
    Severity levels:
    - info: Informational message (blue)
    - success: Success message (green)
    - warning: Warning message (yellow)
    - error: Error message (orange)
    - critical: Critical alert (red)
    
    Optional facts can be provided as key-value pairs to display additional information.
    """
    try:
        severity = AlertSeverity(request.severity)
    except ValueError:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid severity. Must be one of: {[s.value for s in AlertSeverity]}"
        )
    
    result = await teams_service.send_alert(
        title=request.title,
        message=request.message,
        severity=severity,
        webhook_url=request.webhook_url,
        facts=request.facts,
        actions=request.actions,
        source=request.source
    )
    
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error"))
    
    return result


@router.post("/teams/send-card", response_model=None)
async def send_teams_card(
    request: TeamsSendCardRequest,
    current_user: dict[str, Any] = Depends(get_current_user)
):
    """
    Send a custom Adaptive Card to Microsoft Teams.
    
    The card should follow Microsoft Adaptive Card schema.
    See: https://adaptivecards.io/
    """
    result = await teams_service.send_card(
        card=request.card,
        webhook_url=request.webhook_url
    )
    
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error"))
    
    return result


@router.post("/teams/send-candidate-notification", response_model=None)
async def send_teams_candidate_notification(
    request: TeamsCandidateNotificationRequest,
    current_user: dict[str, Any] = Depends(get_current_user)
):
    """
    Send a candidate-related notification to Microsoft Teams.
    
    This is a convenience endpoint for sending formatted candidate updates.
    """
    result = await teams_service.send_candidate_notification(
        candidate_name=request.candidate_name,
        event=request.event,
        job_title=request.job_title,
        details=request.details,
        action_url=request.action_url,
        webhook_url=request.webhook_url
    )
    
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error"))
    
    return result


@router.post("/teams/test", response_model=None)
async def test_teams_connection(
    request: TeamsTestRequest,
    current_user: dict[str, Any] = Depends(get_current_user)
):
    """
    Test Microsoft Teams webhook connection.
    
    Sends a test message to verify the webhook is configured correctly.
    If no webhook_url is provided, uses the default TEAMS_WEBHOOK_URL environment variable.
    """
    result = await teams_service.test_connection(
        webhook_url=request.webhook_url
    )
    
    return result


@router.get("/teams/status", response_model=None)
async def get_teams_status(
    current_user: dict[str, Any] = Depends(get_current_user)
):
    """
    Get Microsoft Teams integration status.
    
    Returns whether Teams is configured and in what mode (production/development).
    """
    return {
        "configured": teams_service.webhook_url is not None,
        "mode": "development" if teams_service.is_development else "production",
        "webhook_url_set": bool(teams_service.webhook_url),
        "available_severity_levels": [s.value for s in AlertSeverity]
    }


@router.get("/status", response_model=None)
async def get_integrations_status(
    current_user: dict[str, Any] = Depends(get_current_user)
):
    """
    Get status of all external integrations.
    
    Returns configuration status for Teams, Webhooks, and other integrations.
    """
    return {
        "teams": {
            "configured": teams_service.webhook_url is not None,
            "mode": "development" if teams_service.is_development else "production"
        },
        "webhooks": {
            "available": True,
            "description": "External webhook notifications for recruitment events"
        },
        "available_integrations": [
            {
                "id": "teams",
                "name": "Microsoft Teams",
                "description": "Send notifications to Teams channels via Incoming Webhooks",
                "configured": teams_service.webhook_url is not None
            },
            {
                "id": "webhooks",
                "name": "External Webhooks",
                "description": "Notify external systems when recruitment events occur",
                "configured": True
            }
        ]
    }


@router.get("/health", response_model=None)
async def get_integrations_health(
    current_user: dict[str, Any] = Depends(get_current_user)
):
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

    # --- LinkedIn / Indeed (uses real health_check from JobBoardService) ---
    try:
        from app.domains.job_management.services.job_board_service import JobBoardService
        _jbs = JobBoardService()
        job_board_health = _jbs.health_check()
    except Exception as _jbe:
        job_board_health = {
            "status": "disconnected",
            "platforms": {
                "linkedin": {"status": "disconnected", "configured": False, "message": str(_jbe)[:200]},
                "indeed": {"status": "not_configured", "configured": False, "feed_available": True, "message": str(_jbe)[:200]},
            },
        }
    integrations["linkedin"] = {
        **job_board_health["platforms"]["linkedin"],
        "check_type": "config_only",
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

    # --- Teams ---
    integrations["teams"] = {
        "status": "connected" if teams_service.webhook_url else "not_configured",
        "configured": bool(teams_service.webhook_url),
        "mode": "development" if teams_service.is_development else "production",
    }

    configured_count = sum(1 for v in integrations.values() if v.get("configured"))
    return {
        "status": "healthy" if configured_count > 0 else "not_configured",
        "configured_count": configured_count,
        "total": len(integrations),
        "integrations": integrations,
    }
