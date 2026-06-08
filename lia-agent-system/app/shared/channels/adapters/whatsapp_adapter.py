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


class WhatsAppChannelAdapter(ChannelAdapter):
    channel_type = ChannelType.WHATSAPP

    _PHONE_REGEX = re.compile(r"^\+?\d{10,15}$")

    def validate_contact(self, contact: str) -> bool:
        cleaned = re.sub(r"[\s\-\(\)]", "", contact)
        return bool(self._PHONE_REGEX.match(cleaned))

    async def is_available(self, company_id: str | None = None, db: "Any | None" = None) -> bool:
        try:
            from app.domains.communication.services.whatsapp_factory import WhatsAppProviderFactory
            meta = WhatsAppProviderFactory.get_meta_provider()
            twilio = WhatsAppProviderFactory.get_twilio_provider()
            return meta.is_configured or twilio.is_configured
        except Exception as e:
            logger.warning(f"[WHATSAPP_ADAPTER] Erro ao verificar disponibilidade: {e}")
            return False

    async def send(self, message: ChannelMessage) -> DeliveryResult:
        message_id = str(uuid.uuid4())
        try:
            if not self.validate_contact(message.recipient_contact):
                logger.warning(
                    f"[WHATSAPP_ADAPTER] Número inválido: {message.recipient_contact}"
                )
                return DeliveryResult(
                    success=False,
                    channel=self.channel_type,
                    message_id=message_id,
                    status=DeliveryStatus.FAILED,
                    error="Formato de número de telefone inválido",
                )

            from app.domains.communication.services.whatsapp_factory import WhatsAppProviderFactory

            provider = await WhatsAppProviderFactory.get_provider(message.company_id)

            if not provider.is_configured:
                logger.warning("[WHATSAPP_ADAPTER] Nenhum provedor WhatsApp configurado")
                return DeliveryResult(
                    success=False,
                    channel=self.channel_type,
                    message_id=message_id,
                    status=DeliveryStatus.FAILED,
                    error="Nenhum provedor WhatsApp configurado",
                )

            text = message.body_text or ""
            if message.subject:
                text = f"*{message.subject}*\n\n{text}"

            result = await provider.send_text_message(
                to=message.recipient_contact,
                text=text,
            )

            if result.success:
                logger.info(
                    f"[WHATSAPP_ADAPTER] Mensagem enviada: {result.message_id} "
                    f"para {message.recipient_contact}"
                )
                return DeliveryResult(
                    success=True,
                    channel=self.channel_type,
                    message_id=message_id,
                    status=DeliveryStatus.SENT,
                    provider_id=result.message_id,
                    metadata={"provider": result.provider},
                )

            logger.warning(
                f"[WHATSAPP_ADAPTER] Falha ao enviar: {result.error}"
            )
            return DeliveryResult(
                success=False,
                channel=self.channel_type,
                message_id=message_id,
                status=DeliveryStatus.FAILED,
                error=result.error,
            )

        except Exception as e:
            logger.error(
                f"[WHATSAPP_ADAPTER] Erro ao enviar mensagem: {e}", exc_info=True
            )
            return DeliveryResult(
                success=False,
                channel=self.channel_type,
                message_id=message_id,
                status=DeliveryStatus.FAILED,
                error=str(e),
            )

    async def check_status(self, message_id: str) -> DeliveryStatus:
        return DeliveryStatus.SENT
