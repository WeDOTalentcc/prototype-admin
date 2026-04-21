"""FIX 30 (2026-04-21) — memory_resolver.resolve() enriquecer quantifier.

Closes the runtime-inert gap where FIX 26 added _QUANTIFIER_PATTERNS to the
gate but resolve() returned passthrough when no entity context existed.

Smoke test evidence (before FIX 30):
  Turn 1: 'quantas vagas por status?' → LIA answers (no last_entity set, just
  aggregation)
  Turn 2: 'todas' → LIA: "preciso que você me diga a que se refere" (bug)

FIX 30: resolve() now injects a quantifier continuation hint regardless of
ConversationState content, instructing the LLM to use conversation history.
"""
from __future__ import annotations

import asyncio


def _run(coro):
    return asyncio.run(coro)


def test_resolve_quantifier_no_state_injects_hint() -> None:
    """FIX 30: 'todas' with no conversation_state must still enrich with continuation hint."""
    from app.orchestrator.memory_resolver import MemoryResolver

    resolver = MemoryResolver()
    enriched, resolved = _run(resolver.resolve("todas", session_id="sess-fix30"))

    assert resolved is True, (
        "FIX 30: resolve() must return resolved=True for quantifier even without entity state"
    )
    assert "quantifier" in enriched.lower() or "FIX 30" in enriched, (
        "FIX 30: enriched message must include quantifier continuation hint"
    )
    assert "todas" in enriched, "FIX 30: original message content preserved"
    assert "x o quê" in enriched.lower() or "o quê?" in enriched.lower(), (
        "FIX 30: hint must explicitly call out 'X o quê?' anti-pattern so LLM avoids it"
    )


def test_resolve_quantifier_with_state_combines_hints() -> None:
    """FIX 30: when both state context AND quantifier hint apply, both must inject."""
    from app.orchestrator.memory_resolver import MemoryResolver
    from app.shared.memory.conversation_state import ConversationState

    state = ConversationState(
        company_id="co-test",
        last_entity={"type": "vaga", "id": "v0042", "name": "Backend Sr"},
    )
    resolver = MemoryResolver()
    enriched, resolved = _run(resolver.resolve("todas", session_id="sess-fix30-ctx", conversation_state=state))

    assert resolved is True
    low = enriched.lower()
    # Both context AND quantifier hint should appear
    assert "contexto da sessão" in low or "contexto da sessao" in low or "v0042" in enriched, (
        "FIX 30: should preserve existing ConversationState context enrichment"
    )
    assert "quantifier" in low or "FIX 30" in enriched, (
        "FIX 30: should also add quantifier continuation hint"
    )


def test_resolve_non_quantifier_does_not_add_hint() -> None:
    """FIX 30 regression: pronouns/refs should NOT trigger quantifier hint."""
    from app.orchestrator.memory_resolver import MemoryResolver

    resolver = MemoryResolver()
    enriched, _ = _run(resolver.resolve("mostra ele", session_id="sess-pronoun"))

    assert "quantifier" not in enriched.lower() and "FIX 30" not in enriched, (
        "FIX 30: non-quantifier messages must not receive quantifier hint"
    )


def test_resolve_concrete_action_not_affected() -> None:
    """FIX 30 regression: concrete action messages pass unchanged."""
    from app.orchestrator.memory_resolver import MemoryResolver

    resolver = MemoryResolver()
    enriched, resolved = _run(resolver.resolve("busque python em SP", session_id="sess-concrete"))

    assert enriched == "busque python em SP"
    assert resolved is False


def test_fix30_marker_in_memory_resolver() -> None:
    """FIX 30 audit marker."""
    from pathlib import Path

    import app.orchestrator.memory_resolver as mr

    source = Path(mr.__file__).read_text(encoding="utf-8")
    assert "FIX 30" in source, (
        "FIX 30: memory_resolver.py must contain FIX 30 marker"
    )
    assert "quantifier" in source.lower() and "resolve" in source, (
        "FIX 30: memory_resolver must have quantifier enrichment in resolve()"
    )
