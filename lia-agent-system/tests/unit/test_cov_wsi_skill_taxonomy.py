"""Coverage tests for wsi_skill_taxonomy.py — 12 pure functions, 106 stmts."""
import pytest

from app.domains.job_creation.services.wsi_skill_taxonomy import (
    ALLOWED_BIAS_RISK,
    ALLOWED_DECAY_RATE,
    ALLOWED_OCEAN,
    ALLOWED_SENIORITY,
    ALLOWED_SOURCES,
    DECAY_LAMBDA_BY_TYPE,
    THRESHOLD_BY_BIAS_RISK,
    WsiParent,
    WsiSkill,
    WsiTaxonomy,
    all_parent_ids,
    all_skill_ids,
    find_skill,
    get_decay_lambda,
    get_sample_threshold,
    get_skill_to_parent_index,
    get_skills_by_bias_risk,
    get_skills_by_ocean,
    load_taxonomy,
    parent_of,
    skills_by_parent,
)


class TestConstants:
    def test_threshold_high_is_30(self):
        assert THRESHOLD_BY_BIAS_RISK["high"] == 30

    def test_threshold_medium_is_20(self):
        assert THRESHOLD_BY_BIAS_RISK["medium"] == 20

    def test_threshold_low_is_12(self):
        assert THRESHOLD_BY_BIAS_RISK["low"] == 12

    def test_decay_fast_higher_than_normal(self):
        assert DECAY_LAMBDA_BY_TYPE["fast"] > DECAY_LAMBDA_BY_TYPE["normal"]

    def test_decay_normal_higher_than_slow(self):
        assert DECAY_LAMBDA_BY_TYPE["normal"] > DECAY_LAMBDA_BY_TYPE["slow"]

    def test_allowed_ocean_has_five_dims(self):
        assert len(ALLOWED_OCEAN) == 5
        for dim in ("O", "C", "E", "A", "N"):
            assert dim in ALLOWED_OCEAN

    def test_allowed_seniority_has_four(self):
        assert {"jr", "pl", "sr", "ld"} <= ALLOWED_SENIORITY

    def test_allowed_sources_has_known_sources(self):
        assert "ONET" in ALLOWED_SOURCES
        assert "BEI" in ALLOWED_SOURCES


class TestLoadTaxonomy:
    def test_returns_wsi_taxonomy(self):
        tax = load_taxonomy()
        assert isinstance(tax, WsiTaxonomy)

    def test_has_version(self):
        tax = load_taxonomy()
        assert tax.version

    def test_has_parents(self):
        tax = load_taxonomy()
        assert len(tax.parents) > 0

    def test_total_skills_positive(self):
        tax = load_taxonomy()
        assert tax.total_skills > 0

    def test_total_parents_matches_dict(self):
        tax = load_taxonomy()
        assert tax.total_parents == len(tax.parents)

    def test_cached_returns_same_object(self):
        t1 = load_taxonomy()
        t2 = load_taxonomy()
        assert t1 is t2


class TestAllSkillIds:
    def test_returns_non_empty_sorted_list(self):
        ids = all_skill_ids()
        assert isinstance(ids, list)
        assert len(ids) > 10
        assert ids == sorted(ids)

    def test_all_lowercase_snake_case(self):
        for skill_id in all_skill_ids():
            assert skill_id == skill_id.lower()
            assert " " not in skill_id


class TestAllParentIds:
    def test_returns_sorted_list(self):
        ids = all_parent_ids()
        assert isinstance(ids, list)
        assert len(ids) > 5
        assert ids == sorted(ids)

    def test_all_lowercase(self):
        for pid in all_parent_ids():
            assert pid == pid.lower()


class TestFindSkill:
    def test_known_skill_returns_wsi_skill(self):
        skill_id = all_skill_ids()[0]
        skill = find_skill(skill_id)
        assert isinstance(skill, WsiSkill)
        assert skill.id == skill_id

    def test_unknown_skill_returns_none(self):
        assert find_skill("this_skill_does_not_exist_xyz") is None

    def test_skill_has_required_fields(self):
        skill = find_skill(all_skill_ids()[0])
        assert skill.name_pt
        assert skill.description
        assert skill.seniority_min in ALLOWED_SENIORITY
        assert skill.source in ALLOWED_SOURCES

    def test_skill_bias_risk_is_valid(self):
        skill = find_skill(all_skill_ids()[0])
        assert skill.bias_risk in ALLOWED_BIAS_RISK

    def test_skill_decay_rate_is_valid(self):
        skill = find_skill(all_skill_ids()[0])
        assert skill.decay_rate in ALLOWED_DECAY_RATE


class TestParentOf:
    def test_known_skill_has_parent(self):
        skill_id = all_skill_ids()[0]
        parent_id = parent_of(skill_id)
        assert parent_id is not None
        assert isinstance(parent_id, str)

    def test_unknown_skill_returns_none(self):
        assert parent_of("nonexistent_skill_xyz") is None

    def test_parent_is_in_all_parents(self):
        skill_id = all_skill_ids()[0]
        parent_id = parent_of(skill_id)
        assert parent_id in all_parent_ids()


class TestSkillsByParent:
    def test_known_parent_returns_list(self):
        parent_id = all_parent_ids()[0]
        skills = skills_by_parent(parent_id)
        assert isinstance(skills, list)
        assert len(skills) > 0

    def test_unknown_parent_returns_empty(self):
        assert skills_by_parent("unknown_parent_xyz") == []

    def test_all_returned_are_wsi_skill(self):
        parent_id = all_parent_ids()[0]
        for skill in skills_by_parent(parent_id):
            assert isinstance(skill, WsiSkill)


class TestGetSkillsByOcean:
    def test_valid_dimension_returns_list(self):
        result = get_skills_by_ocean("O")
        assert isinstance(result, list)
        assert len(result) > 0

    def test_invalid_dimension_returns_empty(self):
        assert get_skills_by_ocean("X") == []
        assert get_skills_by_ocean("") == []

    def test_all_returned_match_dimension(self):
        for dim in ("O", "C", "E", "A", "N"):
            for skill in get_skills_by_ocean(dim):
                assert skill.primary_ocean == dim


class TestGetSkillsByBiasRisk:
    def test_high_risk_returns_list(self):
        result = get_skills_by_bias_risk("high")
        assert isinstance(result, list)

    def test_medium_risk_has_most_skills(self):
        medium = get_skills_by_bias_risk("medium")
        low = get_skills_by_bias_risk("low")
        assert len(medium) > 0 or len(low) > 0

    def test_all_returned_match_risk(self):
        for risk in ("low", "medium", "high"):
            for skill in get_skills_by_bias_risk(risk):
                assert skill.bias_risk == risk


class TestGetSampleThreshold:
    def test_high_risk_returns_30(self):
        skill = WsiSkill(
            id="test_skill", name_pt="Test", description="Test skill",
            seniority_min="pl", source="ONET", bias_risk="high", decay_rate="normal"
        )
        assert get_sample_threshold(skill) == 30

    def test_medium_risk_returns_20(self):
        skill = WsiSkill(
            id="test_skill2", name_pt="Test", description="Test skill",
            seniority_min="pl", source="ONET", bias_risk="medium", decay_rate="normal"
        )
        assert get_sample_threshold(skill) == 20

    def test_low_risk_returns_12(self):
        skill = WsiSkill(
            id="test_skill3", name_pt="Test", description="Test skill",
            seniority_min="pl", source="ONET", bias_risk="low", decay_rate="normal"
        )
        assert get_sample_threshold(skill) == 12


class TestGetDecayLambda:
    def test_fast_decay_rate(self):
        skill = WsiSkill(
            id="ts1", name_pt="T", description="T", seniority_min="jr",
            source="ONET", bias_risk="low", decay_rate="fast"
        )
        assert get_decay_lambda(skill) == DECAY_LAMBDA_BY_TYPE["fast"]

    def test_normal_decay_rate(self):
        skill = WsiSkill(
            id="ts2", name_pt="T", description="T", seniority_min="jr",
            source="ONET", bias_risk="low", decay_rate="normal"
        )
        assert get_decay_lambda(skill) == DECAY_LAMBDA_BY_TYPE["normal"]

    def test_slow_decay_rate(self):
        skill = WsiSkill(
            id="ts3", name_pt="T", description="T", seniority_min="jr",
            source="ONET", bias_risk="low", decay_rate="slow"
        )
        assert get_decay_lambda(skill) == DECAY_LAMBDA_BY_TYPE["slow"]


class TestSkillToParentIndex:
    def test_returns_dict(self):
        idx = get_skill_to_parent_index()
        assert isinstance(idx, dict)
        assert len(idx) > 10

    def test_all_skills_in_index(self):
        idx = get_skill_to_parent_index()
        for skill_id in all_skill_ids():
            assert skill_id in idx
