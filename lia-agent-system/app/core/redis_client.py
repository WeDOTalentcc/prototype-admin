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


async def close_redis() -> None:
    """Close the shared Redis connection (call on app shutdown)."""
    global _redis_client
    if _redis_client is not None:
        try:
            await _redis_client.close()
        except Exception:
            pass
        _redis_client = None
