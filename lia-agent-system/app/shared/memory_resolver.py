# LIA-R04 — MemoryResolver com action_history
# Mantém contexto de sessão e histórico de ações para o orchestrator.
# Referência: Tezi AI e HireEZ usam memória de sessão para personalização.
# LGPD Art. 15: dados de memória de sessão devem ter TTL e podem ser deletados.

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

import json as _json
import os

# UC-P2-01: Redis persistence for action_history (TTL 24h, non-blocking)
try:
    import redis as _redis_module
    _REDIS = _redis_module.from_url(
        os.getenv("REDIS_URL", "redis://localhost:6379/0"),
        decode_responses=True,
    )
    _REDIS.ping()
except Exception:
    _REDIS = None

_ACTION_HISTORY_TTL = 86400  # 24 h (LGPD Art. 15 -- session data lifecycle)

logger = logging.getLogger(__name__)

_MAX_ACTION_HISTORY = 20
_MAX_INTENT_HISTORY = 10


@dataclass
class ActionRecord:
    """Single action record for history tracking."""
    domain: str
    action: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, Any] = field(default_factory=dict)
    success: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "domain": self.domain,
            "action": self.action,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
            "success": self.success,
        }


class MemoryResolver:
    """Manages in-session memory for the LIA orchestrator.

    Tracks:
    - action_history: last N actions with domain, action name, metadata
    - intent_history: last N detected intents
    - entity_cache: referenced entities (candidate_id, job_id, etc.)
    - user_preferences: persistent user-level preferences

    LIA-R04: Permite que o orchestrator mantenha contexto entre turnos
    da mesma sessão, possibilitando referências como 'o candidato anterior'
    ou 'a vaga que analisamos antes'.
    """

    def __init__(self, session_id: str, user_id: str = "", company_id: str = "") -> None:
        self.session_id = session_id
        self.user_id = user_id
        self.company_id = company_id  # Multi-tenancy: tenant isolation
        self._action_history: list[ActionRecord] = []
        self._intent_history: list[str] = []
        self._entity_cache: dict[str, Any] = {}
        self._user_preferences: dict[str, Any] = {}
        self._created_at = datetime.now(UTC)

    # ------------------------------------------------------------------
    # Action history (LIA-R04 core feature)
    # ------------------------------------------------------------------

    def add_action(
        self,
        domain: str,
        action: str,
        metadata: dict[str, Any] | None = None,
        success: bool = True,
    ) -> ActionRecord:
        """Record an action taken by the orchestrator or agent.

        Capped at _MAX_ACTION_HISTORY entries (FIFO eviction).
        """
        record = ActionRecord(
            domain=domain,
            action=action,
            metadata=metadata or {},
            success=success,
        )
        self._action_history.append(record)
        if len(self._action_history) > _MAX_ACTION_HISTORY:
            self._action_history = self._action_history[-_MAX_ACTION_HISTORY:]
        logger.debug(
            "[MemoryResolver][%s] action recorded: %s.%s",
            self.session_id, domain, action,
        )
        # UC-P2-01: persist to Redis (non-blocking, fail-open)
        # Task #1144: Redis key MUST embed company_id (tenant namespacing).
        if _REDIS:
            try:
                from app.shared.security.tenant_redis_namespace import (
                    record_namespace_violation,
                    tenant_namespaced_key,
                )
                if not self.company_id:
                    record_namespace_violation("memory_resolver.action_history")
                    return record
                key = tenant_namespaced_key(
                    "lia:action_history", self.company_id, self.session_id
                )
                _REDIS.rpush(key, _json.dumps(record.to_dict()))
                _REDIS.expire(key, _ACTION_HISTORY_TTL)
            except RuntimeError:
                # Task #1144 fail-loud — namespace violations must propagate
                # in production. Never coalesce into the generic "fail-open"
                # debug log below.
                raise
            except Exception as exc:  # noqa: BLE001
                logger.debug(
                    "[MemoryResolver][%s] Redis write failed (non-blocking): %s",
                    self.session_id, exc,
                )
        return record

    def get_action_history(self, session_id: str | None = None) -> list[dict]:
        """Return full action history, preferring Redis when available (UC-P2-01).

        Task #1144: read uses the tenant-namespaced key. Missing company_id
        falls back to the in-process buffer (still tenant-isolated by the
        ``_sessions[company_id]`` partition in :func:`get_or_create_resolver`).
        """
        sid = session_id or self.session_id
        if _REDIS and self.company_id:
            try:
                from app.shared.security.tenant_redis_namespace import (
                    tenant_namespaced_key,
                )
                key = tenant_namespaced_key(
                    "lia:action_history", self.company_id, sid
                )
                raw = _REDIS.lrange(key, 0, -1)
                if raw:
                    return [_json.loads(r) for r in raw]
            except Exception:  # noqa: BLE001
                pass
        return [a.to_dict() for a in self._action_history]

    def get_recent_actions(self, limit: int = 5) -> list[dict]:
        """Return the N most recent actions as dicts (Redis-backed when available)."""
        history = self.get_action_history()
        return history[-limit:]

    def get_actions_for_domain(self, domain: str, limit: int = 5) -> list[dict[str, Any]]:
        """Return recent actions filtered by domain."""
        filtered = [a for a in self._action_history if a.domain == domain]
        return [a.to_dict() for a in filtered[-limit:]]

    def get_last_action(self) -> dict[str, Any] | None:
        """Return the most recent action, or None if history is empty."""
        if self._action_history:
            return self._action_history[-1].to_dict()
        return None

    # ------------------------------------------------------------------
    # Intent history
    # ------------------------------------------------------------------

    def add_intent(self, intent: str) -> None:
        """Record a detected intent (capped at _MAX_INTENT_HISTORY)."""
        self._intent_history.append(intent)
        if len(self._intent_history) > _MAX_INTENT_HISTORY:
            self._intent_history = self._intent_history[-_MAX_INTENT_HISTORY:]

    def get_intent_history(self, limit: int = 5) -> list[str]:
        """Return the N most recent intents."""
        return self._intent_history[-limit:]

    def get_last_intent(self) -> str | None:
        return self._intent_history[-1] if self._intent_history else None

    # ------------------------------------------------------------------
    # Entity cache
    # ------------------------------------------------------------------

    def set_entity(self, entity_type: str, entity_id: str, metadata: dict | None = None) -> None:
        """Cache a referenced entity (e.g., candidate_id, job_id)."""
        self._entity_cache[entity_type] = {
            "id": entity_id,
            "metadata": metadata or {},
            "cached_at": datetime.now(UTC).isoformat(),
        }

    def get_entity(self, entity_type: str) -> dict[str, Any] | None:
        """Retrieve a cached entity by type."""
        return self._entity_cache.get(entity_type)

    def get_entity_id(self, entity_type: str) -> str | None:
        """Shorthand to get just the entity ID."""
        entry = self._entity_cache.get(entity_type)
        return entry["id"] if entry else None

    # ------------------------------------------------------------------
    # User preferences
    # ------------------------------------------------------------------

    def set_preference(self, key: str, value: Any) -> None:
        self._user_preferences[key] = value

    def get_preference(self, key: str, default: Any = None) -> Any:
        return self._user_preferences.get(key, default)

    # ------------------------------------------------------------------
    # Context snapshot (for logging / session bridge integration)
    # ------------------------------------------------------------------

    def get_context(self) -> dict[str, Any]:
        """Return full memory context snapshot for orchestrator use."""
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "company_id": self.company_id,
            "action_history": self.get_recent_actions(10),
            "intent_history": self.get_intent_history(5),
            "entity_cache": self._entity_cache,
            "user_preferences": self._user_preferences,
            "created_at": self._created_at.isoformat(),
            "action_count": len(self._action_history),
        }

    def clear(self) -> None:
        """Clear all in-session memory (LGPD Art. 15 — right to erasure)."""
        self._action_history.clear()
        self._intent_history.clear()
        self._entity_cache.clear()
        logger.info("[MemoryResolver][%s] Memory cleared (LGPD erasure)", self.session_id)


# Module-level session store (in-memory; for persistent storage use SessionBridge)
_sessions: dict[str, dict[str, MemoryResolver]] = {}  # {company_id: {session_id: resolver}}


def get_or_create_resolver(session_id: str, user_id: str = "", company_id: str = "") -> MemoryResolver:
    """Get or create a MemoryResolver for a session, partitioned by company_id."""
    if company_id not in _sessions:
        _sessions[company_id] = {}
    if session_id not in _sessions[company_id]:
        _sessions[company_id][session_id] = MemoryResolver(
            session_id=session_id, user_id=user_id, company_id=company_id
        )
    return _sessions[company_id][session_id]


def clear_session(session_id: str, company_id: str = "") -> bool:
    """Remove a session's memory, scoped by company_id."""
    if company_id and company_id in _sessions and session_id in _sessions[company_id]:
        _sessions[company_id][session_id].clear()
        del _sessions[company_id][session_id]
        return True
    if not company_id:
        for cid in list(_sessions.keys()):
            if session_id in _sessions[cid]:
                _sessions[cid][session_id].clear()
                del _sessions[cid][session_id]
                return True
    return False
