"""
Fase de elegibilidade da triagem (maquina de estados pura).

Epico Elegibilidade 2026-06-03, Fase B (canonical-fix + harness-engineering).

Perguntas eliminatorias de elegibilidade sao feitas ANTES dos blocos WSI.
Logica PURA (sem DB): recebe (state, answer) -> (new_state, response). A casca
de I/O (messaging.py / lifecycle.py) persiste o state em
TriagemSession.metadata_json["eligibility"] e cria as TriagemMessage.

Consome o PRODUTOR UNICO EligibilityVerificationService (decisao Paulo #3):
nenhuma regra de matching/reconsideracao vive aqui — so orquestracao de sub-estados.
"""
from __future__ import annotations

from dataclasses import asdict
from typing import Any

from app.domains.cv_screening.services.eligibility_verification_service import (
    EligibilityQuestion,
    ReconsiderationResult,
    eligibility_service,
)

# Sub-estados da fase
PHASE_ASKING = "asking"
PHASE_RECONSIDERING = "reconsidering"
PHASE_CONFIRMING = "confirming"
PHASE_COMPLETE = "complete"
PHASE_TALENT_POOL = "talent_pool"

_TERMINAL = {PHASE_COMPLETE, PHASE_TALENT_POOL}


def build_eligibility_state(job_eligibility_questions: list[dict] | None) -> dict[str, Any]:
    """Normaliza via produtor e retorna o estado inicial da fase.

    Retorna {} quando nao ha nenhuma pergunta eliminatoria — nesse caso a
    triagem vai direto para os blocos WSI (sem fase de elegibilidade).
    """
    qs = eligibility_service.get_eligibility_questions_from_job(
        {"eligibility_questions": job_eligibility_questions or []}
    )
    eliminatory = [q for q in qs if q.is_eliminatory]
    if not eliminatory:
        return {}
    return {
        "questions": [_eq_to_dict(q) for q in eliminatory],
        "index": 0,
        "phase": PHASE_ASKING,
        "reconsideration_count": 0,
        "pending_original_answer": None,
    }


def is_active(state: dict[str, Any] | None) -> bool:
    """True quando ha fase de elegibilidade pendente (nao terminal)."""
    if not state:
        return False
    return state.get("phase") not in _TERMINAL


def current_question_text(state: dict[str, Any] | None) -> str | None:
    """Texto da pergunta de elegibilidade atual (para start_session)."""
    if not is_active(state):
        return None
    qs = state.get("questions") or []
    idx = state.get("index", 0)
    if 0 <= idx < len(qs):
        return qs[idx].get("question")
    return None


def advance(state: dict[str, Any], answer: str) -> tuple[dict[str, Any], dict[str, Any]]:
    """Processa a resposta do candidato na fase de elegibilidade.

    Retorna (novo_state, response). response pode conter:
      - content: texto da LIA
      - type: tipo da mensagem
      - eligibility_done: True quando todas eliminatorias passaram -> iniciar WSI
      - talent_pool: True quando candidato foi redirecionado ao banco de talentos
    """
    state = dict(state)
    phase = state.get("phase", PHASE_ASKING)
    questions = state.get("questions") or []
    idx = state.get("index", 0)
    if idx >= len(questions):
        state["phase"] = PHASE_COMPLETE
        return state, {"eligibility_done": True}

    q = _dict_to_eq(questions[idx])

    if phase == PHASE_ASKING:
        result, msg = eligibility_service.check_answer(
            q, answer, state.get("reconsideration_count", 0)
        )
        if result == ReconsiderationResult.PASSED:
            return _advance_to_next(state)
        if result == ReconsiderationResult.NEEDS_RECONSIDERATION:
            state["phase"] = PHASE_RECONSIDERING
            state["pending_original_answer"] = answer
            return state, {"content": msg, "type": "eligibility_reconsideration"}
        # MAX_RECONSIDERATIONS_REACHED
        state["phase"] = PHASE_TALENT_POOL
        return state, {"content": msg, "type": "eligibility_talent_pool", "talent_pool": True}

    if phase == PHASE_RECONSIDERING:
        ctx = eligibility_service.create_reconsideration_context(
            q, state.get("pending_original_answer") or "", state.get("reconsideration_count", 0)
        )
        result, msg = eligibility_service.process_reconsideration_response(answer, ctx)
        if result == ReconsiderationResult.KEPT_INCOMPATIBLE:
            state["phase"] = PHASE_TALENT_POOL
            return state, {"content": msg, "type": "eligibility_talent_pool", "talent_pool": True}
        if result == ReconsiderationResult.RECONSIDERED_PASSED:
            state["phase"] = PHASE_CONFIRMING
            state["reconsideration_count"] = state.get("reconsideration_count", 0) + 1
            return state, {"content": msg, "type": "eligibility_confirmation"}
        # NEEDS_RECONSIDERATION — nao entendeu "1/2", repete
        return state, {"content": msg, "type": "eligibility_reconsideration"}

    if phase == PHASE_CONFIRMING:
        passed, msg = eligibility_service.process_confirmation_response(
            answer, q.expected_answer or "", q.question_type
        )
        if passed:
            return _advance_to_next(state)
        state["phase"] = PHASE_TALENT_POOL
        return state, {"content": msg, "type": "eligibility_talent_pool", "talent_pool": True}

    # fase terminal inesperada
    return state, {"eligibility_done": True}


def _advance_to_next(state: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    state["index"] = state.get("index", 0) + 1
    state["reconsideration_count"] = 0
    state["pending_original_answer"] = None
    questions = state.get("questions") or []
    if state["index"] >= len(questions):
        state["phase"] = PHASE_COMPLETE
        return state, {"eligibility_done": True}
    next_q = questions[state["index"]]
    return state, {
        "content": next_q.get("question"),
        "type": "question",
        "eligibility": True,
    }


def _eq_to_dict(q: EligibilityQuestion) -> dict[str, Any]:
    d = asdict(q)
    # campo canonico no snapshot usa "question" (nao "question_text")
    d["question"] = d.pop("question_text", "")
    return d


def _dict_to_eq(d: dict[str, Any]) -> EligibilityQuestion:
    return EligibilityQuestion(
        id=str(d.get("id", "")),
        question_text=d.get("question") or d.get("question_text") or "",
        question_type=d.get("question_type") or "yes_no",
        options=d.get("options"),
        is_eliminatory=bool(d.get("is_eliminatory", True)),
        expected_answer=d.get("expected_answer"),
        category=d.get("category") or "default",
    )
