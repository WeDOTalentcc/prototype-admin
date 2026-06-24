"""wsi_questions_node canonical - PR-10 split (2026-05-26).

Movido de graph.py durante refactor estrutural ONDA 3 sub-sprint B.
Mantem comportamento byte-identical via tests de regressao.

Generate WSI screening questions via LLM + fallback templates.
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
from app.domains.job_creation.internal.constants import WSI_DEFAULT_DISTRIBUTION_COMPACT_PLENO
from app.domains.job_creation.helpers.async_audit import (
    emit_audit_fire_and_forget,
    run_coro_in_threadpool,
)
from app.domains.job_creation.helpers.llm_exceptions import (
    classify_llm_exception_reason,
)

logger = logging.getLogger(__name__)


def _wsi_source_decision(state: JobCreationState) -> tuple[str, list]:
    """Pure (sem LLM/graph): decide a FONTE das perguntas WSI. PR-B2b.

    - 'resume'     : perguntas ja aprovadas (resume path).
    - 'reuse_seed' : clone — reaproveitar perguntas da vaga origem
                     (state['seed_wsi_questions'], estacionadas por
                     apply_seed_to_state). Apresentadas no HITL #2; a
                     FairnessGuard L4 do node roda nelas (re-check free) e o
                     gate existente oferece aprovar/editar/gerar-novas — e o
                     "perguntar ao recrutador" sem nova state-machine.
    - 'generate'   : gerar via LLM (default / 'gerar novas').

    wsi_regenerate_pending (recrutador escolheu 'gerar novas' no gate) forca
    'generate' — por isso o reuse so dispara na PRIMEIRA entrada do estagio
    (wsi_questions ainda vazio).
    """
    if state.get("wsi_regenerate_pending"):
        return ("generate", [])
    if state.get("questions_approved") is not None and state.get("wsi_questions"):
        return ("resume", list(state.get("wsi_questions") or []))
    if not state.get("wsi_questions") and state.get("seed_wsi_questions"):
        return ("reuse_seed", list(state.get("seed_wsi_questions") or []))
    return ("generate", [])


def wsi_questions_node(state: JobCreationState) -> JobCreationState:
    """F6: Generate WSI screening questions via LLM.

    This is HITL point 2 — recruiter must approve all questions.

    WSI absolute rules enforced:
    - CBI only (no hypothetical questions)
    - No cultural fit questions
    - Min questions per distribution table (F5)
    """
    # Deferred imports to avoid circular dependency with graph.py module-level state.
    from app.domains.job_creation.graph import (
        _emit_fallback_telemetry,
        _emit_wizard_fallback_metric,
        _emit_wizard_step_audit,
        _get_wsi_generator,
    )

    t0 = time.time()
    # PR-10 fix Fix J: lazy import de graph.py (circular import risk)
    # Pendencia 5 (2026-05-27): emit_policy_block_audit + l4_counter add aqui.
    from app.domains.job_creation.graph import (
        evaluate_wizard_policy,
        emit_policy_block_audit,
        lia_wizard_fairness_l4_check_failed_total,
    )

    logger.info("[JobCreation:wsi_questions] Starting F6")

    # Policy gate check
    from app.domains.job_creation.policy_gate import PolicyDecision, WizardIntent
    _wsi_policy = evaluate_wizard_policy(WizardIntent.GENERATE_WSI, state)
    _wsi_pd_decisions = (state.get("policy_decisions") or []) + [{
        "stage": "wsi_questions",
        "policy_decision": str(_wsi_policy.decision),
        "rationale": _wsi_policy.rationale,
    }]
    if _wsi_policy.decision == PolicyDecision.DENY:
        logger.warning("[PolicyGate:wsi_questions] DENY — %s", _wsi_policy.rationale)
        emit_policy_block_audit(stage="wsi_questions", decision=_wsi_policy)
        _wsi_pd_dict = {"policy_decision": str(_wsi_policy.decision), "rationale": _wsi_policy.rationale}
        return {
            **state,
            "policy_decisions": _wsi_pd_decisions,
            "wsi_questions": [],
            "error": f"WSI gen blocked: {_wsi_policy.rationale}",
            "pending_human_confirmation": False,
            "requires_approval": False,
            "ws_stage_payload": build_ws_stage_payload(
                stage="wsi_questions",
                completeness=0,
                requires_approval=False,
                data={
                    # Task #1099 — invariant: data.message obrigatório.
                    "message": msg("wsi_questions.policy_deny", rationale=_wsi_policy.rationale),
                    "policy_blocked": True,
                    "policy_decision": _wsi_pd_dict,
                },
            ),
        }
    _wsi_pending_hitl = (_wsi_policy.decision == PolicyDecision.HITL_REQUIRED)

    from app.domains.job_creation.schemas import EnrichedJobDescription

    # If already approved, skip re-generation (resume path).
    # T5 (Task #1087): respeitar `wsi_regenerate_pending` — quando o gate
    # LLM-based decide regenerar/editar/adicionar, ele seta esse marker
    # transitório no state pra forçar o node a re-rodar o generator
    # mesmo que `questions_approved` ou `wsi_questions` ainda estejam
    # populados de um turno anterior. O marker é limpo no fim do node.
    _force_regen = bool(state.get("wsi_regenerate_pending"))
    _wsi_src, _wsi_seed_data = _wsi_source_decision(state)
    _reused_from_source = False
    if _wsi_src == "resume":
        questions_data = list(state.get("wsi_questions") or [])
    elif _wsi_src == "reuse_seed":
        # PR-B2b: clone — reaproveitar perguntas da vaga origem. A FairnessGuard
        # L4 abaixo roda nelas; o gate da aprovar/editar/gerar-novas.
        questions_data = list(_wsi_seed_data)
        _reused_from_source = True
    else:
        jd_enriched_dict = state.get("jd_enriched", {})

        # ── FairnessGuard pre-check (WSI input) ──
        # If jd_enriched is discriminatory, do not call the LLM at all.
        _wsi_input_blocked = False
        if jd_enriched_dict:
            _wsi_pre_text = " ".join(filter(None, [
                jd_enriched_dict.get("about_role", ""),
                " ".join(jd_enriched_dict.get("responsabilidades", []) or []),
            ]))
            try:
                from app.shared.compliance.fairness_guard import FairnessGuard as _WSIFg
                _wsi_pre_check = _WSIFg().check(_wsi_pre_text)
                if _wsi_pre_check.is_blocked:
                    logger.warning(
                        "[JobCreation:wsi_questions] FairnessGuard PRE-BLOCK: category=%s — skipping LLM",
                        _wsi_pre_check.category,
                    )
                    _wsi_input_blocked = True
            except Exception as _wsi_pre_exc:
                logger.warning("[JobCreation:wsi_questions] FairnessGuard pre-check failed (fail-open): %s", _wsi_pre_exc)

        if _wsi_input_blocked:
            questions_data = []
        else:
            # ── PII masking (BEFORE LLM) ──
            _safe_wsi_dict = dict(jd_enriched_dict) if jd_enriched_dict else {}
            try:
                from app.domains.job_creation.compliance import mask_pii_for_llm as _wsi_mask
                for _f in ("about_role", "titulo_padronizado"):
                    if _safe_wsi_dict.get(_f):
                        _safe_wsi_dict[_f] = _wsi_mask(_safe_wsi_dict[_f])
                if _safe_wsi_dict.get("responsabilidades"):
                    _safe_wsi_dict["responsabilidades"] = [
                        _wsi_mask(r) if isinstance(r, str) else r
                        for r in _safe_wsi_dict["responsabilidades"]
                    ]
            except Exception as _wsi_pii_exc:
                logger.warning("[JobCreation:wsi_questions] PII masking failed (fail-open): %s", _wsi_pii_exc)

            enriched = EnrichedJobDescription(**_safe_wsi_dict) if _safe_wsi_dict else None
            # PR-11 F-4.7: fallback canonical via WSI_DEFAULT_DISTRIBUTION_COMPACT_PLENO
            # (constante top-level — alinhada com _get_question_distribution).
            distribution = state.get(
                "question_distribution", dict(WSI_DEFAULT_DISTRIBUTION_COMPACT_PLENO),
            )
            # Sprint F.4: defensive coerce — state may have None explicit; .get(default) only kicks in for MISSING keys.
            if not isinstance(distribution, dict):
                distribution = dict(WSI_DEFAULT_DISTRIBUTION_COMPACT_PLENO)
            seniority = state.get("seniority_resolved", "pleno")
            trait_rankings = state.get("trait_rankings", [])

            if enriched:
                generator = _get_wsi_generator()
                # Task #1062: timeout determinístico (D4 da auditoria #1058).
                # Em timeout cai no `_fallback_questions(block, count)` por
                # bloco — mantém o wizard avançando com perguntas mínimas
                # CBI-conformes para revisão humana (HITL #2 ainda exigido).
                import concurrent.futures as _cf_wq
                _WSI_LLM_TIMEOUT_S = float(__import__("os").environ.get(
                    "LIA_WSI_QUESTIONS_TIMEOUT_S", "120"
                ))
                # Task #1065 — flag de fallback determinístico (timeout LLM
                # → `_fallback_questions`). Painel renderiza banner pedindo
                # revisão extra antes da aprovação HITL.
                wsi_questions_used_fallback = False
                # Task #1067 — root-cause label propagado pro painel.
                wsi_questions_fallback_reason: Optional[str] = None
                # NOTE: shutdown(wait=False) — ver comentário em bigfive_node.
                _ex_wq = _cf_wq.ThreadPoolExecutor(max_workers=1)
                try:
                    try:
                        _fut_wq = _ex_wq.submit(
                            generator.generate_questions,
                            enriched=enriched,
                            seniority=seniority,
                            distribution=distribution,
                            trait_rankings=trait_rankings,
                        )
                        question_objs = _fut_wq.result(
                            timeout=_WSI_LLM_TIMEOUT_S
                        )
                    except _cf_wq.TimeoutError:
                        logger.warning(
                            "[JobCreation:wsi_questions] LLM timeout after %.1fs — "
                            "deterministic fallback (Task #1062)",
                            _WSI_LLM_TIMEOUT_S,
                        )
                        n_tech = distribution.get("technical", 5)
                        n_behav = distribution.get("behavioral", 2)
                        question_objs = []
                        if n_tech > 0:
                            question_objs.extend(
                                generator._fallback_questions("technical", n_tech)
                            )
                        if n_behav > 0:
                            question_objs.extend(
                                generator._fallback_questions("behavioral", n_behav)
                            )
                        wsi_questions_used_fallback = True
                        wsi_questions_fallback_reason = "timeout"
                        _emit_wizard_fallback_metric(
                            node="wsi_questions", state=state, reason="llm_timeout",
                            timeout_s=_WSI_LLM_TIMEOUT_S,
                            elapsed_ms=(time.time() - t0) * 1000,
                        )
                    except Exception as _wq_exc:  # noqa: BLE001 — fail-open
                        logger.warning(
                            "[JobCreation:wsi_questions] LLM call failed (%s) — fallback",
                            _wq_exc,
                        )
                        n_tech = distribution.get("technical", 5)
                        n_behav = distribution.get("behavioral", 2)
                        question_objs = []
                        if n_tech > 0:
                            question_objs.extend(
                                generator._fallback_questions("technical", n_tech)
                            )
                        if n_behav > 0:
                            question_objs.extend(
                                generator._fallback_questions("behavioral", n_behav)
                            )
                        wsi_questions_used_fallback = True
                        wsi_questions_fallback_reason = classify_llm_exception_reason(_wq_exc)
                        _emit_wizard_fallback_metric(
                            node="wsi_questions", state=state,
                            reason=f"llm_{wsi_questions_fallback_reason}",
                            timeout_s=_WSI_LLM_TIMEOUT_S,
                            elapsed_ms=(time.time() - t0) * 1000,
                        )
                finally:
                    _ex_wq.shutdown(wait=False)
                questions_data = [q.model_dump() for q in question_objs]
            else:
                questions_data = []

    # ── Layer 4: question fairness guard (per-question scan) ──
    # Removes biased questions and registers in wsi_dropped_questions for audit.
    _wsi_dropped: list[dict[str, Any]] = list(state.get("wsi_dropped_questions") or [])
    _wsi_kept: list[dict[str, Any]] = []
    try:
        from app.shared.compliance.fairness_guard import FairnessGuard
        _fg_q = FairnessGuard()
        for _q in questions_data:
            _q_text = _q.get("question", "") if isinstance(_q, dict) else ""
            if not _q_text:
                _wsi_kept.append(_q)
                continue
            _check = _fg_q.check(_q_text)
            if _check.is_blocked:
                _wsi_dropped.append({
                    "question": _q_text,
                    "category": _check.category,
                    "blocked_terms": _check.blocked_terms,
                    "message": _check.educational_message,
                })
                logger.warning(
                    "[JobCreation:wsi_questions] FairnessGuard L4 dropped question: "
                    "category=%s, terms=%s",
                    _check.category, _check.blocked_terms,
                )
            else:
                _wsi_kept.append(_q)
        questions_data = _wsi_kept
    except Exception as _fg_l4_exc:
        # PR-8 ONDA 3 / F-3.4: increment counter + structured log (era silent mute).
        if lia_wizard_fairness_l4_check_failed_total is not None:
            try:
                lia_wizard_fairness_l4_check_failed_total.labels(
                    node="wsi_questions",
                    reason=type(_fg_l4_exc).__name__,
                ).inc()
            except Exception:  # pragma: no cover - never block on metric
                pass
        logger.warning(
            "[JobCreation:wsi_questions] FairnessGuard L4 check failed (fail-open): %s",
            _fg_l4_exc,
            exc_info=True,
        )
        # On failure, keep all questions (don't lose recruiter's work)


    # ── Gate de distribuição mínima (metodologia WSI, Tarefa 3) ──
    # Valida que questions_data contém pelo menos o mínimo de perguntas técnicas
    # e comportamentais definido pela tabela de distribuição (_get_question_distribution).
    # Quando insuficiente registra distribution_gap no stage_data para o painel
    # renderizar um aviso de revisão ANTES de aprovar.
    _distribution_gap: Dict[str, Any] | None = None
    try:
        from app.domains.job_creation.helpers.wsi_distribution import block_distribution as _gqd
        _dist_mode = state.get("screening_mode", "compact") or "compact"
        _dist_seniority = state.get("seniority_resolved", "pleno") or "pleno"
        _expected_dist = _gqd(_dist_mode, _dist_seniority)
        _min_tech = _expected_dist.get("technical", 0)
        _min_behav = _expected_dist.get("behavioral", 0)

        _tech_count = sum(
            1 for q in questions_data
            if isinstance(q, dict) and q.get("block") in ("technical", "tecnica")
        )
        _behav_count = sum(
            1 for q in questions_data
            if isinstance(q, dict) and q.get("block") in ("behavioral", "comportamental")
        )

        if _tech_count < _min_tech or _behav_count < _min_behav:
            _distribution_gap = {
                "tech": {"current": _tech_count, "required": _min_tech},
                "behavioral": {"current": _behav_count, "required": _min_behav},
                "mode": _dist_mode,
                "seniority": _dist_seniority,
            }
            logger.warning(
                "[JobCreation:wsi_questions] distribution below minimum — "
                "tech %d/%d behavioral %d/%d (mode=%s seniority=%s)",
                _tech_count, _min_tech,
                _behav_count, _min_behav,
                _dist_mode, _dist_seniority,
                extra={
                    "tech_current": _tech_count,
                    "tech_required": _min_tech,
                    "behavioral_current": _behav_count,
                    "behavioral_required": _min_behav,
                },
            )
    except Exception as _dist_exc:
        logger.warning(
            "[JobCreation:wsi_questions] distribution gate failed (fail-open): %s",
            _dist_exc,
        )

    # Build ws_stage_payload data — include fairness_warning when questions were dropped
    _wsi_stage_data: Dict[str, Any] = {
        # Task #1099 — invariant: data.message obrigatório (parametrizada
        # pelo número de perguntas geradas + flag de fallback + dropped
        # count). Sem isso o WizardSessionService cai em
        # _emit_silent_fallback (Task #1089).
        "message": (
            msg("wsi_questions.ready_fallback_with_dropped", count=len(questions_data), dropped=len(_wsi_dropped))
            if locals().get("wsi_questions_used_fallback", False) and _wsi_dropped
            else msg("wsi_questions.ready_fallback", count=len(questions_data))
            if locals().get("wsi_questions_used_fallback", False)
            else msg("wsi_questions.ready_with_dropped", count=len(questions_data), dropped=len(_wsi_dropped))
            if _wsi_dropped
            else msg("wsi_questions.ready", count=len(questions_data))
        ),
        "questions": questions_data,
        "screening_mode": state.get("screening_mode"),
        "distribution": state.get("question_distribution"),
        # Task #1065 — flag de fallback determinístico para o painel
        # renderizar o banner "Sugestão mínima — revise".
        "wsi_questions_used_fallback": locals().get(
            "wsi_questions_used_fallback", False
        ),
        # Task #1067 — root-cause label.
        "wsi_questions_fallback_reason": locals().get(
            "wsi_questions_fallback_reason", None
        ),
        # Task #1070 — snapshot agregado de degradação (sessão/tenant).
        "ai_degraded_mode": _emit_fallback_telemetry(
            state,
            "wsi_questions",
            locals().get("wsi_questions_fallback_reason", None),
        ),
    }
    # PR-B2b: ao reaproveitar perguntas da vaga origem, a mensagem deixa claro e
    # o gate existente oferece aprovar/editar/gerar-novas (o "perguntar").
    if _reused_from_source:
        _wsi_stage_data["message"] = (
            f"Reaproveitei {len(questions_data)} pergunta(s) de triagem da vaga "
            "de origem. Quer manter (aprovar), editar, ou gerar novas?"
        )
        _wsi_stage_data["wsi_reused_from_source"] = True
    if _wsi_dropped:
        _wsi_stage_data["fairness_warning"] = {
            "kind": "questions_dropped",
            "dropped_count": len(_wsi_dropped),
        }
        _wsi_stage_data["dropped_questions"] = _wsi_dropped
    if _distribution_gap:
        _wsi_stage_data["distribution_gap"] = _distribution_gap

    updates: Dict[str, Any] = {
        "current_stage": "wsi_questions",
        "wsi_questions": questions_data,
        "wsi_dropped_questions": _wsi_dropped,
        "stage_history": (state.get("stage_history") or []) + ["wsi_questions"],
        "completeness": calculate_completeness("wsi_questions"),
        "requires_approval": True,
        "pending_human_confirmation": locals().get("_wsi_pending_hitl", False),
        "policy_decisions": locals().get("_wsi_pd_decisions", state.get("policy_decisions") or []),
        "ws_stage_payload": build_ws_stage_payload(
            stage="wsi_questions",
            completeness=calculate_completeness("wsi_questions"),
            requires_approval=True,
            data=_wsi_stage_data,
        ),
    }
    # Inject policy_decision into ws_stage_payload.data for HITL/ALLOW visibility
    if "_wsi_policy" in dir():
        _wsi_pd_data = {
            "policy_decision": {
                "policy_decision": str(_wsi_policy.decision),
                "rationale": _wsi_policy.rationale,
            }
        }
        updates["ws_stage_payload"]["data"].update(_wsi_pd_data)

    # ── Audit EU AI Act Art.13 — WSI questions generation decision ──
    try:
        import asyncio as _asyncio
        from app.shared.compliance.audit_service import AuditService
        _audit = AuditService()
        _company_id = str(state.get("workspace_id") or state.get("company_id") or "")
        if _company_id:
            emit_audit_fire_and_forget(
                lambda: _audit.log_decision(
                    company_id=_company_id,
                    agent_name="job_creation:wsi_questions",
                    decision_type="generate_wsi_questions",
                    action="generate_questions",
                    decision=f"generated_{len(questions_data)}_kept_{len(_wsi_dropped)}_dropped",
                    reasoning=[
                        f"distribution={state.get('question_distribution')}",
                        f"seniority={state.get('seniority_resolved')}",
                        f"dropped_by_fairness={len(_wsi_dropped)}",
                    ],
                    criteria_used=["distribution", "trait_rankings", "competency_tree",
                                   "fairness_layer4"],
                    job_vacancy_id=state.get("job_id"),
                    human_review_required=True,  # HITL 2
                )
            )
    except Exception as _audit_exc:
        logger.warning(
            "[JobCreation:wsi_questions] audit log failed (fail-open): %s", _audit_exc,
        )

    # ── Task #1061: wizard_step_completed audit (EU AI Act Art.13) ──
    _emit_wizard_step_audit(
        stage="wsi_questions",
        state=state,
        before={"questions_count": len(state.get("wsi_questions") or [])},
        after={
            "questions_count": len(questions_data),
            "dropped_count": len(_wsi_dropped),
        },
        reasoning_extra=[
            f"distribution={state.get('question_distribution')}",
            f"seniority={state.get('seniority_resolved')}",
            f"dropped_by_fairness={len(_wsi_dropped)}",
        ],
        criteria_used=["distribution", "trait_rankings", "competency_tree",
                       "fairness_layer4"],
        human_review_required=True,
    )

    elapsed = (time.time() - t0) * 1000
    logger.info("[JobCreation:wsi_questions] %d questions | %0.fms", len(questions_data), elapsed)
    return {**state, **updates}

