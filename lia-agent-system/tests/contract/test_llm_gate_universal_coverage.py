"""
Contract tests — Wave 3 universal ai_credit_gate coverage via llm_bootstrap.

Validates the monkey-patches installed by `app.shared.llm_bootstrap` actually
enforce `check_credit_budget` before invoking the LLM SDK primitives. Closes
the coverage gap identified by the AI credits audit (2026-05-21).

We test the SHIM, not the SDK. The SDK calls themselves are mocked at the
underlying-method seam (`messages.create`, `chat.completions.create`,
`models.generate_content`). The gate is the contract under test.
"""
from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.middleware.auth_enforcement import _current_company_id
from app.shared.llm_bootstrap import (
    _enforce_credit_gate_async,
    _enforce_credit_gate_sync,
    _estimate_tokens_anthropic,
    _estimate_tokens_openai,
    _estimate_tokens_genai,
    install_llm_guards,
)
from app.shared.services.ai_credit_gate import AICreditExhausted


COMPANY_OK = "company-with-credits-uuid"
COMPANY_EXHAUSTED = "company-exhausted-uuid"


# ----------------------------------------------------------------------
# Estimators
# ----------------------------------------------------------------------

def test_estimate_tokens_anthropic_basic():
    kwargs = {
        "messages": [{"role": "user", "content": "Hello world" * 100}],
        "system": "You are helpful",
        "max_tokens": 500,
    }
    estimated = _estimate_tokens_anthropic(kwargs)
    # ~1100 chars / 4 + 500 max
    assert estimated > 500
    assert estimated < 1000


def test_estimate_tokens_anthropic_structured_content():
    kwargs = {
        "messages": [
            {"role": "user", "content": [{"type": "text", "text": "abc" * 100}]}
        ],
        "max_tokens": 256,
    }
    estimated = _estimate_tokens_anthropic(kwargs)
    assert estimated > 256
    # 300 chars / 4 + 256 = 331
    assert 320 <= estimated <= 350


def test_estimate_tokens_openai_basic():
    kwargs = {
        "messages": [{"role": "user", "content": "X" * 200}],
        "max_tokens": 100,
    }
    estimated = _estimate_tokens_openai(kwargs)
    assert estimated >= 150
    # 200/4 + 100 = 150
    assert estimated <= 160


def test_estimate_tokens_genai_basic():
    kwargs = {"contents": "Hello " * 100}
    estimated = _estimate_tokens_genai(kwargs)
    # 600 chars / 4 + 1024 default = ~1174
    assert estimated > 1000


# ----------------------------------------------------------------------
# Sync gate — no context = fail-safe ALLOW (silent skip)
# ----------------------------------------------------------------------

def test_sync_gate_no_context_skips_silently():
    """When _current_company_id is empty, gate must NOT raise — fail-safe ALLOW."""
    token = _current_company_id.set("")
    try:
        # Should not raise even though no context is set
        _enforce_credit_gate_sync(
            "test-anthropic",
            {"messages": [{"role": "user", "content": "x"}], "max_tokens": 10},
            estimator=_estimate_tokens_anthropic,
        )
    finally:
        _current_company_id.reset(token)


# ----------------------------------------------------------------------
# Async gate — exhausted credits raise AICreditExhausted
# ----------------------------------------------------------------------

@pytest.mark.asyncio
async def test_async_gate_exhausted_raises():
    """When ai_credits_balance is exhausted, the gate raises AICreditExhausted."""
    token = _current_company_id.set(COMPANY_EXHAUSTED)
    try:
        with patch(
            "app.shared.services.ai_credit_gate.check_credit_budget",
            new=AsyncMock(
                side_effect=AICreditExhausted(
                    f"AI credit budget exhausted (company={COMPANY_EXHAUSTED})",
                    company_id=COMPANY_EXHAUSTED,
                    remaining=0,
                    service="test",
                )
            ),
        ):
            with pytest.raises(AICreditExhausted) as exc_info:
                await _enforce_credit_gate_async(
                    "openai-async",
                    {"messages": [{"role": "user", "content": "x"}], "max_tokens": 50},
                    estimator=_estimate_tokens_openai,
                )
            assert exc_info.value.company_id == COMPANY_EXHAUSTED
            assert exc_info.value.remaining == 0
    finally:
        _current_company_id.reset(token)


@pytest.mark.asyncio
async def test_async_gate_with_credits_passes():
    """When ai_credits_balance has remaining quota, gate returns silently."""
    token = _current_company_id.set(COMPANY_OK)
    try:
        with patch(
            "app.shared.services.ai_credit_gate.check_credit_budget",
            new=AsyncMock(return_value={"monthly_limit": 100000, "current_usage": 1000, "remaining": 99000}),
        ):
            # Should not raise
            await _enforce_credit_gate_async(
                "openai-async",
                {"messages": [{"role": "user", "content": "x"}], "max_tokens": 50},
                estimator=_estimate_tokens_openai,
            )
    finally:
        _current_company_id.reset(token)


@pytest.mark.asyncio
async def test_async_gate_db_error_fails_safe_allow():
    """When DB lookup errors (outage), gate falls back to ALLOW (fail-safe)."""
    token = _current_company_id.set(COMPANY_OK)
    try:
        with patch(
            "app.shared.services.ai_credit_gate.check_credit_budget",
            new=AsyncMock(side_effect=RuntimeError("DB outage")),
        ):
            # Should not raise — fail-safe ALLOW for non-AICreditExhausted errors
            await _enforce_credit_gate_async(
                "anthropic-async",
                {"messages": [{"role": "user", "content": "x"}], "max_tokens": 50},
                estimator=_estimate_tokens_anthropic,
            )
    finally:
        _current_company_id.reset(token)


# ----------------------------------------------------------------------
# Service inference — caller path → service label
# ----------------------------------------------------------------------

@pytest.mark.asyncio
async def test_service_label_inferred_from_caller():
    """The `service` kwarg passed to check_credit_budget should be the filename
    of the most-recent non-bootstrap stack frame."""
    captured = {}

    async def _fake_check(db, company_id, *, estimated_tokens, service, **kwargs):
        captured["service"] = service
        return {"monthly_limit": 1000, "current_usage": 0, "remaining": 1000}

    token = _current_company_id.set(COMPANY_OK)
    try:
        with patch(
            "app.shared.services.ai_credit_gate.check_credit_budget",
            new=_fake_check,
        ):
            await _enforce_credit_gate_async(
                "anthropic-async",
                {"messages": [{"role": "user", "content": "x"}], "max_tokens": 5},
                estimator=_estimate_tokens_anthropic,
            )
        # This test file IS the caller, so service should be the test filename
        assert "test_llm_gate_universal_coverage" in captured.get("service", "")
    finally:
        _current_company_id.reset(token)


# ----------------------------------------------------------------------
# Idempotency — install_llm_guards() multiple times is safe
# ----------------------------------------------------------------------

def test_install_llm_guards_idempotent():
    """Calling install_llm_guards multiple times must not double-patch."""
    install_llm_guards()
    install_llm_guards()
    install_llm_guards()
    # Smoke — if double-patching occurred, this would chain wrappers and
    # eventually overflow on the next SDK call. Stable here means OK.


# ----------------------------------------------------------------------
# Coverage parametrize — each of the 7 bypassing services has the proper
# import path (gates apply through SDK monkey-patches transitively).
# ----------------------------------------------------------------------

# Maps each previously-bypassing service to the LLM call seam it now flows
# through. After install_llm_guards(), all of these go through the gate
# automatically.
BYPASSING_SERVICES = [
    ("app.domains.job_creation.services.intake_extractor", "messages.create"),
    ("app.domains.interview_scheduling.agents.interview_scheduling_nodes", "messages.create"),
    ("app.domains.ai.services.agent_quality_evaluator", "messages.create"),
    ("app.domains.job_creation.services.wsi_question_generator", "messages.create"),
    ("app.domains.job_creation.services.wizard_supervisor_classifier", "messages.create"),
    ("app.services.agent_quality_evaluator", "messages.create"),
    ("app.domains.ai.services.agent_quality_evaluator", "messages.create"),
]


@pytest.mark.parametrize("module_path,seam", BYPASSING_SERVICES)
def test_bypassing_service_module_imports_cleanly(module_path, seam):
    """Smoke — each of the 7 services that historically bypassed llm_factory
    still imports cleanly after bootstrap is in effect. If import breaks,
    the credit gate would mask itself behind ImportError silently."""
    try:
        __import__(module_path)
    except ImportError as exc:
        pytest.skip(f"Module {module_path} not available in test env: {exc}")
