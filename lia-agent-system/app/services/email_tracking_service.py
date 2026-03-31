"""
Email Tracking Service — COMP-7.

Tracking pixel (open) + link redirect (click).
LGPD Art. 7 VI: base legal = interesse legítimo.
SHA256 hash para IP e email (nunca armazena plaintext de PII).

Features:
  - generate_tracking_token(notification_id, company_id) → token
  - record_open(token, ip, user_agent)
  - record_click(token, link_url, ip, user_agent)
  - get_stats(notification_id, company_id) → dict
"""
import hashlib
import os
import secrets
import logging
import urllib.parse
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

_TRACKING_BASE_URL = os.getenv("API_BASE_URL", "https://api.wedotalent.com")

from app.models.email_tracking import EmailTrackingEvent

logger = logging.getLogger(__name__)


def _sha256(value: str) -> str:
    """SHA256 hash one-way — nunca armazena PII reversível."""
    return hashlib.sha256(value.encode()).hexdigest()


def _hash_ip(ip: Optional[str]) -> Optional[str]:
    """Hash SHA256 do IP do cliente."""
    return _sha256(ip) if ip else None


def _hash_email(email: Optional[str]) -> Optional[str]:
    """Hash SHA256 do email do destinatário."""
    return _sha256(email.lower().strip()) if email else None


class EmailTrackingService:
    """Tracking de abertura e clique em emails enviados pela plataforma."""

    def generate_tracking_token(
        self,
        notification_id: str,
        company_id: str,
        recipient_email: Optional[str] = None,
    ) -> str:
        """
        Gera token único para tracking de abertura.

        Token é URL-safe, 32 bytes aleatórios.
        Não contém PII — o mapeamento notification_id ↔ token é feito na tabela.
        """
        return secrets.token_urlsafe(32)

    async def create_tracking_token(
        self,
        db: AsyncSession,
        notification_id: str,
        company_id: str,
        recipient_email: Optional[str] = None,
    ) -> str:
        """
        Persiste token de tracking e retorna token string.
        """
        token = self.generate_tracking_token(notification_id, company_id, recipient_email)
        event = EmailTrackingEvent(
            notification_id=notification_id,
            company_id=company_id,
            token=token,
            event_type="token",  # Token criado, ainda não usado
            recipient_hash=_hash_email(recipient_email),
        )
        db.add(event)
        await db.flush()
        return token

    async def record_open(
        self,
        db: AsyncSession,
        token: str,
        ip: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> bool:
        """
        Registra abertura de email (pixel 1x1).

        Returns:
            True se token válido e evento registrado, False caso contrário.
        """
        # Buscar token base para pegar notification_id e company_id
        stmt = select(EmailTrackingEvent).where(
            EmailTrackingEvent.token == token,
            EmailTrackingEvent.event_type == "token",
        )
        result = await db.execute(stmt)
        base_event = result.scalar_one_or_none()

        if not base_event:
            logger.debug("[EmailTracking] Token inválido: %s", token[:16])
            return False

        open_event = EmailTrackingEvent(
            notification_id=base_event.notification_id,
            company_id=base_event.company_id,
            token=f"{token}:open:{secrets.token_hex(8)}",  # token único por open
            event_type="open",
            recipient_hash=base_event.recipient_hash,
            ip_hash=_hash_ip(ip),
            user_agent=(user_agent or "")[:500],  # limitar user-agent
        )
        db.add(open_event)
        await db.commit()
        logger.debug("[EmailTracking] open registrado notification=%s", base_event.notification_id)
        return True

    async def record_click(
        self,
        db: AsyncSession,
        token: str,
        link_url: str,
        ip: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Optional[str]:
        """
        Registra clique em link e retorna URL de destino para redirect.

        Returns:
            URL de destino para redirecionar o usuário, ou None se token inválido.
        """
        stmt = select(EmailTrackingEvent).where(
            EmailTrackingEvent.token == token,
            EmailTrackingEvent.event_type == "token",
        )
        result = await db.execute(stmt)
        base_event = result.scalar_one_or_none()

        if not base_event:
            logger.debug("[EmailTracking] Token clique inválido: %s", token[:16])
            return None

        click_event = EmailTrackingEvent(
            notification_id=base_event.notification_id,
            company_id=base_event.company_id,
            token=f"{token}:click:{secrets.token_hex(8)}",
            event_type="click",
            recipient_hash=base_event.recipient_hash,
            ip_hash=_hash_ip(ip),
            user_agent=(user_agent or "")[:500],
            link_url=link_url[:2000],  # limitar URL
        )
        db.add(click_event)
        await db.commit()
        return link_url

    async def get_stats(
        self,
        db: AsyncSession,
        notification_id: str,
        company_id: str,
    ) -> Dict[str, Any]:
        """
        Retorna estatísticas de tracking para uma notificação.

        Returns:
            Dict com opens, clicks, unique_opens (por recipient_hash).
        """
        # Contagem por tipo
        stmt = (
            select(EmailTrackingEvent.event_type, func.count().label("count"))
            .where(
                EmailTrackingEvent.notification_id == notification_id,
                EmailTrackingEvent.company_id == company_id,
                EmailTrackingEvent.event_type.in_(["open", "click"]),
            )
            .group_by(EmailTrackingEvent.event_type)
        )
        result = await db.execute(stmt)
        counts = {row.event_type: row.count for row in result}

        # Unique opens por recipient
        stmt_unique = (
            select(func.count(EmailTrackingEvent.recipient_hash.distinct()).label("unique_opens"))
            .where(
                EmailTrackingEvent.notification_id == notification_id,
                EmailTrackingEvent.company_id == company_id,
                EmailTrackingEvent.event_type == "open",
                EmailTrackingEvent.recipient_hash.isnot(None),
            )
        )
        result_unique = await db.execute(stmt_unique)
        unique_opens = result_unique.scalar() or 0

        return {
            "notification_id": notification_id,
            "opens": counts.get("open", 0),
            "clicks": counts.get("click", 0),
            "unique_opens": unique_opens,
        }


    async def record_webhook_event(
        self,
        db: AsyncSession,
        sg_message_id: str,
        event_type: str,
        email: Optional[str] = None,
        ip: Optional[str] = None,
        user_agent: Optional[str] = None,
        url: Optional[str] = None,
        timestamp: Optional[int] = None,
        raw_event: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Record an event received from SendGrid Event Webhook.

        Maps sg_message_id to a notification_id by looking up MessageQueue.
        Falls back to storing with sg_message_id as notification_id.
        """
        notification_id = sg_message_id
        company_id = ""

        try:
            from app.models.message_queue import MessageQueue
            stmt = select(MessageQueue.id, MessageQueue.company_id).where(
                MessageQueue.extra_data["sg_message_id"].astext == sg_message_id,
            ).limit(1)
            result = await db.execute(stmt)
            row = result.first()
            if row:
                notification_id = str(row.id)
                company_id = str(row.company_id or "")
        except Exception:
            pass

        event_time = None
        if timestamp:
            try:
                event_time = datetime.fromtimestamp(int(timestamp), tz=timezone.utc)
            except (ValueError, OSError):
                pass

        tracking_event = EmailTrackingEvent(
            notification_id=notification_id,
            company_id=company_id,
            token=f"webhook:{sg_message_id}:{event_type}:{secrets.token_hex(4)}",
            event_type=event_type,
            recipient_hash=_hash_email(email),
            ip_hash=_hash_ip(ip),
            user_agent=(user_agent or "")[:500],
            link_url=(url or "")[:2000] if url else None,
        )
        db.add(tracking_event)

        _STATUS_MAP = {
            "delivered": "delivered",
            "open": "opened",
            "click": "clicked",
            "bounce": "bounced",
            "dropped": "failed",
            "spamreport": "spam_reported",
            "unsubscribe": "unsubscribed",
        }
        if notification_id != sg_message_id and event_type in _STATUS_MAP:
            try:
                from app.models.message_queue import MessageQueue
                from sqlalchemy import update as sql_update
                await db.execute(
                    sql_update(MessageQueue)
                    .where(MessageQueue.id == notification_id)
                    .values(
                        status=_STATUS_MAP[event_type],
                        updated_at=datetime.now(timezone.utc),
                    )
                )
            except Exception as status_exc:
                logger.debug("[EmailTracking] communication status update skipped: %s", status_exc)

    async def resolve_company_template(
        self,
        db: AsyncSession,
        sg_message_id: str,
    ) -> tuple:
        """Resolve company_id and template_id from sg_message_id via MessageQueue.

        Returns:
            Tuple of (company_id, template_id). Empty strings if not found.
        """
        try:
            from app.models.message_queue import MessageQueue
            stmt = select(
                MessageQueue.company_id,
                MessageQueue.extra_data,
            ).where(
                MessageQueue.extra_data["sg_message_id"].astext == sg_message_id,
            ).limit(1)
            result = await db.execute(stmt)
            row = result.first()
            if row:
                company_id = str(row.company_id or "")
                extra = row.extra_data or {}
                template_id = extra.get("template_id", "")
                return (company_id, template_id)
        except Exception:
            pass
        return ("", "")

    def inject_pixel_and_links(
        self,
        html_body: str,
        token: str,
        action_url: Optional[str] = None,
        base_url: str = _TRACKING_BASE_URL,
    ) -> str:
        """
        Injeta pixel de rastreamento 1×1 no HTML e envolve action_url com redirect.

        LGPD Art. 7 VI: base legal = interesse legítimo (melhoria do serviço de notificação).
        Sem PII no HTML — apenas token opaco.

        Args:
            html_body: HTML original do email.
            token: Token gerado por generate_tracking_token().
            action_url: URL de ação principal a ser rastreada (opcional).
            base_url: Base da API de tracking (override para testes).

        Returns:
            HTML modificado com pixel e, opcionalmente, link de clique rastreado.
        """
        pixel_url = f"{base_url}/api/v1/email-tracking/pixel/{token}.gif"
        pixel_tag = (
            f'\n<img src="{pixel_url}" width="1" height="1" alt="" '
            f'style="display:none;border:0;" />'
        )

        if "</body>" in html_body:
            html_body = html_body.replace("</body>", f"{pixel_tag}\n</body>", 1)
        else:
            html_body = html_body + pixel_tag

        if action_url:
            encoded = urllib.parse.quote(action_url, safe="")
            click_url = f"{base_url}/api/v1/email-tracking/click/{token}?url={encoded}"
            # Substitui apenas a primeira ocorrência da URL no atributo href
            html_body = html_body.replace(f'href="{action_url}"', f'href="{click_url}"', 1)

        return html_body


email_tracking_service = EmailTrackingService()
