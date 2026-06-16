"""
Rails CRUD Event Consumer — listens to events published by Rails ats_api.

Exchange: lia_rails_events (direct, durable)
Events: candidate.created/updated, job.created/updated, apply.created/updated

Reliability (PE-4):
  - DLQ: failed messages dead-letter to lia_fastapi.rails_crud_events.dlq via DLX
  - Retry: RabbitMQ x-death header tracks retry count, max MAX_RETRIES
  - After max retries: nack(requeue=False) → routed to DLQ for manual triage

Started via: await rails_crud_consumer.start()
"""
import asyncio
import json
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

EXCHANGE_NAME = "lia_rails_events"
QUEUE_NAME = "lia_fastapi.rails_crud_events"

# PE-4: Dead-letter infrastructure
DLX_NAME = f"{EXCHANGE_NAME}.dlx"
DLQ_NAME = f"{QUEUE_NAME}.dlq"
MAX_RETRIES = 3

_EMBEDDING_EVENTS = {
    "candidate.created", "candidate.updated",
    "job.created", "job.updated",
}
_LOG_ONLY_EVENTS = {"apply.created", "apply.updated"}


def _get_retry_count(message) -> int:
    """Extract retry count from x-death header (incremented by RabbitMQ on each dead-letter)."""
    try:
        x_death = message.headers.get("x-death") if message.headers else None
        if x_death and isinstance(x_death, list) and x_death:
            return int(x_death[0].get("count", 0))
    except Exception:
        pass
    return 0


async def _handle_embedding(event: dict) -> None:
    """Generate embedding for candidate or job. Raises on failure to trigger retry/DLQ."""
    from app.domains.ai.services.domain_embedding_service import DomainEmbeddingService
    from app.core.database import get_async_session

    event_type = event.get("event_type", "")
    source_type = "candidate" if "candidate" in event_type else "job"
    source_id = str(event.get(f"{source_type}_id", ""))
    company_id = str(event.get("company_id", ""))
    content = event.get("content") or event.get("name") or event.get("title") or ""

    if not source_id or not company_id:
        # Permanent error — no retry would fix this. Log and ack.
        logger.warning("[RailsCRUD] Missing IDs in %s: %s — discarding", event_type, event)
        return

    svc = DomainEmbeddingService()
    async with get_async_session() as db:
        ok = await svc.embed_document(content, source_type, source_id, company_id, db)
        if ok:
            logger.info("[RailsCRUD] Embedded %s id=%s", source_type, source_id)
        else:
            # Transient — raise to trigger retry via DLX
            raise RuntimeError(f"Embedding returned False for {source_type} id={source_id}")


async def _process_message(message) -> None:
    """Route a single message; on failure use retry + DLQ (PE-4)."""
    retry_count = _get_retry_count(message)

    try:
        event = json.loads(message.body.decode())
        event_type = event.get("event_type", "")

        if event_type in _EMBEDDING_EVENTS:
            await _handle_embedding(event)
        elif event_type in _LOG_ONLY_EVENTS:
            logger.info("[RailsCRUD] %s apply_id=%s (logged)", event_type, event.get("apply_id"))
        else:
            logger.debug("[RailsCRUD] Unknown event: %s", event_type)

        await message.ack()

    except json.JSONDecodeError as exc:
        # Permanent — bad JSON cannot be fixed by retry. Send to DLQ immediately.
        logger.error("[RailsCRUD] Invalid JSON, sending to DLQ: %s", exc)
        await message.reject(requeue=False)

    except Exception as exc:
        if retry_count >= MAX_RETRIES:
            logger.error(
                "[RailsCRUD] Max retries (%d) exhausted, sending to DLQ. event_type=%s err=%s",
                MAX_RETRIES,
                (event.get("event_type") if "event" in locals() else "?"),
                exc,
            )
            await message.reject(requeue=False)
        else:
            logger.warning(
                "[RailsCRUD] Processing error (retry %d/%d): %s",
                retry_count + 1, MAX_RETRIES, exc,
            )
            # nack with requeue=False routes to DLX which puts it back in main queue
            # via TTL mechanism — RabbitMQ increments x-death.count automatically
            await message.reject(requeue=False)


class RailsCRUDConsumer:
    def __init__(self):
        self._connection = None
        self._running = False

    async def start(self) -> None:
        rabbitmq_url = getattr(settings, "RABBITMQ_URL", None)
        if not rabbitmq_url:
            logger.warning("[RailsCRUD] RABBITMQ_URL not set — consumer inactive")
            return
        try:
            import aio_pika
            self._connection = await aio_pika.connect_robust(rabbitmq_url)
            channel = await self._connection.channel()
            await channel.set_qos(prefetch_count=10)

            # Main exchange (events from Rails)
            exchange = await channel.declare_exchange(
                EXCHANGE_NAME, aio_pika.ExchangeType.DIRECT, durable=True,
            )

            # PE-4: Dead-letter exchange + queue
            dlx = await channel.declare_exchange(
                DLX_NAME, aio_pika.ExchangeType.FANOUT, durable=True,
            )
            dlq = await channel.declare_queue(DLQ_NAME, durable=True)
            await dlq.bind(dlx)

            # Main queue with DLX configured
            queue = await channel.declare_queue(
                QUEUE_NAME,
                durable=True,
                arguments={
                    "x-dead-letter-exchange": DLX_NAME,
                },
            )
            for key in (*_EMBEDDING_EVENTS, *_LOG_ONLY_EVENTS):
                await queue.bind(exchange, routing_key=key)

            await queue.consume(_process_message)
            self._running = True
            logger.info(
                "[RailsCRUD] Consumer started — exchange=%s queue=%s dlq=%s max_retries=%d",
                EXCHANGE_NAME, QUEUE_NAME, DLQ_NAME, MAX_RETRIES,
            )
        except Exception as exc:
            logger.error("[RailsCRUD] Failed to start: %s", exc)

    async def stop(self) -> None:
        self._running = False
        if self._connection and not self._connection.is_closed:
            await self._connection.close()
        logger.info("[RailsCRUD] Consumer stopped")


rails_crud_consumer = RailsCRUDConsumer()
