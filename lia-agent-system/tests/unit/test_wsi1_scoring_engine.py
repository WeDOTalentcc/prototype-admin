"""
Tests WSI-1 — Scoring Engine
Spec F8: fórmula tri-componente, STAR ponderado, bloom_alinhamento,
         acumulação ponderada correta, SENIORITY_WEIGHTS no score final.
"""
import pytest
from unittest.mock import MagicMock, patch


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

TECHNICAL_RESPONSE = (
    "Tenho 4 anos de experiência com Python e FastAPI. "
    "Implementei um serviço de autenticação que reduziu latência em 40%. "
    "Usei PostgreSQL com índices otimizados e Redis para cache."
)

BEHAVIORAL_RESPONSE = (
    "Quando eu estava liderando o projeto de migração (Situation), "
    "minha tarefa era garantir zero downtime (Task), "
    "então decidi implementar feature flags e rollout gradual (Action), "
    "o resultado foi migração sem incidentes com 99.9% de uptime (Result)."
)

SHORT_GENERIC_RESPONSE = "Tenho experiência com isso. Já fiz antes."


# ---------------------------------------------------------------------------
# F8 — Fórmula Tri-Componente
# ---------------------------------------------------------------------------

class TestFormulaTriComponente:
    def test_formula_version_is_v2(self):
        from app.domains.cv_screening.services.wsi_deterministic_scorer import (
            calculate_wsi_deterministic,
        )
        result = calculate_wsi_deterministic(TECHNICAL_RESPONSE, question_type="technical")
        assert result.formula_version == "v2"

    def test_technical_formula_uses_three_components(self):
        from app.domains.cv_screening.services.wsi_deterministic_scorer import (
            calculate_wsi_deterministic, WSI_FORMULA_WEIGHTS_TECHNICAL,
        )
        result = calculate_wsi_deterministic(TECHNICAL_RESPONSE, question_type="technical")
        # fórmula deve mencionar os 3 pesos
        assert str(WSI_FORMULA_WEIGHTS_TECHNICAL["autodeclaracao"]) in result.formula_applied
        assert str(WSI_FORMULA_WEIGHTS_TECHNICAL["evidencias_tecnicas"]) in result.formula_applied
        assert str(WSI_FORMULA_WEIGHTS_TECHNICAL["bloom_alinhamento"]) in result.formula_applied

    def test_behavioral_formula_uses_star_and_trait(self):
        from app.domains.cv_screening.services.wsi_deterministic_scorer import (
            calculate_wsi_deterministic, WSI_FORMULA_WEIGHTS_BEHAVIORAL,
        )
        result = calculate_wsi_deterministic(BEHAVIORAL_RESPONSE, question_type="behavioral")
        assert str(WSI_FORMULA_WEIGHTS_BEHAVIORAL["star_estrutura"]) in result.formula_applied
        assert str(WSI_FORMULA_WEIGHTS_BEHAVIORAL["sinais_trait"]) in result.formula_applied

    def test_final_score_bounded_1_to_5(self):
        from app.domains.cv_screening.services.wsi_deterministic_scorer import (
            calculate_wsi_deterministic,
        )
        for qt in ("technical", "behavioral"):
            result = calculate_wsi_deterministic(TECHNICAL_RESPONSE, question_type=qt)
            assert 1.0 <= result.final_score <= 5.0


# ---------------------------------------------------------------------------
# STAR Score Ponderado
# ---------------------------------------------------------------------------

class TestStarScore:
    def test_star_weights_sum_to_one(self):
        from app.domains.cv_screening.services.wsi_deterministic_scorer import (
            STAR_COMPONENT_WEIGHTS,
        )
        assert abs(sum(STAR_COMPONENT_WEIGHTS.values()) - 1.0) < 0.001

    def test_full_star_response_score_is_one(self):
        from app.domains.cv_screening.services.wsi_deterministic_scorer import (
            calculate_star_score,
        )
        components, score = calculate_star_score(BEHAVIORAL_RESPONSE)
        # resposta contém S, T, A, R
        assert score == pytest.approx(1.0, abs=0.01)
        assert all(components.values())

    def test_empty_response_star_score_zero(self):
        from app.domains.cv_screening.services.wsi_deterministic_scorer import (
            calculate_star_score,
        )
        _, score = calculate_star_score("não sei responder")
        assert score == pytest.approx(0.0, abs=0.1)

    def test_behavioral_result_has_star_components(self):
        from app.domains.cv_screening.services.wsi_deterministic_scorer import (
            calculate_wsi_deterministic,
        )
        result = calculate_wsi_deterministic(BEHAVIORAL_RESPONSE, question_type="behavioral")
        assert result.star_components is not None
        assert isinstance(result.star_components, dict)
        assert set(result.star_components.keys()) == {"S", "T", "A", "R"}

    def test_technical_result_has_empty_star(self):
        from app.domains.cv_screening.services.wsi_deterministic_scorer import (
            calculate_wsi_deterministic,
        )
        result = calculate_wsi_deterministic(TECHNICAL_RESPONSE, question_type="technical")
        # Técnica não usa STAR
        assert result.star_score == 0.0


# ---------------------------------------------------------------------------
# Bloom Alignment
# ---------------------------------------------------------------------------

class TestBloomAlignment:
    def test_perfect_alignment(self):
        from app.domains.cv_screening.services.wsi_deterministic_scorer import (
            calculate_bloom_alignment,
        )
        assert calculate_bloom_alignment(3, 3) == pytest.approx(1.0)

    def test_one_level_off(self):
        from app.domains.cv_screening.services.wsi_deterministic_scorer import (
            calculate_bloom_alignment,
        )
        alignment = calculate_bloom_alignment(4, 3)
        assert alignment == pytest.approx(0.8, abs=0.01)

    def test_max_distance(self):
        from app.domains.cv_screening.services.wsi_deterministic_scorer import (
            calculate_bloom_alignment,
        )
        alignment = calculate_bloom_alignment(1, 6)
        assert alignment == pytest.approx(0.0, abs=0.01)

    def test_result_has_bloom_alignment_field(self):
        from app.domains.cv_screening.services.wsi_deterministic_scorer import (
            calculate_wsi_deterministic,
        )
        result = calculate_wsi_deterministic(
            TECHNICAL_RESPONSE, question_type="technical", bloom_expected=4
        )
        assert 0.0 <= result.bloom_alignment <= 1.0


# ---------------------------------------------------------------------------
# flags_structured (para G6)
# ---------------------------------------------------------------------------

class TestFlagsStructured:
    def test_inflation_flag_detected(self):
        from app.domains.cv_screening.services.wsi_deterministic_scorer import (
            calculate_wsi_deterministic,
        )
        # autodeclaração alta com contexto fraco
        result = calculate_wsi_deterministic(
            "expert nível máximo 5 de 5",
            autodeclaracao_override=5.0,
            contexto_override=1.5,
            question_type="technical",
        )
        assert result.flags_structured is not None
        assert result.flags_structured["is_inflation"] is True

    def test_no_inflation_clean_response(self):
        from app.domains.cv_screening.services.wsi_deterministic_scorer import (
            calculate_wsi_deterministic,
        )
        result = calculate_wsi_deterministic(TECHNICAL_RESPONSE, question_type="technical")
        assert result.flags_structured is not None
        assert result.flags_structured["is_inflation"] is False

    def test_short_flag_detected(self):
        from app.domains.cv_screening.services.wsi_deterministic_scorer import (
            calculate_wsi_deterministic,
        )
        result = calculate_wsi_deterministic("ok", question_type="technical")
        assert result.flags_structured["is_short"] is True


# ---------------------------------------------------------------------------
# Acumulação Ponderada Correta
# ---------------------------------------------------------------------------

class TestAccumulacaoPonderada:
    def _make_state(self):
        """Cria estado mínimo para testes."""
        from app.domains.cv_screening.agents.wsi_interview_graph import WSIInterviewState
        return WSIInterviewState(
            session_id="test-session",
            company_id="company-1",
            candidate_id="candidate-1",
            job_id="job-1",
        )

    def _make_graph(self):
        from app.domains.cv_screening.agents.wsi_interview_graph import WSIInterviewNodes
        return WSIInterviewNodes()

    def test_first_score_is_exact(self):
        """Primeira pontuação deve ser exatamente o score recebido."""
        agent = self._make_graph()
        state = self._make_state()
        agent._accumulate_score(state, "technical", 4.0, 5.0)
        assert state.technical_score == pytest.approx(4.0)
        assert state.technical_score_count == 1

    def test_two_equal_scores_average(self):
        """Dois scores iguais devem resultar na média exata."""
        agent = self._make_graph()
        state = self._make_state()
        agent._accumulate_score(state, "technical", 3.0, 5.0)
        agent._accumulate_score(state, "technical", 5.0, 5.0)
        assert state.technical_score == pytest.approx(4.0)
        assert state.technical_score_count == 2

    def test_three_scores_correct_average(self):
        """Três scores: média deve ser exata (não running average decay)."""
        agent = self._make_graph()
        state = self._make_state()
        for s in [2.0, 4.0, 3.0]:
            agent._accumulate_score(state, "technical", s, 5.0)
        # Média correta = (2+4+3)/3 = 3.0
        assert state.technical_score == pytest.approx(3.0, abs=0.01)
        assert state.technical_score_count == 3

    def test_behavioral_separate_from_technical(self):
        """Contadores de bloco técnico e comportamental são independentes."""
        agent = self._make_graph()
        state = self._make_state()
        agent._accumulate_score(state, "technical", 4.0, 5.0)
        agent._accumulate_score(state, "behavioral", 2.0, 5.0)
        agent._accumulate_score(state, "behavioral", 4.0, 5.0)
        assert state.technical_score == pytest.approx(4.0)
        assert state.behavioral_score == pytest.approx(3.0)
        assert state.technical_score_count == 1
        assert state.behavioral_score_count == 2


# ---------------------------------------------------------------------------
# SENIORITY_WEIGHTS no score final
# ---------------------------------------------------------------------------

class TestSeniorityWeightsIntegration:
    def test_seniority_passed_to_final_score(self):
        """generate_feedback deve passar seniority ao calculate_final_wsi_score."""
        from app.domains.cv_screening.services.wsi_deterministic_scorer import (
            calculate_final_wsi_score, SENIORITY_WEIGHTS,
        )
        # Para diretor: técnico=31.25%, comportamental=68.75%
        result = calculate_final_wsi_score(
            technical_scores=[("t1", 4.0, 1.0)],
            behavioral_scores=[("b1", 2.0, 1.0)],
            seniority="diretor",
        )
        weights = SENIORITY_WEIGHTS["diretor"]
        expected = round(weights["technical"] * 4.0 + weights["behavioral"] * 2.0, 2)
        assert result["final_score"] == pytest.approx(expected, abs=0.05)

    def test_default_seniority_fallback(self):
        """Sem seniority: usa fallback pleno (t=0.625, b=0.375)."""
        from app.domains.cv_screening.services.wsi_deterministic_scorer import (
            calculate_final_wsi_score,
        )
        result = calculate_final_wsi_score(
            technical_scores=[("t1", 4.0, 1.0)],
            behavioral_scores=[("b1", 2.0, 1.0)],
        )
        # t=0.625×4 + b=0.375×2 = 2.5 + 0.75 = 3.25
        assert result["final_score"] == pytest.approx(3.25, abs=0.05)

    def test_state_serialization_includes_counts(self):
        """Contadores de score devem sobreviver à serialização/deserialização."""
        from app.domains.cv_screening.agents.wsi_interview_graph import (
            WSIInterviewState, _wsi_state_to_dict, _wsi_state_from_dict,
        )
        state = WSIInterviewState(
            session_id="s1", company_id="c1", candidate_id="ca1", job_id="j1"
        )
        state.technical_score = 3.5
        state.technical_score_count = 2
        state.behavioral_score_count = 1

        d = _wsi_state_to_dict(state)
        assert d["technical_score_count"] == 2
        assert d["behavioral_score_count"] == 1

        restored = _wsi_state_from_dict(d)
        assert restored.technical_score_count == 2
        assert restored.behavioral_score_count == 1
