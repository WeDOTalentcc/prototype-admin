"""
Communication Service - Comprehensive communication management for LIA recruitment platform.

This service handles:
1. Approval System (Human-in-the-Loop):
   - Initial contact with candidates: REQUIRES APPROVAL before sending
   - Rejection feedback: REQUIRES APPROVAL + AI personalization
   - Reminders, confirmations: AUTOMATIC (no approval needed)

2. Communication Policies (Best Practices):
   - Sending hours: 8h-20h weekdays only (Brazilian timezone)
   - Rate limiting: max 3 messages per day per candidate
   - LGPD compliance: opt-out tracking, consent management
   - Quarantine: 3 months after rejection (cannot re-contact)
   - Track all communications in audit log

3. Provider Abstraction:
   - Abstract email provider interface (Mailgun primary, Resend fallback, AWS SES)
   - Abstract WhatsApp provider interface (Twilio, WhatsApp Business API)
   - Fallback handling when provider fails
   - Retry logic with exponential backoff
"""
import asyncio
import logging
import os
import random
import uuid
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import JSON, Boolean, Column, DateTime, Integer, String, Text, and_, desc, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal, Base
from app.domains.communication.services.message_providers import (
    AWSEmailProvider,
    MailgunMessageProvider,
    MessageProvider,
    MockEmailProvider,
    MockWhatsAppProvider,
    ResendMessageProvider,
    TwilioWhatsAppProvider,
    WhatsAppBusinessProvider,
)
from app.enums.communication import (
    ApprovalStatus,
    CommunicationStatus,
    MESSAGE_TYPE_TO_SITUATION,
    MessageChannel,
    MessageType,
    TemplateSituation,
)
from app.services.notification_service import (
    NotificationService,
    NotificationType,
)
from app.templates.communication_templates import EmailTemplates, WhatsAppTemplates

logger = logging.getLogger(__name__)

BRAZIL_TZ_OFFSET_HOURS = -3


MESSAGE_REQUIRES_APPROVAL = {
    MessageType.INITIAL_CONTACT: True,
    MessageType.SCREENING_INVITATION: True,
    MessageType.REJECTION_FEEDBACK: True,
    MessageType.OFFER: True,
    MessageType.SCREENING_REMINDER: False,
    MessageType.SCREENING_PASSED: False,
    MessageType.SCREENING_FAILED: True,
    MessageType.INTERVIEW_INVITE: False,
    MessageType.INTERVIEW_SCHEDULED: False,
    MessageType.INTERVIEW_REMINDER: False,
    MessageType.INTERVIEW_CONFIRMATION: False,
    MessageType.INTERVIEW_CONFIRMED: False,
    MessageType.PROCESS_CLOSED: True,
    MessageType.GENERAL: True,
}

class PendingApproval(Base):
    """Pending approval requests for communications requiring human review."""
    __tablename__ = "pending_approvals"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    company_id = Column(String, nullable=False, index=True)
    
    candidate_id = Column(String, nullable=False, index=True)
    candidate_name = Column(String(255), nullable=True)
    candidate_email = Column(String(255), nullable=True)
    candidate_phone = Column(String(50), nullable=True)
    
    job_id = Column(String, nullable=True, index=True)
    job_title = Column(String(255), nullable=True)
    
    message_type = Column(String(50), nullable=False, index=True)
    channel = Column(String(20), nullable=False, default="email")
    
    subject = Column(String(500), nullable=True)
    body = Column(Text, nullable=False)
    body_html = Column(Text, nullable=True)
    
    ai_personalization = Column(Text, nullable=True)
    personalization_context = Column(JSON, default=dict)
    
    status = Column(String(20), default="pending", index=True)
    
    requested_by = Column(String(255), nullable=True)
    requested_at = Column(DateTime, default=datetime.utcnow)
    
    reviewed_by = Column(String(255), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    review_notes = Column(Text, nullable=True)
    
    modified_subject = Column(String(500), nullable=True)
    modified_body = Column(Text, nullable=True)
    
    priority = Column(String(20), default="normal")
    expires_at = Column(DateTime, nullable=True)
    
    communication_log_id = Column(String, nullable=True)
    
    extra_data = Column(JSON, default=dict)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "company_id": self.company_id,
            "candidate_id": self.candidate_id,
            "candidate_name": self.candidate_name,
            "candidate_email": self.candidate_email,
            "candidate_phone": self.candidate_phone,
            "job_id": self.job_id,
            "job_title": self.job_title,
            "message_type": self.message_type,
            "channel": self.channel,
            "subject": self.subject,
            "body": self.body,
            "body_html": self.body_html,
            "ai_personalization": self.ai_personalization,
            "personalization_context": self.personalization_context,
            "status": self.status,
            "requested_by": self.requested_by,
            "requested_at": self.requested_at.isoformat() if self.requested_at else None,
            "reviewed_by": self.reviewed_by,
            "reviewed_at": self.reviewed_at.isoformat() if self.reviewed_at else None,
            "review_notes": self.review_notes,
            "modified_subject": self.modified_subject,
            "modified_body": self.modified_body,
            "priority": self.priority,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "communication_log_id": self.communication_log_id,
            "extra_data": self.extra_data,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class CommunicationLog(Base):
    """Audit log for all communications sent."""
    __tablename__ = "communication_logs"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    company_id = Column(String, nullable=False, index=True)
    
    candidate_id = Column(String, nullable=False, index=True)
    candidate_email = Column(String(255), nullable=True)
    candidate_phone = Column(String(50), nullable=True)
    
    job_id = Column(String, nullable=True, index=True)
    
    message_type = Column(String(50), nullable=False, index=True)
    channel = Column(String(20), nullable=False, index=True)
    
    subject = Column(String(500), nullable=True)
    body = Column(Text, nullable=False)
    body_html = Column(Text, nullable=True)
    
    status = Column(String(20), default="pending", index=True)
    
    sent_at = Column(DateTime, nullable=True, index=True)
    delivered_at = Column(DateTime, nullable=True)
    read_at = Column(DateTime, nullable=True)
    failed_at = Column(DateTime, nullable=True)
    
    provider_name = Column(String(50), nullable=True)
    provider_message_id = Column(String(255), nullable=True)
    provider_response = Column(JSON, default=dict)
    
    retry_count = Column(Integer, default=0)
    last_retry_at = Column(DateTime, nullable=True)
    next_retry_at = Column(DateTime, nullable=True)
    
    error_message = Column(Text, nullable=True)
    error_code = Column(String(50), nullable=True)
    
    approval_id = Column(String, nullable=True)
    approved_by = Column(String(255), nullable=True)
    
    sent_by = Column(String(255), nullable=True)
    
    extra_data = Column(JSON, default=dict)
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "company_id": self.company_id,
            "candidate_id": self.candidate_id,
            "candidate_email": self.candidate_email,
            "candidate_phone": self.candidate_phone,
            "job_id": self.job_id,
            "message_type": self.message_type,
            "channel": self.channel,
            "subject": self.subject,
            "body": self.body,
            "status": self.status,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "delivered_at": self.delivered_at.isoformat() if self.delivered_at else None,
            "read_at": self.read_at.isoformat() if self.read_at else None,
            "provider_name": self.provider_name,
            "provider_message_id": self.provider_message_id,
            "retry_count": self.retry_count,
            "error_message": self.error_message,
            "approval_id": self.approval_id,
            "approved_by": self.approved_by,
            "sent_by": self.sent_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class CandidateOptOut(Base):
    """LGPD-compliant opt-out tracking for candidates."""
    __tablename__ = "candidate_opt_outs"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    company_id = Column(String, nullable=False, index=True)
    
    candidate_id = Column(String, nullable=False, index=True)
    candidate_email = Column(String(255), nullable=True, index=True)
    candidate_phone = Column(String(50), nullable=True, index=True)
    
    channel = Column(String(20), nullable=False, index=True)
    
    opt_out_type = Column(String(50), nullable=False, default="all")
    opt_out_reason = Column(Text, nullable=True)
    
    opted_out_at = Column(DateTime, default=datetime.utcnow, index=True)
    opted_out_via = Column(String(50), nullable=True)
    
    is_active = Column(Boolean, default=True)
    reactivated_at = Column(DateTime, nullable=True)
    reactivated_by = Column(String(255), nullable=True)
    
    consent_given_at = Column(DateTime, nullable=True)
    consent_ip_address = Column(String(50), nullable=True)
    consent_user_agent = Column(String(500), nullable=True)
    
    extra_data = Column(JSON, default=dict)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "company_id": self.company_id,
            "candidate_id": self.candidate_id,
            "candidate_email": self.candidate_email,
            "candidate_phone": self.candidate_phone,
            "channel": self.channel,
            "opt_out_type": self.opt_out_type,
            "opt_out_reason": self.opt_out_reason,
            "opted_out_at": self.opted_out_at.isoformat() if self.opted_out_at else None,
            "is_active": self.is_active,
            "consent_given_at": self.consent_given_at.isoformat() if self.consent_given_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class CandidateQuarantine(Base):
    """Quarantine tracking for rejected candidates (3 months no-contact)."""
    __tablename__ = "candidate_quarantines"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    company_id = Column(String, nullable=False, index=True)
    
    candidate_id = Column(String, nullable=False, index=True)
    job_id = Column(String, nullable=True, index=True)
    
    reason = Column(String(100), nullable=False, default="rejection")
    
    quarantine_start = Column(DateTime, default=datetime.utcnow, index=True)
    quarantine_end = Column(DateTime, nullable=False, index=True)
    quarantine_days = Column(Integer, default=90)
    
    is_active = Column(Boolean, default=True, index=True)
    lifted_at = Column(DateTime, nullable=True)
    lifted_by = Column(String(255), nullable=True)
    lift_reason = Column(Text, nullable=True)
    
    extra_data = Column(JSON, default=dict)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "company_id": self.company_id,
            "candidate_id": self.candidate_id,
            "job_id": self.job_id,
            "reason": self.reason,
            "quarantine_start": self.quarantine_start.isoformat() if self.quarantine_start else None,
            "quarantine_end": self.quarantine_end.isoformat() if self.quarantine_end else None,
            "quarantine_days": self.quarantine_days,
            "is_active": self.is_active,
            "lifted_at": self.lifted_at.isoformat() if self.lifted_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }



class CommunicationService:
    """
    Comprehensive communication service for LIA recruitment platform.
    
    Handles:
    - Approval workflows (human-in-the-loop)
    - Communication policies (sending hours, rate limits, LGPD)
    - Provider abstraction with fallbacks
    - Retry logic with exponential backoff
    - Audit logging
    """
    
    MAX_MESSAGES_PER_DAY = 3
    QUARANTINE_DAYS = 90
    SENDING_START_HOUR = 8
    SENDING_END_HOUR = 20
    MAX_RETRIES = 3
    BASE_RETRY_DELAY_SECONDS = 60
    
    def __init__(self):
        self.notification_service = NotificationService()
        
        self._email_providers: list[MessageProvider] = [
            MailgunMessageProvider(),
            ResendMessageProvider(),
            MockEmailProvider(),
        ]
        
        self._whatsapp_providers: list[MessageProvider] = [
            TwilioWhatsAppProvider(),
            WhatsAppBusinessProvider(),
            MockWhatsAppProvider(),
        ]
    
    def _get_brazil_now(self) -> datetime:
        """Get current time in Brazil timezone (UTC-3)."""
        return datetime.utcnow() + timedelta(hours=BRAZIL_TZ_OFFSET_HOURS)
    
    def _is_within_sending_hours(self) -> bool:
        """Check if current time is within allowed sending hours (8h-20h weekdays)."""
        brazil_now = self._get_brazil_now()
        
        if brazil_now.weekday() >= 5:
            return False
        
        current_hour = brazil_now.hour
        return self.SENDING_START_HOUR <= current_hour < self.SENDING_END_HOUR
    
    def _get_next_sending_window(self) -> datetime:
        """Get the next valid sending window."""
        brazil_now = self._get_brazil_now()
        
        if brazil_now.weekday() >= 5:
            days_until_monday = 7 - brazil_now.weekday()
            next_window = brazil_now.replace(
                hour=self.SENDING_START_HOUR, minute=0, second=0, microsecond=0
            ) + timedelta(days=days_until_monday)
        elif brazil_now.hour >= self.SENDING_END_HOUR:
            if brazil_now.weekday() == 4:
                next_window = brazil_now.replace(
                    hour=self.SENDING_START_HOUR, minute=0, second=0, microsecond=0
                ) + timedelta(days=3)
            else:
                next_window = brazil_now.replace(
                    hour=self.SENDING_START_HOUR, minute=0, second=0, microsecond=0
                ) + timedelta(days=1)
        elif brazil_now.hour < self.SENDING_START_HOUR:
            next_window = brazil_now.replace(
                hour=self.SENDING_START_HOUR, minute=0, second=0, microsecond=0
            )
        else:
            next_window = brazil_now
        
        return next_window - timedelta(hours=BRAZIL_TZ_OFFSET_HOURS)
    
    async def _check_rate_limit(
        self,
        candidate_id: str,
        company_id: str,
        db: AsyncSession
    ) -> tuple[bool, int]:
        """
        Check if candidate has exceeded daily rate limit.
        
        Returns:
            Tuple of (is_allowed, messages_sent_today)
        """
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        
        result = await db.execute(
            select(CommunicationLog).where(
                and_(
                    CommunicationLog.candidate_id == candidate_id,
                    CommunicationLog.company_id == company_id,
                    CommunicationLog.sent_at >= today_start,
                    CommunicationLog.status.in_(["sent", "delivered", "read"])
                )
            )
        )
        
        logs = list(result.scalars())
        messages_today = len(logs)
        
        return messages_today < self.MAX_MESSAGES_PER_DAY, messages_today
    
    async def _check_opt_out(
        self,
        candidate_id: str,
        company_id: str,
        channel: MessageChannel,
        db: AsyncSession
    ) -> tuple[bool, CandidateOptOut | None]:
        """
        Check if candidate has opted out of communications.
        
        Returns:
            Tuple of (is_opted_out, opt_out_record)
        """
        result = await db.execute(
            select(CandidateOptOut).where(
                and_(
                    CandidateOptOut.candidate_id == candidate_id,
                    CandidateOptOut.company_id == company_id,
                    CandidateOptOut.is_active,
                    or_(
                        CandidateOptOut.channel == channel.value,
                        CandidateOptOut.opt_out_type == "all"
                    )
                )
            )
        )
        
        opt_out = result.scalar_one_or_none()
        return bool(opt_out), opt_out
    
    async def _check_quarantine(
        self,
        candidate_id: str,
        company_id: str,
        db: AsyncSession
    ) -> tuple[bool, CandidateQuarantine | None]:
        """
        Check if candidate is in quarantine period.
        
        Returns:
            Tuple of (is_in_quarantine, quarantine_record)
        """
        now = datetime.utcnow()
        
        result = await db.execute(
            select(CandidateQuarantine).where(
                and_(
                    CandidateQuarantine.candidate_id == candidate_id,
                    CandidateQuarantine.company_id == company_id,
                    CandidateQuarantine.is_active,
                    CandidateQuarantine.quarantine_end > now
                )
            )
        )
        
        quarantine = result.scalar_one_or_none()
        return bool(quarantine), quarantine
    
    async def validate_can_send(
        self,
        candidate_id: str,
        company_id: str,
        channel: MessageChannel,
        message_type: MessageType,
        db: AsyncSession | None = None
    ) -> dict[str, Any]:
        """
        Validate if a message can be sent to a candidate.
        
        Returns validation result with details about any blocking issues.
        """
        should_close = False
        if db is None:
            db = AsyncSessionLocal()
            should_close = True
        
        try:
            result = {
                "can_send": True,
                "requires_approval": MESSAGE_REQUIRES_APPROVAL.get(message_type, True),
                "warnings": [],
                "blocks": []
            }
            
            is_opted_out, opt_out = await self._check_opt_out(
                candidate_id, company_id, channel, db
            )
            if is_opted_out:
                result["can_send"] = False
                result["blocks"].append({
                    "type": "opt_out",
                    "message": f"Candidato optou por não receber comunicações via {channel.value}",
                    "opt_out_date": opt_out.opted_out_at.isoformat() if opt_out else None
                })
            
            is_in_quarantine, quarantine = await self._check_quarantine(
                candidate_id, company_id, db
            )
            if is_in_quarantine:
                result["can_send"] = False
                result["blocks"].append({
                    "type": "quarantine",
                    "message": f"Candidato está em quarentena até {quarantine.quarantine_end.strftime('%d/%m/%Y')}",
                    "quarantine_end": quarantine.quarantine_end.isoformat() if quarantine else None,
                    "reason": quarantine.reason if quarantine else None
                })
            
            is_within_limit, messages_today = await self._check_rate_limit(
                candidate_id, company_id, db
            )
            if not is_within_limit:
                result["can_send"] = False
                result["blocks"].append({
                    "type": "rate_limit",
                    "message": f"Limite diário atingido ({self.MAX_MESSAGES_PER_DAY} mensagens)",
                    "messages_today": messages_today
                })
            elif messages_today >= 2:
                result["warnings"].append({
                    "type": "approaching_limit",
                    "message": f"Aproximando do limite diário ({messages_today}/{self.MAX_MESSAGES_PER_DAY})"
                })
            
            if not self._is_within_sending_hours():
                next_window = self._get_next_sending_window()
                result["warnings"].append({
                    "type": "outside_hours",
                    "message": "Fora do horário de envio (8h-20h dias úteis)",
                    "next_window": next_window.isoformat(),
                    "will_queue": True
                })
            
            return result
            
        finally:
            if should_close:
                await db.close()
    
    async def create_approval_request(
        self,
        company_id: str,
        candidate_id: str,
        candidate_name: str,
        candidate_email: str | None,
        candidate_phone: str | None,
        message_type: MessageType,
        channel: MessageChannel,
        subject: str | None,
        body: str,
        body_html: str | None = None,
        job_id: str | None = None,
        job_title: str | None = None,
        ai_personalization: str | None = None,
        personalization_context: dict[str, Any] | None = None,
        requested_by: str | None = None,
        priority: str = "normal",
        expires_in_hours: int = 48,
        extra_data: dict[str, Any] | None = None,
        db: AsyncSession | None = None
    ) -> dict[str, Any]:
        """
        Create a new approval request for a communication.
        
        Returns the created approval request.
        """
        should_close = False
        if db is None:
            db = AsyncSessionLocal()
            should_close = True
        
        try:
            validation = await self.validate_can_send(
                candidate_id, company_id, channel, message_type, db
            )
            
            if not validation["can_send"]:
                return {
                    "success": False,
                    "error": "cannot_send",
                    "validation": validation
                }
            
            expires_at = datetime.utcnow() + timedelta(hours=expires_in_hours)
            
            approval = PendingApproval(
                company_id=company_id,
                candidate_id=candidate_id,
                candidate_name=candidate_name,
                candidate_email=candidate_email,
                candidate_phone=candidate_phone,
                job_id=job_id,
                job_title=job_title,
                message_type=message_type.value,
                channel=channel.value,
                subject=subject,
                body=body,
                body_html=body_html,
                ai_personalization=ai_personalization,
                personalization_context=personalization_context or {},
                status=ApprovalStatus.PENDING.value,
                requested_by=requested_by,
                priority=priority,
                expires_at=expires_at,
                extra_data=extra_data or {}
            )
            
            db.add(approval)
            await db.commit()
            await db.refresh(approval)
            
            await self.notification_service.create_notification(
                user_id=requested_by or "system",
                title=f"Aprovação pendente: {message_type.value}",
                message=f"Mensagem para {candidate_name} aguarda aprovação",
                notification_type=NotificationType.ACTION_REQUIRED,
                category="approval",
                source_agent="communication_agent",
                related_candidate_id=candidate_id,
                related_job_id=job_id,
                action_url=f"/approvals/{approval.id}",
                action_label="Revisar",
                expires_in_hours=expires_in_hours,
                db=db
            )
            
            logger.info(f"📝 Approval request created: {approval.id} for {candidate_name}")
            
            return {
                "success": True,
                "approval_id": approval.id,
                "approval": approval.to_dict(),
                "validation": validation
            }
            
        except Exception:
            try:
                await db.rollback()
            except Exception:
                pass
            raise
        finally:
            if should_close:
                await db.close()
    
    async def approve_request(
        self,
        approval_id: str,
        reviewed_by: str,
        review_notes: str | None = None,
        modified_subject: str | None = None,
        modified_body: str | None = None,
        send_immediately: bool = True,
        db: AsyncSession | None = None
    ) -> dict[str, Any]:
        """
        Approve a pending communication request and optionally send it.
        
        Returns the approval result and communication log if sent.
        """
        should_close = False
        if db is None:
            db = AsyncSessionLocal()
            should_close = True
        
        try:
            result = await db.execute(
                select(PendingApproval).where(
                    PendingApproval.id == approval_id
                )
            )
            approval = result.scalar_one_or_none()
            
            if not approval:
                return {"success": False, "error": "not_found"}
            
            if approval.status != ApprovalStatus.PENDING.value:
                return {"success": False, "error": "already_processed", "status": approval.status}
            
            approval.status = ApprovalStatus.APPROVED.value
            approval.reviewed_by = reviewed_by
            approval.reviewed_at = datetime.utcnow()
            approval.review_notes = review_notes
            approval.modified_subject = modified_subject
            approval.modified_body = modified_body
            
            await db.commit()
            await db.refresh(approval)
            
            logger.info(f"✅ Approval approved: {approval_id} by {reviewed_by}")
            
            communication_result = None
            if send_immediately:
                final_subject = modified_subject or approval.subject
                final_body = modified_body or approval.body
                
                communication_result = await self.send_message(
                    company_id=approval.company_id,
                    candidate_id=approval.candidate_id,
                    candidate_email=approval.candidate_email,
                    candidate_phone=approval.candidate_phone,
                    message_type=MessageType(approval.message_type),
                    channel=MessageChannel(approval.channel),
                    subject=final_subject,
                    body=final_body,
                    body_html=approval.body_html,
                    job_id=approval.job_id,
                    approval_id=approval_id,
                    approved_by=reviewed_by,
                    sent_by=reviewed_by,
                    db=db
                )
                
                if communication_result.get("success"):
                    approval.communication_log_id = communication_result.get("log_id")
                    await db.commit()
            
            return {
                "success": True,
                "approval": approval.to_dict(),
                "communication_result": communication_result
            }
            
        except Exception:
            try:
                await db.rollback()
            except Exception:
                pass
            raise
        finally:
            if should_close:
                await db.close()
    
    async def reject_request(
        self,
        approval_id: str,
        reviewed_by: str,
        review_notes: str,
        db: AsyncSession | None = None
    ) -> dict[str, Any]:
        """
        Reject a pending communication request.
        """
        should_close = False
        if db is None:
            db = AsyncSessionLocal()
            should_close = True
        
        try:
            result = await db.execute(
                select(PendingApproval).where(
                    PendingApproval.id == approval_id
                )
            )
            approval = result.scalar_one_or_none()
            
            if not approval:
                return {"success": False, "error": "not_found"}
            
            if approval.status != ApprovalStatus.PENDING.value:
                return {"success": False, "error": "already_processed", "status": approval.status}
            
            approval.status = ApprovalStatus.REJECTED.value
            approval.reviewed_by = reviewed_by
            approval.reviewed_at = datetime.utcnow()
            approval.review_notes = review_notes
            
            await db.commit()
            await db.refresh(approval)
            
            logger.info(f"❌ Approval rejected: {approval_id} by {reviewed_by}")
            
            return {
                "success": True,
                "approval": approval.to_dict()
            }
            
        except Exception:
            try:
                await db.rollback()
            except Exception:
                pass
            raise
        finally:
            if should_close:
                await db.close()
    
    async def get_pending_approvals(
        self,
        company_id: str,
        message_type: MessageType | None = None,
        channel: MessageChannel | None = None,
        priority: str | None = None,
        limit: int = 50,
        offset: int = 0,
        db: AsyncSession | None = None
    ) -> dict[str, Any]:
        """Get pending approval requests for a company."""
        should_close = False
        if db is None:
            db = AsyncSessionLocal()
            should_close = True
        
        try:
            conditions = [
                PendingApproval.company_id == company_id,
                PendingApproval.status == ApprovalStatus.PENDING.value,
                or_(
                    PendingApproval.expires_at.is_(None),
                    PendingApproval.expires_at > datetime.utcnow()
                )
            ]
            
            if message_type:
                conditions.append(PendingApproval.message_type == message_type.value)
            if channel:
                conditions.append(PendingApproval.channel == channel.value)
            if priority:
                conditions.append(PendingApproval.priority == priority)
            
            result = await db.execute(
                select(PendingApproval)
                .where(and_(*conditions))
                .order_by(
                    desc(PendingApproval.priority == "urgent"),
                    desc(PendingApproval.priority == "high"),
                    PendingApproval.requested_at
                )
                .limit(limit)
                .offset(offset)
            )
            
            approvals = [a.to_dict() for a in result.scalars()]
            
            return {
                "approvals": approvals,
                "total": len(approvals),
                "has_more": len(approvals) == limit
            }
            
        finally:
            if should_close:
                await db.close()
    
    def _get_provider(self, channel: MessageChannel) -> MessageProvider | None:
        """Get an available provider for the given channel."""
        if channel == MessageChannel.EMAIL:
            providers = self._email_providers
        elif channel == MessageChannel.WHATSAPP:
            providers = self._whatsapp_providers
        else:
            return None
        
        for provider in providers:
            if provider.is_available():
                return provider
        
        return None
    
    async def send_message(
        self,
        company_id: str,
        candidate_id: str,
        candidate_email: str | None,
        candidate_phone: str | None,
        message_type: MessageType,
        channel: MessageChannel,
        subject: str | None,
        body: str,
        body_html: str | None = None,
        job_id: str | None = None,
        approval_id: str | None = None,
        approved_by: str | None = None,
        sent_by: str | None = None,
        skip_policy_checks: bool = False,
        db: AsyncSession | None = None
    ) -> dict[str, Any]:
        """
        Send a message to a candidate.
        
        Handles provider selection, fallbacks, and retry logic.
        """
        should_close = False
        if db is None:
            db = AsyncSessionLocal()
            should_close = True
        
        try:
            if not skip_policy_checks:
                validation = await self.validate_can_send(
                    candidate_id, company_id, channel, message_type, db
                )
                
                if not validation["can_send"]:
                    return {
                        "success": False,
                        "error": "blocked",
                        "validation": validation
                    }
            
            if channel == MessageChannel.EMAIL:
                recipient = candidate_email
            else:
                recipient = candidate_phone
            
            if not recipient:
                return {
                    "success": False,
                    "error": "no_recipient",
                    "message": f"No {channel.value} address available for candidate"
                }
            
            log = CommunicationLog(
                company_id=company_id,
                candidate_id=candidate_id,
                candidate_email=candidate_email,
                candidate_phone=candidate_phone,
                job_id=job_id,
                message_type=message_type.value,
                channel=channel.value,
                subject=subject,
                body=body,
                body_html=body_html,
                status=CommunicationStatus.PENDING.value,
                approval_id=approval_id,
                approved_by=approved_by,
                sent_by=sent_by
            )
            
            db.add(log)
            await db.commit()
            await db.refresh(log)
            
            if not self._is_within_sending_hours():
                next_window = self._get_next_sending_window()
                log.status = CommunicationStatus.QUEUED.value
                log.next_retry_at = next_window
                await db.commit()
                
                logger.info(f"📬 Message queued for sending at {next_window}: {log.id}")
                
                return {
                    "success": True,
                    "queued": True,
                    "log_id": log.id,
                    "scheduled_for": next_window.isoformat(),
                    "message": "Message queued for next sending window"
                }
            
            success, provider_msg_id, response = await self._send_with_retry(
                channel, recipient, subject, body, body_html, log, db
            )
            
            if success:
                log.status = CommunicationStatus.SENT.value
                log.sent_at = datetime.utcnow()
                log.provider_message_id = provider_msg_id
                log.provider_response = response or {}
                
                logger.info(f"✉️ Message sent successfully: {log.id}")
            else:
                log.status = CommunicationStatus.FAILED.value
                log.failed_at = datetime.utcnow()
                log.error_message = response.get("error") if response else "Unknown error"
                
                logger.error(f"❌ Message failed: {log.id} - {log.error_message}")
            
            await db.commit()
            await db.refresh(log)
            
            try:
                from app.services.event_dispatcher import event_dispatcher
                await event_dispatcher.on_message_sent(
                    company_id=company_id,
                    candidate_id=candidate_id,
                    message_type=message_type.value,
                    channel=channel.value,
                    job_id=job_id,
                    success=success,
                    log_id=str(log.id)
                )
            except Exception as e:
                logger.warning(f"Event dispatch failed for message sent: {e}")
            
            return {
                "success": success,
                "log_id": log.id,
                "log": log.to_dict(),
                "provider_message_id": provider_msg_id
            }
            
        except Exception:
            try:
                await db.rollback()
            except Exception:
                pass
            raise
        finally:
            if should_close:
                await db.close()
    
    async def _send_with_retry(
        self,
        channel: MessageChannel,
        recipient: str,
        subject: str | None,
        body: str,
        body_html: str | None,
        log: CommunicationLog,
        db: AsyncSession
    ) -> tuple[bool, str | None, dict[str, Any] | None]:
        """
        Send message with retry logic and exponential backoff.
        """
        providers = self._email_providers if channel == MessageChannel.EMAIL else self._whatsapp_providers
        
        for retry in range(self.MAX_RETRIES):
            for provider in providers:
                if not provider.is_available():
                    continue
                
                log.provider_name = provider.name
                log.retry_count = retry + 1
                log.last_retry_at = datetime.utcnow()
                await db.commit()
                
                success, msg_id, response = await provider.send(
                    to=recipient,
                    subject=subject,
                    body=body,
                    body_html=body_html
                )
                
                if success:
                    return True, msg_id, response
                
                logger.warning(f"Provider {provider.name} failed, trying next...")
            
            if retry < self.MAX_RETRIES - 1:
                delay = self.BASE_RETRY_DELAY_SECONDS * (2 ** retry)
                jitter = random.uniform(0, delay * 0.1)
                wait_time = delay + jitter
                
                logger.info(f"All providers failed, waiting {wait_time:.0f}s before retry {retry + 2}")
                await asyncio.sleep(wait_time)
        
        return False, None, {"error": "All providers failed after retries"}
    
    async def send_automatic_message(
        self,
        company_id: str,
        candidate_id: str,
        candidate_name: str,
        candidate_email: str | None,
        candidate_phone: str | None,
        message_type: MessageType,
        channel: MessageChannel,
        template_variables: dict[str, Any],
        job_id: str | None = None,
        job_title: str | None = None,
        sent_by: str | None = "system",
        db: AsyncSession | None = None
    ) -> dict[str, Any]:
        """
        Send an automatic message (no approval required) using templates.
        
        Used for reminders, confirmations, and other automated communications.
        """
        if MESSAGE_REQUIRES_APPROVAL.get(message_type, True):
            return {
                "success": False,
                "error": "requires_approval",
                "message": f"Message type {message_type.value} requires approval"
            }
        
        if channel == MessageChannel.EMAIL:
            template_func = self._get_email_template(message_type)
            if template_func:
                template_result = template_func(**template_variables)
                subject = template_result.get("subject", "")
                body = template_result.get("body", "")
            else:
                return {"success": False, "error": "template_not_found"}
        else:
            template_func = self._get_whatsapp_template(message_type)
            if template_func:
                body = template_func(**template_variables)
                subject = None
            else:
                return {"success": False, "error": "template_not_found"}
        
        return await self.send_message(
            company_id=company_id,
            candidate_id=candidate_id,
            candidate_email=candidate_email,
            candidate_phone=candidate_phone,
            message_type=message_type,
            channel=channel,
            subject=subject,
            body=body,
            job_id=job_id,
            sent_by=sent_by,
            db=db
        )
    
    async def send_templated_message(
        self,
        db: AsyncSession,
        message_type: MessageType,
        company_id: str,
        candidate_id: str,
        candidate_email: str | None,
        candidate_name: str,
        variables: dict[str, Any],
        channel: MessageChannel = MessageChannel.EMAIL,
        job_id: str | None = None,
        sent_by: str | None = "system",
        skip_approval_check: bool = False
    ) -> dict[str, Any]:
        """
        Send a message using database templates selected via MESSAGE_TYPE_TO_SITUATION.

        Delegates template resolution and rendering to TemplateService, then sends
        the rendered content via send_message() with all policy checks applied.

        Args:
            db: Database session
            message_type: Type of message (determines template selection)
            company_id: Company ID for multi-tenancy
            candidate_id: Candidate ID
            candidate_email: Candidate's email address
            candidate_name: Candidate's name
            variables: Template variables for rendering
            channel: Communication channel (default: EMAIL)
            job_id: Optional job vacancy ID
            sent_by: Who is sending (default: system)
            skip_approval_check: Skip approval check for auto-approved message types

        Returns:
            Result dict with success status and details
        """
        from app.domains.communication.services.template_service import render_message_template

        try:
            rendered = await render_message_template(
                db=db,
                message_type=message_type,
                channel=channel,
                company_id=company_id,
                candidate_id=candidate_id,
                variables=variables,
            )

            if not rendered.get("success"):
                return rendered

            send_result = await self.send_message(
                company_id=company_id,
                candidate_id=candidate_id,
                candidate_email=candidate_email,
                candidate_phone=None,
                message_type=message_type,
                channel=channel,
                subject=rendered.get("subject"),
                body=rendered.get("body_text") or rendered.get("body_html", ""),
                body_html=rendered.get("body_html"),
                job_id=job_id,
                sent_by=sent_by,
                skip_policy_checks=skip_approval_check,
                db=db,
            )

            if send_result.get("success"):
                logger.info("📧 Templated message sent: %s", message_type.value)
                send_result["template_used"] = rendered.get("template_name")
                send_result["template_situation"] = rendered.get("template_situation")

                log_id = send_result.get("log_id")
                _tracking_extra = {
                    "template_id": rendered.get("template_id"),
                    "template_source": rendered.get("template_source", "default"),
                }
                if log_id and _tracking_extra:
                    try:
                        from sqlalchemy import update as sa_update
                        await db.execute(
                            sa_update(CommunicationLog)
                            .where(CommunicationLog.id == log_id)
                            .values(extra_data=_tracking_extra)
                        )
                        await db.commit()
                    except Exception as _upd_exc:
                        try:
                            await db.rollback()
                        except Exception:
                            pass
                        logger.debug("[ABTracking] CommunicationLog extra_data update skipped: %s", _upd_exc)

                try:
                    from app.shared.intelligence.template_learning.template_learning_service import (
                        template_learning_service,
                    )
                    template_learning_service.record_send(
                        company_id=company_id,
                        template_id=rendered.get("template_id", ""),
                        context={"message_type": message_type.value, "candidate_id": candidate_id},
                    )
                except Exception:
                    pass

            return send_result

        except Exception as e:
            try:
                await db.rollback()
            except Exception:
                pass
            logger.error("❌ Failed to send templated message: %s", e)
            return {
                "success": False,
                "error": "send_failed",
                "message": str(e),
            }

    def _get_email_template(self, message_type: MessageType):
        """Get the appropriate email template function for a message type.

        Delegates to template_service for a single source of truth.
        """
        from app.domains.communication.services.template_service import get_email_template_func
        return get_email_template_func(message_type)

    def _get_whatsapp_template(self, message_type: MessageType):
        """Get the appropriate WhatsApp template function for a message type.

        Delegates to template_service for a single source of truth.
        """
        from app.domains.communication.services.template_service import get_whatsapp_template_func
        return get_whatsapp_template_func(message_type)
    
    async def record_opt_out(
        self,
        company_id: str,
        candidate_id: str,
        channel: MessageChannel,
        candidate_email: str | None = None,
        candidate_phone: str | None = None,
        opt_out_reason: str | None = None,
        opted_out_via: str = "user_request",
        db: AsyncSession | None = None
    ) -> dict[str, Any]:
        """Record a candidate's opt-out from communications (LGPD compliance)."""
        should_close = False
        if db is None:
            db = AsyncSessionLocal()
            should_close = True
        
        try:
            opt_out = CandidateOptOut(
                company_id=company_id,
                candidate_id=candidate_id,
                candidate_email=candidate_email,
                candidate_phone=candidate_phone,
                channel=channel.value,
                opt_out_type="channel_specific",
                opt_out_reason=opt_out_reason,
                opted_out_via=opted_out_via
            )
            
            db.add(opt_out)
            await db.commit()
            await db.refresh(opt_out)
            
            logger.info(f"🚫 Opt-out recorded: {candidate_id} for {channel.value}")
            
            return {
                "success": True,
                "opt_out": opt_out.to_dict()
            }
            
        except Exception:
            try:
                await db.rollback()
            except Exception:
                pass
            raise
        finally:
            if should_close:
                await db.close()
    
    async def record_consent(
        self,
        company_id: str,
        candidate_id: str,
        channel: MessageChannel,
        candidate_email: str | None = None,
        candidate_phone: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        db: AsyncSession | None = None
    ) -> dict[str, Any]:
        """Record a candidate's consent for communications (LGPD compliance)."""
        should_close = False
        if db is None:
            db = AsyncSessionLocal()
            should_close = True
        
        try:
            result = await db.execute(
                select(CandidateOptOut).where(
                    and_(
                        CandidateOptOut.candidate_id == candidate_id,
                        CandidateOptOut.company_id == company_id,
                        CandidateOptOut.channel == channel.value,
                        CandidateOptOut.is_active
                    )
                )
            )
            opt_out = result.scalar_one_or_none()
            
            if opt_out:
                opt_out.is_active = False
                opt_out.reactivated_at = datetime.utcnow()
                opt_out.reactivated_by = "consent"
                opt_out.consent_given_at = datetime.utcnow()
                opt_out.consent_ip_address = ip_address
                opt_out.consent_user_agent = user_agent
                
                await db.commit()
                await db.refresh(opt_out)
                
                logger.info(f"✅ Consent recorded (reactivated): {candidate_id} for {channel.value}")
            else:
                logger.info(f"ℹ️ Consent recorded (no prior opt-out): {candidate_id} for {channel.value}")
            
            return {
                "success": True,
                "reactivated": bool(opt_out)
            }
            
        except Exception:
            try:
                await db.rollback()
            except Exception:
                pass
            raise
        finally:
            if should_close:
                await db.close()
    
    async def add_to_quarantine(
        self,
        company_id: str,
        candidate_id: str,
        reason: str = "rejection",
        job_id: str | None = None,
        quarantine_days: int = 90,
        db: AsyncSession | None = None
    ) -> dict[str, Any]:
        """Add a candidate to quarantine (no contact for specified period)."""
        should_close = False
        if db is None:
            db = AsyncSessionLocal()
            should_close = True
        
        try:
            now = datetime.utcnow()
            quarantine_end = now + timedelta(days=quarantine_days)
            
            quarantine = CandidateQuarantine(
                company_id=company_id,
                candidate_id=candidate_id,
                job_id=job_id,
                reason=reason,
                quarantine_start=now,
                quarantine_end=quarantine_end,
                quarantine_days=quarantine_days
            )
            
            db.add(quarantine)
            await db.commit()
            await db.refresh(quarantine)
            
            logger.info(f"⏳ Quarantine added: {candidate_id} until {quarantine_end.strftime('%Y-%m-%d')}")
            
            return {
                "success": True,
                "quarantine": quarantine.to_dict()
            }
            
        except Exception:
            try:
                await db.rollback()
            except Exception:
                pass
            raise
        finally:
            if should_close:
                await db.close()
    
    async def lift_quarantine(
        self,
        quarantine_id: str,
        lifted_by: str,
        lift_reason: str,
        db: AsyncSession | None = None
    ) -> dict[str, Any]:
        """Lift a quarantine early."""
        should_close = False
        if db is None:
            db = AsyncSessionLocal()
            should_close = True
        
        try:
            result = await db.execute(
                select(CandidateQuarantine).where(
                    CandidateQuarantine.id == quarantine_id
                )
            )
            quarantine = result.scalar_one_or_none()
            
            if not quarantine:
                return {"success": False, "error": "not_found"}
            
            quarantine.is_active = False
            quarantine.lifted_at = datetime.utcnow()
            quarantine.lifted_by = lifted_by
            quarantine.lift_reason = lift_reason
            
            await db.commit()
            await db.refresh(quarantine)
            
            logger.info(f"🔓 Quarantine lifted: {quarantine_id} by {lifted_by}")
            
            return {
                "success": True,
                "quarantine": quarantine.to_dict()
            }
            
        except Exception:
            try:
                await db.rollback()
            except Exception:
                pass
            raise
        finally:
            if should_close:
                await db.close()
    
    async def get_communication_history(
        self,
        company_id: str,
        candidate_id: str,
        channel: MessageChannel | None = None,
        status: CommunicationStatus | None = None,
        limit: int = 50,
        offset: int = 0,
        db: AsyncSession | None = None
    ) -> dict[str, Any]:
        """Get communication history for a candidate."""
        should_close = False
        if db is None:
            db = AsyncSessionLocal()
            should_close = True
        
        try:
            conditions = [
                CommunicationLog.company_id == company_id,
                CommunicationLog.candidate_id == candidate_id
            ]
            
            if channel:
                conditions.append(CommunicationLog.channel == channel.value)
            if status:
                conditions.append(CommunicationLog.status == status.value)
            
            result = await db.execute(
                select(CommunicationLog)
                .where(and_(*conditions))
                .order_by(desc(CommunicationLog.created_at))
                .limit(limit)
                .offset(offset)
            )
            
            logs = [log.to_dict() for log in result.scalars()]
            
            return {
                "logs": logs,
                "total": len(logs),
                "has_more": len(logs) == limit
            }
            
        finally:
            if should_close:
                await db.close()
    
    async def get_daily_stats(
        self,
        company_id: str,
        date: datetime | None = None,
        db: AsyncSession | None = None
    ) -> dict[str, Any]:
        """Get daily communication statistics."""
        should_close = False
        if db is None:
            db = AsyncSessionLocal()
            should_close = True
        
        try:
            if date is None:
                date = datetime.utcnow()
            
            day_start = date.replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = day_start + timedelta(days=1)
            
            result = await db.execute(
                select(CommunicationLog).where(
                    and_(
                        CommunicationLog.company_id == company_id,
                        CommunicationLog.created_at >= day_start,
                        CommunicationLog.created_at < day_end
                    )
                )
            )
            
            logs = list(result.scalars())
            
            stats = {
                "date": day_start.strftime("%Y-%m-%d"),
                "total_messages": len(logs),
                "by_status": {},
                "by_channel": {},
                "by_type": {},
                "success_rate": 0.0
            }
            
            for log in logs:
                stats["by_status"][log.status] = stats["by_status"].get(log.status, 0) + 1
                stats["by_channel"][log.channel] = stats["by_channel"].get(log.channel, 0) + 1
                stats["by_type"][log.message_type] = stats["by_type"].get(log.message_type, 0) + 1
            
            sent_count = stats["by_status"].get("sent", 0) + stats["by_status"].get("delivered", 0)
            if logs:
                stats["success_rate"] = (sent_count / len(logs)) * 100
            
            return stats
            
        finally:
            if should_close:
                await db.close()
    
    async def send_screening_result(
        self,
        db: AsyncSession,
        candidate_id: str,
        vacancy_id: str,
        company_id: str,
        passed: bool,
        wsi_score: float,
        strengths: list[str],
        development_areas: list[str] | None = None,
        candidate_name: str | None = None,
        candidate_email: str | None = None,
        candidate_phone: str | None = None,
        job_title: str | None = None,
        company_name: str | None = None
    ) -> dict[str, Any]:
        """
        Send screening result communication to candidate.
        
        - If passed: Send screening_passed via email AND WhatsApp
        - If failed: Send screening_failed via email only (with approval if configured)
        
        Args:
            db: Database session
            candidate_id: ID of the candidate
            vacancy_id: ID of the vacancy
            company_id: ID of the company
            passed: Whether the candidate passed screening
            wsi_score: WSI score (0-100)
            strengths: List of identified strengths
            development_areas: List of development areas (for failed candidates)
            candidate_name: Candidate's name
            candidate_email: Candidate's email address
            candidate_phone: Candidate's phone number (for WhatsApp)
            job_title: Title of the job vacancy
            company_name: Name of the company
            
        Returns:
            Dict with results for each channel attempted
        """
        results = {
            "success": True,
            "candidate_id": candidate_id,
            "vacancy_id": vacancy_id,
            "passed": passed,
            "wsi_score": wsi_score,
            "channels": {}
        }
        
        development_areas = development_areas or []
        candidate_name = candidate_name or "Candidato"
        job_title = job_title or "Vaga"
        
        if passed:
            email_template = EmailTemplates.screening_passed(
                candidate_name=candidate_name,
                job_title=job_title,
                strengths=strengths,
                company_name=company_name
            )
            whatsapp_message = WhatsAppTemplates.screening_passed(
                candidate_name=candidate_name,
                strengths=strengths
            )
            message_type = MessageType.SCREENING_PASSED
            template_name = "screening_passed"
        else:
            email_template = EmailTemplates.screening_failed(
                candidate_name=candidate_name,
                job_title=job_title,
                strengths=strengths,
                development_areas=development_areas
            )
            whatsapp_message = None
            message_type = MessageType.SCREENING_FAILED
            template_name = "screening_failed"
        
        if candidate_email:
            requires_approval = MESSAGE_REQUIRES_APPROVAL.get(message_type, True)
            
            if requires_approval:
                email_result = await self.create_approval_request(
                    company_id=company_id,
                    candidate_id=candidate_id,
                    candidate_name=candidate_name,
                    candidate_email=candidate_email,
                    candidate_phone=candidate_phone,
                    message_type=message_type,
                    channel=MessageChannel.EMAIL,
                    subject=email_template["subject"],
                    body=email_template["body"],
                    job_id=vacancy_id,
                    job_title=job_title,
                    requested_by="lia_agent",
                    priority="high" if passed else "normal",
                    extra_data={
                        "template_name": template_name,
                        "wsi_score": wsi_score,
                        "strengths": strengths,
                        "development_areas": development_areas
                    },
                    db=db
                )
                results["channels"]["email"] = {
                    "status": "pending_approval",
                    "approval_id": email_result.get("approval_id"),
                    "template_name": template_name
                }
                logger.info(f"📧 Email approval created for screening result: {candidate_id} - {'passed' if passed else 'failed'}")
            else:
                email_result = await self.send_message(
                    company_id=company_id,
                    candidate_id=candidate_id,
                    candidate_email=candidate_email,
                    candidate_phone=candidate_phone,
                    message_type=message_type,
                    channel=MessageChannel.EMAIL,
                    subject=email_template["subject"],
                    body=email_template["body"],
                    job_id=vacancy_id,
                    sent_by="lia_agent",
                    db=db
                )
                results["channels"]["email"] = {
                    "status": "sent" if email_result.get("success") else "failed",
                    "log_id": email_result.get("log_id"),
                    "template_name": template_name,
                    "error": email_result.get("error")
                }
                logger.info(f"📧 Email sent for screening result: {candidate_id} - {'passed' if passed else 'failed'}")
        else:
            results["channels"]["email"] = {
                "status": "skipped",
                "reason": "no_email_address"
            }
        
        if passed and candidate_phone and whatsapp_message:
            whatsapp_result = await self.send_message(
                company_id=company_id,
                candidate_id=candidate_id,
                candidate_email=candidate_email,
                candidate_phone=candidate_phone,
                message_type=MessageType.SCREENING_PASSED,
                channel=MessageChannel.WHATSAPP,
                subject=None,
                body=whatsapp_message,
                job_id=vacancy_id,
                sent_by="lia_agent",
                db=db
            )
            results["channels"]["whatsapp"] = {
                "status": "sent" if whatsapp_result.get("success") else "failed",
                "log_id": whatsapp_result.get("log_id"),
                "template_name": "screening_passed",
                "error": whatsapp_result.get("error")
            }
            logger.info(f"📱 WhatsApp sent for screening passed: {candidate_id}")
        elif passed and not candidate_phone:
            results["channels"]["whatsapp"] = {
                "status": "skipped",
                "reason": "no_phone_number"
            }
        
        has_failures = any(
            ch.get("status") == "failed" 
            for ch in results["channels"].values()
        )
        results["success"] = not has_failures
        
        logger.info(
            f"📨 Screening result dispatch complete for {candidate_id}: "
            f"passed={passed}, wsi_score={wsi_score}, channels={list(results['channels'].keys())}"
        )
        
        return results

    async def process_queued_messages(
        self,
        db: AsyncSession | None = None
    ) -> dict[str, Any]:
        """Process messages that were queued for later sending."""
        if not self._is_within_sending_hours():
            return {
                "processed": 0,
                "message": "Outside sending hours"
            }
        
        should_close = False
        if db is None:
            db = AsyncSessionLocal()
            should_close = True
        
        try:
            now = datetime.utcnow()
            
            result = await db.execute(
                select(CommunicationLog).where(
                    and_(
                        CommunicationLog.status == CommunicationStatus.QUEUED.value,
                        or_(
                            CommunicationLog.next_retry_at.is_(None),
                            CommunicationLog.next_retry_at <= now
                        )
                    )
                ).limit(100)
            )
            
            queued_logs = list(result.scalars())
            processed = 0
            
            for log in queued_logs:
                recipient = log.candidate_email if log.channel == "email" else log.candidate_phone
                
                if not recipient:
                    log.status = CommunicationStatus.FAILED.value
                    log.error_message = "No recipient address"
                    continue
                
                success, msg_id, response = await self._send_with_retry(
                    MessageChannel(log.channel),
                    recipient,
                    log.subject,
                    log.body,
                    log.body_html,
                    log,
                    db
                )
                
                if success:
                    log.status = CommunicationStatus.SENT.value
                    log.sent_at = datetime.utcnow()
                    log.provider_message_id = msg_id
                    log.provider_response = response or {}
                    processed += 1
                else:
                    log.status = CommunicationStatus.FAILED.value
                    log.failed_at = datetime.utcnow()
                    log.error_message = response.get("error") if response else "Unknown error"
            
            await db.commit()
            
            logger.info(f"📤 Processed {processed} queued messages")
            
            return {
                "processed": processed,
                "total_queued": len(queued_logs)
            }
            
        except Exception:
            try:
                await db.rollback()
            except Exception:
                pass
            raise
        finally:
            if should_close:
                await db.close()


communication_service = CommunicationService()


def get_communication_service() -> CommunicationService:
    return communication_service
