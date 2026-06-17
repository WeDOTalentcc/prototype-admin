"""
Notification deduplication via Redis.

Prevents sending the same notification multiple times in the event of retries
or duplicate events. Uses a Redis key with a NX (set-if-not-exists) flag and
a configurable TTL.

Key format:
    notif_sent:{idempotency_key}

Idempotency key is derived from:
    sha256(f"{event_type}:{user_id}:{company_id}:{content_hash}")

where content_hash = sha256(title + message) — allows re-sending genuinely
different messages to the same user for the same event type after the TTL
expires.

Design decisions:
- FAIL-OPEN: if Redis is unavailable we allow the send (availability > dedup).
  A missed dedup is a duplicate notification; a false dedup is a lost one.
  Duplicates are recoverable; lost critical notifications are not.
- TTL default: 24 h (86 400 s) — resets after a natural day cycle.
- Mark on first send path only; skip path never writes.
"""
from __future__ import annotations

import hashlib
import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

# Redis key prefix — must not clash with token_budget:, voice_calls:, etc.
_KEY_PREFIX = "notif_sent"

# 24 hours by default; callers may override
DEFAULT_DEDUP_TTL_SECONDS: int = 86_400


def build_idempotency_key(
    event_type: str,
    user_id: str,
    company_id: str,
    title: str,
    message: str,
) -> str:
    """Derive a stable idempotency key from the notification's semantic identity.

    The key is a SHA-256 hex digest so it is safe to use as a Redis key
    (no spaces, controlled length, no tenant PII in plain text).

    Uses a two-layer hash:
    1. content_hash = sha256(title + message)  — captures what was said
    2. outer sha256(event_type + user_id + company_id + content_hash) — full identity

    A different event_type, user, company, or message text produces a different key,
    so they are never collapsed together.
    """
    content_hash = hashlib.sha256(
        f"{title}\x00{message}".encode("utf-8")
    ).hexdigest()[:16]  # 16 hex chars = 64 bits — ample collision resistance
    raw = f"{event_type}\x00{user_id}\x00{company_id}\x00{content_hash}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _redis_key(idempotency_key: str) -> str:
    return f"{_KEY_PREFIX}:{idempotency_key}"


async def _get_redis():
    """Return a fresh aioredis client. Returns None if Redis is unavailable.

    Mirrors the pattern in learning_snapshot_service._get_redis() and
    data_request_voice_service._check_voice_budget() — a per-call client
    so callers can close it without affecting a shared singleton.
    """
    try:
        import redis.asyncio as aioredis  # type: ignore[import]

        url = os.getenv("REDIS_URL", "redis://localhost:6379")
        return aioredis.from_url(
            url,
            decode_responses=True,
            socket_connect_timeout=0.5,
            socket_timeout=0.5,
        )
    except Exception as exc:  # pragma: no cover
        logger.warning("[NotifDedup] Redis unavailable, fail-open: %s", exc)
        return None


async def is_duplicate(
    idempotency_key: str,
    ttl_seconds: int = DEFAULT_DEDUP_TTL_SECONDS,
    *,
    _redis=None,  # injectable for testing — avoids real Redis in unit tests
) -> bool:
    """Return True when this notification was already sent within *ttl_seconds*.

    Uses SET NX EX (atomic set-if-not-exists with TTL).

    - First call   → key absent  → SET NX succeeds (returns True/b"OK") → NOT a dup
    - Repeat call  → key present → SET NX fails    (returns None)        → IS a dup
    - Redis down   → fail-open   → returns False (allow the send)

    Args:
        idempotency_key: Derived via :func:`build_idempotency_key`.
        ttl_seconds: How long to remember a sent notification. Default 24 h.
        _redis: Optional pre-built aioredis client (injected in tests so no
                real Redis connection is opened).
    """
    redis = _redis if _redis is not None else await _get_redis()
    if redis is None:
        logger.warning("[NotifDedup] Redis unavailable — fail-open, allowing send")
        return False

    key = _redis_key(idempotency_key)
    try:
        # SET NX EX: returns truthy on success (new key set), None if key existed
        result = await redis.set(key, "1", ex=ttl_seconds, nx=True)
        is_dup = result is None
        if is_dup:
            logger.info("[NotifDedup] Duplicate suppressed — key=%s ttl=%ds", key, ttl_seconds)
        return is_dup
    except Exception as exc:
        logger.warning("[NotifDedup] Redis error — fail-open: %s", exc)
        return False
    finally:
        # Close only if we opened this client (not caller-injected _redis)
        if _redis is None:
            try:
                await redis.aclose()
            except Exception:
                pass
