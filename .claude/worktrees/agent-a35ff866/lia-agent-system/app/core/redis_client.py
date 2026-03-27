"""
Redis client — thin wrapper around aioredis.

Usage:
    redis = await get_redis()
    await redis.get("key")
"""
from __future__ import annotations

import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

_redis_client = None


async def get_redis():
    """Return a shared aioredis client (lazy init). Raises on failure."""
    global _redis_client
    if _redis_client is None:
        import aioredis  # type: ignore[import]
        url = os.getenv("REDIS_URL", "redis://localhost:6379")
        _redis_client = await aioredis.from_url(
            url, encoding="utf-8", decode_responses=True
        )
    return _redis_client


async def get_redis_connection():
    """Retorna conexão Redis com decode_responses=True (fail-safe → None).

    Cada chamada retorna uma nova conexão própria para uso como async context manager.
    Usado por serviços que precisam de `async with redis:` por operação.

    Returns:
        Redis client ou None se Redis indisponível.
    """
    try:
        import redis.asyncio as aioredis
        from app.core.config import settings
        return await aioredis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            socket_connect_timeout=0.5,
            socket_timeout=0.5,
        )
    except Exception:
        try:
            import aioredis as _aioredis  # type: ignore[import]
            from app.core.config import settings
            return await _aioredis.from_url(settings.REDIS_URL, decode_responses=True)
        except Exception:
            return None


async def close_redis() -> None:
    """Close the shared Redis connection (call on app shutdown)."""
    global _redis_client
    if _redis_client is not None:
        try:
            await _redis_client.close()
        except Exception:
            pass
        _redis_client = None
