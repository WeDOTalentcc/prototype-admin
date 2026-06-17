"""
Integration Tests — Pipeline CV Screening: rubric scoring, auto-exclusion, ranking.

Exercita o comportamento REAL de:
- RubricEvaluationService._calculate_score(): André's formula (evidence weights + multipliers)
- RubricEvaluationService._check_essential_exclusion(): auto-exclusão por essential missing
- RubricEvaluationService._get_recommendation_action(): score→action thresholds
- EvidenceType weights: explicit=1.0, implicit=0.7, inferred=0.3
- RequirementPriorityEnum multipliers: ESSENTIAL=3, IMPORTANT=2, NICE_TO_HAVE=1
- Auto-exclusion: essential+missing OR essential+non-explicit evidence triggers exclusion
- CVParserService._fallback_extraction(): estrutura ParsedCV sem LLM
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.domains.cv_screening.services.rubric_evaluation_service import (
    RubricEvaluationService,
    EvidenceType,
    EvaluationLevelEnum,
)
from app.schemas.rubric import (
    RubricEvaluationResult,
    RequirementEvaluation,
    RequirementPriorityEnum,
)


# ---------------------------------------------------------------------------
# Helper: build a RequirementEvaluation with André's formula fields
# ---------------------------------------------------------------------------

def _eval(
    requirement: str = "Req",
    priority: RequirementPriorityEnum = RequirementPriorityEnum.IMPORTANT,
    level: EvaluationLevelEnum = EvaluationLevelEnum.MEETS,
    evidence_type: EvidenceType = EvidenceType.EXPLICIT,
    points: int = 75,
    multiplier: int = 2,
) -> RequirementEvaluation:
    return RequirementEvaluation(
        requirement=requirement,
        priority=priority,
        level=level,
        evidence_type=evidence_type,
        confidence=1.0,
        points=points,
        multiplier=multiplier,
        weighted_points=float(points * multiplier),
        max_weighted_points=float(100 * multiplier),
        evidence="Evidência explícita no CV",
        reasoning="Atende ao critério",
    )


# ---------------------------------------------------------------------------
# Seção 1 — _calculate_score(): André's formula
# ---------------------------------------------------------------------------

class TestCalculateScoreFormula:

    def _svc(self) -> RubricEvaluationService:
        svc = RubricEvaluationService.__new__(RubricEvaluationService)
        return svc

    def test_single_exceeds_explicit_scores_close_to_100(self):
        """EXCEEDS explícito (100pts × 1.0 weight × mul2) → score ~ 100."""
        svc = self._svc()
        evals = [_eval(level=EvaluationLevelEnum.EXCEEDS, evidence_type=EvidenceType.EXPLICIT,
                       points=100, multiplier=2)]
        score, total_w, max_p, raw = svc._calculate_score(evals)
        # total_adjusted_weighted = 100 * 1.0 * 2 = 200, max = 200 → 100%
        assert score >= 95.0, f"Expected >= 95.0, got {score}"

    def test_inferred_evidence_reduces_score_vs_explicit(self):
        """MEETS inferred (×0.3) deve ter score menor que MEETS explicit (×1.0)."""
        svc = self._svc()
        ev_explicit = [_eval(evidence_type=EvidenceType.EXPLICIT, points=75, multiplier=2)]
        ev_inferred = [_eval(evidence_type=EvidenceType.INFERRED, points=75, multiplier=2)]

        score_explicit, *_ = svc._calculate_score(ev_explicit)
        score_inferred, *_ = svc._calculate_score(ev_inferred)

        assert score_inferred < score_explicit, \
            f"Inferred ({score_inferred}) should be < explicit ({score_explicit})"

    def test_implicit_evidence_between_explicit_and_inferred(self):
        """Implicit (×0.7) deve estar entre explicit (×1.0) e inferred (×0.3)."""
        svc = self._svc()
        ev_ex, *_ = svc._calculate_score([_eval(evidence_type=EvidenceType.EXPLICIT, points=75)])
        ev_im, *_ = svc._calculate_score([_eval(evidence_type=EvidenceType.IMPLICIT, points=75)])
        ev_in, *_ = svc._calculate_score([_eval(evidence_type=EvidenceType.INFERRED, points=75)])
        assert ev_in < ev_im < ev_ex, \
            f"Expected inferred({ev_in}) < implicit({ev_im}) < explicit({ev_ex})"

    def test_essential_multiplier_3_outweighs_nice_to_have_multiplier_1(self):
        """ESSENTIAL (multiplier=3) deve pesar mais que NICE_TO_HAVE (multiplier=1)."""
        svc = self._svc()
        ev_essential = [
            _eval(priority=RequirementPriorityEnum.ESSENTIAL, points=75, multiplier=3)
        ]
        ev_nicetohave = [
            _eval(priority=RequirementPriorityEnum.NICE_TO_HAVE, points=75, multiplier=1)
        ]
        # Both should give same percentage (75/100 = 75%) since formula normalizes
        score_ess, tw_ess, mp_ess, _ = svc._calculate_score(ev_essential)
        score_n2h, tw_n2h, mp_n2h, _ = svc._calculate_score(ev_nicetohave)
        # max_possible_points should differ by 3x
        assert mp_ess == mp_n2h * 3

    def test_empty_evaluations_returns_all_zeros(self):
        """Lista vazia → (0.0, 0.0, 0.0, 0.0)."""
        svc = self._svc()
        result = svc._calculate_score([])
        assert result == (0.0, 0.0, 0.0, 0.0)

    def test_all_missing_explicit_returns_score_zero(self):
        """MISSING com 0pts explícitos → score = 0."""
        svc = self._svc()
        evals = [
            _eval(level=EvaluationLevelEnum.MISSING,
                  evidence_type=EvidenceType.EXPLICIT,
                  points=0, multiplier=2),
        ]
        score, *_ = svc._calculate_score(evals)
        assert score == 0.0

    def test_mixed_evaluations_produces_intermediate_score(self):
        """MEETS+MISSING mix → score entre 0 e 100."""
        svc = self._svc()
        evals = [
            _eval(level=EvaluationLevelEnum.MEETS, points=75, multiplier=2,
                  evidence_type=EvidenceType.EXPLICIT),
            _eval(level=EvaluationLevelEnum.MISSING, points=0, multiplier=2,
                  evidence_type=EvidenceType.EXPLICIT),
        ]
        score, *_ = svc._calculate_score(evals)
        assert 0 < score < 80


# ---------------------------------------------------------------------------
# Seção 2 — _check_essential_exclusion(): auto-exclusion logic
# ---------------------------------------------------------------------------

class TestCheckEssentialExclusion:

    def _svc(self) -> RubricEvaluationService:
        return RubricEvaluationService.__new__(RubricEvaluationService)

    def test_essential_missing_triggers_auto_exclusion(self):
        """ESSENTIAL + MISSING → auto_excluded=True."""
        svc = self._svc()
        evals = [
            _eval(requirement="Python 5+ anos",
                  priority=RequirementPriorityEnum.ESSENTIAL,
                  level=EvaluationLevelEnum.MISSING,
                  evidence_type=EvidenceType.EXPLICIT,
                  points=0, multiplier=3),
        ]
        excluded, reasons = svc._check_essential_exclusion(evals)
        assert excluded is True
        assert len(reasons) > 0
        assert "essencial" in reasons[0].lower() or "Python" in reasons[0]

    def test_essential_meets_explicit_does_not_trigger_exclusion(self):
        """ESSENTIAL + MEETS + EXPLICIT → não exclui."""
        svc = self._svc()
        evals = [
            _eval(requirement="Python 5+ anos",
                  priority=RequirementPriorityEnum.ESSENTIAL,
                  level=EvaluationLevelEnum.MEETS,
                  evidence_type=EvidenceType.EXPLICIT,
                  points=75, multiplier=3),
        ]
        excluded, reasons = svc._check_essential_exclusion(evals)
        assert excluded is False
        assert reasons == []

    def test_essential_meets_inferred_triggers_exclusion(self):
        """ESSENTIAL + MEETS + INFERRED (não explicit) → auto_excluded=True."""
        svc = self._svc()
        evals = [
            _eval(requirement="Python 5+ anos",
                  priority=RequirementPriorityEnum.ESSENTIAL,
                  level=EvaluationLevelEnum.MEETS,
                  evidence_type=EvidenceType.INFERRED,
                  points=75, multiplier=3),
        ]
        excluded, reasons = svc._check_essential_exclusion(evals)
        assert excluded is True
        assert any("inferred" in r.lower() or "implíc" in r.lower() or "evidência" in r.lower()
                   for r in reasons)

    def test_important_missing_does_not_trigger_exclusion(self):
        """IMPORTANT + MISSING → não exclui (apenas essential dispara)."""
        svc = self._svc()
        evals = [
            _eval(requirement="Docker",
                  priority=RequirementPriorityEnum.IMPORTANT,
                  level=EvaluationLevelEnum.MISSING,
                  evidence_type=EvidenceType.EXPLICIT,
                  points=0, multiplier=2),
        ]
        excluded, reasons = svc._check_essential_exclusion(evals)
        assert excluded is False

    def test_multiple_essential_failures_produces_multiple_reasons(self):
        """Dois essential MISSING → dois motivos de exclusão."""
        svc = self._svc()
        evals = [
            _eval("Python 5+ anos",
                  priority=RequirementPriorityEnum.ESSENTIAL,
                  level=EvaluationLevelEnum.MISSING,
                  points=0, multiplier=3),
            _eval("AWS Certified",
                  priority=RequirementPriorityEnum.ESSENTIAL,
                  level=EvaluationLevelEnum.MISSING,
                  points=0, multiplier=3),
        ]
        excluded, reasons = svc._check_essential_exclusion(evals)
        assert excluded is True
        assert len(reasons) == 2


# ---------------------------------------------------------------------------
# Seção 3 — _get_recommendation_action(): score thresholds
# ---------------------------------------------------------------------------

class TestRecommendationAction:

    def _svc(self) -> RubricEvaluationService:
        return RubricEvaluationService.__new__(RubricEvaluationService)

    def test_score_85_plus_recommends_interview(self):
        """Score >= 85 → 'interview'."""
        svc = self._svc()
        assert svc._get_recommendation_action(90.0) == "interview"
        assert svc._get_recommendation_action(85.0) == "interview"

    def test_score_70_to_84_recommends_interview(self):
        """Score 70-84 → 'interview'."""
        svc = self._svc()
        assert svc._get_recommendation_action(75.0) == "interview"
        assert svc._get_recommendation_action(70.0) == "interview"

    def test_score_55_to_69_recommends_review(self):
        """Score 55-69 → 'review'."""
        svc = self._svc()
        assert svc._get_recommendation_action(60.0) == "review"
        assert svc._get_recommendation_action(55.0) == "review"

    def test_score_below_55_recommends_reject(self):
        """Score < 55 → 'reject'."""
        svc = self._svc()
        assert svc._get_recommendation_action(50.0) == "reject"
        assert svc._get_recommendation_action(0.0) == "reject"

    def test_boundary_at_70_is_interview(self):
        """Exatamente 70 deve retornar 'interview'."""
        svc = self._svc()
        assert svc._get_recommendation_action(70.0) == "interview"

    def test_boundary_at_55_is_review(self):
        """Exatamente 55 deve retornar 'review'."""
        svc = self._svc()
        assert svc._get_recommendation_action(55.0) == "review"

    def test_boundary_below_55_is_reject(self):
        """54.99 deve retornar 'reject'."""
        svc = self._svc()
        assert svc._get_recommendation_action(54.99) == "reject"


# ---------------------------------------------------------------------------
# Seção 4 — RubricEvaluationResult schema: required fields
# ---------------------------------------------------------------------------

class TestRubricEvaluationResultSchema:

    def _make_result(self, **kwargs) -> RubricEvaluationResult:
        """Build a RubricEvaluationResult with required fields."""
        defaults = {
            "score": 75.0,
            "total_weighted_points": 150.0,
            "max_possible_points": 200.0,
            "evaluations": [],
            "recommendation": "Alto Match",
            "reasoning": "Candidato atende aos critérios principais.",
            "auto_excluded": False,
            "exclusion_reasons": [],
        }
        defaults.update(kwargs)
        return RubricEvaluationResult(**defaults)

    def test_result_requires_total_and_max_points(self):
        """RubricEvaluationResult com campos mínimos deve ser construído sem erro."""
        result = self._make_result(score=75.0, total_weighted_points=150.0, max_possible_points=200.0)
        assert result.score == 75.0
        assert result.total_weighted_points == 150.0
        assert result.max_possible_points == 200.0

    def test_score_is_capped_at_99(self):
        """Score acima de 99 deve lançar erro (Cap 99 da metodologia André)."""
        with pytest.raises(Exception):
            self._make_result(score=100.0)

    def test_auto_excluded_false_by_default(self):
        """auto_excluded deve ser aceito como False."""
        result = self._make_result(score=50.0, recommendation="Baixo Match", auto_excluded=False)
        assert result.auto_excluded is False

    def test_auto_excluded_result_has_exclusion_reasons(self):
        """Resultado com auto_excluded=True deve ter reasons não-vazia."""
        result = self._make_result(
            score=0.0,
            total_weighted_points=0.0,
            recommendation="Excluído",
            auto_excluded=True,
            exclusion_reasons=["Python essencial não atendido"],
        )
        assert result.auto_excluded is True
        assert len(result.exclusion_reasons) == 1


# ---------------------------------------------------------------------------
# Seção 5 — CVParserService: fallback extraction structure
# ---------------------------------------------------------------------------

class TestCVParserFallbackExtraction:

    @pytest.mark.asyncio
    async def test_fallback_extraction_returns_parsedcv_without_llm(self):
        """_fallback_extraction com texto simples deve retornar ParsedCV válido."""
        from app.domains.cv_screening.services.cv_parser import CVParserService
        from app.schemas.cv_parser import ParsedCV

        svc = CVParserService.__new__(CVParserService)
        text = "João Silva\njsilva@email.com\n+5511999999999\nPython, SQL\nUniversidade de São Paulo"

        result = await svc._fallback_extraction(text)

        assert isinstance(result, ParsedCV)
        # ParsedCV uses full_name (not name) and email/phone as optional fields
        assert hasattr(result, "full_name")
        assert result.full_name is not None  # Should have extracted something

    @pytest.mark.asyncio
    async def test_fallback_extraction_does_not_crash_on_empty_text(self):
        """_fallback_extraction com texto vazio não deve lançar exceção."""
        from app.domains.cv_screening.services.cv_parser import CVParserService
        from app.schemas.cv_parser import ParsedCV

        svc = CVParserService.__new__(CVParserService)
        result = await svc._fallback_extraction("")
        assert isinstance(result, ParsedCV)


# ---------------------------------------------------------------------------
# Seção 8 — CVScoringService E2E Pipeline: upload → parse → score → rank
#
# Testa o FLUXO REAL de ponta-a-ponta (com serviços externos mockados):
#   1. CVParserService.extract_with_ai() → ParsedCV (LLM mocked)
#   2. CVScoringService.screen_candidate() → dict com rubric_score + recommendation
#   3. Lógica de ranking determinística: score → recommendation label
# ---------------------------------------------------------------------------

class TestCVScreeningPipelineE2E:
    """
    End-to-end pipeline test for CV screening.

    Verifica que o pipeline completo:
    - Upload de texto de CV → CVParserService extrai ParsedCV via LLM (mocked)
    - CVScoringService orquestra rubric evaluation e retorna resultado determinístico
    - Recomendação é determinada pelos thresholds configurados (não por LLM)
    """

    def _make_rubric_evaluation_result(
        self,
        score: float,
        recommendation: str = "Recomendado",
    ):
        """Build a RubricEvaluationResult for a given score."""
        from app.schemas.rubric import (
            RubricEvaluationResult,
            RequirementEvaluation,
            RequirementPriorityEnum,
            EvaluationLevelEnum,
            EvidenceType,
        )
        eval_item = RequirementEvaluation(
            requirement="Experiência com Python",
            priority=RequirementPriorityEnum.ESSENTIAL,
            level=EvaluationLevelEnum.MEETS,
            evidence_type=EvidenceType.EXPLICIT,
            confidence=1.0,
            points=75,
            multiplier=3,
            weighted_points=225.0,
            max_weighted_points=300.0,
            evidence="Candidato menciona 5 anos de Python em produção.",
        )
        return RubricEvaluationResult(
            score=min(score, 99),
            raw_score=score,
            total_weighted_points=225.0,
            max_possible_points=300.0,
            evaluations=[eval_item],
            strengths=["Sólida experiência Python"],
            concerns=[],
            reasoning="Candidato atende os requisitos essenciais com evidências explícitas.",
            recommendation=recommendation,
        )

    @pytest.mark.asyncio
    async def test_screen_candidate_returns_success_dict_with_rubric_score(self):
        """
        screen_candidate deve retornar dict com success=True e rubric_score
        quando candidato e requisitos são encontrados (DB + RubricEvaluation mocked).
        """
        from app.domains.cv_screening.services.cv_scoring_service import CVScoringService
        from app.domains.cv_screening.services.rubric_evaluation_service import (
            rubric_evaluation_service,
        )

        svc = CVScoringService()

        candidate_data = {
            "name": "Maria Teste",
            "email": "maria@test.com",
            "skills": ["Python", "SQL", "Docker"],
            "experience_years": 5,
            "summary": "Engenheira de software com 5 anos de experiência em Python.",
        }

        from app.schemas.rubric import JobRequirementCreate, RequirementPriorityEnum
        requirements = [
            JobRequirementCreate(
                requirement="Experiência com Python (5+ anos)",
                priority=RequirementPriorityEnum.ESSENTIAL,
            )
        ]

        mock_eval = self._make_rubric_evaluation_result(score=78.0, recommendation="Recomendado")

        mock_db = AsyncMock()
        mock_db.commit = AsyncMock()
        mock_db.rollback = AsyncMock()
        mock_db.close = AsyncMock()

        with patch.object(svc, "_get_candidate_data", new_callable=AsyncMock, return_value=candidate_data), \
             patch.object(svc, "_get_job_requirements", new_callable=AsyncMock, return_value=requirements), \
             patch.object(svc, "_get_job_info", new_callable=AsyncMock, return_value={"title": "Eng. Software Sênior"}), \
             patch.object(svc, "_update_candidate_score", new_callable=AsyncMock), \
             patch(
                 "app.domains.cv_screening.services.cv_scoring_service.rubric_evaluation_service.evaluate_candidate",
                 new_callable=AsyncMock,
                 return_value=mock_eval,
             ), \
             patch(
                 "app.domains.cv_screening.services.cv_scoring_service.activity_service.create_activity",
                 new_callable=AsyncMock,
             ):
            result = await svc.screen_candidate(
                candidate_id="cand-pipeline-001",
                vacancy_id="job-pipeline-001",
                company_id="company-test",
                db=mock_db,
            )

        assert result["success"] is True, f"Expected success=True, got: {result}"
        assert result["candidate_id"] == "cand-pipeline-001"
        assert result["vacancy_id"] == "job-pipeline-001"
        assert result["rubric_score"] == 78.0
        assert "recommendation" in result
        assert "cv_fit" in result
        assert "methodology" in result

    @pytest.mark.asyncio
    async def test_screen_candidate_returns_failure_dict_when_candidate_not_found(self):
        """
        screen_candidate deve retornar dict com success=False e error='candidate_not_found'
        quando candidato não está no DB.
        """
        from app.domains.cv_screening.services.cv_scoring_service import CVScoringService

        svc = CVScoringService()
        mock_db = AsyncMock()
        mock_db.rollback = AsyncMock()
        mock_db.close = AsyncMock()

        with patch.object(svc, "_get_candidate_data", new_callable=AsyncMock, return_value=None):
            result = await svc.screen_candidate(
                candidate_id="nonexistent-cand",
                vacancy_id="job-001",
                company_id="company-test",
                db=mock_db,
            )

        assert result["success"] is False
        assert result["error"] == "candidate_not_found"

    @pytest.mark.asyncio
    async def test_screen_candidate_returns_failure_when_no_requirements(self):
        """
        screen_candidate deve retornar success=False com error='no_requirements'
        quando vaga não tem requisitos cadastrados.
        """
        from app.domains.cv_screening.services.cv_scoring_service import CVScoringService

        svc = CVScoringService()
        mock_db = AsyncMock()
        mock_db.rollback = AsyncMock()
        mock_db.close = AsyncMock()

        candidate_data = {"name": "João", "skills": ["Python"]}

        with patch.object(svc, "_get_candidate_data", new_callable=AsyncMock, return_value=candidate_data), \
             patch.object(svc, "_get_job_requirements", new_callable=AsyncMock, return_value=[]):
            result = await svc.screen_candidate(
                candidate_id="cand-001",
                vacancy_id="job-no-reqs",
                company_id="company-test",
                db=mock_db,
            )

        assert result["success"] is False
        assert result["error"] == "no_requirements"

    def test_get_cv_fit_indicator_score_85_is_highly_recommended(self):
        """Score 85+ → label 'Altamente Recomendado' (limiar alto)."""
        from app.domains.cv_screening.services.cv_scoring_service import CVScoringService
        svc = CVScoringService()
        result = svc._get_cv_fit_indicator(85.0)
        label = result.get("label", result.get("recommendation", ""))
        assert "recomendado" in label.lower() or result.get("cv_fit_score", 0) >= 4

    def test_get_cv_fit_indicator_score_30_is_not_recommended(self):
        """Score 30 → label baixo ou 'Não Recomendado'."""
        from app.domains.cv_screening.services.cv_scoring_service import CVScoringService
        svc = CVScoringService()
        result = svc._get_cv_fit_indicator(30.0)
        assert result.get("cv_fit_score", 5) <= 2

    @pytest.mark.asyncio
    async def test_pipeline_e2e_high_score_gets_aprovado_sub_status(self):
        """
        Pipeline completo: score >= 70 deve gerar sub_status='cv_approved'
        (mapeamento determinístico score → sub_status).
        """
        from app.domains.cv_screening.services.cv_scoring_service import CVScoringService

        svc = CVScoringService()
        mock_db = AsyncMock()
        mock_db.commit = AsyncMock()
        mock_db.rollback = AsyncMock()
        mock_db.close = AsyncMock()

        candidate_data = {"name": "Ana", "skills": ["Python", "AWS"]}
        from app.schemas.rubric import JobRequirementCreate, RequirementPriorityEnum
        requirements = [JobRequirementCreate(requirement="Python", priority=RequirementPriorityEnum.ESSENTIAL)]
        mock_eval = self._make_rubric_evaluation_result(score=88.0, recommendation="Altamente Recomendado")

        with patch.object(svc, "_get_candidate_data", new_callable=AsyncMock, return_value=candidate_data), \
             patch.object(svc, "_get_job_requirements", new_callable=AsyncMock, return_value=requirements), \
             patch.object(svc, "_get_job_info", new_callable=AsyncMock, return_value={"title": "SRE Sênior"}), \
             patch.object(svc, "_update_candidate_score", new_callable=AsyncMock), \
             patch(
                 "app.domains.cv_screening.services.cv_scoring_service.rubric_evaluation_service.evaluate_candidate",
                 new_callable=AsyncMock,
                 return_value=mock_eval,
             ), \
             patch(
                 "app.domains.cv_screening.services.cv_scoring_service.activity_service.create_activity",
                 new_callable=AsyncMock,
             ):
            result = await svc.screen_candidate(
                candidate_id="cand-high-score",
                vacancy_id="job-sre",
                company_id="company-test",
                db=mock_db,
            )

        assert result["success"] is True
        assert result["rubric_score"] >= 85.0
        assert result["sub_status"] == "cv_approved", \
            f"Expected cv_approved for score {result['rubric_score']}, got {result['sub_status']}"

    @pytest.mark.asyncio
    async def test_pipeline_e2e_low_score_gets_rejected_sub_status(self):
        """
        Pipeline completo: score < 40 deve gerar sub_status='cv_rejected'.
        """
        from app.domains.cv_screening.services.cv_scoring_service import CVScoringService

        svc = CVScoringService()
        mock_db = AsyncMock()
        mock_db.commit = AsyncMock()
        mock_db.rollback = AsyncMock()
        mock_db.close = AsyncMock()

        candidate_data = {"name": "Pedro", "skills": ["Vendas"]}
        from app.schemas.rubric import JobRequirementCreate, RequirementPriorityEnum
        requirements = [JobRequirementCreate(requirement="Python avançado", priority=RequirementPriorityEnum.ESSENTIAL)]
        mock_eval = self._make_rubric_evaluation_result(score=25.0, recommendation="Não Recomendado")

        with patch.object(svc, "_get_candidate_data", new_callable=AsyncMock, return_value=candidate_data), \
             patch.object(svc, "_get_job_requirements", new_callable=AsyncMock, return_value=requirements), \
             patch.object(svc, "_get_job_info", new_callable=AsyncMock, return_value={"title": "Dev Python Sênior"}), \
             patch.object(svc, "_update_candidate_score", new_callable=AsyncMock), \
             patch(
                 "app.domains.cv_screening.services.cv_scoring_service.rubric_evaluation_service.evaluate_candidate",
                 new_callable=AsyncMock,
                 return_value=mock_eval,
             ), \
             patch(
                 "app.domains.cv_screening.services.cv_scoring_service.activity_service.create_activity",
                 new_callable=AsyncMock,
             ):
            result = await svc.screen_candidate(
                candidate_id="cand-low-score",
                vacancy_id="job-python-senior",
                company_id="company-test",
                db=mock_db,
            )

        assert result["success"] is True
        assert result["rubric_score"] <= 40.0
        assert result["sub_status"] == "cv_rejected", \
            f"Expected cv_rejected for score {result['rubric_score']}, got {result['sub_status']}"

    @pytest.mark.asyncio
    async def test_pipeline_e2e_result_includes_methodology_metadata(self):
        """
        Resultado do pipeline deve incluir metadados da metodologia BARS
        (formula, evidence_weights, cap).
        """
        from app.domains.cv_screening.services.cv_scoring_service import CVScoringService

        svc = CVScoringService()
        mock_db = AsyncMock()
        mock_db.commit = AsyncMock()
        mock_db.rollback = AsyncMock()
        mock_db.close = AsyncMock()

        candidate_data = {"name": "Carlos", "skills": ["SQL"]}
        from app.schemas.rubric import JobRequirementCreate, RequirementPriorityEnum
        requirements = [JobRequirementCreate(requirement="SQL", priority=RequirementPriorityEnum.IMPORTANT)]
        mock_eval = self._make_rubric_evaluation_result(score=60.0)

        with patch.object(svc, "_get_candidate_data", new_callable=AsyncMock, return_value=candidate_data), \
             patch.object(svc, "_get_job_requirements", new_callable=AsyncMock, return_value=requirements), \
             patch.object(svc, "_get_job_info", new_callable=AsyncMock, return_value={"title": "DBA"}), \
             patch.object(svc, "_update_candidate_score", new_callable=AsyncMock), \
             patch(
                 "app.domains.cv_screening.services.cv_scoring_service.rubric_evaluation_service.evaluate_candidate",
                 new_callable=AsyncMock,
                 return_value=mock_eval,
             ), \
             patch(
                 "app.domains.cv_screening.services.cv_scoring_service.activity_service.create_activity",
                 new_callable=AsyncMock,
             ):
            result = await svc.screen_candidate(
                candidate_id="cand-meta",
                vacancy_id="job-dba",
                company_id="company-test",
                db=mock_db,
            )

        assert result["success"] is True
        methodology = result.get("methodology", {})
        assert "BARS" in methodology.get("name", ""), \
            f"Expected BARS in methodology name, got: {methodology.get('name')}"
        assert methodology.get("cap") == 99, "Score cap deve ser 99"
        evidence_weights = methodology.get("evidence_weights", {})
        assert evidence_weights.get("explicit") == 1.0
        assert evidence_weights.get("implicit") == 0.7
        assert evidence_weights.get("inferred") == 0.3
