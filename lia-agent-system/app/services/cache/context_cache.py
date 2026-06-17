"""
ContextCache — recruiter context cache with 5-min TTL.
Implements DIM-02: context caches + TTL + invalidation.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)

DEFAULT_TTL = 300    # 5 minutes
LONG_TTL    = 3600   # 1 hour (static data)


class ContextCache:
    """Redis-backed context cache with metadata TTL and pattern invalidation."""

    def __init__(self, redis_client: Any) -> None:
        self.redis = redis_client

    # ── read ──────────────────────────────────────────────────────────────

    async def get_with_ttl(
        self,
        key: str,
        ttl_seconds: int = DEFAULT_TTL,
    ) -> dict | None:
        """Return cached value, or None if missing/stale (caller refetches)."""
        raw = await self.redis.get(f"ctx:{key}")
        if not raw:
            return None

        meta = await self.redis.hgetall(f"ctx:meta:{key}")
        if not meta or "created_at" not in meta:
            await self.redis.delete(f"ctx:{key}", f"ctx:meta:{key}")
            return None

        age = datetime.utcnow().timestamp() - float(meta["created_at"])
        if age > ttl_seconds:
            await self.redis.delete(f"ctx:{key}", f"ctx:meta:{key}")
            return None

        try:
            return json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            await self.redis.delete(f"ctx:{key}", f"ctx:meta:{key}")
            return None

    # ── write ─────────────────────────────────────────────────────────────

    async def set_with_ttl(
        self,
        key: str,
        value: dict,
        ttl_seconds: int = DEFAULT_TTL,
    ) -> None:
        """Store value + metadata; both expire after ttl_seconds."""
        meta_key = f"ctx:meta:{key}"
        await self.redis.setex(f"ctx:{key}", ttl_seconds, json.dumps(value))
        await self.redis.hset(
            meta_key,
            mapping={
                "created_at": str(datetime.utcnow().timestamp()),
                "ttl": str(ttl_seconds),
                "version": "1",
            },
        )
        await self.redis.expire(meta_key, ttl_seconds)

    # ── invalidation ──────────────────────────────────────────────────────

    async def invalidate_for_recruiter(self, recruiter_id: str) -> int:
        """Delete all ctx:* keys for a recruiter (call on writes). Returns deleted count."""
        patterns = [
            f"ctx:recruiter:{recruiter_id}:*",
            f"ctx:meta:recruiter:{recruiter_id}:*",
        ]
        deleted = 0
        for pattern in patterns:
            cursor: int = 0
            while True:
                cursor, keys = await self.redis.scan(cursor, match=pattern, count=100)
                if keys:
                    await self.redis.delete(*keys)
                    deleted += len(keys)
                if cursor == 0:
                    break
        logger.debug(
            "[ContextCache] invalidated %d keys for recruiter=%s", deleted, recruiter_id
        )
        return deleted


# ── module-level singleton factory ────────────────────────────────────────

_instance: ContextCache | None = None


async def get_context_cache() -> ContextCache:
    """Return shared ContextCache backed by the canonical get_redis() singleton."""
    global _instance
    if _instance is None:
        from app.core.redis_client import get_redis
        _instance = ContextCache(await get_redis())
    return _instance
