"""FIX 29 (2026-04-21) — persona rules must be inside rendered prose block.

Empirical smoke test showed FIX 26/27/28 rules (contextual_inference,
greeting_template, proatividade_dados) were added as top-level YAML keys but
_load_persona_base only reads data['prompts']['lia_persona'] → dead YAML.

FIX 29 migrates those rules into the lia_persona content as markdown sections.

This test file asserts:
  - No dead top-level keys remain in lia_persona.yaml
  - The rules' content is present inside prompts.lia_persona text
  - SystemPromptBuilder.build() output includes the rule text (end-to-end)
"""
from __future__ import annotations

from pathlib import Path
import yaml


def _find_file(rel: str) -> Path:
    here = Path(__file__).resolve()
    for parent in here.parents:
        cand = parent / rel
        if cand.exists():
            return cand
    raise RuntimeError(f"{rel} not found")


def test_persona_yaml_has_no_dead_toplevel_rule_keys() -> None:
    """FIX 29: appended top-level keys must be gone (they were never rendered)."""
    data = yaml.safe_load(_find_file("app/prompts/shared/lia_persona.yaml").read_text(encoding="utf-8"))
    forbidden = {"greeting_template", "contextual_inference", "proatividade_dados"}
    present = forbidden & set(data.keys())
    assert not present, (
        f"FIX 29: dead top-level keys must be removed from lia_persona.yaml "
        f"(found: {present}). These keys were ignored by _load_persona_base — "
        f"migrate their content INTO prompts.lia_persona as markdown sections."
    )


def test_recruiter_assistant_yaml_has_no_dead_proatividade_key() -> None:
    """FIX 29: proatividade_dados must be removed from recruiter_assistant.yaml
    (it's migrated into lia_persona where it's actually rendered)."""
    data = yaml.safe_load(
        _find_file("app/prompts/domains/recruiter_assistant.yaml").read_text(encoding="utf-8")
    )
    assert "proatividade_dados" not in data, (
        "FIX 29: top-level proatividade_dados in recruiter_assistant.yaml was "
        "dead YAML. Content is now in lia_persona.yaml prompts.lia_persona."
    )


def test_persona_content_contains_migrated_rules() -> None:
    """FIX 29: the 3 rules' content must be present inside prompts.lia_persona."""
    data = yaml.safe_load(_find_file("app/prompts/shared/lia_persona.yaml").read_text(encoding="utf-8"))
    persona = data["prompts"]["lia_persona"]
    low = persona.lower()

    # Greeting template markers
    assert "saudação" in low or "saudacao" in low, (
        "FIX 29: lia_persona must contain Saudação section migrated from greeting_template"
    )
    assert "como posso ajudar" in low, (
        "FIX 29: greeting anti-pattern must be cited in persona"
    )

    # Contextual inference markers
    assert "inferência contextual" in low or "inferencia contextual" in low, (
        "FIX 29: lia_persona must contain Inferência Contextual section"
    )
    assert "o quê" in low or "o que" in low, (
        "FIX 29: contextual_inference rule must cite 'X o quê?' anti-pattern"
    )

    # Proatividade markers
    assert "proatividade" in low, (
        "FIX 29: lia_persona must contain Proatividade section"
    )
    assert "navegar" in low, (
        "FIX 29: proatividade rule must cite 'navegar para X' anti-pattern"
    )


def test_fix29_marker_present() -> None:
    """FIX 29 audit marker for traceability."""
    data = yaml.safe_load(_find_file("app/prompts/shared/lia_persona.yaml").read_text(encoding="utf-8"))
    persona = data["prompts"]["lia_persona"]
    assert "FIX 29" in persona, (
        "FIX 29: lia_persona content must contain FIX 29 marker documenting migration"
    )


def test_system_prompt_builder_output_includes_migrated_rules_end_to_end() -> None:
    """FIX 29 end-to-end: SystemPromptBuilder.build() must emit the rules.

    This is the critical empirical check — without it, FIX 26/27/28 are
    test-green but runtime-dead (same pattern as FIX 15 → FIX 19 from PARTE L).
    """
    # Clear any cached persona so we read fresh
    from app.shared.prompts.system_prompt_builder import _load_persona_base
    _load_persona_base.cache_clear()

    from app.shared.prompts.system_prompt_builder import SystemPromptBuilder

    prompt = SystemPromptBuilder.build(
        agent_type="orchestrator",
        company_id="co-test",
        user_name="Paulo",
    )

    low = prompt.lower()
    # All 3 rules must be in the final rendered prompt
    assert "saudação" in low or "saudacao" in low, (
        "FIX 29 runtime: greeting_template must appear in build() output"
    )
    assert "inferência contextual" in low or "inferencia contextual" in low, (
        "FIX 29 runtime: contextual_inference must appear in build() output"
    )
    assert "proatividade de dados" in low, (
        "FIX 29 runtime: proatividade_dados must appear in build() output"
    )
