"""Cross-request idempotency cache for write endpoints.

`ContextManager` keeps a per-instance set of seen idempotency keys, which is
correct for a single conversational session but does *not* deduplicate retries
that come in across separate HTTP requests. The platform-side write endpoints
(candidate, vacancy, application) need cross-request dedup so that a client
that retries the same logical operation — possibly switching between a fork
UUID and a Rails bigint for the same candidate (ADR 003 / Task #472) — runs
only once.

This module provides a tiny TTL-bounded process-wide cache and a
`reject_duplicate_async` helper that:

1. Computes the canonical idempotency key via
   :meth:`ContextManager.generate_idempotency_key_async` so dual-ID params
   collapse onto the same hash when a `RailsAdapter` is supplied.
2. Atomically registers the key. If the key was already seen within the TTL
   window, raises HTTP 409 Conflict so the caller's retry is rejected
   instead of double-executing the side effect.

The cache is in-memory and per-process. That matches the existing
`ContextManager.idempotency_keys` semantics and is enough to neutralize the
common retry storm (browser refresh, network blip → axios retry, double
form submit). A multi-process deployment would still need an external store
(Redis) for full coverage, but that is outside the scope of this task.
"""
from __future__ import annotations

import asyncio
import time
from typing import Any

from fastapi import HTTPException

from app.shared.robustness.context_management import ContextManager


DEFAULT_TTL_SECONDS = 300
MAX_ENTRIES = 10_000

_lock = asyncio.Lock()
_seen: dict[str, float] = {}


def _evict_expired(now: float) -> None:
    """Drop expired entries; if still over MAX_ENTRIES, drop oldest first."""
    expired = [k for k, exp in _seen.items() if exp <= now]
    for k in expired:
        _seen.pop(k, None)
    if len(_seen) > MAX_ENTRIES:
        overflow = len(_seen) - MAX_ENTRIES
        for k, _exp in sorted(_seen.items(), key=lambda kv: kv[1])[:overflow]:
            _seen.pop(k, None)


async def reject_duplicate_async(
    operation: str,
    params: dict[str, Any],
    adapter: Any | None,
    *,
    scope: str = "global",
    ttl_seconds: int = DEFAULT_TTL_SECONDS,
) -> str:
    """Register the canonical idempotency key for ``(operation, params)`` in
    the process-wide cache, raising HTTP 409 if it was already seen.

    ``scope`` is fed into ``ContextManager.session_id`` so different tenants
    or users do not collide on identical params (e.g. two recruiters from
    different companies updating different candidates that happen to share
    a Rails bigint).

    Returns the registered key on success, so the caller can echo it in
    response headers / logs if desired.
    """
    ctx = ContextManager(session_id=scope, user_id=scope)
    key = await ctx.generate_idempotency_key_async(operation, params, adapter)
    now = time.monotonic()
    async with _lock:
        _evict_expired(now)
        existing = _seen.get(key)
        if existing is not None and existing > now:
            raise HTTPException(
                status_code=409,
                detail={
                    "error": "duplicate_request",
                    "message": (
                        "Esta operação já foi processada recentemente. "
                        "Aguarde o resultado da requisição original antes de reenviar."
                    ),
                    "idempotency_key": key,
                },
            )
        _seen[key] = now + ttl_seconds
    return key


def _reset_for_tests() -> None:
    """Clear the in-memory cache. Test-only helper."""
    _seen.clear()
