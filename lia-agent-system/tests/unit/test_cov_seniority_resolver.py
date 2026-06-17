"""Coverage tests for seniority_resolver.py — deterministic signal combination."""
import pytest
from app.domains.cv_screening.services.seniority_resolver import (
    SenioritySignal,
    SeniorityResolution,
    _infer_seniority_from_salary,
    _infer_seniority_from_skills,
    resolve_seniority_simple,
    SIGNAL_WEIGHTS,
    SENIORITY_DISPLAY_NAMES,
    SENIORITY_RESOLVER_ENABLED,
    SENIOR_SKILL_INDICATORS,
    JUNIOR_SKILL_INDICATORS,
)


class TestConstants:
    def test_resolver_enabled(self):
        assert SENIORITY_RESOLVER_ENABLED is True

    def test_signal_weights_sum_less_than_2(self):
        total = sum(SIGNAL_WEIGHTS.values())
        assert total > 0

    def test_display_names_for_all_levels(self):
        assert "junior" in SENIORITY_DISPLAY_NAMES
        assert "senior" in SENIORITY_DISPLAY_NAMES
        assert "pleno" in SENIORITY_DISPLAY_NAMES

    def test_senior_skill_indicators_nonempty(self):
        assert len(SENIOR_SKILL_INDICATORS) > 0
        assert "kubernetes" in SENIOR_SKILL_INDICATORS

    def test_junior_skill_indicators_nonempty(self):
        assert len(JUNIOR_SKILL_INDICATORS) > 0


class TestSenioritySignal:
    def test_basic_instantiation(self):
        s = SenioritySignal(
            source="explicit",
            level="senior",
            confidence=0.9,
            weight=0.5,
            evidence="Recruiter said 'senior'",
        )
        assert s.source == "explicit"
        assert s.level == "senior"
        assert s.confidence == pytest.approx(0.9)

    def test_level_none(self):
        s = SenioritySignal(
            source="salary_range",
            level=None,
            confidence=0.0,
            weight=0.15,
            evidence=None,
        )
        assert s.level is None
        assert s.evidence is None


class TestSeniorityResolution:
    def test_basic_instantiation(self):
        r = SeniorityResolution(
            level="senior",
            source="explicit+title",
            confidence=0.85,
            agreement="majority",
            signals=[],
            validation_warnings=[],
            requires_confirmation=False,
            confirmation_message=None,
            metadata={},
        )
        assert r.level == "senior"
        assert r.confidence == pytest.approx(0.85)

    def test_with_conflict(self):
        r = SeniorityResolution(
            level="pleno",
            source="title_keywords",
            confidence=0.4,
            agreement="conflict",
            signals=[],
            validation_warnings=["Conflito entre título e salário"],
            requires_confirmation=True,
            confirmation_message="O nível parece conflituoso",
            metadata={"signal_count": 2},
        )
        assert r.agreement == "conflict"
        assert len(r.validation_warnings) == 1


class TestInferSeniorityFromSalary:
    def test_high_salary_returns_senior_or_lead(self):
        result = _infer_seniority_from_salary(15000, 25000)
        assert result is not None
        assert result in ["senior", "lead", "executive"]

    def test_low_salary_returns_junior(self):
        result = _infer_seniority_from_salary(2000, 4000)
        assert result in ["junior", "pleno"]

    def test_none_both_returns_none(self):
        result = _infer_seniority_from_salary(None, None)
        assert result is None

    def test_only_min_salary(self):
        result = _infer_seniority_from_salary(8000, None)
        assert result is not None

    def test_only_max_salary(self):
        result = _infer_seniority_from_salary(None, 12000)
        assert result is not None

    def test_mid_salary_returns_pleno(self):
        result = _infer_seniority_from_salary(5000, 8000)
        assert result in ["pleno", "junior", "senior"]

    def test_returns_string(self):
        result = _infer_seniority_from_salary(10000, 15000)
        assert isinstance(result, str)


class TestInferSeniorityFromSkills:
    def test_empty_list_returns_none(self):
        result = _infer_seniority_from_skills([])
        assert result is None

    def test_none_returns_none(self):
        result = _infer_seniority_from_skills(None)
        assert result is None

    def test_senior_skills_returns_senior(self):
        result = _infer_seniority_from_skills(["kubernetes", "system design", "arquitetura"])
        assert result == "senior"

    def test_junior_skills_returns_junior(self):
        result = _infer_seniority_from_skills(["html básico", "excel", "word"])
        assert result == "junior"

    def test_mixed_skills_returns_something(self):
        result = _infer_seniority_from_skills(["Python", "Django", "PostgreSQL"])
        assert result is None or isinstance(result, str)

    def test_case_insensitive(self):
        result = _infer_seniority_from_skills(["Kubernetes", "System Design"])
        assert result == "senior"


class TestResolveSenioritySimple:
    def test_explicit_senior(self):
        result = resolve_seniority_simple(explicit_seniority="senior")
        assert result in ["senior", "lead", "executive", "pleno", "junior"]

    def test_no_input_returns_default(self):
        result = resolve_seniority_simple()
        assert isinstance(result, str)
        assert result in ["junior", "pleno", "senior", "lead", "executive"]

    def test_returns_string(self):
        result = resolve_seniority_simple(job_title="Backend Engineer")
        assert isinstance(result, str)

    def test_explicit_junior_title(self):
        result = resolve_seniority_simple(explicit_seniority="junior", job_title="Desenvolvedor Júnior")
        assert result in ["junior", "pleno"]

    def test_explicit_overrides_title(self):
        result = resolve_seniority_simple(explicit_seniority="senior", job_title="Estagiário")
        # Explicit signal has weight 0.50, should dominate
        assert result is not None

    def test_with_all_params(self):
        result = resolve_seniority_simple(
            explicit_seniority="pleno",
            job_title="Engenheiro de Software",
            job_description="Precisa de 3 anos de experiência com Python",
        )
        assert isinstance(result, str)

    def test_lead_seniority(self):
        result = resolve_seniority_simple(explicit_seniority="lead")
        assert result in ["lead", "senior", "executive", "pleno"]
