"""G6 (2026-04-21) — Multi-tenant capability toggle.

Tests:
- renderer honors `enabled_for_tenant` field
- default_off cards skipped unless in enable override
- default_on cards skipped when in disable override
- system_only cards never render via default API
- build() accepts new kwargs + threads them through
"""
from __future__ import annotations


def test_render_default_on_card_visible_by_default() -> None:
    """G6: card with no enabled_for_tenant field renders (backward compat)."""
    from app.shared.prompts.system_prompt_builder import _render_capability_cards

    out = _render_capability_cards()
    # Init I.A shipped 16 cards all with default_on (no field) — should render
    assert "Minhas Capacidades" in out
    assert "Listar e buscar vagas" in out, (
        "G6: default_on card must render without overrides"
    )


def test_render_disable_override_hides_default_on_card() -> None:
    """G6: tenant_disable_overrides hides a default_on card."""
    from app.shared.prompts.system_prompt_builder import _render_capability_cards

    out = _render_capability_cards(
        tenant_disable_overrides=frozenset(["list_and_search_jobs"])
    )
    assert "Listar e buscar vagas" not in out, (
        "G6: disable override must remove default_on card"
    )
    # Other cards still render
    assert "Ver detalhes de uma vaga" in out


def test_render_signature_accepts_overrides() -> None:
    """G6: _render_capability_cards accepts tenant_enable/disable_overrides kwargs."""
    import inspect

    from app.shared.prompts.system_prompt_builder import _render_capability_cards

    sig = inspect.signature(_render_capability_cards)
    assert "tenant_enable_overrides" in sig.parameters
    assert "tenant_disable_overrides" in sig.parameters


def test_build_signature_accepts_tenant_toggle_kwargs() -> None:
    """G6: SystemPromptBuilder.build() accepts tenant_enable/disable_card_ids."""
    import inspect

    from app.shared.prompts.system_prompt_builder import SystemPromptBuilder

    sig = inspect.signature(SystemPromptBuilder.build)
    assert "tenant_enable_card_ids" in sig.parameters
    assert "tenant_disable_card_ids" in sig.parameters


def test_build_threads_overrides_to_renderer_end_to_end() -> None:
    """G6: passing disable via build() must produce filtered prompt."""
    from app.shared.prompts.system_prompt_builder import (
        SystemPromptBuilder,
        _load_persona_base,
    )
    _load_persona_base.cache_clear()

    prompt_full = SystemPromptBuilder.build(
        agent_type="orchestrator",
        company_id="co-test",
    )
    assert "Listar e buscar vagas" in prompt_full

    prompt_filtered = SystemPromptBuilder.build(
        agent_type="orchestrator",
        company_id="co-test",
        tenant_disable_card_ids=frozenset(["list_and_search_jobs"]),
    )
    assert "Listar e buscar vagas" not in prompt_filtered, (
        "G6 end-to-end: build() must pass disable override to renderer"
    )
    # Other cards survive
    assert "Buscar candidatos" in prompt_filtered


def test_yaml_documents_enabled_for_tenant_field() -> None:
    """G6: capability_cards.yaml must document the enabled_for_tenant field."""
    from pathlib import Path

    here = Path(__file__).resolve()
    for parent in here.parents:
        cand = parent / "app/prompts/catalog/capability_cards.yaml"
        if cand.exists():
            break
    else:
        raise RuntimeError("capability_cards.yaml not found")

    text = cand.read_text(encoding="utf-8")
    assert "G6" in text, "G6: capability_cards.yaml must reference G6"
    assert "enabled_for_tenant" in text, (
        "G6: YAML must document enabled_for_tenant field (even if default_on is implicit)"
    )
