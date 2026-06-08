import logging
import os
import uuid
from typing import Any

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

    async def is_available(
        self,
        company_id: str | None = None,
        db: Any | None = None,
    ) -> bool:
        """
        Return True only when a viable delivery path exists.

        Priority:
          1. TEAMS_WEBHOOK_URL env var (global fallback)
          2. Per-tenant webhook_url resolved from IntegrationConnection row in DB
             (when company_id + db are supplied by the caller)
          3. teams_service singleton webhook_url (set from env or explicit instantiation)

        When company_id and db are provided the per-tenant URL is checked via
        resolve_tenant_teams_webhook_url so that tenants that have only a
        DB-stored URL are NOT silently dropped.
        """
        webhook_url = os.environ.get("TEAMS_WEBHOOK_URL")
        if webhook_url:
            return True

        if company_id and db:
            try:
                from app.domains.communication.services.teams_service import (
                    resolve_tenant_teams_webhook_url,
                )

                url, source = await resolve_tenant_teams_webhook_url(company_id, db)
                if url:
                    logger.debug(
                        "[TEAMS_ADAPTER] Per-tenant Teams URL resolved "
                        "(company=%s, source=%s) — canal disponível",
                        company_id,
                        source,
                    )
                    return True
            except Exception as exc:
                logger.warning(
                    "[TEAMS_ADAPTER] Falha ao resolver URL por tenant "
                    "(company=%s): %s",
                    company_id,
                    exc,
                )

        try:
            from app.domains.communication.services.teams_service import teams_service as _svc

            if _svc.webhook_url:
                return True
        except Exception:
            pass

        logger.debug(
            "[TEAMS_ADAPTER] TEAMS_WEBHOOK_URL não configurada, nenhuma URL por "
            "tenant encontrada e teams_service sem URL "
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

            resolved_webhook_url: str | None = None
            db = message.metadata.get("_db") if message.metadata else None
            if message.company_id and db:
                try:
                    from app.domains.communication.services.teams_service import (
                        resolve_tenant_teams_webhook_url,
                    )

                    resolved_webhook_url, _source = await resolve_tenant_teams_webhook_url(
                        message.company_id, db
                    )
                    if resolved_webhook_url:
                        logger.debug(
                            "[TEAMS_ADAPTER] Usando URL por tenant para fallback "
                            "(company=%s, source=%s)",
                            message.company_id,
                            _source,
                        )
                except Exception as exc:
                    logger.warning(
                        "[TEAMS_ADAPTER] Falha ao resolver URL por tenant no fallback "
                        "(company=%s): %s",
                        message.company_id,
                        exc,
                    )

            from app.domains.communication.services.teams_service import teams_service

            result = await teams_service.send_message(
                text=body,
                title=title,
                webhook_url=resolved_webhook_url or None,
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
