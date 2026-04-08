"""
Rails CRUD Event Consumer — listens to events published by Rails ats_api.

Exchange: lia_rails_events (direct, durable)
Events: candidate.created/updated, job.created/updated, apply.created/updated

On candidate/job created → generate embedding for RAG search.
On apply events → log only (future: update pipeline).

Started via: await rails_crud_consumer.start()
"""
import asyncio
import json
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

EXCHANGE_NAME = "lia_rails_events"
QUEUE_NAME = "lia_fastapi.rails_crud_events"

_EMBEDDING_EVENTS = {
    "candidate.created", "candidate.updated",
    "job.created", "job.updated",
}
_LOG_ONLY_EVENTS = {"apply.created", "apply.updated"}


async def _handle_embedding(event: dict) -> None:
    """Generate embedding for candidate or job."""
    from app.domains.ai.services.domain_embedding_service import DomainEmbeddingService
    from app.core.database import get_async_session

    event_type = event.get("event_type", "")
    source_type = "candidate" if "candidate" in event_type else "job"
    source_id = str(event.get(f"{source_type}_id", ""))
    company_id = str(event.get("company_id", ""))
    content = event.get("content") or event.get("name") or event.get("title") or ""

    if not source_id or not company_id:
        logger.warning("[RailsCRUD] Missing IDs in %s: %s", event_type, event)
        return

    try:
        svc = DomainEmbeddingService()
        async with get_async_session() as db:
            ok = await svc.embed_document(content, source_type, source_id, company_id, db)
            if ok:
                logger.info("[RailsCRUD] Embedded %s id=%s", source_type, source_id)
            else:
                logger.warning("[RailsCRUD] Embedding failed for %s id=%s", source_type, source_id)
    except Exception as exc:
        logger.error("[RailsCRUD] Embedding error %s: %s", event_type, exc)


async def _process_message(message) -> None:
    """Route a single message to the appropriate handler."""
    async with message.process():
        try:
            event = json.loads(message.body.decode())
            event_type = event.get("event_type", "")

            if event_type in _EMBEDDING_EVENTS:
                await _handle_embedding(event)
            elif event_type in _LOG_ONLY_EVENTS:
                logger.info("[RailsCRUD] %s apply_id=%s (logged)", event_type, event.get("apply_id"))
            else:
                logger.debug("[RailsCRUD] Unknown event: %s", event_type)
        except Exception as exc:
            logger.error("[RailsCRUD] Message processing error: %s", exc)


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
            exchange = await channel.declare_exchange(EXCHANGE_NAME, aio_pika.ExchangeType.DIRECT, durable=True)
            queue = await channel.declare_queue(QUEUE_NAME, durable=True)
            for key in (*_EMBEDDING_EVENTS, *_LOG_ONLY_EVENTS):
                await queue.bind(exchange, routing_key=key)
            await queue.consume(_process_message)
            self._running = True
            logger.info("[RailsCRUD] Consumer started — bound to %s", EXCHANGE_NAME)
        except Exception as exc:
            logger.error("[RailsCRUD] Failed to start: %s", exc)

    async def stop(self) -> None:
        self._running = False
        if self._connection and not self._connection.is_closed:
            await self._connection.close()
        logger.info("[RailsCRUD] Consumer stopped")


rails_crud_consumer = RailsCRUDConsumer()
