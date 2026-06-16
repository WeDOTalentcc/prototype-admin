"""Audit task #637 — `_generate_summary_from_dicts` end-to-end.

Until this task, `_generate_summary_from_dicts` invoked
`self._extract_structured_ids(messages)` but the helper did not exist —
the first dict-based summarization in production raised
``AttributeError`` and silently fell back to the simple summary, losing
both the LLM-backed text and the structured IDs that the comment in the
method promises to preserve.

These tests run the method without any stubs around the helper so that a
future regression (helper deleted again, signature changed, etc.) trips
the suite immediately.
"""
from __future__ import annotations

import pytest

from app.domains.recruiter_assistant.services.conversation_memory import (
    ConversationMemory,
)


class _StubLLM:
    def __init__(self, response: str) -> None:
        self._response = response
        self.calls: list[dict] = []

    async def safe_invoke(self, prompt, *, provider=None, on_usage=None, **kwargs):
        self.calls.append(
            {"prompt": prompt, "provider": provider, "on_usage": on_usage}
        )
        return self._response


def test_extract_structured_ids_finds_uuids_numerics_and_refs():
    mem = ConversationMemory(llm_service=None)

    messages = [
        {
            "role": "user",
            "content": (
                "Olha a vaga 1776373052020 do candidato 42, "
                "uuid 550e8400-e29b-41d4-a716-446655440000."
            ),
        },
        {
            "role": "assistant",
            "content": "ID solto: 9876543210, e job ABC-99.",
        },
    ]

    extracted = mem._extract_structured_ids(messages)

    assert "vaga 1776373052020" in extracted
    assert "candidato 42" in extracted
    assert "job ABC-99" in extracted
    assert "550e8400-e29b-41d4-a716-446655440000" in extracted
    assert "9876543210" in extracted
    # Numeric attached to a labeled ref must not be duplicated outside it.
    assert extracted.count("1776373052020") == 1


def test_extract_structured_ids_empty_when_no_signals():
    mem = ConversationMemory(llm_service=None)
    assert mem._extract_structured_ids([]) == ""
    assert mem._extract_structured_ids(
        [{"role": "user", "content": "oi tudo bem?"}]
    ) == ""


@pytest.mark.asyncio
async def test_generate_summary_from_dicts_runs_without_stubs_no_llm():
    """Without an LLM, the dict summary path must still produce text and
    prepend any structured IDs it found."""
    mem = ConversationMemory(llm_service=None)

    messages = [
        {"role": "user", "content": "Status da vaga 1776373052020?"},
        {"role": "assistant", "content": "Em aberto."},
    ]

    summary = await mem._generate_summary_from_dicts(messages)

    assert summary  # Non-empty — i.e. helper did not crash.
    assert "[IDs preservados:" in summary
    assert "vaga 1776373052020" in summary


@pytest.mark.asyncio
async def test_generate_summary_from_dicts_runs_without_stubs_with_llm():
    """With an LLM the method must call it and prepend preserved IDs to
    the LLM output. No stubbing of `_extract_structured_ids`."""
    llm = _StubLLM("Resumo gerado pelo LLM.")
    mem = ConversationMemory(llm_service=llm)

    messages = [
        {
            "role": "user",
            "content": "Quero ver candidato 42 da vaga 1776373052020.",
        },
        {"role": "assistant", "content": "Ok, abrindo."},
    ]

    summary = await mem._generate_summary_from_dicts(messages)

    assert llm.calls, "LLM safe_invoke should have been called"
    assert summary.startswith("[IDs preservados:")
    assert "vaga 1776373052020" in summary
    assert "candidato 42" in summary
    assert "Resumo gerado pelo LLM." in summary


@pytest.mark.asyncio
async def test_generate_summary_from_dicts_empty_messages_returns_empty():
    mem = ConversationMemory(llm_service=None)
    assert await mem._generate_summary_from_dicts([]) == ""
