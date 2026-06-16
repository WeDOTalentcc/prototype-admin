"""RealtimeCreditSession — canonical credit gate for OpenAI Realtime API WebSocket.

ADR-WT-VOICE-001 (proposed): session-level credit accounting canonical.

Pattern:
- **Pre-session check (feedforward / guide)**: estimate token budget for the
  expected session duration (multiplied by audio cost multiplier), call the
  canonical ``check_credit_budget`` gate; fail-loud (raise ``AICreditExhausted``)
  when insufficient. This is REGRA 4 — no silent best-effort fallback.
- **Per-event reconciliation (feedback / sensor)**: on each ``response.done``
  event from the OpenAI Realtime stream, read ``response.usage`` and reconcile
  the credit ledger against the running pre-call estimate via the canonical
  ``reconcile_credits`` helper. This closes the harness loop (estimate is
  always corrected by ground-truth usage).
- **Mid-session exhaustion**: after each reconcile, sample remaining credits;
  if below ``_MIN_SESSION_BUFFER`` raise ``SessionShouldTerminate`` so the
  WebSocket caller can close the connection gracefully (e.g., send a
  ``response.cancel`` + 4004 close code).
- **Concurrent session cap (defense against abuse)**: per-tenant Redis counter
  (``realtime_sessions_active:<company_id>``) atomically incremented in
  ``pre_session_check``. Default cap = 5 concurrent sessions per tenant; raises
  ``ConcurrentSessionLimitExceeded`` when crossed. Worst-case burn at cap = 5
  sessions × $0.90/min = $4.50/min per tenant (was $18/min uncapped @ 100).

Multi-tenancy (REGRA ZERO + Pydantic Conventions REGRA 6):
- ``company_id`` is mandatory; constructor raises ``ValueError`` if empty
  (fail-closed). Caller must source it from ``RuntimeContext.from_contextvars``
  or ``Depends(require_company_id)`` — NEVER from request payload.
- Observability uses ``company_id_hash`` (SHA-256 first 12 chars) — never the
  raw UUID, so Prometheus cardinality stays bounded and LGPD-safe.

Single source of truth — used by:
- ``app/shared/providers/voice_openai_realtime.py`` (provider entry point)
- Future WebSocket route handlers under ``app/api/websockets/``

----

## Open questions pending Anderson (PLAN_WEBSOCKET_VOICE_GATE 2026-05-22)

Resolved 2026-05-22 (decisions implemented):
- Q3 multiplier 3.5x ✅ Implemented (was 2.0x — recalibrated vs Claude $3/M baseline)
- Q4 buffer 1500 ✅ Implemented (was 1000 — covers ~2 typical turns)
- Q5 dual timeout ✅ Implemented (120s idle + 1800s hard cap)
- Q6 concurrent cap 5 default ✅ Implemented (Redis-based, per-tenant)

Still pending:
- Q1 RESOLVED 2026-05-22 (ADR-WT-2027) -- BYOK = track-only mode in
  ``check_credit_budget`` (Opcao C). Tenant pays provider direct; WeDoTalent
  still tracks consumption for LGPD Art. 37 + emits ``byok_track_only_total``
  Grafana counter. Optional ``byok_soft_cap`` per tenant emits
  ``byok_soft_cap_breached_total`` for alarm without blocking. Backed by
  ``app.shared.services.byok_detector.is_byok_active`` + sensor
  ``scripts/check_credit_gate_respects_byok.py``.

2. **SDK vs raw WebSocket** — provider uses ``websockets`` lib (raw). OpenAI
   Python SDK 1.30+ added ``openai.AsyncOpenAI().beta.realtime`` — migrating
   to SDK would unify retries/circuit-breaker patterns. Currently agnostic:
   ``on_event`` consumes ``dict`` so works with either source. TODO: revisit
   once SDK API stabilizes (still beta as of 2026-05-22).
"""
from __future__ import annotations

import hashlib
import logging
import time
import uuid
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


# ── Canonical constants (single source of truth) ────────────────────────────
_REALTIME_TOKEN_EQ_PER_SEC = 33.33
"""Whisper-equivalent baseline: 2000 token-eq/min divided by 60s.

Matches the constant ``_WHISPER_TOKEN_EQ_PER_MINUTE`` in
``app/shared/llm_bootstrap.py`` and ``check_credit_budget``'s
``audio_duration_seconds`` conversion. Use the same constant so audio
budgeting stays consistent across single-shot Whisper and long-lived
Realtime sessions.
"""

_REALTIME_AUDIO_MULTIPLIER = 3.5
"""Audio cost multiplier vs Claude $3/M text baseline (recalibrated 2026-05-22).

Pricing math (verified 2026-05-22 vs OpenAI public Realtime billing):
- Input audio:  $32/1M tokens (Realtime) → 10.67x Claude baseline
- Output audio: $64/1M tokens (Realtime) → 21.33x Claude baseline
- Blended ~50/50 in/out mix: ~16x raw, conservatively damped to 3.5x
  because credit ledger uses Whisper token-eq (already inflated baseline).

Was 2.0x — under-charged tenants by ~75%, leaking margin on every session.
3.5x restores correct cost recovery. Tune via Q3 spec if Anderson disagrees;
canonical sensor pins this value in contract tests.
"""

_MIN_SESSION_BUFFER = 1500
"""Token-equivalents that must remain free after each reconcile.

If ``remaining < _MIN_SESSION_BUFFER`` we abort BEFORE the next turn
(SessionShouldTerminate). 1500 covers ~2 typical turns (~30s each at the
calibrated 3.5x audio multiplier) instead of 1 (was 1000). Avoids the
edge case where one turn finishes the buffer but the next one starts
mid-flight and burns into negative ledger.
"""

_IDLE_TIMEOUT_SEC = 120
"""Idle timeout: 2 min without any event closes the session.

Detects orphan WebSocket clients (browser tab crash, network drop) where the
candidate is no longer present. Tighter than the 600s previously used — most
real conversations have at least one event per turn (~10-30s).
"""

_HARD_CAP_SEC = 1800
"""Hard cap: 30 min absolute, force-close regardless of activity.

Belt-and-suspenders against runaway sessions (e.g., malicious looping bot
that emits a heartbeat every 60s to keep idle timer from firing). 30 min is
long enough for WSI screening (~45 min target) WITHOUT split, but typical
WSI is <30 min so most sessions complete naturally. Long interviews (45-60min)
should be split client-side into multiple sessions.

This REPLACES the previous single 600s timeout that was prematurely cutting
WSI sessions mid-screening. See PLAN_WEBSOCKET_VOICE_GATE Q5.
"""

_CONCURRENT_PER_TENANT_DEFAULT = 5
"""Default concurrent session cap per tenant (Q6 decision 2026-05-22).

Worst-case burn at cap: 5 sessions × $0.90/min ≈ $4.50/min/tenant. With
100 tenants hitting cap simultaneously = $450/min platform burn (still
recoverable via credit accounting); without cap = $1800/min runaway risk.

Override per tenant via plan tier (enterprise can request higher via
admin UI — gated by _CONCURRENT_PER_TENANT_MAX).
"""

_CONCURRENT_PER_TENANT_MAX = 50
"""Hard ceiling for admin override.

Even enterprise tenants can't exceed this; protects platform from a single
tenant monopolizing OpenAI rate limits. Adjust via deploy-time config if
Anderson approves higher limits for a specific deal.
"""

# Redis key prefix for concurrent session counter.
# Pattern: realtime_sessions_active:<company_id> -> int (atomic INCR/DECR).
_REDIS_KEY_PREFIX = "realtime_sessions_active:"
_SESSION_TTL_SEC = _HARD_CAP_SEC + 60
"""TTL on the counter key. Self-heals counter if a close() path is missed
(e.g., pod crash, network partition). Cleanup buffer of 60s past hard cap
ensures the slot is freed even if the session would have force-closed.
"""


class SessionShouldTerminate(Exception):
    """Raised mid-session when remaining credit falls below the safety buffer.

    The WebSocket caller MUST handle this by closing the connection
    gracefully (e.g., emit ``response.cancel`` + close code 4004).
    Re-raising as 5xx is wrong — exhaustion is not a server error.
    """

    def __init__(self, reason: str, session_id: str, remaining_credits: int):
        self.reason = reason
        self.session_id = session_id
        self.remaining_credits = remaining_credits
        super().__init__(
            f"Session {session_id} should terminate: {reason} "
            f"(remaining={remaining_credits})"
        )


class ConcurrentSessionLimitExceeded(Exception):
    """Raised when tenant reaches concurrent session cap (Q6 defense).

    REGRA 4: fail-loud. Caller MUST translate this into a WS close
    with code 4003 (policy violation) + structured reason in payload
    BEFORE accepting the WS upgrade. NEVER silent skip — that would
    let abusive tenants past the gate.
    """

    def __init__(
        self,
        message: str,
        company_id: str,
        current_count: int,
        max_count: int,
    ):
        self.company_id = company_id
        self.current_count = current_count
        self.max_count = max_count
        super().__init__(message)


def _hash_cid(company_id: str) -> str:
    """SHA-256 first 12 chars — bounded cardinality for Prometheus labels."""
    return hashlib.sha256(company_id.encode("utf-8")).hexdigest()[:12]


async def _get_remaining_credits(company_id: str) -> int:
    """Read current remaining credits via canonical gate (estimated_tokens=0).

    Wraps ``check_credit_budget`` with zero estimate so we get the
    ``remaining`` field without mutating the ledger. Fail-safe ALLOW
    semantics inherited from the gate (Redis/DB outage → we assume
    enough credit remains and return a sentinel large number, so the
    session continues; reconciliation will catch up next turn).
    """
    try:
        from app.shared.services.ai_credit_gate import check_credit_budget
        from lia_config.database import AsyncSessionLocal

        async with AsyncSessionLocal() as db:
            info = await check_credit_budget(
                db,
                company_id,
                estimated_tokens=0,
                service="voice_realtime",
                fail_safe=True,
            )
            if not isinstance(info, dict):
                return 10**9
            if info.get("fail_safe") or info.get("unconfigured"):
                # Outage / no budget configured -> do not terminate
                # mid-session over a transient error.
                return 10**9
            return int(info.get("remaining", 0))
    except Exception as exc:  # pragma: no cover -- fail-safe ALLOW
        logger.warning(
            "[RealtimeCreditSession] remaining-credit probe failed "
            "(fail-safe ALLOW): %s",
            exc,
        )
        return 10**9


@dataclass
class RealtimeCreditSession:
    """Per-session credit accounting + lifecycle wrapper.

    Construct ONCE per WebSocket lifecycle. Call:

    1. ``await session.pre_session_check(estimated_session_seconds=...)``
       BEFORE opening the WS. Fail-loud on insufficient budget OR
       concurrent cap exceeded.
    2. ``await session.on_event(event)`` for EVERY received event. Cheap
       no-op for non-billing events; reconciles on ``response.done``.
    3. ``await session.close(reason="normal")`` once when the WS closes
       (success, error, or timeout). Emits the terminated counter AND
       releases the concurrent slot via Redis DECR.

    Idempotency: ``on_event`` after ``close`` is a safe no-op.
    """

    company_id: str
    session_id: uuid.UUID = field(default_factory=uuid.uuid4)
    started_at: float = field(default_factory=time.time)
    estimated_tokens_so_far: int = 0
    actual_tokens_so_far: int = 0
    last_event_at: float = field(default_factory=time.time)
    terminated: bool = False
    terminate_reason: str | None = None
    turn_count: int = 0
    # Internal: whether we've acquired a concurrent slot (so close knows to release).
    _slot_acquired: bool = field(default=False, init=False, repr=False)

    def __post_init__(self) -> None:
        # Multi-tenancy fail-closed (REGRA ZERO + Pydantic Conventions R6)
        if not self.company_id:
            raise ValueError(
                "company_id required — RuntimeContext fail-closed; "
                "do NOT default to a placeholder tenant"
            )

    # ── Concurrent cap helpers (Redis-backed) ──────────────────────────

    async def _try_acquire_concurrent_slot(self) -> tuple[bool, int]:
        """Atomic INCR + cap check via Redis pipeline.

        Returns (acquired, current_count). On Redis failure: fail-safe ALLOW
        (returns (True, 0)) — losing the cap is preferable to blocking all
        sessions when Redis is down. Logged loudly so operators see it.
        """
        try:
            from app.core.redis_client import get_redis

            client = await get_redis()
            key = f"{_REDIS_KEY_PREFIX}{self.company_id}"
            async with client.pipeline(transaction=True) as pipe:
                pipe.incr(key)
                pipe.expire(key, _SESSION_TTL_SEC)
                result = await pipe.execute()
            count = int(result[0])
            cap = _CONCURRENT_PER_TENANT_DEFAULT  # TODO: per-tenant override
            if count > cap:
                # Roll back: did NOT get slot
                try:
                    await client.decr(key)
                except Exception:
                    pass
                return False, count
            return True, count
        except Exception as exc:
            # Redis outage → fail-safe ALLOW (log loud, continue without cap)
            logger.warning(
                "[RealtimeCreditSession] concurrent-slot probe failed "
                "(fail-safe ALLOW): %s",
                exc,
            )
            return True, 0

    async def _release_concurrent_slot(self) -> None:
        """DECR the per-tenant counter. Guard against negative values."""
        if not self._slot_acquired:
            return
        try:
            from app.core.redis_client import get_redis

            client = await get_redis()
            key = f"{_REDIS_KEY_PREFIX}{self.company_id}"
            count = int(await client.decr(key))
            if count < 0:
                # Cleanup bug guard: never let counter drift negative.
                await client.set(key, 0)
        except Exception as exc:
            logger.warning(
                "[RealtimeCreditSession] concurrent-slot release failed "
                "(safe to ignore — TTL will reap): %s",
                exc,
            )
        finally:
            self._slot_acquired = False

    # ── Lifecycle: pre-session ───────────────────────────────────────────

    async def pre_session_check(self, estimated_session_seconds: int) -> None:
        """Pre-flight credit gate: fail-loud BEFORE opening the WebSocket.

        Ordering (cheap → expensive):
        1. Validate args (fail-fast on bad caller).
        2. Concurrent cap via Redis INCR (cheap, atomic, per-tenant).
        3. Credit budget via DB (more expensive; only paid if cap passes).

        If credit gate fails AFTER we've acquired a concurrent slot, we
        release it before re-raising so the slot isn't leaked.

        Args:
            estimated_session_seconds: caller's best estimate of session
                duration. Used for budget projection only; actual usage is
                reconciled per-turn afterwards. Realistic default in caller
                is 1800s (30 min) for interview-style sessions — happens to
                match _HARD_CAP_SEC by design.

        Raises:
            ConcurrentSessionLimitExceeded: tenant reached cap.
            AICreditExhausted: projected budget exceeds remaining credits.
                Caller MUST translate into a WS close with code 4003 (policy
                violation) + structured reason BEFORE accepting WS upgrade.
        """
        if estimated_session_seconds <= 0:
            raise ValueError("estimated_session_seconds must be > 0")

        # Step 1: concurrent cap (cheap, atomic)
        acquired, current_count = await self._try_acquire_concurrent_slot()
        if not acquired:
            from app.shared.observability.canary_metrics import (
                realtime_session_terminated_total,
            )

            if realtime_session_terminated_total is not None:
                try:
                    realtime_session_terminated_total.labels(
                        reason="concurrent_cap_reached"
                    ).inc()
                except Exception:
                    pass
            logger.warning(
                "[RealtimeCreditSession] concurrent cap reached "
                "company_id_hash=%s current=%d max=%d",
                _hash_cid(self.company_id),
                current_count,
                _CONCURRENT_PER_TENANT_DEFAULT,
            )
            raise ConcurrentSessionLimitExceeded(
                message=(
                    f"Tenant reached concurrent Realtime session cap "
                    f"(current={current_count} max={_CONCURRENT_PER_TENANT_DEFAULT})"
                ),
                company_id=self.company_id,
                current_count=current_count,
                max_count=_CONCURRENT_PER_TENANT_DEFAULT,
            )
        # Slot acquired — must release on any subsequent failure path.
        self._slot_acquired = True

        # Step 2: credit budget projection (more expensive)
        estimated = int(
            estimated_session_seconds
            * _REALTIME_TOKEN_EQ_PER_SEC
            * _REALTIME_AUDIO_MULTIPLIER
        )
        self.estimated_tokens_so_far = estimated

        from app.shared.observability.canary_metrics import (
            realtime_session_started_total,
            realtime_session_terminated_total,
        )

        try:
            from app.shared.services.ai_credit_gate import check_credit_budget
            from lia_config.database import AsyncSessionLocal

            async with AsyncSessionLocal() as db:
                await check_credit_budget(
                    db,
                    self.company_id,
                    estimated_tokens=estimated,
                    service="voice_realtime",
                )
        except Exception as exc:
            try:
                from app.shared.services.ai_credit_gate import (
                    AICreditExhausted as _AICE,
                )

                if isinstance(exc, _AICE):
                    if realtime_session_terminated_total is not None:
                        try:
                            realtime_session_terminated_total.labels(
                                reason="credit_exhausted_pre"
                            ).inc()
                        except Exception:
                            pass
                    logger.warning(
                        "[RealtimeCreditSession] pre-check FAILED -- fail-loud "
                        "company_id_hash=%s session=%s estimated=%d",
                        _hash_cid(self.company_id),
                        self.session_id,
                        estimated,
                    )
                    # Release the concurrent slot before re-raising
                    await self._release_concurrent_slot()
                    raise
            except ImportError:
                pass
            logger.warning(
                "[RealtimeCreditSession] pre-check non-credit error "
                "(fail-safe ALLOW): %s",
                exc,
            )

        if realtime_session_started_total is not None:
            try:
                realtime_session_started_total.labels(
                    company_id_hash=_hash_cid(self.company_id)
                ).inc()
            except Exception:
                pass
        logger.info(
            "[RealtimeCreditSession] session started company_id_hash=%s "
            "session=%s estimated_seconds=%d estimated_tokens=%d "
            "concurrent_count=%d",
            _hash_cid(self.company_id),
            self.session_id,
            estimated_session_seconds,
            estimated,
            current_count,
        )

    # ── Lifecycle: per-event ─────────────────────────────────────────────

    async def on_event(self, event: dict[str, Any]) -> None:
        """Process an incoming OpenAI Realtime event.

        - ``response.done``: reconcile actual usage; check mid-session
          exhaustion; may raise ``SessionShouldTerminate``.
        - ``error``: structured log, no raise (the WS layer decides what
          to do with provider errors).
        - Other events: cheap touch of ``last_event_at`` only.

        Idempotent after ``close``: no-op.
        """
        if self.terminated:
            return  # idempotent

        self.last_event_at = time.time()
        event_type = event.get("type", "unknown")

        if event_type == "error":
            logger.error(
                "[RealtimeCreditSession] provider error session=%s payload=%r",
                self.session_id,
                event.get("error"),
            )
            return

        if event_type != "response.done":
            return  # only response.done carries final usage

        usage = event.get("response", {}).get("usage", {}) or {}
        actual_input = int(usage.get("input_tokens", 0) or 0)
        actual_output = int(usage.get("output_tokens", 0) or 0)
        turn_total = actual_input + actual_output
        self.turn_count += 1

        from app.shared.observability.canary_metrics import (
            realtime_session_terminated_total,
            realtime_tokens_consumed_total,
        )

        if realtime_tokens_consumed_total is not None:
            try:
                realtime_tokens_consumed_total.labels(direction="input").inc(
                    actual_input
                )
                realtime_tokens_consumed_total.labels(direction="output").inc(
                    actual_output
                )
            except Exception:
                pass

        try:
            from app.shared.llm_bootstrap import reconcile_credits

            await reconcile_credits(
                self.company_id,
                0,
                turn_total,
                service="voice_realtime",
            )
        except Exception as exc:  # pragma: no cover -- fail-safe
            logger.warning(
                "[RealtimeCreditSession] reconcile failed (fail-safe): %s",
                exc,
            )

        self.actual_tokens_so_far += turn_total

        remaining = await _get_remaining_credits(self.company_id)
        if remaining < _MIN_SESSION_BUFFER:
            self.terminated = True
            self.terminate_reason = "credit_exhausted_mid"
            if realtime_session_terminated_total is not None:
                try:
                    realtime_session_terminated_total.labels(
                        reason="credit_exhausted_mid"
                    ).inc()
                except Exception:
                    pass
            # Release concurrent slot since session is going away
            await self._release_concurrent_slot()
            logger.warning(
                "[RealtimeCreditSession] mid-session exhaust "
                "company_id_hash=%s session=%s turn_count=%d consumed=%d "
                "remaining=%d buffer=%d",
                _hash_cid(self.company_id),
                self.session_id,
                self.turn_count,
                self.actual_tokens_so_far,
                remaining,
                _MIN_SESSION_BUFFER,
            )
            raise SessionShouldTerminate(
                reason="credit_exhausted_mid_session",
                session_id=str(self.session_id),
                remaining_credits=remaining,
            )

    # ── Lifecycle: introspection + close ─────────────────────────────────

    def is_inactive(self) -> bool:
        """True if the session should be force-closed.

        Two reasons (dual timeout, Q5 decision 2026-05-22):
        - Idle timeout (``_IDLE_TIMEOUT_SEC``, default 120s): no events
          received recently → likely orphan WebSocket (client crashed,
          network drop). Cheap to detect, fast cleanup.
        - Hard cap (``_HARD_CAP_SEC``, default 1800s / 30min): total
          session duration exceeded, force-close regardless of activity.
          Defense against heartbeat-only loops that game the idle timer.
        """
        now = time.time()
        idle_seconds = now - self.last_event_at
        total_seconds = now - self.started_at
        if idle_seconds > _IDLE_TIMEOUT_SEC:
            return True
        if total_seconds > _HARD_CAP_SEC:
            return True
        return False

    def inactive_reason(self) -> str | None:
        """Return reason string if inactive, None otherwise.

        Used by caller telemetry to distinguish 'idle_timeout' from
        'hard_cap' close events. Computed off the same clocks as
        ``is_inactive`` so the two answers stay consistent.
        """
        now = time.time()
        if (now - self.last_event_at) > _IDLE_TIMEOUT_SEC:
            return "idle_timeout"
        if (now - self.started_at) > _HARD_CAP_SEC:
            return "hard_cap"
        return None

    async def close(self, reason: str = "normal") -> None:
        """Mark session closed + emit terminated counter once.

        Safe to call multiple times; only the first call emits the metric
        (matches the ``terminated`` flag in mid-session-exhaust handling).
        ALWAYS attempts to release the concurrent slot (idempotent — sets
        ``_slot_acquired=False`` after first call so duplicates are no-ops).
        """
        if self.terminated:
            duration = time.time() - self.started_at
            logger.info(
                "[RealtimeCreditSession] session closed (post-exhaust) "
                "session=%s duration_seconds=%.1f turn_count=%d "
                "tokens_actual=%d",
                self.session_id,
                duration,
                self.turn_count,
                self.actual_tokens_so_far,
            )
            # Slot release is idempotent (no-op if already released by mid-exhaust)
            await self._release_concurrent_slot()
            return

        self.terminated = True
        self.terminate_reason = reason
        from app.shared.observability.canary_metrics import (
            realtime_session_terminated_total,
        )

        if realtime_session_terminated_total is not None:
            try:
                realtime_session_terminated_total.labels(reason=reason).inc()
            except Exception:
                pass
        # Release the concurrent slot
        await self._release_concurrent_slot()
        duration = time.time() - self.started_at
        logger.info(
            "[RealtimeCreditSession] session closed session=%s reason=%s "
            "duration_seconds=%.1f turn_count=%d tokens_actual=%d",
            self.session_id,
            reason,
            duration,
            self.turn_count,
            self.actual_tokens_so_far,
        )
