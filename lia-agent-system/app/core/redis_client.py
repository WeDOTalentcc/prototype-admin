"""
Redis client — thin wrapper around redis.asyncio.

Supports authenticated Redis URLs (Cloud Run / production):
    redis://:password@host:port/db           — standard auth
    rediss://:password@host:port/db          — TLS + auth (Cloud Memorystore)
    redis://user:password@host:port/db       — user + password auth

All connection functions use `from_url()` which parses the URL natively and
supports auth tokens without any special handling required.

Usage:
    redis = await get_redis()
    await redis.get("key")
"""
from __future__ import annotations

import logging
import os
import re

logger = logging.getLogger(__name__)

# Matches Redis URLs with credentials: redis://:pass@, redis://user:pass@, rediss://:token@
# The `[^:@/]*` allows empty username (common: redis://:password@host)
_AUTH_PATTERN = re.compile(r"redis[s]?://[^:@/]*:[^@]+@")
# Replacement substitutes both username and password with *** for safe logging
_AUTH_MASK_SUB = re.compile(r"(redis[s]?://)[^:@/]*:[^@]+@")


def _log_redis_url_info(url: str, context: str = "") -> None:
    """Log Redis URL without exposing credentials.

    Handles all auth URL forms:
        redis://:password@host:port/db      — empty username (most common)
        redis://user:password@host:port/db  — explicit user
        rediss://:token@host:port/db        — TLS with auth
    """
    if _AUTH_PATTERN.match(url):
        safe_url = _AUTH_MASK_SUB.sub(r"\1***:***@", url)
        logger.info("[Redis] %sConnecting with auth to: %s", f"{context} " if context else "", safe_url)
    else:
        logger.debug("[Redis] %sConnecting (no auth) to: %s", f"{context} " if context else "", url)


_redis_client = None


async def get_redis():
    """Return a shared aioredis client (lazy init). Raises on failure.

    Supports authenticated Redis URLs:
        REDIS_URL=redis://:mypassword@redis.example.com:6379/0
        REDIS_URL=rediss://:token@managed.redis.host:6380/0  (TLS)
    """
    global _redis_client
    if _redis_client is None:
        import redis.asyncio as aioredis
        url = os.getenv("REDIS_URL", "redis://localhost:6379")
        _log_redis_url_info(url, "get_redis:")
        _redis_client = aioredis.from_url(
            url,
            encoding="utf-8",
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
            retry_on_timeout=True,
        )
    return _redis_client


async def get_redis_connection():
    """Retorna conexão Redis com decode_responses=True (fail-safe → None).

    Cada chamada retorna uma nova conexão própria para uso como async context manager.
    Usado por serviços que precisam de `async with redis:` por operação.

    Suporta URLs autenticadas:
        REDIS_URL=redis://:password@host:6379/0
        REDIS_URL=rediss://:token@managed.redis.host:6380/0  (TLS)

    Returns:
        Redis client ou None se Redis indisponível.
    """
    try:
        import redis.asyncio as aioredis

        from app.core.config import settings
        url = settings.REDIS_URL
        _log_redis_url_info(url, "get_redis_connection:")
        return aioredis.from_url(
            url,
            decode_responses=True,
            socket_connect_timeout=0.5,
            socket_timeout=0.5,
        )
    except Exception as e:
        logger.warning("[Redis] get_redis_connection failed: %s", e)
        return None


async def close_redis() -> None:
    """Close the shared Redis connection (call on app shutdown)."""
    global _redis_client
    if _redis_client is not None:
        try:
            await _redis_client.aclose()
        except Exception:
            pass
        _redis_client = None
