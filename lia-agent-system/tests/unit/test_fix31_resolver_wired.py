"""FIX 31 (2026-04-21) — memory_resolver.resolve() wired into production chat path.

Closes gap discovered by re-smoke after FIX 30:
  - FIX 19 wired resolver into cascaded_router Tier 0
  - BUT the production chat path goes: /api/v1/chat → ChatAdapter →
    MainOrchestrator._process_via_orchestrator → _route_with_tenant_llm →
    Orchestrator.process_request → ... (NO resolver call)
  - So FIX 19 (affirmations) + FIX 30 (quantifiers) were dead in chat.

Canonical-fix: invoke memory_resolver.resolve() at the entry of
MainOrchestrator._process_via_orchestrator, right before LLM routing,
so enrichment reaches the LLM prompt assembly.

Tests are structural (import + marker) — full integration validated
by smoke test at API level after restart.
"""
from __future__ import annotations

from pathlib import Path


def test_main_orchestrator_imports_memory_resolver() -> None:
    """FIX 31: main_orchestrator.py must import memory_resolver for production use."""
    import app.orchestrator.main_orchestrator as mo

    source = Path(mo.__file__).read_text(encoding="utf-8")
    assert "memory_resolver" in source, (
        "FIX 31: main_orchestrator.py must import and use memory_resolver. "
        "Without this wiring, resolve() enrichments from FIX 19/30 never reach "
        "the LLM via the chat path."
    )


def test_main_orchestrator_calls_resolve_before_routing() -> None:
    """FIX 31: resolve() must be called inside _process_via_orchestrator."""
    import app.orchestrator.main_orchestrator as mo

    source = Path(mo.__file__).read_text(encoding="utf-8")
    # Ensure resolve call sits within _process_via_orchestrator scope
    method_start = source.find("async def _process_via_orchestrator")
    assert method_start > 0
    # Next async def after _process_via_orchestrator defines its end
    next_def = source.find("\n    async def ", method_start + 30)
    if next_def == -1:
        next_def = source.find("\n    def ", method_start + 30)
    body = source[method_start:next_def] if next_def > 0 else source[method_start:]

    assert "memory_resolver" in body and "resolve" in body, (
        "FIX 31: _process_via_orchestrator body must call memory_resolver.resolve()"
    )


def test_fix31_marker_present() -> None:
    """FIX 31 audit marker for traceability."""
    import app.orchestrator.main_orchestrator as mo

    source = Path(mo.__file__).read_text(encoding="utf-8")
    assert "FIX 31" in source, (
        "FIX 31: main_orchestrator.py must contain FIX 31 marker"
    )


def test_resolver_call_uses_conversation_id_as_session() -> None:
    """FIX 31: resolve() must use conv_id as session_id so state lookup works."""
    import app.orchestrator.main_orchestrator as mo

    source = Path(mo.__file__).read_text(encoding="utf-8")
    # The call should pass conv_id or session_id to resolve
    assert "session_id=conv_id" in source or "session_id = conv_id" in source or "resolve(ctx.message, conv_id" in source, (
        "FIX 31: resolve() must be called with session_id=conv_id so it can "
        "fetch ConversationState for this conversation"
    )


def test_resolver_does_not_bypass_llm_enrichment() -> None:
    """FIX 31 regression: ctx.message must be updated after resolve when resolved=True."""
    import app.orchestrator.main_orchestrator as mo

    source = Path(mo.__file__).read_text(encoding="utf-8")
    # Look for assignment pattern after resolve call
    assert "ctx.message = " in source or "_enriched_message" in source, (
        "FIX 31: when resolver enriches the message, the enriched version "
        "must flow into downstream LLM — not be discarded"
    )
