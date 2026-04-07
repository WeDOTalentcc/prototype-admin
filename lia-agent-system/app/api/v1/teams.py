"""
Microsoft Teams webhook endpoints.

Includes:
- Message handling from Teams Bot Framework
- Adaptive Card action webhook for Teams → WhatsApp Screening connector
- Proactive notifications to Teams users
"""
import hashlib
import hmac
import json
import logging
import uuid
from datetime import datetime
from enum import Enum, StrEnum
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.domains.communication.services.teams_auth import bot_auth
from app.domains.communication.services.teams_simple import simple_teams_bot
from app.models.teams import TeamsActionAuditLog, TeamsConversation, TeamsMessage

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/teams", tags=["teams"])


class TeamsCardAction(StrEnum):
    """Supported Adaptive Card actions from Teams."""
    APPROVE = "approve"
    REJECT = "reject"
    SCHEDULE = "schedule"
    RESCHEDULE = "reschedule"
    REQUEST_INFO = "request_info"


class TeamsWebhookPayload(BaseModel):
    """Payload from Teams Adaptive Card action."""
    action: str = Field(..., description="Action type: approve, reject, schedule")
    candidate_id: str | None = Field(None, description="Candidate ID")
    candidate_name: str | None = Field(None, description="Candidate name")
    candidate_phone: str | None = Field(None, description="Candidate phone number")
    vacancy_id: str | None = Field(None, description="Job vacancy ID")
    vacancy_title: str | None = Field(None, description="Job vacancy title")
    company_id: str | None = Field(None, description="Company ID")
    recruiter_id: str | None = Field(None, description="Recruiter user ID who performed the action")
    recruiter_name: str | None = Field(None, description="Recruiter name")
    notes: str | None = Field(None, description="Optional notes from recruiter")
    scheduled_date: str | None = Field(None, description="Scheduled date for interviews")
    item_id: str | None = Field(None, description="Generic item ID for approvals")
    metadata: dict[str, Any] | None = Field(default_factory=dict, description="Additional metadata")
    
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
    audit_id: str | None = None
    candidate_id: str | None = None
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class TeamsActionAuditLogSchema(BaseModel):
    """Pydantic schema for Teams audit log response."""
    id: str = Field(..., description="Audit log ID")
    action: str
    actor_id: str | None = None
    actor_name: str | None = None
    candidate_id: str | None = None
    vacancy_id: str | None = None
    company_id: str | None = None
    source: str = "teams_adaptive_card"
    result: str
    details: dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


def _verify_teams_webhook_signature(payload: bytes, signature: str | None) -> bool:
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
    actor_id: str | None = None,
    actor_name: str | None = None,
    candidate_id: str | None = None,
    vacancy_id: str | None = None,
    company_id: str | None = None,
    details: dict[str, Any] | None = None,
    db: AsyncSession | None = None
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
    vacancy_id: str | None,
    vacancy_title: str | None,
    company_id: str | None,
    recruiter_name: str | None,
    db: AsyncSession
) -> dict[str, Any]:
    """
    Start WhatsApp screening for an approved candidate.
    
    Uses the CommunicationDispatcher to send screening invite via WhatsApp.
    """
    try:
        from app.domains.communication.services.communication_dispatcher import communication_dispatcher
        from app.domains.communication.services.communication_history_service import communication_history_service
        
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
                    company_id=company_id or None,
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
    x_teams_signature: str | None = Header(None, alias="X-Teams-Signature"),
    x_company_id: str | None = Header(None, alias="X-Company-ID"),
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


@router.get("/webhook/audit-logs", response_model=None)
async def get_teams_audit_logs(
    limit: int = 50,
    action: str | None = None,
    candidate_id: str | None = None,
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


@router.post("/messages", response_model=None)
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
    - File attachment (CV) is sent
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

        service_url = activity.get("serviceUrl")
        conversation_id = activity.get("conversation", {}).get("id")
        activity_id = activity.get("id")

        # Handle file attachments (CV uploads) first
        if activity.get("type") == "message":
            attachments = activity.get("attachments") or []
            file_attachments = [
                a for a in attachments
                if a.get("contentType") not in ("text/html",) and a.get("contentUrl")
            ]
            if file_attachments:
                try:
                    from app.domains.communication.services.teams_card_renderer import teams_card_renderer
                    from app.domains.communication.services.teams_orchestrator_bridge import teams_orchestrator_bridge

                    cv_result = await teams_orchestrator_bridge.process_cv_attachment(
                        activity, file_attachments[0], db=db
                    )
                    cv_card = teams_card_renderer.render(cv_result)
                    if cv_card:
                        await simple_teams_bot.send_adaptive_card(
                            service_url=service_url,
                            conversation_id=conversation_id,
                            card_payload=cv_card,
                        )
                    else:
                        await simple_teams_bot.send_message(
                            service_url=service_url,
                            conversation_id=conversation_id,
                            text=cv_result.get("message", "CV processado."),
                        )
                except Exception as cv_err:
                    logger.error(f"[Teams] CV attachment processing error: {cv_err}", exc_info=True)
                    await simple_teams_bot.send_message(
                        service_url=service_url,
                        conversation_id=conversation_id,
                        text="Erro ao processar o arquivo. Tente novamente.",
                    )
                await _store_conversation_reference(activity, db)
                await _log_teams_message(activity, db)
                return {"status": "ok"}

        # Process text message via orchestrator-backed bot
        response = await simple_teams_bot.process_activity(activity)

        if isinstance(response, dict) and response.get("type") == "card":
            await simple_teams_bot.send_adaptive_card(
                service_url=service_url,
                conversation_id=conversation_id,
                card_payload=response["card"],
            )
        elif isinstance(response, dict) and response.get("type") == "text":
            await simple_teams_bot.send_message(
                service_url=service_url,
                conversation_id=conversation_id,
                text=response["text"],
                reply_to_activity_id=activity_id if activity.get("type") == "message" else None,
            )
        elif isinstance(response, str):
            # Legacy plain string response
            await simple_teams_bot.send_message(
                service_url=service_url,
                conversation_id=conversation_id,
                text=response,
                reply_to_activity_id=activity_id if activity.get("type") == "message" else None,
            )
        elif isinstance(response, dict) and "messages" in response:
            # Multiple messages (for conversationUpdate welcome)
            for msg in response["messages"]:
                await simple_teams_bot.send_message(
                    service_url=service_url,
                    conversation_id=conversation_id,
                    text=msg["text"],
                )

        # Store conversation reference if this is a message
        if activity.get("type") == "message":
            await _store_conversation_reference(activity, db)

        # Log the message
        await _log_teams_message(activity, db)

        return {"status": "ok"}

    except HTTPException:
        # Re-raise HTTP exceptions (401, 503, etc) with original status codes
        raise
    except Exception as e:
        logger.error(f"Error processing Teams message: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


router.add_api_route(
    "/messages/",
    receive_teams_message,
    methods=["POST"],
    response_model=None,
    include_in_schema=False,
)


@router.get("/health", response_model=None)
async def teams_health():
    """Health check for Teams integration."""
    return {
        "status": "healthy",
        "service": "teams-bot",
        "bot_configured": simple_teams_bot.app_id is not None
    }


def _parse_teams_timestamp(ts: str | None) -> datetime | None:
    """Parse ISO 8601 timestamp string from Teams activity into datetime."""
    if not ts:
        return None
    try:
        # Teams sends e.g. "2026-04-07T01:23:01.5130745Z" — strip sub-second precision > 6 digits
        ts_clean = ts.rstrip("Z").split(".")[0]
        return datetime.fromisoformat(ts_clean)
    except Exception:
        return datetime.utcnow()


async def _store_conversation_reference(activity: dict[str, Any], db: AsyncSession):
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

        last_msg_at = _parse_teams_timestamp(activity.get("timestamp"))

        if not existing:
            teams_conv = TeamsConversation(
                conversation_id=conversation_id,
                service_url=activity.get("serviceUrl", ""),
                tenant_id=activity.get("conversation", {}).get("tenantId"),
                channel_id=activity.get("channelId"),
                user_id=from_user.get("id", ""),
                user_name=from_user.get("name"),
                user_aad_object_id=from_user.get("aadObjectId"),
                conversation_reference=activity,
                last_message_at=last_msg_at,
            )
            db.add(teams_conv)
            logger.info(f"Stored new Teams conversation: {conversation_id}")
        else:
            existing.last_message_at = last_msg_at
            existing.conversation_reference = activity

    except Exception as e:
        logger.error(f"Error storing conversation reference: {e}", exc_info=True)


async def _log_teams_message(activity: dict[str, Any], db: AsyncSession):
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
            
    except Exception as e:
        logger.error(f"Error logging Teams message: {e}", exc_info=True)


@router.post("/send-notification", response_model=None)
async def send_proactive_notification(
    notification_data: dict[str, Any],
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
                TeamsConversation.is_active
            )
        )
        teams_conv = result.scalar_one_or_none()
        
        if not teams_conv:
            raise HTTPException(status_code=404, detail="Teams conversation not found")
        
        # Send notification via adaptive card
        from app.domains.communication.services.teams_simple import SimpleTeamsBot
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


def _create_notification_card(notification_type: str, data: dict[str, Any]) -> dict[str, Any]:
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


@router.post("/proactive/check", response_model=None)
async def run_proactivity_checks(
    company_id: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """Run proactivity checks (stalled pipelines, deadlines). Call periodically."""
    try:
        from app.domains.communication.services.teams_proactivity_engine import teams_proactivity_engine
        stalled_sent = await teams_proactivity_engine.check_stalled_pipelines(company_id)
        deadlines_sent = await teams_proactivity_engine.check_approaching_deadlines(company_id)
        return {
            "stalled_notifications_sent": stalled_sent,
            "deadline_notifications_sent": deadlines_sent,
            "total": stalled_sent + deadlines_sent,
        }
    except Exception as e:
        logger.error(f"[Teams] proactivity check error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/proactive/new-candidate", response_model=None)
async def notify_new_candidate(
    candidate_id: str,
    candidate_name: str,
    vacancy_id: str,
    vacancy_title: str,
    company_id: str,
    estimated_score: float | None = None,
):
    """Notify recruiters when new candidate applies."""
    try:
        from app.domains.communication.services.teams_proactivity_engine import teams_proactivity_engine
        sent = await teams_proactivity_engine.on_candidate_applied(
            candidate_id=candidate_id,
            candidate_name=candidate_name,
            vacancy_id=vacancy_id,
            vacancy_title=vacancy_title,
            company_id=company_id,
            estimated_score=estimated_score,
        )
        return {"sent": sent}
    except Exception as e:
        logger.error(f"[Teams] notify_new_candidate error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/proactive/screening-complete", response_model=None)
async def notify_screening_complete(
    candidate_id: str,
    candidate_name: str,
    vacancy_id: str,
    job_title: str,
    match_score: float,
    recommendation: str,
    company_id: str,
    recruiter_teams_id: str | None = None,
):
    """Notify recruiters when a screening (WSI/BARS) completes."""
    try:
        from app.domains.communication.services.teams_proactivity_engine import teams_proactivity_engine
        sent = await teams_proactivity_engine.on_screening_complete(
            candidate_id=candidate_id,
            candidate_name=candidate_name,
            vacancy_id=vacancy_id,
            job_title=job_title,
            match_score=match_score,
            recommendation=recommendation,
            company_id=company_id,
            recruiter_teams_id=recruiter_teams_id,
        )
        return {"sent": sent}
    except Exception as e:
        logger.error(f"[Teams] notify_screening_complete error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/proactive/daily-digest", response_model=None)
async def send_daily_digest(
    company_id: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Trigger the daily digest card for all Teams recruiters.
    Should be called by a cron job at 08:00 every weekday.
    """
    from app.domains.communication.services.teams_proactivity_engine import teams_proactivity_engine
    sent = await teams_proactivity_engine.send_daily_digest(company_id=company_id)
    return {"sent": sent, "status": "ok"}


@router.post("/feedback", response_model=None)
async def receive_card_feedback(
    payload: dict[str, Any],
    db: AsyncSession = Depends(get_db),
):
    """
    Receive 👍👎 feedback from Teams Adaptive Card buttons.
    Logs the feedback for LIA quality improvement.
    """
    feedback_type = payload.get("feedback", "unknown")
    feedback_text = payload.get("feedback_text", "")
    user_id = payload.get("user_id", "unknown")
    logger.info(f"[Teams Feedback] type={feedback_type} user={user_id} text={feedback_text[:80]!r}")
    # TODO: persist to feedback table for LIA training
    return {"status": "received", "feedback": feedback_type}


# ============================================================================
# SSO — Azure AD Identity (Sprint Azure)
# ============================================================================

@router.get("/auth/sso-page", response_model=None)
async def teams_sso_page(
    conversation_id: str,
    client_id: str = "",
    tenant_id: str = "",
):
    """
    OAuth start page — user is redirected here when clicking "Conectar conta".
    Redirects to Azure AD consent page.
    """
    import os
    azure_client_id = client_id or os.environ.get("AZURE_CLIENT_ID", "")
    azure_tenant_id = tenant_id or os.environ.get("AZURE_TENANT_ID", "")
    platform_url = os.environ.get("WEDOTALENT_PLATFORM_URL", "https://app.wedotalent.com")
    redirect_uri = f"{platform_url}/api/v1/teams/auth/callback"

    if not azure_client_id or not azure_tenant_id:
        from fastapi.responses import HTMLResponse
        return HTMLResponse(
            "<h2>⚠️ Azure AD não configurado.</h2>"
            "<p>Defina AZURE_CLIENT_ID e AZURE_TENANT_ID nas variáveis de ambiente.</p>",
            status_code=503,
        )

    auth_url = (
        f"https://login.microsoftonline.com/{azure_tenant_id}/oauth2/v2.0/authorize"
        f"?client_id={azure_client_id}"
        f"&response_type=code"
        f"&redirect_uri={redirect_uri}"
        f"&scope=openid+profile+email+User.Read"
        f"&state={conversation_id}"
        f"&prompt=select_account"
    )

    from fastapi.responses import RedirectResponse
    return RedirectResponse(url=auth_url)


@router.get("/auth/callback", response_model=None)
async def teams_sso_callback(
    code: str = "",
    state: str = "",  # conversation_id
    error: str = "",
    db: AsyncSession = Depends(get_db),
):
    """
    OAuth callback — Azure AD redirects here after user signs in.
    Exchanges code for profile, maps identity, sends confirmation to Teams.
    """
    import os

    from fastapi.responses import HTMLResponse

    platform_url = os.environ.get("WEDOTALENT_PLATFORM_URL", "https://app.wedotalent.com")
    redirect_uri = f"{platform_url}/api/v1/teams/auth/callback"

    if error:
        return HTMLResponse(f"<h2>❌ Erro de autenticação: {error}</h2>", status_code=400)

    if not code:
        return HTMLResponse("<h2>❌ Código de autorização ausente.</h2>", status_code=400)

    try:
        from app.domains.communication.services.teams_sso_service import teams_sso_service
        profile = await teams_sso_service.exchange_auth_code(code, redirect_uri)

        if not profile:
            return HTMLResponse("<h2>❌ Falha ao obter perfil do Azure AD.</h2>", status_code=500)

        # state = conversation_id sent in the SSO page request
        conversation_id = state

        # Send confirmation card to the Teams conversation
        from app.domains.communication.services.teams_card_renderer import teams_card_renderer
        confirm_card = teams_card_renderer.render_notification_card(
            title="✅ Conta conectada!",
            body_text=(
                f"Olá, **{profile.get('display_name', 'Recrutador')}**! "
                f"Sua conta WeDOTalent foi conectada com sucesso. "
                f"Agora posso responder no contexto correto da sua empresa."
            ),
            actions=[
                {"type": "Action.Submit", "title": "☀️ Resumo do dia", "data": {"message": "Me dê um resumo das atividades de hoje"}},
                {"type": "Action.Submit", "title": "📋 Ver vagas", "data": {"message": "Quais são as vagas ativas?"}},
            ],
            color="#22C55E",
            emoji="✅",
        )

        # Try to send card to the conversation
        try:
            from app.domains.communication.services.teams_simple import simple_teams_bot
            await simple_teams_bot.send_adaptive_card(
                service_url="",  # Will need stored service_url
                conversation_id=conversation_id,
                card=confirm_card,
            )
        except Exception as send_err:
            logger.warning(f"[TeamsSSO] Could not send confirmation card: {send_err}")

        return HTMLResponse(
            f"""
            <html>
            <body style="font-family:sans-serif;text-align:center;padding:40px">
              <h1>✅ Autenticado com sucesso!</h1>
              <p>Olá, <strong>{profile.get("display_name","")}</strong>!</p>
              <p>Você pode fechar esta janela e voltar ao Teams.</p>
              <script>setTimeout(() => window.close(), 3000);</script>
            </body>
            </html>
            """,
            status_code=200,
        )

    except Exception as e:
        logger.error(f"[TeamsSSO] Callback error: {e}", exc_info=True)
        return HTMLResponse(f"<h2>❌ Erro interno: {str(e)}</h2>", status_code=500)


# ============================================================================
# Calendar — Interview Scheduling via Microsoft Graph
# ============================================================================

class ScheduleInterviewRequest(BaseModel):
    candidate_name: str
    vacancy_title: str
    recruiter_email: str
    candidate_email: str | None = None
    interview_date: str   # "2026-04-10"
    interview_time: str   # "14:00"
    duration: int = 60
    candidate_id: str | None = None
    vacancy_id: str | None = None
    notes: str | None = None


@router.post("/calendar/schedule", response_model=None)
async def schedule_interview_via_teams(
    request: ScheduleInterviewRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Schedule an interview via Microsoft Graph Calendar.
    Called from Teams card button (Action.Submit with action=schedule_interview)
    or directly from the orchestrator.

    Creates:
    - Outlook calendar event for recruiter (and candidate if email provided)
    - Teams Meeting link embedded in the event
    - Platform deep link in event description
    """
    from datetime import datetime

    from app.domains.communication.services.teams_calendar_service import teams_calendar_service

    try:
        dt_str = f"{request.interview_date}T{request.interview_time}:00"
        start_time = datetime.fromisoformat(dt_str)
    except ValueError:
        raise HTTPException(status_code=400, detail="Data/hora inválida. Use formato YYYY-MM-DD e HH:MM.")

    title = f"Entrevista — {request.candidate_name}"
    if request.vacancy_title:
        title += f" ({request.vacancy_title})"

    result = await teams_calendar_service.schedule_interview(
        title=title,
        recruiter_email=request.recruiter_email,
        candidate_name=request.candidate_name,
        candidate_email=request.candidate_email,
        start_time=start_time,
        duration_minutes=request.duration,
        vacancy_title=request.vacancy_title,
        candidate_id=request.candidate_id,
        vacancy_id=request.vacancy_id,
        notes=request.notes,
    )
    return result


@router.post("/calendar/cancel", response_model=None)
async def cancel_interview_via_teams(
    event_id: str,
    organizer_email: str,
    message: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """Cancel a previously scheduled interview event."""
    from app.domains.communication.services.teams_calendar_service import teams_calendar_service
    return await teams_calendar_service.cancel_interview(
        event_id=event_id,
        organizer_email=organizer_email,
        cancellation_message=message,
    )


# ============================================================================
# Teams App Manifest — generate manifest.json for Teams App Studio
# ============================================================================

@router.get("/manifest", response_model=None)
async def get_teams_manifest():
    """
    Generate and return the Teams app manifest.json.
    Download this file and upload to Teams Admin Center / App Studio.

    Requires env vars:
      TEAMS_APP_ID        — generate a UUID for your app
      TEAMS_BOT_APP_ID    — Microsoft App ID of the bot
      AZURE_CLIENT_ID     — for SSO
      WEDOTALENT_PLATFORM_URL — e.g. https://app.wedotalent.com
    """
    import os
    import uuid

    from fastapi.responses import JSONResponse

    platform_url = os.environ.get("WEDOTALENT_PLATFORM_URL", "https://app.wedotalent.com").rstrip("/")
    try:
        from urllib.parse import urlparse
        platform_domain = urlparse(platform_url).netloc
    except Exception:
        platform_domain = "app.wedotalent.com"

    manifest = {
        "$schema": "https://developer.microsoft.com/en-us/json-schemas/teams/v1.17/MicrosoftTeams.schema.json",
        "manifestVersion": "1.17",
        "version": "1.0.0",
        "id": os.environ.get("TEAMS_APP_ID", str(uuid.uuid4())),
        "packageName": "com.wedotalent.wedo",
        "developer": {
            "name": "WeDOTalent",
            "websiteUrl": platform_url,
            "privacyUrl": f"{platform_url}/privacy",
            "termsOfUseUrl": f"{platform_url}/terms",
        },
        "icons": {"color": f"{platform_url}/teams-icons/wedo-color.png", "outline": f"{platform_url}/teams-icons/wedo-outline.png"},
        "name": {"short": "WeDO", "full": "WeDOTalent — Recrutamento Inteligente"},
        "description": {
            "short": "Plataforma de recrutamento com IA",
            "full": "WeDOTalent conecta recrutadores à LIA, a assistente de IA para busca de candidatos, triagem, agendamento e relatórios — direto no Teams.",
        },
        "accentColor": "#000000",
        "bots": [{
            "botId": os.environ.get("TEAMS_BOT_APP_ID", os.environ.get("TEAMS_APP_ID", "")),
            "scopes": ["personal", "team", "groupChat"],
            "supportsFiles": True,
            "isNotificationOnly": False,
            "commandLists": [{
                "scopes": ["personal", "team", "groupChat"],
                "commands": [
                    {"title": "ajuda",      "description": "Ver todas as funcionalidades da LIA"},
                    {"title": "buscar",     "description": "Buscar candidatos para uma vaga"},
                    {"title": "triagem",    "description": "Ver candidatos aguardando triagem WSI"},
                    {"title": "relatorio",  "description": "Gerar relatório semanal de recrutamento"},
                    {"title": "pipeline",   "description": "Ver saúde do pipeline de recrutamento"},
                    {"title": "vagas",      "description": "Ver vagas ativas e seus status"},
                    {"title": "candidatos", "description": "Ver candidatos aguardando retorno"},
                    {"title": "resumo",     "description": "Resumo das atividades do dia"},
                ],
            }],
        }],
        "staticTabs": [
            {"entityId": "tab-vagas",      "name": "Vagas",       "contentUrl": f"{platform_url}/teams-tab/vagas",      "websiteUrl": f"{platform_url}/vagas",      "scopes": ["personal"]},
            {"entityId": "tab-candidatos", "name": "Candidatos",  "contentUrl": f"{platform_url}/teams-tab/candidatos", "websiteUrl": f"{platform_url}/candidatos", "scopes": ["personal"]},
            {"entityId": "tab-pipeline",   "name": "Pipeline",    "contentUrl": f"{platform_url}/teams-tab/pipeline",   "websiteUrl": f"{platform_url}/pipeline",   "scopes": ["personal"]},
            {"entityId": "tab-dashboard",  "name": "Dashboard",   "contentUrl": f"{platform_url}/teams-tab/dashboard",  "websiteUrl": f"{platform_url}/dashboard",  "scopes": ["personal"]},
        ],
        "configurableTabs": [{
            "configurationUrl": f"{platform_url}/teams-tab/configure",
            "canUpdateConfiguration": True,
            "scopes": ["team", "groupChat"],
        }],
        "permissions": ["identity", "messageTeamMembers"],
        "validDomains": [platform_domain, "token.botframework.com", "login.microsoftonline.com"],
        "webApplicationInfo": {
            "id": os.environ.get("AZURE_CLIENT_ID", ""),
            "resource": f"api://{platform_domain}/{os.environ.get('AZURE_CLIENT_ID', '')}",
        },
        "authorization": {
            "permissions": {
                "resourceSpecific": [
                    {"name": "ChannelMessage.Read.Group",  "type": "Application"},
                    {"name": "ChatMessage.Read.Chat",      "type": "Application"},
                    {"name": "TeamSettings.Read.Group",    "type": "Delegated"},
                ]
            }
        },
    }

    return JSONResponse(
        content=manifest,
        headers={"Content-Disposition": "attachment; filename=manifest.json"},
    )


# ================================================================== #
# Teams Tab endpoints (Approach 2: SSO + behavioral tracking)
# ================================================================== #

class TabAuthRequest(BaseModel):
    """SSO token from Teams SDK sent by the iframe."""
    sso_token: str = Field(..., description="JWT from Teams authentication.getAuthToken()")


class TabAuthResponse(BaseModel):
    """Platform JWT for authenticated API calls from the iframe."""
    access_token: str
    user_id: str
    email: str
    company_id: str
    teams_user_id: str | None = None


class TabEventRequest(BaseModel):
    """Behavioral event from the Teams Tab tracker hook."""
    event_type: str = Field(..., description="e.g. click_create_job, prolonged_stay")
    entity_type: str | None = Field(None, description="e.g. job, candidate")
    entity_id: str | None = Field(None, description="ID of the entity being acted on")
    teams_user_id: str | None = Field(None, description="AAD object ID of the tab user")
    platform_user_id: str | None = Field(None, description="WeDOTalent user UUID")
    context: dict[str, Any] | None = Field(default_factory=dict)


@router.post("/tab/auth", response_model=TabAuthResponse)
async def teams_tab_auth(
    payload: TabAuthRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Validate a Teams Tab SSO token and return a platform access token.

    Flow:
    1. Receive the JWT from Teams SDK `authentication.getAuthToken()`
    2. Exchange it with Azure AD for an access token (OBO flow)
    3. Fetch Graph /me to get AAD object ID + email
    4. Look up or create the matching WeDOTalent user
    5. Return a platform JWT so the iframe can call protected APIs
    """
    import os

    import httpx
    from sqlalchemy import select

    from app.auth.models import User

    azure_client_id = os.environ.get("AZURE_CLIENT_ID", "")
    azure_client_secret = os.environ.get("AZURE_CLIENT_SECRET", "")
    azure_tenant_id = os.environ.get("AZURE_TENANT_ID", "")

    if not (azure_client_id and azure_client_secret and azure_tenant_id):
        # SSO not configured — return a minimal guest token for dev
        logger.warning("[TeamsTabAuth] Azure not configured, returning guest token")
        return TabAuthResponse(
            access_token="dev-fallback-token",
            user_id="dev-user",
            email="dev@wedotalent.com",
            company_id=None,
        )

    try:
        # OBO (On-Behalf-Of) flow: exchange Teams SSO token for Graph token
        token_url = f"https://login.microsoftonline.com/{azure_tenant_id}/oauth2/v2.0/token"
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(token_url, data={
                "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
                "client_id": azure_client_id,
                "client_secret": azure_client_secret,
                "assertion": payload.sso_token,
                "requested_token_use": "on_behalf_of",
                "scope": "https://graph.microsoft.com/User.Read openid profile email",
            })
            token_data = resp.json()

        graph_token = token_data.get("access_token")
        if not graph_token:
            logger.error(f"[TeamsTabAuth] OBO exchange failed: {token_data}")
            raise HTTPException(status_code=401, detail="Invalid SSO token")

        # Fetch user profile from Graph
        async with httpx.AsyncClient(timeout=10) as client:
            me_resp = await client.get(
                "https://graph.microsoft.com/v1.0/me",
                headers={"Authorization": f"Bearer {graph_token}"},
            )
            profile = me_resp.json()

        aad_object_id: str = profile.get("id", "")
        email: str = profile.get("mail") or profile.get("userPrincipalName") or ""
        profile.get("displayName") or email

        if not aad_object_id or not email:
            raise HTTPException(status_code=401, detail="Could not retrieve user profile from Azure AD")

        # Look up WeDOTalent user by AAD object ID first, then email
        user: User | None = None
        stmt = select(User).where(User.azure_ad_object_id == aad_object_id).limit(1)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            stmt = select(User).where(User.email == email).limit(1)
            result = await db.execute(stmt)
            user = result.scalar_one_or_none()
            if user and not user.azure_ad_object_id:
                # Backfill AAD ID
                user.azure_ad_object_id = aad_object_id
                db.add(user)

        if not user:
            raise HTTPException(
                status_code=404,
                detail=f"No WeDOTalent account found for {email}. Ask your admin to invite you.",
            )

        # Generate a platform JWT (reuse existing auth service if available)
        from app.core.security import create_access_token
        platform_token = create_access_token(subject=str(user.id), company_id=getattr(user, "company_id", None))

        logger.info(f"[TeamsTabAuth] SSO resolved: AAD={aad_object_id} → user={user.id}")
        return TabAuthResponse(
            access_token=platform_token,
            user_id=str(user.id),
            email=user.email,
            company_id=str(user.company_id) if user.company_id else "",
            teams_user_id=aad_object_id,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[TeamsTabAuth] Unexpected error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="SSO authentication failed")


@router.post("/tab/events", response_model=None)
async def teams_tab_events(
    payload: TabEventRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Receive a behavioral event from the Teams Tab iframe tracker.

    If the event represents a complex action, sends a proactive Adaptive
    Card to the recruiter's Teams chat with a deep link to the platform.
    """
    from sqlalchemy import select

    from app.domains.communication.services.teams_simple import SimpleTeamsBot
    from app.domains.communication.services.teams_tab_trigger import get_trigger_engine

    engine = get_trigger_engine()
    card = engine.evaluate(
        event_type=payload.event_type,
        entity_id=payload.entity_id,
        context=payload.context,
    )

    if card is None:
        return {"status": "ignored", "event_type": payload.event_type}

    # Find conversation reference for this Teams user
    teams_user_id = payload.teams_user_id
    if not teams_user_id and payload.platform_user_id:
        # Look up AAD object ID from User record
        try:
            from app.auth.models import User
            stmt = select(User).where(User.id == payload.platform_user_id).limit(1)
            result = await db.execute(stmt)
            user = result.scalar_one_or_none()
            if user and user.azure_ad_object_id:
                teams_user_id = user.azure_ad_object_id
        except Exception as e:
            logger.warning(f"[TeamsTabEvents] Could not resolve platform_user_id: {e}")

    if not teams_user_id:
        logger.warning(f"[TeamsTabEvents] No teams_user_id for event '{payload.event_type}' — cannot send proactive")
        return {"status": "no_teams_identity", "event_type": payload.event_type}

    # Find TeamsConversation by user_aad_object_id
    stmt = select(TeamsConversation).where(
        TeamsConversation.user_aad_object_id == teams_user_id,
        TeamsConversation.is_active,
    ).limit(1)
    result = await db.execute(stmt)
    conv = result.scalar_one_or_none()

    if not conv:
        logger.warning(f"[TeamsTabEvents] No active TeamsConversation for AAD user '{teams_user_id}'")
        return {"status": "no_conversation", "event_type": payload.event_type}

    # Send proactive Adaptive Card
    bot = SimpleTeamsBot()
    success = await bot.send_adaptive_card(
        service_url=conv.service_url,
        conversation_id=conv.conversation_id,
        card_payload=card,
    )

    if not success:
        logger.error(f"[TeamsTabEvents] Failed to send card for event '{payload.event_type}'")
        return {"status": "send_failed", "event_type": payload.event_type}

    logger.info(f"[TeamsTabEvents] Proactive card sent for event='{payload.event_type}', user='{teams_user_id}'")
    return {"status": "sent", "event_type": payload.event_type}
