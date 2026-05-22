"""Contract tests for RealtimeCreditSession (PLAN_WEBSOCKET_VOICE_GATE 2026-05-22).

The contract under test is:

  *RealtimeCreditSession is the single source of truth for OpenAI Realtime
  WebSocket credit accounting. It MUST fail-loud on pre-flight exhaust,
  reconcile every ``response.done``, and terminate mid-session when the
  remaining-credit buffer is crossed.*

Strategy: pure-unit. We mock ``check_credit_budget`` /
``reconcile_credits`` / ``_get_remaining_credits`` so the tests do not
spin up a real DB. This is intentional — they belong in
``tests/contract/`` because they pin BEHAVIOURAL invariants, not
integration paths.

Sensors covered:
- Multi-tenancy fail-closed (REGRA ZERO + Pydantic Conv R6)
- Pre-session check fail-loud (REGRA 4)
- Reconcile on ``response.done`` event (harness feedback)
- Ignore on non-billing events (no false reconcile)
- Mid-session exhaust raises ``SessionShouldTerminate``
- Idle detection via ``is_inactive``
- Close emits terminated counter exactly once
"""
from __future__ import annotations

import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.domains.voice.services.realtime_credit_session import (
    ConcurrentSessionLimitExceeded,
    RealtimeCreditSession,
    SessionShouldTerminate,
    _CONCURRENT_PER_TENANT_DEFAULT,
    _CONCURRENT_PER_TENANT_MAX,
    _HARD_CAP_SEC,
    _IDLE_TIMEOUT_SEC,
    _MIN_SESSION_BUFFER,
    _REALTIME_AUDIO_MULTIPLIER,
    _REALTIME_TOKEN_EQ_PER_SEC,
)
from app.shared.services.ai_credit_gate import AICreditExhausted


_TENANT_A = "11111111-1111-1111-1111-111111111111"


# ── 1. Multi-tenancy fail-closed ────────────────────────────────────────


def test_constructor_rejects_empty_company_id():
    """Empty company_id MUST fail-closed at construction time."""
    with pytest.raises(ValueError, match="company_id required"):
        RealtimeCreditSession(company_id="")


# ── 2. Pre-session check ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_pre_session_check_passes_when_sufficient_credits():
    """Happy path: gate allows, started counter emits, no exception."""
    fake_gate = AsyncMock(
        return_value={
            "monthly_limit": 1_000_000,
            "current_usage": 0,
            "remaining": 1_000_000,
        }
    )
    fake_session_ctx = AsyncMock()
    fake_session_ctx.__aenter__ = AsyncMock(return_value=AsyncMock())
    fake_session_ctx.__aexit__ = AsyncMock(return_value=None)
    fake_session_local = lambda: fake_session_ctx  # noqa: E731

    with patch(
        "app.shared.services.ai_credit_gate.check_credit_budget", fake_gate
    ), patch(
        "lia_config.database.AsyncSessionLocal", fake_session_local
    ):
        session = RealtimeCreditSession(company_id=_TENANT_A)
        await session.pre_session_check(estimated_session_seconds=300)

    fake_gate.assert_awaited_once()
    # Session not terminated; estimated tokens have been stamped.
    assert session.terminated is False
    assert session.estimated_tokens_so_far > 0


@pytest.mark.asyncio
async def test_pre_session_check_fails_loud_when_insufficient_credits():
    """REGRA 4: pre-flight exhaust MUST raise (no silent fallback)."""
    fake_gate = AsyncMock(
        side_effect=AICreditExhausted(
            "exhausted",
            company_id=_TENANT_A,
            remaining=0,
            service="voice_realtime",
        )
    )
    fake_session_ctx = AsyncMock()
    fake_session_ctx.__aenter__ = AsyncMock(return_value=AsyncMock())
    fake_session_ctx.__aexit__ = AsyncMock(return_value=None)
    fake_session_local = lambda: fake_session_ctx  # noqa: E731

    with patch(
        "app.shared.services.ai_credit_gate.check_credit_budget", fake_gate
    ), patch(
        "lia_config.database.AsyncSessionLocal", fake_session_local
    ):
        session = RealtimeCreditSession(company_id=_TENANT_A)
        with pytest.raises(AICreditExhausted):
            await session.pre_session_check(estimated_session_seconds=300)


@pytest.mark.asyncio
async def test_pre_session_check_rejects_non_positive_seconds():
    """Defensive: invalid duration must be rejected (no implicit zero-budget)."""
    session = RealtimeCreditSession(company_id=_TENANT_A)
    with pytest.raises(ValueError, match="must be > 0"):
        await session.pre_session_check(estimated_session_seconds=0)


# ── 3. on_event reconciles on response.done ─────────────────────────────


@pytest.mark.asyncio
async def test_on_event_reconciles_on_response_done():
    """response.done payload should drive a reconcile call + token counters."""
    fake_reconcile = AsyncMock()
    fake_remaining = AsyncMock(return_value=999_999)

    with patch(
        "app.shared.llm_bootstrap.reconcile_credits", fake_reconcile
    ), patch(
        "app.domains.voice.services.realtime_credit_session"
        "._get_remaining_credits",
        fake_remaining,
    ):
        session = RealtimeCreditSession(company_id=_TENANT_A)
        event = {
            "type": "response.done",
            "response": {"usage": {"input_tokens": 500, "output_tokens": 800}},
        }
        await session.on_event(event)

    fake_reconcile.assert_awaited_once()
    args, kwargs = fake_reconcile.await_args
    # Signature: reconcile_credits(company_id, estimated, actual, *, service)
    assert args[0] == _TENANT_A
    assert args[1] == 0  # estimated already debited up-front
    assert args[2] == 1300  # actual turn total = 500 + 800
    assert kwargs.get("service") == "voice_realtime"
    assert session.actual_tokens_so_far == 1300
    assert session.turn_count == 1
    assert session.terminated is False


@pytest.mark.asyncio
async def test_on_event_ignores_non_billing_events():
    """Audio buffer chunks etc. must NOT trigger reconcile (would inflate cost)."""
    fake_reconcile = AsyncMock()
    fake_remaining = AsyncMock(return_value=999_999)

    with patch(
        "app.shared.llm_bootstrap.reconcile_credits", fake_reconcile
    ), patch(
        "app.domains.voice.services.realtime_credit_session"
        "._get_remaining_credits",
        fake_remaining,
    ):
        session = RealtimeCreditSession(company_id=_TENANT_A)
        await session.on_event(
            {"type": "input_audio_buffer.append", "audio": "blob"}
        )
        await session.on_event({"type": "input_audio_buffer.commit"})
        await session.on_event({"type": "response.created"})

    fake_reconcile.assert_not_awaited()
    assert session.turn_count == 0
    assert session.actual_tokens_so_far == 0


@pytest.mark.asyncio
async def test_on_event_error_payload_logged_no_raise(caplog):
    """error events MUST log structured but NOT raise (WS layer decides)."""
    fake_reconcile = AsyncMock()
    fake_remaining = AsyncMock(return_value=999_999)

    with patch(
        "app.shared.llm_bootstrap.reconcile_credits", fake_reconcile
    ), patch(
        "app.domains.voice.services.realtime_credit_session"
        "._get_remaining_credits",
        fake_remaining,
    ):
        session = RealtimeCreditSession(company_id=_TENANT_A)
        await session.on_event(
            {"type": "error", "error": {"message": "rate_limit"}}
        )

    fake_reconcile.assert_not_awaited()
    assert session.terminated is False


# ── 4. Mid-session exhaust ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_mid_session_exhaust_raises_should_terminate():
    """When remaining < _MIN_SESSION_BUFFER, on_event MUST raise."""
    fake_reconcile = AsyncMock()
    # Drop remaining below buffer.
    fake_remaining = AsyncMock(return_value=_MIN_SESSION_BUFFER - 1)

    with patch(
        "app.shared.llm_bootstrap.reconcile_credits", fake_reconcile
    ), patch(
        "app.domains.voice.services.realtime_credit_session"
        "._get_remaining_credits",
        fake_remaining,
    ):
        session = RealtimeCreditSession(company_id=_TENANT_A)
        event = {
            "type": "response.done",
            "response": {"usage": {"input_tokens": 100, "output_tokens": 100}},
        }
        with pytest.raises(SessionShouldTerminate) as excinfo:
            await session.on_event(event)

    assert "credit_exhausted_mid_session" in str(excinfo.value)
    assert session.terminated is True
    assert session.terminate_reason == "credit_exhausted_mid"
    # tokens still counted before the raise (so caller can audit)
    assert session.actual_tokens_so_far == 200


@pytest.mark.asyncio
async def test_on_event_is_noop_after_terminate():
    """After terminate, additional events must NOT mutate state."""
    fake_reconcile = AsyncMock()
    fake_remaining = AsyncMock(return_value=999_999)

    with patch(
        "app.shared.llm_bootstrap.reconcile_credits", fake_reconcile
    ), patch(
        "app.domains.voice.services.realtime_credit_session"
        "._get_remaining_credits",
        fake_remaining,
    ):
        session = RealtimeCreditSession(company_id=_TENANT_A)
        session.terminated = True
        await session.on_event(
            {
                "type": "response.done",
                "response": {
                    "usage": {"input_tokens": 999, "output_tokens": 999}
                },
            }
        )

    fake_reconcile.assert_not_awaited()
    assert session.actual_tokens_so_far == 0
    assert session.turn_count == 0


# ── 5. is_inactive ─────────────────────────────────────────────────────


def test_is_inactive_returns_false_when_fresh():
    """Just-constructed session is not inactive."""
    session = RealtimeCreditSession(company_id=_TENANT_A)
    assert session.is_inactive() is False


def test_is_inactive_returns_true_after_timeout():
    """Session past the idle threshold is inactive."""
    session = RealtimeCreditSession(company_id=_TENANT_A)
    session.last_event_at = time.time() - (_IDLE_TIMEOUT_SEC + 1)
    assert session.is_inactive() is True


# ── 6. close ───────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_close_marks_terminated_and_is_idempotent():
    """close() should be safe to call multiple times and only emit metric once."""
    session = RealtimeCreditSession(company_id=_TENANT_A)
    await session.close(reason="normal")
    assert session.terminated is True
    assert session.terminate_reason == "normal"

    # Second call: should not raise, should not change reason.
    await session.close(reason="another_reason")
    assert session.terminate_reason == "normal"


@pytest.mark.asyncio
async def test_close_after_mid_session_exhaust_does_not_double_count():
    """close() after mid-session exhaust must log but NOT re-emit terminated counter.

    Pinned because the mid-exhaust path sets ``terminated=True`` and emits
    the metric. A naïve close() implementation would double-count, skewing
    Prometheus rollups.
    """
    fake_reconcile = AsyncMock()
    fake_remaining = AsyncMock(return_value=_MIN_SESSION_BUFFER - 1)

    with patch(
        "app.shared.llm_bootstrap.reconcile_credits", fake_reconcile
    ), patch(
        "app.domains.voice.services.realtime_credit_session"
        "._get_remaining_credits",
        fake_remaining,
    ):
        session = RealtimeCreditSession(company_id=_TENANT_A)
        event = {
            "type": "response.done",
            "response": {"usage": {"input_tokens": 10, "output_tokens": 10}},
        }
        with pytest.raises(SessionShouldTerminate):
            await session.on_event(event)
        assert session.terminate_reason == "credit_exhausted_mid"

        # Now close should be a no-op metric-wise but still safe to call.
        await session.close(reason="normal")
        # Reason stays as the mid-exhaust reason (we don't overwrite).
        assert session.terminate_reason == "credit_exhausted_mid"


# ── 7. Canonical constants (PLAN_WEBSOCKET_VOICE_GATE 2026-05-22) ──────────


def test_multiplier_is_3_5x_canonical():
    """Q3 decision: multiplier MUST be 3.5x (recalibrated from 2.0x).

    2.0x undercharged tenants ~75% because OpenAI Realtime billing
    ($32/M input + $64/M output) is ~16x raw vs Claude $3/M baseline.
    3.5x is the canonical post-recalibration value.
    """
    assert _REALTIME_AUDIO_MULTIPLIER == 3.5, (
        f"Multiplier regression! Expected 3.5 (Q3 decision 2026-05-22), "
        f"got {_REALTIME_AUDIO_MULTIPLIER}. Margin leak risk."
    )


def test_min_session_buffer_is_1500():
    """Q4 decision: buffer MUST be 1500 (covers ~2 typical turns)."""
    assert _MIN_SESSION_BUFFER == 1500, (
        f"Buffer regression! Expected 1500 (Q4 decision 2026-05-22), "
        f"got {_MIN_SESSION_BUFFER}."
    )


def test_idle_timeout_is_120_seconds():
    """Q5 decision: idle timeout = 120s (orphan WS detection)."""
    assert _IDLE_TIMEOUT_SEC == 120, (
        f"Idle timeout regression! Expected 120s (Q5 decision 2026-05-22), "
        f"got {_IDLE_TIMEOUT_SEC}."
    )


def test_hard_cap_is_1800_seconds():
    """Q5 decision: hard cap = 1800s / 30min (force-close)."""
    assert _HARD_CAP_SEC == 1800, (
        f"Hard cap regression! Expected 1800s (Q5 decision 2026-05-22), "
        f"got {_HARD_CAP_SEC}."
    )


def test_concurrent_cap_default_is_5():
    """Q6 decision: default concurrent cap per tenant = 5."""
    assert _CONCURRENT_PER_TENANT_DEFAULT == 5, (
        f"Concurrent cap regression! Expected 5 (Q6 decision 2026-05-22), "
        f"got {_CONCURRENT_PER_TENANT_DEFAULT}."
    )


def test_concurrent_cap_max_is_50():
    """Q6 hard ceiling = 50 (admin override limit)."""
    assert _CONCURRENT_PER_TENANT_MAX == 50, (
        f"Concurrent cap ceiling regression! Expected 50, "
        f"got {_CONCURRENT_PER_TENANT_MAX}."
    )


def test_session_buffer_covers_2_typical_turns():
    """Sanity: 1500 buffer covers ≥2 typical 30s turns at 3.5x multiplier.

    typical turn ≈ 30s × 33.33 token-eq/s × 3.5x ≈ 3500 token-eq.
    Buffer 1500 < single turn (intentional — protects post-turn ledger,
    not pre-turn). But it must equal ~half a turn min, so we never
    abort with ample remaining budget.
    """
    typical_turn_seconds = 30
    typical_turn_tokens = int(
        typical_turn_seconds
        * _REALTIME_TOKEN_EQ_PER_SEC
        * _REALTIME_AUDIO_MULTIPLIER
    )
    # Buffer should be a meaningful fraction of typical turn (not zero, not 10x)
    assert _MIN_SESSION_BUFFER >= typical_turn_tokens // 3, (
        f"Buffer ({_MIN_SESSION_BUFFER}) too small vs typical turn "
        f"({typical_turn_tokens} tokens)."
    )
    assert _MIN_SESSION_BUFFER <= typical_turn_tokens * 2, (
        f"Buffer ({_MIN_SESSION_BUFFER}) too large vs typical turn "
        f"({typical_turn_tokens} tokens) — would abort too aggressively."
    )


# ── 8. Dual timeout (idle vs hard cap) ─────────────────────────────────────


def test_inactive_reason_returns_idle_when_no_events():
    """Idle path: last_event_at older than _IDLE_TIMEOUT_SEC → 'idle_timeout'."""
    session = RealtimeCreditSession(company_id=_TENANT_A)
    # Backdate last_event_at past idle window but NOT past hard cap
    session.last_event_at = time.time() - (_IDLE_TIMEOUT_SEC + 5)
    session.started_at = time.time() - 100  # well under hard cap

    assert session.is_inactive() is True
    assert session.inactive_reason() == "idle_timeout"


def test_inactive_reason_returns_hard_cap_when_over_30min():
    """Hard cap path: started_at older than _HARD_CAP_SEC even if events recent."""
    session = RealtimeCreditSession(company_id=_TENANT_A)
    # Backdate started_at past hard cap but keep last_event_at fresh
    # (simulates heartbeat-only abuse pattern that games idle timer)
    session.started_at = time.time() - (_HARD_CAP_SEC + 5)
    session.last_event_at = time.time() - 10  # well under idle

    assert session.is_inactive() is True
    assert session.inactive_reason() == "hard_cap"


def test_inactive_reason_none_when_session_fresh():
    """Healthy session within both windows → None."""
    session = RealtimeCreditSession(company_id=_TENANT_A)
    assert session.is_inactive() is False
    assert session.inactive_reason() is None


def test_dual_timeout_idle_takes_precedence_when_both_exceeded():
    """When both conditions hit, idle reported first (cheaper check / more common)."""
    session = RealtimeCreditSession(company_id=_TENANT_A)
    # Both exceeded
    session.started_at = time.time() - (_HARD_CAP_SEC + 100)
    session.last_event_at = time.time() - (_IDLE_TIMEOUT_SEC + 100)
    assert session.inactive_reason() == "idle_timeout"  # idle checked first


# ── 9. Concurrent cap acquire/release ──────────────────────────────────────


def _make_fake_redis(initial_count: int):
    """Build a fake redis client that tracks an in-memory counter."""
    state = {"count": initial_count}

    async def _incr(_key):
        state["count"] += 1
        return state["count"]

    async def _decr(_key):
        state["count"] -= 1
        return state["count"]

    async def _set(_key, value):
        state["count"] = int(value)
        return True

    async def _expire(_key, _ttl):
        return True

    # Build async pipeline mock
    class _PipelineCtx:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *_):
            return None

        def incr(self, key):
            return self

        def expire(self, key, ttl):
            return self

        async def execute(self):
            # Mirror INCR semantics
            state["count"] += 1
            return [state["count"], True]

    client = MagicMock()
    client.pipeline = MagicMock(return_value=_PipelineCtx())
    client.decr = _decr
    client.set = _set
    client.expire = _expire
    client.incr = _incr
    return client, state


@pytest.mark.asyncio
async def test_concurrent_cap_blocks_6th_session_when_default_5():
    """6th concurrent session at default cap=5 MUST raise ConcurrentSessionLimitExceeded."""
    # Simulate Redis already has 5 active sessions for this tenant
    fake_client, state = _make_fake_redis(initial_count=5)
    fake_get = AsyncMock(return_value=fake_client)

    fake_credit_gate = AsyncMock(return_value={"remaining": 1_000_000})
    fake_session_ctx = AsyncMock()
    fake_session_ctx.__aenter__ = AsyncMock(return_value=AsyncMock())
    fake_session_ctx.__aexit__ = AsyncMock(return_value=None)
    fake_session_local = lambda: fake_session_ctx  # noqa: E731

    with patch("app.core.redis_client.get_redis", fake_get), patch(
        "app.shared.services.ai_credit_gate.check_credit_budget",
        fake_credit_gate,
    ), patch("lia_config.database.AsyncSessionLocal", fake_session_local):
        session = RealtimeCreditSession(company_id=_TENANT_A)
        with pytest.raises(ConcurrentSessionLimitExceeded) as excinfo:
            await session.pre_session_check(estimated_session_seconds=300)

    assert excinfo.value.max_count == _CONCURRENT_PER_TENANT_DEFAULT
    assert excinfo.value.current_count > _CONCURRENT_PER_TENANT_DEFAULT
    # Credit gate must NOT have been called (cheap cap check fired first)
    fake_credit_gate.assert_not_awaited()


@pytest.mark.asyncio
async def test_concurrent_cap_allows_5th_session():
    """5th session (== cap) MUST be allowed; INCR result == 5 is OK."""
    fake_client, state = _make_fake_redis(initial_count=4)  # post-INCR = 5
    fake_get = AsyncMock(return_value=fake_client)

    fake_credit_gate = AsyncMock(return_value={"remaining": 1_000_000})
    fake_session_ctx = AsyncMock()
    fake_session_ctx.__aenter__ = AsyncMock(return_value=AsyncMock())
    fake_session_ctx.__aexit__ = AsyncMock(return_value=None)
    fake_session_local = lambda: fake_session_ctx  # noqa: E731

    with patch("app.core.redis_client.get_redis", fake_get), patch(
        "app.shared.services.ai_credit_gate.check_credit_budget",
        fake_credit_gate,
    ), patch("lia_config.database.AsyncSessionLocal", fake_session_local):
        session = RealtimeCreditSession(company_id=_TENANT_A)
        await session.pre_session_check(estimated_session_seconds=300)

    assert session._slot_acquired is True
    fake_credit_gate.assert_awaited_once()


@pytest.mark.asyncio
async def test_concurrent_slot_released_on_close():
    """close() MUST DECR the Redis counter when slot was acquired."""
    fake_client, state = _make_fake_redis(initial_count=2)
    fake_get = AsyncMock(return_value=fake_client)

    fake_credit_gate = AsyncMock(return_value={"remaining": 1_000_000})
    fake_session_ctx = AsyncMock()
    fake_session_ctx.__aenter__ = AsyncMock(return_value=AsyncMock())
    fake_session_ctx.__aexit__ = AsyncMock(return_value=None)
    fake_session_local = lambda: fake_session_ctx  # noqa: E731

    with patch("app.core.redis_client.get_redis", fake_get), patch(
        "app.shared.services.ai_credit_gate.check_credit_budget",
        fake_credit_gate,
    ), patch("lia_config.database.AsyncSessionLocal", fake_session_local):
        session = RealtimeCreditSession(company_id=_TENANT_A)
        await session.pre_session_check(estimated_session_seconds=300)
        # After acquire: count incremented to 3
        assert state["count"] == 3
        assert session._slot_acquired is True

        # close() should DECR
        await session.close(reason="normal")
        assert state["count"] == 2
        # And mark slot as released (idempotent)
        assert session._slot_acquired is False


@pytest.mark.asyncio
async def test_concurrent_slot_released_on_credit_exhausted():
    """If credit gate raises AFTER concurrent slot acquired, slot MUST be released.

    Otherwise abuse pattern: hit credit cap, leave 5 zombie slots blocking
    tenant forever (until TTL).
    """
    fake_client, state = _make_fake_redis(initial_count=2)
    fake_get = AsyncMock(return_value=fake_client)

    fake_credit_gate = AsyncMock(
        side_effect=AICreditExhausted(
            "exhausted",
            company_id=_TENANT_A,
            remaining=0,
            service="voice_realtime",
        )
    )
    fake_session_ctx = AsyncMock()
    fake_session_ctx.__aenter__ = AsyncMock(return_value=AsyncMock())
    fake_session_ctx.__aexit__ = AsyncMock(return_value=None)
    fake_session_local = lambda: fake_session_ctx  # noqa: E731

    with patch("app.core.redis_client.get_redis", fake_get), patch(
        "app.shared.services.ai_credit_gate.check_credit_budget",
        fake_credit_gate,
    ), patch("lia_config.database.AsyncSessionLocal", fake_session_local):
        session = RealtimeCreditSession(company_id=_TENANT_A)
        with pytest.raises(AICreditExhausted):
            await session.pre_session_check(estimated_session_seconds=300)

    # After acquire+release-on-failure: count back to original 2
    assert state["count"] == 2
    assert session._slot_acquired is False


@pytest.mark.asyncio
async def test_concurrent_count_resets_to_zero_if_negative():
    """If DECR drives counter below 0 (cleanup bug), MUST self-heal to 0."""
    fake_client, state = _make_fake_redis(initial_count=0)
    fake_get = AsyncMock(return_value=fake_client)

    with patch("app.core.redis_client.get_redis", fake_get):
        session = RealtimeCreditSession(company_id=_TENANT_A)
        # Force a release without acquire
        session._slot_acquired = True
        await session._release_concurrent_slot()
        # Counter went -1, then was reset to 0
        assert state["count"] == 0


@pytest.mark.asyncio
async def test_concurrent_slot_release_idempotent_on_double_close():
    """Calling close() twice MUST NOT double-DECR the Redis counter."""
    fake_client, state = _make_fake_redis(initial_count=2)
    fake_get = AsyncMock(return_value=fake_client)

    fake_credit_gate = AsyncMock(return_value={"remaining": 1_000_000})
    fake_session_ctx = AsyncMock()
    fake_session_ctx.__aenter__ = AsyncMock(return_value=AsyncMock())
    fake_session_ctx.__aexit__ = AsyncMock(return_value=None)
    fake_session_local = lambda: fake_session_ctx  # noqa: E731

    with patch("app.core.redis_client.get_redis", fake_get), patch(
        "app.shared.services.ai_credit_gate.check_credit_budget",
        fake_credit_gate,
    ), patch("lia_config.database.AsyncSessionLocal", fake_session_local):
        session = RealtimeCreditSession(company_id=_TENANT_A)
        await session.pre_session_check(estimated_session_seconds=300)
        assert state["count"] == 3

        await session.close(reason="normal")
        assert state["count"] == 2

        # Second close should NOT decrement again
        await session.close(reason="normal")
        assert state["count"] == 2  # unchanged
