import logging
import uuid
from datetime import datetime

from app.core.database import AsyncSessionLocal
from app.shared.channels.channel_adapter import (
    ChannelAdapter,
    ChannelMessage,
    ChannelType,
    DeliveryResult,
    DeliveryStatus,
)

logger = logging.getLogger(__name__)


class InAppChannelAdapter(ChannelAdapter):
    channel_type = ChannelType.IN_APP

    def validate_contact(self, contact: str) -> bool:
        return bool(contact and len(contact.strip()) > 0)

    async def is_available(self, company_id: str | None = None, db: "Any | None" = None) -> bool:
        return True

    async def send(self, message: ChannelMessage) -> DeliveryResult:
        message_id = str(uuid.uuid4())
        try:
            if not self.validate_contact(message.recipient_contact):
                logger.warning(
                    f"[IN_APP_ADAPTER] ID de usuário inválido: {message.recipient_contact}"
                )
                return DeliveryResult(
                    success=False,
                    channel=self.channel_type,
                    message_id=message_id,
                    status=DeliveryStatus.FAILED,
                    error="ID de usuário inválido",
                )

            from app.services.notification_service import Notification

            async with AsyncSessionLocal() as db:
                # RLS-EXEMPT: Notification here is the in-app message envelope (this Notification shadow is a non-ORM message DTO consumed by the in-app channel adapter; the ORM model is NotificationPolicy).  WT-LEGACY-RLS-EXEMPT exp:2026-11-30
                notification = Notification(
                    id=message_id,
                    user_id=message.recipient_contact,
                    title=message.subject or "Nova notificação",
                    message=message.body_text,
                    notification_type="info",
                    category="multi_channel",
                    priority="normal",
                    source_agent="multi_channel_service",
                    related_job_id=message.vacancy_id,
                    related_candidate_id=message.recipient_id,
                    channels=["in_app"],
                    channels_sent=["in_app"],
                    extra_data=message.metadata or {},
                    created_at=datetime.utcnow(),
                )
                db.add(notification)
                await db.commit()

            logger.info(
                f"[IN_APP_ADAPTER] Notificação criada: {message_id} "
                f"para usuário {message.recipient_contact}"
            )

            return DeliveryResult(
                success=True,
                channel=self.channel_type,
                message_id=message_id,
                status=DeliveryStatus.DELIVERED,
            )

        except Exception as e:
            try:
                await db.rollback()
            except Exception:
                pass
            logger.error(
                f"[IN_APP_ADAPTER] Erro ao criar notificação: {e}", exc_info=True
            )
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

            from app.services.notification_service import Notification

            async with AsyncSessionLocal() as db:
                result = await db.execute(
                    select(Notification.is_read).where(Notification.id == message_id)
                )
                is_read = result.scalar_one_or_none()
                if is_read is not None:
                    return DeliveryStatus.READ if is_read else DeliveryStatus.DELIVERED
        except Exception as e:
            logger.error(f"[IN_APP_ADAPTER] Erro ao verificar status: {e}")
        return DeliveryStatus.DELIVERED
