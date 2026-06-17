"""
Redis Pub/Sub transport — substitui RabbitMQ para domain events em dev/prod Replit.

Canal único: "platform.events" (espelha o exchange RabbitMQ original).
Routing: dispatch_event() filtra por event_type internamente.

Fire-and-forget: se o subscriber cair por 1s o evento se perde — aceitável para
notificações Teams / agent dispatch. Para garantia de entrega, usar Celery
(já configurado com Redis broker).
"""
from __future__ import annotations

import asyncio
import json
import logging
import os

from collections.abc import Awaitable, Callable

logger = logging.getLogger(__name__)

PLATFORM_EVENTS_CHANNEL = "platform.events"

_subscriber_task: asyncio.Task | None = None


def _dev_redis_url() -> str:
    """Resolve Redis URL respeitando o dev guard (não consome Upstash em development)."""
    import re
    url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    app_env = os.getenv("APP_ENV", "")
    allow_remote = os.getenv("LIA_DEV_ALLOW_REMOTE_REDIS", "").lower() in ("1", "true")
    if app_env.lower() == "development" and not allow_remote:
        if re.search(r"@[^/]+\.[^/]+", url):
            return "redis://localhost:6379/0"
    return url


async def publish_event(channel: str, message: dict) -> bool:
    """Publica evento no canal Redis. Retorna True em sucesso, False em falha (graceful)."""
    try:
        import redis.asyncio as aioredis
        url = _dev_redis_url()
        conn = aioredis.from_url(url, decode_responses=True, socket_connect_timeout=1.0)
        try:
            await conn.publish(channel, json.dumps(message))
        finally:
            await conn.aclose()
        return True
    except Exception as exc:
        logger.error("[RedisPubSub] publish failed channel=%s: %s", channel, exc)
        return False


async def _subscriber_loop(
    channel: str,
    handler: Callable[[dict], Awaitable[None]],
) -> None:
    """Loop de subscriber — reconecta automaticamente em caso de falha."""
    import redis.asyncio as aioredis
    retry_delay = 2.0
    while True:
        try:
            url = _dev_redis_url()
            conn = aioredis.from_url(url, decode_responses=True)
            try:
                async with conn.pubsub() as pubsub:
                    await pubsub.subscribe(channel)
                    logger.info("[RedisPubSub] Subscribed → channel=%s", channel)
                    retry_delay = 2.0
                    async for msg in pubsub.listen():
                        if msg["type"] != "message":
                            continue
                        try:
                            payload = json.loads(msg["data"])
                            await handler(payload)
                        except asyncio.CancelledError:
                            raise
                        except Exception as exc:
                            logger.error("[RedisPubSub] handler error: %s", exc)
            finally:
                await conn.aclose()
        except asyncio.CancelledError:
            logger.info("[RedisPubSub] Subscriber cancelled: %s", channel)
            return
        except Exception as exc:
            logger.warning(
                "[RedisPubSub] Disconnected (retry %.0fs): %s", retry_delay, exc
            )
            await asyncio.sleep(retry_delay)
            retry_delay = min(retry_delay * 2, 30.0)


def start_subscriber(
    channel: str,
    handler: Callable[[dict], Awaitable[None]],
    *,
    name: str = "redis_pubsub_subscriber",
) -> "asyncio.Task":
    """Inicia subscriber como background task. Retorna a task."""
    task = asyncio.create_task(_subscriber_loop(channel, handler), name=name)
    logger.info("[RedisPubSub] Subscriber task iniciado: %s → %s", name, channel)
    return task


def stop_subscriber(task: "asyncio.Task | None") -> None:
    """Cancela graciosamente a subscriber task."""
    if task and not task.done():
        task.cancel()
        logger.info("[RedisPubSub] Subscriber task cancelado: %s", task.get_name())
