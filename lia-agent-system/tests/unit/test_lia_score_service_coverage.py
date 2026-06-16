"""
Unit tests for app.services.lia_score_service
Covers pure functions/methods that don't require DB connections.
"""
import pytest
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from unittest.mock import MagicMock, patch

from app.shared.services.lia_score_service import (
    LIAScoreService,
    LIAScoreBreakdown,
    LIAScoreResult,
    RankingScoreBreakdown,
    RankingScoreResult,
    DataAvailability,
    WEIGHT_DISTRIBUTION,
    RECENCY_BOOST_THRESHOLDS,
    RECENCY_BOOST_DEFAULT,
    SeniorityLevel,
    SENIORITY_ALIASES,
    SENIORITY_YEARS_MAP,
)


class TestDataAvailabilityEnum:
    def test_values(self):
        assert DataAvailability.CV_WSI_PREREQ.value == "cv_wsi_prereq"
        assert DataAvailability.CV_PREREQ.value == "cv_prereq"
        assert DataAvailability.CV_ONLY.value == "cv_only"

    def test_weight_distribution_keys(self):
        for da in DataAvailability:
            assert da in WEIGHT_DISTRIBUTION

    def test_weights_sum_to_one_for_cv_wsi_prereq(self):
        w = WEIGHT_DISTRIBUTION[DataAvailability.CV_WSI_PREREQ]
        total = sum(w.values())
        assert abs(total - 1.0) < 0.001


class TestRankingScoreBreakdown:
    def _make_breakdown(self, **kwargs):
        defaults = dict(
            rubricas_score=80.0,
            wsi_score=70.0,
            prerequisites_score=90.0,
            recency_boost=60.0,
            calibration_adjustment=2.0,
            completeness_factor=0.9,
            weights_used={"rubricas": 0.4, "wsi": 0.25, "prereq": 0.15, "recency": 0.1},
            data_availability="cv_wsi_prereq",
            weighted_rubricas=32.0,
            weighted_wsi=17.5,
            weighted_prereq=13.5,
            weighted_recency=6.0,
        )
        defaults.update(kwargs)
        return RankingScoreBreakdown(**defaults)

    def test_calculate_raw_score(self):
        b = self._make_breakdown(
            weighted_rubricas=32.0,
            weighted_wsi=17.5,
            weighted_prereq=13.5,
            weighted_recency=6.0,
            calibration_adjustment=2.0,
        )
        raw = b.calculate_raw_score()
        assert abs(raw - 71.0) < 0.01

    def test_calculate_final_score_applies_completeness(self):
        b = self._make_breakdown(
            weighted_rubricas=40.0,
            weighted_wsi=25.0,
            weighted_prereq=15.0,
            weighted_recency=10.0,
            calibration_adjustment=0.0,
            completeness_factor=0.8,
        )
        final = b.calculate_final_score()
        assert abs(final - 72.0) < 0.01  # 90 * 0.8

    def test_final_score_clamped_to_100(self):
        b = self._make_breakdown(
            weighted_rubricas=80.0,
            weighted_wsi=80.0,
            weighted_prereq=80.0,
            weighted_recency=80.0,
            calibration_adjustment=5.0,
            completeness_factor=1.0,
        )
        assert b.calculate_final_score() == 100.0

    def test_final_score_clamped_to_zero(self):
        b = self._make_breakdown(
            weighted_rubricas=-200.0,
            weighted_wsi=0.0,
            weighted_prereq=0.0,
            weighted_recency=0.0,
            calibration_adjustment=-5.0,
            completeness_factor=1.0,
        )
        assert b.calculate_final_score() == 0.0

    def test_to_dict_keys(self):
        b = self._make_breakdown()
        d = b.to_dict()
        assert "rubricas_score" in d
        assert "wsi_score" in d
        assert "prerequisites_score" in d
        assert "recency_boost" in d
        assert "calibration_adjustment" in d
        assert "completeness_factor" in d
        assert "final_score" in d
        assert "raw_score" in d

    def test_to_dict_wsi_none(self):
        b = self._make_breakdown(wsi_score=None)
        d = b.to_dict()
        assert d["wsi_score"] is None


class TestLIAScoreBreakdown:
    def test_total_score_with_defaults(self):
        bd = LIAScoreBreakdown(
            skills_match=80.0,
            experience_match=70.0,
            seniority_match=100.0,
            location_match=90.0,
            title_match=60.0,
        )
        # default weights: 0.35, 0.20, 0.15, 0.15, 0.15
        expected = 80 * 0.35 + 70 * 0.20 + 100 * 0.15 + 90 * 0.15 + 60 * 0.15
        assert abs(bd.total_score() - expected) < 0.01

    def test_to_dict_rounds(self):
        bd = LIAScoreBreakdown(
            skills_match=80.12345,
            experience_match=70.0,
            seniority_match=100.0,
            location_match=90.0,
            title_match=60.0,
        )
        d = bd.to_dict()
        assert d["skills_match"] == round(80.12345, 1)


class TestLIAScoreService:
    def setup_method(self):
        self.svc = LIAScoreService()

    def test_skill_synonyms_built(self):
        assert "javascript" in self.svc.skill_synonyms
        assert "js" in self.svc.skill_synonyms["javascript"]

    def test_normalize_skill_synonym(self):
        assert self.svc._normalize_skill("JS") == "javascript"
        assert self.svc._normalize_skill("k8s") == "kubernetes"

    def test_normalize_skill_unknown(self):
        assert self.svc._normalize_skill("SomeUnknownSkill") == "someunknownskill"

    def test_extract_skills_from_query(self):
        skills = self.svc._extract_skills_from_query("Precisa de Python e React")
        assert "python" in skills

    def test_extract_skills_empty_query(self):
        skills = self.svc._extract_skills_from_query("")
        assert skills == []

    def test_extract_experience_years_pattern(self):
        years = self.svc._extract_experience_years_from_query("5 anos de experiência")
        assert years == 5

    def test_extract_experience_years_no_match(self):
        years = self.svc._extract_experience_years_from_query("bom comunicador")
        assert years is None

    def test_extract_seniority_from_query(self):
        level = self.svc._extract_seniority_from_query("desenvolvedor senior")
        assert level == SeniorityLevel.SENIOR

    def test_extract_seniority_junior(self):
        level = self.svc._extract_seniority_from_query("vaga junior")
        assert level == SeniorityLevel.JUNIOR

    def test_extract_seniority_not_found(self):
        level = self.svc._extract_seniority_from_query("recrutamento")
        assert level is None

    def test_extract_location_remote(self):
        loc = self.svc._extract_location_from_query("trabalho remoto")
        assert loc == "remoto"

    def test_extract_location_sao_paulo(self):
        loc = self.svc._extract_location_from_query("vaga em são paulo")
        assert loc == "são paulo"

    def test_extract_location_not_found(self):
        loc = self.svc._extract_location_from_query("bom salário")
        assert loc is None

    def test_calculate_skills_match_all(self):
        pct, matched, missing = self.svc._calculate_skills_match(
            ["python", "react", "docker"],
            ["python", "react"],
        )
        assert pct == 100.0
        assert len(missing) == 0

    def test_calculate_skills_match_none_required(self):
        pct, matched, missing = self.svc._calculate_skills_match(["python"], [])
        assert pct == 100.0

    def test_calculate_skills_match_partial(self):
        pct, matched, missing = self.svc._calculate_skills_match(
            ["python"],
            ["python", "react", "docker"],
        )
        assert pct < 100.0
        assert len(missing) > 0

    def test_calculate_experience_no_requirement(self):
        score = self.svc._calculate_experience_match(3.0, None)
        assert score == 100.0

    def test_calculate_experience_exact_match(self):
        score = self.svc._calculate_experience_match(5.0, 5)
        assert score == 100.0

    def test_calculate_experience_below_80_pct(self):
        score = self.svc._calculate_experience_match(4.0, 5)  # 80%
        assert score == 85.0

    def test_calculate_experience_unknown_candidate(self):
        score = self.svc._calculate_experience_match(None, 5)
        assert score == 50.0

    def test_calculate_seniority_exact(self):
        score = self.svc._calculate_seniority_match("senior", None, SeniorityLevel.SENIOR)
        assert score == 100.0

    def test_calculate_seniority_no_requirement(self):
        score = self.svc._calculate_seniority_match("junior", None, None)
        assert score == 100.0

    def test_calculate_seniority_inferred_from_years(self):
        # 7 years → SENIOR range
        score = self.svc._calculate_seniority_match(None, 7.0, SeniorityLevel.SENIOR)
        assert score == 100.0

    def test_calculate_seniority_unknown(self):
        score = self.svc._calculate_seniority_match(None, None, SeniorityLevel.SENIOR)
        assert score == 50.0

    def test_calculate_location_no_requirement(self):
        score = self.svc._calculate_location_match("São Paulo", False, None)
        assert score == 100.0

    def test_calculate_location_remote_candidate_ok(self):
        score = self.svc._calculate_location_match(None, True, "remoto")
        assert score == 100.0

    def test_calculate_location_remote_not_available(self):
        score = self.svc._calculate_location_match("São Paulo", False, "remoto")
        assert score == 70.0

    def test_calculate_location_city_match(self):
        score = self.svc._calculate_location_match("São Paulo", False, "são paulo")
        assert score == 100.0

    def test_calculate_title_no_candidate_title(self):
        score = self.svc._calculate_title_match(None, "python developer")
        assert score == 50.0

    def test_calculate_title_exact_keyword_match(self):
        score = self.svc._calculate_title_match("Senior Developer", "developer")
        assert score == 100.0

    def test_calculate_title_no_query_keywords(self):
        score = self.svc._calculate_title_match("Some Title", "looking for talent")
        assert score == 80.0

    def test_calculate_score_full(self):
        candidate = {
            "skills": ["python", "react"],
            "total_experience_years": 5,
            "seniority_level": "senior",
            "location": "São Paulo",
            "is_remote": False,
            "current_title": "Senior Developer",
        }
        criteria = {"query": "python developer senior", "filters": {}}
        result = self.svc.calculate_score(candidate, criteria)
        assert isinstance(result, LIAScoreResult)
        assert 0 <= result.score <= 100

    def test_calculate_scores_batch_sorted(self):
        candidates = [
            {"skills": [], "total_experience_years": 1},
            {"skills": ["python", "react", "docker"], "total_experience_years": 8},
        ]
        criteria = {"query": "python developer senior", "filters": {}}
        results = self.svc.calculate_scores_batch(candidates, criteria)
        scores = [r[1].score for r in results]
        assert scores[0] >= scores[1]

    def test_calculate_scores_batch_no_sort(self):
        candidates = [
            {"skills": ["python"], "total_experience_years": 5},
        ]
        criteria = {"query": "python", "filters": {}}
        results = self.svc.calculate_scores_batch(candidates, criteria, sort_by_score=False)
        assert len(results) == 1

    def test_generate_reasoning_high_score(self):
        bd = LIAScoreBreakdown(
            skills_match=90.0, experience_match=90.0,
            seniority_match=90.0, location_match=90.0, title_match=90.0,
        )
        reasoning = self.svc._generate_reasoning(90.0, bd, ["python", "react"], [])
        assert "Excelente" in reasoning

    def test_generate_reasoning_low_score(self):
        bd = LIAScoreBreakdown(
            skills_match=20.0, experience_match=20.0,
            seniority_match=20.0, location_match=20.0, title_match=20.0,
        )
        reasoning = self.svc._generate_reasoning(20.0, bd, [], ["python"])
        assert "Baixa" in reasoning
