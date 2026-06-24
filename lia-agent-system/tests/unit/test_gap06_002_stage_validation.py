"""GAP-06-002: Per-stage required field validation for job vacancies.

TDD tests for app.shared.vacancy_stage_validation.
"""

import pytest
from types import SimpleNamespace

from app.shared.vacancy_stage_validation import (
    STAGE_REQUIRED_FIELDS,
    validate_stage_requirements,
    get_stage_requirements,
)


def _make_vacancy(**kwargs):
    """Create a minimal vacancy-like object with sensible defaults."""
    defaults = {
        "title": "Engenheiro de Software",
        "description": "Desenvolver aplicações web com Python e React.",
        "department": "Tecnologia",
        "employment_type": "CLT",
        "work_model": "remoto",
        "seniority_level": "Pleno",
    }
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


# --- Stage: rascunho ---

class TestRascunho:
    def test_rascunho_only_needs_title(self):
        vacancy = _make_vacancy(description=None, department=None, employment_type=None)
        missing = validate_stage_requirements(vacancy, "rascunho")
        assert missing == []

    def test_rascunho_fails_without_title(self):
        vacancy = _make_vacancy(title=None)
        missing = validate_stage_requirements(vacancy, "rascunho")
        assert "title" in missing

    def test_rascunho_empty_string_title_is_missing(self):
        vacancy = _make_vacancy(title="   ")
        missing = validate_stage_requirements(vacancy, "rascunho")
        assert "title" in missing


# --- Stage: enriquecida ---

class TestEnriquecida:
    def test_enriquecida_needs_title_and_description(self):
        vacancy = _make_vacancy()
        missing = validate_stage_requirements(vacancy, "enriquecida")
        assert missing == []

    def test_enriquecida_missing_description(self):
        vacancy = _make_vacancy(description=None)
        missing = validate_stage_requirements(vacancy, "enriquecida")
        assert "description" in missing
        assert "title" not in missing

    def test_enriquecida_missing_both(self):
        vacancy = _make_vacancy(title="", description="")
        missing = validate_stage_requirements(vacancy, "enriquecida")
        assert "title" in missing
        assert "description" in missing


# --- Stage: aguardando_aprovacao ---

class TestAguardandoAprovacao:
    def test_aguardando_aprovacao_needs_department(self):
        vacancy = _make_vacancy()
        missing = validate_stage_requirements(vacancy, "aguardando_aprovacao")
        assert missing == []

    def test_aguardando_aprovacao_missing_department(self):
        vacancy = _make_vacancy(department=None)
        missing = validate_stage_requirements(vacancy, "aguardando_aprovacao")
        assert "department" in missing


# --- Stage: publicada ---

class TestPublicada:
    def test_publicada_needs_all_fields(self):
        vacancy = _make_vacancy()
        missing = validate_stage_requirements(vacancy, "publicada")
        assert missing == []

    def test_publicada_missing_employment_type(self):
        vacancy = _make_vacancy(employment_type=None)
        missing = validate_stage_requirements(vacancy, "publicada")
        assert "employment_type" in missing

    def test_publicada_missing_multiple(self):
        vacancy = _make_vacancy(department=None, employment_type="")
        missing = validate_stage_requirements(vacancy, "publicada")
        assert "department" in missing
        assert "employment_type" in missing


# --- Status mapping (Ativa → publicada rules) ---

class TestStatusMapping:
    def test_ativa_maps_to_publicada_rules(self):
        vacancy = _make_vacancy()
        missing = validate_stage_requirements(vacancy, "Ativa")
        assert missing == []

    def test_ativa_catches_missing_fields(self):
        vacancy = _make_vacancy(employment_type=None)
        missing = validate_stage_requirements(vacancy, "Ativa")
        assert "employment_type" in missing


# --- Edge cases ---

class TestEdgeCases:
    def test_unknown_stage_allows_transition(self):
        vacancy = _make_vacancy(title=None, description=None)
        missing = validate_stage_requirements(vacancy, "nonexistent_stage")
        assert missing == []

    def test_empty_string_counts_as_missing(self):
        vacancy = _make_vacancy(title="", description="  ")
        missing = validate_stage_requirements(vacancy, "enriquecida")
        assert "title" in missing
        assert "description" in missing

    def test_missing_attribute_counts_as_missing(self):
        """Object without the attribute at all should be treated as missing."""
        vacancy = SimpleNamespace(title="Test")  # no description attr
        missing = validate_stage_requirements(vacancy, "enriquecida")
        assert "description" in missing

    def test_get_stage_requirements_returns_list(self):
        reqs = get_stage_requirements("publicada")
        assert isinstance(reqs, list)
        assert "title" in reqs
        assert "description" in reqs

    def test_get_stage_requirements_unknown_returns_empty(self):
        reqs = get_stage_requirements("nonexistent")
        assert reqs == []

    def test_stages_are_progressive(self):
        """Each later stage requires at least as many fields as the previous."""
        ordered_stages = [
            "rascunho", "enriquecida", "wsi_config",
            "aguardando_aprovacao", "publicada",
        ]
        for i in range(1, len(ordered_stages)):
            prev_fields = set(STAGE_REQUIRED_FIELDS[ordered_stages[i - 1]])
            curr_fields = set(STAGE_REQUIRED_FIELDS[ordered_stages[i]])
            assert prev_fields <= curr_fields, (
                f"Stage {ordered_stages[i]} should require at least all fields "
                f"from {ordered_stages[i-1]}. Missing: {prev_fields - curr_fields}"
            )
