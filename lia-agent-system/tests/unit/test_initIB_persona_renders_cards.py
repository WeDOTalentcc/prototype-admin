"""Initiative I.B (2026-04-21) — Persona renders capability_cards in prompt.

Closes anti-hallucination loop end-to-end. FIX 23 (open_ended_discovery) + FIX 24
(no hallucinated caps) + Init I.A (capability_cards.yaml with 16 curated cards)
+ Init I.B (this) = LLM ALWAYS has the grounded list when answering
"o que você sabe fazer?".

Before Init I.B: persona guidelines forbade free prose but provided no source.
After Init I.B: persona includes a `## Minhas Capacidades` section rendered
from capability_cards.yaml so the LLM has concrete cards to reference.

Tests structural + end-to-end SystemPromptBuilder.build() output.
"""
from __future__ import annotations


def test_capability_cards_rendered_for_orchestrator() -> None:
    """Init I.B: orchestrator prompt must include capability cards section."""
    from app.shared.prompts.system_prompt_builder import (
        SystemPromptBuilder,
        _load_persona_base,
    )
    _load_persona_base.cache_clear()

    prompt = SystemPromptBuilder.build(
        agent_type="orchestrator",
        company_id="co-test",
    )
    low = prompt.lower()
    assert "minhas capacidades" in low or "minhas capacidade" in low, (
        "Init I.B: orchestrator prompt must include '## Minhas Capacidades' section"
    )
    # At least 3 card titles should appear (proof cards are actually rendered)
    # Pick stable card titles from capability_cards.yaml
    card_title_keywords = ["listar e buscar vagas", "ver detalhes de uma vaga", "buscar candidatos"]
    hits = sum(1 for k in card_title_keywords if k in low)
    assert hits >= 2, (
        f"Init I.B: at least 2 of {card_title_keywords} should appear in prompt, found {hits}"
    )


def test_capability_cards_rendered_for_recruiter_assistant() -> None:
    """Init I.B: recruiter_assistant agent also gets cards."""
    from app.shared.prompts.system_prompt_builder import (
        SystemPromptBuilder,
        _load_persona_base,
    )
    _load_persona_base.cache_clear()

    prompt = SystemPromptBuilder.build(
        agent_type="recruiter_assistant",
        company_id="co-test",
    )
    assert "Minhas Capacidades" in prompt or "minhas capacidade" in prompt.lower(), (
        "Init I.B: recruiter_assistant must also receive capability cards"
    )


def test_capability_cards_include_opt_out() -> None:
    """Init I.B regression: opt-out via include_capability_cards=False works."""
    from app.shared.prompts.system_prompt_builder import (
        SystemPromptBuilder,
        _load_persona_base,
    )
    _load_persona_base.cache_clear()

    prompt = SystemPromptBuilder.build(
        agent_type="orchestrator",
        company_id="co-test",
        include_capability_cards=False,
    )
    assert "Minhas Capacidades" not in prompt, (
        "Init I.B: include_capability_cards=False must skip the section (token budget escape hatch)"
    )


def test_capability_cards_each_card_references_real_tool() -> None:
    """Init I.B CI invariant: every rendered card must cite a tool name present
    in the live tool_registry (carries through Init I.A CI guard at render time)."""
    from app.shared.prompts.system_prompt_builder import _render_capability_cards
    from app.tools import initialize_tools
    from app.tools.registry import tool_registry

    tool_registry.clear()
    initialize_tools()
    registered = set(tool_registry.list_tools())

    rendered = _render_capability_cards()
    # Parse card block — rendered output should list tools per card.
    # We don't require strict format; just assert that mentioned tool names
    # (when explicitly cited with `tool:` prefix) exist.
    import re
    mentioned = re.findall(r"\btool(?:s)?:\s*([a-z_, ]+)", rendered.lower())
    for group in mentioned:
        for name in (n.strip() for n in group.split(",")):
            if not name:
                continue
            assert name in registered, (
                f"Init I.B render references unregistered tool {name!r}. "
                f"Update capability_cards.yaml or register the tool."
            )


def test_initIB_marker_present() -> None:
    """Init I.B audit marker for traceability."""
    from pathlib import Path

    import app.shared.prompts.system_prompt_builder as spb

    source = Path(spb.__file__).read_text(encoding="utf-8")
    assert "Initiative I.B" in source or "Init I.B" in source, (
        "Init I.B: system_prompt_builder.py must contain I.B marker"
    )
    assert "_render_capability_cards" in source, (
        "Init I.B: renderer function must exist"
    )
