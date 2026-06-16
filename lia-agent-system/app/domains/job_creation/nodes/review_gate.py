"""review_gate_node canonical - PR-10 split (2026-05-26).

Movido de graph.py durante refactor estrutural ONDA 3 sub-sprint B.
Mantem comportamento byte-identical via tests de regressao.

Gate post review to capture recruiter approval/changes and route to publish or rework.
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
from app.domains.job_creation.internal.constants import _REVIEW_VALID_TARGET_SECTIONS
from app.domains.job_creation.helpers.async_audit import (
    emit_audit_fire_and_forget,
    run_coro_in_threadpool,
)
from app.domains.job_creation.helpers.llm_exceptions import (
    classify_llm_exception_reason,
)

logger = logging.getLogger(__name__)


def review_gate_node(state: JobCreationState) -> JobCreationState:
    """T6 (Task #1088) — gate LLM-based para HITL #3 (review/publish).

    Substitui a heurística keyword-based de ``domain.py::_route_by_stage``
    para o stage ``review``/``publish`` (linhas 'public'/'manda'/'publica')
    quando o flag ``LIA_WIZARD_LLM_GATES`` está ON. Allowlist específica
    do stage (``STAGE_ALLOWLISTS["review"]``):

      - ``publish_now``           → DUPLA CONFIRMAÇÃO via chat:
                                    1ª chamada: seta ``pending_publish_confirmation=True``
                                    + ``publish_confirmation_ts=now()``; route=END,
                                    pede confirmação na clarify message.
                                    2ª chamada (mesmo intent) DENTRO do TTL
                                    (300s) com flag set: seta
                                    ``policy_confirmed_publish=True`` (que
                                    destrava o publish_node PolicyGate);
                                    route=publish.
      - ``request_changes``       → mapeia ``target_section`` → nó destino
                                    via ``_REVIEW_TARGET_SECTION_TO_NODE``;
                                    limpa flag de aprovação correspondente
                                    (jd_approved/questions_approved/etc) e
                                    persiste ``review_request_changes_pending``.
      - ``configure_destinations`` → valida ``destinations`` contra
                                    ``_REVIEW_DESTINATIONS_ALLOWLIST``;
                                    seta ``publish_platforms=destinations``;
                                    route=END (espera publish_now).
      - ``ask_clarification``     → state inalterado; ``gate_clarify_message=...``
                                    route=END.

    Confidence < 0.7 → re-pergunta natural sem mutar pacote.
    Resume detection mirroring wsi_questions_gate_node: ``current_stage="review"``
    + user_query fresh (não processado nesta invocação).

    Audit row registra ``confirmation_method`` ∈ {chat, button, dual}
    em ``criteria_used`` (SOX 7 anos retention via decision_type=
    ``wizard_step_completed``).
    """
    # Pendencia 5 (2026-05-27): lazy import de graph.py (circular import risk).
    from app.domains.job_creation.graph import _PUBLISH_DUAL_CONFIRMATION_TTL_S

    # Deferred imports to avoid circular dependency with graph.py module-level state.
    from app.domains.job_creation.graph import (
        _emit_review_gate_audit,
        _extract_last_turns,
        _in_graph_runtime,
        _resolve_effective_destinations_allowlist,
        _try_meta_helper,
    )

    # T6 (post-review fix #1) — ``review_request_changes_pending`` é
    # transiente por definição: setado pelo gate, consumido por
    # ``route_after_review_gate`` UMA vez, e a partir daí é estale. Se o
    # graph retornar a este nó (próximo turno do recrutador, ou um
    # passthrough sem mensagem), garantimos que NUNCA reroteamos com base
    # em estado antigo — limpamos no ENTRY. Sem isso, qualquer no-op
    # entrada em review_gate_node (sem resume_msg fresca) ainda routava para o
    # destino mapeado, criando reroute loops.
    _stale_pending = state.get("review_request_changes_pending")
    if _stale_pending:
        logger.debug(
            "[JobCreation:review_gate] clearing stale review_request_changes_pending on entry: %r",
            _stale_pending,
        )

    resume_msg = (state.get("gate_resume_message") or "").strip()
    if not resume_msg:
        # WS resume detection — caminho canônico via process_message não
        # seta gate_resume_message; detectamos via state nativo.
        _at_review = state.get("current_stage") == "review"
        _uq = (state.get("user_query") or "").strip()
        _seen = (state.get("gate_seen_user_query") or "").strip()
        _is_fresh_turn = bool(_uq) and _uq != _seen
        if _at_review and _is_fresh_turn:
            resume_msg = _uq
            logger.info(
                "[JobCreation:review_gate] WS resume detected (review + fresh user_query) — classify",
            )
    if not resume_msg and _in_graph_runtime():
        # Task #1094 — pausa canônica via interrupt() (HITL #3 — review/publish).
        from langgraph.types import interrupt
        _resume = interrupt({
            "type": "approval",
            "stage": "review",
            "data": {
                "readiness_check": state.get("readiness_check"),
                "ws_stage_payload": state.get("ws_stage_payload"),
            },
        })
        resume_msg = (str(_resume) if _resume is not None else "").strip()
    if not resume_msg:
        _last_intent = state.get("gate_last_intent")
        _is_transitional = _last_intent in ("ask_clarification",)
        clean_state = {
            **state,
            "current_stage": "review",
            # Garante limpeza mesmo no early-return.
            "review_request_changes_pending": None,
        }
        if _is_transitional:
            clean_state["gate_last_intent"] = None
        logger.info(
            "[JobCreation:review_gate] no resume message — END (waiting for user, prior_intent=%s, cleared=%s)",
            _last_intent, _is_transitional,
        )
        return clean_state

    # FairnessGuard L1 sobre a mensagem do gate (defesa em profundidade).
    try:
        from app.shared.compliance.fairness_guard import FairnessGuard
        _fg = FairnessGuard().check(resume_msg)
        if _fg.is_blocked:
            logger.warning(
                "[JobCreation:review_gate] FairnessGuard L1 BLOCK on resume message: cat=%s, terms=%s",
                _fg.category, _fg.blocked_terms,
            )
            return {
                **state,
                "gate_resume_message": "",
                "gate_clarify_message": _fg.educational_message,
                "fairness_blocked": True,
                "fairness_block_reason": _fg.educational_message,
                "current_stage": "review",
            }
    except Exception as exc:
        logger.debug("[JobCreation:review_gate] FairnessGuard check failed (fail-open): %s", exc)

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
            stage="review",
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
        logger.warning("[JobCreation:review_gate] classify failed (fallback): %s", exc)
        output = _make_fallback()

    # Confidence floor — clarify sem mutar pacote.
    # Sprint F.2 fix — threshold lower do que demais gates (0.55 vs 0.7).
    # Review gate tem espaço de intent menor (publish_now / request_changes /
    # configure_destinations / ask_clarification) — menos ambiguidade
    # justifica threshold relaxado. Bug F2 E2E 2026-05-20: classifier
    # retornava confidence=0.65 em "aprovado, pode publicar a vaga"
    # (frase canonical) — threshold 0.7 era over-aggressive.
    if (output.confidence or 0.0) < 0.55:
        logger.info(
            "[JobCreation:review_gate] confidence=%.2f < 0.55 → clarify (intent=%s)",
            output.confidence, output.intent,
        )
        clarify_state = {
            **state,
            "gate_resume_message": "",
            "gate_clarify_message": (
                output.conversational_reply
                or msg("review_gate.clarify_default")
            ),
            "gate_last_intent": output.intent,
            "gate_last_confidence": output.confidence,
            "current_stage": "review",
            "gate_seen_user_query": resume_msg,
        }
        try:
            _emit_review_gate_audit(state, resume_msg, output, confirmation_method="chat")
        except Exception as exc:
            logger.debug("[JobCreation:review_gate] audit emit failed: %s", exc)
        return clarify_state

    intent = output.intent
    extracted = output.extracted_data or {}

    next_state: dict = {
        **state,
        "gate_resume_message": "",
        "gate_clarify_message": None,
        "gate_last_intent": intent,
        "gate_last_confidence": output.confidence,
        "current_stage": "review",
        "gate_seen_user_query": resume_msg,
        # T6 (post-review fix #1) — sempre nasce limpo neste turno.
        # Quem precisar (request_changes não-destinations) seta logo abaixo.
        "review_request_changes_pending": None,
    }
    confirmation_method = "chat"

    if intent == "publish_now":
        # T6 (post-review #2 fix) — HARD readiness gate. Antes de qualquer
        # dual-confirmation, validar que o pacote está pronto. Se não, NÃO
        # avança para pending; emite ask_clarification determinístico que
        # cita exatamente o que falta (readiness_check.missing). Sem isso,
        # o recrutador poderia destravar publish mesmo com pacote incompleto
        # — viola Inegociável de governança da plataforma (consequential
        # decision gate em hiring flow).
        _readiness = state.get("readiness_check") or {}
        if not _readiness.get("ready"):
            _missing = _readiness.get("missing") or []
            _missing_pt = {
                "jd_approved": msg("review_gate.missing_field_jd_approved"),
                "questions_approved": msg("review_gate.missing_field_questions_approved"),
                "has_questions": msg("review_gate.missing_field_has_questions"),
                "has_seniority": "senioridade definida",
                "quality_score_ok": msg("review_gate.missing_field_quality_score_ok"),
            }
            _missing_str = ", ".join(_missing_pt.get(k, k) for k in _missing) or "configurações pendentes"
            next_state["pending_publish_confirmation"] = False
            next_state["publish_confirmation_ts"] = None
            next_state["policy_confirmed_publish"] = False
            # Reclassifica como ask_clarification para o audit trail
            # (intent original publish_now ficou em gate_last_intent acima).
            next_state["gate_clarify_message"] = msg("review_gate.missing_fields_publish_blocked", missing=_missing_str)
            confirmation_method = "chat"
            logger.info(
                "[JobCreation:review_gate] publish_now BLOCKED — readiness not ready, missing=%s",
                _missing,
            )
            try:
                _emit_review_gate_audit(state, resume_msg, output, confirmation_method=confirmation_method)
            except Exception as exc:
                logger.debug("[JobCreation:review_gate] audit emit failed: %s", exc)
            return next_state

        import time as _time
        _now = _time.time()
        _pending = bool(state.get("pending_publish_confirmation"))
        _ts = state.get("publish_confirmation_ts") or 0.0
        # F-2.4 (P0-#4): clock-skew guard for dual-confirmation TTL.
        # `_now - _ts` pode ser negativo (clock voltou no tempo via NTP correction)
        # ou >> TTL drástico (worker restart, deploy delay, pgbouncer reconnect,
        # timestamp persistido em DB com tz diferente). Clip preserva dual-confirm
        # em janela canonical [0, 2*TTL] + warn quando age > TTL pra observability.
        _ts_age = max(0.0, min(_now - float(_ts), 2.0 * _PUBLISH_DUAL_CONFIRMATION_TTL_S))
        _within_ttl = _pending and _ts_age <= _PUBLISH_DUAL_CONFIRMATION_TTL_S
        if _pending and _ts_age > _PUBLISH_DUAL_CONFIRMATION_TTL_S:
            logger.warning(
                "[review_gate] dual-confirm TTL excedido: age=%.1fs > TTL=%ds — "
                "exigindo nova confirmação. clock-skew suspeita se age >> TTL.",
                _ts_age, int(_PUBLISH_DUAL_CONFIRMATION_TTL_S),
            )
        if _within_ttl:
            # 2ª confirmação dentro da janela → destrava publish_node.
            next_state["policy_confirmed_publish"] = True
            next_state["pending_publish_confirmation"] = False
            next_state["publish_confirmation_ts"] = None
            # T6 — propaga confirmation_method para o publish_node final
            # audit (rastreabilidade SOX 7y).
            next_state["publish_confirmation_method"] = "dual"
            # Sprint M fix (2026-05-21): on dual-confirmation success, clear
            # gate_clarify_message + gate_last_intent so the downstream
            # publish_node "Vaga publicada com sucesso!" message wins
            # over the LLM"s chatty conversational_reply (which often
            # reads as a THIRD-confirmation request, e.g. "Vou publicar...
            # só me confirma uma última vez"). The dual-confirmation
            # branch is fully deterministic — no need for LLM text here.
            next_state["gate_clarify_message"] = None
            next_state["gate_last_intent"] = None
            confirmation_method = "dual"
            logger.info(
                "[JobCreation:review_gate] publish_now SECOND turn within TTL — confirmed (route=publish, gate_clarify_message cleared so publish_node message wins)",
            )
        else:
            # 1ª confirmação (ou expirada) → SETA pending + pede confirmação.
            # T6 (post-review fix #3) — mensagem DETERMINÍSTICA com sumário
            # do pacote (título, faixa salarial, # de questões WSI, destinos).
            # Não delega ao conversational_reply do LLM (que pode omitir
            # campos críticos). Auditável e estável para evals.
            next_state["pending_publish_confirmation"] = True
            next_state["publish_confirmation_ts"] = _now
            next_state["policy_confirmed_publish"] = False
            _jd = state.get("jd_enriched") or {}
            _title = (
                _jd.get("titulo_padronizado")
                or state.get("parsed_title")
                or msg("review_gate.no_title_fallback")
            )
            _smin = state.get("salary_min")
            _smax = state.get("salary_max")
            _scur = state.get("salary_currency") or "BRL"
            if _smin and _smax:
                _salary = f"{_scur} {_smin:,}–{_smax:,}".replace(",", ".")
            elif _smin:
                _salary = f"{_scur} a partir de {_smin:,}".replace(",", ".")
            else:
                _salary = msg("review_gate.salary_not_defined")
            _q_total = len(state.get("wsi_questions") or [])
            _dests = state.get("publish_platforms") or []
            _dests_str = ", ".join(_dests) if _dests else "os canais configurados"
            next_state["gate_clarify_message"] = (
                f"Pronto pra publicar:\n"
                f"• Vaga: {_title}\n"
                f"• Salário: {_salary}\n"
                f"• Questões WSI: {_q_total}\n"
                f"• Canais: {_dests_str}\n"
                f"Confirma para publicar agora?"
            )
            confirmation_method = "chat"
            logger.info(
                "[JobCreation:review_gate] publish_now FIRST turn — pending confirmation (TTL=%.0fs)",
                _PUBLISH_DUAL_CONFIRMATION_TTL_S,
            )

    elif intent == "request_changes":
        target = str(extracted.get("target_section") or "").strip().lower()
        instruction = str(extracted.get("instruction") or "").strip()[:500]
        if target not in _REVIEW_VALID_TARGET_SECTIONS or not instruction:
            logger.info(
                "[JobCreation:review_gate] request_changes schema inválido (target=%r, instr_len=%d) → clarify",
                target, len(instruction),
            )
            valid_sections = ", ".join(sorted(_REVIEW_VALID_TARGET_SECTIONS))
            next_state["gate_clarify_message"] = (
                msg("review_gate.request_changes_clarify", valid_sections=valid_sections)
            )
        elif target == "destinations":
            # Inline-handled: NÃO há nó destino para "destinations" — pedimos
            # imediatamente a lista de canais (próximo turno cai em
            # ``configure_destinations``). Resolvemos a allowlist tenant-aware
            # para listar SOMENTE canais que o tenant tem habilitados.
            allow_eff, is_tenant = _resolve_effective_destinations_allowlist(state)
            allow_str = ", ".join(sorted(allow_eff))
            scope = msg("review_gate.tenant_scope") if is_tenant else msg("review_gate.available_scope")
            next_state["review_request_changes_pending"] = {
                "target_section": "destinations",
                "instruction": instruction,
            }
            next_state["gate_clarify_message"] = (
                msg("review_gate.channels_ask", scope_capitalized=scope.capitalize(), allow_str=allow_str)
            )
            next_state["pending_publish_confirmation"] = False
            next_state["publish_confirmation_ts"] = None
        else:
            next_state["review_request_changes_pending"] = {
                "target_section": target,
                "instruction": instruction,
            }
            # Limpa flag de aprovação da seção correspondente para forçar
            # re-execução do nó destino na próxima invocação do graph.
            # T6 (post-review fix #2) — para title/description também
            # invalidamos jd_enriched, senão jd_enrichment_node pula a
            # re-geração (linha 607: ``if state.get("jd_enriched"): pula``)
            # e o ajuste cirúrgico nunca é aplicado. A instruction fica
            # disponível em ``review_request_changes_pending["instruction"]``
            # para o nó destino consultar (read-only hint cirúrgico).
            if target in ("title", "description"):
                next_state["jd_approved"] = None
                next_state["jd_enriched"] = None
                next_state["jd_quality_score"] = None
                next_state["jd_quality_warnings"] = []
            elif target == "questions":
                next_state["questions_approved"] = None
                next_state["wsi_regenerate_pending"] = True
                next_state["wsi_questions"] = []
            elif target == "salary":
                next_state["salary_min"] = None
                next_state["salary_max"] = None
            # pipeline: sem flag global a limpar — o nó eligibility lê
            # ``review_request_changes_pending`` como hint cirúrgico.
            next_state["gate_clarify_message"] = (
                output.conversational_reply
                or f"Beleza, vou voltar em {target} pra ajustar ({instruction[:60]})."
            )
            # Reseta dual-confirmation se houver — recrutador pediu mudança.
            next_state["pending_publish_confirmation"] = False
            next_state["publish_confirmation_ts"] = None

    elif intent == "configure_destinations":
        raw_dests = extracted.get("destinations") or []
        if not isinstance(raw_dests, list):
            raw_dests = []
        # T6 — tenant-aware validation: intersect com canônica + ATS habilitados.
        allow_eff, is_tenant_constrained = _resolve_effective_destinations_allowlist(state)
        normalized = [str(d).strip().lower() for d in raw_dests]
        valid = [d for d in normalized if d in allow_eff]
        rejected = [d for d in normalized if d and d not in allow_eff]
        # Dedup preservando ordem.
        seen = set()
        valid_dedup = []
        for d in valid:
            if d not in seen:
                seen.add(d)
                valid_dedup.append(d)
        if not valid_dedup:
            allowed_str = ", ".join(sorted(allow_eff))
            scope = msg("review_gate.tenant_scope") if is_tenant_constrained else msg("review_gate.available_scope")
            if rejected:
                rej_str = ", ".join(sorted(set(rejected)))
                next_state["gate_clarify_message"] = (
                    msg("review_gate.channels_rejected", rej_str=rej_str, scope=scope, scope_capitalized=scope.capitalize(), allowed_str=allowed_str)
                )
            else:
                next_state["gate_clarify_message"] = (
                    msg("review_gate.channels_ask_fallback", scope_capitalized=scope.capitalize(), allowed_str=allowed_str)
                )
        else:
            next_state["publish_platforms"] = valid_dedup
            # Limpa o request_changes pending — destinos foram resolvidos.
            next_state["review_request_changes_pending"] = None
            if rejected:
                rej_str = ", ".join(sorted(set(rejected)))
                scope = "habilitados pelo seu tenant" if is_tenant_constrained else "disponíveis"
                next_state["gate_clarify_message"] = (
                    msg("review_gate.channels_partial_ok", valid_channels=", ".join(valid_dedup), rej_str=rej_str, scope=scope)
                    + msg("review_gate.missing_fields_summary").replace("publica", "confirma")
                )
            else:
                next_state["gate_clarify_message"] = (
                    output.conversational_reply
                    or msg("review_gate.channels_ok", valid_channels=", ".join(valid_dedup))
                )
            # Reseta dual-confirmation — destinos mudaram.
            next_state["pending_publish_confirmation"] = False
            next_state["publish_confirmation_ts"] = None

    elif intent == "ask_clarification":
        # Task #1123 — resposta rica via Sonnet (tenant + history-aware).
        # Fail-OPEN para o reply do classifier se Sonnet falhar.
        _sonnet_reply = _try_meta_helper(
            state=state,
            stage="review",
            user_message=resume_msg,
            stage_description=(
                "HITL #4: revisão final da vaga antes da publicação. "
                "Recrutador pode publicar, ajustar campo específico, "
                "trocar destinos de publicação, ou pedir esclarecimento."
            ),
        )
        next_state["gate_clarify_message"] = (
            _sonnet_reply
            or output.conversational_reply
            or msg("review_gate.explain_clarify")
        )

    else:
        logger.warning("[JobCreation:review_gate] unhandled intent=%r → clarify", intent)
        next_state["gate_clarify_message"] = (
            msg("review_gate.final_clarify")
        )

    # Audit row (best-effort) — confirmation_method é o discriminador SOX
    # entre "chat single turn", "dual chat confirmation" e "button"
    # (button é setado externamente via _handle_gate_review quando o FE
    # emite um sinal explícito de botão).
    try:
        _emit_review_gate_audit(state, resume_msg, output, confirmation_method=confirmation_method)
    except Exception as exc:
        logger.debug("[JobCreation:review_gate] audit emit failed: %s", exc)

    return next_state

