import base64
import logging
import re
import uuid
from datetime import datetime

from sqlalchemy import select, and_

from app.shared.channels.channel_adapter import (
    ChannelAdapter, ChannelType, ChannelMessage, DeliveryResult, DeliveryStatus
)
from app.core.database import AsyncSessionLocal
from app.models.message_queue import MessageQueue, MessageStatus, MessageChannel, MessagePriority

logger = logging.getLogger(__name__)

# F7 — Footer obrigatório em emails gerados por IA (LGPD + EU AI Act / PL em tramitação)
AI_GENERATED_FOOTER = (
    "\n\n---\n"
    "*Esta mensagem foi gerada com assistência de Inteligência Artificial "
    "pela plataforma LIA (WeDOTalent).*"
)


def _add_ai_footer(body_text: str | None, body_html: str | None) -> tuple[str | None, str | None]:
    """Adiciona footer de IA ao corpo do email se ainda não presente."""
    marker = "WeDOTalent"
    if body_text and marker not in body_text:
        body_text = body_text + AI_GENERATED_FOOTER
    if body_html and marker not in body_html:
        footer_html = (
            "<br><hr><p><small><em>"
            "Esta mensagem foi gerada com assistência de Inteligência Artificial "
            "pela plataforma LIA (WeDOTalent)."
            "</em></small></p>"
        )
        body_html = body_html + footer_html
    return body_text, body_html


async def _is_opted_out(email: str) -> bool:
    """Check if candidate has opted out of email communications (LGPD)."""
    try:
        from app.domains.analytics.models.observability import ConsentEvent
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(ConsentEvent.id).where(
                    and_(
                        ConsentEvent.subject_email == email,
                        ConsentEvent.event_type == "revoked",
                        ConsentEvent.consent_given == False,
                    )
                ).limit(1)
            )
            return result.scalar_one_or_none() is not None
    except Exception as e:
        logger.debug(f"[EMAIL_ADAPTER] Opt-out check failed (fail-open): {e}")
        return False


def _generate_unsubscribe_url(email: str, company_id: str) -> str:
    """Generate unsubscribe URL token for email opt-out link."""
    token = base64.urlsafe_b64encode(f"{email}:{company_id}".encode()).decode()
    return f"/api/v1/communication/unsubscribe/{token}"


class EmailChannelAdapter(ChannelAdapter):
    channel_type = ChannelType.EMAIL

    _EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")

    def validate_contact(self, contact: str) -> bool:
        return bool(self._EMAIL_REGEX.match(contact))

    async def is_available(self) -> bool:
        return True

    async def send(self, message: ChannelMessage) -> DeliveryResult:
        message_id = str(uuid.uuid4())

        # I5: LGPD opt-out check before sending
        if await _is_opted_out(message.recipient_contact):
            logger.info(f"[EMAIL_ADAPTER] Skipping email to {message.recipient_contact} — opted out (LGPD)")
            return DeliveryResult(
                success=False,
                channel=self.channel_type,
                message_id=message_id,
                status=DeliveryStatus.FAILED,
                error="Candidato optou por não receber comunicações (LGPD Art. 8°, §5°)",
            )

        try:
            # I5: Auto-inject unsubscribe URL into template variables
            if not (message.template_vars or {}).get("unsubscribe_url"):
                if message.template_vars is None:
                    message.template_vars = {}
                message.template_vars["unsubscribe_url"] = _generate_unsubscribe_url(
                    message.recipient_contact, message.company_id or "system"
                )

            # F7 — Adicionar footer de IA em emails gerados por agentes LIA
            if getattr(message, "ai_generated", False) or getattr(message, "source_agent", None):
                message.body_text, message.body_html = _add_ai_footer(
                    message.body_text, message.body_html
                )

            if not self.validate_contact(message.recipient_contact):
                logger.warning(f"[EMAIL_ADAPTER] Email inválido: {message.recipient_contact}")
                return DeliveryResult(
                    success=False,
                    channel=self.channel_type,
                    message_id=message_id,
                    status=DeliveryStatus.FAILED,
                    error="Formato de email inválido",
                )

            async with AsyncSessionLocal() as db:
                queue_entry = MessageQueue(
                    id=message_id,
                    company_id=message.company_id or "system",
                    candidate_id=message.recipient_id,
                    candidate_name=message.recipient_name,
                    candidate_email=message.recipient_contact,
                    vacancy_id=message.vacancy_id,
                    channel=MessageChannel.EMAIL,
                    message_type="multi_channel",
                    priority=MessagePriority.NORMAL,
                    subject=message.subject or "",
                    body_html=message.body_html,
                    body_text=message.body_text,
                    template_id=message.template_id,
                    template_variables=message.template_vars or {},
                    status=MessageStatus.SENT,
                    sent_at=datetime.utcnow(),
                    created_by="multi_channel_service",
                    extra_data=message.metadata or {},
                )
                db.add(queue_entry)
                await db.commit()

            logger.info(
                f"[EMAIL_ADAPTER] Email enfileirado: {message_id} para {message.recipient_contact}"
            )

            return DeliveryResult(
                success=True,
                channel=self.channel_type,
                message_id=message_id,
                status=DeliveryStatus.QUEUED,
                metadata={"smtp_configured": False},
            )

        except Exception as e:
            logger.error(f"[EMAIL_ADAPTER] Erro ao enviar email: {e}", exc_info=True)
            return DeliveryResult(
                success=False,
                channel=self.channel_type,
                message_id=message_id,
                status=DeliveryStatus.FAILED,
                error=str(e),
            )

    async def check_status(self, message_id: str) -> DeliveryStatus:
        try:
            from sqlalchemy import select

            async with AsyncSessionLocal() as db:
                result = await db.execute(
                    select(MessageQueue.status).where(MessageQueue.id == message_id)
                )
                status = result.scalar_one_or_none()
                if status:
                    status_map = {
                        MessageStatus.PENDING: DeliveryStatus.QUEUED,
                        MessageStatus.PROCESSING: DeliveryStatus.QUEUED,
                        MessageStatus.SENT: DeliveryStatus.SENT,
                        MessageStatus.DELIVERED: DeliveryStatus.DELIVERED,
                        MessageStatus.FAILED: DeliveryStatus.FAILED,
                        MessageStatus.BOUNCED: DeliveryStatus.BOUNCED,
                    }
                    return status_map.get(status, DeliveryStatus.QUEUED)
        except Exception as e:
            logger.error(f"[EMAIL_ADAPTER] Erro ao verificar status: {e}")
        return DeliveryStatus.QUEUED
