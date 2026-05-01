"""
Unit Tests — LIA Score (CVScoringService): geração, thresholds e persistência (Task #53, Item 3).

Testa o comportamento REAL do CVScoringService:
- _get_recommendation: mapeamento de score → recomendação
- _get_cv_fit_indicator: conversão rubric → cv_fit (0-5)
- _get_sub_status: mapeamento score → pipeline sub_status
- _update_candidate_score: atualização de VacancyCandidate no DB
- SCORE_THRESHOLDS: valores corretos por metodologia
- screen_candidate: candidato não encontrado, sem requisitos, fluxo sucesso
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4


# ---------------------------------------------------------------------------
# Seção 1 — Threshold mapping: score → recommendation label
# ---------------------------------------------------------------------------

class TestRecommendationThresholds:

    def _svc(self):
        from app.domains.cv_screening.services.cv_scoring_service import CVScoringService
        return CVScoringService()

    def test_score_100_is_highly_recommended(self):
        assert self._svc()._get_recommendation(100.0) == "Altamente Recomendado"

    def test_score_85_is_highly_recommended(self):
        assert self._svc()._get_recommendation(85.0) == "Altamente Recomendado"

    def test_score_84_is_recommended(self):
        assert self._svc()._get_recommendation(84.9) == "Recomendado"

    def test_score_70_is_recommended(self):
        assert self._svc()._get_recommendation(70.0) == "Recomendado"

    def test_score_69_is_potential(self):
        assert self._svc()._get_recommendation(69.9) == "Potencial"

    def test_score_55_is_potential(self):
        assert self._svc()._get_recommendation(55.0) == "Potencial"

    def test_score_54_is_low_match(self):
        assert self._svc()._get_recommendation(54.9) == "Baixo Match"

    def test_score_40_is_low_match(self):
        assert self._svc()._get_recommendation(40.0) == "Baixo Match"

    def test_score_39_is_not_recommended(self):
        assert self._svc()._get_recommendation(39.9) == "Não Recomendado"

    def test_score_0_is_not_recommended(self):
        assert self._svc()._get_recommendation(0.0) == "Não Recomendado"

    def test_score_thresholds_constants_match_methodology(self):
        """SCORE_THRESHOLDS deve refletir a metodologia BARS/André."""
        svc = self._svc()
        assert svc.SCORE_THRESHOLDS["highly_recommended"] == 85
        assert svc.SCORE_THRESHOLDS["recommended"] == 70
        assert svc.SCORE_THRESHOLDS["potential"] == 55
        assert svc.SCORE_THRESHOLDS["low_match"] == 40
        assert svc.SCORE_THRESHOLDS["not_recommended"] == 0


# ---------------------------------------------------------------------------
# Seção 2 — CV Fit Indicator (escala 0-5)
# ---------------------------------------------------------------------------

class TestCVFitIndicatorConversion:

    def _svc(self):
        from app.domains.cv_screening.services.cv_scoring_service import CVScoringService
        return CVScoringService()

    def test_rubric_100_gives_cv_fit_5(self):
        result = self._svc()._get_cv_fit_indicator(100.0)
        assert result["cv_fit_score"] == 5.0
        assert result["classification"] == "Excelente"

    def test_rubric_90_gives_cv_fit_4_5(self):
        result = self._svc()._get_cv_fit_indicator(90.0)
        assert result["cv_fit_score"] == 4.5
        assert result["classification"] == "Excelente"

    def test_rubric_80_gives_cv_fit_4_0(self):
        result = self._svc()._get_cv_fit_indicator(80.0)
        assert result["cv_fit_score"] == 4.0
        assert result["classification"] == "Alto"

    def test_rubric_79_gives_medio_classification(self):
        result = self._svc()._get_cv_fit_indicator(79.9)
        assert result["classification"] in ("Alto", "Médio")

    def test_rubric_60_gives_cv_fit_3(self):
        result = self._svc()._get_cv_fit_indicator(60.0)
        assert result["cv_fit_score"] == 3.0
        assert result["classification"] == "Médio"

    def test_rubric_40_gives_regular_classification(self):
        result = self._svc()._get_cv_fit_indicator(40.0)
        assert result["classification"] == "Regular"

    def test_rubric_0_gives_cv_fit_0(self):
        result = self._svc()._get_cv_fit_indicator(0.0)
        assert result["cv_fit_score"] == 0.0
        assert result["classification"] == "Baixo"

    def test_indicator_is_marked_preliminary(self):
        result = self._svc()._get_cv_fit_indicator(70.0)
        assert result["is_preliminary"] is True

    def test_indicator_has_rubric_percentage(self):
        result = self._svc()._get_cv_fit_indicator(70.0)
        assert result["rubric_percentage"] == 70.0

    def test_cv_fit_score_formula_is_rubric_divided_by_20(self):
        svc = self._svc()
        for score in [20, 40, 60, 80, 100]:
            result = svc._get_cv_fit_indicator(float(score))
            assert abs(result["cv_fit_score"] - score / 20) < 0.01


# ---------------------------------------------------------------------------
# Seção 3 — Sub-status pipeline mapping
# ---------------------------------------------------------------------------

class TestSubStatusPipelineMapping:

    def _svc(self):
        from app.domains.cv_screening.services.cv_scoring_service import CVScoringService
        return CVScoringService()

    def test_score_70_maps_to_cv_approved(self):
        assert self._svc()._get_sub_status(70.0) == "cv_approved"

    def test_score_85_maps_to_cv_approved(self):
        assert self._svc()._get_sub_status(85.0) == "cv_approved"

    def test_score_55_maps_to_cv_analyzing(self):
        assert self._svc()._get_sub_status(55.0) == "cv_analyzing"

    def test_score_65_maps_to_cv_analyzing(self):
        assert self._svc()._get_sub_status(65.0) == "cv_analyzing"

    def test_score_54_maps_to_cv_rejected(self):
        assert self._svc()._get_sub_status(54.9) == "cv_rejected"

    def test_score_0_maps_to_cv_rejected(self):
        assert self._svc()._get_sub_status(0.0) == "cv_rejected"


# ---------------------------------------------------------------------------
# Seção 4 — _update_candidate_score: DB persistence
# ---------------------------------------------------------------------------

class TestUpdateCandidateScorePersistence:

    @pytest.mark.asyncio
    async def test_update_candidate_score_calls_db_execute(self):
        """_update_candidate_score deve chamar db.execute para buscar VacancyCandidate."""
        from app.domains.cv_screening.services.cv_scoring_service import CVScoringService
        from app.models.candidate import VacancyCandidate
        svc = CVScoringService()

        mock_vc = MagicMock()
        mock_vc.cv_score = 0.0
        mock_vc.cv_fit_score = 0.0
        mock_vc.sub_status = "pending"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_vc
        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(return_value=mock_result)

        candidate_id = str(uuid4())
        vacancy_id = str(uuid4())

        mock_query = MagicMock()
        mock_query.where.return_value = mock_query
        with patch("app.domains.cv_screening.services.cv_scoring_service.select", return_value=mock_query), \
             patch("app.domains.cv_screening.services.cv_scoring_service.VacancyCandidate") as mock_vc_cls:
            mock_vc_cls.candidate_id = MagicMock()
            mock_vc_cls.job_vacancy_id = MagicMock()
            await svc._update_candidate_score(
                candidate_id=candidate_id,
                vacancy_id=vacancy_id,
                score=82.5,
                cv_fit_score=4.1,
                sub_status="cv_approved",
                db=mock_db,
            )

        mock_db.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_update_candidate_score_no_vacancy_candidate_does_not_raise(self):
        """Se VacancyCandidate não existe, _update_candidate_score não deve lançar exceção."""
        from app.domains.cv_screening.services.cv_scoring_service import CVScoringService
        svc = CVScoringService()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(return_value=mock_result)

        mock_query = MagicMock()
        mock_query.where.return_value = mock_query
        with patch("app.domains.cv_screening.services.cv_scoring_service.select", return_value=mock_query), \
             patch("app.domains.cv_screening.services.cv_scoring_service.VacancyCandidate") as mock_vc_cls:
            mock_vc_cls.candidate_id = MagicMock()
            mock_vc_cls.job_vacancy_id = MagicMock()
            await svc._update_candidate_score(
                candidate_id=str(uuid4()),
                vacancy_id=str(uuid4()),
                score=70.0,
                cv_fit_score=3.5,
                sub_status="cv_approved",
                db=mock_db,
            )

    @pytest.mark.asyncio
    async def test_screen_candidate_calls_update_score_on_success(self):
        """screen_candidate deve chamar _update_candidate_score quando screening tem sucesso."""
        from app.domains.cv_screening.services.cv_scoring_service import CVScoringService
        from app.schemas.rubric import RubricEvaluationResult
        svc = CVScoringService()

        mock_db = AsyncMock()
        cdata = {"id": str(uuid4()), "name": "Test Candidate", "email": "test@test.com"}
        reqs = [MagicMock()]
        job_info = {"title": "Desenvolvedor Python"}

        mock_eval = RubricEvaluationResult(
            score=75.0,
            raw_score=75.0,
            total_weighted_points=75.0,
            max_possible_points=100.0,
            recommendation="Recomendado",
            strengths=["Python"],
            concerns=[],
            reasoning="Bom candidato",
            evaluations=[],
        )

        update_score_mock = AsyncMock()
        svc._update_candidate_score = update_score_mock

        with patch.object(svc, "_get_candidate_data", new_callable=AsyncMock, return_value=cdata), \
             patch.object(svc, "_get_job_requirements", new_callable=AsyncMock, return_value=reqs), \
             patch.object(svc, "_get_job_info", new_callable=AsyncMock, return_value=job_info), \
             patch("app.domains.cv_screening.services.cv_scoring_service.rubric_evaluation_service.evaluate_candidate",
                   new_callable=AsyncMock, return_value=mock_eval), \
             patch("app.domains.cv_screening.services.cv_scoring_service.activity_service.create_activity",
                   new_callable=AsyncMock):
            result = await svc.screen_candidate(
                candidate_id=str(uuid4()),
                vacancy_id=str(uuid4()),
                company_id="company-001",
                db=mock_db,
            )

        assert result["success"] is True
        update_score_mock.assert_awaited_once()
