"""
Interview Session Store — Redis-backed session storage for WSIInterviewGraph.

Stores WSIInterviewState objects in Redis with a 2-hour TTL.
Falls back to an in-memory dict when Redis is unavailable (e.g., local dev).
"""
import logging
import pickle
from typing import Any, Optional

logger = logging.getLogger(__name__)

SESSION_TTL_SECONDS = 7200  # 2 hours
KEY_PREFIX = "wsi_session:"

try:
    import redis.asyncio as aioredis
    _AIOREDIS_AVAILABLE = True
except ImportError:
    aioredis = None  # type: ignore
    _AIOREDIS_AVAILABLE = False


class InterviewSessionStore:
    """
    Async session store backed by Redis with in-memory fallback.

    Usage:
        store = InterviewSessionStore()
        await store.set(session_id, state)
        state = await store.get(session_id)
        await store.delete(session_id)
    """

    def __init__(self) -> None:
        self._memory: dict[str, Any] = {}
        self._redis: Optional[Any] = None
        self._redis_available = False

    async def _get_redis(self) -> Optional[Any]:
        if not _AIOREDIS_AVAILABLE:
            return None
        if self._redis is not None:
            return self._redis
        try:
            from app.core.config import settings
            self._redis = aioredis.from_url(settings.REDIS_URL, decode_responses=False)
            # Probe with a ping
            await self._redis.ping()
            self._redis_available = True
            logger.info("[InterviewSessionStore] Connected to Redis")
        except Exception as exc:
            logger.warning(
                f"[InterviewSessionStore] Redis unavailable ({exc}), using in-memory fallback"
            )
            self._redis = None
            self._redis_available = False
        return self._redis

    async def set(self, session_id: str, state: Any) -> None:
        key = KEY_PREFIX + session_id
        redis = await self._get_redis()
        if redis and self._redis_available:
            try:
                payload = pickle.dumps(state)
                await redis.setex(key, SESSION_TTL_SECONDS, payload)
                return
            except Exception as exc:
                logger.warning(f"[InterviewSessionStore] Redis set failed ({exc}), falling back to memory")
        self._memory[session_id] = state

    async def get(self, session_id: str) -> Optional[Any]:
        key = KEY_PREFIX + session_id
        redis = await self._get_redis()
        if redis and self._redis_available:
            try:
                payload = await redis.get(key)
                if payload is not None:
                    return pickle.loads(payload)
                return None
            except Exception as exc:
                logger.warning(f"[InterviewSessionStore] Redis get failed ({exc}), falling back to memory")
        return self._memory.get(session_id)

    async def delete(self, session_id: str) -> None:
        key = KEY_PREFIX + session_id
        redis = await self._get_redis()
        if redis and self._redis_available:
            try:
                await redis.delete(key)
                return
            except Exception as exc:
                logger.warning(f"[InterviewSessionStore] Redis delete failed ({exc})")
        self._memory.pop(session_id, None)


# Singleton — shared across all endpoints in the same process
interview_session_store = InterviewSessionStore()
