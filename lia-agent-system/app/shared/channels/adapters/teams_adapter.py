import logging
import os
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
        """
        Return True only when a viable delivery path exists.

        Priority: 1) TEAMS_WEBHOOK_URL env var, 2) teams_service singleton webhook_url
        (which is set from env or an explicit TeamsService(webhook_url=...) instance),
        3) DB-configured per-tenant URL (checked lazily via teams_service reference).

        Both TeamsBot._deliver_card() and TeamsService.send_message() fall back
        to the incoming webhook; without it neither path can deliver messages.
        Bot Framework credentials (MICROSOFT_APP_ID/PASSWORD) are used for proactive
        sends when a conversation_reference is supplied, but are not sufficient alone.
        """
        webhook_url = os.environ.get("TEAMS_WEBHOOK_URL")
        if webhook_url:
            return True
        # Also consider per-tenant URL configured at the service level (e.g. via DB-backed
        # TeamsService instantiation). The global singleton reflects env-only config; callers
        # that resolved a per-tenant URL pass it via webhook_url= override on send_message().
        try:
            from app.domains.communication.services.teams_service import teams_service as _svc
            if _svc.webhook_url:
                return True
        except Exception:
            pass
        logger.debug(
            "[TEAMS_ADAPTER] TEAMS_WEBHOOK_URL não configurada e teams_service sem URL "
            "— canal Teams indisponível para entregas via webhook global"
        )
        return False

    async def send(self, message: ChannelMessage) -> DeliveryResult:
        message_id = str(uuid.uuid4())
        try:
            from app.domains.communication.services.teams_bot import teams_bot

            title = message.subject or "Notificação LIA"
            body = message.body_text or ""

            if message.metadata and message.metadata.get("adaptive_card"):
                card_payload = message.metadata["adaptive_card"]
                success = await teams_bot._deliver_card(card_payload)
            else:
                card_payload = _build_simple_card(title, body)
                success = await teams_bot._deliver_card(card_payload)

            if success:
                logger.info(
                    f"[TEAMS_ADAPTER] Mensagem enviada via Teams: {message_id}"
                )
                return DeliveryResult(
                    success=True,
                    channel=self.channel_type,
                    message_id=message_id,
                    status=DeliveryStatus.SENT,
                    provider_id=message_id,
                    metadata={"provider": "teams_bot"},
                )

            logger.warning(
                "[TEAMS_ADAPTER] Falha ao enviar via TeamsBot — tentando TeamsService"
            )
            from app.domains.communication.services.teams_service import teams_service

            result = await teams_service.send_message(
                text=body,
                title=title,
            )
            if result.get("success"):
                logger.info(
                    f"[TEAMS_ADAPTER] Mensagem enviada via TeamsService: {message_id}"
                )
                return DeliveryResult(
                    success=True,
                    channel=self.channel_type,
                    message_id=message_id,
                    status=DeliveryStatus.SENT,
                    provider_id=message_id,
                    metadata={"provider": "teams_service", "mode": result.get("mode")},
                )

            error_msg = result.get("error", "Falha desconhecida ao enviar via Teams")
            logger.error(f"[TEAMS_ADAPTER] Falha ao enviar: {error_msg}")
            return DeliveryResult(
                success=False,
                channel=self.channel_type,
                message_id=message_id,
                status=DeliveryStatus.FAILED,
                error=error_msg,
            )

        except Exception as e:
            logger.error(f"[TEAMS_ADAPTER] Erro inesperado: {e}", exc_info=True)
            return DeliveryResult(
                success=False,
                channel=self.channel_type,
                message_id=message_id,
                status=DeliveryStatus.FAILED,
                error=str(e),
            )

    async def check_status(self, message_id: str) -> DeliveryStatus:
        return DeliveryStatus.SENT


def _build_simple_card(title: str, body: str) -> dict:
    return {
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "type": "AdaptiveCard",
        "version": "1.4",
        "body": [
            {
                "type": "TextBlock",
                "text": title,
                "weight": "Bolder",
                "size": "Medium",
                "wrap": True,
            },
            {
                "type": "TextBlock",
                "text": body,
                "wrap": True,
                "spacing": "Small",
            },
        ],
    }
