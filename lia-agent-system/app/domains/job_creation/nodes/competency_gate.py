"""competency_gate_node canonical - PR-10 split (2026-05-26).

Movido de graph.py durante refactor estrutural ONDA 3 sub-sprint B.
Mantem comportamento byte-identical via tests de regressao.

Gate post-competency to capture recruiter feedback and route to publish or back.
"""

import logging
import time
from typing import Any, Dict, List, Optional

from app.domains.job_creation.state import (
    JobCreationState,
    calculate_completeness,
)
from app.domains.job_creation.helpers.ws_payload_builder import (
    build_ws_stage_payload,
)
from app.domains.job_creation.helpers.i18n import msg
from app.domains.job_creation.helpers.async_audit import (
    emit_audit_fire_and_forget,
    run_coro_in_threadpool,
)
from app.domains.job_creation.helpers.llm_exceptions import (
    classify_llm_exception_reason,
)
# Module-level import so tests can mock: app.domains.job_creation.nodes.competency_gate._in_graph_runtime
from app.domains.job_creation.internal.utils import _in_graph_runtime

logger = logging.getLogger(__name__)


def competency_gate_node(state: JobCreationState) -> JobCreationState:
    """T4 (Task #1086) — gate LLM-based para HITL #2 (competency / screening_mode).

    Substitui a heurística keyword-based em ``domain.py::_route_by_stage``
    (linhas 'compact'/'compacto'/'7q'/'full'/'12q'/'completo') quando o
    flag ``LIA_WIZARD_LLM_GATES`` está ON. Allowlist específica do stage
    (definida em ``STAGE_ALLOWLISTS["competency"]``):

      - ``select_compact``  → ``screening_mode="compact"``
      - ``select_full``     → ``screening_mode="full"``
      - ``ask_question``    → state inalterado; ``gate_clarify_message=...``
                              (recomendação por seniority)
      - ``undecided``       → state inalterado; ``gate_clarify_message=...``
                              (recomendação leve por seniority)

    Confidence < 0.7 → re-pergunta natural sem mutar ``screening_mode``.
    Resume detection mirroring jd_gate_node: ``current_stage="competency"``
    + ``seniority_resolved`` truthy + ``screening_mode`` falsy +
    user_query fresh (não processado nesta invocação).
    """
    # Fase 1: mode confirmed at intake — skip LLM gate entirely.
    # route_after_competency_gate sees screening_mode set and routes to wsi_questions.
    if state.get("screening_mode") in ("compact", "full"):
        mode = state["screening_mode"]
        mode_label = "Compacto (7 perguntas)" if mode == "compact" else "Completo (12 perguntas)"
        logger.info("[JobCreation:competency_gate] mode=%s confirmed at intake — skip LLM gate", mode)
        return {
            **state,
            "current_stage": "competency",
            "gate_clarify_message": f"Modo **{mode_label}** registrado. Gerando as perguntas WSI agora.",
            "gate_last_intent": "select_compact" if mode == "compact" else "select_full",
        }

    # Deferred imports to avoid circular dependency with graph.py module-level state.
    from app.domains.job_creation.graph import (
        _extract_last_turns,
        _try_meta_helper,
        _emit_competency_gate_audit,
    )
    # _in_graph_runtime is available at module level (imported above)

    resume_msg = (state.get("gate_resume_message") or "").strip()
    if not resume_msg:
        # WS resume detection — caminho canônico via process_message não
        # seta gate_resume_message; detectamos via state nativo.
        _at_competency = (
            state.get("current_stage") == "competency"
            or bool(state.get("seniority_resolved"))
        )
        _no_mode_yet = not state.get("screening_mode")
        _uq = (state.get("user_query") or "").strip()
        _seen = (state.get("gate_seen_user_query") or "").strip()
        _is_fresh_turn = bool(_uq) and _uq != _seen
        if _at_competency and _no_mode_yet and _is_fresh_turn:
            resume_msg = _uq
            logger.info(
                "[JobCreation:competency_gate] WS resume detected (competency + fresh user_query, no mode yet) — classify",
            )
    if not resume_msg and _in_graph_runtime():
        # Task #1094 — pausa canônica via interrupt() (HITL #2 — competency).
        from langgraph.types import interrupt
        _resume = interrupt({
            "type": "approval",
            "stage": "competency",
            "data": {
                "seniority_resolved": state.get("seniority_resolved"),
                "competency_recommendation": state.get("competency_recommendation"),
            },
        })
        resume_msg = (str(_resume) if _resume is not None else "").strip()
    if not resume_msg:
        # Sem mensagem nova — cleanup de intent transitório (mirror jd_gate
        # T2 fix #4) e END via route_after_competency_gate.
        _last_intent = state.get("gate_last_intent")
        _is_transitional = _last_intent in ("ask_question", "undecided")
        clean_state = {**state, "current_stage": "competency"}
        if _is_transitional:
            clean_state["gate_last_intent"] = None
        logger.info(
            "[JobCreation:competency_gate] no resume message — END (waiting for user, prior_intent=%s, cleared=%s)",
            _last_intent, _is_transitional,
        )
        return clean_state

    # FairnessGuard L1 sobre a mensagem do gate (defesa em profundidade).
    try:
        from app.shared.compliance.fairness_guard import FairnessGuard
        _fg = FairnessGuard().check(resume_msg)
        if _fg.is_blocked:
            logger.warning(
                "[JobCreation:competency_gate] FairnessGuard L1 BLOCK on resume message: cat=%s, terms=%s",
                _fg.category, _fg.blocked_terms,
            )
            return {
                **state,
                "gate_resume_message": "",
                "gate_clarify_message": _fg.educational_message,
                "fairness_blocked": True,
                "fairness_block_reason": _fg.educational_message,
                "current_stage": "competency",
            }
    except Exception as exc:
        logger.debug("[JobCreation:competency_gate] FairnessGuard check failed (fail-open): %s", exc)

    # LLM classifier (per-stage allowlist + prompt).
    from app.domains.job_creation.services.wizard_gate_classifier import (
        get_wizard_gate_classifier, _make_fallback,
    )
    classifier = get_wizard_gate_classifier()

    output = None
    try:
        _company_id = state.get("workspace_id") or state.get("company_id")
        _user_id = state.get("user_id") or state.get("recruiter_id")
        coro_factory = lambda: classifier.classify(  # noqa: E731
            user_message=resume_msg,
            stage="competency",
            ws_stage_payload=state.get("ws_stage_payload"),
            tenant_context_snippet=str(state.get("tenant_context_snippet") or ""),
            hiring_policy_summary=str(state.get("hiring_policy_summary") or ""),
            company_id=str(_company_id) if _company_id else None,
            user_id=str(_user_id) if _user_id else None,
            last_turns=_extract_last_turns(state, n=3),  # Task #1123
        )
        # PR-14 (2026-05-26): helper canonical run_coro_in_threadpool() substitui
        # bloco running_loop + ThreadPoolExecutor inline (Tipo B migration).
        output = run_coro_in_threadpool(coro_factory, timeout=30.0)
    except Exception as exc:
        logger.warning("[JobCreation:competency_gate] classify failed (fallback): %s", exc)
        output = _make_fallback()

    # Audit row (best-effort).
    try:
        _emit_competency_gate_audit(state, resume_msg, output)
    except Exception as exc:
        logger.debug("[JobCreation:competency_gate] audit emit failed: %s", exc)

    # Resolve seniority recommendation (helper para ask_question / undecided).
    seniority = (state.get("seniority_resolved") or state.get("seniority") or "").lower()
    if seniority in ("estagio", "estágio", "junior", "júnior", "pleno"):
        recommended = "Compacto (7 perguntas)"
    elif seniority in ("senior", "sênior", "lead", "principal", "staff", "diretor"):
        recommended = "Completo (12 perguntas)"
    else:
        recommended = "Compacto (7 perguntas)"

    # Confidence floor — clarify sem mutar screening_mode.
    if (output.confidence or 0.0) < 0.7:
        logger.info(
            "[JobCreation:competency_gate] confidence=%.2f < 0.7 → clarify (intent=%s)",
            output.confidence, output.intent,
        )
        return {
            **state,
            "gate_resume_message": "",
            "gate_clarify_message": (
                output.conversational_reply
                or f"Compacto (7 perguntas) ou Completo (12 perguntas)? Pra esta vaga eu sugiro {recommended}."
            ),
            "gate_last_intent": output.intent,
            "gate_last_confidence": output.confidence,
            "current_stage": "competency",
            "gate_seen_user_query": resume_msg,
        }

    intent = output.intent
    next_state: dict = {
        **state,
        "gate_resume_message": "",
        "gate_clarify_message": None,
        "gate_last_intent": intent,
        "gate_last_confidence": output.confidence,
        "current_stage": "competency",
        "gate_seen_user_query": resume_msg,
    }

    if intent == "select_compact":
        next_state["screening_mode"] = "compact"
        next_state["gate_clarify_message"] = (
            output.conversational_reply
            or "Modo Compacto (7 perguntas) selecionado. Vou gerar as perguntas WSI agora."
        )
    elif intent == "select_full":
        next_state["screening_mode"] = "full"
        next_state["gate_clarify_message"] = (
            output.conversational_reply
            or "Modo Completo (12 perguntas) selecionado. Vou gerar as perguntas WSI agora."
        )
    elif intent == "ask_question":
        # Task #1123 — resposta rica via Sonnet (tenant + history-aware).
        _sonnet_reply = _try_meta_helper(
            state=state,
            stage="competency",
            user_message=resume_msg,
            stage_description=(
                msg("competency_gate.recommend_mode", recommended=recommended)
            ),
        )
        next_state["gate_clarify_message"] = (
            _sonnet_reply
            or output.conversational_reply
            or msg("competency_gate.explain_modes", recommended=recommended)
        )
    elif intent == "undecided":
        next_state["gate_clarify_message"] = (
            output.conversational_reply
            or f"Sem problema. Pra esta vaga eu sugiro {recommended}; me confirma quando puder pra eu seguir."
        )
    else:
        # Defesa em profundidade.
        logger.warning("[JobCreation:competency_gate] unhandled intent=%r → clarify", intent)
        next_state["gate_clarify_message"] = (
            f"Compacto (7 perguntas) ou Completo (12 perguntas)? Pra esta vaga eu sugiro {recommended}."
        )

    return next_state

