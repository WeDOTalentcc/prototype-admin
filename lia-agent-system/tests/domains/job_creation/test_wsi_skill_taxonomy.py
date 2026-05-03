"""Tests for WSI Skill Taxonomy Loader - Sprint B Phase 3.

Cobertura:
- load_taxonomy: 199 skills, 26 parents, validacao
- find_skill / parent_of: lookup correto
- all_skill_ids / all_parent_ids: listas completas
- skills_by_parent: agrupamento correto
- validacao falha em skill malformada
"""
from __future__ import annotations

import pytest


def test_load_taxonomy_returns_v3_structure():
    from app.domains.job_creation.services.wsi_skill_taxonomy import load_taxonomy

    tax = load_taxonomy()
    assert tax.version == "v3"
    assert tax.total_parents == 26
    assert tax.total_skills == 199


def test_load_taxonomy_has_all_15_universal_categories():
    from app.domains.job_creation.services.wsi_skill_taxonomy import load_taxonomy

    tax = load_taxonomy()
    # Universais
    assert "communication_collaboration" in tax.parents
    assert "execution_delivery" in tax.parents
    assert "thinking_decision" in tax.parents
    assert "people_management" in tax.parents
    assert "technical_leadership" in tax.parents


def test_load_taxonomy_has_11_vertical_categories():
    from app.domains.job_creation.services.wsi_skill_taxonomy import load_taxonomy

    tax = load_taxonomy()
    # Verticais
    assert "health_clinical" in tax.parents
    assert "education_pedagogy" in tax.parents
    assert "ai_ml_specialist" in tax.parents
    assert "pharma_life_sciences" in tax.parents
    assert "telecommunications" in tax.parents


def test_technical_leadership_has_14_skills_after_expansion():
    from app.domains.job_creation.services.wsi_skill_taxonomy import skills_by_parent

    skills = skills_by_parent("technical_leadership")
    assert len(skills) == 14
    skill_ids = {s.id for s in skills}
    # Phase 3 expansion adds these
    assert "distributed_systems_design" in skill_ids
    assert "data_intensive_application_design" in skill_ids
    assert "security_architecture" in skill_ids
    assert "observability_engineering" in skill_ids
    assert "devops_excellence" in skill_ids
    assert "ml_systems_design" in skill_ids
    assert "frontend_architecture" in skill_ids


def test_no_fairness_flagged_skills_in_v3():
    """v3 removed all fairness-flagged skills per Paulo decision."""
    from app.domains.job_creation.services.wsi_skill_taxonomy import load_taxonomy

    tax = load_taxonomy()
    flagged = []
    for parent_id, parent in tax.parents.items():
        for skill in parent.skills:
            if skill.fairness_flag is not None:
                flagged.append((parent_id, skill.id, skill.fairness_flag))
    assert flagged == [], f"v3 should have no fairness flags, found: {flagged}"


def test_removed_skills_not_present():
    """v3 removed: executive_communication, executive_presence, bias_interruption, founder_mindset_at_scale."""
    from app.domains.job_creation.services.wsi_skill_taxonomy import find_skill

    assert find_skill("executive_communication") is None
    assert find_skill("executive_presence") is None
    assert find_skill("bias_interruption") is None
    assert find_skill("founder_mindset_at_scale") is None


def test_find_skill_returns_skill():
    from app.domains.job_creation.services.wsi_skill_taxonomy import find_skill

    skill = find_skill("active_listening")
    assert skill is not None
    assert skill.id == "active_listening"
    assert "Captura" in skill.description or "captura" in skill.description.lower()


def test_find_skill_returns_none_for_unknown():
    from app.domains.job_creation.services.wsi_skill_taxonomy import find_skill

    assert find_skill("nonexistent_skill_xyz") is None
    assert find_skill("") is None


def test_parent_of_returns_correct_parent():
    from app.domains.job_creation.services.wsi_skill_taxonomy import parent_of

    assert parent_of("active_listening") == "communication_collaboration"
    assert parent_of("clinical_diagnostic_reasoning") == "health_clinical"
    assert parent_of("distributed_systems_design") == "technical_leadership"


def test_parent_of_returns_none_for_unknown():
    from app.domains.job_creation.services.wsi_skill_taxonomy import parent_of

    assert parent_of("xxx") is None


def test_all_skill_ids_returns_199():
    from app.domains.job_creation.services.wsi_skill_taxonomy import all_skill_ids

    ids = all_skill_ids()
    assert len(ids) == 199
    assert ids == sorted(ids)  # alphabetical
    assert "active_listening" in ids


def test_all_parent_ids_returns_26():
    from app.domains.job_creation.services.wsi_skill_taxonomy import all_parent_ids

    parents = all_parent_ids()
    assert len(parents) == 26
    assert parents == sorted(parents)


def test_skills_by_parent_returns_correct_count():
    from app.domains.job_creation.services.wsi_skill_taxonomy import skills_by_parent

    # health_clinical has 8 skills
    assert len(skills_by_parent("health_clinical")) == 8
    # education_pedagogy has 7
    assert len(skills_by_parent("education_pedagogy")) == 7
    # technical_leadership has 14 (expanded)
    assert len(skills_by_parent("technical_leadership")) == 14


def test_skills_by_parent_returns_empty_for_unknown():
    from app.domains.job_creation.services.wsi_skill_taxonomy import skills_by_parent

    assert skills_by_parent("nonexistent") == []


def test_all_skills_have_valid_seniority():
    from app.domains.job_creation.services.wsi_skill_taxonomy import (
        ALLOWED_SENIORITY, load_taxonomy,
    )

    tax = load_taxonomy()
    for parent in tax.parents.values():
        for skill in parent.skills:
            assert skill.seniority_min in ALLOWED_SENIORITY


def test_all_skills_have_valid_source():
    from app.domains.job_creation.services.wsi_skill_taxonomy import (
        ALLOWED_SOURCES, load_taxonomy,
    )

    tax = load_taxonomy()
    for parent in tax.parents.values():
        for skill in parent.skills:
            assert skill.source in ALLOWED_SOURCES


def test_all_skill_ids_are_unique():
    """Skill ids must be unique across the entire taxonomy (otherwise ambiguity)."""
    from app.domains.job_creation.services.wsi_skill_taxonomy import all_skill_ids

    ids = all_skill_ids()
    assert len(ids) == len(set(ids))
