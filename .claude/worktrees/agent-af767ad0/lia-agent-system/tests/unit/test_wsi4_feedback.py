"""
Tests WSI-4 — Feedback Determinístico F8.5.1
Spec: template 3 blocos (POSITIVO/DESENVOLVIMENTO/NIVEL),
      3 paths (APROVADO/EM_AVALIACAO/REPROVADO),
      multi-gate reasons no feedback.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_candidate():
    from app.domains.cv_screening.services.personalized_feedback_service import CandidateContext
    return CandidateContext(
        candidate_id="cand-1",
        name="Maria Silva",
        email="maria@example.com",
    )


def _make_job():
    from app.domains.cv_screening.services.personalized_feedback_service import JobContext
    return JobContext(
        job_id="job-1",
        title="Engenheira de Software",
        company_name="ACME",
        seniority_level="pleno",
    )


def _make_evaluation(score: float = 3.0):
    from app.domains.cv_screening.services.personalized_feedback_service import WSIEvaluationContext
    return WSIEvaluationContext(
        overall_wsi=score,
        classification="medio",
        strengths=["Comunicação clara", "Experiência com Python"],
        development_areas=["Escalabilidade", "Testes automatizados"],
        skill_gaps=["Kubernetes"],
    )


def _make_request(decision_type="REPROVADO", failed_gates=None, score=2.0):
    from app.domains.cv_screening.services.personalized_feedback_service import (
        PersonalizedFeedbackRequest,
    )
    return PersonalizedFeedbackRequest(
        candidate=_make_candidate(),
        job=_make_job(),
        evaluation=_make_evaluation(score),
        decision_type=decision_type,
        failed_gates=failed_gates or [],
    )


def _make_service():
    from app.domains.cv_screening.services.personalized_feedback_service import PersonalizedFeedbackService
    svc = PersonalizedFeedbackService.__new__(PersonalizedFeedbackService)
    svc.llm = MagicMock()
    return svc


# ---------------------------------------------------------------------------
# Template F8.5.1 — 3 Blocos
# ---------------------------------------------------------------------------

class TestTemplateF851:
    def test_template_has_bloco_positivo(self):
        """Template deve conter seção de pontos fortes (BLOCO_POSITIVO)."""
        svc = _make_service()
        req = _make_request(score=4.0)
        body, data = svc._build_f851_template_body(req)
        # Pontos fortes devem aparecer no corpo
        assert any(kw in body for kw in ["Pontos identificados", "destaque", "Pontos presentes"])

    def test_template_has_bloco_desenvolvimento(self):
        """Template deve conter seção de desenvolvimento (BLOCO_DESENVOLVIMENTO)."""
        svc = _make_service()
        req = _make_request(score=2.0)
        body, data = svc._build_f851_template_body(req)
        assert any(kw in body for kw in ["Pontos que poderiam enriquecer", "desenvolvimento"])

    def test_template_has_bloco_nivel(self):
        """Template deve conter bloco de resultado/decisão (BLOCO_NIVEL)."""
        svc = _make_service()
        req = _make_request(score=2.0)
        body, data = svc._build_f851_template_body(req)
        assert "Resultado:" in body

    def test_template_version_f851_in_data(self):
        """feedback_data deve indicar template_version = F8.5.1."""
        svc = _make_service()
        req = _make_request()
        _, data = svc._build_f851_template_body(req)
        assert data.get("template_version") == "F8.5.1"

    def test_template_includes_candidate_first_name(self):
        """Feedback deve incluir o primeiro nome do candidato."""
        svc = _make_service()
        req = _make_request()
        body, _ = svc._build_f851_template_body(req)
        assert "Maria" in body

    def test_template_includes_job_title(self):
        """Feedback deve incluir o título da vaga."""
        svc = _make_service()
        req = _make_request()
        body, _ = svc._build_f851_template_body(req)
        assert "Engenheira de Software" in body


# ---------------------------------------------------------------------------
# 3 Paths: APROVADO / EM_AVALIACAO / REPROVADO
# ---------------------------------------------------------------------------

class TestFeedbackPaths:
    def test_aprovado_path_contains_congratulations(self):
        """Path APROVADO deve conter mensagem de parabéns / próxima etapa."""
        svc = _make_service()
        req = _make_request(decision_type="APROVADO", score=4.5)
        body, data = svc._build_f851_template_body(req)
        assert "Parabéns" in body or "próxima etapa" in body.lower()
        assert data["decision_type"] == "APROVADO"

    def test_em_avaliacao_path_contains_review_message(self):
        """Path EM_AVALIACAO deve indicar análise em andamento."""
        svc = _make_service()
        req = _make_request(decision_type="EM_AVALIACAO", score=3.0)
        body, data = svc._build_f851_template_body(req)
        assert "análise" in body.lower() or "avaliada" in body.lower()
        assert data["decision_type"] == "EM_AVALIACAO"

    def test_reprovado_path_contains_rejection_message(self):
        """Path REPROVADO deve indicar encerramento respeitoso."""
        svc = _make_service()
        req = _make_request(decision_type="REPROVADO", score=1.5)
        body, data = svc._build_f851_template_body(req)
        assert "não avançaremos" in body.lower() or "não seguiremos" in body.lower()
        assert data["decision_type"] == "REPROVADO"

    def test_reprovado_message_does_not_appear_in_aprovado(self):
        """Mensagem de reprovação NÃO deve aparecer no path APROVADO."""
        svc = _make_service()
        req = _make_request(decision_type="APROVADO", score=4.5)
        body, _ = svc._build_f851_template_body(req)
        assert "não avançaremos" not in body.lower()
        assert "não seguiremos" not in body.lower()


# ---------------------------------------------------------------------------
# Multi-Gate Reasons
# ---------------------------------------------------------------------------

class TestMultiGateReasons:
    def test_failed_gates_included_in_reprovado_body(self):
        """Quando reprovado, gates ativados devem aparecer no feedback."""
        svc = _make_service()
        req = _make_request(
            decision_type="REPROVADO",
            failed_gates=["G2", "G4"],
        )
        body, data = svc._build_f851_template_body(req)
        assert "injeção de prompt" in body.lower()
        assert "skill crítica" in body.lower()
        assert "G2" in str(data["failed_gates"])
        assert "G4" in str(data["failed_gates"])

    def test_no_gate_reasons_when_no_failed_gates(self):
        """Sem gates falhos, seção de critérios não aparece."""
        svc = _make_service()
        req = _make_request(decision_type="REPROVADO", failed_gates=[])
        body, data = svc._build_f851_template_body(req)
        assert "Critério(s)" not in body
        assert data["failed_gates"] == []

    def test_all_gate_labels_translated(self):
        """Todos os 6 gates devem ter label traduzido em PT-BR."""
        svc = _make_service()
        gates = ["G1", "G2", "G3", "G4", "G5", "G6"]
        req = _make_request(decision_type="REPROVADO", failed_gates=gates)
        body, _ = svc._build_f851_template_body(req)
        assert "elegibilidade" in body
        assert "injeção de prompt" in body
        assert "competência técnica mínima" in body
        assert "skill crítica" in body
        assert "engajamento insuficiente" in body
        assert "inflação sistemática" in body

    def test_em_avaliacao_does_not_show_gate_reasons(self):
        """Path EM_AVALIACAO não deve mostrar gates falhos mesmo se presentes."""
        svc = _make_service()
        req = _make_request(decision_type="EM_AVALIACAO", failed_gates=["G3"])
        body, _ = svc._build_f851_template_body(req)
        assert "Critério(s)" not in body


# ---------------------------------------------------------------------------
# Métodos send_approval_feedback / send_review_feedback
# ---------------------------------------------------------------------------

class TestApprovalAndReviewMethods:
    def test_service_has_send_approval_feedback(self):
        """PersonalizedFeedbackService deve ter método send_approval_feedback."""
        from app.domains.cv_screening.services.personalized_feedback_service import PersonalizedFeedbackService
        assert hasattr(PersonalizedFeedbackService, "send_approval_feedback")

    def test_service_has_send_review_feedback(self):
        """PersonalizedFeedbackService deve ter método send_review_feedback."""
        from app.domains.cv_screening.services.personalized_feedback_service import PersonalizedFeedbackService
        assert hasattr(PersonalizedFeedbackService, "send_review_feedback")

    @pytest.mark.asyncio
    async def test_send_approval_feedback_sets_aprovado(self):
        """send_approval_feedback deve gerar feedback com decision_type=APROVADO."""
        from app.domains.cv_screening.services.personalized_feedback_service import PersonalizedFeedbackService

        svc = PersonalizedFeedbackService.__new__(PersonalizedFeedbackService)
        svc.llm = MagicMock()

        # Mock generate_personalized_feedback
        mock_result = MagicMock()
        mock_result.body_text = "Parabéns!"
        svc.generate_personalized_feedback = AsyncMock(return_value=mock_result)

        result = await svc.send_approval_feedback(
            candidate=_make_candidate(),
            job=_make_job(),
            evaluation=_make_evaluation(4.5),
            company_id="company-1",
        )

        # Verify it called generate with APROVADO
        call_args = svc.generate_personalized_feedback.call_args
        request_arg = call_args[0][0]
        assert request_arg.decision_type == "APROVADO"
        assert result == mock_result

    @pytest.mark.asyncio
    async def test_send_review_feedback_sets_em_avaliacao(self):
        """send_review_feedback deve gerar feedback com decision_type=EM_AVALIACAO."""
        from app.domains.cv_screening.services.personalized_feedback_service import PersonalizedFeedbackService

        svc = PersonalizedFeedbackService.__new__(PersonalizedFeedbackService)
        svc.llm = MagicMock()

        mock_result = MagicMock()
        svc.generate_personalized_feedback = AsyncMock(return_value=mock_result)

        await svc.send_review_feedback(
            candidate=_make_candidate(),
            job=_make_job(),
            evaluation=_make_evaluation(3.0),
        )

        call_args = svc.generate_personalized_feedback.call_args
        request_arg = call_args[0][0]
        assert request_arg.decision_type == "EM_AVALIACAO"


# ---------------------------------------------------------------------------
# PersonalizedFeedbackRequest tem decision_type e failed_gates
# ---------------------------------------------------------------------------

class TestRequestModel:
    def test_request_has_decision_type_field(self):
        """PersonalizedFeedbackRequest deve ter campo decision_type."""
        from app.domains.cv_screening.services.personalized_feedback_service import PersonalizedFeedbackRequest
        req = PersonalizedFeedbackRequest(
            candidate=_make_candidate(),
            job=_make_job(),
            evaluation=_make_evaluation(),
            decision_type="REPROVADO",
        )
        assert req.decision_type == "REPROVADO"

    def test_request_has_failed_gates_field(self):
        """PersonalizedFeedbackRequest deve ter campo failed_gates."""
        from app.domains.cv_screening.services.personalized_feedback_service import PersonalizedFeedbackRequest
        req = PersonalizedFeedbackRequest(
            candidate=_make_candidate(),
            job=_make_job(),
            evaluation=_make_evaluation(),
            failed_gates=["G2", "G6"],
        )
        assert req.failed_gates == ["G2", "G6"]

    def test_default_decision_type_is_reprovado(self):
        """decision_type padrão deve ser REPROVADO."""
        from app.domains.cv_screening.services.personalized_feedback_service import PersonalizedFeedbackRequest
        req = PersonalizedFeedbackRequest(
            candidate=_make_candidate(),
            job=_make_job(),
            evaluation=_make_evaluation(),
        )
        assert req.decision_type == "REPROVADO"
