import logging
from typing import Any

from app.shared.channels.channel_adapter import (
    ChannelAdapter,
    ChannelMessage,
    ChannelType,
    DeliveryResult,
    DeliveryStatus,
)

logger = logging.getLogger(__name__)


class ChannelRouter:
    def __init__(self, adapters: dict[ChannelType, ChannelAdapter]):
        self._adapters = adapters

    async def route(
        self,
        message: ChannelMessage,
        preferred_channels: list[ChannelType],
        fallback: bool = True,
        db: Any | None = None,
    ) -> DeliveryResult:
        channels_to_try = list(preferred_channels)

        if fallback:
            for channel_type in self._adapters:
                if channel_type not in channels_to_try:
                    channels_to_try.append(channel_type)

        logger.info(
            f"[CHANNEL_ROUTER] Roteando mensagem para {message.recipient_name}. "
            f"Canais: {[c.value for c in channels_to_try]}"
        )

        if db is not None:
            if message.metadata is None:
                message.metadata = {"_db": db}
            else:
                message.metadata["_db"] = db

        company_id: str | None = message.company_id or None

        for channel_type in channels_to_try:
            adapter = self._adapters.get(channel_type)
            if not adapter:
                logger.debug(
                    f"[CHANNEL_ROUTER] Adaptador não encontrado: {channel_type.value}"
                )
                continue

            try:
                available = await adapter.is_available(company_id=company_id, db=db)
                if not available:
                    logger.info(
                        f"[CHANNEL_ROUTER] Canal indisponível: {channel_type.value}"
                    )
                    continue

                if not adapter.validate_contact(message.recipient_contact):
                    logger.info(
                        f"[CHANNEL_ROUTER] Contato inválido para {channel_type.value}: "
                        f"{message.recipient_contact}"
                    )
                    continue

                logger.info(
                    f"[CHANNEL_ROUTER] Tentando enviar via {channel_type.value}"
                )
                result = await adapter.send(message)

                if result.success:
                    logger.info(
                        f"[CHANNEL_ROUTER] Mensagem enviada com sucesso via "
                        f"{channel_type.value}: {result.message_id}"
                    )
                    return result

                logger.warning(
                    f"[CHANNEL_ROUTER] Falha ao enviar via {channel_type.value}: "
                    f"{result.error}"
                )

                if not fallback:
                    return result

            except Exception as e:
                logger.error(
                    f"[CHANNEL_ROUTER] Erro no canal {channel_type.value}: {e}",
                    exc_info=True,
                )
                if not fallback:
                    return DeliveryResult(
                        success=False,
                        channel=channel_type,
                        message_id="",
                        status=DeliveryStatus.FAILED,
                        error=str(e),
                    )

        logger.error(
            f"[CHANNEL_ROUTER] Todos os canais falharam para {message.recipient_name}"
        )
        return DeliveryResult(
            success=False,
            channel=preferred_channels[0] if preferred_channels else ChannelType.EMAIL,
            message_id="",
            status=DeliveryStatus.FAILED,
            error="Todos os canais de comunicação falharam",
        )
