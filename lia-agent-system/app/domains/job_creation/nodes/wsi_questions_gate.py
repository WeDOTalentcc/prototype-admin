"""wsi_questions_gate_node canonical - PR-10 split (2026-05-26).

Movido de graph.py durante refactor estrutural ONDA 3 sub-sprint B.
Mantem comportamento byte-identical via tests de regressao.

Gate post wsi_questions to capture recruiter feedback.
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

logger = logging.getLogger(__name__)

# ── Task #1089 — geração cirúrgica + hard gate de mínimo ─────────────────────
_BEHAVIORAL_TOPIC_HINTS = (
    "lideran", "comunica", "colabora", "equipe", "time", "conflito",
    "pressao", "pressão", "resilien", "adapta", "empatia", "negocia",
    "feedback", "autonomia", "proativ", "organiza", "prazo", "etica", "ética",
    "relacion", "influen", "mentor",
)


def _infer_block_from_topic(topic: str) -> str:
    """Heurística leve (computacional) para classificar o tópico de uma pergunta
    nova em técnica vs comportamental. O recrutador revisa antes de aprovar."""
    t = (topic or "").lower()
    return "behavioral" if any(h in t for h in _BEHAVIORAL_TOPIC_HINTS) else "technical"


def _mode_min_total(state: "JobCreationState"):
    """(mode, mínimo de perguntas TOTAL do modo) — compact=7, full=12."""
    from app.domains.job_creation.helpers.screening_mode_config import SCREENING_MODE_CONFIG
    mode = state.get("screening_mode") or "compact"
    cfg = SCREENING_MODE_CONFIG.get(mode) or SCREENING_MODE_CONFIG["compact"]
    return mode, cfg["total_questions"]


def _surgical_ctx(state: "JobCreationState"):
    """(generator, enriched, seniority, trait_rankings) p/ geração cirúrgica.

    Retorna (None, None, None, None) quando jd_enriched ausente — o caller faz
    fail-soft (mantém o pacote + clarify), nunca quebra o gate.
    """
    try:
        from app.domains.job_creation.graph import _get_wsi_generator
        from app.domains.job_creation.schemas import EnrichedJobDescription
        jd = state.get("jd_enriched") or {}
        if not jd:
            return None, None, None, None
        enriched = EnrichedJobDescription(**jd)
        return (
            _get_wsi_generator(), enriched,
            state.get("seniority_resolved") or "pleno",
            state.get("trait_rankings") or [],
        )
    except Exception as exc:  # noqa: BLE001 — fail-soft
        logger.warning("[wsi_questions_gate] surgical ctx unavailable: %s", exc)
        return None, None, None, None



def wsi_questions_gate_node(state: JobCreationState) -> JobCreationState:
    """T5 (Task #1087) — gate LLM-based para HITL #2 (wsi_questions).

    Substitui a heurística keyword-based em ``domain.py::_route_by_stage``
    (linhas 'aprov'/'aceito'/'regener'/'refaz') quando o flag
    ``LIA_WIZARD_LLM_GATES`` está ON. Allowlist específica do stage
    (definida em ``STAGE_ALLOWLISTS["wsi_questions"]``):

      - ``approve_all``             → ``questions_approved=True`` (→ eligibility)
      - ``regenerate_all``          → ``questions_approved=False`` +
                                      ``wsi_questions=[]`` +
                                      ``wsi_regenerate_pending=True``
                                      (→ wsi_questions full regen)
      - ``edit_specific_question``  → ``wsi_questions_pending_edit=
                                      {index, instruction}`` +
                                      ``wsi_regenerate_pending=True`` +
                                      ``questions_approved=False`` +
                                      ``wsi_questions=[]``
                                      (→ wsi_questions regen advisory)
      - ``add_question``            → ``wsi_questions_pending_add=
                                      {topic}`` +
                                      ``wsi_regenerate_pending=True`` +
                                      ``questions_approved=False`` +
                                      ``wsi_questions=[]``
                                      (→ wsi_questions regen advisory)
      - ``remove_question``         → splice in-state por question_index
                                      (1-based) + ``questions_approved=
                                      None`` (→ END, aguarda aprovação
                                      do pacote reduzido no próximo turno)
      - ``ask_question``            → state inalterado;
                                      ``gate_clarify_message=...``

    NOTA T5/cirurgia: ``edit_specific_question`` e ``add_question``
    persistem markers (``wsi_questions_pending_edit`` /
    ``wsi_questions_pending_add``) no state mas ATUALMENTE disparam
    full regen via ``wsi_regenerate_pending``. A geração cirúrgica
    (one-question replace/append usando os markers como hint) está
    deixada como follow-up Task #1089 — o contrato de state está
    estável e o classifier já produz o schema correto.

    Confidence < 0.7 → re-pergunta natural sem mutar pacote.
    Resume detection mirroring competency_gate_node: ``current_stage=
    "wsi_questions"`` + ``wsi_questions`` truthy + user_query fresh.
    """
    # Deferred imports to avoid circular dependency with graph.py module-level state.
    from app.domains.job_creation.graph import (
        _extract_last_turns,
        _in_graph_runtime,
        _try_meta_helper,
        _emit_wsi_questions_gate_audit,
    )

    resume_msg = (state.get("gate_resume_message") or "").strip()
    if not resume_msg:
        _at_wsi = (
            state.get("current_stage") == "wsi_questions"
            and bool(state.get("wsi_questions"))
        )
        _no_decision_yet = state.get("questions_approved") is None
        _uq = (state.get("user_query") or "").strip()
        _seen = (state.get("gate_seen_user_query") or "").strip()
        _is_fresh_turn = bool(_uq) and _uq != _seen
        if _at_wsi and _no_decision_yet and _is_fresh_turn:
            resume_msg = _uq
            logger.info(
                "[JobCreation:wsi_questions_gate] WS resume detected (wsi_questions + fresh user_query, awaiting decision) — classify",
            )
    if not resume_msg and _in_graph_runtime():
        # Task #1094 — pausa canônica via interrupt() (HITL #2 — WSI questions).
        from langgraph.types import interrupt
        _resume = interrupt({
            "type": "approval",
            "stage": "wsi_questions",
            "data": {
                "wsi_questions": state.get("wsi_questions"),
                "screening_mode": state.get("screening_mode"),
            },
        })
        resume_msg = (str(_resume) if _resume is not None else "").strip()
    if not resume_msg:
        _last_intent = state.get("gate_last_intent")
        _is_transitional = _last_intent in ("ask_question",)
        clean_state = {**state, "current_stage": "wsi_questions"}
        if _is_transitional:
            clean_state["gate_last_intent"] = None
        logger.info(
            "[JobCreation:wsi_questions_gate] no resume message — END (waiting for user, prior_intent=%s, cleared=%s)",
            _last_intent, _is_transitional,
        )
        return clean_state

    # FairnessGuard L1 sobre a mensagem do gate (defesa em profundidade).
    try:
        from app.shared.compliance.fairness_guard import FairnessGuard
        _fg = FairnessGuard().check(resume_msg)
        if _fg.is_blocked:
            logger.warning(
                "[JobCreation:wsi_questions_gate] FairnessGuard L1 BLOCK on resume message: cat=%s, terms=%s",
                _fg.category, _fg.blocked_terms,
            )
            return {
                **state,
                "gate_resume_message": "",
                "gate_clarify_message": _fg.educational_message,
                "fairness_blocked": True,
                "fairness_block_reason": _fg.educational_message,
                "current_stage": "wsi_questions",
            }
    except Exception as exc:
        logger.debug("[JobCreation:wsi_questions_gate] FairnessGuard check failed (fail-open): %s", exc)

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
            stage="wsi_questions",
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
    # Fallback path is fail-soft and feeds into the clarify HITL branch
    # below (confidence < 0.7 surfaces a real question to the recruiter).
    # See REGRA-4-EXEMPT marker on the clarify return for sensor opt-out.
    except Exception as exc:
        logger.warning("[JobCreation:wsi_questions_gate] classify failed (fallback): %s", exc)
        output = _make_fallback()

    # Audit row (best-effort).
    try:
        _emit_wsi_questions_gate_audit(state, resume_msg, output)
    except Exception as exc:
        logger.debug("[JobCreation:wsi_questions_gate] audit emit failed: %s", exc)

    current_questions = list(state.get("wsi_questions") or [])
    total_q = len(current_questions)

    # Confidence floor — clarify sem mutar pacote.
    if (output.confidence or 0.0) < 0.7:
        logger.info(
            "[JobCreation:wsi_questions_gate] confidence=%.2f < 0.7 → clarify (intent=%s)",
            output.confidence, output.intent,
        )
        # HITL clarify, not silent fallback. `output` pode ter vindo do
        # except `_make_fallback()` (confidence=0.0) ou do classifier real
        # com confidence baixa. Em AMBOS os casos, surfa pergunta real pro
        # recrutador (clarify_message) — fluxo HITL canonical, sem mascarar
        # falha como sucesso.
        # REGRA-4-EXEMPT (Wave D2.3): HITL clarify return — fallback_used flag
        # não aplicável (resposta é clarify message, não envelope de sucesso).
        return {
            **state,
            "gate_resume_message": "",
            "gate_clarify_message": (
                output.conversational_reply
                or msg("wsi_questions_gate.approve_or_regen")
            ),
            "gate_last_intent": output.intent,
            "gate_last_confidence": output.confidence,
            "current_stage": "wsi_questions",
            "gate_seen_user_query": resume_msg,
        }

    intent = output.intent
    extracted = output.extracted_data or {}

    # Validação determinística de question_index 1-based vs len(wsi_questions).
    def _valid_index(raw) -> int | None:
        try:
            idx = int(raw)
        except (TypeError, ValueError):
            return None
        if total_q <= 0:
            return None
        if idx < 1 or idx > total_q:
            return None
        return idx

    next_state: dict = {
        **state,
        "gate_resume_message": "",
        "gate_clarify_message": None,
        "gate_last_intent": intent,
        "gate_last_confidence": output.confidence,
        "current_stage": "wsi_questions",
        "gate_seen_user_query": resume_msg,
    }

    if intent == "approve_all":
        _mode, _min_total = _mode_min_total(state)
        if total_q < _min_total:
            # Hard gate: não aprova abaixo do mínimo do modo. Auto-completa as
            # faltantes (cobrindo competências confirmadas não cobertas) e pede
            # re-aprovação do pacote completo.
            _gen, _enr, _sen, _tr = _surgical_ctx(state)
            _added = []
            if _gen is not None and _enr is not None:
                try:
                    _missing = _gen.generate_missing_questions(
                        enriched=_enr, seniority=_sen,
                        existing_questions=current_questions,
                        screening_mode=_mode, trait_rankings=_tr,
                    )
                    _added = [m.model_dump() for m in _missing]
                except Exception as _ac_exc:  # noqa: BLE001 — fail-soft
                    logger.warning("[wsi_questions_gate] auto-complete failed: %s", _ac_exc)
            if _added:
                _completed = current_questions + _added
                next_state["wsi_questions"] = _completed
                next_state["questions_approved"] = None
                next_state["wsi_regenerate_pending"] = False
                next_state["gate_clarify_message"] = (
                    f"O modo {_mode} exige no mínimo {_min_total} perguntas e havia {total_q}. "
                    f"Completei com {len(_added)} (total {len(_completed)}). Pode revisar e aprovar?"
                )
            else:
                next_state["questions_approved"] = None
                next_state["gate_clarify_message"] = (
                    f"O modo {_mode} exige no mínimo {_min_total} perguntas, mas há {total_q}. "
                    "Quer que eu gere as faltantes ou prefere ajustar?"
                )
        else:
            next_state["questions_approved"] = True
            next_state["wsi_regenerate_pending"] = False
            next_state["wsi_questions_pending_edit"] = None
            next_state["wsi_questions_pending_add"] = None
            next_state["gate_clarify_message"] = (
                output.conversational_reply
                or "Aprovado! Vou seguir para configurar as perguntas de elegibilidade."
            )

    elif intent == "regenerate_all":
        next_state["questions_approved"] = False
        next_state["wsi_questions"] = []
        next_state["wsi_regenerate_pending"] = True
        next_state["wsi_questions_pending_edit"] = None
        next_state["wsi_questions_pending_add"] = None
        next_state["gate_clarify_message"] = (
            output.conversational_reply
            or "Sem problema, vou regenerar o pacote inteiro agora."
        )

    elif intent == "edit_specific_question":
        idx = _valid_index(extracted.get("question_index"))
        instruction = str(extracted.get("instruction") or "").strip()[:500]
        if idx is None or not instruction:
            # Schema inválido → clarify sem mutar pacote.
            logger.info(
                "[JobCreation:wsi_questions_gate] edit_specific_question schema inválido (idx=%r, instr_len=%d) → clarify",
                extracted.get("question_index"), len(instruction),
            )
            next_state["gate_clarify_message"] = (
                msg("wsi_questions_gate.edit_question_clarify", total_q=total_q)
            )
        else:
            # Task #1089 — edição CIRÚRGICA: regenera só a pergunta `idx`,
            # preserva as demais. Mantém a metodologia WSI (mesma validação).
            _gen, _enr, _sen, _tr = _surgical_ctx(state)
            _base_q = current_questions[idx - 1]
            _block = (_base_q.get("block") if isinstance(_base_q, dict) else getattr(_base_q, "block", "technical")) or "technical"
            _new_q = None
            if _gen is not None and _enr is not None:
                _new_q = _gen.generate_single_question(
                    block=_block, enriched=_enr, seniority=_sen,
                    directive=instruction, base_question=_base_q, trait_rankings=_tr,
                )
            next_state["questions_approved"] = None
            next_state["wsi_regenerate_pending"] = False
            next_state["wsi_questions_pending_edit"] = None
            if _new_q is not None:
                _updated = list(current_questions)
                _updated[idx - 1] = _new_q.model_dump()
                next_state["wsi_questions"] = _updated
                next_state["gate_clarify_message"] = (
                    output.conversational_reply
                    or f"Ajustei a pergunta {idx}. Quer revisar o pacote e aprovar?"
                )
            else:
                # Fail-soft: mantém a original (nunca insere pergunta off-WSI).
                next_state["gate_clarify_message"] = (
                    f"Não consegui ajustar a pergunta {idx} mantendo a metodologia WSI. "
                    "Pode reformular o pedido?"
                )

    elif intent == "add_question":
        topic = str(extracted.get("topic") or "").strip()[:200]
        if not topic:
            logger.info(
                "[JobCreation:wsi_questions_gate] add_question sem topic → clarify",
            )
            next_state["gate_clarify_message"] = (
                msg("wsi_questions_gate.add_question_topic")
            )
        else:
            # Task #1089 — adição CIRÚRGICA: gera 1 pergunta nova e INCREMENTA
            # o pacote (N -> N+1), preservando as existentes.
            _gen, _enr, _sen, _tr = _surgical_ctx(state)
            _block = _infer_block_from_topic(topic)
            _new_q = None
            if _gen is not None and _enr is not None:
                _new_q = _gen.generate_single_question(
                    block=_block, enriched=_enr, seniority=_sen,
                    directive=topic, base_question=None, trait_rankings=_tr,
                )
                if _new_q is None:
                    try:
                        _new_q = _gen._fallback_questions(_block, 1)[0]
                    except Exception:  # noqa: BLE001
                        _new_q = None
            next_state["questions_approved"] = None
            next_state["wsi_regenerate_pending"] = False
            next_state["wsi_questions_pending_add"] = None
            if _new_q is not None:
                _updated = list(current_questions) + [_new_q.model_dump()]
                next_state["wsi_questions"] = _updated
                next_state["gate_clarify_message"] = (
                    output.conversational_reply
                    or f"Adicionei uma pergunta sobre {topic}. O pacote ficou com {len(_updated)}. Quer aprovar?"
                )
            else:
                next_state["gate_clarify_message"] = (
                    f"Não consegui gerar a pergunta sobre {topic} agora. Pode tentar de novo?"
                )

    elif intent == "remove_question":
        idx = _valid_index(extracted.get("question_index"))
        if idx is None:
            logger.info(
                "[JobCreation:wsi_questions_gate] remove_question índice inválido (%r, total=%d) → clarify",
                extracted.get("question_index"), total_q,
            )
            next_state["gate_clarify_message"] = (
                msg("wsi_questions_gate.remove_question_clarify", total_q=total_q)
            )
        else:
            new_questions = current_questions[: idx - 1] + current_questions[idx:]
            next_state["wsi_questions"] = new_questions
            # Não aprova nem regenera — aguarda aprovação do pacote reduzido.
            next_state["questions_approved"] = None
            next_state["wsi_regenerate_pending"] = False
            _mode, _min_total = _mode_min_total(state)
            if len(new_questions) < _min_total:
                next_state["gate_clarify_message"] = (
                    f"Removida a pergunta {idx}. O pacote ficou com {len(new_questions)} — "
                    f"o modo {_mode} pede no mínimo {_min_total}. Quando você aprovar, "
                    "eu completo as faltantes automaticamente (ou adicione/edite antes)."
                )
            else:
                next_state["gate_clarify_message"] = (
                    output.conversational_reply
                    or f"Removida a pergunta {idx}. O pacote ficou com {len(new_questions)} perguntas — me confirma se posso seguir."
                )

    elif intent == "ask_question":
        # Task #1123 — resposta rica via Sonnet (tenant + history-aware).
        _sonnet_reply = _try_meta_helper(
            state=state,
            stage="wsi_questions",
            user_message=resume_msg,
            stage_description=(
                f"HITL #3: revisão do pacote WSI gerado ({total_q} perguntas). "
                "Recrutador pode aprovar, regenerar tudo, editar/adicionar/remover uma."
            ),
        )
        next_state["gate_clarify_message"] = (
            _sonnet_reply
            or output.conversational_reply
            or msg("wsi_questions_gate.explain_clarify")
        )

    else:
        logger.warning("[JobCreation:wsi_questions_gate] unhandled intent=%r → clarify", intent)
        next_state["gate_clarify_message"] = (
            msg("wsi_questions_gate.final_clarify")
        )

    return next_state

