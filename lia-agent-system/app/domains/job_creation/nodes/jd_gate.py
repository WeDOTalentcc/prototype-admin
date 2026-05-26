"""jd_gate_node canonical - PR-10 split (2026-05-26).

Movido de graph.py durante refactor estrutural ONDA 3 sub-sprint B.
Mantem comportamento byte-identical via tests de regressao.

Gate post jd_enrichment to capture recruiter feedback on description.
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
from app.domains.job_creation.helpers.async_audit import (
    emit_audit_fire_and_forget,
    run_coro_in_threadpool,
)
from app.domains.job_creation.helpers.llm_exceptions import (
    classify_llm_exception_reason,
)

logger = logging.getLogger(__name__)


def jd_gate_node(state: JobCreationState) -> JobCreationState:
    """T2 — gate LLM-based para HITL #1 (jd_enrichment).

    Quando ``state['gate_resume_message']`` está presente, classifica o intent
    do recrutador via LLM (Haiku/Flash temp=0), valida via Pydantic + allowlist,
    e muta state determinísticamente. Sem mensagem de resume → no-op (END
    via ``route_after_gate``).

    Mutações por intent:
      - ``approve``              → ``jd_approved=True``
      - ``reject_with_feedback`` → ``jd_approved=False``, ``jd_rejection_feedback=...``
      - ``provide_new_content``  → ``jd_approved=False``, ``raw_input=<novo>``,
                                   ``jd_enriched=None`` (invalida cache),
                                   roteia para ``intake`` para re-enriquecer
      - ``ask_question``         → state inalterado; ``gate_clarify_message=...``
      - ``off_topic``            → state inalterado; ``gate_clarify_message=...``

    Confidence < 0.7 → re-pergunta natural sem mutar ``jd_approved``.
    """
    # Deferred imports to avoid circular dependency with graph.py module-level state.
    from app.domains.job_creation.graph import (
        _extract_last_turns,
        _in_graph_runtime,
        _try_meta_helper,
        _emit_jd_gate_audit,
    )

    # T2 fix #2 (code review #2): no caminho canônico WS via
    # ``WizardSessionService.process_message`` → ``graph.invoke`` direto, o
    # campo ``gate_resume_message`` NÃO é setado externamente — só o caminho
    # action-based em ``domain.py::_handle_gate_jd`` o seta. Para o gate ser
    # alcançado em produção (que é o objetivo da task), detectamos o resume
    # turn por sinal de state nativo: ``jd_enriched`` já populado +
    # ``jd_approved`` ainda None ⇒ recrutador está respondendo ao HITL #1.
    # Nesse caso, ``user_query`` é a resposta dele. Mantemos
    # ``gate_resume_message`` como fonte preferencial para preservar a
    # semântica explícita do path action-based e dos testes existentes.
    msg = (state.get("gate_resume_message") or "").strip()
    if not msg:
        # T2 fix #6 (code review #5): WS resume também precisa cobrir
        # POST-REJECT (jd_approved=False após reject_with_feedback). Antes
        # checávamos só ``jd_approved is None``, então o turno seguinte do
        # recrutador era ignorado uma vez (cleanup limpava jd_approved=None
        # SEM classificar). Agora aceitamos qualquer estado != True
        # (None ou False), e usamos um marcador ``gate_seen_user_query``
        # para evitar re-classificar a MESMA mensagem na mesma invocação
        # (ex.: provide_new_content → intake → jd_enrichment → jd_gate
        # re-entra com user_query inalterado).
        _has_enriched = bool(state.get("jd_enriched"))
        _not_approved_yet = state.get("jd_approved") is not True
        _uq = (state.get("user_query") or "").strip()
        _seen = (state.get("gate_seen_user_query") or "").strip()
        _raw = (state.get("raw_input") or "").strip()
        _is_fresh_turn = bool(_uq) and _uq != _seen
        # T2 fix #8 (code review #6 comment): NÃO auto-classificar no
        # primeiro pass após enrichment — quando ``user_query == raw_input``
        # estamos na invocação inicial (recrutador acabou de mandar a JD;
        # intake+jd_enrichment populou ``jd_enriched`` na MESMA invocação).
        # Sem este guard, o gate roda LLM classifier sobre a própria JD
        # (que classifica como ``provide_new_content`` → re-enrichment loop)
        # e ainda incorre custo desnecessário. Resume real só acontece no
        # turno SEGUINTE, quando ``user_query`` é a resposta do recrutador
        # ao HITL — nesse ponto ``user_query != raw_input``.
        _is_initial_pass = bool(_raw) and _uq == _raw
        if _has_enriched and _not_approved_yet and _is_fresh_turn and not _is_initial_pass:
            msg = _uq
            logger.info(
                "[JobCreation:jd_gate] WS resume detected (jd_enriched + fresh user_query, jd_approved=%s) — classify",
                state.get("jd_approved"),
            )
    if not msg and _in_graph_runtime():
        # Task #1094 — pausa canônica via langgraph.types.interrupt().
        # Quando o caller usa ``Command(resume=<msg>)`` (process_message ou
        # JobCreationGraph.resume_with_message), interrupt() retorna a
        # mensagem do recrutador e o gate prossegue para classificar abaixo.
        # Em primeira entrada (HITL freshly reached), interrupt() levanta
        # GraphInterrupt — capturada pelo Pregel runtime para checkpointar
        # o state e devolver o controle ao caller. Caminho legacy END
        # no-op (offline / domain.py REST com gate_resume_message) é
        # preservado pelo guard ``_in_graph_runtime()``.
        from langgraph.types import interrupt
        _resume = interrupt({
            "type": "approval",
            "stage": "jd_enrichment",
            "data": {
                "jd_enriched": state.get("jd_enriched"),
                "jd_quality_score": state.get("jd_quality_score"),
            },
        })
        msg = (str(_resume) if _resume is not None else "").strip()
    if not msg:
        # Primeira passagem (após enrichment) OU re-entrada após
        # ``provide_new_content`` ter rodado intake+jd_enrichment_node. Sem
        # mensagem nova do recrutador para classificar.
        #
        # T2 fix #4 (code review #3): LIMPAR ``gate_last_intent`` e resetar
        # ``jd_approved`` quando re-entrando depois de um intent transitório
        # (provide_new_content / reject_with_feedback / ask_question /
        # off_topic). Sem isso, o ``route_after_gate`` ainda enxerga
        # ``provide_new_content + jd_approved=False`` desta visita anterior
        # e re-roteia para ``intake`` em loop até estourar
        # ``GraphRecursionError``. ``approve`` (jd_approved=True) NÃO é
        # transitório — preservamos. ``fairness_blocked`` também é terminal.
        _last_intent = state.get("gate_last_intent")
        _is_transitional = _last_intent in (
            "provide_new_content", "reject_with_feedback",
            "ask_question", "off_topic",
        )
        clean_state = {**state, "current_stage": "jd_enrichment"}
        if _is_transitional and not state.get("jd_fairness_blocked"):
            clean_state["gate_last_intent"] = None
            # jd_approved foi setado a False por essas mutações — reseta para
            # None ("aguardando aprovação") para o route cair no branch END
            # padrão e aguardar o próximo turno do recrutador.
            if state.get("jd_approved") is False:
                clean_state["jd_approved"] = None
        logger.info(
            "[JobCreation:jd_gate] no resume message — END (waiting for user, prior_intent=%s, cleared=%s)",
            _last_intent, _is_transitional,
        )
        return clean_state

    # Layer 1 fairness on the user's *resume* message (a discriminação pode
    # entrar via "manda bala mas só candidatos masculinos"). FairnessGuard L1
    # também roda em ``jd_enrichment_node`` sobre ``raw_input`` — aqui é defesa
    # adicional sobre a mensagem do gate.
    try:
        from app.shared.compliance.fairness_guard import FairnessGuard
        _fg = FairnessGuard().check(msg)
        if _fg.is_blocked:
            logger.warning(
                "[JobCreation:jd_gate] FairnessGuard L1 BLOCK on resume message: cat=%s, terms=%s",
                _fg.category, _fg.blocked_terms,
            )
            return {
                **state,
                "gate_resume_message": "",
                "gate_clarify_message": _fg.educational_message,
                "fairness_blocked": True,
                "jd_fairness_blocked": True,
                "fairness_block_reason": _fg.educational_message,
                "current_stage": "jd_enrichment",
            }
    except Exception as exc:
        # Fail-open: bug do guard não deve travar o wizard.
        logger.debug("[JobCreation:jd_gate] FairnessGuard check failed (fail-open): %s", exc)

    # LLM classifier — async chamado em sync context (graph nodes são sync).
    from app.domains.job_creation.services.wizard_gate_classifier import (
        get_wizard_gate_classifier, _make_fallback,
    )
    classifier = get_wizard_gate_classifier()

    output = None
    try:
        # T2 fix #3 (code review #2): plumb company_id/user_id do state para
        # o classifier registrar custo no ledger ``external_api_consumption``
        # (ConsumptionTrackingService.record_llm_call) por tenant. Sem isso,
        # o cost tracker fica configurado mas nunca dispara em produção.
        _company_id = (
            state.get("workspace_id") or state.get("company_id")
        )
        _user_id = state.get("user_id") or state.get("recruiter_id")
        coro_factory = lambda: classifier.classify(  # noqa: E731
            user_message=msg,
            stage="jd_enrichment",
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
        logger.warning("[JobCreation:jd_gate] classify failed (fallback): %s", exc)
        output = _make_fallback()

    # Audit row (best-effort) — EU AI Act Art. 13: decisão LLM rastreável.
    try:
        _emit_jd_gate_audit(state, msg, output)
    except Exception as exc:
        logger.debug("[JobCreation:jd_gate] audit emit failed: %s", exc)

    # Confidence floor — re-pergunta natural sem mutar jd_approved.
    if (output.confidence or 0.0) < 0.7:
        logger.info(
            "[JobCreation:jd_gate] confidence=%.2f < 0.7 → clarify (intent=%s)",
            output.confidence, output.intent,
        )
        return {
            **state,
            "gate_resume_message": "",
            "gate_clarify_message": output.conversational_reply,
            "gate_last_intent": output.intent,
            "gate_last_confidence": output.confidence,
            "current_stage": "jd_enrichment",
            "gate_seen_user_query": msg,
        }

    intent = output.intent
    next_state: dict = {
        **state,
        "gate_resume_message": "",
        "gate_clarify_message": None,
        "gate_last_intent": intent,
        "gate_last_confidence": output.confidence,
        "current_stage": "jd_enrichment",
        # T2 fix #6: marca a mensagem como já classificada nesta invocação,
        # para evitar re-classificação no segundo visit do gate (após
        # provide_new_content → intake → jd_enrichment → jd_gate).
        "gate_seen_user_query": msg,
    }

    extracted = output.extracted_data if isinstance(output.extracted_data, dict) else {}

    if intent == "approve":
        next_state["jd_approved"] = True
        next_state["gate_clarify_message"] = output.conversational_reply or None
    elif intent == "reject_with_feedback":
        next_state["jd_approved"] = False
        feedback = (extracted.get("feedback") or output.conversational_reply or msg)
        next_state["jd_rejection_feedback"] = str(feedback)[:1000]
        next_state["gate_clarify_message"] = output.conversational_reply or None
    elif intent == "provide_new_content":
        new_content = extracted.get("new_content") or msg
        next_state["jd_approved"] = False
        next_state["raw_input"] = str(new_content)[:8000]
        next_state["jd_enriched"] = None  # invalida cache → jd_enrichment_node re-roda
        next_state["jd_quality_score"] = 0.0
        # F-1.6 (P0-#3): provide_new_content cascade invalidation.
        # Recrutador trocando JD: derivados (bigfive, traits, wsi questions,
        # competency tree, pipeline template) foram calculados sobre a JD
        # ANTERIOR. Sem zerar, wizard publicaria vaga com mistura de 2 JDs
        # diferentes. Próximo turno re-calcula do zero sobre a nova JD.
        # Sprint Pipeline Templates (2026-05-26) expandiu escopo: agora
        # pipeline_template_id + score + skipped + interview_stages também
        # ficam stale e precisam ser invalidados aqui.
        next_state["bigfive_profile"] = None
        next_state["trait_rankings"] = []
        next_state["wsi_questions"] = []
        next_state["competency_tree"] = []
        next_state["pipeline_template_id"] = None
        next_state["pipeline_template_score"] = None
        next_state["pipeline_template_skipped"] = False
        next_state["interview_stages"] = []
        next_state["gate_clarify_message"] = (
            output.conversational_reply
            or "Recebi a descrição nova. Vou re-enriquecer agora."
        )
    elif intent == "ask_question":
        # Task #1123 — resposta rica via Sonnet (tenant + history-aware).
        # Fail-OPEN para o reply do classifier se Sonnet falhar.
        _sonnet_reply = _try_meta_helper(
            state=state,
            stage="jd_enrichment",
            user_message=msg,
            stage_description=(
                "HITL #1: revisão da descrição enriquecida da vaga (JD). "
                "O recrutador pode aprovar, rejeitar, ou enviar nova JD."
            ),
        )
        next_state["gate_clarify_message"] = (
            _sonnet_reply or output.conversational_reply
        )
    elif intent == "off_topic":
        _sonnet_reply = _try_meta_helper(
            state=state,
            stage="jd_enrichment",
            user_message=msg,
            stage_description=(
                "HITL #1: revisão da descrição enriquecida da vaga (JD). "
                "Recrutador desviou — trazer de volta para aprovação."
            ),
        )
        next_state["gate_clarify_message"] = (
            _sonnet_reply
            or output.conversational_reply
            or "Vamos focar na descrição da vaga? Você quer aprovar ou ajustar algo?"
        )
    else:
        # Defesa em profundidade — Pydantic Literal já blinda, mas se algo
        # vazar (ex.: bug futuro no schema) caímos no fallback de pergunta.
        logger.warning("[JobCreation:jd_gate] unhandled intent=%r → clarify", intent)
        next_state["gate_clarify_message"] = (
            "Não consegui interpretar sua resposta. Pode me dizer se aprovou "
            "a descrição enriquecida ou se quer ajustar alguma coisa?"
        )

    return next_state

