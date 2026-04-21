"""FIX 26 (2026-04-21) — Quantifier patterns + contextual_inference rule.

Closes chat gap: user said "todas" after LIA listed job statuses → LIA asked
"'Todas' o quê?" (clarification spam). Root causes:
  1. memory_resolver._should_resolve() has no quantifier patterns, so "todas"
     bypasses the enrichment gate.
  2. lia_persona.yaml has no rule telling LIA that a 1-2 word reply following
     its own question = continuation (not new standalone query).

Canonical-fix (both sides):
  - memory_resolver: add _QUANTIFIER_PATTERNS to gate
  - lia_persona: add `contextual_inference` rule

Non-goals: full Initiative II state machine.
"""
from __future__ import annotations

import pytest


@pytest.mark.parametrize(
    "msg",
    ["todas", "todos", "nenhum", "nenhuma", "alguns", "algumas",
     "tudo", "cada", "qualquer", "TODAS", "  todas  "],
)
def test_should_resolve_catches_quantifier(msg: str) -> None:
    """FIX 26: memory_resolver gate must accept quantifier-only messages.

    Without this, 'todas' (continuation of a prior list question) bypasses
    the enrichment gate and LIA asks 'todas o quê?' in the next turn.
    """
    from app.orchestrator.memory_resolver import _should_resolve

    assert _should_resolve(msg) is True, (
        f"FIX 26: {msg!r} (quantifier) should trigger memory resolver gate "
        f"so resolve() can inject last-entity context"
    )


@pytest.mark.parametrize(
    "msg",
    ["busque python em SP", "crie vacancy X", "cancele V0042 por orçamento"],
)
def test_should_resolve_does_not_regress_on_concrete_messages(msg: str) -> None:
    """FIX 26 regression: concrete action messages should NOT trigger gate just
    because the quantifier regex is permissive.
    """
    from app.orchestrator.memory_resolver import _should_resolve

    # These messages have no pronouns, no entity refs, no positional, no
    # affirmation, and (crucially) no bare quantifier. Gate should be False.
    assert _should_resolve(msg) is False, (
        f"FIX 26: {msg!r} is a concrete action, gate must stay False "
        f"(quantifier regex should not over-match)"
    )


def test_fix26_marker_in_memory_resolver() -> None:
    """FIX 26 audit marker."""
    from pathlib import Path

    import app.orchestrator.memory_resolver as mr

    source = Path(mr.__file__).read_text(encoding="utf-8")
    assert "FIX 26" in source, (
        "FIX 26: memory_resolver.py must contain FIX 26 marker for traceability"
    )
    assert "_QUANTIFIER_PATTERNS" in source, (
        "FIX 26: memory_resolver must define _QUANTIFIER_PATTERNS regex"
    )


def test_contextual_inference_rule_in_lia_persona() -> None:
    """FIX 26: persona YAML must include contextual_inference rule.

    Without this rule, LLM defaults to asking 'X o quê?' on ambiguous short
    replies instead of inferring continuation from the prior 3 messages.
    """
    from pathlib import Path

    # Walk up to find lia-agent-system/app/prompts/shared/lia_persona.yaml
    here = Path(__file__).resolve()
    for parent in here.parents:
        candidate = parent / "app/prompts/shared/lia_persona.yaml"
        if candidate.exists():
            break
    else:
        raise RuntimeError("lia_persona.yaml not found")

    # Post-FIX 29: rule migrated from top-level key INTO prompts.lia_persona.
    # Check inside the rendered persona content (single source of truth).
    import yaml
    data = yaml.safe_load(candidate.read_text(encoding="utf-8"))
    persona = data["prompts"]["lia_persona"].lower()
    assert "fix 26" in persona or "fix 29" in persona, (
        "FIX 26 (post-FIX 29): marker must be in prompts.lia_persona content"
    )
    assert "inferência contextual" in persona or "inferencia contextual" in persona or "infer" in persona, (
        "FIX 26 (post-FIX 29): persona must include Inferência Contextual section"
    )
    assert "o quê" in persona or "o que" in persona or "quê?" in persona or "que?" in persona, (
        "FIX 26: rule must explicitly call out 'X o quê?' as forbidden anti-pattern"
    )
