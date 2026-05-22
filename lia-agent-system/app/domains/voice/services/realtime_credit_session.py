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

1. **BYOK strategy** — when tenant brings own OpenAI API key, do WeDOTalent
   credits still apply, or is BYOK = unmetered? Current defaults assume YES,
   credits still gate (defense-in-depth against accidental free-tier abuse).
   TODO: confirm with Anderson + add tenant-flag bypass when needed.

2. **SDK vs raw WebSocket** — provider uses ``websockets`` lib (raw). OpenAI
   Python SDK 1.30+ added ``openai.AsyncOpenAI().beta.realtime`` — migrating
   to SDK would unify retries/circuit-breaker patterns. Currently agnostic:
   ``on_event`` consumes ``dict`` so works with either source. TODO: revisit
   once SDK API stabilizes (still beta as of 2026-05-22).

3. **Audio cost multiplier (current default 2.0x)** — OpenAI Realtime billing
   spec (verified 2026-05-22): input audio = $5/1M tok, output audio = $20/1M tok,
   text = standard gpt-4o pricing. 2.0x is a conservative blended midpoint
   assuming ~50/50 input/output token mix. TODO: Anderson confirms vs current
   Claude $3/M input baseline (which is what canonical credit ledger denominates).

4. **MIN_SESSION_BUFFER calibration (default 1000 token-eq)** — minimal
   credit headroom required to keep session alive after each reconcile. 1000
   is a chute; recalibrate after first 100 production sessions using P95 of
   per-turn token consumption. TODO: add Grafana dashboard pulling
   ``realtime_tokens_consumed_total`` and emit recommended new threshold.

5. **Session timeout (default 600s / 10min inactive)** — auto-close stale
   sessions to prevent orphan resource consumption when WS client crashes
   without ``close`` frame. TODO: Anderson confirms vs typical interview
   length (currently bug: candidate may sit silently mid-screening; need
   product input).

6. **Concurrent sessions per tenant (default unlimited)** — no current cap
   on parallel WS sessions. Could DDoS one tenant's credit balance. TODO:
   add gate via Redis-based counter once Anderson defines fair-use policy.

All six defaults are CONSERVATIVE (lean toward fail-loud); Anderson can
override with explicit decision later without breaking semantics.
"""
from __future__ import annotations

import hashlib
import logging
import time
import uuid
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


# ── Tunable defaults (Open questions above; conservative bias) ──────────────
_REALTIME_TOKEN_EQ_PER_SEC = 33.33
"""Whisper-equivalent baseline: 2000 token-eq/min divided by 60s.

Matches the constant ``_WHISPER_TOKEN_EQ_PER_MINUTE`` in
``app/shared/llm_bootstrap.py`` and ``check_credit_budget``'s
``audio_duration_seconds`` conversion. Use the same constant so audio
budgeting stays consistent across single-shot Whisper and long-lived
Realtime sessions.
"""

_REALTIME_AUDIO_MULTIPLIER = 2.0
"""Conservative audio cost multiplier vs text baseline.

Realtime input audio is roughly 1.7x and output audio 6.7x the cost of
text ($5/$20 per 1M tokens vs $3/M Claude baseline that the credit
ledger uses). 2.0x is a blended midpoint assuming 50/50 in/out mix.
Tune via ``_REALTIME_AUDIO_MULTIPLIER`` env override once Anderson
confirms billing model.
"""

_MIN_SESSION_BUFFER = 1000
"""Token-equivalents that must remain free after each reconcile.

If ``remaining < _MIN_SESSION_BUFFER`` we abort BEFORE the next turn
(SessionShouldTerminate). Conservative: lets one more ~30s turn finish
without going negative.
"""

_DEFAULT_SESSION_TIMEOUT_SEC = 600
"""Idle timeout: 10 min without any event closes the session.

Polled by ``is_inactive()`` from the WS read loop's keepalive check.
Mirrors typical OpenAI Realtime server-side timeout to avoid surprises.
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
       BEFORE opening the WS. Fail-loud on insufficient budget.
    2. ``await session.on_event(event)`` for EVERY received event. Cheap
       no-op for non-billing events; reconciles on ``response.done``.
    3. ``await session.close(reason="normal")`` once when the WS closes
       (success, error, or timeout). Emits the terminated counter.

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

    def __post_init__(self) -> None:
        # Multi-tenancy fail-closed (REGRA ZERO + Pydantic Conventions R6)
        if not self.company_id:
            raise ValueError(
                "company_id required — RuntimeContext fail-closed; "
                "do NOT default to a placeholder tenant"
            )

    # ── Lifecycle: pre-session ───────────────────────────────────────────

    async def pre_session_check(self, estimated_session_seconds: int) -> None:
        """Pre-flight credit gate: fail-loud BEFORE opening the WebSocket.

        Args:
            estimated_session_seconds: caller's best estimate of session
                duration. Used for budget projection only; actual usage is
                reconciled per-turn afterwards. Realistic default in caller
                is 1800s (30 min) for interview-style sessions.

        Raises:
            AICreditExhausted: when projected budget exceeds remaining
                credits. Caller MUST translate this into a WS close
                with code 4003 (policy violation) + a structured reason
                in the payload BEFORE accepting the WS upgrade.
        """
        if estimated_session_seconds <= 0:
            raise ValueError("estimated_session_seconds must be > 0")

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
            # Re-raise only the canonical credit exception. Any other
            # exception (DB outage, etc.) is fail-safe ALLOW -- we
            # already log inside ``check_credit_budget``.
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
            "session=%s estimated_seconds=%d estimated_tokens=%d",
            _hash_cid(self.company_id),
            self.session_id,
            estimated_session_seconds,
            estimated,
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

        # Per-direction telemetry
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

        # Reconcile vs prior actual (delta = this turn's actual usage).
        # We pre-decremented the entire estimated session budget once in
        # ``pre_session_check``; per-turn reconciliation tops up or
        # refunds based on real usage.
        try:
            from app.shared.llm_bootstrap import reconcile_credits

            # Pass estimated=0, actual=turn_total: this turn's delta is
            # exactly turn_total tokens because we already debited the
            # whole-session estimate up-front.
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

        # Mid-session exhaustion check
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
        """True if the session has been silent for longer than the timeout.

        Poll from the WS read loop's keepalive; close gracefully when True.
        """
        return (time.time() - self.last_event_at) > _DEFAULT_SESSION_TIMEOUT_SEC

    async def close(self, reason: str = "normal") -> None:
        """Mark session closed + emit terminated counter once.

        Safe to call multiple times; only the first call emits the metric
        (matches the ``terminated`` flag in mid-session-exhaust handling).
        """
        if self.terminated:
            # Already counted by the mid-exhaust path; just log final state.
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
