"""Onda 4.2 G4.B — cost_tracker wired into ClaudeLLMProvider tests."""
from __future__ import annotations

from pathlib import Path


def test_g4b_marker_in_llm_claude() -> None:
    """G4.B: llm_claude.py must contain G4.B marker + _record_cost_call import."""
    import app.shared.providers.llm_claude as mod

    source = Path(mod.__file__).read_text(encoding="utf-8")
    assert "G4.B" in source
    assert "_record_cost_call" in source
    assert "cost_tracker" in source


def test_generate_calls_record_cost_on_success(monkeypatch) -> None:
    """G4.B runtime: generate() invokes record_call with tenant+tokens."""
    import asyncio
    from unittest.mock import AsyncMock, MagicMock, patch

    from app.shared.providers.llm_claude import ClaudeLLMProvider

    # Mock Anthropic response
    fake_usage = MagicMock()
    fake_usage.input_tokens = 1000
    fake_usage.output_tokens = 250
    fake_content = [MagicMock(text="hello")]
    fake_response = MagicMock(content=fake_content, usage=fake_usage)

    fake_client = MagicMock()
    fake_client.messages.create = MagicMock(return_value=fake_response)

    provider = ClaudeLLMProvider(api_key="test-dummy")
    provider._client = fake_client

    calls_recorded: list = []

    def _spy(**kwargs):
        calls_recorded.append(kwargs)
        return {}

    with patch("app.shared.providers.llm_claude._record_cost_call", side_effect=_spy):
        with patch(
            "app.shared.providers.llm_claude._get_tenant",
            return_value="tenant-g4b-test",
        ):
            result = asyncio.run(provider.generate("test prompt", model="claude-haiku-4-5"))

    assert result.text == "hello"
    assert len(calls_recorded) == 1
    call = calls_recorded[0]
    assert call["tenant_id"] == "tenant-g4b-test"
    assert call["model"] == "claude-haiku-4-5"
    assert call["input_tokens"] == 1000
    assert call["output_tokens"] == 250
    assert call["latency_ms"] >= 0


def test_generate_does_not_crash_if_cost_tracker_raises() -> None:
    """G4.B resilience: cost_tracker error is non-fatal for generate()."""
    import asyncio
    from unittest.mock import MagicMock, patch

    from app.shared.providers.llm_claude import ClaudeLLMProvider

    fake_usage = MagicMock(input_tokens=100, output_tokens=50)
    fake_response = MagicMock(content=[MagicMock(text="ok")], usage=fake_usage)
    fake_client = MagicMock()
    fake_client.messages.create = MagicMock(return_value=fake_response)

    provider = ClaudeLLMProvider(api_key="test")
    provider._client = fake_client

    def _boom(**_):
        raise RuntimeError("cost tracker exploded")

    with patch("app.shared.providers.llm_claude._record_cost_call", side_effect=_boom):
        # Should NOT raise — generate must return normally
        result = asyncio.run(provider.generate("x"))
    assert result.text == "ok"


def test_record_cost_call_importable() -> None:
    """G4.B: _record_cost_call must be importable at module level."""
    from app.shared.providers.llm_claude import _record_cost_call, _get_tenant

    # They are fail-safe stubs even if sources unavailable
    assert callable(_record_cost_call)
    assert callable(_get_tenant)
