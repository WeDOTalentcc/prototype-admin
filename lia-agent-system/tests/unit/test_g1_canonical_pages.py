"""G1 canonical contract — page_type vocabulary single source of truth.

Tests:
1. CanonicalPage covers all dashboard routes (no orphan FE routes).
2. PAGE_DESCRIPTIONS_PT_BR has an entry for every CanonicalPage (except GENERAL).
3. Legacy aliases (settings_config, candidates, kanban, ...) normalize correctly.
4. normalize_page("") and normalize_page(None) return GENERAL safely.
5. describe_page(GENERAL) returns None (skip "Localização" section).
6. system_prompt_builder.build() includes "Localização" section for canonical
   page values that were previously falling to "general" (configuracoes,
   funil_talentos, recrutar, agent_studio).
"""
from __future__ import annotations

import pytest

from app.shared.canonical_pages import (
    CanonicalPage,
    PAGE_DESCRIPTIONS_PT_BR,
    LEGACY_PAGE_ALIASES,
    normalize_page,
    describe_page,
)
from app.shared.prompts.system_prompt_builder import SystemPromptBuilder


class TestCanonicalPageEnum:
    def test_general_value_exists(self):
        assert CanonicalPage.GENERAL == "general"

    def test_pt_br_routes_have_canonical_values(self):
        """All main dashboard routes must have a canonical CanonicalPage."""
        required_pages = {
            "vagas", "vaga_detalhe", "recrutar", "funil_talentos",
            "candidato_detalhe", "configuracoes", "agent_studio",
            "dashboard", "tasks", "biblioteca",
        }
        all_values = {p.value for p in CanonicalPage}
        missing = required_pages - all_values
        assert not missing, (
            f"CanonicalPage missing required dashboard pages: {missing}. "
            f"Add them to app/shared/canonical_pages.py + mirror in TS."
        )

    def test_every_page_has_description_except_general(self):
        """Coverage invariant — every CanonicalPage (except GENERAL) has a description."""
        missing = []
        for page in CanonicalPage:
            if page == CanonicalPage.GENERAL:
                continue  # GENERAL intentionally has a "skip-this" desc
            if page not in PAGE_DESCRIPTIONS_PT_BR:
                missing.append(page.value)
        assert not missing, (
            f"PAGE_DESCRIPTIONS_PT_BR missing entries for: {missing}"
        )


class TestNormalizePage:
    @pytest.mark.parametrize("raw,expected", [
        # Canonical values (passthrough)
        ("vagas", CanonicalPage.VAGAS),
        ("configuracoes", CanonicalPage.CONFIGURACOES),
        ("funil_talentos", CanonicalPage.FUNIL_TALENTOS),
        ("agent_studio", CanonicalPage.AGENT_STUDIO),
        # Legacy aliases
        ("kanban", CanonicalPage.PIPELINE_KANBAN),
        ("candidates", CanonicalPage.CANDIDATO_DETALHE),
        ("settings_config", CanonicalPage.CONFIGURACOES),
        ("job_detail", CanonicalPage.VAGA_DETALHE),
        ("sourcing", CanonicalPage.FUNIL_TALENTOS),
        ("vacancies", CanonicalPage.VAGAS),
        ("wizard", CanonicalPage.RECRUTAR),
        # Edge cases
        ("", CanonicalPage.GENERAL),
        (None, CanonicalPage.GENERAL),
        ("totally-unknown-page", CanonicalPage.GENERAL),
        # Case insensitive
        ("CONFIGURACOES", CanonicalPage.CONFIGURACOES),
        ("  vagas  ", CanonicalPage.VAGAS),  # whitespace
    ])
    def test_normalize(self, raw, expected):
        assert normalize_page(raw) == expected


class TestDescribePage:
    def test_general_returns_none(self):
        """GENERAL → None means: skip Localização section in system prompt."""
        assert describe_page(CanonicalPage.GENERAL) is None
        assert describe_page("general") is None
        assert describe_page(None) is None
        assert describe_page("") is None

    def test_canonical_value_returns_description(self):
        desc = describe_page(CanonicalPage.CONFIGURACOES)
        assert desc is not None
        assert "Configurações" in desc

    def test_legacy_alias_returns_description(self):
        """Legacy strings still resolve to descriptions."""
        desc = describe_page("settings_config")
        assert desc is not None
        assert "Configurações" in desc


class TestSystemPromptBuilderIntegration:
    """SystemPromptBuilder.build() must inject Localização section for
    canonical pages, including the new PT-BR ones that previously fell
    to 'general' (configuracoes, funil_talentos, recrutar, etc.)."""

    @pytest.mark.parametrize("page,expected_substring", [
        ("configuracoes", "Configurações"),
        ("funil_talentos", "Funil de Talentos"),
        ("recrutar", "wizard"),
        ("agent_studio", "Agent Studio"),
        ("tasks", "Tarefas"),
        # Legacy aliases also work (compatibility)
        ("settings_config", "Configurações"),
        ("kanban", "Kanban"),
    ])
    def test_build_includes_localizacao_for_page(self, page, expected_substring):
        prompt = SystemPromptBuilder.build(
            agent_type="orchestrator",
            context_page=page,
        )
        assert "### Localização" in prompt, (
            f"Localização section missing for page={page!r}. "
            f"This means LIA does not know where the user is — "
            f"causing 'não recebi contexto de página' behavior."
        )
        assert expected_substring.lower() in prompt.lower(), (
            f"Expected '{expected_substring}' in Localização for page={page!r}"
        )

    def test_build_skips_localizacao_for_general(self):
        """GENERAL page should NOT emit a Localização section — would be noise."""
        prompt = SystemPromptBuilder.build(
            agent_type="orchestrator",
            context_page="general",
        )
        assert "### Localização" not in prompt, (
            "Localização section should be skipped for context_page='general' "
            "— adds noise without information."
        )

    def test_build_skips_localizacao_for_unknown(self):
        prompt = SystemPromptBuilder.build(
            agent_type="orchestrator",
            context_page="totally-unknown",
        )
        assert "### Localização" not in prompt
