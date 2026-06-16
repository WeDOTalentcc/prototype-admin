"""Canonical (2026-06-04): agentic loop transient-overload resilience.

Sensor for the harness defect found diagnosing the floating-chat failure:
a single Anthropic/Vertex `overloaded_error` (HTTP 529) used to `break` the
loop immediately, burning the iteration budget and degrading UX into a
misleading "reformule a pergunta". The loop must now retry with backoff and,
on persistent overload, flag `failure_reason="provider_overloaded"` so the
orchestrator returns an honest overload-specific message (REGRA-4 honesty).
"""
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.orchestrator.execution.agentic_loop import (
    AgenticLoop,
    _is_transient_provider_error,
)


# ── 1. Pure classifier (fast, deterministic) ────────────────────────────────
class TestTransientClassifier:
    def test_overloaded_error_dict_is_transient(self):
        exc = Exception(
            "{'type': 'error', 'error': {'details': None, 'type': "
            "'overloaded_error', 'message': 'Overloaded'}, 'request_id': 'req_vrtx_x'}"
        )
        assert _is_transient_provider_error(exc) is True

    def test_plain_overloaded_is_transient(self):
        assert _is_transient_provider_error(Exception("Overloaded")) is True

    def test_rate_limit_is_transient(self):
        assert _is_transient_provider_error(Exception("rate_limit_error")) is True

    def test_service_unavailable_is_transient(self):
        assert _is_transient_provider_error(Exception("503 Service Unavailable")) is True

    def test_value_error_is_not_transient(self):
        assert _is_transient_provider_error(ValueError("bad parameter foo")) is False

    def test_key_error_is_not_transient(self):
        assert _is_transient_provider_error(KeyError("missing field")) is False


# ── helpers ──────────────────────────────────────────────────────────────────
def _clean_c3b():
    return type(
        "R",
        (),
        {
            "hate_speech_blocked": False,
            "injection_blocked": False,
            "clean_message": "hi",
            "block_reason": None,
        },
    )()


def _mk_loop(generate_side_effect):
    loop = AgenticLoop()
    loop._llm_service = AsyncMock()
    loop._llm_service.generate_with_tools = AsyncMock(side_effect=generate_side_effect)
    loop._tool_executor = AsyncMock()
    # Normally set by _ensure_deps (which we no-op in tests).
    loop._ToolExecutionContext = MagicMock(return_value=object())
    return loop


def _patches(loop):
    return [
        patch.object(loop, "_ensure_deps"),
        patch.object(loop, "get_tool_schemas", return_value=[{"name": "x"}]),
        patch(
            "app.orchestrator.execution.agentic_loop._c3b_pre",
            new=AsyncMock(return_value=_clean_c3b()),
        ),
        patch(
            "app.orchestrator.execution.agentic_loop._c3b_post",
            new=AsyncMock(side_effect=lambda txt, ctx: txt),
        ),
        patch("asyncio.sleep", new=AsyncMock()),
    ]


async def _run(loop, **kw):
    ctxs = _patches(loop)
    for c in ctxs:
        c.start()
    try:
        return await loop.run(
            user_message="buscar candidatos",
            company_id="c1",
            user_id="u1",
            provider="claude",
            **kw,
        )
    finally:
        for c in ctxs:
            c.stop()


# ── 2. Persistent overload → retries then honest failure_reason ──────────────
@pytest.mark.asyncio
async def test_persistent_overload_returns_failure_reason():
    loop = _mk_loop(Exception("{'error': {'type': 'overloaded_error'}}"))
    result = await _run(loop)
    assert result["response"] is None
    assert result["failure_reason"] == "provider_overloaded"
    # retried: at least 2 attempts (1 + LIA_AGENTIC_OVERLOAD_RETRIES default 2 = 3)
    assert loop._llm_service.generate_with_tools.call_count >= 2


# ── 3. Transient-then-success recovers (no degraded fallback) ────────────────
@pytest.mark.asyncio
async def test_transient_then_success_recovers():
    text_resp = type(
        "TR", (), {"is_tool_call": False, "text_response": "ok done", "tool_calls": []}
    )()
    calls = {"n": 0}

    async def _se(*a, **k):
        calls["n"] += 1
        if calls["n"] == 1:
            raise Exception("overloaded_error")
        return text_resp

    loop = _mk_loop(_se)
    result = await _run(loop)
    assert result["response"] == "ok done"
    assert calls["n"] == 2  # 1 transient fail + 1 success


# ── 4. Non-transient error: no retry, not flagged as overload ────────────────
@pytest.mark.asyncio
async def test_non_transient_error_no_retry():
    loop = _mk_loop(ValueError("bad schema"))
    result = await _run(loop)
    assert result["response"] is None
    assert result.get("failure_reason") == "llm_error"
    assert loop._llm_service.generate_with_tools.call_count == 1
