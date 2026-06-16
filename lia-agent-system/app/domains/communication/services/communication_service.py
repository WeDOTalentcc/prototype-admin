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
import random
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import Any

from app.domains.communication.repositories.communication_repository import CommunicationRepository
from app.domains.candidates.repositories.candidate_repository import CandidateRepository
from sqlalchemy import and_, desc, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.domains.communication.services.communication_models import (
    CandidateOptOut,
    CandidateQuarantine,
    CommunicationLog,
    PendingApproval,
)
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


@asynccontextmanager
async def _get_db(db: AsyncSession | None = None):
    """Async context manager for DB session lifecycle.

    If *db* is already provided the caller owns the session and we just
    yield it back.  When *db* is ``None`` we create a fresh
    ``AsyncSessionLocal`` and close it on exit.
    """
    should_close = db is None
    if should_close:
        db = AsyncSessionLocal()
    try:
        yield db
    finally:
        if should_close:
            await db.close()



# GAP-07-005: channel -> legacy channel_opt_out JSONB flag
_CHANNEL_TO_JSONB_FLAG: dict[str, str] = {
    "email":    "marketing_email",
    "whatsapp": "whatsapp",
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
    
    def _is_within_sending_hours(self, settings: dict | None = None) -> bool:
        """Check if current time is within allowed sending hours.

        WT-2022 P0.SCH1 (Wave 2 2026-05-22): tenant-aware com timezone +
        respect_holidays wired. settings dict pode override defaults:
          - sending_hours_start (int, default 8)
          - sending_hours_end (int, default 20)
          - respect_weekends (bool, default True)
          - respect_holidays (bool, default False) - Wave 2 P0.SCH-1
          - timezone (str IANA, default America/Sao_Paulo) - Wave 2 P0.SCH-1
        Backward-compat: settings=None usa defaults canonical (UTC-3 hardcoded).
        Helper: get_company_communication_settings em
        app/shared/services/communication_settings_consumer.py.
        """
        s = settings or {}

        # WT-2022 Wave 2 P0.SCH-1: tenant-aware timezone (default UTC-3 BR).
        # Helper get_tenant_now le settings["timezone"] e cai em UTC-3 fail-safe.
        if settings:
            from app.shared.services.communication_settings_consumer import get_tenant_now
            now = get_tenant_now(settings)
        else:
            now = self._get_brazil_now()

        respect_weekends = bool(s.get("respect_weekends", True))
        respect_holidays = bool(s.get("respect_holidays", False))
        start_hour = int(s.get("sending_hours_start", self.SENDING_START_HOUR))
        end_hour = int(s.get("sending_hours_end", self.SENDING_END_HOUR))

        if respect_weekends and now.weekday() >= 5:
            return False

        # WT-2022 Wave 2 P0.SCH-1: respect_holidays wire (national BR holidays only).
        # Estaduais/municipais ficam pra proxima sprint (exige UF tenant-aware).
        if respect_holidays:
            from app.shared.services.communication_settings_consumer import is_brazilian_holiday
            if is_brazilian_holiday(now.date()):
                return False

        current_hour = now.hour
        return start_hour <= current_hour < end_hour
    
    def _is_holiday_now(self, settings: dict | None = None) -> bool:
        """WT-2022 Wave 2 P0.SCH-1: check se data atual (tenant tz) é feriado BR.

        Usado pra rotular skip metric (holiday vs outside_hours). Não decide
        envio — esse é _is_within_sending_hours quem faz.
        """
        try:
            from app.shared.services.communication_settings_consumer import (
                get_tenant_now,
                is_brazilian_holiday,
            )
            now = get_tenant_now(settings) if settings else self._get_brazil_now()
            return is_brazilian_holiday(now.date())
        except Exception as e:
            logger.warning("[communication] Holiday check failed, defaulting to False: %s", e, exc_info=True)
            return False

    def _get_next_sending_window(self, settings: dict | None = None) -> datetime:
        """Get the next valid sending window.

        P0-W1-04 fix: aceita settings do tenant para usar sending_hours_start/end
        configurados, em vez das constantes hardcoded SENDING_START_HOUR/END_HOUR.
        LGPD Art. 7: limites configurados pelo responsavel devem ser respeitados.

        Backward-compat: settings=None usa defaults canonical (UTC-3 hardcoded, 8h-20h).
        """
        s = settings or {}
        start_hour = int(s.get("sending_hours_start", self.SENDING_START_HOUR))
        end_hour = int(s.get("sending_hours_end", self.SENDING_END_HOUR))
        respect_weekends = bool(s.get("respect_weekends", True))

        if settings:
            from app.shared.services.communication_settings_consumer import get_tenant_now
            brazil_now = get_tenant_now(settings)
        else:
            brazil_now = self._get_brazil_now()

        if respect_weekends and brazil_now.weekday() >= 5:
            days_until_monday = 7 - brazil_now.weekday()
            next_window = brazil_now.replace(
                hour=start_hour, minute=0, second=0, microsecond=0
            ) + timedelta(days=days_until_monday)
        elif brazil_now.hour >= end_hour:
            if respect_weekends and brazil_now.weekday() == 4:
                next_window = brazil_now.replace(
                    hour=start_hour, minute=0, second=0, microsecond=0
                ) + timedelta(days=3)
            else:
                next_window = brazil_now.replace(
                    hour=start_hour, minute=0, second=0, microsecond=0
                ) + timedelta(days=1)
        elif brazil_now.hour < start_hour:
            next_window = brazil_now.replace(
                hour=start_hour, minute=0, second=0, microsecond=0
            )
        else:
            next_window = brazil_now

        if settings:
            # get_tenant_now ja retorna hora local -- nao tem offset UTC para desfazer
            return next_window
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
        
        logs = await CommunicationRepository(db).list_logs_since(
            candidate_id=candidate_id,
            company_id=company_id,
            since=today_start,
            statuses=["sent", "delivered", "read"],
        )
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
        opt_out = await CommunicationRepository(db).get_active_optout(
            candidate_id=candidate_id,
            company_id=company_id,
            channel_value=channel.value,
        )
        if opt_out:
            return True, opt_out

        # GAP-07-005: fallback — legacy JSONB written by email_tracking/optout handlers
        jsonb_flag = _CHANNEL_TO_JSONB_FLAG.get(channel.value)
        if jsonb_flag:
            try:
                candidate = await CandidateRepository(db).get_by_id(candidate_id)
                if candidate and candidate.channel_opt_out and jsonb_flag in candidate.channel_opt_out:
                    return True, None
            except Exception:
                logger.warning("_check_opt_out: JSONB fallback failed for %s", candidate_id)

        return False, None

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
        
        quarantine = await CommunicationRepository(db).get_active_quarantine(
            candidate_id=candidate_id,
            company_id=company_id,
            now=now,
        )
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

        Checks (in order): LGPD consent → opt-out → quarantine → rate limit → hours.
        Returns validation result with details about any blocking issues.
        """
        async with _get_db(db) as db:
            result = {
                "can_send": True,
                "requires_approval": MESSAGE_REQUIRES_APPROVAL.get(message_type, True),
                "warnings": [],
                "blocks": []
            }

            # --- LGPD Consent Gate (fail-closed) ---
            from app.domains.communication.services.consent_gate import CommunicationConsentGate

            consent_gate = CommunicationConsentGate(db)
            is_marketing = message_type.value in (
                "initial_contact", "follow_up", "general",
            )
            consent_result = await consent_gate.check(
                candidate_id, company_id, channel, is_marketing=is_marketing,
            )
            if not consent_result.allowed:
                result["can_send"] = False
                result["blocks"].append({
                    "type": "lgpd_consent",
                    "message": (
                        f"Candidato não tem consentimento LGPD para {channel.value} "
                        f"(motivo: {consent_result.reason})"
                    ),
                    "consent_type": consent_result.consent_type,
                    "reason": consent_result.reason,
                })
                return result  # Consent block is final — skip remaining checks

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

            # WT-2022 P0.SCH1 (Wave 2 2026-05-22): tenant-aware settings — sending
            # hours + cooldown + max_per_candidate + holidays wired in single load.
            from app.shared.services.communication_settings_consumer import (
                get_company_communication_settings,
                check_cooldown_hours,
                check_max_per_candidate,
                inc_communication_skip,
            )
            settings = await get_company_communication_settings(db, company_id)

            # Cooldown gate (was ghost setting — wired Wave 2).
            cooldown_ok, cooldown_reason = await check_cooldown_hours(
                db, candidate_id, company_id, settings
            )
            if not cooldown_ok:
                inc_communication_skip("cooldown")
                cooldown_h = int(settings.get("cooldown_hours_between_messages", 24) or 24)
                result["can_send"] = False
                result["blocks"].append({
                    "type": "cooldown",
                    "message": f"Aguarde {cooldown_h}h desde última mensagem (cooldown_hours_between_messages)",
                })

            # Max-per-candidate rolling 7d window (was ghost setting — wired Wave 2).
            max_ok, max_reason = await check_max_per_candidate(
                db, candidate_id, company_id, settings
            )
            if not max_ok:
                inc_communication_skip("max_per_candidate")
                max_cand = int(settings.get("max_messages_per_candidate", 5) or 5)
                result["can_send"] = False
                result["blocks"].append({
                    "type": "max_per_candidate",
                    "message": f"Limite máximo de {max_cand} mensagens em 7 dias atingido (max_messages_per_candidate)",
                })

            if not self._is_within_sending_hours(settings):
                # Sensor: outside_hours / holiday breakdown
                if settings.get("respect_holidays") and self._is_holiday_now(settings):
                    inc_communication_skip("holiday")
                else:
                    inc_communication_skip("outside_hours")
                next_window = self._get_next_sending_window(settings)
                # P0-W1-04: mostrar janela real do tenant, nao hardcoded 8h-20h.
                _start = int(settings.get("sending_hours_start", self.SENDING_START_HOUR)) if settings else self.SENDING_START_HOUR
                _end = int(settings.get("sending_hours_end", self.SENDING_END_HOUR)) if settings else self.SENDING_END_HOUR
                _resp_wknd = bool(settings.get("respect_weekends", True)) if settings else True
                _window_desc = f"{_start}h-{_end}h {'dias uteis' if _resp_wknd else 'qualquer dia'}"
                result["warnings"].append({
                    "type": "outside_hours",
                    "message": f"Fora do horario de envio ({_window_desc})",
                    "next_window": next_window.isoformat(),
                    "will_queue": True
                })

            return result
    
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
        async with _get_db(db) as db:
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
                
                logger.info(f"📝 Approval request created: {approval.id} for {candidate_id}")
                
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
    
    async def _process_review(
        self,
        approval_id: str,
        action: str,
        reviewed_by: str,
        review_notes: str | None = None,
        modified_subject: str | None = None,
        modified_body: str | None = None,
        send_immediately: bool = False,
        db: AsyncSession | None = None,
    ) -> dict[str, Any]:
        """Shared logic for approve_request and reject_request.

        Args:
            action: Either ``"approve"`` or ``"reject"``.
        """
        new_status = (
            ApprovalStatus.APPROVED.value if action == "approve"
            else ApprovalStatus.REJECTED.value
        )

        async with _get_db(db) as db:
            try:
                approval = await CommunicationRepository(db).get_pending_approval_by_id(approval_id)

                if not approval:
                    return {"success": False, "error": "not_found"}

                if approval.status != ApprovalStatus.PENDING.value:
                    return {"success": False, "error": "already_processed", "status": approval.status}

                approval.status = new_status
                approval.reviewed_by = reviewed_by
                approval.reviewed_at = datetime.utcnow()
                approval.review_notes = review_notes

                if action == "approve":
                    approval.modified_subject = modified_subject
                    approval.modified_body = modified_body

                await db.commit()
                await db.refresh(approval)

                if action == "approve":
                    logger.info(f"✅ Approval approved: {approval_id} by {reviewed_by}")
                else:
                    logger.info(f"❌ Approval rejected: {approval_id} by {reviewed_by}")

                communication_result = None
                if action == "approve" and send_immediately:
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

                resp: dict[str, Any] = {
                    "success": True,
                    "approval": approval.to_dict(),
                }
                if communication_result is not None:
                    resp["communication_result"] = communication_result
                return resp

            except Exception:
                try:
                    await db.rollback()
                except Exception:
                    pass
                raise

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
        return await self._process_review(
            approval_id=approval_id,
            action="approve",
            reviewed_by=reviewed_by,
            review_notes=review_notes,
            modified_subject=modified_subject,
            modified_body=modified_body,
            send_immediately=send_immediately,
            db=db,
        )
    
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
        return await self._process_review(
            approval_id=approval_id,
            action="reject",
            reviewed_by=reviewed_by,
            review_notes=review_notes,
            db=db,
        )
    
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
        async with _get_db(db) as db:
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
            
            # ADR-001-EXEMPT: dynamic where conditions list + computed order-by;
            # promoting to repo would require leaking SQLAlchemy expressions. Sprint 6 follow-up.
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
        async with _get_db(db) as db:
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

                # WT-2022 P0.SCH1: tenant-aware sending hours via communication_settings.
                from app.shared.services.communication_settings_consumer import (
                    get_company_communication_settings,
                )
                settings = await get_company_communication_settings(db, company_id)
                if not self._is_within_sending_hours(settings):
                    next_window = self._get_next_sending_window(settings)
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
                    from app.shared.services.event_dispatcher import event_dispatcher
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
                
                # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
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
                except Exception as e:
                    logger.debug("[communication] template_learning record_send skipped: %s", e)

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
        async with _get_db(db) as db:
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
        async with _get_db(db) as db:
            try:
                opt_out = await CommunicationRepository(db).get_active_optout_for_channel(
                    candidate_id=candidate_id,
                    company_id=company_id,
                    channel_value=channel.value,
                )
                
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
        async with _get_db(db) as db:
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
    
    async def lift_quarantine(
        self,
        quarantine_id: str,
        lifted_by: str,
        lift_reason: str,
        db: AsyncSession | None = None
    ) -> dict[str, Any]:
        """Lift a quarantine early."""
        async with _get_db(db) as db:
            try:
                quarantine = await CommunicationRepository(db).get_quarantine_by_id(quarantine_id)
                
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
        async with _get_db(db) as db:
            conditions = [
                CommunicationLog.company_id == company_id,
                CommunicationLog.candidate_id == candidate_id
            ]
            
            if channel:
                conditions.append(CommunicationLog.channel == channel.value)
            if status:
                conditions.append(CommunicationLog.status == status.value)
            
            # ADR-001-EXEMPT: dynamic where conditions list (channel/status filters built inline).
            # Sprint 6 follow-up: promote to repo with kwarg-driven filter helper.
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
    
    async def get_daily_stats(
        self,
        company_id: str,
        date: datetime | None = None,
        db: AsyncSession | None = None
    ) -> dict[str, Any]:
        """Get daily communication statistics."""
        async with _get_db(db) as db:
            if date is None:
                date = datetime.utcnow()
            
            day_start = date.replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = day_start + timedelta(days=1)
            
            logs = await CommunicationRepository(db).list_logs_in_day(
                company_id=company_id, day_start=day_start, day_end=day_end
            )
            
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
        """Process messages that were queued for later sending.

        WT-2022 P0.SCH1: tenant-aware sending hours. O gate global (defaults
        canonical 8h-20h dias úteis) atua como fast-path conservador: se TODOS
        os tenants estão fora da janela default, pulamos o batch inteiro.
        Dentro do loop, cada log é re-checado contra communication_settings
        do tenant específico (`log.company_id`) — tenant com janela estendida
        (ex: 22h cutoff) pode enviar mesmo quando o default já fechou.
        """
        if not self._is_within_sending_hours():
            return {
                "processed": 0,
                "message": "Outside sending hours"
            }

        async with _get_db(db) as db:
            try:
                from app.shared.services.communication_settings_consumer import (
                    get_company_communication_settings,
                )

                now = datetime.utcnow()

                queued_logs = await CommunicationRepository(db).list_queued_logs_for_retry(
                    now=now,
                    queued_status=CommunicationStatus.QUEUED.value,
                    limit=100,
                )
                processed = 0
                skipped_tenant_hours = 0
                # Cache settings per company_id pra evitar refetch dentro do batch.
                settings_cache: dict[str, dict] = {}

                for log in queued_logs:
                    recipient = log.candidate_email if log.channel == "email" else log.candidate_phone

                    if not recipient:
                        log.status = CommunicationStatus.FAILED.value
                        log.error_message = "No recipient address"
                        continue

                    # WT-2022 P0.SCH1: per-tenant sending hours check.
                    tenant_id = str(log.company_id) if log.company_id else None
                    if tenant_id:
                        if tenant_id not in settings_cache:
                            settings_cache[tenant_id] = await get_company_communication_settings(
                                db, tenant_id
                            )
                        if not self._is_within_sending_hours(settings_cache[tenant_id]):
                            # Tenant ainda fora da própria janela — re-queue (não falha).
                            skipped_tenant_hours += 1
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

                logger.info(
                    "📤 Processed %d queued messages (skipped_tenant_hours=%d)",
                    processed, skipped_tenant_hours,
                )

                return {
                    "processed": processed,
                    "total_queued": len(queued_logs),
                    "skipped_tenant_hours": skipped_tenant_hours,
                }
                
            except Exception:
                try:
                    await db.rollback()
                except Exception:
                    pass
                raise


communication_service = CommunicationService()


def get_communication_service() -> CommunicationService:
    return communication_service
