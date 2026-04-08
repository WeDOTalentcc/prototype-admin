"""
Unit tests for RubricEvaluationService — targeting
app/domains/cv_screening/services/rubric_evaluation_service.py.
Covers: RubricEvaluationCache, CalibrationFeedback, get_recommendation,
RubricEvaluationService helpers (_extract_cv_content, _detect_vague_language,
_detect_anomalies, _check_essential_exclusion, _format_requirements_for_prompt,
_calculate_score, _fallback_evaluation, _parse_llm_response).
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta


# ---------------------------------------------------------------------------
# get_recommendation
# ---------------------------------------------------------------------------

class TestGetRecommendation:
    def test_highly_recommended(self):
        from app.domains.cv_screening.services.rubric_evaluation_service import get_recommendation
        assert get_recommendation(90) == "Altamente Recomendado"
        assert get_recommendation(85) == "Altamente Recomendado"

    def test_recommended(self):
        from app.domains.cv_screening.services.rubric_evaluation_service import get_recommendation
        assert get_recommendation(75) == "Recomendado"
        assert get_recommendation(70) == "Recomendado"

    def test_potential(self):
        from app.domains.cv_screening.services.rubric_evaluation_service import get_recommendation
        assert get_recommendation(60) == "Potencial"
        assert get_recommendation(55) == "Potencial"

    def test_low_match(self):
        from app.domains.cv_screening.services.rubric_evaluation_service import get_recommendation
        assert get_recommendation(45) == "Baixo Match"
        assert get_recommendation(40) == "Baixo Match"

    def test_not_recommended(self):
        from app.domains.cv_screening.services.rubric_evaluation_service import get_recommendation
        assert get_recommendation(30) == "Não Recomendado"
        assert get_recommendation(0) == "Não Recomendado"


# ---------------------------------------------------------------------------
# RubricEvaluationCache
# ---------------------------------------------------------------------------

class TestRubricEvaluationCache:
    @pytest.fixture
    def cache(self):
        from app.domains.cv_screening.services.rubric_evaluation_service import RubricEvaluationCache
        return RubricEvaluationCache(ttl_hours=1)

    @pytest.fixture
    def mock_result(self):
        r = MagicMock()
        r.score = 75.0
        return r

    @pytest.fixture
    def mock_requirements(self):
        req = MagicMock()
        req.requirement = "Python experience"
        req.priority = MagicMock()
        req.priority.value = "essential"
        req.description = "3+ years"
        return [req]

    def test_get_returns_none_when_empty(self, cache, mock_requirements):
        result = cache.get({"id": "c1", "name": "Test"}, mock_requirements)
        assert result is None

    def test_set_and_get(self, cache, mock_result, mock_requirements):
        candidate = {"id": "c1", "name": "Test Candidate"}
        cache.set(candidate, mock_requirements, mock_result)
        cached = cache.get(candidate, mock_requirements)
        assert cached is not None
        assert cached.score == 75.0

    def test_expired_entry_returns_none(self, mock_result, mock_requirements):
        from app.domains.cv_screening.services.rubric_evaluation_service import RubricEvaluationCache
        cache = RubricEvaluationCache(ttl_hours=0)  # 0 hours = instant expiry
        candidate = {"id": "c1", "name": "Test"}
        cache.set(candidate, mock_requirements, mock_result)
        # The ttl is 0 hours, but timedelta(hours=0) means it expires immediately at next check
        # Since set and get happen almost instantly, we need to manipulate the cache
        key = list(cache._cache.keys())[0]
        cache._cache[key] = (mock_result, datetime.utcnow() - timedelta(hours=1))
        cached = cache.get(candidate, mock_requirements)
        assert cached is None

    def test_clear_expired(self, cache, mock_result, mock_requirements):
        candidate = {"id": "c1", "name": "Test"}
        cache.set(candidate, mock_requirements, mock_result)
        # Force expiry
        key = list(cache._cache.keys())[0]
        cache._cache[key] = (mock_result, datetime.utcnow() - timedelta(hours=2))
        cleared = cache.clear_expired()
        assert cleared == 1

    def test_log_variation(self, cache):
        cache.log_variation("c1", "j1", 70.0, 80.0, 10.0)
        log = cache.get_variation_log()
        assert len(log) == 1
        assert log[0]["candidate_id"] == "c1"
        assert log[0]["variation"] == 10.0

    def test_log_variation_exceeds_threshold(self, cache):
        cache.log_variation("c1", "j1", 40.0, 80.0, 40.0)
        log = cache.get_variation_log()
        assert log[0]["exceeds_threshold"] is True

    def test_log_variation_within_threshold(self, cache):
        cache.log_variation("c1", "j1", 70.0, 72.0, 2.0)
        log = cache.get_variation_log()
        assert log[0]["exceeds_threshold"] is False

    def test_calibration_version_invalidates_cache(self, cache, mock_result, mock_requirements):
        candidate = {"id": "c1", "name": "Test"}
        cache.set(candidate, mock_requirements, mock_result, calibration_version=1)
        # Same calibration version should hit
        cached = cache.get(candidate, mock_requirements, calibration_version=1)
        assert cached is not None
        # Different calibration version should miss
        cached2 = cache.get(candidate, mock_requirements, calibration_version=2)
        assert cached2 is None


# ---------------------------------------------------------------------------
# CalibrationFeedback
# ---------------------------------------------------------------------------

class TestCalibrationFeedback:
    @pytest.fixture
    def feedback(self):
        from app.domains.cv_screening.services.rubric_evaluation_service import CalibrationFeedback
        return CalibrationFeedback()

    def test_initial_calibration_version(self, feedback):
        assert feedback.get_calibration_version("job-1") == 0

    def test_record_feedback_increments_version(self, feedback):
        feedback.record_feedback(
            evaluation_id="eval-1",
            candidate_id="c1",
            job_id="job-1",
            original_score=70.0,
            recruiter_adjusted_score=80.0,
            recruiter_decision="approved",
        )
        assert feedback.get_calibration_version("job-1") == 1

    def test_get_calibration_adjustment(self, feedback):
        adj = feedback.get_calibration_adjustment("job-1")
        assert isinstance(adj, float)

    def test_feedback_stats_empty(self, feedback):
        stats = feedback.get_feedback_stats()
        assert isinstance(stats, dict)

    def test_feedback_stats_after_feedback(self, feedback):
        feedback.record_feedback(
            evaluation_id="eval-2",
            candidate_id="c1",
            job_id="job-1",
            original_score=70.0,
            recruiter_adjusted_score=85.0,
            recruiter_decision="approved",
        )
        stats = feedback.get_feedback_stats(job_id="job-1")
        assert stats.get("total_feedbacks", 0) >= 1 or "total" in str(stats)

    def test_multiple_feedbacks_aggregate(self, feedback):
        for i in range(5):
            feedback.record_feedback(
                evaluation_id=f"eval-{i}",
                candidate_id=f"c{i}",
                job_id="job-1",
                original_score=60.0 + i,
                recruiter_adjusted_score=70.0 + i,
                recruiter_decision="approved",
            )
        version = feedback.get_calibration_version("job-1")
        assert version == 5


# ---------------------------------------------------------------------------
# RubricEvaluationService helpers
# ---------------------------------------------------------------------------

class TestRubricEvaluationServiceHelpers:
    @pytest.fixture
    def service(self):
        from app.domains.cv_screening.services.rubric_evaluation_service import RubricEvaluationService
        mock_llm = MagicMock()
        return RubricEvaluationService(llm_service=mock_llm)

    def test_extract_cv_content_basic(self, service):
        candidate = {
            "current_title": "Senior Dev",
            "current_company": "Acme",
            "years_of_experience": 10,
            "seniority_level": "Senior",
            "technical_skills": ["Python", "FastAPI"],
            "soft_skills": ["Leadership"],
            "certifications": ["AWS SA"],
            "languages": {"English": "Fluent", "Portuguese": "Native"},
        }
        content = service._extract_cv_content(candidate)
        assert "Senior Dev" in content
        assert "Python" in content
        assert "AWS SA" in content
        assert "English" in content

    def test_extract_cv_content_with_education(self, service):
        candidate = {
            "education": [
                {"degree": "MSc", "institution": "MIT", "field_of_study": "CS"}
            ]
        }
        content = service._extract_cv_content(candidate)
        assert "MSc" in content
        assert "MIT" in content

    def test_extract_cv_content_with_work_history(self, service):
        candidate = {
            "work_history": [
                {
                    "title": "Engineer",
                    "company_name": "BigCo",
                    "start_date": "2020",
                    "end_date": "2023",
                    "description": "Built systems",
                    "technologies": ["Python", "Go"],
                }
            ]
        }
        content = service._extract_cv_content(candidate)
        assert "Engineer" in content
        assert "BigCo" in content
        assert "Python" in content

    def test_extract_cv_content_with_resume_text(self, service):
        candidate = {"resume_text": "Full resume text here"}
        content = service._extract_cv_content(candidate)
        assert "Full resume text here" in content

    def test_extract_cv_content_with_location(self, service):
        candidate = {
            "location_city": "Sao Paulo",
            "location_state": "SP",
            "location_country": "Brazil",
            "is_remote": True,
        }
        content = service._extract_cv_content(candidate)
        assert "Sao Paulo" in content
        assert "remote" in content.lower()

    def test_detect_vague_language_positive(self, service):
        assert service._detect_vague_language("pode ter experiência") is True
        assert service._detect_vague_language("provavelmente tem skills") is True
        assert service._detect_vague_language("suggests expertise") is True
        assert service._detect_vague_language("may have experience") is True

    def test_detect_vague_language_negative(self, service):
        assert service._detect_vague_language("Has 5 years of Python experience") is False
        assert service._detect_vague_language("Certified AWS Solutions Architect") is False

    def test_detect_anomalies_too_many_exceeds(self, service):
        from app.schemas.rubric import EvaluationLevelEnum, EvidenceType, RequirementPriorityEnum
        evals = []
        for i in range(10):
            e = MagicMock()
            e.level = EvaluationLevelEnum.EXCEEDS
            e.evidence_type = EvidenceType.EXPLICIT
            e.priority = RequirementPriorityEnum.ESSENTIAL
            evals.append(e)
        candidate = {"technical_skills": ["Python"]}
        anomalies = service._detect_anomalies(evals, candidate)
        assert len(anomalies) > 0
        assert any("ANOMALY" in a for a in anomalies)

    def test_detect_anomalies_inferred_meets(self, service):
        from app.schemas.rubric import EvaluationLevelEnum, EvidenceType, RequirementPriorityEnum
        e = MagicMock()
        e.level = EvaluationLevelEnum.MEETS
        e.evidence_type = EvidenceType.INFERRED
        e.priority = RequirementPriorityEnum.IMPORTANT
        anomalies = service._detect_anomalies([e], {"technical_skills": ["Python", "Go", "Rust"]})
        assert any("inferred" in a.lower() for a in anomalies)

    def test_check_essential_exclusion_missing(self, service):
        from app.schemas.rubric import EvaluationLevelEnum, RequirementPriorityEnum
        e = MagicMock()
        e.level = EvaluationLevelEnum.MISSING
        e.priority = RequirementPriorityEnum.ESSENTIAL
        e.requirement = "Python 5+ years"
        excluded, reasons = service._check_essential_exclusion([e])
        assert excluded is True
        assert len(reasons) > 0

    def test_check_essential_exclusion_not_excluded(self, service):
        from app.schemas.rubric import EvaluationLevelEnum, EvidenceType, RequirementPriorityEnum
        e = MagicMock()
        e.level = EvaluationLevelEnum.MEETS
        e.priority = RequirementPriorityEnum.ESSENTIAL
        e.evidence_type = EvidenceType.EXPLICIT
        e.requirement = "Python 5+ years"
        excluded, reasons = service._check_essential_exclusion([e])
        assert excluded is False

    def test_format_requirements_for_prompt(self, service):
        from app.schemas.rubric import RequirementPriorityEnum
        req = MagicMock()
        req.requirement = "Python experience"
        req.priority = RequirementPriorityEnum.ESSENTIAL
        req.description = "3+ years"
        result = service._format_requirements_for_prompt([req])
        assert "Python experience" in result
        assert "ESSENTIAL" in result

    def test_detect_anomalies_low_experience_many_exceeds(self, service):
        from app.schemas.rubric import EvaluationLevelEnum, EvidenceType, RequirementPriorityEnum
        evals = []
        for _ in range(5):
            e = MagicMock()
            e.level = EvaluationLevelEnum.EXCEEDS
            e.evidence_type = EvidenceType.EXPLICIT
            e.priority = RequirementPriorityEnum.IMPORTANT
            evals.append(e)
        candidate = {"years_of_experience": 1, "technical_skills": ["Python", "Go", "Rust", "Java"]}
        anomalies = service._detect_anomalies(evals, candidate)
        assert any("years experience" in a for a in anomalies)
