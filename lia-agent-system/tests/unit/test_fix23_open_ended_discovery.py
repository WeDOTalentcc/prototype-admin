"""FIX 23 (2026-04-21) — open_ended_discovery in capability_truthfulness.

Closes "o que você sabe fazer?" → free-text hallucinated bullets gap.
Extends FIX 17 guardrail with explicit instructions for open-ended questions.

Structural tests — YAML parses + contains expected guardrail text.
Full enforcement comes from Initiative I (Grounded Capability System).
"""
from __future__ import annotations

from pathlib import Path
import yaml


def _load_guardrails() -> dict:
    here = Path(__file__).resolve()
    for parent in here.parents:
        candidate = parent / "app/prompts/shared/guardrails_block.yaml"
        if candidate.exists():
            return yaml.safe_load(candidate.read_text(encoding="utf-8"))
    raise RuntimeError("guardrails_block.yaml not found")


def test_fix23_marker_in_guardrails() -> None:
    """FIX 23 audit marker in capability_truthfulness block."""
    data = _load_guardrails()
    block = data["universal"]["capability_truthfulness"]
    assert "FIX 23" in block, (
        "FIX 23: capability_truthfulness block must contain FIX 23 marker"
    )


def test_open_ended_discovery_section_exists() -> None:
    """FIX 23: block must include `open_ended_discovery` guidance."""
    data = _load_guardrails()
    block = data["universal"]["capability_truthfulness"]
    assert "open_ended_discovery" in block.lower() or "descoberta aberta" in block.lower(), (
        "FIX 23: capability_truthfulness must include an open_ended_discovery "
        "section covering 'o que você sabe fazer?' style queries"
    )


def test_open_ended_section_forbids_free_prose() -> None:
    """FIX 23: guidance must explicitly forbid free-text bullets."""
    data = _load_guardrails()
    block = data["universal"]["capability_truthfulness"]
    # Must mention NOT generating free-text lists
    low = block.lower()
    assert "não gerar lista livre" in low or "não gere lista livre" in low or "no free" in low, (
        "FIX 23: open_ended_discovery must forbid free-text bullet lists"
    )
    # Must explicitly call out predictive hallucination
    assert "prevejo" in low or "forecast" in low or "preditiva" in low, (
        "FIX 23: must explicitly call out 'prevejo' / predictive as anti-pattern "
        "(this was the exact hallucination in the chat audit)"
    )


def test_guardrails_yaml_parses_cleanly() -> None:
    """FIX 23 regression: YAML must still parse after edits."""
    data = _load_guardrails()
    assert isinstance(data, dict)
    assert "universal" in data
    assert "capability_truthfulness" in data["universal"]
