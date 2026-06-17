"""
Contract tests — P1.AIC2 (2026-05-22) multimodal vision credit gate.

Validates that `app.domains.ai.services.multimodal_service.MultimodalService`
routes through `anthropic.AsyncAnthropic.messages.create` (and
`google.genai.Client.aio.models.generate_content` for video) so the
`app.shared.llm_bootstrap` monkey-patches enforce `check_credit_budget`
transitively. Closes the gap identified by the Wave 3 AI credits audit.

We test the SHIM, not the SDK. The SDK calls themselves are mocked at the
underlying method seam. The gate is the contract under test.
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.middleware.auth_enforcement import _current_company_id
from app.shared.llm_bootstrap import install_llm_guards
from app.shared.services.ai_credit_gate import AICreditExhausted


# Ensure bootstrap is installed once for the whole module — same idempotent
# install_llm_guards() the production main.py wires.
install_llm_guards()


COMPANY_OK = "test-company-uuid-multimodal"
COMPANY_EXHAUSTED = "test-company-exhausted-multimodal"


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------

def _png_bytes() -> bytes:
    # 1x1 transparent PNG — header is enough for _detect_image_format.
    return (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"
        b"\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00"
        b"\x1f\x15\xc4\x89\x00\x00\x00\rIDATx\x9cc\xf8\xcf\xc0"
        b"\x00\x00\x00\x03\x00\x01]\xa3\x1a\xdf\x00\x00\x00\x00"
        b"IEND\xaeB`\x82"
    )


def _make_anthropic_response(text: str = "ok"):
    """Build a minimal object mimicking Anthropic SDK Message response."""
    block = MagicMock()
    block.type = "text"
    block.text = text
    resp = MagicMock()
    resp.content = [block]
    resp.model = "claude-sonnet-4-20250514"
    resp.usage = MagicMock()
    resp.usage.model_dump = MagicMock(
        return_value={"input_tokens": 100, "output_tokens": 50}
    )
    return resp


# ----------------------------------------------------------------------
# REGRA 4: Without tenant context the gate fail-safe ALLOWs.
# Hard-failing would break test fixtures + internal jobs. Coverage of
# fail-closed-on-real-tenant is in test_async_gate_exhausted_raises below.
# ----------------------------------------------------------------------

@pytest.mark.asyncio
async def test_vision_call_without_context_silently_passes(monkeypatch):
    """Without _current_company_id set, the gate skips (fail-safe ALLOW).

    Verifies the gate path runs (no NameError, no double-patch), and that
    a downstream SDK mock is reached. The companion test
    `test_vision_call_exhausted_credits_raises_ai_credit_exhausted` covers
    the fail-closed-when-exhausted path.
    """
    from app.domains.ai.services.multimodal_service import MultimodalService

    svc = MultimodalService()
    svc.anthropic_key = "sk-test"

    fake_create = AsyncMock(return_value=_make_anthropic_response("hi"))

    token = _current_company_id.set("")
    try:
        with patch.object(
            svc, "_get_anthropic_client", new=AsyncMock(
                return_value=MagicMock(messages=MagicMock(create=fake_create))
            )
        ):
            result = await svc.analyze_image(_png_bytes(), analysis_type="general")
        assert result["analysis"] == "hi"
        fake_create.assert_awaited_once()
    finally:
        _current_company_id.reset(token)


# ----------------------------------------------------------------------
# Tenant set + budget exhausted → AICreditExhausted bubbles through SDK.
# ----------------------------------------------------------------------

@pytest.mark.asyncio
async def test_vision_call_exhausted_credits_raises_ai_credit_exhausted():
    """Verifies the bootstrap gate raises AICreditExhausted before the
    SDK underlying create() is invoked when balance is exhausted.

    We patch `check_credit_budget` (the inner async helper called by the
    monkey-patch's `_enforce_credit_gate_async`) to simulate exhaustion.
    """
    from app.domains.ai.services.multimodal_service import MultimodalService

    svc = MultimodalService()
    svc.anthropic_key = "sk-test"

    # The SDK seam — should NOT be called when gate raises.
    fake_create = AsyncMock(return_value=_make_anthropic_response("never"))

    token = _current_company_id.set(COMPANY_EXHAUSTED)
    try:
        with patch(
            "app.shared.services.ai_credit_gate.check_credit_budget",
            new=AsyncMock(
                side_effect=AICreditExhausted(
                    "exhausted",
                    company_id=COMPANY_EXHAUSTED,
                    remaining=0,
                    service="multimodal_service",
                )
            ),
        ), patch.object(
            svc, "_get_anthropic_client", new=AsyncMock(
                return_value=MagicMock(messages=MagicMock(create=fake_create))
            )
        ):
            with pytest.raises(AICreditExhausted) as exc_info:
                await svc.analyze_image(_png_bytes(), analysis_type="general")

        assert exc_info.value.company_id == COMPANY_EXHAUSTED
        # Critical: the SDK was NEVER called because the gate raised first.
        fake_create.assert_not_awaited()
    finally:
        _current_company_id.reset(token)


# ----------------------------------------------------------------------
# Estimator: the gate is called with a non-zero estimated token count
# computed from the image-bearing messages payload.
# ----------------------------------------------------------------------

@pytest.mark.asyncio
async def test_vision_call_decrements_estimated_tokens():
    """The Anthropic monkey-patch must invoke check_credit_budget with a
    positive estimated_tokens. We capture the kwargs passed to the inner
    helper to assert this.

    NOTE: The bootstrap uses `_enforce_credit_gate_sync` on Anthropic's
    `messages.create` (which is sync from the SDK's perspective, even on
    AsyncAnthropic — the wrapper awaits internally). We patch the gate
    helper used in that path.
    """
    captured: dict = {}

    async def _fake_check(_db, company_id, *, estimated_tokens, service, **kwargs):
        captured["company_id"] = company_id
        captured["estimated_tokens"] = estimated_tokens
        captured["service"] = service
        return {"monthly_limit": 100000, "current_usage": 0, "remaining": 100000}

    from app.domains.ai.services.multimodal_service import MultimodalService

    svc = MultimodalService()
    svc.anthropic_key = "sk-test"

    fake_create = AsyncMock(return_value=_make_anthropic_response("done"))

    token = _current_company_id.set(COMPANY_OK)
    try:
        with patch(
            "app.shared.services.ai_credit_gate.check_credit_budget",
            new=_fake_check,
        ), patch.object(
            svc, "_get_anthropic_client", new=AsyncMock(
                return_value=MagicMock(messages=MagicMock(create=fake_create))
            )
        ):
            await svc.analyze_image(_png_bytes(), analysis_type="general")

        # The gate ran with a real company_id and a non-zero estimate.
        assert captured.get("company_id") == COMPANY_OK
        # Vision prompt + max_tokens=4096 should produce a non-trivial estimate.
        assert captured.get("estimated_tokens", 0) > 100
        # service label is inferred from caller stack walk.
        assert captured.get("service")  # non-empty
    finally:
        _current_company_id.reset(token)
