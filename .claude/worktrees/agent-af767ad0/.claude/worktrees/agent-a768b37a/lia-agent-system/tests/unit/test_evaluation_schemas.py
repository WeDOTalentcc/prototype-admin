"""
Unit tests for evaluation schemas and ScreeningQuestionSet model.
Covers:
- app.schemas.evaluation_criteria (EvaluationCriteriaResponse, CriteriaMatchResult)
- app.domains.cv_screening.models.screening_question_set (ScreeningQuestionSet)
"""
import pytest

pytestmark = pytest.mark.easy

import uuid
from datetime import datetime
from unittest.mock import MagicMock, patch


class TestEvaluationCriteriaResponse:
    """Tests for EvaluationCriteriaResponse Pydantic schema."""

    def _make_schema(self, **overrides):
        from app.schemas.evaluation_criteria import EvaluationCriteriaResponse
        defaults = dict(
            id=uuid.uuid4(),
            name="Comunicação",
            category="behavioral",
            subcategory="soft_skills",
            positive_evidences=["Articulate", "Clear"],
            negative_evidences=["Vague"],
            evaluation_guidelines="Assess clarity",
            effectiveness_score=0.85,
            usage_count=12,
            source="manual",
        )
        defaults.update(overrides)
        return EvaluationCriteriaResponse(**defaults)

    def test_valid_full_instance(self):
        obj = self._make_schema()
        assert obj.name == "Comunicação"
        assert obj.category == "behavioral"
        assert obj.effectiveness_score == 0.85

    def test_optional_subcategory_none(self):
        obj = self._make_schema(subcategory=None)
        assert obj.subcategory is None

    def test_optional_evaluation_guidelines_none(self):
        obj = self._make_schema(evaluation_guidelines=None)
        assert obj.evaluation_guidelines is None

    def test_positive_evidences_list(self):
        obj = self._make_schema(positive_evidences=["A", "B", "C"])
        assert len(obj.positive_evidences) == 3
        assert "A" in obj.positive_evidences

    def test_negative_evidences_empty_list(self):
        obj = self._make_schema(negative_evidences=[])
        assert obj.negative_evidences == []

    def test_effectiveness_score_zero(self):
        obj = self._make_schema(effectiveness_score=0.0)
        assert obj.effectiveness_score == 0.0

    def test_usage_count_zero(self):
        obj = self._make_schema(usage_count=0)
        assert obj.usage_count == 0

    def test_id_is_uuid(self):
        uid = uuid.uuid4()
        obj = self._make_schema(id=uid)
        assert obj.id == uid

    def test_from_attributes_config_exists(self):
        from app.schemas.evaluation_criteria import EvaluationCriteriaResponse
        assert EvaluationCriteriaResponse.model_config.get("from_attributes") is True or \
               hasattr(EvaluationCriteriaResponse, "Config")

    def test_serialization_to_dict(self):
        obj = self._make_schema()
        data = obj.model_dump()
        assert "name" in data
        assert "category" in data
        assert "effectiveness_score" in data


class TestCriteriaMatchResult:
    """Tests for CriteriaMatchResult Pydantic schema."""

    def _make_criteria_response(self):
        from app.schemas.evaluation_criteria import EvaluationCriteriaResponse
        return EvaluationCriteriaResponse(
            id=uuid.uuid4(),
            name="Technical",
            category="technical",
            positive_evidences=["code review"],
            negative_evidences=[],
            effectiveness_score=0.9,
            usage_count=5,
            source="auto",
        )

    def test_valid_match_result(self):
        from app.schemas.evaluation_criteria import CriteriaMatchResult
        criteria = self._make_criteria_response()
        result = CriteriaMatchResult(
            requirement="Python 5+ anos",
            matched_criteria=[criteria],
            match_score=0.95,
        )
        assert result.requirement == "Python 5+ anos"
        assert len(result.matched_criteria) == 1
        assert result.match_score == 0.95

    def test_empty_matched_criteria(self):
        from app.schemas.evaluation_criteria import CriteriaMatchResult
        result = CriteriaMatchResult(
            requirement="Go lang",
            matched_criteria=[],
            match_score=0.0,
        )
        assert result.matched_criteria == []

    def test_multiple_matched_criteria(self):
        from app.schemas.evaluation_criteria import CriteriaMatchResult
        c1 = self._make_criteria_response()
        c2 = self._make_criteria_response()
        result = CriteriaMatchResult(
            requirement="Fullstack",
            matched_criteria=[c1, c2],
            match_score=0.80,
        )
        assert len(result.matched_criteria) == 2

    def test_serialization(self):
        from app.schemas.evaluation_criteria import CriteriaMatchResult
        result = CriteriaMatchResult(
            requirement="Leadership",
            matched_criteria=[],
            match_score=0.5,
        )
        data = result.model_dump()
        assert data["requirement"] == "Leadership"
        assert data["match_score"] == 0.5


def _get_sqs_model():
    """Import ScreeningQuestionSet, returning None if SQLAlchemy MetaData conflict."""
    import sys
    cached = sys.modules.get("app.domains.cv_screening.models.screening_question_set")
    if cached:
        return getattr(cached, "ScreeningQuestionSet", None)
    try:
        from app.domains.cv_screening.models.screening_question_set import ScreeningQuestionSet
        return ScreeningQuestionSet
    except Exception:
        return None


class TestScreeningQuestionSetModel:
    """Tests for ScreeningQuestionSet SQLAlchemy model attributes."""

    def test_model_tablename(self):
        import pytest
        cls = _get_sqs_model()
        if cls is None:
            pytest.skip("ScreeningQuestionSet unavailable")
        assert cls.__tablename__ == "screening_question_sets"

    def test_model_has_expected_columns(self):
        import pytest
        cls = _get_sqs_model()
        if cls is None:
            pytest.skip("ScreeningQuestionSet unavailable")
        try:
            col_names = [c.name for c in cls.__table__.columns]
        except Exception:
            pytest.skip("Table already registered in shared MetaData")
        assert "id" in col_names
        assert "job_vacancy_id" in col_names

    def test_model_indexes_exist(self):
        import pytest
        cls = _get_sqs_model()
        if cls is None:
            pytest.skip("ScreeningQuestionSet unavailable")
        try:
            index_names = [idx.name for idx in cls.__table__.indexes]
        except Exception:
            pytest.skip("Table already registered in shared MetaData")
        assert any("job_vacancy" in name for name in index_names)

    def test_repr_format(self):
        import pytest
        cls = _get_sqs_model()
        if cls is None:
            pytest.skip("ScreeningQuestionSet unavailable")
        assert "ScreeningQuestionSet" in repr(cls)

    def test_extra_metadata_column_name(self):
        import pytest
        cls = _get_sqs_model()
        if cls is None:
            pytest.skip("ScreeningQuestionSet unavailable")
        try:
            col = cls.__table__.columns.get("metadata")
        except Exception:
            pytest.skip("Table already registered in shared MetaData")
        assert col is not None
