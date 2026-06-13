"""
EventsOutboxService — garantia de entrega para eventos criticos.

Harness: Guide computacional Sprint E.
  publish_via_outbox() = INSERT atomico (mesmo transaction do dominio)
  drain_to_pubsub() = le pending → publica no Redis → marca delivered

Fail-safe: se outbox falhar, cai para fire-and-forget (nunca bloqueia o dominio).

ADR Sprint E (2026-06-13): eventos criticos listados em CRITICAL_EVENT_TYPES
DEVEM usar publish_via_outbox() ao inves de publish_platform_event() direto.
Sensor: scripts/check_critical_events_use_outbox.py
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

# Module-level import so tests can patch app.shared.messaging.events_outbox_service.DomainEventsOutbox
try:
    from lia_models.domain_events_outbox import DomainEventsOutbox, OutboxStatus
except ImportError:
    DomainEventsOutbox = None  # type: ignore[assignment,misc]
    OutboxStatus = None  # type: ignore[assignment]

MAX_ATTEMPTS = 5
BATCH_SIZE = 50


class EventsOutboxService:
    """Gerencia o outbox de eventos de dominio."""

    async def publish_via_outbox(
        self,
        event: Any,
        db: "AsyncSession",
        *,
        fail_open: bool = True,
    ) -> bool:
        """
        Grava evento no domain_events_outbox (mesma transacao do dominio).

        Args:
            event: PlatformEvent subclass
            db: SQLAlchemy session (do dominio que esta chamando)
            fail_open: se True (default), falha silenciosa com fire-and-forget fallback

        Returns:
            True se gravou no outbox, False se usou fire-and-forget fallback
        """
        try:
            # Try to get correlation_id from request context
            correlation_id = None
            try:
                from app.middleware.request_id import get_correlation_id
                correlation_id = get_correlation_id()
            except Exception:
                pass

            record = DomainEventsOutbox(
                event_id=event.event_id,
                event_type=event.event_type,
                company_id=str(event.company_id),
                payload=event.model_dump(mode="json"),
                status=OutboxStatus.PENDING,
                correlation_id=event.correlation_id or correlation_id or None,
                source_api=getattr(event, "source_api", "lia-agent-system"),
                version=getattr(event, "version", "1.0"),
            )
            db.add(record)
            await db.flush()
            logger.debug(
                "[EventsOutbox] Queued: event_type=%s event_id=%s",
                event.event_type,
                event.event_id,
            )
            return True

        except Exception as exc:
            logger.warning(
                "[EventsOutbox] publish_via_outbox failed (fail_open=%s): %s",
                fail_open,
                exc,
            )
            if fail_open:
                # Fallback: fire-and-forget (sem garantia, mas nao bloqueia)
                await self._fire_and_forget(event)
            return False

    async def drain_to_pubsub(self, batch_size: int = BATCH_SIZE) -> int:
        """
        Le eventos pending do outbox e publica no Redis pub/sub.
        Retorna numero de eventos processados.
        Chamado por Celery task ou background worker.
        """
        from datetime import UTC, datetime

        from sqlalchemy import and_, select

        from app.shared.messaging.redis_pubsub_transport import (
            PLATFORM_EVENTS_CHANNEL,
            publish_event,
        )
        from lia_config.database import AsyncSessionLocal
        from lia_models.domain_events_outbox import DomainEventsOutbox, OutboxStatus

        processed = 0

        async with AsyncSessionLocal() as db:
            stmt = (
                select(DomainEventsOutbox)
                .where(
                    and_(
                        DomainEventsOutbox.status == OutboxStatus.PENDING,
                        DomainEventsOutbox.attempts < MAX_ATTEMPTS,
                    )
                )
                .order_by(DomainEventsOutbox.created_at)
                .limit(batch_size)
            )
            rows = (await db.execute(stmt)).scalars().all()

            for row in rows:
                try:
                    ok = await publish_event(PLATFORM_EVENTS_CHANNEL, row.payload)
                    if ok:
                        row.status = OutboxStatus.DELIVERED
                        row.delivered_at = datetime.now(UTC)
                        processed += 1
                    else:
                        row.attempts += 1
                        row.last_error = "Redis publish returned False"
                        if row.attempts >= MAX_ATTEMPTS:
                            row.status = OutboxStatus.DEAD_LETTER
                except Exception as exc:
                    row.attempts += 1
                    row.last_error = str(exc)[:500]
                    if row.attempts >= MAX_ATTEMPTS:
                        row.status = OutboxStatus.DEAD_LETTER
                    logger.error(
                        "[EventsOutbox] drain error event_id=%s: %s", row.event_id, exc
                    )

            await db.commit()

        logger.info("[EventsOutbox] drain_to_pubsub processed=%d", processed)
        return processed

    async def _fire_and_forget(self, event: Any) -> None:
        """Fallback: publica diretamente no Redis sem outbox."""
        try:
            from app.shared.messaging.platform_events import publish_platform_event

            await publish_platform_event(event)
        except Exception as exc:
            logger.error("[EventsOutbox] fire_and_forget also failed: %s", exc)


# Singleton
_outbox_service: EventsOutboxService | None = None


def get_events_outbox_service() -> EventsOutboxService:
    global _outbox_service
    if _outbox_service is None:
        _outbox_service = EventsOutboxService()
    return _outbox_service
