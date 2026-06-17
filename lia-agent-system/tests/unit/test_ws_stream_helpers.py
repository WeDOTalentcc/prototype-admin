"""
PM-02 (Audit Rev 4) — streaming token-level via `astream_events("v2")`.

Cobre o helper `app.api.v1._ws_stream_helpers`:
  * `is_token_streaming_enabled()` lê env var.
  * `stream_wizard_tokens()` extrai chunks de eventos LangGraph e chama
    `on_token` por chunk.
  * Eventos sem texto utilizável são ignorados (filter).
  * `max_tokens` faz truncate seguro.
  * `on_token` que levanta exceção não quebra o stream.
"""
from __future__ import annotations

import asyncio
from types import SimpleNamespace
from typing import Any, AsyncIterator

import pytest

pytestmark = pytest.mark.easy

from app.api.v1._ws_stream_helpers import (
    is_token_streaming_enabled,
    stream_wizard_tokens,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _aiter(events: list[dict[str, Any]]) -> AsyncIterator[dict[str, Any]]:
    for event in events:
        yield event


def _chat_event(text: str) -> dict[str, Any]:
    """Mimic a `on_chat_model_stream` event from LangGraph v2."""
    return {
        "event": "on_chat_model_stream",
        "data": {"chunk": SimpleNamespace(content=text)},
    }


def _llm_event(text: str) -> dict[str, Any]:
    """Mimic the legacy `on_llm_stream` shape."""
    return {
        "event": "on_llm_stream",
        "data": {"chunk": SimpleNamespace(text=text)},
    }


# ---------------------------------------------------------------------------
# Feature flag
# ---------------------------------------------------------------------------


class TestFeatureFlag:

    def test_default_off(self, monkeypatch):
        monkeypatch.delenv("LIA_WS_TOKEN_STREAMING", raising=False)
        assert is_token_streaming_enabled() is False

    @pytest.mark.parametrize("value", ["1", "true", "TRUE", "yes", "Yes"])
    def test_truthy_values(self, monkeypatch, value):
        monkeypatch.setenv("LIA_WS_TOKEN_STREAMING", value)
        assert is_token_streaming_enabled() is True

    @pytest.mark.parametrize("value", ["0", "false", "no", "", "maybe"])
    def test_falsy_values(self, monkeypatch, value):
        monkeypatch.setenv("LIA_WS_TOKEN_STREAMING", value)
        assert is_token_streaming_enabled() is False


# ---------------------------------------------------------------------------
# stream_wizard_tokens
# ---------------------------------------------------------------------------


class TestStreamWizardTokens:

    @pytest.mark.asyncio
    async def test_emits_chat_model_stream_chunks(self):
        events = [_chat_event("Olá "), _chat_event("mundo"), _chat_event("!")]
        captured: list[str] = []

        async def on_token(t: str) -> None:
            captured.append(t)

        emitted = await stream_wizard_tokens(_aiter(events), on_token=on_token)

        assert emitted == 3
        assert captured == ["Olá ", "mundo", "!"]

    @pytest.mark.asyncio
    async def test_emits_legacy_llm_stream_chunks(self):
        events = [_llm_event("ABC"), _llm_event("DEF")]
        captured: list[str] = []

        async def on_token(t: str) -> None:
            captured.append(t)

        emitted = await stream_wizard_tokens(_aiter(events), on_token=on_token)

        assert emitted == 2
        assert captured == ["ABC", "DEF"]

    @pytest.mark.asyncio
    async def test_filters_unrelated_events(self):
        events = [
            {"event": "on_chain_start", "data": {}},
            _chat_event("Hi"),
            {"event": "on_tool_end", "data": {"output": "ignored"}},
            _chat_event(" there"),
        ]
        captured: list[str] = []

        async def on_token(t: str) -> None:
            captured.append(t)

        emitted = await stream_wizard_tokens(_aiter(events), on_token=on_token)

        assert emitted == 2
        assert captured == ["Hi", " there"]

    @pytest.mark.asyncio
    async def test_filters_empty_chunks(self):
        events = [
            _chat_event(""),
            _chat_event("real"),
            {"event": "on_chat_model_stream", "data": {"chunk": SimpleNamespace(content=None)}},
        ]
        captured: list[str] = []

        async def on_token(t: str) -> None:
            captured.append(t)

        emitted = await stream_wizard_tokens(_aiter(events), on_token=on_token)

        assert emitted == 1
        assert captured == ["real"]

    @pytest.mark.asyncio
    async def test_max_tokens_truncates(self):
        events = [_chat_event(str(i)) for i in range(20)]
        captured: list[str] = []

        async def on_token(t: str) -> None:
            captured.append(t)

        emitted = await stream_wizard_tokens(
            _aiter(events), on_token=on_token, max_tokens=5
        )

        assert emitted == 5
        assert captured == ["0", "1", "2", "3", "4"]

    @pytest.mark.asyncio
    async def test_on_token_failure_isolated(self):
        events = [_chat_event("a"), _chat_event("b"), _chat_event("c")]
        attempts: list[str] = []

        async def flaky_on_token(t: str) -> None:
            attempts.append(t)
            if t == "b":
                raise RuntimeError("ws send failed")

        emitted = await stream_wizard_tokens(_aiter(events), on_token=flaky_on_token)

        # All 3 tokens were attempted; "b" failed silently. Helper still
        # returns the count of *attempted* emissions for observability.
        assert attempts == ["a", "b", "c"]
        assert emitted == 2  # Only "a" and "c" succeeded

    @pytest.mark.asyncio
    async def test_multipart_content_concatenated(self):
        # Some LLM SDKs return list-of-parts (text + non-text). Helper
        # concatenates only the str parts.
        events = [
            {
                "event": "on_chat_model_stream",
                "data": {
                    "chunk": SimpleNamespace(
                        content=["hello ", {"type": "image_url", "url": "x"}, "world"]
                    )
                },
            }
        ]
        captured: list[str] = []

        async def on_token(t: str) -> None:
            captured.append(t)

        emitted = await stream_wizard_tokens(_aiter(events), on_token=on_token)

        assert emitted == 1
        assert captured == ["hello world"]

    @pytest.mark.asyncio
    async def test_dict_chunk_shape(self):
        events = [
            {
                "event": "on_chat_model_stream",
                "data": {"chunk": {"content": "from-dict"}},
            }
        ]
        captured: list[str] = []

        async def on_token(t: str) -> None:
            captured.append(t)

        emitted = await stream_wizard_tokens(_aiter(events), on_token=on_token)

        assert emitted == 1
        assert captured == ["from-dict"]
