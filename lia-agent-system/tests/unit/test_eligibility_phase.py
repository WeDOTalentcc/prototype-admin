"""
SENSOR (harness) — maquina de estados da fase de elegibilidade na triagem.

Epico Elegibilidade 2026-06-03, Fase B. Pina o fluxo eliminatorio que o
candidato vive ANTES dos blocos WSI: aprovacao, reconsideracao (2x), talent pool.

Se este teste falhar, perguntas de elegibilidade pararam de cortar candidato
ou a maquina de estados regrediu. Logica de matching/reconsideracao vive no
produtor unico EligibilityVerificationService — aqui so a orquestracao.
"""
from __future__ import annotations

from app.domains.recruitment.services.triagem_session_service import eligibility_phase as ep


def _job(qs):
    return qs


WIZARD_Q = {"id": "q1", "question": "Voce possui CNH categoria B?", "required_answer": "yes"}
JOBEDIT_Q = {
    "id": "q2",
    "type": "yes_no",
    "question": "Aceita trabalho presencial?",
    "disqualify_on_fail": True,
    "expected_answer": "Sim",
}


class TestBuildState:
    def test_no_questions_returns_empty(self):
        assert ep.build_eligibility_state([]) == {}
        assert ep.build_eligibility_state(None) == {}

    def test_builds_state_from_mixed_shapes(self):
        state = ep.build_eligibility_state([WIZARD_Q, JOBEDIT_Q])
        assert state["phase"] == ep.PHASE_ASKING
        assert state["index"] == 0
        assert len(state["questions"]) == 2
        assert ep.is_active(state) is True
        assert ep.current_question_text(state) == "Voce possui CNH categoria B?"

    def test_non_eliminatory_excluded(self):
        # is_eliminatory explicitamente False -> nao entra na fase
        state = ep.build_eligibility_state(
            [{"id": "x", "question": "Pergunta informativa", "is_eliminatory": False}]
        )
        assert state == {}


class TestHappyPath:
    def test_all_correct_completes_and_signals_wsi(self):
        state = ep.build_eligibility_state([WIZARD_Q, JOBEDIT_Q])
        state, resp = ep.advance(state, "sim")  # q1 ok -> proxima
        assert resp.get("content") == "Aceita trabalho presencial?"
        assert ep.is_active(state) is True
        state, resp = ep.advance(state, "sim")  # q2 ok -> done
        assert resp.get("eligibility_done") is True
        assert ep.is_active(state) is False
        assert state["phase"] == ep.PHASE_COMPLETE


class TestReconsiderationKeep:
    def test_wrong_then_keep_goes_talent_pool(self):
        state = ep.build_eligibility_state([JOBEDIT_Q])
        state, resp = ep.advance(state, "nao")  # errou eliminatoria
        assert resp["type"] == "eligibility_reconsideration"
        assert state["phase"] == ep.PHASE_RECONSIDERING
        state, resp = ep.advance(state, "1")  # manter resposta -> talent pool
        assert resp.get("talent_pool") is True
        assert state["phase"] == ep.PHASE_TALENT_POOL
        assert ep.is_active(state) is False


class TestReconsiderationReconsider:
    def test_wrong_then_reconsider_then_confirm_passes(self):
        state = ep.build_eligibility_state([JOBEDIT_Q])
        state, resp = ep.advance(state, "nao")  # errou
        assert state["phase"] == ep.PHASE_RECONSIDERING
        state, resp = ep.advance(state, "2")  # reconsiderar -> confirmacao
        assert resp["type"] == "eligibility_confirmation"
        assert state["phase"] == ep.PHASE_CONFIRMING
        state, resp = ep.advance(state, "sim")  # confirma corretamente -> done
        assert resp.get("eligibility_done") is True
        assert state["phase"] == ep.PHASE_COMPLETE

    def test_reconsider_then_confirm_wrong_goes_talent_pool(self):
        state = ep.build_eligibility_state([JOBEDIT_Q])
        state, _ = ep.advance(state, "nao")
        state, _ = ep.advance(state, "2")  # reconsiderar
        state, resp = ep.advance(state, "nao")  # confirma errado -> talent pool
        assert resp.get("talent_pool") is True
        assert state["phase"] == ep.PHASE_TALENT_POOL
