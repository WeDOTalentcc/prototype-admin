import logging
import re
import uuid

from app.shared.channels.channel_adapter import (
    ChannelAdapter,
    ChannelMessage,
    ChannelType,
    DeliveryResult,
    DeliveryStatus,
)

logger = logging.getLogger(__name__)


class SMSChannelAdapter(ChannelAdapter):
    channel_type = ChannelType.SMS

    _PHONE_REGEX = re.compile(r"^\+?\d{10,15}$")

    def validate_contact(self, contact: str) -> bool:
        cleaned = re.sub(r"[\s\-\(\)]", "", contact)
        return bool(self._PHONE_REGEX.match(cleaned))

    async def is_available(self, company_id: str | None = None, db: "Any | None" = None) -> bool:
        return False

    async def send(self, message: ChannelMessage) -> DeliveryResult:
        logger.info("[SMS_ADAPTER] Canal SMS não configurado")
        return DeliveryResult(
            success=False,
            channel=self.channel_type,
            message_id=str(uuid.uuid4()),
            status=DeliveryStatus.FAILED,
            error="Canal SMS não disponível. Integração Twilio SMS pendente.",
        )

    async def check_status(self, message_id: str) -> DeliveryStatus:
        return DeliveryStatus.FAILED
