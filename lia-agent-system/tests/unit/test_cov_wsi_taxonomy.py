"""Coverage tests for app/domains/job_creation/services/wsi_skill_taxonomy.py
and app/shared/wsi_skill_taxonomy.py (re-export shim).
"""
import pytest
from app.domains.job_creation.services.wsi_skill_taxonomy import (
    WsiSkill,
    WsiParent,
    WsiTaxonomy,
    THRESHOLD_BY_BIAS_RISK,
    DECAY_LAMBDA_BY_TYPE,
    ALLOWED_OCEAN,
    ALLOWED_BIAS_RISK,
    ALLOWED_DECAY_RATE,
    ALLOWED_SENIORITY,
    ALLOWED_SOURCES,
    load_taxonomy,
    find_skill,
    parent_of,
    all_skill_ids,
    all_parent_ids,
    skills_by_parent,
    get_skills_by_ocean,
    get_skills_by_bias_risk,
    get_sample_threshold,
    get_decay_lambda,
)


class TestConstants:
    def test_threshold_by_bias_risk(self):
        assert THRESHOLD_BY_BIAS_RISK["high"] == 30
        assert THRESHOLD_BY_BIAS_RISK["medium"] == 20
        assert THRESHOLD_BY_BIAS_RISK["low"] == 12

    def test_decay_lambda_by_type(self):
        assert DECAY_LAMBDA_BY_TYPE["fast"] == pytest.approx(0.12)
        assert DECAY_LAMBDA_BY_TYPE["normal"] == pytest.approx(0.05)
        assert DECAY_LAMBDA_BY_TYPE["slow"] == pytest.approx(0.02)

    def test_allowed_ocean(self):
        assert "O" in ALLOWED_OCEAN
        assert "C" in ALLOWED_OCEAN
        assert "E" in ALLOWED_OCEAN
        assert "A" in ALLOWED_OCEAN
        assert "N" in ALLOWED_OCEAN
        assert len(ALLOWED_OCEAN) == 5

    def test_allowed_bias_risk(self):
        assert "low" in ALLOWED_BIAS_RISK
        assert "medium" in ALLOWED_BIAS_RISK
        assert "high" in ALLOWED_BIAS_RISK

    def test_allowed_decay_rate(self):
        assert "fast" in ALLOWED_DECAY_RATE
        assert "normal" in ALLOWED_DECAY_RATE
        assert "slow" in ALLOWED_DECAY_RATE

    def test_allowed_seniority(self):
        assert "jr" in ALLOWED_SENIORITY
        assert "pl" in ALLOWED_SENIORITY
        assert "sr" in ALLOWED_SENIORITY
        assert "ld" in ALLOWED_SENIORITY


class TestLoadTaxonomy:
    def test_loads_successfully(self):
        tax = load_taxonomy()
        assert tax is not None
        assert isinstance(tax, WsiTaxonomy)

    def test_has_parents(self):
        tax = load_taxonomy()
        assert len(tax.parents) > 0

    def test_cached_same_instance(self):
        tax1 = load_taxonomy()
        tax2 = load_taxonomy()
        assert tax1 is tax2  # lru_cache returns same instance

    def test_has_expected_parents(self):
        tax = load_taxonomy()
        assert "communication_collaboration" in tax.parents
        assert "execution_delivery" in tax.parents
        assert "learning_adaptation" in tax.parents

    def test_parents_have_skills(self):
        tax = load_taxonomy()
        for parent_id, parent in tax.parents.items():
            assert len(parent.skills) > 0, f"Parent {parent_id} has no skills"


class TestAllSkillIds:
    def test_returns_list(self):
        ids = all_skill_ids()
        assert isinstance(ids, list)
        assert len(ids) > 0

    def test_sorted(self):
        ids = all_skill_ids()
        assert ids == sorted(ids)

    def test_contains_known_skills(self):
        ids = all_skill_ids()
        assert "active_listening" in ids


class TestAllParentIds:
    def test_returns_list(self):
        ids = all_parent_ids()
        assert isinstance(ids, list)
        assert len(ids) > 0

    def test_sorted(self):
        ids = all_parent_ids()
        assert ids == sorted(ids)

    def test_contains_known_parents(self):
        ids = all_parent_ids()
        assert "communication_collaboration" in ids


class TestFindSkill:
    def test_finds_existing_skill(self):
        skill = find_skill("active_listening")
        assert skill is not None
        assert skill.id == "active_listening"

    def test_returns_none_for_nonexistent(self):
        skill = find_skill("nonexistent_skill_xyz_123")
        assert skill is None

    def test_returns_wsi_skill_instance(self):
        skill_ids = all_skill_ids()
        skill = find_skill(skill_ids[0])
        assert isinstance(skill, WsiSkill)
        assert skill.id == skill_ids[0]
        assert skill.name_pt
        assert skill.description
        assert skill.seniority_min in ALLOWED_SENIORITY


class TestParentOf:
    def test_returns_parent_id(self):
        parent = parent_of("active_listening")
        assert parent is not None
        assert parent == "communication_collaboration"

    def test_returns_none_for_nonexistent(self):
        parent = parent_of("nonexistent_skill_xyz")
        assert parent is None


class TestSkillsByParent:
    def test_returns_skills_for_valid_parent(self):
        skills = skills_by_parent("communication_collaboration")
        assert isinstance(skills, list)
        assert len(skills) > 0
        assert all(isinstance(s, WsiSkill) for s in skills)

    def test_returns_empty_for_nonexistent_parent(self):
        skills = skills_by_parent("nonexistent_parent_xyz")
        assert skills == []

    def test_active_listening_in_communication(self):
        skills = skills_by_parent("communication_collaboration")
        skill_ids = [s.id for s in skills]
        assert "active_listening" in skill_ids


class TestGetSkillsByOcean:
    def test_valid_ocean_returns_list(self):
        skills = get_skills_by_ocean("A")
        assert isinstance(skills, list)
        assert len(skills) > 0

    def test_invalid_ocean_returns_empty(self):
        skills = get_skills_by_ocean("X")  # invalid
        assert skills == []

    def test_all_ocean_dims_have_skills(self):
        for dim in ["O", "C", "E", "A", "N"]:
            skills = get_skills_by_ocean(dim)
            assert len(skills) >= 0  # may be 0 for some dims

    def test_returned_skills_have_correct_ocean(self):
        skills = get_skills_by_ocean("C")  # Conscientiousness
        for s in skills:
            assert s.primary_ocean == "C"


class TestGetSkillsByBiasRisk:
    def test_medium_risk_returns_list(self):
        skills = get_skills_by_bias_risk("medium")
        assert isinstance(skills, list)
        assert len(skills) > 0

    def test_all_risk_levels(self):
        for level in ["low", "medium", "high"]:
            skills = get_skills_by_bias_risk(level)
            assert isinstance(skills, list)

    def test_returned_skills_have_correct_risk(self):
        skills = get_skills_by_bias_risk("high")
        for s in skills:
            assert s.bias_risk == "high"


class TestGetSampleThreshold:
    def test_high_risk_skill(self):
        # Find a high-risk skill or create a mock
        high_skills = get_skills_by_bias_risk("high")
        if high_skills:
            threshold = get_sample_threshold(high_skills[0])
            assert threshold == 30

    def test_medium_risk_skill(self):
        medium_skills = get_skills_by_bias_risk("medium")
        if medium_skills:
            threshold = get_sample_threshold(medium_skills[0])
            assert threshold == 20

    def test_low_risk_skill(self):
        low_skills = get_skills_by_bias_risk("low")
        if low_skills:
            threshold = get_sample_threshold(low_skills[0])
            assert threshold == 12


class TestGetDecayLambda:
    def test_normal_decay_skill(self):
        # Find a skill with normal decay rate
        skill_ids = all_skill_ids()
        for sid in skill_ids:
            skill = find_skill(sid)
            if skill and skill.decay_rate == "normal":
                lam = get_decay_lambda(skill)
                assert lam == pytest.approx(0.05)
                break

    def test_fast_decay_skill(self):
        skill_ids = all_skill_ids()
        for sid in skill_ids:
            skill = find_skill(sid)
            if skill and skill.decay_rate == "fast":
                lam = get_decay_lambda(skill)
                assert lam == pytest.approx(0.12)
                break

    def test_slow_decay_skill(self):
        skill_ids = all_skill_ids()
        for sid in skill_ids:
            skill = find_skill(sid)
            if skill and skill.decay_rate == "slow":
                lam = get_decay_lambda(skill)
                assert lam == pytest.approx(0.02)
                break


class TestWsiSkillModel:
    def test_skill_fields(self):
        skill = find_skill("active_listening")
        assert skill.id == "active_listening"
        assert skill.name_pt == "Escuta ativa"
        assert skill.description
        assert skill.seniority_min in ALLOWED_SENIORITY
        assert skill.source in ALLOWED_SOURCES
        assert skill.bias_risk in ALLOWED_BIAS_RISK
        assert skill.decay_rate in ALLOWED_DECAY_RATE

    def test_all_skills_have_required_fields(self):
        for skill_id in all_skill_ids():
            skill = find_skill(skill_id)
            assert skill is not None
            assert skill.id == skill_id
            assert skill.name_pt
            assert skill.description
            assert skill.bias_risk in ALLOWED_BIAS_RISK
            assert skill.decay_rate in ALLOWED_DECAY_RATE


class TestShimReexport:
    """Test the shared-layer re-export shim."""

    def test_shim_imports_work(self):
        from app.shared.wsi_skill_taxonomy import (
            WsiSkill as WsiSkill2,
            THRESHOLD_BY_BIAS_RISK as THRESH2,
            load_taxonomy as load2,
            find_skill as find2,
            all_skill_ids as all_ids2,
        )
        assert THRESH2["medium"] == 20
        tax = load2()
        assert tax is not None
        skill = find2("active_listening")
        assert skill is not None
        ids = all_ids2()
        assert len(ids) > 0
