"""Coverage tests for app/shared/bars_evaluator.py — BARS evaluation system."""
import pytest
from app.shared.bars_evaluator import (
    BARSLevel,
    BARSAnchor,
    BARSCriteria,
    BARSEvaluation,
    BARSRubric,
    build_cv_screening_rubric,
    build_interview_rubric,
    build_sourcing_rubric,
    register_rubric,
    get_rubric,
    get_rubric_for_domain,
)


class TestBARSLevel:
    def test_values(self):
        assert BARSLevel.UNSATISFACTORY == 1
        assert BARSLevel.BELOW_EXPECTATIONS == 2
        assert BARSLevel.MEETS_EXPECTATIONS == 3
        assert BARSLevel.EXCEEDS_EXPECTATIONS == 4
        assert BARSLevel.OUTSTANDING == 5

    def test_ordering(self):
        assert BARSLevel.UNSATISFACTORY < BARSLevel.OUTSTANDING
        assert BARSLevel.MEETS_EXPECTATIONS < BARSLevel.EXCEEDS_EXPECTATIONS

    def test_is_int_enum(self):
        assert int(BARSLevel.MEETS_EXPECTATIONS) == 3


class TestBARSAnchor:
    def test_basic(self):
        a = BARSAnchor(level=BARSLevel.MEETS_EXPECTATIONS, description="Adequate")
        assert a.level == BARSLevel.MEETS_EXPECTATIONS
        assert a.description == "Adequate"
        assert a.examples == []

    def test_with_examples(self):
        a = BARSAnchor(
            level=BARSLevel.OUTSTANDING,
            description="Exceptional",
            examples=["Led a team of 10", "Shipped 3 products"],
        )
        assert len(a.examples) == 2
        assert "Led a team of 10" in a.examples


class TestBARSCriteria:
    def setup_method(self):
        self.criteria = BARSCriteria(
            criteria_id="technical",
            name="Technical Skills",
            description="Level of technical proficiency",
            weight=0.35,
            anchors=[
                BARSAnchor(BARSLevel.UNSATISFACTORY, "No skills"),
                BARSAnchor(BARSLevel.MEETS_EXPECTATIONS, "Adequate skills"),
                BARSAnchor(BARSLevel.OUTSTANDING, "Expert level"),
            ],
        )

    def test_basic(self):
        assert self.criteria.criteria_id == "technical"
        assert self.criteria.name == "Technical Skills"
        assert self.criteria.weight == pytest.approx(0.35)
        assert len(self.criteria.anchors) == 3

    def test_get_anchor_found(self):
        anchor = self.criteria.get_anchor(BARSLevel.MEETS_EXPECTATIONS)
        assert anchor is not None
        assert anchor.description == "Adequate skills"

    def test_get_anchor_not_found(self):
        anchor = self.criteria.get_anchor(BARSLevel.BELOW_EXPECTATIONS)
        assert anchor is None

    def test_get_description_for_level_found(self):
        desc = self.criteria.get_description_for_level(BARSLevel.MEETS_EXPECTATIONS)
        assert desc == "Adequate skills"

    def test_get_description_for_level_not_found(self):
        desc = self.criteria.get_description_for_level(BARSLevel.BELOW_EXPECTATIONS)
        assert "2" in desc  # f"Level {level.value}"

    def test_default_weight(self):
        c = BARSCriteria(
            criteria_id="x",
            name="X",
            description="desc",
        )
        assert c.weight == pytest.approx(1.0)
        assert c.anchors == []


class TestBARSEvaluation:
    def test_compute_overall_weighted(self):
        criteria = [
            BARSCriteria("technical", "Tech", "desc", weight=0.5),
            BARSCriteria("communication", "Comm", "desc", weight=0.5),
        ]
        scores = {"technical": 4, "communication": 2}
        result = BARSEvaluation.compute_overall(scores, criteria)
        assert result == pytest.approx(3.0)

    def test_compute_overall_empty_scores(self):
        criteria = [BARSCriteria("x", "X", "desc", weight=1.0)]
        result = BARSEvaluation.compute_overall({}, criteria)
        assert result == pytest.approx(0.0)

    def test_compute_overall_partial_scores(self):
        """Criteria not in scores are excluded from weight total."""
        criteria = [
            BARSCriteria("a", "A", "desc", weight=0.6),
            BARSCriteria("b", "B", "desc", weight=0.4),
        ]
        scores = {"a": 4}  # only "a" scored
        result = BARSEvaluation.compute_overall(scores, criteria)
        assert result == pytest.approx(4.0)  # 4 * 0.6 / 0.6

    def test_compute_overall_unequal_weights(self):
        criteria = [
            BARSCriteria("x", "X", "desc", weight=0.7),
            BARSCriteria("y", "Y", "desc", weight=0.3),
        ]
        scores = {"x": 5, "y": 3}
        result = BARSEvaluation.compute_overall(scores, criteria)
        expected = (5 * 0.7 + 3 * 0.3) / 1.0
        assert result == pytest.approx(expected)


class TestBARSRubric:
    def setup_method(self):
        self.rubric = BARSRubric(
            rubric_id="test_rubric",
            name="Test Rubric",
            domain="testing",
            pass_threshold=3.0,
        )
        self.c1 = BARSCriteria(
            criteria_id="skill1",
            name="Skill 1",
            description="First skill",
            weight=0.5,
            anchors=[
                BARSAnchor(BARSLevel.UNSATISFACTORY, "Poor"),
                BARSAnchor(BARSLevel.MEETS_EXPECTATIONS, "OK"),
                BARSAnchor(BARSLevel.OUTSTANDING, "Great"),
            ],
        )
        self.c2 = BARSCriteria(
            criteria_id="skill2",
            name="Skill 2",
            description="Second skill",
            weight=0.5,
            anchors=[
                BARSAnchor(BARSLevel.UNSATISFACTORY, "Bad"),
                BARSAnchor(BARSLevel.MEETS_EXPECTATIONS, "Fine"),
            ],
        )
        self.rubric.add_criteria(self.c1)
        self.rubric.add_criteria(self.c2)

    def test_add_criteria(self):
        assert len(self.rubric.criteria) == 2

    def test_evaluate_advance(self):
        scores = {"skill1": 4, "skill2": 4}
        eval_result = self.rubric.evaluate("cand-001", scores)
        assert eval_result.candidate_id == "cand-001"
        assert eval_result.rubric_id == "test_rubric"
        assert eval_result.overall_score == pytest.approx(4.0)
        assert eval_result.recommendation == "advance"

    def test_evaluate_strong_advance(self):
        scores = {"skill1": 5, "skill2": 5}
        eval_result = self.rubric.evaluate("cand-002", scores)
        assert eval_result.overall_score == pytest.approx(5.0)
        assert eval_result.recommendation == "strong_advance"

    def test_evaluate_reject(self):
        scores = {"skill1": 1, "skill2": 1}
        eval_result = self.rubric.evaluate("cand-003", scores)
        assert eval_result.overall_score == pytest.approx(1.0)
        assert eval_result.recommendation == "reject"

    def test_evaluate_review(self):
        scores = {"skill1": 2, "skill2": 2}
        eval_result = self.rubric.evaluate("cand-004", scores)
        assert eval_result.overall_score == pytest.approx(2.0)
        assert eval_result.recommendation == "review"

    def test_evaluate_with_justifications(self):
        scores = {"skill1": 3, "skill2": 4}
        justifications = {"skill1": "Adequate performance", "skill2": "Strong results"}
        eval_result = self.rubric.evaluate("cand-005", scores, justifications)
        assert eval_result.justifications["skill1"] == "Adequate performance"

    def test_evaluate_sets_evaluated_at(self):
        scores = {"skill1": 3, "skill2": 3}
        eval_result = self.rubric.evaluate("cand-006", scores)
        assert eval_result.evaluated_at != ""
        assert "T" in eval_result.evaluated_at  # ISO format

    def test_get_explanation(self):
        scores = {"skill1": 3, "skill2": 4}
        justifications = {"skill1": "Met expectations", "skill2": "Above average"}
        eval_result = self.rubric.evaluate("cand-007", scores, justifications)
        explanation = self.rubric.get_explanation(eval_result)
        assert "Test Rubric" in explanation
        assert "cand-007" in explanation
        assert "Skill 1" in explanation
        assert "Skill 2" in explanation
        assert "Met expectations" in explanation

    def test_get_explanation_without_justifications(self):
        scores = {"skill1": 5, "skill2": 1}
        eval_result = self.rubric.evaluate("cand-008", scores)
        explanation = self.rubric.get_explanation(eval_result)
        assert "cand-008" in explanation
        assert "OUTSTANDING" in explanation or "UNSATISFACTORY" in explanation

    def test_rubric_empty_criteria(self):
        rubric = BARSRubric(
            rubric_id="empty",
            name="Empty",
            domain="test",
        )
        assert rubric.criteria == []
        assert rubric.pass_threshold == pytest.approx(3.0)
        assert rubric.description == ""


class TestPrebuiltRubrics:
    def test_build_cv_screening_rubric(self):
        rubric = build_cv_screening_rubric()
        assert rubric.rubric_id == "cv_screening_v1"
        assert rubric.domain == "cv_screening"
        assert len(rubric.criteria) == 4
        crit_ids = {c.criteria_id for c in rubric.criteria}
        assert "technical_skills" in crit_ids
        assert "experience" in crit_ids
        assert "education" in crit_ids
        assert "cultural_indicators" in crit_ids

    def test_cv_screening_rubric_weights_sum_to_one(self):
        rubric = build_cv_screening_rubric()
        total_weight = sum(c.weight for c in rubric.criteria)
        assert total_weight == pytest.approx(1.0)

    def test_cv_screening_rubric_all_anchors(self):
        rubric = build_cv_screening_rubric()
        for criteria in rubric.criteria:
            assert len(criteria.anchors) == 5
            levels = {a.level for a in criteria.anchors}
            assert BARSLevel.UNSATISFACTORY in levels
            assert BARSLevel.OUTSTANDING in levels

    def test_build_interview_rubric(self):
        rubric = build_interview_rubric()
        assert rubric.rubric_id == "interview_eval_v1"
        assert rubric.domain == "interview_scheduling"
        assert len(rubric.criteria) == 4
        crit_ids = {c.criteria_id for c in rubric.criteria}
        assert "communication" in crit_ids
        assert "problem_solving" in crit_ids
        assert "cultural_fit" in crit_ids
        assert "motivation" in crit_ids

    def test_interview_rubric_weights_sum_to_one(self):
        rubric = build_interview_rubric()
        total_weight = sum(c.weight for c in rubric.criteria)
        assert total_weight == pytest.approx(1.0)

    def test_build_sourcing_rubric(self):
        rubric = build_sourcing_rubric()
        assert rubric.rubric_id == "sourcing_eval_v1"
        assert rubric.domain == "sourcing"
        assert len(rubric.criteria) == 4

    def test_sourcing_rubric_weights_sum_to_one(self):
        rubric = build_sourcing_rubric()
        total_weight = sum(c.weight for c in rubric.criteria)
        assert total_weight == pytest.approx(1.0)

    def test_sourcing_rubric_anchors(self):
        rubric = build_sourcing_rubric()
        for criteria in rubric.criteria:
            assert len(criteria.anchors) == 5


class TestRubricRegistry:
    def test_get_rubric_registered(self):
        # Pre-built rubrics are auto-registered at import time
        rubric = get_rubric("cv_screening_v1")
        assert rubric is not None
        assert rubric.rubric_id == "cv_screening_v1"

    def test_get_rubric_not_found(self):
        rubric = get_rubric("nonexistent_rubric_xyz")
        assert rubric is None

    def test_get_rubric_for_domain_found(self):
        rubric = get_rubric_for_domain("cv_screening")
        assert rubric is not None

    def test_get_rubric_for_domain_not_found(self):
        rubric = get_rubric_for_domain("nonexistent_domain")
        assert rubric is None

    def test_register_and_retrieve(self):
        new_rubric = BARSRubric(
            rubric_id="custom_test_rubric_xyz",
            name="Custom Test",
            domain="custom_domain_test",
        )
        register_rubric(new_rubric)
        retrieved = get_rubric("custom_test_rubric_xyz")
        assert retrieved is not None
        assert retrieved.name == "Custom Test"

    def test_get_rubric_for_domain_custom(self):
        # Custom domain registered above
        rubric = get_rubric_for_domain("custom_domain_test")
        assert rubric is not None


class TestBARSEndToEnd:
    def test_cv_screening_full_evaluation(self):
        rubric = build_cv_screening_rubric()
        scores = {
            "technical_skills": 4,
            "experience": 3,
            "education": 4,
            "cultural_indicators": 5,
        }
        justifications = {
            "technical_skills": "Strong Python and FastAPI experience",
            "experience": "3 years relevant experience",
            "education": "Computer Science degree",
            "cultural_indicators": "Values align perfectly",
        }
        eval_result = rubric.evaluate("cand-e2e", scores, justifications)
        assert eval_result.overall_score > 3.0
        assert eval_result.recommendation in {"advance", "strong_advance"}
        explanation = rubric.get_explanation(eval_result)
        assert "cand-e2e" in explanation

    def test_reject_low_scores(self):
        rubric = build_cv_screening_rubric()
        scores = {
            "technical_skills": 1,
            "experience": 1,
            "education": 2,
            "cultural_indicators": 1,
        }
        eval_result = rubric.evaluate("poor-cand", scores)
        assert eval_result.recommendation == "reject"

    def test_interview_evaluation(self):
        rubric = build_interview_rubric()
        scores = {
            "communication": 5,
            "problem_solving": 5,
            "cultural_fit": 4,
            "motivation": 5,
        }
        eval_result = rubric.evaluate("star-cand", scores)
        assert eval_result.recommendation == "strong_advance"
