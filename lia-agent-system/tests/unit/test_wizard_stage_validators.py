"""
Tests for wizard_stage_validators — Frente D.
6 stages × 3 scenarios = 18+ tests.
"""
import pytest
from app.domains.job_management.schemas.wizard_stage_validators import validate_stage


class TestDescriptionValidator:
    def test_complete_ok(self):
        draft = {"job_title": "Engenheiro de Software", "seniority": "pleno"}
        assert validate_stage("description", draft) == []

    def test_missing_job_title(self):
        draft = {"seniority": "pleno"}
        missing = validate_stage("description", draft)
        assert "job_title" in missing

    def test_empty_title(self):
        draft = {"job_title": "   ", "seniority": "pleno"}
        missing = validate_stage("description", draft)
        assert "job_title" in missing


class TestBasicInfoValidator:
    def test_complete_ok(self):
        draft = {"num_positions": 2, "department": "Engenharia"}
        assert validate_stage("basic-info", draft) == []

    def test_has_department_only(self):
        draft = {"department": "Engenharia"}
        assert validate_stage("basic-info", draft) == []

    def test_has_num_positions_only(self):
        draft = {"num_positions": 1}
        assert validate_stage("basic-info", draft) == []

    def test_missing_both(self):
        draft = {}
        missing = validate_stage("basic-info", draft)
        assert "num_positions_or_department" in missing


class TestCompetenciesValidator:
    def test_complete_ok(self):
        draft = {"detected_skills": ["Python", "FastAPI"]}
        assert validate_stage("competencies", draft) == []

    def test_missing_skills(self):
        draft = {}
        missing = validate_stage("competencies", draft)
        assert "detected_skills" in missing

    def test_empty_skills_list(self):
        draft = {"detected_skills": []}
        missing = validate_stage("competencies", draft)
        assert "detected_skills" in missing


class TestSalaryValidator:
    def test_complete_with_min(self):
        draft = {"salary_min": 5000}
        assert validate_stage("salary", draft) == []

    def test_complete_disclosed(self):
        draft = {"salary_disclosed": True}
        assert validate_stage("salary", draft) == []

    def test_missing_both(self):
        draft = {}
        missing = validate_stage("salary", draft)
        assert "salary_min_or_salary_disclosed" in missing


class TestWsiValidator:
    def test_complete_3_questions(self):
        draft = {"wsi_questions": ["q1", "q2", "q3"]}
        assert validate_stage("wsi-questions", draft) == []

    def test_fewer_than_3(self):
        draft = {"wsi_questions": ["q1", "q2"]}
        missing = validate_stage("wsi-questions", draft)
        assert "wsi_questions_min_3" in missing

    def test_empty_questions(self):
        draft = {}
        missing = validate_stage("wsi-questions", draft)
        assert "wsi_questions_min_3" in missing


class TestReviewValidator:
    def test_complete_ok(self):
        draft = {"job_description": "A" * 200}
        assert validate_stage("review", draft) == []

    def test_too_short(self):
        draft = {"job_description": "Short"}
        missing = validate_stage("review", draft)
        assert "job_description_min_150_chars" in missing

    def test_missing_jd(self):
        draft = {}
        missing = validate_stage("review", draft)
        assert "job_description_min_150_chars" in missing


class TestUnknownStage:
    def test_unknown_stage_returns_empty(self):
        assert validate_stage("nonexistent", {}) == []

    def test_exception_in_validator_fail_open(self):
        # Even if job_draft is weird, should not raise
        assert isinstance(validate_stage("description", None), list)
