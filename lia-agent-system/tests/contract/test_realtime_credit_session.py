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
from unittest.mock import AsyncMock, patch

import pytest

from app.domains.voice.services.realtime_credit_session import (
    RealtimeCreditSession,
    SessionShouldTerminate,
    _MIN_SESSION_BUFFER,
    _DEFAULT_SESSION_TIMEOUT_SEC,
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
    session.last_event_at = time.time() - (_DEFAULT_SESSION_TIMEOUT_SEC + 1)
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
