"""
Sensor — seguranca juridica do feedback de reprovacao (auditoria 2026-06-10).
Camada 2 (Unitario BE — pytest, sem DB).

Decisoes Paulo:
1. Motivos de alto risco juridico -> IA NUNCA redige (feedback generico forcado),
   mas o motivo segue selecionavel p/ uso interno.
2. Dados internos (scores WSI, gaps, notas verbatim) NAO entram no prompt do LLM.
3. Assinatura = nome do cliente (tenant), nunca "WeDoTalent".
"""
import pytest
from unittest.mock import patch, MagicMock

from app.domains.automation.services.stage_transition_automation import (
    MessageGenerator,
    is_high_risk_rejection,
    HIGH_RISK_REJECTION_SUBSTATUS,
)


class TestHighRiskRejectionSet:
    def test_high_risk_members(self):
        for code in [
            "negative_references", "failed_background_check", "failed_admission_exam",
            "inadequate_attitude", "lack_professionalism",
        ]:
            assert is_high_risk_rejection(code) is True, code

    def test_normal_motives_not_high_risk(self):
        for code in ["over_qualified", "another_candidate_selected", "lacking_experience"]:
            assert is_high_risk_rejection(code) is False, code

    def test_empty_safe(self):
        assert is_high_risk_rejection("") is False
        assert is_high_risk_rejection(None) is False


class TestPersonalizationDataNoInternal:
    def test_excludes_scores_gaps_notes(self):
        ctx = {
            "wsi_score": {"overall": 72, "technical": 80, "behavioral": 65},
            "lia_parecer": {"strengths": ["comunicacao", "lideranca"], "development_areas": ["SQL avancado"]},
            "interview_notes": [
                {"stage": "interview_technical", "gaps": ["SQL", "System Design"], "strengths": ["x"]}
            ],
        }
        out = MessageGenerator._build_personalization_data(ctx)
        # sem scores numericos
        assert "72" not in out and "80" not in out and "65" not in out
        assert "Score" not in out
        # sem gaps / notas internas
        assert "SQL" not in out and "System Design" not in out
        assert "Gaps" not in out
        assert "desenvolvimento" not in out.lower()
        # mantem pontos fortes positivos
        assert "comunicacao" in out or "lideranca" in out


class TestFallbackSignature:
    def test_uses_client_name_not_vendor(self):
        res = MessageGenerator._generate_fallback(
            {"name": "Maria Silva"}, "rejected", "over_qualified",
            {"title": "Analista", "company_name": "ACME Tecnologia"}, "email",
        )
        assert "WeDoTalent" not in res["body"]
        assert "ACME Tecnologia" in res["body"]

    def test_neutral_when_no_company(self):
        res = MessageGenerator._generate_fallback(
            {"name": "Maria"}, "rejected", "over_qualified", {"title": "Analista"}, "email",
        )
        assert "WeDoTalent" not in res["body"]
        assert "Equipe de Recrutamento" in res["body"]


class TestHighRiskForcesGeneric:
    @pytest.mark.asyncio
    async def test_high_risk_returns_fallback_without_calling_llm(self):
        boom = MagicMock(side_effect=AssertionError("LLM NAO deve ser chamado p/ motivo de alto risco"))
        with patch(
            "app.domains.automation.services.stage_transition_automation.is_llm_available",
            return_value=True,
        ), patch(
            "app.domains.automation.services.stage_transition_automation.get_anthropic_client",
            boom,
        ):
            res = await MessageGenerator.generate(
                candidate_context={"name": "Maria"},
                to_stage="rejected",
                substatus="negative_references",
                job_context={"title": "Analista", "company_name": "ACME"},
                message_type="feedback_construtivo",
                channel="email",
            )
        assert res["metadata"]["generated_by"] == "fallback_template"
        assert "WeDoTalent" not in res["body"]
