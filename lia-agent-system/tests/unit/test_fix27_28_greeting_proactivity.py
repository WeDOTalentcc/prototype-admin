"""FIX 27 + 28 (2026-04-21) — Greeting template + proatividade_dados rule.

Closes two chat gaps:
  FIX 27: 'oi' → 'Olá! Como posso ajudar?' (generic, no LIA branding, no context)
  FIX 28: 'na tela gestão de vagas' → LIA suggests user navigates instead of fetching

Both are prompt-level fixes:
  - FIX 27: add greeting_template guidance in lia_persona.yaml referencing
    existing SystemPromptBuilder context variables (vagas_abertas, etc).
  - FIX 28: add proatividade_dados rule in recruiter_assistant.yaml forbidding
    'você gostaria de navegar para X' pattern.

Structural tests — YAML contains expected markers.
"""
from __future__ import annotations

from pathlib import Path


def _find_file(rel: str) -> Path:
    here = Path(__file__).resolve()
    for parent in here.parents:
        candidate = parent / rel
        if candidate.exists():
            return candidate
    raise RuntimeError(f"{rel} not found")


def test_fix27_greeting_template_in_persona() -> None:
    """FIX 27: lia_persona.yaml must include a greeting template section."""
    text = _find_file("app/prompts/shared/lia_persona.yaml").read_text(encoding="utf-8")
    low = text.lower()
    assert "fix 27" in low, "FIX 27: lia_persona.yaml must contain FIX 27 marker"
    # Must reference the dynamic context variables the builder exposes
    assert "greeting_template" in low or "saudação" in low or "saudacao" in low, (
        "FIX 27: persona must define a greeting template section"
    )
    # Must guide LIA to open with LIA branding + a concrete hook
    assert "sou a lia" in low and "vagas" in low, (
        "FIX 27: greeting template must include LIA branding + vagas context hook"
    )


def test_fix27_greeting_forbids_generic_opener() -> None:
    """FIX 27: persona must explicitly call out generic 'Olá! Como posso ajudar?' as anti-pattern."""
    text = _find_file("app/prompts/shared/lia_persona.yaml").read_text(encoding="utf-8")
    low = text.lower()
    # Must explicitly forbid generic opener
    assert "como posso ajudar" in low, (
        "FIX 27: persona must mention 'Como posso ajudar?' anti-pattern (generic opener)"
    )


def test_fix28_proatividade_dados_rule_in_recruiter_assistant() -> None:
    """FIX 28: recruiter_assistant.yaml must include proatividade_dados rule."""
    text = _find_file("app/prompts/domains/recruiter_assistant.yaml").read_text(encoding="utf-8")
    low = text.lower()
    assert "fix 28" in low, "FIX 28: recruiter_assistant.yaml must contain FIX 28 marker"
    assert "proatividade_dados" in low or "proatividade de dados" in low, (
        "FIX 28: must define proatividade_dados rule"
    )
    # Must explicitly forbid the "navegar para X" pattern
    assert "navegar" in low and ("nunca" in low or "não" in low or "nao" in low), (
        "FIX 28: proatividade_dados must explicitly forbid 'você gostaria de navegar para X' pattern"
    )


def test_persona_and_assistant_yamls_still_parse() -> None:
    """FIX 27/28 regression: YAML must still parse."""
    import yaml

    for rel in ("app/prompts/shared/lia_persona.yaml", "app/prompts/domains/recruiter_assistant.yaml"):
        data = yaml.safe_load(_find_file(rel).read_text(encoding="utf-8"))
        assert isinstance(data, dict)
