"""
Tests for Interview Scheduling domain (nova arquitetura DDD).

Cobre:
- Happy path: agendamento de entrevista
- WSI interviewer: perguntas limitadas a competências profissionais
- FairnessGuard: perguntas pessoais bloqueadas
"""
import pytest


class TestInterviewSchedulingImport:
    """Importações do domínio."""

    def test_domain_importable(self):
        """Domínio interview_scheduling importável."""
        from app.domains.interview_scheduling import domain as interview_domain
        assert interview_domain is not None


class TestWSIInterviewerGuardrails:
    """WSI Interviewer: apenas perguntas profissionais."""

    def test_personal_question_detected_by_fairness(self):
        """Perguntas pessoais devem ser detectadas pelo FairnessGuard."""
        from app.shared.compliance.fairness_guard import FairnessGuard
        guard = FairnessGuard()
        personal_question = "Você tem filhos? Está planejando engravidar?"
        result = guard.check_explicit_bias(personal_question)
        assert result.is_biased

    def test_professional_question_passes(self):
        """Perguntas profissionais devem passar pelo FairnessGuard."""
        from app.shared.compliance.fairness_guard import FairnessGuard
        guard = FairnessGuard()
        professional = "Descreva um projeto técnico complexo que você liderou."
        result = guard.check_explicit_bias(professional)
        assert not result.is_biased


class TestInterviewFairness:
    """Fairness em avaliações de entrevista."""

    def test_fairness_guard_layers_importable(self):
        """Todos os métodos do FairnessGuard devem ser acessíveis."""
        from app.shared.compliance.fairness_guard import FairnessGuard
        guard = FairnessGuard()
        assert callable(guard.check_explicit_bias)
        assert callable(guard.check_implicit_bias)
        assert callable(guard.check_semantic)
