"""Contract tests -- Wave 4 Gap 2 (2026-05-22): streaming + tool-use reconciliation.

Pre-Wave 4 the credit gate ran ONLY pre-call with ``estimated = prompt + max_tokens``.
That estimate is wrong by construction for two cases:

* Streaming: the SDK yields chunks. Final usage is only known after the
  stream closes. If actual << estimated we over-charged the tenant; if
  actual >> estimated (rare, max_tokens caps it) we under-charged.
* Tool-use: each turn is a separate ``create()`` call. The pre-call
  estimate uses the new prompt + new max_tokens, so the gate is invoked
  per turn (correct), but the post-call delta still needs to be reconciled
  to match real billing.

These tests pin the reconciliation contract: after each successful
SDK call the gate must observe ``response.usage`` (non-streaming) or
the final chunk's ``.usage`` (streaming) and adjust the credit ledger.
"""
from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.middleware.auth_enforcement import _current_company_id
from app.shared.llm_bootstrap import (
    _extract_response_usage_tokens,
    _OpenAIStreamReconciler,
    reconcile_credits,
)


COMPANY_ID = "company-recon-test-uuid"


# ----------------------------------------------------------------------
# (1) Non-streaming: reconciliation observes response.usage and emits delta.
# ----------------------------------------------------------------------

@pytest.mark.asyncio
async def test_non_streaming_reconciles_estimate_vs_actual():
    """Given an estimated cost of 1000 and actual usage of 600 (200 in +
    400 out), reconcile_credits is called with a delta of -400."""
    # Patch only the metric -- the DB lookup is best-effort + swallowed
    # internally (fail-safe) so we don't need to mock the DB seam.
    with patch(
        "app.shared.observability.canary_metrics.llm_gate_reconciliation_delta_total"
    ) as mock_metric:
        mock_metric.labels.return_value = MagicMock()
        await reconcile_credits(
            COMPANY_ID, estimated=1000, actual=600, service="anthropic"
        )
        # delta = 600 - 1000 = -400 -> sign='negative', value=400
        mock_metric.labels.assert_called_with(provider="anthropic", sign="negative")
        mock_metric.labels.return_value.inc.assert_called_with(400)


# ----------------------------------------------------------------------
# (2) Streaming: _OpenAIStreamReconciler accumulates across chunks
#     and reconciles on iterator exhaustion.
# ----------------------------------------------------------------------

@pytest.mark.asyncio
async def test_streaming_reconciles_on_stream_close():
    """OpenAI streaming with ``stream_options={include_usage:True}`` produces a
    final chunk with .usage. The reconciler must observe that and call
    reconcile_credits exactly once when the async iterator is exhausted."""

    # Build a fake async stream that yields N chunks, the last with .usage.
    class _Chunk:
        def __init__(self, usage=None):
            self.usage = usage

    class _Usage:
        def __init__(self, prompt_tokens, completion_tokens):
            self.prompt_tokens = prompt_tokens
            self.completion_tokens = completion_tokens

    chunks = [
        _Chunk(),
        _Chunk(),
        _Chunk(),
        _Chunk(usage=_Usage(prompt_tokens=300, completion_tokens=200)),  # actual = 500
    ]

    class _FakeAsyncStream:
        def __init__(self, items):
            self._iter = iter(items)

        def __aiter__(self):
            return self

        async def __anext__(self):
            try:
                return next(self._iter)
            except StopIteration:
                raise StopAsyncIteration

    fake_stream = _FakeAsyncStream(chunks)
    reconciler = _OpenAIStreamReconciler(
        fake_stream,
        company_id=COMPANY_ID,
        estimated=1000,
        service="openai-async",
        is_async=True,
    )

    with patch(
        "app.shared.llm_bootstrap.reconcile_credits", new_callable=AsyncMock
    ) as mock_recon:
        async for _ in reconciler:
            pass

        # Exactly one reconcile call after the stream closed.
        mock_recon.assert_awaited_once_with(
            COMPANY_ID, 1000, 500, service="openai-async"
        )


# ----------------------------------------------------------------------
# (3) Tool-use multi-turn: each create() call gates independently.
#     Each turn's reconciliation is independent (no leakage between turns).
# ----------------------------------------------------------------------

@pytest.mark.asyncio
async def test_tool_use_each_turn_gates_individually():
    """Verify that tool-use's two SDK turns produce TWO reconciliation
    calls (turn 1: tool_use response, turn 2: final answer). Each reconciles
    with its own estimate/actual pair."""
    with patch(
        "app.shared.observability.canary_metrics.llm_gate_reconciliation_delta_total"
    ) as mock_metric:
        mock_metric.labels.return_value = MagicMock()

        # Simulate turn 1: estimated 1024 (prompt + default max), actual 350
        await reconcile_credits(
            COMPANY_ID, estimated=1024, actual=350, service="anthropic"
        )
        # Simulate turn 2: estimated 1500 (longer prompt with tool_result),
        # actual 800
        await reconcile_credits(
            COMPANY_ID, estimated=1500, actual=800, service="anthropic"
        )

        # Two label() calls -- one per turn.
        assert mock_metric.labels.call_count == 2
        # Both negative (under-utilized estimates).
        mock_metric.labels.assert_any_call(provider="anthropic", sign="negative")
        # Delta magnitudes: |350-1024|=674, |800-1500|=700
        inc_calls = [
            c.args[0] for c in mock_metric.labels.return_value.inc.call_args_list
        ]
        assert 674 in inc_calls
        assert 700 in inc_calls


# ----------------------------------------------------------------------
# (4) Zero delta: estimate == actual -> no ledger update, no metric.
# ----------------------------------------------------------------------

@pytest.mark.asyncio
async def test_reconcile_zero_delta_no_op():
    """When estimate exactly matches actual the reconciliation must be a
    no-op (no DB write, no metric increment)."""
    with patch(
        "app.shared.observability.canary_metrics.llm_gate_reconciliation_delta_total"
    ) as mock_metric:
        await reconcile_credits(
            COMPANY_ID, estimated=500, actual=500, service="anthropic"
        )
        mock_metric.labels.assert_not_called()


# ----------------------------------------------------------------------
# (5) Reconcile emits Prometheus metric with correct sign label.
# ----------------------------------------------------------------------

@pytest.mark.asyncio
async def test_reconcile_emits_prometheus_metric():
    """Reconciliation deltas of either sign must produce a counter
    increment with the matching sign label."""
    with patch(
        "app.shared.observability.canary_metrics.llm_gate_reconciliation_delta_total"
    ) as mock_metric:
        mock_metric.labels.return_value = MagicMock()

        # positive: actual > estimated
        await reconcile_credits(
            COMPANY_ID, estimated=500, actual=1200, service="openai"
        )
        mock_metric.labels.assert_called_with(provider="openai", sign="positive")
        mock_metric.labels.return_value.inc.assert_called_with(700)

        # negative: actual < estimated
        mock_metric.reset_mock()
        await reconcile_credits(
            COMPANY_ID, estimated=2000, actual=500, service="openai"
        )
        mock_metric.labels.assert_called_with(provider="openai", sign="negative")
        mock_metric.labels.return_value.inc.assert_called_with(1500)


# ----------------------------------------------------------------------
# Bonus sanity: response shape extraction handles all 3 providers.
# ----------------------------------------------------------------------

def test_extract_response_usage_anthropic_shape():
    """Anthropic Message.usage has input_tokens + output_tokens."""
    response = MagicMock()
    response.usage = MagicMock()
    response.usage.input_tokens = 100
    response.usage.output_tokens = 250
    # Remove the prompt/completion keys to disambiguate
    del response.usage.prompt_tokens
    del response.usage.completion_tokens
    del response.usage.prompt_token_count
    del response.usage.candidates_token_count
    del response.usage.total_tokens
    assert _extract_response_usage_tokens(response) == 350


def test_extract_response_usage_openai_shape():
    """OpenAI ChatCompletion.usage has prompt_tokens + completion_tokens."""
    response = MagicMock()
    response.usage = MagicMock()
    response.usage.prompt_tokens = 200
    response.usage.completion_tokens = 400
    response.usage.input_tokens = 0
    response.usage.output_tokens = 0
    response.usage.prompt_token_count = 0
    response.usage.candidates_token_count = 0
    response.usage.total_tokens = 0
    assert _extract_response_usage_tokens(response) == 600


def test_extract_response_usage_no_usage_returns_zero():
    """When the SDK does not expose .usage (older SDK versions, streaming
    without include_usage), extractor returns 0 (safe -- no reconcile)."""
    response = MagicMock(spec=[])  # no .usage attribute
    assert _extract_response_usage_tokens(response) == 0
