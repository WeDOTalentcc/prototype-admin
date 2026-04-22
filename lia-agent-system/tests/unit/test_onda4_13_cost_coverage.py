"""Onda 4.13 — G4.B cost tracking coverage across ALL active LLM paths.

Runtime smoke revealed PARTE L gap: cost_tracker.record_call emits
[LIA-COST] correctly, but the chat flow uses tool-call paths that were
NEVER wired. Onda 4.2 only wired generate() + generate_with_system(),
which chat never invokes.

Canonical-fix: wire producer (record_call) into the 3 active caller
sites. Add Gemini pricing so estimate_cost_usd doesn't silently fall
back to Claude haiku pricing (cost drift).

Tests are structural (source grep) because wiring SDK clients in unit
tests requires heavy mocking; runtime smoke (post-patch) validates
actual log emission.
"""
from __future__ import annotations

from pathlib import Path


def _root() -> Path:
    p = Path(__file__).resolve()
    for parent in p.parents:
        if (parent / "app").is_dir() and (parent / "tests").is_dir():
            return parent
    raise RuntimeError("repo root not found")


def test_cost_tracker_has_gemini_pricing() -> None:
    """Onda 4.13: cost_tracker.estimate_cost_usd handles gemini-* models."""
    from app.shared.observability.cost_tracker import estimate_cost_usd, _PRICING_PER_1M

    # Gemini Flash — official Google pricing ~$0.30/1M in, $2.50/1M out
    # (as of 2026-04). Update if Google changes.
    gemini_keys = [k for k in _PRICING_PER_1M if k.startswith("gemini")]
    assert gemini_keys, "Onda 4.13: _PRICING_PER_1M must include gemini-* entries"
    # Specifically the primary model used in chat
    cost = estimate_cost_usd("gemini-2.5-flash", input_tokens=1_000_000, output_tokens=1_000_000)
    assert cost > 0, "gemini-2.5-flash should produce non-zero cost estimate"


def test_llm_service_claude_tool_path_wired() -> None:
    """Onda 4.13: app/domains/ai/services/llm.py _generate_with_tools_claude
    must call record_call after response."""
    text = (_root() / "app/domains/ai/services/llm.py").read_text(encoding="utf-8")
    # Scope: inside _generate_with_tools_claude body
    start = text.find("async def _generate_with_tools_claude(")
    assert start >= 0, "anchor _generate_with_tools_claude not found"
    end = text.find("async def _generate_with_tools_gemini(", start)
    body = text[start:end]
    assert "record_call" in body or "_record_cost" in body, (
        "Onda 4.13: _generate_with_tools_claude must invoke record_call"
    )


def test_llm_service_gemini_tool_path_wired() -> None:
    """Onda 4.13: _generate_with_tools_gemini must call record_call."""
    text = (_root() / "app/domains/ai/services/llm.py").read_text(encoding="utf-8")
    start = text.find("async def _generate_with_tools_gemini(")
    assert start >= 0
    # Find next async def to bound body
    end = text.find("async def ", start + 10)
    body = text[start:end]
    assert "record_call" in body or "_record_cost" in body, (
        "Onda 4.13: _generate_with_tools_gemini must invoke record_call"
    )


def test_llm_claude_provider_tools_path_wired() -> None:
    """Onda 4.13: llm_claude.py generate_with_tools must call _record_cost_call.

    Separate provider-layer path (alternate caller). Wire for parity.
    """
    text = (_root() / "app/shared/providers/llm_claude.py").read_text(encoding="utf-8")
    start = text.find("async def generate_with_tools(")
    assert start >= 0
    # Bound body: to next method OR class end
    end = text.find("\n    async def ", start + 10)
    body = text[start:end] if end > 0 else text[start:]
    assert "_record_cost_call" in body, (
        "Onda 4.13: llm_claude.generate_with_tools must invoke _record_cost_call"
    )


def test_lia_cost_marker_traceable_in_sources() -> None:
    """Onda 4.13: [LIA-COST] marker present in source (producer contract)."""
    tracker = (_root() / "app/shared/observability/cost_tracker.py").read_text(encoding="utf-8")
    assert "[LIA-COST]" in tracker, "cost_tracker must emit [LIA-COST] marker"
