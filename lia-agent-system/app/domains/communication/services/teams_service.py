"""
Microsoft Teams Service - Incoming Webhook integration.

This service handles sending messages to Microsoft Teams channels using Incoming Webhooks.
Different from the Bot Framework integration (teams_simple.py), this uses simple HTTP POST
to Teams Incoming Webhook URLs for channel notifications.

Environment Variables:
- TEAMS_WEBHOOK_URL: Default Teams Incoming Webhook URL for notifications
"""
import logging
import os
from datetime import datetime
from enum import Enum, StrEnum
from typing import Any

import httpx

from app.core.config import settings
from app.shared.security.url_validator import UnsafeOutboundURLError, safe_outbound_url

logger = logging.getLogger(__name__)


class AlertSeverity(StrEnum):
    """Alert severity levels for Teams notifications."""
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


SEVERITY_COLORS = {
    AlertSeverity.INFO: "#0078D4",
    AlertSeverity.SUCCESS: "#107C10",
    AlertSeverity.WARNING: "#FFB900",
    AlertSeverity.ERROR: "#D83B01",
    AlertSeverity.CRITICAL: "#E81123",
}

SEVERITY_ICONS = {
    AlertSeverity.INFO: "ℹ️",
    AlertSeverity.SUCCESS: "✅",
    AlertSeverity.WARNING: "⚠️",
    AlertSeverity.ERROR: "❌",
    AlertSeverity.CRITICAL: "🚨",
}


class TeamsService:
    """
    Service for sending messages to Microsoft Teams via Incoming Webhooks.
    
    This service provides methods to:
    - Send simple text messages
    - Send formatted Adaptive Cards
    - Send alerts with severity levels
    
    In development mode (when TEAMS_WEBHOOK_URL is not set), messages are logged instead of sent.
    """
    
    def __init__(self, webhook_url: str | None = None):
        """
        Initialize TeamsService.

        Args:
            webhook_url: Teams Incoming Webhook URL. If not provided, uses TEAMS_WEBHOOK_URL env var.

        How to obtain TEAMS_WEBHOOK_URL:
          1. Open the target Teams channel.
          2. Click the channel name → Manage channel → Connectors (or "..." → Connectors).
          3. Search for "Incoming Webhook" → Configure.
          4. Give it a name (e.g. "LIA Agent System") and click Create.
          5. Copy the generated URL and set it as the TEAMS_WEBHOOK_URL secret.
        """
        self.webhook_url = webhook_url or os.environ.get("TEAMS_WEBHOOK_URL")
        self.is_development = not self.webhook_url

        if self.is_development:
            logger.info(
                "TeamsService running in development mode — messages will be logged only. "
                "Set TEAMS_WEBHOOK_URL to enable outbound delivery to Teams channels."
            )
    
    async def send_message(
        self,
        text: str,
        webhook_url: str | None = None,
        title: str | None = None,
        subtitle: str | None = None,
    ) -> dict[str, Any]:
        """
        Send a simple text message to Teams channel.
        
        Args:
            text: Message text to send
            webhook_url: Override webhook URL (optional)
            title: Optional message title
            subtitle: Optional subtitle
            
        Returns:
            Result dict with success status and details
        """
        url = webhook_url or self.webhook_url
        
        if self.is_development and not url:
            logger.info(f"[TEAMS DEV] Message: {title or 'No title'} - {text}")
            return {
                "success": True,
                "mode": "development",
                "message": "Message logged (development mode)",
                "logged_at": datetime.utcnow().isoformat()
            }
        
        if not url:
            return {
                "success": False,
                "error": "No Teams webhook URL configured"
            }
        
        payload: dict[str, Any] = {
            "@type": "MessageCard",
            "@context": "http://schema.org/extensions",
            "themeColor": "0078D4",
            "text": text,
        }
        
        if title:
            payload["title"] = title
        
        if subtitle:
            payload["text"] = f"**{subtitle}**\n\n{text}"
        
        return await self._send_webhook(url, payload)
    
    async def send_card(
        self,
        card: dict[str, Any],
        webhook_url: str | None = None,
    ) -> dict[str, Any]:
        """
        Send a formatted Adaptive Card to Teams channel.
        
        Args:
            card: Adaptive Card payload (see Microsoft Adaptive Card schema)
            webhook_url: Override webhook URL (optional)
            
        Returns:
            Result dict with success status and details
        """
        url = webhook_url or self.webhook_url
        
        if self.is_development and not url:
            logger.info(f"[TEAMS DEV] Adaptive Card: {card}")
            return {
                "success": True,
                "mode": "development",
                "message": "Card logged (development mode)",
                "logged_at": datetime.utcnow().isoformat()
            }
        
        if not url:
            return {
                "success": False,
                "error": "No Teams webhook URL configured"
            }
        
        payload = {
            "type": "message",
            "attachments": [
                {
                    "contentType": "application/vnd.microsoft.card.adaptive",
                    "contentUrl": None,
                    "content": card
                }
            ]
        }
        
        return await self._send_webhook(url, payload)
    
    async def send_adaptive_card(
        self,
        card_payload: dict[str, Any],
        webhook_url: str | None = None
    ) -> dict[str, Any]:
        """
        Send an adaptive card to Teams channel.
        
        Args:
            card_payload: Adaptive card payload with attachments
            webhook_url: Override webhook URL (optional)
            
        Returns:
            Result dict with success status and details
        """
        url = webhook_url or self.webhook_url
        
        if self.is_development and not url:
            card_title = card_payload.get('attachments', [{}])[0].get('content', {}).get('body', [{}])[0].get('text', 'No title')
            logger.info(f"[TEAMS DEV] Adaptive Card: {card_title}")
            return {
                "success": True,
                "mode": "development",
                "message": "Adaptive card logged (development mode)",
                "logged_at": datetime.utcnow().isoformat()
            }
        
        if not url:
            return {
                "success": False,
                "error": "No webhook URL configured"
            }
        
        return await self._send_webhook(url, card_payload)
    
    async def send_alert(
        self,
        title: str,
        message: str,
        severity: AlertSeverity = AlertSeverity.INFO,
        webhook_url: str | None = None,
        facts: list[dict[str, str]] | None = None,
        actions: list[dict[str, Any]] | None = None,
        source: str | None = None,
    ) -> dict[str, Any]:
        """
        Send an alert with severity level to Teams channel.
        
        Args:
            title: Alert title
            message: Alert message/description
            severity: Severity level (info, success, warning, error, critical)
            webhook_url: Override webhook URL (optional)
            facts: List of key-value facts to display
            actions: List of action buttons
            source: Source system/agent that generated the alert
            
        Returns:
            Result dict with success status and details
        """
        url = webhook_url or self.webhook_url
        
        icon = SEVERITY_ICONS.get(severity, "ℹ️")
        SEVERITY_COLORS.get(severity, "#0078D4")
        
        if self.is_development and not url:
            logger.info(f"[TEAMS DEV] Alert [{severity.value}]: {icon} {title} - {message}")
            if facts:
                for fact in facts:
                    # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
                    logger.info(f"  - {fact.get('name')}: {fact.get('value')}")
            return {
                "success": True,
                "mode": "development",
                "message": "Alert logged (development mode)",
                "severity": severity.value,
                "logged_at": datetime.utcnow().isoformat()
            }
        
        if not url:
            return {
                "success": False,
                "error": "No Teams webhook URL configured"
            }
        
        card_body = [
            {
                "type": "TextBlock",
                "text": f"{icon} {title}",
                "weight": "Bolder",
                "size": "Medium",
                "wrap": True
            },
            {
                "type": "TextBlock",
                "text": message,
                "wrap": True,
                "spacing": "Small"
            }
        ]
        
        if source:
            card_body.append({
                "type": "TextBlock",
                "text": f"Fonte: {source}",
                "size": "Small",
                "isSubtle": True,
                "spacing": "Small"
            })
        
        if facts:
            fact_set = {
                "type": "FactSet",
                "facts": facts,
                "spacing": "Medium"
            }
            card_body.append(fact_set)
        
        card_body.append({
            "type": "TextBlock",
            "text": f"Enviado em: {datetime.utcnow().strftime('%d/%m/%Y %H:%M:%S')} UTC",
            "size": "Small",
            "isSubtle": True,
            "spacing": "Medium"
        })
        
        card = {
            "type": "AdaptiveCard",
            "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
            "version": "1.4",
            "body": card_body
        }
        
        if actions:
            card["actions"] = actions
        
        return await self.send_card(card, url)
    
    async def send_candidate_notification(
        self,
        candidate_name: str,
        event: str,
        job_title: str | None = None,
        details: str | None = None,
        action_url: str | None = None,
        webhook_url: str | None = None,
    ) -> dict[str, Any]:
        """
        Send a candidate-related notification to Teams.
        
        Args:
            candidate_name: Name of the candidate
            event: Event description (e.g., "moved to interview stage")
            job_title: Related job vacancy title
            details: Additional details
            action_url: URL to view more details
            webhook_url: Override webhook URL (optional)
            
        Returns:
            Result dict with success status and details
        """
        facts = [
            {"name": "Candidato", "value": candidate_name},
            {"name": "Evento", "value": event}
        ]
        
        if job_title:
            facts.append({"name": "Vaga", "value": job_title})
        
        actions = None
        if action_url:
            actions = [
                {
                    "type": "Action.OpenUrl",
                    "title": "Ver Detalhes",
                    "url": action_url
                }
            ]
        
        return await self.send_alert(
            title="Atualização de Candidato",
            message=details or f"{candidate_name} {event}",
            severity=AlertSeverity.INFO,
            webhook_url=webhook_url,
            facts=facts,
            actions=actions,
            source="LIA Agent System"
        )
    
    async def send_interview_reminder(
        self,
        candidate_name: str,
        job_title: str,
        interview_time: datetime,
        interviewer: str,
        meeting_url: str | None = None,
        webhook_url: str | None = None,
    ) -> dict[str, Any]:
        """
        Send an interview reminder to Teams.
        
        Args:
            candidate_name: Name of the candidate
            job_title: Job vacancy title
            interview_time: Scheduled interview time
            interviewer: Name of the interviewer
            meeting_url: URL to join the meeting
            webhook_url: Override webhook URL (optional)
            
        Returns:
            Result dict with success status and details
        """
        facts = [
            {"name": "Candidato", "value": candidate_name},
            {"name": "Vaga", "value": job_title},
            {"name": "Horário", "value": interview_time.strftime('%d/%m/%Y às %H:%M')},
            {"name": "Entrevistador", "value": interviewer}
        ]
        
        actions = []
        if meeting_url:
            actions.append({
                "type": "Action.OpenUrl",
                "title": "Entrar na Reunião",
                "url": meeting_url
            })
        
        return await self.send_alert(
            title="🗓️ Lembrete de Entrevista",
            message=f"Entrevista agendada com {candidate_name} para a vaga de {job_title}",
            severity=AlertSeverity.INFO,
            webhook_url=webhook_url,
            facts=facts,
            actions=actions if actions else None,
            source="LIA Agent System"
        )
    
    async def _send_webhook(self, url: str, payload: dict[str, Any]) -> dict[str, Any]:
        """
        Send payload to Teams Incoming Webhook.
        
        Args:
            url: Webhook URL
            payload: JSON payload to send
            
        Returns:
            Result dict with success status and details
        """
        try:
            safe_outbound_url(url, require_https=True)
        except UnsafeOutboundURLError as exc:
            logger.warning("TeamsService: blocked unsafe webhook URL: %s", exc)
            return {
                "success": False,
                "error": "Invalid or unsafe webhook URL"
            }
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(
                    url,
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    logger.info("Teams message sent successfully")
                    return {
                        "success": True,
                        "status_code": response.status_code,
                        "sent_at": datetime.utcnow().isoformat()
                    }
                else:
                    logger.error(f"Teams webhook failed: {response.status_code} - {response.text}")
                    return {
                        "success": False,
                        "status_code": response.status_code,
                        "error": response.text
                    }
                    
        except httpx.TimeoutException:
            logger.error("Teams webhook timeout")
            return {
                "success": False,
                "error": "Request timeout"
            }
        except Exception as e:
            logger.error(f"Teams webhook error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    # ── Offer event notifications (called from offer_portal.py, fail-soft) ──

    async def on_offer_viewed(
        self,
        offer_id: str,
        company_id: str,
        candidate_name: str,
    ) -> None:
        """Notify recruiter when candidate opens the offer portal link."""
        try:
            db_gen = get_db()
            db = await db_gen.__anext__()
            webhook_url, _ = await resolve_tenant_teams_webhook_url(company_id, db)
            await db_gen.aclose()
        except Exception:
            webhook_url = None

        if webhook_url:
            await self.send_alert(
                title="👁️ Proposta visualizada",
                message=f"{candidate_name} abriu o link da proposta.",
                severity=AlertSeverity.INFO,
                webhook_url=webhook_url,
                facts=[
                    {"name": "Candidato", "value": candidate_name},
                    {"name": "Proposta ID", "value": offer_id[:8] + "..."},
                ],
                source="Offer Portal",
            )

        # Fire automation trigger OFFER_VIEWED
        try:
            from app.domains.automation.services.automation_trigger_service import automation_trigger_service
            from app.shared.automation.trigger_types_canonical import TriggerType
            await automation_trigger_service.fire_offer_trigger(
                trigger_type=TriggerType.OFFER_VIEWED,
                offer_id=offer_id,
                company_id=company_id,
                candidate_name=candidate_name,
                metadata={"event": "offer_viewed"},
            )
        except Exception as _e:
            logger.debug("[teams_service] automation trigger OFFER_VIEWED skipped: %s", _e)

    async def on_offer_responded(
        self,
        offer_id: str,
        company_id: str,
        candidate_name: str,
        acao: str,
        notas: str | None = None,
    ) -> None:
        """Notify recruiter when candidate accepts or declines via portal."""
        is_accepted = acao == "aceitar"
        severity = AlertSeverity.SUCCESS if is_accepted else AlertSeverity.WARNING
        emoji = "✅" if is_accepted else "❌"
        acao_label = "aceitou" if is_accepted else "recusou"

        try:
            db_gen = get_db()
            db = await db_gen.__anext__()
            webhook_url, _ = await resolve_tenant_teams_webhook_url(company_id, db)
            await db_gen.aclose()
        except Exception:
            webhook_url = None

        if webhook_url:
            facts = [
                {"name": "Candidato", "value": candidate_name},
                {"name": "Decisão", "value": acao_label.capitalize()},
                {"name": "Proposta ID", "value": offer_id[:8] + "..."},
            ]
            if notas:
                facts.append({"name": "Observações", "value": notas[:200]})
            await self.send_alert(
                title=f"{emoji} Proposta {acao_label}",
                message=f"{candidate_name} {acao_label} a proposta.",
                severity=severity,
                webhook_url=webhook_url,
                facts=facts,
                source="Offer Portal",
            )

        # Fire OFFER_DECLINED or let OFFER_ACCEPTED flow through existing handler
        trigger_type_str = "offer_declined" if not is_accepted else "offer_accepted"
        try:
            from app.domains.automation.services.automation_trigger_service import automation_trigger_service
            from app.shared.automation.trigger_types_canonical import TriggerType
            tt = TriggerType.OFFER_DECLINED if not is_accepted else TriggerType.OFFER_ACCEPTED
            await automation_trigger_service.fire_offer_trigger(
                trigger_type=tt,
                offer_id=offer_id,
                company_id=company_id,
                candidate_name=candidate_name,
                metadata={"event": trigger_type_str, "notas": notas},
            )
        except Exception as _e:
            logger.debug("[teams_service] automation trigger %s skipped: %s", trigger_type_str, _e)


    async def on_offer_expired(
        self,
        offer_id: str,
        company_id: str,
        candidate_name: str,
    ) -> None:
        """Notify recruiter when an offer expires without candidate response."""
        try:
            db_gen = get_db()
            db = await db_gen.__anext__()
            webhook_url, _ = await resolve_tenant_teams_webhook_url(company_id, db)
            await db_gen.aclose()
        except Exception:
            webhook_url = None

        if webhook_url:
            await self.send_alert(
                title="⏰ Proposta expirada",
                message=f"A proposta para {candidate_name} expirou sem resposta.",
                severity=AlertSeverity.WARNING,
                webhook_url=webhook_url,
                facts=[
                    {"name": "Candidato", "value": candidate_name},
                    {"name": "Proposta ID", "value": offer_id[:8] + "..."},
                ],
                source="Offer Service",
            )

        try:
            from app.domains.automation.services.automation_trigger_service import automation_trigger_service
            from app.shared.automation.trigger_types_canonical import TriggerType
            await automation_trigger_service.fire_offer_trigger(
                trigger_type=TriggerType.OFFER_EXPIRED,
                offer_id=offer_id,
                company_id=company_id,
                candidate_name=candidate_name,
                metadata={"event": "offer_expired"},
            )
        except Exception as _e:
            logger.debug("[teams_service] automation trigger OFFER_EXPIRED skipped: %s", _e)


    async def test_connection(self, webhook_url: str | None = None) -> dict[str, Any]:
        """
        Test Teams webhook connection by sending a test message.
        
        Args:
            webhook_url: Webhook URL to test (optional, uses default if not provided)
            
        Returns:
            Result dict with success status and details
        """
        return await self.send_alert(
            title="Teste de Conexão",
            message="Esta é uma mensagem de teste do LIA Agent System. Se você está vendo isso, a integração está funcionando corretamente!",
            severity=AlertSeverity.SUCCESS,
            webhook_url=webhook_url,
            facts=[
                {"name": "Sistema", "value": "LIA Agent System"},
                {"name": "Ambiente", "value": settings.APP_ENV},
                {"name": "Teste", "value": "Conexão OK"}
            ],
            source="LIA Agent System - Teste"
        )


teams_service = TeamsService()


def get_teams_service() -> "TeamsService":
    return teams_service


async def resolve_tenant_teams_webhook_url(
    company_id: str,
    db: "Any",
) -> "tuple[str | None, str]":
    """Resolve the outbound Teams webhook URL for a tenant.

    Lookup priority:
      1. Per-tenant ``IntegrationConnection`` row (encrypted in DB).
      2. Global ``TEAMS_WEBHOOK_URL`` environment variable.
      3. ``("none", "none")`` — caller should treat as development/log-only mode.

    Returns:
        ``(url, source)`` where *source* is ``"db"``, ``"env"``, or ``"none"``.

    This function is the canonical resolver used by every outbound send path
    (API endpoints, background jobs, tool registry).  Callers that hold a DB
    session and a resolved ``company_id`` MUST use this instead of reading
    ``os.environ["TEAMS_WEBHOOK_URL"]`` directly so that per-tenant
    configuration is honoured.
    """
    try:
        from sqlalchemy import select as _sa_select

        from app.models.integration_hub import IntegrationConnection as _IC
        from app.models.integration_hub import IntegrationProvider as _IP
        from app.shared.services.credentials_crypto import decrypt_credentials as _decrypt

        _SLUG = "microsoft_teams"
        prov_res = await db.execute(
            _sa_select(_IP).where(_IP.slug == _SLUG)
        )
        provider = prov_res.scalar_one_or_none()
        if provider is not None:
            conn_res = await db.execute(
                _sa_select(_IC).where(
                    _IC.company_id == company_id,
                    _IC.provider_id == provider.id,
                )
            )
            conn = conn_res.scalar_one_or_none()
            if conn is not None and conn.credentials_encrypted:
                creds = _decrypt(conn.credentials_encrypted)
                url = creds.get("webhook_url")
                if url:
                    return url, "db"
    except Exception as _exc:
        logger.warning(
            "resolve_tenant_teams_webhook_url: DB lookup failed for company=%s: %s",
            company_id,
            _exc,
        )

    env_url = os.environ.get("TEAMS_WEBHOOK_URL")
    if env_url:
        return env_url, "env"
    return None, "none"
