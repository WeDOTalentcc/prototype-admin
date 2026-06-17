# LIA-R02 — SessionBridge: persistência de contexto cross-session
# Permite que usuários retomem conversas mantendo contexto de sessões anteriores.
# LGPD Art. 15: dados de sessão devem ter TTL definido e podem ser deletados a pedido.

from __future__ import annotations

import json
import logging
import time
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger(__name__)

_SESSION_TTL_SECONDS = 86400 * 7  # 7 days default

# Injectable monotonic clock for testability (monkeypatch this in tests).
_now = time.monotonic


@dataclass
class SessionContext:
    session_id: str
    user_id: str
    domain: str
    # Task #1144: company_id is required for tenant-namespaced Redis keys.
    # Kept as last positional with default to preserve back-compat in tests
    # (``test_inmem_fallback_eviction.py`` instantiates without company_id —
    # those entries land under the legacy ``__unknown__`` namespace and are
    # surfaced as violations by the sentinel test).
    company_id: str = ""
    intent_history: list[str] = field(default_factory=list)  # last N intents
    entity_cache: dict[str, Any] = field(default_factory=dict)  # candidate_id, job_id etc
    last_active: datetime = field(default_factory=lambda: datetime.now(UTC))
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, Any] = field(default_factory=dict)
    
    def to_json(self) -> str:
        data = asdict(self)
        data["last_active"] = self.last_active.isoformat()
        data["created_at"] = self.created_at.isoformat()
        return json.dumps(data)
    
    @classmethod
    def from_json(cls, json_str: str) -> SessionContext:
        data = json.loads(json_str)
        data["last_active"] = datetime.fromisoformat(data["last_active"])
        data["created_at"] = datetime.fromisoformat(data["created_at"])
        return cls(**data)


class SessionBridge:
    """Cross-session context persistence with Redis backend and in-memory fallback.
    
    LIA-R02: Permite que recrutadores retomem contexto entre sessões.
    Ex: "o candidato que analisamos ontem" → bridge resolve para candidate_id
    armazenado na sessão anterior.
    
    LGPD compliance: TTL de 7 dias, suporte a deleção por user_id.
    """
    
    def __init__(self, ttl_seconds: int = _SESSION_TTL_SECONDS):
        self._ttl = ttl_seconds
        # Fallback in-memory: {key: (serialized_json, expiry_monotonic)}
        self._memory_store: dict[str, tuple[str, float]] = {}
        self._redis = None
        self._init_redis()
    
    def _init_redis(self) -> None:
        # NOTE: Redis connectivity is verified lazily on first async call.
        # We store the URL here; actual async client is created on first use.
        try:
            from lia_config.config import settings
            self._redis_url = settings.REDIS_URL or "redis://localhost:6379"
        except Exception:
            import os
            self._redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379")
        self._redis = None  # will be initialised lazily in _get_redis_client()

    async def _get_redis_client(self):
        """Return an async Redis client, creating one if needed."""
        if self._redis is not None:
            return self._redis
        try:
            import redis.asyncio as aioredis
            client = aioredis.from_url(self._redis_url, decode_responses=True)
            await client.ping()
            self._redis = client
            logger.info("[SessionBridge] Async Redis backend connected")
        except Exception as exc:
            logger.warning("[SessionBridge] Redis unavailable, using in-memory: %s", exc)
            self._redis = None
        return self._redis
    
    def _key(self, session_id: str, company_id: str | None = None) -> str:
        """Compose tenant-namespaced Redis key for a session.

        Task #1144: every key must be ``lia:session:<company_id>:<session_id>``.
        Empty ``company_id`` records a namespace violation and falls back to
        ``__unknown__`` (visible via Prometheus sentinel S9).
        """
        from app.shared.security.tenant_redis_namespace import (
            record_namespace_violation,
            tenant_namespaced_key,
        )
        if not company_id:
            # Fail-loud in prod (raises). In dev/test the violation is logged
            # and we return a clearly-marked unknown bucket so unit tests can
            # observe the violation. No broad except wrapping the helper.
            record_namespace_violation("session_bridge")
            return f"lia:session:__unknown__:{session_id}"
        return tenant_namespaced_key("lia:session", company_id, session_id)
    
    def _sweep_memory_store(self) -> None:
        """Evict expired entries from in-memory fallback (TTL-based)."""
        now = _now()
        expired = [k for k, (_, exp) in self._memory_store.items() if now > exp]
        for k in expired:
            del self._memory_store[k]

    async def save(self, ctx: SessionContext) -> None:
        """Persist session context."""
        ctx.last_active = datetime.now(UTC)
        serialized = ctx.to_json()
        try:
            redis_client = await self._get_redis_client()
            if redis_client:
                from app.shared.security.redis_crypto import get_redis_crypto
                await redis_client.setex(
                    self._key(ctx.session_id, ctx.company_id), self._ttl,
                    get_redis_crypto().encrypt(serialized),
                )
            else:
                # Sweep expired entries before adding new one
                self._sweep_memory_store()
                expiry = _now() + self._ttl
                self._memory_store[self._key(ctx.session_id, ctx.company_id)] = (serialized, expiry)
        except RuntimeError:
            # Task #1144 fail-loud — never swallow tenant-namespace violations.
            raise
        except Exception as exc:
            logger.error("[SessionBridge] Failed to save session %s: %s", ctx.session_id, exc)

    async def load(self, session_id: str, company_id: str = "") -> SessionContext | None:
        """Load session context by session_id (tenant-scoped, Task #1144)."""
        try:
            key = self._key(session_id, company_id)
            redis_client = await self._get_redis_client()
            if redis_client:
                raw = await redis_client.get(key)
                if raw:
                    from app.shared.security.redis_crypto import get_redis_crypto
                    return SessionContext.from_json(get_redis_crypto().decrypt(raw))
            else:
                entry = self._memory_store.get(key)
                if entry:
                    serialized, expiry = entry
                    if _now() > expiry:
                        # Expired — sweep and return None
                        del self._memory_store[key]
                        return None
                    return SessionContext.from_json(serialized)
        except RuntimeError:
            # Task #1144 fail-loud — never swallow tenant-namespace violations.
            raise
        except Exception as exc:
            logger.error("[SessionBridge] Failed to load session %s: %s", session_id, exc)
        return None
    
    async def delete(self, session_id: str, company_id: str = "") -> bool:
        """Delete session (LGPD Art. 15 — right to erasure)."""
        key = self._key(session_id, company_id)
        try:
            redis_client = await self._get_redis_client()
            if redis_client:
                return bool(await redis_client.delete(key))
            elif key in self._memory_store:
                del self._memory_store[key]
                return True
        except RuntimeError:
            # Task #1144 fail-loud — never swallow tenant-namespace violations.
            raise
        except Exception as exc:
            logger.error("[SessionBridge] Failed to delete session %s: %s", session_id, exc)
        return False
    
    async def delete_all_for_user(self, user_id: str) -> int:
        """Delete all sessions for a user (LGPD right to erasure)."""
        count = 0
        try:
            redis_client = await self._get_redis_client()
            if redis_client:
                # Task #1144: scan over the tenant-namespaced layout
                # (``lia:session:<company_id>:<session_id>``). The trailing
                # ``*`` matches any tenant — required for cross-tenant LGPD
                # right-to-erasure flows.
                pattern = "lia:session:*"
                async for key in redis_client.scan_iter(pattern):
                    raw = await redis_client.get(key)
                    if raw:
                        ctx = SessionContext.from_json(raw)
                        if ctx.user_id == user_id:
                            await redis_client.delete(key)
                            count += 1
            else:
                to_delete = []
                for key, raw in self._memory_store.items():
                    ctx = SessionContext.from_json(raw)
                    if ctx.user_id == user_id:
                        to_delete.append(key)
                for key in to_delete:
                    del self._memory_store[key]
                    count += 1
        except Exception as exc:
            logger.error("[SessionBridge] Failed to delete user sessions: %s", exc)
        logger.info("[SessionBridge] Deleted %d sessions for user %s", count, user_id)
        return count
    
    async def update_entity_cache(self, session_id: str, entity_type: str, entity_id: str, company_id: str = "") -> None:
        """Update entity cache in existing session (tenant-scoped, Task #1144)."""
        ctx = await self.load(session_id, company_id)
        if ctx:
            ctx.entity_cache[entity_type] = entity_id
            await self.save(ctx)
    
    async def append_intent(self, session_id: str, intent: str, max_history: int = 10, company_id: str = "") -> None:
        """Append intent to history (tenant-scoped, Task #1144)."""
        ctx = await self.load(session_id, company_id)
        if ctx:
            ctx.intent_history.append(intent)
            if len(ctx.intent_history) > max_history:
                ctx.intent_history = ctx.intent_history[-max_history:]
            await self.save(ctx)
