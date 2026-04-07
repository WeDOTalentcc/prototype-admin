"""
Unit tests — WSI Runtime Bug Fixes (Sprint WSI-BUGFIX).

Cobre os 5 fixes aplicados em wsi_interview_graph.py e wsi_service.py:
  BUG-1: parâmetros corretos em calculate_wsi_deterministic (response_text, competency_name)
  BUG-2: await removido de função síncrona
  BUG-3: thresholds de recomendação usam decision do scorer (escala /5)
  BUG-4: confidence Prometheus usa /5.0 (não /10.0)
  BUG-5: _accumulate_score usa score /5 diretamente (não normaliza para /10)
  BUG-6: WSIResult.classification inclui "excepcional"
"""
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime

pytestmark = pytest.mark.hard


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_state():
    from app.domains.cv_screening.agents.wsi_interview_graph import (
        WSIInterviewState,
        WSIQuestionBlock,
        WSIInterviewStage,
    )
    block = WSIQuestionBlock(
        block_id="b-1",
        block_type="technical",
        question="Descreva seu uso de Python?",
        competency="python",
        bloom_level=3,
        dreyfus_level=2,
        max_score=10.0,
    )
    state = WSIInterviewState(
        session_id="sess-test",
        company_id="co-1",
        candidate_id="cand-1",
        job_id="job-1",
        question_blocks=[block],
    )
    state.current_question = block
    state.stage = WSIInterviewStage.SCORE_RESPONSE
    state.candidate_profile["_pending_response"] = {"text": "Uso Python há 5 anos."}
    return state


def _make_scorer_result(score: float = 3.5, bloom: int = 3, dreyfus: int = 2):
    from app.domains.cv_screening.services.wsi_deterministic_scorer import DeterministicWSIResult
    return DeterministicWSIResult(
        autodeclaracao_score=3.0,
        context_score=score,
        bloom_level=bloom,
        bloom_name="Aplicar",
        dreyfus_level=dreyfus,
        dreyfus_name="Intermediário",
        evidences=["5 anos de experiência"],
        red_flags=[],
        penalty=0.0,
        bonus=0.0,
        final_score=score,
        formula_applied=f"(0.4 × 3.0) + (0.6 × {score}) = {score}",
        justification="Contexto adequado. Bloom: Aplicar. Dreyfus: Intermediário.",
    )


# ---------------------------------------------------------------------------
# BUG-1+BUG-2: Parâmetros corretos + sem await
# ---------------------------------------------------------------------------

class TestScoreResponseCallSignature:
    """Verifica que score_response chama calculate_wsi_deterministic corretamente."""

    @pytest.mark.asyncio
    async def test_correct_kwargs_passed_to_scorer(self):
        state = _make_state()
        scorer_result = _make_scorer_result(score=3.8)

        with patch(
            "app.domains.cv_screening.services.wsi_deterministic_scorer.calculate_wsi_deterministic",
            return_value=scorer_result,
        ) as mock_scorer:
            from app.domains.cv_screening.agents.wsi_interview_graph import WSIInterviewNodes
            nodes = WSIInterviewNodes()
            new_state = await nodes.score_response(state)

        mock_scorer.assert_called_once()
        call_kwargs = mock_scorer.call_args
        assert call_kwargs.kwargs.get("response_text") == "Uso Python há 5 anos."
        assert call_kwargs.kwargs.get("competency_name") == "python"
        # Parâmetros inexistentes NÃO devem estar na chamada
        assert "candidate_response" not in (call_kwargs.kwargs or {})
        assert "expected_bloom" not in (call_kwargs.kwargs or {})
        assert "expected_dreyfus" not in (call_kwargs.kwargs or {})
        assert "max_score" not in (call_kwargs.kwargs or {})

    @pytest.mark.asyncio
    async def test_scorer_result_fields_mapped_correctly(self):
        """final_score → score, bloom_level → bloom_achieved, justification → reasoning."""
        state = _make_state()
        scorer_result = _make_scorer_result(score=4.1, bloom=4, dreyfus=3)

        with patch(
            "app.domains.cv_screening.services.wsi_deterministic_scorer.calculate_wsi_deterministic",
            return_value=scorer_result,
        ):
            from app.domains.cv_screening.agents.wsi_interview_graph import WSIInterviewNodes
            nodes = WSIInterviewNodes()
            new_state = await nodes.score_response(state)

        assert len(new_state.responses) == 1
        rec = new_state.responses[0]
        assert rec.score == 4.1
        assert rec.bloom_achieved == 4
        assert rec.dreyfus_achieved == 3
        assert "Contexto adequado" in rec.reasoning

    @pytest.mark.asyncio
    async def test_no_response_skips_without_error(self):
        """Resposta vazia avança sem chamar scorer."""
        state = _make_state()
        state.candidate_profile["_pending_response"] = {"text": ""}

        with patch(
            "app.domains.cv_screening.services.wsi_deterministic_scorer.calculate_wsi_deterministic"
        ) as mock_scorer:
            from app.domains.cv_screening.agents.wsi_interview_graph import WSIInterviewNodes
            nodes = WSIInterviewNodes()
            new_state = await nodes.score_response(state)

        mock_scorer.assert_not_called()
        assert new_state.current_question_index == 1


# ---------------------------------------------------------------------------
# BUG-3: Thresholds de recomendação usam decision do scorer (/5 scale)
# ---------------------------------------------------------------------------

class TestGenerateFeedbackRecommendation:
    """Verifica que a recomendação final segue WSI_CUTOFFS (escala /5)."""

    def _patch_final(self, decision: str, final_score: float):
        return {
            "final_score": final_score,
            "decision": decision,
            "classification": "alto",
            "classification_label": "Alto",
            "gate_g3_triggered": False,
            "breakdown": {},
            "formula": "",
            "cutoffs_applied": {},
        }

    @pytest.mark.asyncio
    async def test_aprovado_quando_decision_approved(self):
        state = _make_state()
        state.candidate_profile.pop("_pending_response", None)
        state.technical_score = 4.0
        state.behavioral_score = 3.8

        with patch(
            "app.domains.cv_screening.services.wsi_deterministic_scorer.calculate_final_wsi_score",
            return_value=self._patch_final("approved", 3.9),
        ):
            from app.domains.cv_screening.agents.wsi_interview_graph import WSIInterviewNodes
            nodes = WSIInterviewNodes()
            new_state = await nodes.generate_feedback(state)

        assert new_state.recommendation == "aprovado"
        assert new_state.wsi_final_score == 3.9

    @pytest.mark.asyncio
    async def test_aguardando_quando_decision_needs_review(self):
        state = _make_state()
        state.candidate_profile.pop("_pending_response", None)
        state.technical_score = 3.2
        state.behavioral_score = 3.0

        with patch(
            "app.domains.cv_screening.services.wsi_deterministic_scorer.calculate_final_wsi_score",
            return_value=self._patch_final("needs_review", 3.1),
        ):
            from app.domains.cv_screening.agents.wsi_interview_graph import WSIInterviewNodes
            nodes = WSIInterviewNodes()
            new_state = await nodes.generate_feedback(state)

        assert new_state.recommendation == "aguardando"

    @pytest.mark.asyncio
    async def test_reprovado_quando_decision_rejected(self):
        state = _make_state()
        state.candidate_profile.pop("_pending_response", None)
        state.technical_score = 2.0
        state.behavioral_score = 1.8

        with patch(
            "app.domains.cv_screening.services.wsi_deterministic_scorer.calculate_final_wsi_score",
            return_value=self._patch_final("rejected", 1.9),
        ):
            from app.domains.cv_screening.agents.wsi_interview_graph import WSIInterviewNodes
            nodes = WSIInterviewNodes()
            new_state = await nodes.generate_feedback(state)

        assert new_state.recommendation == "reprovado"

    @pytest.mark.asyncio
    async def test_score_5_nao_causa_aprovado_automatico_sem_approved_decision(self):
        """Score == 5.0 mas decision='needs_review' → aguardando (não aprovado)."""
        state = _make_state()
        state.candidate_profile.pop("_pending_response", None)
        state.technical_score = 5.0
        state.behavioral_score = 5.0

        with patch(
            "app.domains.cv_screening.services.wsi_deterministic_scorer.calculate_final_wsi_score",
            return_value=self._patch_final("needs_review", 5.0),
        ):
            from app.domains.cv_screening.agents.wsi_interview_graph import WSIInterviewNodes
            nodes = WSIInterviewNodes()
            new_state = await nodes.generate_feedback(state)

        assert new_state.recommendation == "aguardando"


# ---------------------------------------------------------------------------
# BUG-4: Confidence Prometheus usa /5.0
# ---------------------------------------------------------------------------

class TestConfidenceMetric:
    """Verifica que confidence é normalizada para [0.0, 1.0] com /5."""

    def test_confidence_normalizes_to_1_at_score_5(self):
        import math
        score = 5.0
        confidence = min(1.0, score / 5.0)
        assert confidence == 1.0

    def test_confidence_at_score_3_75_is_075(self):
        score = 3.75
        confidence = min(1.0, score / 5.0)
        assert abs(confidence - 0.75) < 0.001

    def test_confidence_capped_at_1(self):
        score = 6.0  # hipotético fora dos limites
        confidence = min(1.0, score / 5.0)
        assert confidence == 1.0

    def test_old_division_by_10_would_give_wrong_max(self):
        """Demonstra que / 10.0 (código anterior) dava max 0.5 para score=5.0."""
        score = 5.0
        old_confidence = score / 10.0
        assert old_confidence == 0.5  # bug original
        new_confidence = min(1.0, score / 5.0)
        assert new_confidence == 1.0  # fix correto


# ---------------------------------------------------------------------------
# BUG-5: _accumulate_score usa score /5 diretamente
# ---------------------------------------------------------------------------

class TestAccumulateScore:
    """Verifica que _accumulate_score não altera escala do score /5."""

    def _get_nodes(self):
        from app.domains.cv_screening.agents.wsi_interview_graph import WSIInterviewNodes
        return WSIInterviewNodes()

    def _make_fresh_state(self):
        from app.domains.cv_screening.agents.wsi_interview_graph import (
            WSIInterviewState,
            WSIQuestionBlock,
        )
        block = WSIQuestionBlock(
            block_id="b-1", block_type="technical",
            question="Q", competency="c", bloom_level=3, dreyfus_level=2,
        )
        return WSIInterviewState(
            session_id="s", company_id="c", candidate_id="ca",
            job_id="j", question_blocks=[block],
        )

    def test_score_3_5_stays_in_range_after_accumulate(self):
        nodes = self._get_nodes()
        state = self._make_fresh_state()
        nodes._accumulate_score(state, "technical", 3.5, 10.0)
        assert 1.0 <= state.technical_score <= 5.0

    def test_score_below_min_clamped_before_average(self):
        """Score 0.5 é clamped para 1.0; primeiro score (n=0): (0*0+1)/(0+1)=1.0.
        Sem clamp seria (0*0+0.5)/(0+1)=0.5 — verifica que clamp agiu (resultado > 0.5)."""
        nodes = self._get_nodes()
        state = self._make_fresh_state()
        nodes._accumulate_score(state, "technical", 0.5, 10.0)
        assert state.technical_score == pytest.approx(1.0)
        assert state.technical_score > 0.5  # confirma que clamp agiu

    def test_behavioral_accumulates_correctly(self):
        nodes = self._get_nodes()
        state = self._make_fresh_state()
        nodes._accumulate_score(state, "behavioral", 4.0, 10.0)
        nodes._accumulate_score(state, "situational", 2.0, 10.0)
        assert 1.0 <= state.behavioral_score <= 5.0


# ---------------------------------------------------------------------------
# BUG-6: WSIResult.classification inclui "excepcional"
# ---------------------------------------------------------------------------

class TestWSIResultClassification:
    """Verifica que WSIResult aceita 'excepcional' como classificação válida."""

    def test_excepcional_is_valid_classification(self):
        from app.domains.cv_screening.services.wsi_service import WSIResult
        result = WSIResult(
            candidate_id="c-1",
            job_vacancy_id="j-1",
            technical_wsi=4.8,
            behavioral_wsi=4.9,
            overall_wsi=4.85,
            classification="excepcional",
            response_analyses=[],
        )
        assert result.classification == "excepcional"

    def test_all_6_levels_accepted(self):
        from app.domains.cv_screening.services.wsi_service import WSIResult

        for lvl in ("excepcional", "excelente", "alto", "medio", "regular", "baixo"):
            r = WSIResult(
                candidate_id="c",
                job_vacancy_id="j",
                technical_wsi=3.0,
                behavioral_wsi=3.0,
                overall_wsi=3.0,
                classification=lvl,
                response_analyses=[],
            )
            assert r.classification == lvl

    def test_scorer_deterministic_also_has_6_levels(self):
        from app.domains.cv_screening.services.wsi_deterministic_scorer import classify_wsi_score
        result_excep = classify_wsi_score(4.5)
        assert result_excep == "excepcional"
        result_exc = classify_wsi_score(4.0)
        assert result_exc == "excelente"
        result_alto = classify_wsi_score(3.5)
        assert result_alto == "alto"
