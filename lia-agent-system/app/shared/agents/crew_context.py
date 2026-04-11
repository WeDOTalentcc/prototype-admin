"""
CrewContext — Shared state for crew executions stored in Redis.

All agents within a crew execution can read/write to a shared context
keyed by crew_execution_id. Multi-tenant isolation is enforced via
company_id prefix in the Redis key.

Uses Redis hash (HSET/HGET) for atomic per-field writes so that
parallel tasks cannot overwrite each other's context entries.

TTL defaults to 1 hour to prevent stale data accumulation.
"""
from __future__ import annotations

import json
import logging
from typing import Any

logger = logging.getLogger(__name__)

CREW_CONTEXT_PREFIX = "lia:crew_ctx"
DEFAULT_TTL_SECONDS = 3600


def _serialize(value: Any) -> str:
    return json.dumps(value, default=str)


def _deserialize(raw: str | bytes) -> Any:
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8")
    return json.loads(raw)


class CrewContext:
    def __init__(
        self,
        crew_execution_id: str,
        company_id: str,
        ttl_seconds: int = DEFAULT_TTL_SECONDS,
    ):
        self.crew_execution_id = crew_execution_id
        self.company_id = company_id
        self.ttl_seconds = ttl_seconds
        self._local_cache: dict[str, Any] = {}

    @property
    def _redis_key(self) -> str:
        return f"{CREW_CONTEXT_PREFIX}:{self.company_id}:{self.crew_execution_id}"

    async def _get_redis(self):
        from app.core.redis_client import get_redis
        return await get_redis()

    async def set(self, key: str, value: Any) -> None:
        self._local_cache[key] = value
        try:
            redis = await self._get_redis()
            pipe = redis.pipeline(transaction=True)
            pipe.hset(self._redis_key, key, _serialize(value))
            pipe.expire(self._redis_key, self.ttl_seconds)
            await pipe.execute()
        except Exception as exc:
            logger.warning("[CrewContext] Redis hset failed (using local cache): %s", exc)

    async def get(self, key: str, default: Any = None) -> Any:
        if key in self._local_cache:
            return self._local_cache[key]
        try:
            redis = await self._get_redis()
            raw = await redis.hget(self._redis_key, key)
            if raw is not None:
                value = _deserialize(raw)
                self._local_cache[key] = value
                return value
        except Exception as exc:
            logger.warning("[CrewContext] Redis hget failed (using local cache): %s", exc)
        return self._local_cache.get(key, default)

    async def get_all(self) -> dict[str, Any]:
        try:
            redis = await self._get_redis()
            raw_all = await redis.hgetall(self._redis_key)
            if raw_all:
                ctx = {
                    (k.decode("utf-8") if isinstance(k, bytes) else k): _deserialize(v)
                    for k, v in raw_all.items()
                }
                self._local_cache.update(ctx)
                return dict(ctx)
        except Exception as exc:
            logger.warning("[CrewContext] Redis hgetall failed (using local cache): %s", exc)
        return dict(self._local_cache)

    async def merge(self, updates: dict[str, Any]) -> None:
        self._local_cache.update(updates)
        try:
            redis = await self._get_redis()
            mapping = {k: _serialize(v) for k, v in updates.items()}
            if mapping:
                pipe = redis.pipeline(transaction=True)
                pipe.hset(self._redis_key, mapping=mapping)
                pipe.expire(self._redis_key, self.ttl_seconds)
                await pipe.execute()
        except Exception as exc:
            logger.warning("[CrewContext] Redis hset/merge failed (using local cache): %s", exc)

    async def delete(self) -> None:
        self._local_cache.clear()
        try:
            redis = await self._get_redis()
            await redis.delete(self._redis_key)
        except Exception as exc:
            logger.warning("[CrewContext] Redis delete failed: %s", exc)
