"""
Microsoft Teams webhook endpoints.

Includes:
- Message handling from Teams Bot Framework
- Adaptive Card action webhook for Teams → WhatsApp Screening connector
- Proactive notifications to Teams users
"""
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, Request, HTTPException, Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum
import logging
import json
import hmac
import hashlib
import os
import uuid

from app.core.database import get_db
from app.models.teams import TeamsConversation, TeamsMessage, TeamsActionAuditLog
from app.services.teams_simple import simple_teams_bot
from app.services.teams_auth import bot_auth
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/teams", tags=["teams"])


class TeamsCardAction(str, Enum):
    """Supported Adaptive Card actions from Teams."""
    APPROVE = "approve"
    REJECT = "reject"
    SCHEDULE = "schedule"
    RESCHEDULE = "reschedule"
    REQUEST_INFO = "request_info"


class TeamsWebhookPayload(BaseModel):
    """Payload from Teams Adaptive Card action."""
    action: str = Field(..., description="Action type: approve, reject, schedule")
    candidate_id: Optional[str] = Field(None, description="Candidate ID")
    candidate_name: Optional[str] = Field(None, description="Candidate name")
    candidate_phone: Optional[str] = Field(None, description="Candidate phone number")
    vacancy_id: Optional[str] = Field(None, description="Job vacancy ID")
    vacancy_title: Optional[str] = Field(None, description="Job vacancy title")
    company_id: Optional[str] = Field(None, description="Company ID")
    recruiter_id: Optional[str] = Field(None, description="Recruiter user ID who performed the action")
    recruiter_name: Optional[str] = Field(None, description="Recruiter name")
    notes: Optional[str] = Field(None, description="Optional notes from recruiter")
    scheduled_date: Optional[str] = Field(None, description="Scheduled date for interviews")
    item_id: Optional[str] = Field(None, description="Generic item ID for approvals")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")
    
    class Config:
        json_schema_extra = {
            "example": {
                "action": "approve",
                "candidate_id": "cand_123",
                "candidate_name": "João Silva",
                "candidate_phone": "+5511999999999",
                "vacancy_id": "vac_456",
                "vacancy_title": "Desenvolvedor Python Senior",
                "company_id": "comp_789"
            }
        }


class TeamsWebhookResponse(BaseModel):
    """Response from Teams webhook processing."""
    success: bool
    action: str
    message: str
    screening_initiated: bool = False
    audit_id: Optional[str] = None
    candidate_id: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class TeamsActionAuditLogSchema(BaseModel):
    """Pydantic schema for Teams audit log response."""
    id: str = Field(..., description="Audit log ID")
    action: str
    actor_id: Optional[str] = None
    actor_name: Optional[str] = None
    candidate_id: Optional[str] = None
    vacancy_id: Optional[str] = None
    company_id: Optional[str] = None
    source: str = "teams_adaptive_card"
    result: str
    details: Dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


def _verify_teams_webhook_signature(payload: bytes, signature: Optional[str]) -> bool:
    """
    Verify webhook signature from Teams.
    
    Uses HMAC-SHA256 with TEAMS_WEBHOOK_SECRET.
    In production, TEAMS_WEBHOOK_SECRET is required and webhook without valid signature is rejected.
    In development, if no secret is configured, allows all requests.
    
    Raises:
        HTTPException: 403 if in production and secret is not configured
        HTTPException: 401 if signature is invalid in production
    """
    teams_webhook_secret = settings.TEAMS_WEBHOOK_SECRET
    is_production = settings.APP_ENV == "production"
    
    # Production security check: require TEAMS_WEBHOOK_SECRET
    if is_production and not teams_webhook_secret:
        logger.error(
            "[TEAMS WEBHOOK SECURITY] TEAMS_WEBHOOK_SECRET not configured in production! "
            "Webhook authentication is disabled. This is a security risk."
        )
        raise HTTPException(
            status_code=403,
            detail="Webhook security not configured. TEAMS_WEBHOOK_SECRET is required in production."
        )
    
    # Development mode: if no secret, allow all requests
    if not teams_webhook_secret:
        logger.warning("[TEAMS WEBHOOK] TEAMS_WEBHOOK_SECRET not configured, skipping signature verification (development mode only)")
        return True
    
    if not signature:
        logger.warning("[TEAMS WEBHOOK] Missing signature header")
        return False
    
    expected_prefix = "sha256="
    if signature.startswith(expected_prefix):
        signature = signature[len(expected_prefix):]
    
    computed_signature = hmac.new(
        teams_webhook_secret.encode('utf-8'),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(computed_signature, signature)


async def _log_teams_action_audit(
    action: str,
    result: str,
    actor_id: Optional[str] = None,
    actor_name: Optional[str] = None,
    candidate_id: Optional[str] = None,
    vacancy_id: Optional[str] = None,
    company_id: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    db: Optional[AsyncSession] = None
) -> str:
    """
    Log Teams action for audit trail to database.
    
    Persists audit logs to PostgreSQL database for compliance and auditing.
    If database is not available, logs warning and returns a placeholder ID.
    
    Args:
        action: The action type (approve, reject, schedule, etc.)
        result: The result (success, failed, auth_failed, etc.)
        actor_id: ID of the user who performed the action
        actor_name: Name of the user who performed the action
        candidate_id: ID of the candidate affected
        vacancy_id: ID of the vacancy/job
        company_id: ID of the company
        details: Additional details about the action
        db: Database session
    
    Returns:
        The audit log ID
    """
    audit_id = str(uuid.uuid4())
    
    try:
        if db is None:
            logger.warning("[TEAMS AUDIT] No database session provided, skipping database persistence")
        else:
            # Create database audit log entry
            audit_entry = TeamsActionAuditLog(
                id=audit_id,
                action=action,
                actor_id=actor_id,
                actor_name=actor_name,
                candidate_id=candidate_id,
                vacancy_id=vacancy_id,
                company_id=company_id,
                result=result,
                details=details or {}
            )
            
            db.add(audit_entry)
            await db.commit()
            
            logger.info(
                f"[TEAMS AUDIT] Action={action} Result={result} "
                f"Actor={actor_name or actor_id} Candidate={candidate_id} "
                f"Vacancy={vacancy_id} AuditID={audit_id} [PERSISTED]"
            )
    except Exception as e:
        logger.error(f"[TEAMS AUDIT] Error persisting audit log to database: {e}", exc_info=True)
        logger.info(f"[TEAMS AUDIT] Audit log created with ID={audit_id} but persistence failed")
    
    return audit_id


async def _start_whatsapp_screening(
    candidate_id: str,
    candidate_name: str,
    candidate_phone: str,
    vacancy_id: Optional[str],
    vacancy_title: Optional[str],
    company_id: Optional[str],
    recruiter_name: Optional[str],
    db: AsyncSession
) -> Dict[str, Any]:
    """
    Start WhatsApp screening for an approved candidate.
    
    Uses the CommunicationDispatcher to send screening invite via WhatsApp.
    """
    try:
        from app.services.communication_dispatcher import communication_dispatcher
        from app.services.communication_history_service import communication_history_service
        
        screening_message = f"""Olá {candidate_name}! 👋

Temos boas notícias! Você foi pré-aprovado para a vaga de *{vacancy_title or 'posição aberta'}*.

Agora vamos para a próxima etapa: uma conversa rápida de triagem para conhecer melhor seu perfil.

Você está disponível para começar agora? Responda *SIM* para iniciar ou *DEPOIS* para agendar outro horário.

🤖 _Sou a LIA, assistente de recrutamento._"""
        
        result = communication_dispatcher.send_whatsapp(
            to_phone=candidate_phone,
            message=screening_message
        )
        
        if result.get("success"):
            try:
                await communication_history_service.log_communication(
                    candidate_id=candidate_id,
                    candidate_name=candidate_name,
                    candidate_email=None,
                    candidate_phone=candidate_phone,
                    vacancy_id=vacancy_id,
                    vacancy_title=vacancy_title,
                    communication_type="screening_invite",
                    channel="whatsapp",
                    direction="outbound",
                    subject=None,
                    message_content=screening_message,
                    sent_by=recruiter_name or "teams_automation",
                    company_id=company_id or "default",
                    extra_data={
                        "message_id": result.get("message_id"),
                        "trigger": "teams_adaptive_card",
                        "action": "approve",
                        "screening_type": "wsi"
                    }
                )
            except Exception as log_err:
                logger.warning(f"Failed to log communication history: {log_err}")
        
        return {
            "success": result.get("success", False),
            "message_id": result.get("message_id"),
            "mock": result.get("mock", False),
            "error": result.get("error")
        }
        
    except Exception as e:
        logger.error(f"Error starting WhatsApp screening: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }


async def _handle_approve_action(
    payload: TeamsWebhookPayload,
    db: AsyncSession
) -> TeamsWebhookResponse:
    """Handle approve action from Teams Adaptive Card."""
    if not payload.candidate_phone:
        return TeamsWebhookResponse(
            success=False,
            action="approve",
            message="Número de telefone do candidato não fornecido",
            candidate_id=payload.candidate_id
        )
    
    screening_result = await _start_whatsapp_screening(
        candidate_id=payload.candidate_id or "",
        candidate_name=payload.candidate_name or "Candidato",
        candidate_phone=payload.candidate_phone,
        vacancy_id=payload.vacancy_id,
        vacancy_title=payload.vacancy_title,
        company_id=payload.company_id,
        recruiter_name=payload.recruiter_name,
        db=db
    )
    
    audit_id = await _log_teams_action_audit(
        action="approve",
        result="success" if screening_result.get("success") else "failed",
        actor_id=payload.recruiter_id,
        actor_name=payload.recruiter_name,
        candidate_id=payload.candidate_id,
        vacancy_id=payload.vacancy_id,
        company_id=payload.company_id,
        details={
            "screening_initiated": screening_result.get("success", False),
            "message_id": screening_result.get("message_id"),
            "mock_mode": screening_result.get("mock", False),
            "error": screening_result.get("error"),
            "notes": payload.notes
        },
        db=db
    )
    
    if screening_result.get("success"):
        return TeamsWebhookResponse(
            success=True,
            action="approve",
            message=f"Candidato {payload.candidate_name} aprovado. Triagem WhatsApp iniciada.",
            screening_initiated=True,
            audit_id=audit_id,
            candidate_id=payload.candidate_id
        )
    else:
        return TeamsWebhookResponse(
            success=False,
            action="approve",
            message=f"Erro ao iniciar triagem: {screening_result.get('error')}",
            screening_initiated=False,
            audit_id=audit_id,
            candidate_id=payload.candidate_id
        )


async def _handle_reject_action(
    payload: TeamsWebhookPayload,
    db: AsyncSession
) -> TeamsWebhookResponse:
    """Handle reject action from Teams Adaptive Card."""
    audit_id = await _log_teams_action_audit(
        action="reject",
        result="success",
        actor_id=payload.recruiter_id,
        actor_name=payload.recruiter_name,
        candidate_id=payload.candidate_id,
        vacancy_id=payload.vacancy_id,
        company_id=payload.company_id,
        details={
            "notes": payload.notes,
            "reason": payload.metadata.get("reason") if payload.metadata else None
        },
        db=db
    )
    
    logger.info(
        f"[TEAMS] Candidate {payload.candidate_id} rejected by {payload.recruiter_name} "
        f"for vacancy {payload.vacancy_id}"
    )
    
    return TeamsWebhookResponse(
        success=True,
        action="reject",
        message=f"Candidato {payload.candidate_name} rejeitado.",
        audit_id=audit_id,
        candidate_id=payload.candidate_id
    )


async def _handle_schedule_action(
    payload: TeamsWebhookPayload,
    db: AsyncSession
) -> TeamsWebhookResponse:
    """Handle schedule/reschedule action from Teams Adaptive Card."""
    action_type = payload.action
    
    audit_id = await _log_teams_action_audit(
        action=action_type,
        result="success",
        actor_id=payload.recruiter_id,
        actor_name=payload.recruiter_name,
        candidate_id=payload.candidate_id,
        vacancy_id=payload.vacancy_id,
        company_id=payload.company_id,
        details={
            "scheduled_date": payload.scheduled_date,
            "notes": payload.notes
        },
        db=db
    )
    
    logger.info(
        f"[TEAMS] Interview scheduled for candidate {payload.candidate_id} "
        f"at {payload.scheduled_date} by {payload.recruiter_name}"
    )
    
    return TeamsWebhookResponse(
        success=True,
        action=action_type,
        message=f"Entrevista agendada para {payload.candidate_name}.",
        audit_id=audit_id,
        candidate_id=payload.candidate_id
    )


@router.post("/webhook", response_model=TeamsWebhookResponse)
async def teams_adaptive_card_webhook(
    request: Request,
    x_teams_signature: Optional[str] = Header(None, alias="X-Teams-Signature"),
    x_company_id: Optional[str] = Header(None, alias="X-Company-ID"),
    db: AsyncSession = Depends(get_db)
):
    """
    Webhook endpoint for receiving Adaptive Card actions from Microsoft Teams.
    
    This endpoint handles:
    - **approve**: Approves candidate and initiates WhatsApp screening
    - **reject**: Rejects candidate and logs the decision
    - **schedule**: Schedules interview for candidate
    - **reschedule**: Reschedules existing interview
    - **request_info**: Requests additional information from candidate
    
    Security:
    - Validates X-Teams-Signature header using HMAC-SHA256
    - If TEAMS_WEBHOOK_SECRET not set, allows all requests (development mode)
    
    Audit:
    - All actions are logged for compliance and auditing
    - Logs include actor, candidate, vacancy, timestamp, and result
    
    Request body example:
    ```json
    {
        "action": "approve",
        "candidate_id": "cand_123",
        "candidate_name": "João Silva",
        "candidate_phone": "+5511999999999",
        "vacancy_id": "vac_456",
        "vacancy_title": "Desenvolvedor Python",
        "company_id": "comp_789",
        "recruiter_id": "user_001",
        "recruiter_name": "Maria Santos"
    }
    ```
    """
    raw_body = await request.body()
    
    # Security check: verify webhook signature
    try:
        if not _verify_teams_webhook_signature(raw_body, x_teams_signature):
            logger.warning("[TEAMS WEBHOOK] Invalid signature")
            await _log_teams_action_audit(
                action="unknown",
                result="auth_failed",
                details={"error": "Invalid signature"},
                db=db
            )
            raise HTTPException(status_code=401, detail="Invalid signature")
    except HTTPException:
        # Re-raise HTTP exceptions (403 for missing secret in production, 401 for invalid signature)
        raise
    
    try:
        payload_data = json.loads(raw_body)
        payload = TeamsWebhookPayload(**payload_data)
        
        if x_company_id and not payload.company_id:
            payload.company_id = x_company_id
        
    except json.JSONDecodeError as e:
        logger.error(f"[TEAMS WEBHOOK] Invalid JSON: {e}")
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
    except Exception as e:
        logger.error(f"[TEAMS WEBHOOK] Payload validation error: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid payload: {str(e)}")
    
    logger.info(f"[TEAMS WEBHOOK] Received action={payload.action} for candidate={payload.candidate_id}")
    
    action = payload.action.lower()
    
    if action == TeamsCardAction.APPROVE.value:
        return await _handle_approve_action(payload, db)
    
    elif action == TeamsCardAction.REJECT.value:
        return await _handle_reject_action(payload, db)
    
    elif action in [TeamsCardAction.SCHEDULE.value, TeamsCardAction.RESCHEDULE.value]:
        return await _handle_schedule_action(payload, db)
    
    elif action == TeamsCardAction.REQUEST_INFO.value:
        audit_id = await _log_teams_action_audit(
            action="request_info",
            result="success",
            actor_id=payload.recruiter_id,
            actor_name=payload.recruiter_name,
            candidate_id=payload.candidate_id,
            vacancy_id=payload.vacancy_id,
            company_id=payload.company_id,
            details={"notes": payload.notes},
            db=db
        )
        return TeamsWebhookResponse(
            success=True,
            action="request_info",
            message=f"Solicitação de informações enviada para {payload.candidate_name}.",
            audit_id=audit_id,
            candidate_id=payload.candidate_id
        )
    
    else:
        await _log_teams_action_audit(
            action=action,
            result="invalid_action",
            actor_id=payload.recruiter_id,
            details={"received_action": action}
        )
        raise HTTPException(
            status_code=400,
            detail=f"Ação não suportada: {action}. Ações válidas: approve, reject, schedule, reschedule, request_info"
        )


@router.get("/webhook/audit-logs")
async def get_teams_audit_logs(
    limit: int = 50,
    action: Optional[str] = None,
    candidate_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieve Teams webhook audit logs from database.
    
    Query parameters:
    - limit: Maximum number of logs to return (default 50)
    - action: Filter by action type
    - candidate_id: Filter by candidate ID
    
    Returns paginated audit logs ordered by most recent first.
    """
    try:
        # Build query
        query = select(TeamsActionAuditLog)
        
        # Apply filters
        filters = []
        if action:
            filters.append(TeamsActionAuditLog.action == action)
        if candidate_id:
            filters.append(TeamsActionAuditLog.candidate_id == candidate_id)
        
        if filters:
            from sqlalchemy import and_
            for filter_clause in filters:
                query = query.where(filter_clause)
        
        # Order by most recent first, limit results
        query = query.order_by(TeamsActionAuditLog.created_at.desc()).limit(limit)
        
        result = await db.execute(query)
        logs = result.scalars().all()
        
        # Count total matching (without limit)
        count_query = select(TeamsActionAuditLog)
        filters = []
        if action:
            filters.append(TeamsActionAuditLog.action == action)
        if candidate_id:
            filters.append(TeamsActionAuditLog.candidate_id == candidate_id)
        
        if filters:
            from sqlalchemy import and_
            for filter_clause in filters:
                count_query = count_query.where(filter_clause)
        
        count_result = await db.execute(count_query)
        total_count = len(count_result.scalars().all())
        
        return {
            "count": len(logs),
            "total": total_count,
            "limit": limit,
            "logs": [log.to_dict() for log in logs]
        }
    except Exception as e:
        logger.error(f"Error retrieving audit logs: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error retrieving audit logs: {str(e)}")


@router.post("/messages")
async def receive_teams_message(
    request: Request,
    authorization: str = Header(None),
    db: AsyncSession = Depends(get_db)
):
    """
    Webhook endpoint for Teams messages.
    
    This is called by Microsoft Bot Framework when:
    - User sends a message to the bot
    - Bot is added to a conversation
    - Adaptive card action is triggered
    """
    try:
        # Get activity payload
        activity = await request.json()
        
        logger.info(f"Received Teams activity: {activity.get('type')}")
        
        # Validate JWT token from Microsoft Bot Framework (REQUIRED)
        if not settings.MICROSOFT_APP_ID or not settings.MICROSOFT_APP_PASSWORD:
            logger.error("Teams Bot not configured - rejecting webhook request")
            raise HTTPException(
                status_code=503,
                detail="Teams Bot not configured. Set MICROSOFT_APP_ID and MICROSOFT_APP_PASSWORD."
            )
        
        # Validate JWT token - ALWAYS required
        is_valid = await bot_auth.validate_token(authorization, settings.MICROSOFT_APP_ID)
        if not is_valid:
            logger.warning("Invalid or missing Bot Framework JWT token")
            raise HTTPException(status_code=401, detail="Unauthorized - invalid JWT token")
        
        # Process activity with simplified bot
        response = await simple_teams_bot.process_activity(activity)
        
        # Send response based on activity type
        service_url = activity.get("serviceUrl")
        conversation_id = activity.get("conversation", {}).get("id")
        activity_id = activity.get("id")
        
        if isinstance(response, str):
            # Simple text response (for messages)
            await simple_teams_bot.send_message(
                service_url=service_url,
                conversation_id=conversation_id,
                text=response,
                reply_to_activity_id=activity_id if activity.get("type") == "message" else None
            )
        elif isinstance(response, dict) and "messages" in response:
            # Multiple messages (for conversationUpdate)
            for msg in response["messages"]:
                await simple_teams_bot.send_message(
                    service_url=service_url,
                    conversation_id=conversation_id,
                    text=msg["text"]
                )
        
        response = {"status": "ok"}
        
        # Store conversation reference if this is a message
        if activity.get("type") == "message":
            await _store_conversation_reference(activity, db)
        
        # Log the message
        await _log_teams_message(activity, db)
        
        return response
    
    except HTTPException:
        # Re-raise HTTP exceptions (401, 503, etc) with original status codes
        raise
    except Exception as e:
        logger.error(f"Error processing Teams message: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def teams_health():
    """Health check for Teams integration."""
    return {
        "status": "healthy",
        "service": "teams-bot",
        "bot_configured": simple_teams_bot.app_id is not None
    }


async def _store_conversation_reference(activity: Dict[str, Any], db: AsyncSession):
    """Store conversation reference for proactive messaging."""
    try:
        conversation_id = activity.get("conversation", {}).get("id")
        from_user = activity.get("from", {})
        
        # Check if conversation already exists
        result = await db.execute(
            select(TeamsConversation).where(
                TeamsConversation.conversation_id == conversation_id
            )
        )
        existing = result.scalar_one_or_none()
        
        if not existing:
            # Create new conversation record
            teams_conv = TeamsConversation(
                conversation_id=conversation_id,
                service_url=activity.get("serviceUrl", ""),
                tenant_id=activity.get("conversation", {}).get("tenantId"),
                channel_id=activity.get("channelId"),
                user_id=from_user.get("id", ""),
                user_name=from_user.get("name"),
                user_aad_object_id=from_user.get("aadObjectId"),
                conversation_reference=activity,  # Store full activity as reference
                last_message_at=activity.get("timestamp")
            )
            db.add(teams_conv)
            await db.commit()
            
            logger.info(f"Stored new Teams conversation: {conversation_id}")
        else:
            # Update last message timestamp
            existing.last_message_at = activity.get("timestamp")
            existing.conversation_reference = activity
            await db.commit()
            
    except Exception as e:
        logger.error(f"Error storing conversation reference: {e}", exc_info=True)


async def _log_teams_message(activity: Dict[str, Any], db: AsyncSession):
    """Log Teams message to database."""
    try:
        conversation_id = activity.get("conversation", {}).get("id")
        
        # Get teams_conversation_id
        result = await db.execute(
            select(TeamsConversation).where(
                TeamsConversation.conversation_id == conversation_id
            )
        )
        teams_conv = result.scalar_one_or_none()
        
        if teams_conv:
            message = TeamsMessage(
                teams_conversation_id=teams_conv.id,
                activity_id=activity.get("id"),
                message_type=activity.get("type", "message"),
                text=activity.get("text"),
                from_id=activity.get("from", {}).get("id", ""),
                from_name=activity.get("from", {}).get("name"),
                direction="incoming",
                activity_data=activity
            )
            db.add(message)
            await db.commit()
            
    except Exception as e:
        logger.error(f"Error logging Teams message: {e}", exc_info=True)


@router.post("/send-notification")
async def send_proactive_notification(
    notification_data: Dict[str, Any],
    db: AsyncSession = Depends(get_db)
):
    """
    Send proactive notification to Teams user.
    
    Request body:
    {
        "user_id": "teams_user_id",
        "notification_type": "approval_needed",
        "data": {...}
    }
    """
    try:
        user_id = notification_data.get("user_id")
        
        # Get conversation reference
        result = await db.execute(
            select(TeamsConversation).where(
                TeamsConversation.user_id == user_id,
                TeamsConversation.is_active == True
            )
        )
        teams_conv = result.scalar_one_or_none()
        
        if not teams_conv:
            raise HTTPException(status_code=404, detail="Teams conversation not found")
        
        # Send notification via adaptive card
        from app.services.teams_simple import SimpleTeamsBot
        bot = SimpleTeamsBot()
        
        # Create card based on notification type
        card = _create_notification_card(
            notification_data.get("notification_type"),
            notification_data.get("data", {})
        )
        
        success = await bot.send_adaptive_card(
            service_url=teams_conv.service_url,
            conversation_id=teams_conv.conversation_id,
            card_payload=card
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to send notification")
        
        return {"status": "sent", "conversation_id": str(teams_conv.id)}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending proactive notification: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


def _create_notification_card(notification_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Create adaptive card for notification."""
    if notification_type == "approval_needed":
        return {
            "type": "AdaptiveCard",
            "version": "1.4",
            "body": [
                {
                    "type": "TextBlock",
                    "text": "✅ Aprovação Necessária",
                    "weight": "Bolder",
                    "size": "Large"
                },
                {
                    "type": "TextBlock",
                    "text": data.get("message", ""),
                    "wrap": True
                }
            ],
            "actions": [
                {
                    "type": "Action.Submit",
                    "title": "Aprovar",
                    "data": {"action": "approve", "item_id": data.get("item_id")}
                },
                {
                    "type": "Action.Submit",
                    "title": "Rejeitar",
                    "data": {"action": "reject", "item_id": data.get("item_id")}
                }
            ]
        }
    
    # Default card
    return {
        "type": "AdaptiveCard",
        "version": "1.4",
        "body": [
            {
                "type": "TextBlock",
                "text": data.get("title", "Notificação"),
                "weight": "Bolder"
            },
            {
                "type": "TextBlock",
                "text": data.get("message", ""),
                "wrap": True
            }
        ]
    }
