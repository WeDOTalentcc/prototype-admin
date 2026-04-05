"""
Tests for Phase 3 - André's Evaluation Criteria Methodology.
Tests cover all 8 mechanisms:
1. Positive/negative evidence base for prompts
2. Explicit/implicit/inferred evidence classification with weights
3. Vague language detection
4. Anomaly detection flags
5. Automatic exclusion for essential requirements
6. Cap 99 with floor rounding
7. Confidence score per requirement
8. "Do not infer" prompt instruction
"""
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.schemas.rubric import (
    EvidenceType,
    RequirementEvaluation,
    RubricEvaluationResult,
    RequirementPriorityEnum,
    EvaluationLevelEnum,
)
from app.domains.cv_screening.services.rubric_evaluation_service import RubricEvaluationService
from app.schemas.rubric import JobRequirementCreate


def make_eval(
    requirement="Test Skill",
    priority=RequirementPriorityEnum.IMPORTANT,
    level=EvaluationLevelEnum.MEETS,
    evidence_type=EvidenceType.EXPLICIT,
    confidence=0.9,
    points=75,
    multiplier=2,
    evidence="Direct evidence from CV",
):
    return RequirementEvaluation(
        requirement=requirement,
        priority=priority,
        level=level,
        evidence_type=evidence_type,
        confidence=confidence,
        points=points,
        multiplier=multiplier,
        weighted_points=points * multiplier,
        max_weighted_points=100 * multiplier,
        evidence=evidence,
    )


class TestEvidenceTypeWeights:
    def test_explicit_evidence_full_weight(self):
        """Explicit evidence should use weight 1.0 in scoring."""
        service = RubricEvaluationService.__new__(RubricEvaluationService)
        evals = [make_eval(evidence_type=EvidenceType.EXPLICIT, points=75, multiplier=2)]
        score, _, _, _ = service._calculate_score(evals)
        assert score == 75

    def test_implicit_evidence_reduced_weight(self):
        """Implicit evidence should use weight 0.7."""
        service = RubricEvaluationService.__new__(RubricEvaluationService)
        evals = [make_eval(evidence_type=EvidenceType.IMPLICIT, points=100, multiplier=2)]
        score, _, _, raw = service._calculate_score(evals)
        assert score == 70
        assert raw == 70.0

    def test_inferred_evidence_heavily_reduced(self):
        """Inferred evidence should use weight 0.3."""
        service = RubricEvaluationService.__new__(RubricEvaluationService)
        evals = [make_eval(evidence_type=EvidenceType.INFERRED, points=100, multiplier=2)]
        score, _, _, raw = service._calculate_score(evals)
        assert score == 30
        assert raw == 30.0

    def test_mixed_evidence_types(self):
        """Mixed evidence types should apply respective weights."""
        service = RubricEvaluationService.__new__(RubricEvaluationService)
        evals = [
            make_eval(evidence_type=EvidenceType.EXPLICIT, points=100, multiplier=3),
            make_eval(evidence_type=EvidenceType.IMPLICIT, points=75, multiplier=2),
            make_eval(evidence_type=EvidenceType.INFERRED, points=40, multiplier=1),
        ]
        score, total, max_p, raw = service._calculate_score(evals)
        assert score == 70
        assert abs(raw - 69.5) < 0.1


class TestCap99:
    def test_perfect_score_capped_at_99(self):
        """Even with all EXCEEDS+EXPLICIT, score cannot exceed 99."""
        service = RubricEvaluationService.__new__(RubricEvaluationService)
        evals = [
            make_eval(level=EvaluationLevelEnum.EXCEEDS, evidence_type=EvidenceType.EXPLICIT, points=100, multiplier=3),
            make_eval(level=EvaluationLevelEnum.EXCEEDS, evidence_type=EvidenceType.EXPLICIT, points=100, multiplier=2),
            make_eval(level=EvaluationLevelEnum.EXCEEDS, evidence_type=EvidenceType.EXPLICIT, points=100, multiplier=1),
        ]
        score, _, _, raw = service._calculate_score(evals)
        assert raw == 100.0
        assert score == 99

    def test_score_below_99_not_capped(self):
        """Score below 99 should pass through unchanged."""
        service = RubricEvaluationService.__new__(RubricEvaluationService)
        evals = [make_eval(evidence_type=EvidenceType.EXPLICIT, points=75, multiplier=1)]
        score, _, _, _ = service._calculate_score(evals)
        assert score < 99

    def test_score_zero_not_affected(self):
        """Score of 0 should remain 0."""
        service = RubricEvaluationService.__new__(RubricEvaluationService)
        evals = [make_eval(level=EvaluationLevelEnum.MISSING, points=0, multiplier=3)]
        score, _, _, _ = service._calculate_score(evals)
        assert score == 0


class TestFloorRounding:
    def test_decimal_rounded_to_integer(self):
        """Scores should always be integers after rounding."""
        service = RubricEvaluationService.__new__(RubricEvaluationService)
        evals = [make_eval(evidence_type=EvidenceType.EXPLICIT, points=75, multiplier=2)]
        score, _, _, _ = service._calculate_score(evals)
        assert score == int(score)

    def test_score_is_always_integer(self):
        """All scores should be integers (no decimal noise)."""
        service = RubricEvaluationService.__new__(RubricEvaluationService)
        for pts in [0, 40, 75, 100]:
            for mult in [1, 2, 3]:
                for ev_type in EvidenceType:
                    evals = [make_eval(points=pts, multiplier=mult, evidence_type=ev_type)]
                    score, _, _, _ = service._calculate_score(evals)
                    assert score == int(score), f"Score {score} not integer for pts={pts}, mult={mult}, ev={ev_type}"

    def test_empty_evaluations_return_zero(self):
        """Empty evaluations should return 0."""
        service = RubricEvaluationService.__new__(RubricEvaluationService)
        score, _, _, _ = service._calculate_score([])
        assert score == 0.0


class TestVagueLanguageDetection:
    def test_detects_portuguese_vague_terms(self):
        """Should detect 'pode ter', 'indica que', 'sugere' etc."""
        service = RubricEvaluationService.__new__(RubricEvaluationService)
        assert service._detect_vague_language("O candidato pode ter experiência com Python")
        assert service._detect_vague_language("Isso indica que o candidato conhece React")
        assert service._detect_vague_language("A experiência sugere familiaridade")

    def test_detects_english_vague_terms(self):
        """Should detect 'probably', 'suggests', 'may have' etc."""
        service = RubricEvaluationService.__new__(RubricEvaluationService)
        assert service._detect_vague_language("Candidate probably knows Python")
        assert service._detect_vague_language("This suggests experience with React")
        assert service._detect_vague_language("Candidate may have used Docker")

    def test_no_false_positive_on_clear_evidence(self):
        """Clear evidence should not trigger vague detection."""
        service = RubricEvaluationService.__new__(RubricEvaluationService)
        assert not service._detect_vague_language("5 years of Python experience at Company X")
        assert not service._detect_vague_language("Led team of 8 engineers")
        assert not service._detect_vague_language("Certificação AWS Solutions Architect")


class TestAnomalyDetection:
    def test_too_many_exceeds_with_few_skills(self):
        """Flag when exceeds count > skills count."""
        service = RubricEvaluationService.__new__(RubricEvaluationService)
        evals = [
            make_eval(level=EvaluationLevelEnum.EXCEEDS, points=100) for _ in range(5)
        ]
        candidate = {"skills": ["Python", "SQL"]}
        anomalies = service._detect_anomalies(evals, candidate)
        assert len(anomalies) > 0
        assert any("ANOMALY" in a for a in anomalies)

    def test_exceeds_over_80_percent(self):
        """Flag when >80% of evaluations are exceeds."""
        service = RubricEvaluationService.__new__(RubricEvaluationService)
        evals = [
            make_eval(level=EvaluationLevelEnum.EXCEEDS, points=100) for _ in range(9)
        ] + [make_eval(level=EvaluationLevelEnum.MEETS, points=75)]
        candidate = {"skills": ["Python", "Java", "React", "Node", "SQL", "Docker", "K8s", "AWS", "GCP", "Go"]}
        anomalies = service._detect_anomalies(evals, candidate)
        assert any(">80%" in a for a in anomalies)

    def test_no_anomaly_for_normal_evaluation(self):
        """Normal evaluation should not trigger anomalies."""
        service = RubricEvaluationService.__new__(RubricEvaluationService)
        evals = [
            make_eval(level=EvaluationLevelEnum.MEETS, points=75),
            make_eval(level=EvaluationLevelEnum.PARTIAL, points=40),
            make_eval(level=EvaluationLevelEnum.MISSING, points=0),
        ]
        candidate = {"skills": ["Python", "Java", "React"]}
        anomalies = service._detect_anomalies(evals, candidate)
        assert len(anomalies) == 0


class TestEssentialExclusion:
    def test_essential_missing_triggers_exclusion(self):
        """Essential requirement with level=missing should exclude."""
        service = RubricEvaluationService.__new__(RubricEvaluationService)
        evals = [
            make_eval(priority=RequirementPriorityEnum.ESSENTIAL, level=EvaluationLevelEnum.MISSING, points=0, multiplier=3),
            make_eval(priority=RequirementPriorityEnum.IMPORTANT, level=EvaluationLevelEnum.MEETS, points=75, multiplier=2),
        ]
        excluded, reasons = service._check_essential_exclusion(evals)
        assert excluded is True
        assert len(reasons) > 0

    def test_essential_inferred_triggers_exclusion(self):
        """Essential requirement with inferred evidence should exclude."""
        service = RubricEvaluationService.__new__(RubricEvaluationService)
        evals = [
            make_eval(
                priority=RequirementPriorityEnum.ESSENTIAL,
                level=EvaluationLevelEnum.MEETS,
                evidence_type=EvidenceType.INFERRED,
                points=75, multiplier=3
            ),
        ]
        excluded, reasons = service._check_essential_exclusion(evals)
        assert excluded is True

    def test_essential_explicit_no_exclusion(self):
        """Essential requirement with explicit evidence should NOT exclude."""
        service = RubricEvaluationService.__new__(RubricEvaluationService)
        evals = [
            make_eval(
                priority=RequirementPriorityEnum.ESSENTIAL,
                level=EvaluationLevelEnum.MEETS,
                evidence_type=EvidenceType.EXPLICIT,
                points=75, multiplier=3
            ),
        ]
        excluded, reasons = service._check_essential_exclusion(evals)
        assert excluded is False
        assert len(reasons) == 0


class TestConfidenceScore:
    def test_confidence_in_evaluation(self):
        """RequirementEvaluation should carry confidence score."""
        eval1 = make_eval(confidence=0.95)
        assert eval1.confidence == 0.95

    def test_default_confidence_is_one(self):
        """Default confidence should be 1.0."""
        eval2 = RequirementEvaluation(
            requirement="Test",
            priority=RequirementPriorityEnum.IMPORTANT,
            level=EvaluationLevelEnum.MEETS,
            points=75, multiplier=2,
            weighted_points=150, max_weighted_points=200,
            evidence="Test evidence"
        )
        assert eval2.confidence == 1.0


class TestRubricEvaluationResultSchema:
    def test_result_has_all_andre_fields(self):
        """Result should include all André methodology fields."""
        result = RubricEvaluationResult(
            score=75.0,
            raw_score=76.3,
            total_weighted_points=305,
            max_possible_points=500,
            evaluations=[],
            reasoning="Test",
            recommendation="Recomendado",
            anomaly_flags=["test"],
            auto_excluded=False,
            exclusion_reasons=[],
            scoring_methodology="andre_v1",
        )
        assert result.raw_score == 76.3
        assert result.scoring_methodology == "andre_v1"
        assert result.auto_excluded is False

    def test_excluded_result(self):
        """Auto-excluded result should have score 0."""
        result = RubricEvaluationResult(
            score=0.0,
            raw_score=65.0,
            total_weighted_points=200,
            max_possible_points=500,
            evaluations=[],
            reasoning="Excluded",
            recommendation="Não Recomendado",
            auto_excluded=True,
            exclusion_reasons=["Essential requirement missing"],
        )
        assert result.auto_excluded is True
        assert result.score == 0.0
        assert result.raw_score == 65.0


class TestEvaluationCriteriaService:
    def test_evidence_patterns_exist(self):
        """EVIDENCE_PATTERNS should have entries for all main categories."""
        from app.domains.cv_screening.services.evaluation_criteria_service import EVIDENCE_PATTERNS
        assert "technical_skill" in EVIDENCE_PATTERNS
        assert "behavioral_competency" in EVIDENCE_PATTERNS
        assert "responsibility" in EVIDENCE_PATTERNS
        for cat, patterns in EVIDENCE_PATTERNS.items():
            assert "positive_templates" in patterns
            assert "negative_templates" in patterns
            assert len(patterns["positive_templates"]) >= 3
            assert len(patterns["negative_templates"]) >= 3

    def test_skill_specific_evidence_exists(self):
        """SKILL_SPECIFIC_EVIDENCE should have key skills."""
        from app.domains.cv_screening.services.evaluation_criteria_service import SKILL_SPECIFIC_EVIDENCE
        assert "Python" in SKILL_SPECIFIC_EVIDENCE
        assert "React" in SKILL_SPECIFIC_EVIDENCE
        assert "Liderança" in SKILL_SPECIFIC_EVIDENCE
        for skill, evidence in SKILL_SPECIFIC_EVIDENCE.items():
            assert "positive" in evidence
            assert "negative" in evidence


class TestEvidenceWeightsClassAttribute:
    def test_evidence_weights_defined(self):
        """EVIDENCE_WEIGHTS class attribute should define all three types."""
        weights = RubricEvaluationService.EVIDENCE_WEIGHTS
        assert EvidenceType.EXPLICIT in weights
        assert EvidenceType.IMPLICIT in weights
        assert EvidenceType.INFERRED in weights

    def test_evidence_weights_values(self):
        """EVIDENCE_WEIGHTS should match André's methodology values."""
        weights = RubricEvaluationService.EVIDENCE_WEIGHTS
        assert weights[EvidenceType.EXPLICIT] == 1.0
        assert weights[EvidenceType.IMPLICIT] == 0.7
        assert weights[EvidenceType.INFERRED] == 0.3


class TestVagueLanguageIndicatorsClassAttribute:
    def test_vague_indicators_include_portuguese(self):
        """VAGUE_LANGUAGE_INDICATORS should include Portuguese terms."""
        indicators = RubricEvaluationService.VAGUE_LANGUAGE_INDICATORS
        assert "pode ter" in indicators
        assert "indica que" in indicators
        assert "sugere" in indicators

    def test_vague_indicators_include_english(self):
        """VAGUE_LANGUAGE_INDICATORS should include English terms."""
        indicators = RubricEvaluationService.VAGUE_LANGUAGE_INDICATORS
        assert "probably" in indicators
        assert "suggests" in indicators
        assert "may have" in indicators


class TestEssentialExclusionImplicitEvidence:
    def test_essential_implicit_triggers_exclusion(self):
        """Essential requirement with implicit evidence should also exclude."""
        service = RubricEvaluationService.__new__(RubricEvaluationService)
        evals = [
            make_eval(
                priority=RequirementPriorityEnum.ESSENTIAL,
                level=EvaluationLevelEnum.EXCEEDS,
                evidence_type=EvidenceType.IMPLICIT,
                points=100, multiplier=3
            ),
        ]
        excluded, reasons = service._check_essential_exclusion(evals)
        assert excluded is True
        assert any("implícita" in r or "implicit" in r for r in reasons)

    def test_essential_partial_no_exclusion(self):
        """Essential with PARTIAL level and explicit evidence should NOT trigger non-explicit exclusion."""
        service = RubricEvaluationService.__new__(RubricEvaluationService)
        evals = [
            make_eval(
                priority=RequirementPriorityEnum.ESSENTIAL,
                level=EvaluationLevelEnum.PARTIAL,
                evidence_type=EvidenceType.EXPLICIT,
                points=40, multiplier=3
            ),
        ]
        excluded, reasons = service._check_essential_exclusion(evals)
        assert excluded is False


    def test_essential_partial_implicit_triggers_exclusion(self):
        """Essential with PARTIAL level and implicit evidence SHOULD trigger exclusion."""
        service = RubricEvaluationService.__new__(RubricEvaluationService)
        evals = [
            make_eval(
                priority=RequirementPriorityEnum.ESSENTIAL,
                level=EvaluationLevelEnum.PARTIAL,
                evidence_type=EvidenceType.IMPLICIT,
                points=40, multiplier=3
            ),
        ]
        excluded, reasons = service._check_essential_exclusion(evals)
        assert excluded is True
        assert any("implicit" in r for r in reasons)


class TestAnomalyDetectionInferredMeets:
    def test_inferred_meets_flagged(self):
        """Meets/exceeds with inferred evidence should be flagged as anomaly."""
        service = RubricEvaluationService.__new__(RubricEvaluationService)
        evals = [
            make_eval(
                level=EvaluationLevelEnum.MEETS,
                evidence_type=EvidenceType.INFERRED,
                points=75
            ),
        ]
        candidate = {"skills": ["Python", "Java", "React"]}
        anomalies = service._detect_anomalies(evals, candidate)
        assert any("inferred" in a.lower() for a in anomalies)

    def test_low_experience_many_exceeds_flagged(self):
        """Low years of experience with many exceeds should be flagged."""
        service = RubricEvaluationService.__new__(RubricEvaluationService)
        evals = [
            make_eval(level=EvaluationLevelEnum.EXCEEDS, points=100) for _ in range(4)
        ]
        candidate = {"skills": ["Python", "Java", "React", "SQL"], "years_of_experience": 1}
        anomalies = service._detect_anomalies(evals, candidate)
        assert any("years" in a.lower() or "experience" in a.lower() for a in anomalies)
