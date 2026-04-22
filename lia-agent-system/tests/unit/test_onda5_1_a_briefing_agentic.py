"""Onda 5.1.a — ctx.extra['extra_instructions'] must reach agentic_loop system_prompt.

PARTE L-class bug: IV.B (Onda 4.4) injects briefing into
`ctx.extra["extra_instructions"]`, but the agentic_loop call site at
main_orchestrator.py:~520 passes only `_proactive_hints_text` to
SystemPromptBuilder.build(extra_instructions=...) — dropping the briefing.

Canonical-fix: producer (IV.B wire) is correct; consumer (agentic call
site) was too narrow. Merge both before passing.

Tests are structural: assert the call site reads and merges
ctx.extra["extra_instructions"] before invoking SystemPromptBuilder.
"""
from __future__ import annotations

from pathlib import Path


def _orchestrator_source() -> str:
    p = Path(__file__).resolve()
    for parent in p.parents:
        cand = parent / "app/orchestrator/main_orchestrator.py"
        if cand.exists():
            return cand.read_text(encoding="utf-8")
    raise RuntimeError("main_orchestrator.py not found")


def test_agentic_call_reads_extra_instructions_from_ctx() -> None:
    """Onda 5.1.a: agentic loop path must consume ctx.extra['extra_instructions'].

    Scope: from `_proactive_hints_text` assignment (setup) through the
    agentic_loop.run call (final LLM invocation).
    """
    src = _orchestrator_source()
    # Widen scope: start at proactive hints assignment (upstream setup)
    # and end at agentic_loop.run invocation.
    start = src.find('ctx.extra["proactive_hints"]')
    assert start > 0, "proactive hints anchor missing"
    end = src.find("agentic_loop.run(", start)
    assert end > 0
    block = src[start:end]
    assert 'ctx.extra.get("extra_instructions"' in block or \
           "ctx.extra.get('extra_instructions'" in block, (
        "Onda 5.1.a: agentic path must merge ctx.extra['extra_instructions'] "
        "(briefing_context producer)"
    )


def test_merged_instructions_include_proactive_hints() -> None:
    """Onda 5.1.a: proactive_hints must still be forwarded (regression)."""
    src = _orchestrator_source()
    start = src.find('ctx.extra["proactive_hints"]')
    end = src.find("agentic_loop.run(", start)
    block = src[start:end]
    # Either inline or as part of merge variable — both forms preserve it
    assert "_proactive_hints_text" in block, (
        "regression: _proactive_hints_text still needs to reach prompt"
    )
    # And the final extra_instructions= kwarg must point at merged or original
    assert "extra_instructions=" in block


def test_marker_onda5_1_in_source() -> None:
    """Onda 5.1.a: traceability marker present."""
    src = _orchestrator_source()
    assert "Onda 5.1" in src, "Onda 5.1 marker must be in source"
