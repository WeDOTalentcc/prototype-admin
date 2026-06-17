"""Sprint 1.1 (B) — _interpret_action_result must include conversation_history.

This is the producer-level fix for N4 ("ficou incompleta") that complements
the persona Anti-pattern #7 fix (commit 9684e730).

Persona Anti-pattern #7 is defense in depth (LLM-side rule). This test pins
the canonical producer-side fix: when the humanizer constructs the
interpretation prompt, it MUST inject `conversation_history` so the LLM can
disambiguate short replies ("sim", "ok", "vamos") that arrive at Phase 0/1.

Without this, the LLM gets a prompt like
    O usuario Paulo pediu: sim
    A acao 'X' foi executada com sucesso.
and defaults to its pretrained "incomplete message" response shape.

With this fix, the prompt becomes
    O usuario Paulo pediu: sim
    ### Historico recente
    - user: vamos abrir a tela de vagas?
    - assistant: Posso te levar ate a tela de vagas. Confirma?
    A acao 'navigate_to' foi executada com sucesso.
which lets the LLM produce a contextual reply.
"""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.orchestrator.execution.main_orchestrator import MainOrchestrator


def _make_orch():
    # Bypass __init__ to avoid heavy DI; we test pure prompt construction.
    return MainOrchestrator.__new__(MainOrchestrator)


def _make_ctx(message: str = "sim", user_name: str = "Paulo"):
    ctx = MagicMock()
    ctx.message = message
    ctx.user_name = user_name
    return ctx


def _make_action_result(action_type: str = "navigate_to", message: str = "OK"):
    ar = MagicMock()
    ar.action_type = action_type
    ar.message = message
    ar.data = None
    return ar


@pytest.mark.asyncio
async def test_interpret_action_result_injects_conversation_history():
    """RED: humanizer prompt must include 'Historico recente' block when history non-empty."""
    orch = _make_orch()
    ctx = _make_ctx("sim")
    ar = _make_action_result("navigate_to", "Tela aberta")

    orchestrator_context = {
        "user_name": "Paulo",
        "user_role": "recruiter",
        "conversation_history": [
            {"role": "user", "content": "vamos abrir a tela de vagas?"},
            {"role": "assistant", "content": "Posso te levar ate a tela de vagas. Confirma?"},
        ],
        "conversation_summary": None,
    }

    captured = {}

    async def fake_generate(**kwargs):
        captured["prompt"] = kwargs.get("prompt", "")
        return "Pronto, tela de vagas aberta."

    with patch("app.domains.ai.services.llm.LLMService") as mock_cls:
        mock_cls.return_value.generate = AsyncMock(side_effect=fake_generate)
        result = await orch._interpret_action_result(ctx, ar, orchestrator_context)

    assert result is not None, "humanizer returned None unexpectedly"
    prompt = captured.get("prompt", "")
    assert prompt, "LLM was not called"

    # CRITICAL N4 ASSERTIONS:
    assert "Historico recente" in prompt or "Histórico recente" in prompt, (
        "Producer-side N4 fix not applied — history block missing.\n"
        f"Prompt was:\n---\n{prompt}\n---"
    )
    assert "vamos abrir a tela de vagas?" in prompt, "prior user turn missing"
    assert "Posso te levar" in prompt, "prior assistant turn missing"


@pytest.mark.asyncio
async def test_interpret_action_result_omits_history_block_when_empty():
    """Empty history → no block (avoid noise in prompt)."""
    orch = _make_orch()
    ctx = _make_ctx("criar vaga", "Paulo")
    ar = _make_action_result("create_job", "Vaga criada")

    orchestrator_context = {
        "user_name": "Paulo",
        "user_role": "recruiter",
        "conversation_history": [],
        "conversation_summary": None,
    }

    captured = {}

    async def fake_generate(**kwargs):
        captured["prompt"] = kwargs.get("prompt", "")
        return "Vaga criada!"

    with patch("app.domains.ai.services.llm.LLMService") as mock_cls:
        mock_cls.return_value.generate = AsyncMock(side_effect=fake_generate)
        await orch._interpret_action_result(ctx, ar, orchestrator_context)

    prompt = captured.get("prompt", "")
    # When history is empty, the block must not appear (no orphan headers).
    assert "Historico recente" not in prompt and "Histórico recente" not in prompt


@pytest.mark.asyncio
async def test_interpret_action_result_includes_summary_when_provided():
    """Long conversations have a summary; humanizer should surface it."""
    orch = _make_orch()
    ctx = _make_ctx("ok", "Paulo")
    ar = _make_action_result("confirm", "OK")

    orchestrator_context = {
        "user_name": "Paulo",
        "user_role": "recruiter",
        "conversation_history": [
            {"role": "user", "content": "blz"},
        ],
        "conversation_summary": "Paulo esta revisando 3 vagas abertas e quer fechar uma delas.",
    }

    captured = {}

    async def fake_generate(**kwargs):
        captured["prompt"] = kwargs.get("prompt", "")
        return "Pronto!"

    with patch("app.domains.ai.services.llm.LLMService") as mock_cls:
        mock_cls.return_value.generate = AsyncMock(side_effect=fake_generate)
        await orch._interpret_action_result(ctx, ar, orchestrator_context)

    prompt = captured.get("prompt", "")
    assert "Resumo da conversa anterior" in prompt or "Resumo da conversa" in prompt, (
        "summary block missing"
    )
    assert "revisando 3 vagas" in prompt


@pytest.mark.asyncio
async def test_interpret_action_result_truncates_history_to_last_6():
    """Bloat-guard: only last 6 turns are included to keep prompt small."""
    orch = _make_orch()
    ctx = _make_ctx("sim", "Paulo")
    ar = _make_action_result("navigate_to", "OK")

    long_history = [
        {"role": "user" if i % 2 == 0 else "assistant", "content": f"turn-{i}"}
        for i in range(20)
    ]
    orchestrator_context = {
        "user_name": "Paulo",
        "user_role": "recruiter",
        "conversation_history": long_history,
        "conversation_summary": None,
    }

    captured = {}

    async def fake_generate(**kwargs):
        captured["prompt"] = kwargs.get("prompt", "")
        return "OK"

    with patch("app.domains.ai.services.llm.LLMService") as mock_cls:
        mock_cls.return_value.generate = AsyncMock(side_effect=fake_generate)
        await orch._interpret_action_result(ctx, ar, orchestrator_context)

    prompt = captured.get("prompt", "")
    # The last 6 turns must be in the prompt, earlier ones not.
    assert "turn-19" in prompt, "most recent turn missing"
    assert "turn-14" in prompt, "boundary turn missing (last 6 = 14..19)"
    assert "turn-13" not in prompt, "older turn leaked — truncation broken"
    assert "turn-0" not in prompt, "oldest turn leaked — truncation broken"
