"""
External Integrations API endpoints.

Provides endpoints for:
- Microsoft Teams (Incoming Webhooks)
- Other external integrations
"""
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
import logging

from app.core.database import get_db
from app.services.teams_service import teams_service, AlertSeverity
from app.auth.dependencies import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/integrations", tags=["integrations"])


class TeamsSendMessageRequest(BaseModel):
    """Request model for sending a Teams message."""
    text: str
    title: Optional[str] = None
    subtitle: Optional[str] = None
    webhook_url: Optional[str] = None


class TeamsSendAlertRequest(BaseModel):
    """Request model for sending a Teams alert."""
    title: str
    message: str
    severity: str = "info"
    facts: Optional[List[Dict[str, str]]] = None
    actions: Optional[List[Dict[str, Any]]] = None
    source: Optional[str] = None
    webhook_url: Optional[str] = None


class TeamsSendCardRequest(BaseModel):
    """Request model for sending a Teams adaptive card."""
    card: Dict[str, Any]
    webhook_url: Optional[str] = None


class TeamsCandidateNotificationRequest(BaseModel):
    """Request model for sending candidate notification to Teams."""
    candidate_name: str
    event: str
    job_title: Optional[str] = None
    details: Optional[str] = None
    action_url: Optional[str] = None
    webhook_url: Optional[str] = None


class TeamsTestRequest(BaseModel):
    """Request model for testing Teams connection."""
    webhook_url: Optional[str] = None


@router.post("/teams/send")
async def send_teams_message(
    request: TeamsSendMessageRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
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


@router.post("/teams/send-alert")
async def send_teams_alert(
    request: TeamsSendAlertRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
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


@router.post("/teams/send-card")
async def send_teams_card(
    request: TeamsSendCardRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
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


@router.post("/teams/send-candidate-notification")
async def send_teams_candidate_notification(
    request: TeamsCandidateNotificationRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
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


@router.post("/teams/test")
async def test_teams_connection(
    request: TeamsTestRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
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


@router.get("/teams/status")
async def get_teams_status(
    current_user: Dict[str, Any] = Depends(get_current_user)
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


@router.get("/status")
async def get_integrations_status(
    current_user: Dict[str, Any] = Depends(get_current_user)
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
