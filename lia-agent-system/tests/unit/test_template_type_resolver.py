"""
Unit tests for canonical template_type_resolver (Onda 37.3.1).

Harness classification: computational sensor — deterministic mapping.
Coverage: keyword priority, edge cases (empty, None), all 5 template types.
"""
from __future__ import annotations

import pytest

from app.domains.job_creation.services.template_type_resolver import (
    TEMPLATE_DISPLAY,
    TEMPLATE_TYPE_KEYWORDS,
    get_template_metadata,
    suggest_template_type,
)


class TestSuggestTemplateType:
    """Deterministic mapping (job_title, department) -> template_type."""

    def test_technical_engineer_pleno(self):
        assert suggest_template_type("Engenheiro de Software Pleno", "Engenharia") == "technical"

    def test_technical_developer_english(self):
        assert suggest_template_type("Senior Developer", "Engineering") == "technical"

    def test_technical_data_analyst(self):
        assert suggest_template_type("Analista de Dados", "Tecnologia") == "technical"

    def test_executive_diretor(self):
        assert suggest_template_type("Diretor de Marketing", "Marketing") == "executive"

    def test_executive_cto(self):
        assert suggest_template_type("CTO", "Engenharia") == "executive"

    def test_executive_vp(self):
        assert suggest_template_type("VP of Engineering", "Tecnologia") == "executive"

    def test_executive_wins_over_technical(self):
        """'Diretor de Engenharia' matches both — executive priority."""
        assert suggest_template_type("Diretor de Engenharia", "Engenharia") == "executive"

    def test_mass_hiring_atendente(self):
        assert suggest_template_type("Atendente de loja", "Operacional") == "mass_hiring"

    def test_mass_hiring_motorista(self):
        assert suggest_template_type("Motorista de Entrega", "Logística") == "mass_hiring"

    def test_intern_estagiario(self):
        assert suggest_template_type("Estagiário em Marketing", "Marketing") == "intern"

    def test_intern_trainee(self):
        assert suggest_template_type("Trainee de Vendas", "Comercial") == "intern"

    def test_intern_wins_over_executive_priority(self):
        """Order matters: intern checked before executive."""
        assert suggest_template_type("Estagiário Diretor", "X") == "intern"

    def test_operational_analista(self):
        assert suggest_template_type("Analista Financeiro", "Financeiro") == "operational"

    def test_operational_coordenador(self):
        assert suggest_template_type("Coordenador de Marketing", "Marketing") == "operational"

    def test_default_fallback_unknown(self):
        """No keyword matches → fallback 'technical'."""
        assert suggest_template_type("Cargo Estranho", "Departamento Único") == "technical"

    def test_none_inputs(self):
        assert suggest_template_type(None, None) == "technical"

    def test_empty_inputs(self):
        assert suggest_template_type("", "") == "technical"

    def test_partial_none(self):
        assert suggest_template_type("Estagiário", None) == "intern"
        # No keyword matches "engenharia" alone → fallback technical
        assert suggest_template_type(None, "Engenharia") == "technical"

    def test_word_boundary_no_false_positive(self):
        """Coordenador must NOT match 'coo' (executive). Regression Onda 37.3.1."""
        assert suggest_template_type("Coordenador de Marketing", "Marketing") == "operational"
        assert suggest_template_type("Coordenador", "RH") == "operational"

    def test_short_acronym_only_matches_as_word(self):
        """'pm' as a word matches technical, but 'pmx' should not."""
        assert suggest_template_type("PM Sênior", "Produto") == "technical"
        # No match for arbitrary substring
        assert suggest_template_type("Empacotador", "Logística") == "technical"  # no kw matches

    def test_case_insensitive(self):
        assert suggest_template_type("DEVELOPER", "ENGINEERING") == "technical"
        assert suggest_template_type("estágio", "rh") == "intern"


class TestGetTemplateMetadata:
    """Display metadata returned for each template type."""

    @pytest.mark.parametrize("ttype", ["technical", "executive", "operational", "mass_hiring", "intern"])
    def test_all_types_have_display_name_and_description(self, ttype):
        meta = get_template_metadata(ttype)
        assert "display_name" in meta
        assert "description" in meta
        assert meta["display_name"]
        assert meta["description"]

    def test_metadata_for_technical(self):
        meta = get_template_metadata("technical")
        assert meta["display_name"] == "Processo Técnico"
        assert "→" in meta["description"]


class TestKeywordCatalog:
    """Catalog invariants — defensive contract checks."""

    def test_all_5_types_in_keywords(self):
        assert set(TEMPLATE_TYPE_KEYWORDS.keys()) == {
            "technical", "executive", "operational", "mass_hiring", "intern",
        }

    def test_all_keywords_are_lowercase(self):
        """Resolver lowercases input — catalog must already be lowercase."""
        for ttype, keywords in TEMPLATE_TYPE_KEYWORDS.items():
            for kw in keywords:
                assert kw == kw.lower(), f"{ttype}: {kw!r} should be lowercase"

    def test_no_empty_keywords(self):
        for ttype, keywords in TEMPLATE_TYPE_KEYWORDS.items():
            for kw in keywords:
                assert kw.strip(), f"{ttype}: empty keyword found"

    def test_display_metadata_for_all_5_types(self):
        assert set(TEMPLATE_DISPLAY.keys()) == {
            "technical", "executive", "operational", "mass_hiring", "intern",
        }
