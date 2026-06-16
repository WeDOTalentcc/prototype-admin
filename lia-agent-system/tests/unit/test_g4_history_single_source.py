"""G4 canonical contract — conversation_history reaches all consumers.

Before this fix, _setup_conversation_memory only populated
orchestrator_context (legacy Phase 2 path). Phase 1.5 agentic_loop
reads ctx.extra["conversation_history"] which was never set, so the
LLM saw [] history and treated every turn as a fresh session.

Tests pin the canonical contract: history populated in both places
from a single conversation_memory.get_context_for_llm source.
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.orchestrator.context.context_adapter import UniversalContext


@pytest.mark.asyncio
async def test_setup_conversation_memory_populates_ctx_extra():
    """G4: _setup_conversation_memory must populate BOTH orchestrator_context
    AND ctx.extra with conversation_history (single source, two consumers)."""
    from app.orchestrator.execution.main_orchestrator import MainOrchestrator

    # Build a minimal MainOrchestrator without invoking __init__.
    instance = MainOrchestrator.__new__(MainOrchestrator)

    ctx = UniversalContext(
        message="oi",
        user_id="u1",
        company_id="tenant-a",
        channel="rest",
        context_page="general",
        context_type="general",
        skip_memory_persist=False,
    )
    orch_ctx: dict = {}

    fake_history = [
        {"role": "user", "content": "olá"},
        {"role": "assistant", "content": "oi! como posso ajudar?"},
    ]
    fake_summary = "User cumprimentou, LIA respondeu."

    fake_conv = MagicMock()
    fake_conv.id = "conv-abc"

    fake_memory = MagicMock()
    fake_memory.get_conversation = AsyncMock(return_value=fake_conv)
    fake_memory.get_or_create_conversation = AsyncMock(return_value=fake_conv)
    fake_memory.add_message = AsyncMock()
    fake_memory.get_context_for_llm = AsyncMock(return_value={
        "messages": fake_history,
        "summary": fake_summary,
    })

    with patch(
        "app.domains.recruiter_assistant.services.conversation_memory."
        "conversation_memory",
        fake_memory,
    ):
        await instance._setup_conversation_memory(ctx, "conv-abc", db=MagicMock(), orchestrator_context=orch_ctx)

    # Legacy path (orchestrator_context) — was already populated
    assert orch_ctx["conversation_history"] == fake_history
    assert orch_ctx["conversation_summary"] == fake_summary

    # G4 canonical contract: ctx.extra also populated
    assert ctx.extra["conversation_history"] == fake_history, (
        "ctx.extra.conversation_history not populated — agentic_loop will "
        "still see empty history and the LLM will generate "
        '"sua mensagem ficou incompleta" on short replies like "sim".'
    )
    assert ctx.extra["conversation_summary"] == fake_summary


@pytest.mark.asyncio
async def test_setup_uses_single_source():
    """G4: ctx.extra and orchestrator_context must contain IDENTICAL
    history references (same call to get_context_for_llm)."""
    from app.orchestrator.execution.main_orchestrator import MainOrchestrator

    instance = MainOrchestrator.__new__(MainOrchestrator)
    ctx = UniversalContext(
        message="ok",
        user_id="u1",
        company_id="tenant-a",
        channel="rest",
        skip_memory_persist=False,
    )
    orch_ctx: dict = {}

    fake_history = [{"role": "user", "content": "vamos ver vagas"}]
    fake_memory = MagicMock()
    fake_memory.get_or_create_conversation = AsyncMock(return_value=MagicMock(id="conv-x"))
    fake_memory.add_message = AsyncMock()
    fake_memory.get_context_for_llm = AsyncMock(return_value={
        "messages": fake_history,
        "summary": None,
    })

    with patch(
        "app.domains.recruiter_assistant.services.conversation_memory."
        "conversation_memory",
        fake_memory,
    ):
        await instance._setup_conversation_memory(ctx, "", db=MagicMock(), orchestrator_context=orch_ctx)

    # Same call data → same content (single source)
    assert orch_ctx["conversation_history"] == ctx.extra["conversation_history"]
    # get_context_for_llm was called only ONCE (no duplicate query)
    assert fake_memory.get_context_for_llm.call_count == 1
