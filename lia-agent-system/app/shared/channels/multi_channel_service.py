import logging
from typing import Any, Optional


from app.shared.channels.adapters.email_adapter import EmailChannelAdapter
from app.shared.channels.adapters.in_app_adapter import InAppChannelAdapter
from app.shared.channels.adapters.sms_adapter import SMSChannelAdapter
from app.shared.channels.adapters.teams_adapter import MSTeamsChannelAdapter
from app.shared.channels.adapters.whatsapp_adapter import WhatsAppChannelAdapter
from app.shared.channels.adapters.voice_adapter import VoiceChannelAdapter
from app.shared.channels.channel_adapter import (
    ChannelAdapter,
    ChannelMessage,
    ChannelType,
    DeliveryResult,
    DeliveryStatus,
)
from app.shared.channels.channel_router import ChannelRouter

logger = logging.getLogger(__name__)


class MultiChannelService:
    _instance: Optional["MultiChannelService"] = None

    def __init__(self):
        self._adapters: dict[ChannelType, ChannelAdapter] = {}
        self._router: ChannelRouter | None = None
        self._auto_register()

    @classmethod
    def get_instance(cls) -> "MultiChannelService":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _auto_register(self):
        default_adapters = [
            EmailChannelAdapter(),
            WhatsAppChannelAdapter(),
            SMSChannelAdapter(),
            InAppChannelAdapter(),
            MSTeamsChannelAdapter(),
            VoiceChannelAdapter(),  # Sprint 3.4 W4-1 V2: generic voice (no plugins)
        ]
        for adapter in default_adapters:
            self.register_adapter(adapter)

    def register_adapter(self, adapter: ChannelAdapter):
        self._adapters[adapter.channel_type] = adapter
        self._router = ChannelRouter(self._adapters)
        logger.debug(
            f"[MULTI_CHANNEL] Adaptador registrado: {adapter.channel_type.value}"
        )

    async def send_message(
        self,
        message: ChannelMessage,
        channels: list[ChannelType] | None = None,
        fallback: bool = True,
        db: Optional[Any] = None,
    ) -> DeliveryResult:
        if channels is None:
            channels = [ChannelType.EMAIL]

        logger.info(
            f"[MULTI_CHANNEL] Enviando mensagem para {message.recipient_name} "
            f"via {[c.value for c in channels]}"
        )

        return await self._router.route(message, channels, fallback=fallback, db=db)

    async def send_bulk(
        self,
        messages: list[ChannelMessage],
        channel: ChannelType,
        db: Optional[Any] = None,
    ) -> list[DeliveryResult]:
        logger.info(
            f"[MULTI_CHANNEL] Envio em massa: {len(messages)} mensagens via {channel.value}"
        )

        results = []
        for msg in messages:
            try:
                result = await self.send_message(msg, channels=[channel], fallback=False, db=db)
                results.append(result)
            except Exception as e:
                logger.error(
                    f"[MULTI_CHANNEL] Erro no envio em massa para "
                    f"{msg.recipient_name}: {e}"
                )
                results.append(
                    DeliveryResult(
                        success=False,
                        channel=channel,
                        message_id="",
                        status=DeliveryStatus.FAILED,
                        error=str(e),
                    )
                )

        sent = sum(1 for r in results if r.success)
        logger.info(
            f"[MULTI_CHANNEL] Envio em massa concluído: {sent}/{len(messages)} enviados"
        )
        return results

    async def get_delivery_status(self, message_id: str) -> DeliveryStatus | None:
        for adapter in self._adapters.values():
            try:
                status = await adapter.check_status(message_id)
                if status != DeliveryStatus.FAILED:
                    return status
            except Exception:
                continue
        return None

    async def get_available_channels(
        self,
        company_id: Optional[str] = None,
        db: Optional[Any] = None,
    ) -> list[dict]:
        channels = []
        for channel_type, adapter in self._adapters.items():
            try:
                available = await adapter.is_available(company_id=company_id, db=db)
            except Exception:
                available = False
            channels.append({
                "channel": channel_type.value,
                "available": available,
            })
        return channels


multi_channel_service = MultiChannelService.get_instance()
