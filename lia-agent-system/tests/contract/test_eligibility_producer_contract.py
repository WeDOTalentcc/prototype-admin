"""
SENSOR (harness-engineering) — contrato do produtor unico de elegibilidade.

Epico Elegibilidade 2026-06-03, Fase A (canonical-fix).

Pina dois invariantes que, se quebrados, fazem perguntas de elegibilidade
configuradas NUNCA cortarem candidato (ghost feature historica):

  1. EligibilityQuestionItem normaliza os 4 shapes divergentes -> canonico.
  2. EligibilityVerificationService.get_eligibility_questions_from_job usa o
     shape canonico (le 'question'/'required_answer'/'disqualify_on_fail',
     nao apenas 'question_text'/'is_eliminatory').

Mensagem de regressao p/ LLM: se este teste falhar, o extractor voltou a ler
um shape nao-canonico. Parse SO via EligibilityQuestionItem. Ver
app/schemas/eligibility_question_item.py + CLAUDE.md Eligibility canonical shape.
"""
from __future__ import annotations

import pytest

from app.schemas.eligibility_question_item import EligibilityQuestionItem
from app.domains.cv_screening.services.eligibility_verification_service import (
    EligibilityVerificationService,
    EligibilityQuestion,
    ReconsiderationResult,
)


# ─────────────────────────────────────────────────────────────────────
# 1. Normalizacao dos 4 shapes historicos -> canonico
# ─────────────────────────────────────────────────────────────────────
class TestCanonicalNormalization:
    def test_wizard_shape(self):
        item = EligibilityQuestionItem(
            id="q1",
            question="Voce tem disponibilidade para trabalho presencial?",
            required_answer="yes",
        )
        assert item.question.startswith("Voce tem disponibilidade")
        assert item.is_eliminatory is True
        assert item.expected_answer == "Sim"
        assert item.category == "work_model"

    def test_job_edit_shape(self):
        item = EligibilityQuestionItem(
            id="q2",
            type="yes_no",
            question="Voce possui CNH categoria B?",
            disqualify_on_fail=True,
            expected_answer="Sim",
            order=2,
        )
        assert item.is_eliminatory is True
        assert item.expected_answer == "Sim"
        assert item.category == "legal"
        assert item.order == 2

    def test_catalog_template_shape(self):
        item = EligibilityQuestionItem(
            question="Aceita atuar em regime remoto?",
            type="yes_no",
            category="work_model",
            eliminatory=True,
            eliminatoryAnswer="Sim",
        )
        assert item.is_eliminatory is True
        assert item.expected_answer == "Sim"
        assert item.category == "work_model"

    def test_legacy_extractor_shape(self):
        item = EligibilityQuestionItem(
            id="q4",
            question_text="Tem ingles avancado?",
            is_eliminatory=True,
            expected_answer="Sim",
        )
        assert item.question == "Tem ingles avancado?"
        assert item.is_eliminatory is True
        assert item.category == "legal"

    def test_required_answer_no_maps_to_nao(self):
        item = EligibilityQuestionItem(question="Tem restricao X?", required_answer="no")
        assert item.expected_answer == "Nao"

    def test_eligibility_defaults_to_eliminatory(self):
        # Por definicao, pergunta de ELEGIBILIDADE e eliminatoria por default
        item = EligibilityQuestionItem(question="Pergunta sem flag eliminatoria")
        assert item.is_eliminatory is True


# ─────────────────────────────────────────────────────────────────────
# 2. Extractor do produtor usa o shape canonico (RED ate corrigir)
# ─────────────────────────────────────────────────────────────────────
class TestProducerExtractorUsesCanonical:
    def test_extractor_reads_wizard_shape(self):
        svc = EligibilityVerificationService()
        job_data = {
            "eligibility_questions": [
                {"id": "q1", "question": "Voce possui CNH categoria B?", "required_answer": "yes"}
            ]
        }
        qs = svc.get_eligibility_questions_from_job(job_data)
        assert len(qs) == 1
        q = qs[0]
        # historicamente o extractor lia 'question_text' -> vazio com shape wizard
        assert q.question_text == "Voce possui CNH categoria B?"
        # historicamente default False -> pergunta nunca cortava
        assert q.is_eliminatory is True
        assert q.expected_answer == "Sim"

    def test_extractor_reads_job_edit_shape(self):
        svc = EligibilityVerificationService()
        job_data = {
            "eligibility_questions": [
                {
                    "id": "q2",
                    "type": "yes_no",
                    "question": "Aceita modelo presencial?",
                    "disqualify_on_fail": True,
                    "expected_answer": "Sim",
                }
            ]
        }
        qs = svc.get_eligibility_questions_from_job(job_data)
        assert qs[0].is_eliminatory is True
        assert qs[0].question_text == "Aceita modelo presencial?"
        assert qs[0].category == "work_model"

    def test_empty_job_returns_empty(self):
        svc = EligibilityVerificationService()
        assert svc.get_eligibility_questions_from_job({}) == []
        assert svc.get_eligibility_questions_from_job({"eligibility_questions": []}) == []


# ─────────────────────────────────────────────────────────────────────
# 3. check_answer — contrato de resultados (deve continuar valido)
# ─────────────────────────────────────────────────────────────────────
class TestCheckAnswerContract:
    def _q(self, expected="Sim"):
        return EligibilityQuestion(
            id="1",
            question_text="Voce possui CNH categoria B?",
            question_type="yes_no",
            options=None,
            is_eliminatory=True,
            expected_answer=expected,
            category="legal",
        )

    def test_match_passes(self):
        svc = EligibilityVerificationService()
        result, _ = svc.check_answer(self._q(), "sim", 0)
        assert result == ReconsiderationResult.PASSED

    def test_mismatch_triggers_reconsideration(self):
        svc = EligibilityVerificationService()
        result, msg = svc.check_answer(self._q(), "nao", 0)
        assert result == ReconsiderationResult.NEEDS_RECONSIDERATION
        assert msg

    def test_mismatch_after_max_goes_talent_pool(self):
        svc = EligibilityVerificationService()
        result, msg = svc.check_answer(self._q(), "nao", 2)
        assert result == ReconsiderationResult.MAX_RECONSIDERATIONS_REACHED
        assert msg

    def test_non_eliminatory_passes(self):
        svc = EligibilityVerificationService()
        q = self._q()
        q.is_eliminatory = False
        result, _ = svc.check_answer(q, "qualquer", 0)
        assert result == ReconsiderationResult.PASSED
