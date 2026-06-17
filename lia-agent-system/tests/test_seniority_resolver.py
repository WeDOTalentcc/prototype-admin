import pytest
import asyncio
from unittest.mock import patch

from app.domains.cv_screening.services.seniority_resolver import (
    _infer_seniority_from_salary,
    _infer_seniority_from_skills,
    _collect_signals,
    _redistribute_weights,
    _detect_conflicts,
    _combine_signals,
    resolve_seniority,
    resolve_seniority_full,
    resolve_seniority_simple,
    SenioritySignal,
    SeniorityResolution,
    SIGNAL_WEIGHTS,
)


class TestMotorDeCombinacao:

    def test_rule1_no_signal_fallback(self):
        signals = [
            SenioritySignal(source="explicit", level=None, confidence=0.0, weight=0.50, evidence="nenhum"),
            SenioritySignal(source="title_keywords", level=None, confidence=0.0, weight=0.25, evidence="nenhum"),
        ]
        result = _combine_signals(signals, [], None, None)
        assert result.level == "pleno"
        assert result.agreement == "none"
        assert result.requires_confirmation is True
        assert result.confidence == 0.0

    def test_rule2_single_explicit_signal(self):
        signals = [
            SenioritySignal(source="explicit", level="senior", confidence=1.0, weight=1.0, evidence="recrutador"),
        ]
        result = _combine_signals(signals, [], "senior", None)
        assert result.level == "senior"
        assert result.agreement == "single"
        assert result.confidence == 0.70

    def test_rule2_single_title_signal(self):
        signals = [
            SenioritySignal(source="title_keywords", level="junior", confidence=0.80, weight=1.0, evidence="titulo"),
        ]
        result = _combine_signals(signals, [], None, "Junior Dev")
        assert result.level == "junior"
        assert result.agreement == "single"
        assert result.confidence == 0.50

    def test_rule3_full_agreement_two_signals(self):
        signals = [
            SenioritySignal(source="explicit", level="senior", confidence=1.0, weight=0.50, evidence="recrutador"),
            SenioritySignal(source="title_keywords", level="senior", confidence=0.80, weight=0.50, evidence="titulo"),
        ]
        result = _combine_signals(signals, [], "senior", "Senior Dev")
        assert result.level == "senior"
        assert result.agreement == "full"
        assert result.confidence == 1.0
        assert result.requires_confirmation is False

    def test_rule3_full_agreement_three_signals(self):
        signals = [
            SenioritySignal(source="explicit", level="pleno", confidence=1.0, weight=0.40, evidence="recrutador"),
            SenioritySignal(source="title_keywords", level="pleno", confidence=0.80, weight=0.30, evidence="titulo"),
            SenioritySignal(source="salary_range", level="pleno", confidence=0.65, weight=0.30, evidence="salario"),
        ]
        result = _combine_signals(signals, [], "pleno", "Desenvolvedor Pleno")
        assert result.level == "pleno"
        assert result.agreement == "full"
        assert result.confidence == 1.0
        assert result.requires_confirmation is False

    def test_rule4_explicit_vs_inferred_conflict(self):
        signals = [
            SenioritySignal(source="explicit", level="junior", confidence=1.0, weight=0.50, evidence="recrutador"),
            SenioritySignal(source="title_keywords", level="senior", confidence=0.80, weight=0.50, evidence="titulo"),
        ]
        result = _combine_signals(signals, [], "junior", "Senior Software Engineer")
        assert result.agreement == "conflict"
        assert result.requires_confirmation is True
        assert result.confidence == 0.40
        assert result.confirmation_message is not None
        assert "Júnior" in result.confirmation_message or "júnior" in result.confirmation_message.lower()
        assert "Sênior" in result.confirmation_message or "sênior" in result.confirmation_message.lower()

    def test_rule5_majority_agreement(self):
        signals = [
            SenioritySignal(source="title_keywords", level="senior", confidence=0.80, weight=0.40, evidence="titulo"),
            SenioritySignal(source="jd_analysis", level="senior", confidence=0.70, weight=0.30, evidence="jd"),
            SenioritySignal(source="salary_range", level="junior", confidence=0.65, weight=0.30, evidence="salario"),
        ]
        result = _combine_signals(signals, [], None, "Senior Dev")
        assert result.agreement == "majority"
        assert result.confidence == 0.85

    def test_rule6_weighted_fallback_no_explicit(self):
        signals = [
            SenioritySignal(source="title_keywords", level="senior", confidence=0.80, weight=0.50, evidence="titulo"),
            SenioritySignal(source="salary_range", level="junior", confidence=0.65, weight=0.30, evidence="salario"),
            SenioritySignal(source="skills_complexity", level="pleno", confidence=0.55, weight=0.20, evidence="skills"),
        ]
        result = _combine_signals(signals, [], None, "Engenheiro")
        assert result.confidence == 0.60


class TestSalaryInference:

    def test_junior_salary_range(self):
        result = _infer_seniority_from_salary(2000, 4000)
        assert result == "junior"

    def test_pleno_salary_range(self):
        result = _infer_seniority_from_salary(8000, 14000)
        assert result == "pleno"

    def test_senior_salary_range(self):
        result = _infer_seniority_from_salary(18000, 25000)
        assert result == "senior"

    def test_lead_or_executive_salary_range(self):
        result = _infer_seniority_from_salary(20000, 30000)
        assert result in ("lead", "executive", "senior")

    def test_none_none_returns_none(self):
        result = _infer_seniority_from_salary(None, None)
        assert result is None


class TestSkillsInference:

    def test_senior_skills(self):
        result = _infer_seniority_from_skills(["kubernetes", "system design", "terraform"])
        assert result == "senior"

    def test_junior_skills(self):
        result = _infer_seniority_from_skills(["html básico", "excel", "word"])
        assert result == "junior"

    def test_empty_skills(self):
        result = _infer_seniority_from_skills([])
        assert result is None

    def test_no_indicators_match(self):
        result = _infer_seniority_from_skills(["python", "javascript"])
        assert result is None


class TestConflictDetection:

    def test_explicit_conflicts_with_title(self):
        signals = [
            SenioritySignal(source="explicit", level="junior", confidence=1.0, weight=0.50, evidence="recrutador"),
            SenioritySignal(source="title_keywords", level="senior", confidence=0.80, weight=0.50, evidence="titulo"),
        ]
        warnings = _detect_conflicts(signals, "junior", None, None)
        assert len(warnings) > 0
        assert any("CONFLITO" in w for w in warnings)
        assert any("ítulo" in w.lower() or "titulo" in w.lower() for w in warnings)

    def test_explicit_conflicts_with_salary(self):
        signals = [
            SenioritySignal(source="explicit", level="junior", confidence=1.0, weight=0.50, evidence="recrutador"),
            SenioritySignal(source="salary_range", level="senior", confidence=0.65, weight=0.50, evidence="salario"),
        ]
        warnings = _detect_conflicts(signals, "junior", 15000, 25000)
        assert len(warnings) > 0
        assert any("INCONSISTÊNCIA" in w for w in warnings)
        assert any("salarial" in w.lower() for w in warnings)

    def test_no_conflicts_when_agreeing(self):
        signals = [
            SenioritySignal(source="explicit", level="senior", confidence=1.0, weight=0.50, evidence="recrutador"),
            SenioritySignal(source="title_keywords", level="senior", confidence=0.80, weight=0.50, evidence="titulo"),
        ]
        warnings = _detect_conflicts(signals, "senior", None, None)
        assert len(warnings) == 0


class TestWeightRedistribution:

    def test_two_active_signals_sum_to_one(self):
        signals = [
            SenioritySignal(source="explicit", level="senior", confidence=1.0, weight=0.50, evidence="recrutador"),
            SenioritySignal(source="title_keywords", level="junior", confidence=0.80, weight=0.25, evidence="titulo"),
        ]
        _redistribute_weights(signals)
        active = [s for s in signals if s.level is not None]
        total = sum(s.weight for s in active)
        assert abs(total - 1.0) < 0.001

    def test_one_active_one_inactive(self):
        signals = [
            SenioritySignal(source="explicit", level="senior", confidence=1.0, weight=0.50, evidence="recrutador"),
            SenioritySignal(source="title_keywords", level=None, confidence=0.0, weight=0.25, evidence="nenhum"),
        ]
        _redistribute_weights(signals)
        active = [s for s in signals if s.level is not None]
        assert len(active) == 1
        assert abs(active[0].weight - 1.0) < 0.001

    def test_zero_active_no_changes(self):
        signals = [
            SenioritySignal(source="explicit", level=None, confidence=0.0, weight=0.50, evidence="nenhum"),
            SenioritySignal(source="title_keywords", level=None, confidence=0.0, weight=0.25, evidence="nenhum"),
        ]
        _redistribute_weights(signals)
        assert signals[0].weight == 0.50
        assert signals[1].weight == 0.25


class TestFeatureFlag:

    @pytest.mark.asyncio
    async def test_disabled_returns_fallback(self):
        with patch("app.domains.cv_screening.services.seniority_resolver.SENIORITY_RESOLVER_ENABLED", False):
            result = await resolve_seniority(explicit_seniority="senior")
            assert result.signals == []
            assert result.metadata["feature_flag_enabled"] is False

    @pytest.mark.asyncio
    async def test_disabled_without_explicit(self):
        with patch("app.domains.cv_screening.services.seniority_resolver.SENIORITY_RESOLVER_ENABLED", False):
            result = await resolve_seniority()
            assert result.level == "pleno"
            assert result.signals == []
            assert result.metadata["feature_flag_enabled"] is False
            assert result.confidence == 0.0


class TestPublicAPI:

    def test_resolve_seniority_full_returns_resolution(self):
        result = resolve_seniority_full(explicit_seniority="senior")
        assert isinstance(result, SeniorityResolution)
        assert result.level is not None
        assert result.agreement is not None
        assert result.confidence is not None
        assert result.signals is not None
        assert result.metadata is not None

    def test_resolve_seniority_simple_returns_string(self):
        result = resolve_seniority_simple(explicit_seniority="senior")
        assert isinstance(result, str)
        assert result in ("junior", "pleno", "senior", "lead", "executive")


class TestPortugueseMessages:

    def test_no_signal_confirmation_message_in_portuguese(self):
        signals = [
            SenioritySignal(source="explicit", level=None, confidence=0.0, weight=0.50, evidence="nenhum"),
        ]
        result = _combine_signals(signals, [], None, None)
        assert result.confirmation_message is not None
        assert "senioridade" in result.confirmation_message.lower()
        assert "Júnior" in result.confirmation_message or "Pleno" in result.confirmation_message

    def test_conflict_confirmation_message_in_portuguese(self):
        signals = [
            SenioritySignal(source="explicit", level="junior", confidence=1.0, weight=0.50, evidence="recrutador"),
            SenioritySignal(source="title_keywords", level="senior", confidence=0.80, weight=0.50, evidence="titulo"),
        ]
        result = _combine_signals(signals, [], "junior", "Senior Dev")
        assert result.confirmation_message is not None
        assert "correto" in result.confirmation_message.lower() or "definiu" in result.confirmation_message.lower()

    def test_validation_warnings_contain_conflito(self):
        signals = [
            SenioritySignal(source="explicit", level="junior", confidence=1.0, weight=0.50, evidence="recrutador"),
            SenioritySignal(source="title_keywords", level="senior", confidence=0.80, weight=0.50, evidence="titulo"),
        ]
        warnings = _detect_conflicts(signals, "junior", None, None)
        assert any("CONFLITO" in w for w in warnings)

    def test_validation_warnings_contain_inconsistencia(self):
        signals = [
            SenioritySignal(source="explicit", level="junior", confidence=1.0, weight=0.50, evidence="recrutador"),
            SenioritySignal(source="salary_range", level="senior", confidence=0.65, weight=0.50, evidence="salario"),
        ]
        warnings = _detect_conflicts(signals, "junior", 15000, 25000)
        assert any("INCONSISTÊNCIA" in w for w in warnings)

    def test_no_signal_message_asks_recruiter(self):
        signals = []
        result = _combine_signals(signals, [], None, None)
        msg = result.confirmation_message
        assert msg is not None
        assert "preciso saber" in msg.lower() or "identificar" in msg.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
