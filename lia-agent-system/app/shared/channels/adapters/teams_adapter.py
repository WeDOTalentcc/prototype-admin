import logging
import uuid

from app.shared.channels.channel_adapter import (
    ChannelAdapter,
    ChannelMessage,
    ChannelType,
    DeliveryResult,
    DeliveryStatus,
)

logger = logging.getLogger(__name__)


class MSTeamsChannelAdapter(ChannelAdapter):
    channel_type = ChannelType.MS_TEAMS

    def validate_contact(self, contact: str) -> bool:
        return bool(contact and len(contact.strip()) > 0)

    async def is_available(self) -> bool:
        return False

    async def send(self, message: ChannelMessage) -> DeliveryResult:
        logger.info("[TEAMS_ADAPTER] Canal MS Teams não configurado")
        return DeliveryResult(
            success=False,
            channel=self.channel_type,
            message_id=str(uuid.uuid4()),
            status=DeliveryStatus.FAILED,
            error="Canal MS Teams não disponível. Integração Microsoft Graph pendente.",
        )

    async def check_status(self, message_id: str) -> DeliveryStatus:
        return DeliveryStatus.FAILED
