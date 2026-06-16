"""
Voice session state via Redis — canonical singleton-replacement (F-15 P0).

Audit: AUDIT_VOICE_SCREENING_ORCHESTRATOR_2026-05-22.md F-15.

Root cause: VoiceScreeningOrchestrator._sessions: dict in-process era
singleton race risk em FastAPI multi-worker:
  - W1 inicia call → session no dict do W1
  - Webhook subsequente vai pro W2 → session not found OU colisão
  - Mesmo single-worker asyncio: concurrent calls cruzam state em pontos await

Fix canonical: state persistido em Redis via SET EX (TTL 4h). API pública
do orchestrator preservada — só internal implementation muda.

Key pattern: `voice:session:{company_id}:{session_id}`
  - Multi-tenancy enforced via _require_company_id em todo método público
  - Active sessions index: `voice:sessions:active:{company_id}` (Redis SET) para
    list_active_sessions sem SCAN

Fallback in-memory: quando Redis indisponível (local dev / testes), cai em
dict in-memory com warning log. Esse fallback NÃO é multi-worker safe — é
apenas para desenvolvimento. Em produção, Redis is required.

TTL: 4 horas (call screening típica < 1h, buffer 4x para reconexões + análise
WSI pós-call). Após TTL, sessions consideradas expiradas e limpas pelo Redis.

ADR-001 compliance: este é o repository canonical para voice session state.
Orchestrator delega leitura/escrita aqui; não toca Redis diretamente.
"""

from __future__ import annotations

import json
import logging
from typing import Any

logger = logging.getLogger(__name__)


def _require_company_id(company_id: Any) -> None:
    """
    Multi-tenancy invariant guard (fail-closed).

    Canonical local helper for this repo. Raises ValueError if company_id is
    missing, empty, or not a string. Mirrors the contract enforced by FastAPI
    dependency `require_company_id` but for non-request contexts (internal
    service calls).
    """
    if not company_id or not isinstance(company_id, str):
        raise ValueError(
            f"company_id is required (multi-tenancy invariant); got {company_id!r}"
        )

SESSION_TTL_SECONDS = 4 * 60 * 60  # 4 hours

try:
    import redis.asyncio as aioredis  # noqa: F401  (probe import)
    _AIOREDIS_AVAILABLE = True
except ImportError:
    _AIOREDIS_AVAILABLE = False


class VoiceSessionRedisRepository:
    """
    Canonical voice session state store. Multi-worker safe via Redis.

    Stores serialized state (dict from `_session_to_state`) keyed by
    company_id + session_id. Multi-tenancy enforced at every public method.

    Public API:
        await save_session_state(company_id, session_id, state)
        await load_session_state(company_id, session_id) -> dict | None
        await delete_session_state(company_id, session_id) -> bool
        await list_active_session_ids(company_id, limit=100) -> list[str]
    """

    KEY_PREFIX = "voice:session"
    ACTIVE_INDEX_PREFIX = "voice:sessions:active"
    REVERSE_INDEX_PREFIX = "voice:session_index"  # session_id -> company_id

    def __init__(self) -> None:
        self._redis: Any | None = None
        self._redis_available: bool | None = None  # None=unknown, True/False=probed
        self._memory_fallback: dict[str, str] = {}  # in-memory fallback (dev only)
        self._memory_active_index: dict[str, set[str]] = {}  # company_id -> {session_id}
        self._memory_reverse_index: dict[str, str] = {}  # session_id -> company_id

    def _session_key(self, company_id: str, session_id: str) -> str:
        _require_company_id(company_id)
        return f"{self.KEY_PREFIX}:{company_id}:{session_id}"

    def _active_index_key(self, company_id: str) -> str:
        _require_company_id(company_id)
        return f"{self.ACTIVE_INDEX_PREFIX}:{company_id}"

    def _reverse_index_key(self, session_id: str) -> str:
        if not session_id:
            raise ValueError("session_id is required")
        return f"{self.REVERSE_INDEX_PREFIX}:{session_id}"

    async def _get_redis(self) -> Any | None:
        """Lazy-init shared Redis client. Returns None if unavailable."""
        if not _AIOREDIS_AVAILABLE:
            if self._redis_available is None:
                logger.warning(
                    "[VoiceSessionRedisRepository] redis.asyncio not installed; "
                    "using in-memory fallback (NOT multi-worker safe)"
                )
                self._redis_available = False
            return None

        if self._redis is not None:
            return self._redis

        try:
            from app.core.redis_client import get_redis
            self._redis = await get_redis()
            # Probe
            await self._redis.ping()
            self._redis_available = True
            logger.info("[VoiceSessionRedisRepository] Connected to Redis")
            return self._redis
        except Exception as exc:
            logger.warning(
                "[VoiceSessionRedisRepository] Redis unavailable (%s); "
                "falling back to in-memory store (NOT multi-worker safe)",
                exc,
            )
            self._redis = None
            self._redis_available = False
            return None

    async def save_session_state(
        self,
        *,
        company_id: str,
        session_id: str,
        state: dict[str, Any],
    ) -> None:
        """
        Persist session state with 4h TTL. Atomic via SET EX.

        Also adds session_id to the active-index SET for list_active_session_ids.
        """
        _require_company_id(company_id)
        if not session_id:
            raise ValueError("session_id is required")

        serialized = json.dumps(state, default=str)
        redis = await self._get_redis()

        if redis is not None:
            # Pipeline atomic: write state + register in active + reverse index
            pipe = redis.pipeline()
            pipe.set(
                self._session_key(company_id, session_id),
                serialized,
                ex=SESSION_TTL_SECONDS,
            )
            pipe.sadd(self._active_index_key(company_id), session_id)
            pipe.expire(self._active_index_key(company_id), SESSION_TTL_SECONDS)
            # Reverse index for session_id-only lookups (Twilio STT pipeline).
            pipe.set(
                self._reverse_index_key(session_id),
                company_id,
                ex=SESSION_TTL_SECONDS,
            )
            await pipe.execute()
            return

        # In-memory fallback
        self._memory_fallback[self._session_key(company_id, session_id)] = serialized
        self._memory_active_index.setdefault(company_id, set()).add(session_id)
        self._memory_reverse_index[session_id] = company_id

    async def load_session_state(
        self,
        *,
        company_id: str,
        session_id: str,
    ) -> dict[str, Any] | None:
        """Load session state. Returns None if not found / expired."""
        _require_company_id(company_id)
        if not session_id:
            return None

        redis = await self._get_redis()
        if redis is not None:
            raw = await redis.get(self._session_key(company_id, session_id))
            if raw is None:
                return None
            if isinstance(raw, bytes):
                raw = raw.decode("utf-8")
            return json.loads(raw)

        # In-memory fallback
        raw = self._memory_fallback.get(self._session_key(company_id, session_id))
        if raw is None:
            return None
        return json.loads(raw)

    async def delete_session_state(
        self,
        *,
        company_id: str,
        session_id: str,
    ) -> bool:
        """Delete session state + remove from active index."""
        _require_company_id(company_id)
        if not session_id:
            return False

        redis = await self._get_redis()
        if redis is not None:
            pipe = redis.pipeline()
            pipe.delete(self._session_key(company_id, session_id))
            pipe.srem(self._active_index_key(company_id), session_id)
            pipe.delete(self._reverse_index_key(session_id))
            results = await pipe.execute()
            return bool(results and results[0])

        # In-memory fallback
        key = self._session_key(company_id, session_id)
        existed = key in self._memory_fallback
        self._memory_fallback.pop(key, None)
        idx = self._memory_active_index.get(company_id)
        if idx is not None:
            idx.discard(session_id)
        self._memory_reverse_index.pop(session_id, None)
        return existed

    async def find_company_id_for_session(
        self,
        *,
        session_id: str,
    ) -> str | None:
        """
        Resolve company_id for a given session_id via reverse index.

        Used by callers (e.g., Twilio STT pipeline) that only have session_id
        in their request context. Multi-tenancy preserved: this returns the
        canonical company_id stored at session-creation time, never trusts
        external input.

        Returns None if session_id is unknown / expired.
        """
        if not session_id:
            return None
        redis = await self._get_redis()
        if redis is not None:
            value = await redis.get(self._reverse_index_key(session_id))
            if value is None:
                return None
            if isinstance(value, bytes):
                value = value.decode("utf-8")
            return value
        # In-memory fallback
        return self._memory_reverse_index.get(session_id)

    async def list_active_session_ids(
        self,
        *,
        company_id: str,
        limit: int = 100,
    ) -> list[str]:
        """
        List session IDs registered as active for a company.

        Uses Redis SET (active index) — no SCAN needed (O(1) amortized).
        """
        _require_company_id(company_id)
        redis = await self._get_redis()
        if redis is not None:
            members = await redis.smembers(self._active_index_key(company_id))
            session_ids = [
                m.decode("utf-8") if isinstance(m, bytes) else m
                for m in members
            ]
            return session_ids[:limit]

        # In-memory fallback
        idx = self._memory_active_index.get(company_id, set())
        return list(idx)[:limit]


_voice_session_repository: VoiceSessionRedisRepository | None = None


def get_voice_session_repository() -> VoiceSessionRedisRepository:
    """Canonical singleton accessor for VoiceSessionRedisRepository."""
    global _voice_session_repository
    if _voice_session_repository is None:
        _voice_session_repository = VoiceSessionRedisRepository()
    return _voice_session_repository
