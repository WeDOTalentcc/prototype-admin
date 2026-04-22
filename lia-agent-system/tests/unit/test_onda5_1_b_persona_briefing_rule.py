"""Onda 5.1.b — persona YAML has explicit rule: briefing context is fact,
not a hypothesis to verify via tools.

After 5.1.a wiring lands the briefing in the prompt, the persona must
be told how to treat it. Without this, LLM may still re-query tools
(its trained default) and contradict the briefing.

Canonical-fix (inferencial guide): producer is correct (briefing injected);
consumer (LLM via persona) needs explicit instruction.
"""
from __future__ import annotations

from pathlib import Path

import yaml


def _persona() -> str:
    p = Path(__file__).resolve()
    for parent in p.parents:
        cand = parent / "app/prompts/shared/lia_persona.yaml"
        if cand.exists():
            return yaml.safe_load(cand.read_text(encoding="utf-8"))["prompts"]["lia_persona"]
    raise RuntimeError("lia_persona.yaml not found")


def test_persona_has_briefing_as_fact_rule() -> None:
    """Onda 5.1.b: persona must instruct LIA to treat briefing_context
    (from extra_instructions) as fact, not re-verify."""
    text = _persona()
    # Must reference the specific marker used by IV.B injection
    assert "Contexto pra saudação" in text or "Contexto pra saudacao" in text, (
        "Onda 5.1.b: persona must reference 'Contexto pra saudação' marker "
        "that IV.B uses in extra_instructions"
    )
    # Must include instruction NOT to re-query tools
    low = text.lower()
    assert ("não chame" in low or "nao chame" in low or
            "não verifique" in low or "nao verifique" in low or
            "sem chamar tool" in low), (
        "Onda 5.1.b: persona must explicitly instruct NOT to call tools "
        "to verify briefing context"
    )


def test_persona_marker_onda5_1_b() -> None:
    """Onda 5.1.b: traceability marker present."""
    text = _persona()
    assert "FIX 5.1" in text or "Onda 5.1" in text


def test_persona_yaml_still_parses() -> None:
    """Regression: YAML still valid after edit."""
    p = Path(__file__).resolve()
    for parent in p.parents:
        cand = parent / "app/prompts/shared/lia_persona.yaml"
        if cand.exists():
            data = yaml.safe_load(cand.read_text(encoding="utf-8"))
            assert isinstance(data, dict)
            assert "prompts" in data
            assert "lia_persona" in data["prompts"]
            assert len(data["prompts"]["lia_persona"]) > 1000
            return
    raise RuntimeError("persona not found")
