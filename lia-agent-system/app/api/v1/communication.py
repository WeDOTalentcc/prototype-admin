"""
Communication API Endpoints using CommunicationDispatcher

Provides endpoints for sending email and WhatsApp messages via the unified dispatcher.
Logs all communications to the CommunicationHistory for tracking.
"""
from fastapi import APIRouter, HTTPException, status, Header, Depends
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
import uuid as uuid_mod

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, not_

from app.services.communication_dispatcher import communication_dispatcher
from app.services.communication_history_service import communication_history_service
from app.core.database import get_db
from app.models.job_vacancy import JobVacancy
from app.models.candidate import VacancyCandidate
from app.models.company import CompanyProfile
from app.shared.pii_masking import get_masked_logger
from app.shared.compliance.audit_service import audit_service

logger = get_masked_logger(__name__)

router = APIRouter(prefix="/communication", tags=["communication"])

EXCLUDED_STATUSES = ('rejected', 'declined', 'withdrawn')
ORGANIC_ORIGINS = ('web', 'whatsapp')
SOURCING_ORIGINS = ('sourcing', 'ats')
DEFAULT_SATURATION_THRESHOLD = 20


async def _check_vacancy_saturation_for_invite(db: AsyncSession, vacancy_id: str) -> dict:
    try:
        vid = uuid_mod.UUID(vacancy_id)
    except (ValueError, TypeError):
        return {"is_saturated": False, "error": "invalid_vacancy_id"}

    result = await db.execute(select(JobVacancy).where(JobVacancy.id == vid))
    vacancy = result.scalar_one_or_none()
    if not vacancy:
        return {"is_saturated": False, "error": "vacancy_not_found"}

    company = None
    try:
        cr = await db.execute(
            select(CompanyProfile).where(CompanyProfile.id == vacancy.company_id)
        )
        company = cr.scalar_one_or_none()
    except Exception:
        pass
    if not company:
        cr2 = await db.execute(
            select(CompanyProfile).where(CompanyProfile.is_default == True).limit(1)
        )
        company = cr2.scalar_one_or_none()

    sat = {}
    if company and company.additional_data:
        sat = company.additional_data.get("saturation_settings", {})

    governance_rules = vacancy.governance_rules or {}
    threshold_web = governance_rules.get("threshold_web", sat.get("threshold_web", DEFAULT_SATURATION_THRESHOLD))
    threshold_sourcing = governance_rules.get("threshold_sourcing", sat.get("threshold_sourcing", DEFAULT_SATURATION_THRESHOLD))

    disabled_until_str = governance_rules.get("saturation_disabled_until")
    bypass_active = False
    if disabled_until_str:
        try:
            disabled_until = datetime.fromisoformat(disabled_until_str)
            if disabled_until > datetime.utcnow():
                bypass_active = True
        except (ValueError, TypeError):
            pass

    active_filter = and_(
        VacancyCandidate.vacancy_id == vid,
        not_(VacancyCandidate.status.in_(EXCLUDED_STATUSES)),
    )
    channel_result = await db.execute(
        select(
            func.count(VacancyCandidate.id).filter(
                VacancyCandidate.origin.in_(ORGANIC_ORIGINS) | VacancyCandidate.origin.is_(None)
            ).label("organic"),
            func.count(VacancyCandidate.id).filter(
                VacancyCandidate.origin.in_(SOURCING_ORIGINS)
            ).label("sourcing"),
        ).where(active_filter)
    )
    row = channel_result.one()
    organic_count = row.organic or 0
    sourcing_count = row.sourcing or 0

    organic_saturated = organic_count >= threshold_web and not bypass_active
    sourcing_saturated = sourcing_count >= threshold_sourcing and not bypass_active
    is_saturated = organic_saturated or sourcing_saturated

    return {
        "is_saturated": is_saturated,
        "bypass_active": bypass_active,
        "organic_count": organic_count,
        "sourcing_count": sourcing_count,
        "threshold_web": threshold_web,
        "threshold_sourcing": threshold_sourcing,
        "organic_saturated": organic_saturated,
        "sourcing_saturated": sourcing_saturated,
    }


class SendEmailRequest(BaseModel):
    to_email: str = Field(..., description="Recipient email address")
    to_name: Optional[str] = Field(None, description="Recipient name")
    subject: str = Field(..., description="Email subject")
    body_html: str = Field(..., description="Email body in HTML format")
    body_text: Optional[str] = Field(None, description="Plain text body fallback")
    candidate_id: Optional[str] = Field(None, description="Candidate ID for tracking")
    candidate_name: Optional[str] = Field(None, description="Candidate name")
    vacancy_id: Optional[str] = Field(None, description="Vacancy ID")
    vacancy_title: Optional[str] = Field(None, description="Vacancy title")
    communication_type: Optional[str] = Field("email", description="Type of communication")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    company_id: Optional[str] = Field(None, description="Company ID for multi-tenancy")


class SendWhatsAppRequest(BaseModel):
    to_phone: str = Field(..., description="Recipient phone number with country code")
    message: str = Field(..., description="Message content")
    candidate_id: Optional[str] = Field(None, description="Candidate ID for tracking")
    candidate_name: Optional[str] = Field(None, description="Candidate name")
    vacancy_id: Optional[str] = Field(None, description="Vacancy ID")
    vacancy_title: Optional[str] = Field(None, description="Vacancy title")
    communication_type: Optional[str] = Field("whatsapp", description="Type of communication")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    company_id: Optional[str] = Field(None, description="Company ID for multi-tenancy")


class SendScreeningInviteRequest(BaseModel):
    channel: str = Field(..., description="Communication channel: email, whatsapp, or telefone")
    candidate_id: str = Field(..., description="Candidate ID")
    candidate_name: str = Field(..., description="Candidate name")
    candidate_email: Optional[str] = Field(None, description="Candidate email")
    candidate_phone: Optional[str] = Field(None, description="Candidate phone")
    subject: Optional[str] = Field(None, description="Email subject (for email channel)")
    message: str = Field(..., description="Message content")
    vacancy_id: Optional[str] = Field(None, description="Vacancy ID")
    vacancy_title: Optional[str] = Field(None, description="Vacancy title")
    screening_question_ids: Optional[list] = Field(None, description="List of screening question IDs")
    stage: Optional[str] = Field("triagem", description="Pipeline stage")
    tone_style: Optional[str] = Field("profissional", description="Message tone style")
    company_id: Optional[str] = Field(None, description="Company ID for multi-tenancy")
    override_saturation: bool = Field(False, description="Override saturation guardrail (manual approval)")


class ScreeningInviteResponse(BaseModel):
    success: bool
    message_id: Optional[str] = None
    mock: bool = False
    channel: str
    recipient: str
    error: Optional[str] = None
    timestamp: Optional[str] = None
    communication_logged: bool = False
    invite_type: str = "screening"


class SendResponse(BaseModel):
    success: bool
    message_id: Optional[str] = None
    mock: bool = False
    channel: str
    recipient: str
    error: Optional[str] = None
    timestamp: Optional[str] = None
    communication_logged: bool = False


@router.post("/send-email", response_model=SendResponse, status_code=status.HTTP_200_OK)
async def send_email(
    request: SendEmailRequest,
    x_company_id: Optional[str] = Header(None, alias="X-Company-ID")
):
    """
    Send an email via the CommunicationDispatcher (SendGrid).
    
    - Uses SendGrid when configured
    - Falls back to mock success in development when API keys not set
    - Logs the communication to CommunicationHistory
    """
    try:
        company_id = x_company_id or request.company_id or "default"
        
        logger.info(f"📧 Sending email to {request.to_email} for company {company_id}")
        
        result = communication_dispatcher.send_email(
            to_email=request.to_email,
            subject=request.subject,
            body_html=request.body_html,
            body_text=request.body_text,
            from_name=request.to_name,
        )
        
        communication_logged = False
        if result.get("success"):
            try:
                await communication_history_service.log_communication(
                    candidate_id=request.candidate_id,
                    candidate_name=request.candidate_name or request.to_name,
                    candidate_email=request.to_email,
                    candidate_phone=None,
                    vacancy_id=request.vacancy_id,
                    vacancy_title=request.vacancy_title,
                    communication_type=request.communication_type or "email",
                    channel="email",
                    direction="outbound",
                    subject=request.subject,
                    message_content=request.body_text or request.body_html,
                    sent_by="recruiter",
                    company_id=company_id,
                    extra_data={
                        "message_id": result.get("message_id"),
                        "mock": result.get("mock", False),
                        **(request.metadata or {})
                    },
                )
                communication_logged = True
                logger.info(f"✅ Communication logged for email to {request.to_email}")
            except Exception as log_error:
                logger.warning(f"⚠️ Failed to log communication: {log_error}")
        
        _masked_recipient = (request.to_email or "")[:3] + "***" if request.to_email else "unknown"
        if result.get("success"):
            try:
                await audit_service.log_decision(
                    company_id=company_id,
                    agent_name="communication_module",
                    decision_type="send_message",
                    action="send_email",
                    decision="sent",
                    reasoning=[
                        "Email communication dispatched",
                        f"Type: {request.communication_type or 'email'}",
                        f"Send result: {result.get('message_id', 'N/A')}",
                        f"Template: {getattr(request, 'template_id', 'custom') or 'custom'}",
                        f"Recipient: {_masked_recipient}",
                    ],
                    criteria_used=["recipient_validation", "template_selection", "channel_availability"],
                    candidate_id=request.candidate_id,
                    job_vacancy_id=request.vacancy_id,
                    human_review_required=False,
                )
            except Exception as audit_err:
                logger.warning(f"Audit log failed for send_email: {audit_err}")
        else:
            try:
                await audit_service.log_decision(
                    company_id=company_id,
                    agent_name="communication_module",
                    decision_type="send_message",
                    action="send_email",
                    decision="failed",
                    reasoning=[
                        "Email dispatch failed",
                        f"Error: {result.get('error', 'unknown')}",
                        f"Recipient: {_masked_recipient}",
                    ],
                    criteria_used=["recipient_validation", "channel_availability"],
                    candidate_id=request.candidate_id,
                    job_vacancy_id=request.vacancy_id,
                    human_review_required=False,
                )
            except Exception as audit_err:
                logger.warning(f"Audit log failed for send_email failure: {audit_err}")

        return SendResponse(
            success=result.get("success", False),
            message_id=result.get("message_id"),
            mock=result.get("mock", False),
            channel="email",
            recipient=request.to_email,
            error=result.get("error"),
            timestamp=result.get("timestamp"),
            communication_logged=communication_logged,
        )
        
    except Exception as e:
        logger.error(f"❌ Error sending email: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send email: {str(e)}"
        )


@router.post("/send-whatsapp", response_model=SendResponse, status_code=status.HTTP_200_OK)
async def send_whatsapp(
    request: SendWhatsAppRequest,
    x_company_id: Optional[str] = Header(None, alias="X-Company-ID")
):
    """
    Send a WhatsApp message via the CommunicationDispatcher (Twilio).
    
    - Uses Twilio when configured
    - Falls back to mock success in development when API keys not set
    - Logs the communication to CommunicationHistory
    """
    try:
        company_id = x_company_id or request.company_id or "default"
        
        logger.info(f"📱 Sending WhatsApp to {request.to_phone} for company {company_id}")
        
        result = communication_dispatcher.send_whatsapp(
            to_phone=request.to_phone,
            message=request.message,
        )
        
        communication_logged = False
        if result.get("success"):
            try:
                await communication_history_service.log_communication(
                    candidate_id=request.candidate_id,
                    candidate_name=request.candidate_name,
                    candidate_email=None,
                    candidate_phone=request.to_phone,
                    vacancy_id=request.vacancy_id,
                    vacancy_title=request.vacancy_title,
                    communication_type=request.communication_type or "whatsapp",
                    channel="whatsapp",
                    direction="outbound",
                    subject=None,
                    message_content=request.message,
                    sent_by="recruiter",
                    company_id=company_id,
                    extra_data={
                        "message_id": result.get("message_id"),
                        "mock": result.get("mock", False),
                        **(request.metadata or {})
                    },
                )
                communication_logged = True
                logger.info(f"✅ Communication logged for WhatsApp to {request.to_phone}")
            except Exception as log_error:
                logger.warning(f"⚠️ Failed to log communication: {log_error}")
        
        _masked_phone = (request.to_phone or "")[:4] + "***" if request.to_phone else "unknown"
        if result.get("success"):
            try:
                await audit_service.log_decision(
                    company_id=company_id,
                    agent_name="communication_module",
                    decision_type="send_message",
                    action="send_whatsapp",
                    decision="sent",
                    reasoning=[
                        "WhatsApp communication dispatched",
                        f"Type: {request.communication_type or 'whatsapp'}",
                        f"Send result: {result.get('message_id', 'N/A')}",
                        f"Template: {getattr(request, 'template_id', 'custom') or 'custom'}",
                        f"Recipient: {_masked_phone}",
                    ],
                    criteria_used=["recipient_validation", "message_content", "channel_availability"],
                    candidate_id=request.candidate_id,
                    job_vacancy_id=request.vacancy_id,
                    human_review_required=False,
                )
            except Exception as audit_err:
                logger.warning(f"Audit log failed for send_whatsapp: {audit_err}")
        else:
            try:
                await audit_service.log_decision(
                    company_id=company_id,
                    agent_name="communication_module",
                    decision_type="send_message",
                    action="send_whatsapp",
                    decision="failed",
                    reasoning=[
                        "WhatsApp dispatch failed",
                        f"Error: {result.get('error', 'unknown')}",
                        f"Recipient: {_masked_phone}",
                    ],
                    criteria_used=["recipient_validation", "channel_availability"],
                    candidate_id=request.candidate_id,
                    job_vacancy_id=request.vacancy_id,
                    human_review_required=False,
                )
            except Exception as audit_err:
                logger.warning(f"Audit log failed for send_whatsapp failure: {audit_err}")

        return SendResponse(
            success=result.get("success", False),
            message_id=result.get("message_id"),
            mock=result.get("mock", False),
            channel="whatsapp",
            recipient=request.to_phone,
            error=result.get("error"),
            timestamp=result.get("timestamp"),
            communication_logged=communication_logged,
        )
        
    except Exception as e:
        logger.error(f"❌ Error sending WhatsApp: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send WhatsApp message: {str(e)}"
        )


@router.post("/send-screening-invite", response_model=ScreeningInviteResponse, status_code=status.HTTP_200_OK)
async def send_screening_invite(
    request: SendScreeningInviteRequest,
    x_company_id: Optional[str] = Header(None, alias="X-Company-ID"),
    db: AsyncSession = Depends(get_db),
):
    """
    Send a WSI (Work Sample Interview) screening invite to a candidate.
    
    Supports email and WhatsApp channels:
    - Email: Uses SendGrid via CommunicationDispatcher
    - WhatsApp: Uses Twilio via CommunicationDispatcher
    - Telefone: Logs the script for phone call (no actual call made)
    
    Checks saturation guardrail before sending — blocks if pipeline is saturated
    unless override_saturation is True (manual recruiter approval).
    
    All invitations are logged to CommunicationHistory for tracking.
    """
    try:
        company_id = x_company_id or request.company_id or "default"
        channel = request.channel.lower()
        
        logger.info(f"Sending screening invite via {channel} to {request.candidate_name} for company {company_id}")

        if request.vacancy_id and not request.override_saturation:
            sat_status = await _check_vacancy_saturation_for_invite(db, request.vacancy_id)
            if sat_status.get("is_saturated"):
                detail_parts = []
                if sat_status.get("organic_saturated"):
                    detail_parts.append(
                        f"organic {sat_status['organic_count']}/{sat_status['threshold_web']}"
                    )
                if sat_status.get("sourcing_saturated"):
                    detail_parts.append(
                        f"sourcing {sat_status['sourcing_count']}/{sat_status['threshold_sourcing']}"
                    )
                detail_msg = ", ".join(detail_parts)
                logger.warning(
                    f"Screening invite blocked by saturation for vacancy {request.vacancy_id}: {detail_msg}"
                )
                raise HTTPException(
                    status_code=409,
                    detail={
                        "error": "saturation_limit_reached",
                        "message": f"Pipeline saturado ({detail_msg}). Convite de triagem bloqueado. Use override_saturation=true para aprovar manualmente.",
                        "organic_count": sat_status["organic_count"],
                        "organic_threshold": sat_status["threshold_web"],
                        "sourcing_count": sat_status["sourcing_count"],
                        "sourcing_threshold": sat_status["threshold_sourcing"],
                    },
                )
        elif request.vacancy_id and request.override_saturation:
            logger.info(f"Saturation override active for screening invite to {request.candidate_name}")
        
        result = {
            "success": False,
            "message_id": None,
            "mock": False,
            "channel": channel,
            "recipient": "",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if channel == "email":
            if not request.candidate_email:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email address is required for email channel"
                )
            
            result = communication_dispatcher.send_email(
                to_email=request.candidate_email,
                subject=request.subject or f"Convite para Triagem - {request.vacancy_title or 'Vaga'}",
                body_html=request.message.replace("\n", "<br>"),
                body_text=request.message,
                from_name="LIA Recrutamento"
            )
            result["recipient"] = request.candidate_email
            
        elif channel == "whatsapp":
            if not request.candidate_phone:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Phone number is required for WhatsApp channel"
                )
            
            result = communication_dispatcher.send_whatsapp(
                to_phone=request.candidate_phone,
                message=request.message
            )
            result["recipient"] = request.candidate_phone
            
        elif channel == "telefone":
            import uuid
            result = {
                "success": True,
                "message_id": f"phone-script-{uuid.uuid4().hex[:12]}",
                "mock": True,
                "channel": "telefone",
                "recipient": request.candidate_phone or "N/A",
                "timestamp": datetime.utcnow().isoformat()
            }
            logger.info(f"📞 Phone script prepared for {request.candidate_name}")
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid channel: {channel}. Must be 'email', 'whatsapp', or 'telefone'"
            )
        
        communication_logged = False
        if result.get("success"):
            try:
                await communication_history_service.log_communication(
                    candidate_id=request.candidate_id,
                    candidate_name=request.candidate_name,
                    candidate_email=request.candidate_email,
                    candidate_phone=request.candidate_phone,
                    vacancy_id=request.vacancy_id,
                    vacancy_title=request.vacancy_title,
                    communication_type="screening_invite",
                    channel=channel,
                    direction="outbound",
                    subject=request.subject,
                    message_content=request.message,
                    sent_by="recruiter",
                    company_id=company_id,
                    extra_data={
                        "message_id": result.get("message_id"),
                        "mock": result.get("mock", False),
                        "invite_type": "wsi_screening",
                        "screening_question_ids": request.screening_question_ids,
                        "stage": request.stage,
                        "tone_style": request.tone_style,
                    },
                )
                communication_logged = True
                logger.info(f"✅ Screening invite logged for {request.candidate_name} via {channel}")
            except Exception as log_error:
                logger.warning(f"⚠️ Failed to log screening invite: {log_error}")
        
        _masked_invite_recipient = (request.candidate_name or "")[:3] + "***" if request.candidate_name else "unknown"
        if result.get("success"):
            try:
                await audit_service.log_decision(
                    company_id=company_id,
                    agent_name="communication_module",
                    decision_type="send_message",
                    action="send_screening_invite",
                    decision="sent",
                    reasoning=[
                        "WSI screening invite dispatched",
                        f"Channel: {channel}",
                        f"Send result: {result.get('message_id', 'N/A')}",
                        f"Mock: {result.get('mock', False)}",
                        f"Override saturation: {request.override_saturation}",
                        f"Recipient: {_masked_invite_recipient}",
                    ],
                    criteria_used=["recipient_validation", "saturation_check", "channel_availability", "vacancy_active"],
                    candidate_id=request.candidate_id,
                    job_vacancy_id=request.vacancy_id,
                    human_review_required=False,
                )
            except Exception as audit_err:
                logger.warning(f"Audit log failed for send_screening_invite: {audit_err}")
        else:
            try:
                await audit_service.log_decision(
                    company_id=company_id,
                    agent_name="communication_module",
                    decision_type="send_message",
                    action="send_screening_invite",
                    decision="failed",
                    reasoning=[
                        "Screening invite dispatch failed",
                        f"Channel: {channel}",
                        f"Error: {result.get('error', 'unknown')}",
                        f"Recipient: {_masked_invite_recipient}",
                    ],
                    criteria_used=["recipient_validation", "saturation_check", "channel_availability"],
                    candidate_id=request.candidate_id,
                    job_vacancy_id=request.vacancy_id,
                    human_review_required=False,
                )
            except Exception as audit_err:
                logger.warning(f"Audit log failed for send_screening_invite failure: {audit_err}")

        return ScreeningInviteResponse(
            success=result.get("success", False),
            message_id=result.get("message_id"),
            mock=result.get("mock", False),
            channel=channel,
            recipient=result.get("recipient", ""),
            error=result.get("error"),
            timestamp=result.get("timestamp"),
            communication_logged=communication_logged,
            invite_type="screening"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error sending screening invite: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send screening invite: {str(e)}"
        )
