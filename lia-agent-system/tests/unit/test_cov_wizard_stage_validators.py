"""Coverage tests for wizard_stage_validators.py — pure dict->list[str]."""
import pytest

from app.domains.job_management.schemas.wizard_stage_validators import (
    STAGE_VALIDATORS,
    validate_stage,
    _validate_description,
    _validate_basic_info,
    _validate_competencies,
    _validate_salary,
    _validate_wsi,
    _validate_review,
)


class TestValidateStage:
    def test_unknown_stage_returns_empty(self):
        assert validate_stage("nonexistent_stage", {}) == []

    def test_known_stage_dispatches(self):
        result = validate_stage("description", {})
        assert isinstance(result, list)

    def test_stage_validators_dict_has_all_stages(self):
        expected = {"description", "basic-info", "competencies", "salary", "wsi-questions", "review"}
        assert expected <= set(STAGE_VALIDATORS.keys())

    def test_stage_exception_returns_empty(self):
        # validate_stage returns [] for unknown stages (fail-open)
        result = validate_stage("completely_unknown_stage_xyz", {})
        assert result == []


class TestValidateDescription:
    def test_missing_job_title_flagged(self):
        result = _validate_description({"seniority": "senior"})
        assert "job_title" in result

    def test_missing_seniority_flagged(self):
        result = _validate_description({"job_title": "Engenheiro"})
        assert "seniority" in result

    def test_both_present_no_missing(self):
        result = _validate_description({"job_title": "Engenheiro", "seniority": "senior"})
        assert result == []

    def test_empty_job_title_flagged(self):
        result = _validate_description({"job_title": "   ", "seniority": "sr"})
        assert "job_title" in result

    def test_empty_dict_both_missing(self):
        result = _validate_description({})
        assert "job_title" in result
        assert "seniority" in result


class TestValidateBasicInfo:
    def test_missing_both_flagged(self):
        result = _validate_basic_info({})
        assert "num_positions_or_department" in result

    def test_has_num_positions_ok(self):
        result = _validate_basic_info({"num_positions": 3})
        assert result == []

    def test_has_department_ok(self):
        result = _validate_basic_info({"department": "Engineering"})
        assert result == []


class TestValidateCompetencies:
    def test_missing_skills_flagged(self):
        result = _validate_competencies({})
        assert "detected_skills" in result

    def test_empty_skills_list_flagged(self):
        result = _validate_competencies({"detected_skills": []})
        assert "detected_skills" in result

    def test_has_skills_ok(self):
        result = _validate_competencies({"detected_skills": ["Python", "SQL"]})
        assert result == []

    def test_competencias_tecnicas_fallback(self):
        result = _validate_competencies({"competenciasTecnicas": ["Python"]})
        assert result == []


class TestValidateSalary:
    def test_missing_salary_flagged(self):
        result = _validate_salary({})
        assert "salary_min_or_salary_disclosed" in result

    def test_has_salary_min_ok(self):
        result = _validate_salary({"salary_min": 5000})
        assert result == []

    def test_has_salary_disclosed_ok(self):
        result = _validate_salary({"salary_disclosed": True})
        assert result == []


class TestValidateWsi:
    def test_missing_questions_flagged(self):
        result = _validate_wsi({})
        assert "wsi_questions_min_3" in result

    def test_fewer_than_3_flagged(self):
        result = _validate_wsi({"wsi_questions": ["q1", "q2"]})
        assert "wsi_questions_min_3" in result

    def test_exactly_3_ok(self):
        result = _validate_wsi({"wsi_questions": ["q1", "q2", "q3"]})
        assert result == []

    def test_more_than_3_ok(self):
        result = _validate_wsi({"wsi_questions": ["q1", "q2", "q3", "q4", "q5", "q6"]})
        assert result == []


class TestValidateReview:
    def test_missing_jd_flagged(self):
        result = _validate_review({})
        assert "job_description_min_150_chars" in result

    def test_short_jd_flagged(self):
        result = _validate_review({"job_description": "short"})
        assert "job_description_min_150_chars" in result

    def test_long_jd_ok(self):
        long_jd = "a" * 200
        result = _validate_review({"job_description": long_jd})
        assert result == []

    def test_enriched_jd_fallback(self):
        long_jd = "a" * 200
        result = _validate_review({"enriched_jd": long_jd})
        assert result == []

    def test_exactly_150_chars_ok(self):
        jd = "a" * 150
        result = _validate_review({"job_description": jd})
        assert result == []
