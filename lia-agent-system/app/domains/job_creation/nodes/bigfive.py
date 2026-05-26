"""bigfive_node canonical - PR-10 split (2026-05-26).

Movido de graph.py durante refactor estrutural ONDA 3 sub-sprint B.
Mantem comportamento byte-identical via tests de regressao.

Generate BigFive personality probes for the role.
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


def bigfive_node(state: JobCreationState) -> JobCreationState:
    """F2+F3: Extract Big Five profile from enriched JD + rank traits.

    F2: LLM extraction (temp=0.1)
    F3: Deterministic trait ranking formula
    """
    # Deferred imports to avoid circular dependency with graph.py module-level state.
    from app.domains.job_creation.graph import (
        _emit_fallback_telemetry,
        _emit_wizard_step_audit,
        _emit_wizard_fallback_metric,
        _get_wsi_generator,
        emit_policy_block_audit,
        evaluate_wizard_policy,
    )

    t0 = time.time()
    logger.info("[JobCreation:bigfive] Starting F2+F3")

    from app.domains.job_creation.schemas import EnrichedJobDescription

    jd_enriched_dict = state.get("jd_enriched", {})

    # ── FairnessGuard pre-check (bigfive input) ──
    # If jd_enriched already contains discriminatory text, skip LLM call.
    if jd_enriched_dict:
        _bf_text_parts = [
            jd_enriched_dict.get("about_role", ""),
            " ".join(jd_enriched_dict.get("responsabilidades", []) or []),
        ]
        _bf_text = " ".join(filter(None, _bf_text_parts))
        try:
            from app.shared.compliance.fairness_guard import FairnessGuard as _BFFg
            _bf_fg_result = _BFFg().check(_bf_text)
            if _bf_fg_result.is_blocked:
                logger.warning(
                    "[JobCreation:bigfive] FairnessGuard PRE-BLOCK: category=%s — skipping LLM",
                    _bf_fg_result.category,
                )
                # Task #1099 — invariant: todo retorno com current_stage
                # setado DEVE incluir ws_stage_payload.data.message truthy.
                # Sem isso o WizardSessionService cai em
                # _emit_silent_fallback (Task #1089).
                _bf_block_msg = (
                    "Detectei linguagem que pode ser discriminatória na "
                    "descrição enriquecida — vou pausar o mapeamento Big "
                    "Five para esta vaga. Revise a JD e me peça para retomar."
                )
                return {
                    **state,
                    "current_stage": "bigfive",
                    "ws_stage_payload": build_ws_stage_payload(
                        stage="bigfive",
                        completeness=0,
                        requires_approval=False,
                        data={
                            "message": _bf_block_msg,
                            "fairness_blocked": True,
                            "fairness_category": _bf_fg_result.category,
                        },
                    ),
                }
        except Exception as _bf_fg_exc:
            logger.warning("[JobCreation:bigfive] FairnessGuard pre-check failed (fail-open): %s", _bf_fg_exc)

    # ── PII masking (BEFORE LLM) ──
    # Strip PII from enriched JD fields before feeding to Big Five LLM.
    _safe_enriched_dict = dict(jd_enriched_dict) if jd_enriched_dict else {}
    try:
        from app.domains.job_creation.compliance import mask_pii_for_llm as _mask_pii
        for _field in ("about_role", "titulo_padronizado"):
            if _safe_enriched_dict.get(_field):
                _safe_enriched_dict[_field] = _mask_pii(_safe_enriched_dict[_field])
        if _safe_enriched_dict.get("responsabilidades"):
            _safe_enriched_dict["responsabilidades"] = [
                _mask_pii(r) if isinstance(r, str) else r
                for r in _safe_enriched_dict["responsabilidades"]
            ]
    except Exception as _bf_pii_exc:
        logger.warning("[JobCreation:bigfive] PII masking failed (fail-open): %s", _bf_pii_exc)

    enriched = EnrichedJobDescription(**_safe_enriched_dict) if _safe_enriched_dict else None

    generator = _get_wsi_generator()

    # Policy gate check
    from app.domains.job_creation.policy_gate import PolicyDecision, WizardIntent
    _policy_result = evaluate_wizard_policy(WizardIntent.SET_PROTECTED_CRITERIA, state)
    _policy_decisions = (state.get("policy_decisions") or []) + [{
        "stage": "bigfive",
        "policy_decision": str(_policy_result.decision),
        "rationale": _policy_result.rationale,
    }]
    if _policy_result.decision == PolicyDecision.DENY:
        logger.warning("[PolicyGate:bigfive] DENY — %s", _policy_result.rationale)
        emit_policy_block_audit(stage="bigfive", decision=_policy_result)
        _pd_dict = {"policy_decision": str(_policy_result.decision), "rationale": _policy_result.rationale}
        return {
            **state,
            "policy_decisions": _policy_decisions,
            "error": f"Big Five bloqueado: {_policy_result.rationale}",
            "pending_human_confirmation": False,
            "requires_approval": False,
            "ws_stage_payload": build_ws_stage_payload(
                stage="bigfive",
                completeness=0,
                requires_approval=False,
                data={
                    # Task #1099 — invariant: data.message obrigatório.
                    "message": (
                        "Não consigo gerar o perfil Big Five — política da "
                        f"empresa bloqueou: {_policy_result.rationale}"
                    ),
                    "policy_blocked": True,
                    "policy_decision": _pd_dict,
                },
            ),
        }
    _pending_hitl = (_policy_result.decision == PolicyDecision.HITL_REQUIRED)

    if enriched:
        # F2: Extract Big Five via LLM — Task #1062: timeout determinístico
        # com fallback (`BigFiveExtraction()` defaults 0.5 across traits).
        # Espelha o padrão de `LIA_JD_ENRICHMENT_TIMEOUT_S` (D4 da auditoria
        # #1058). `rank_traits` é determinístico — não precisa timeout.
        import concurrent.futures as _cf_bf
        from app.domains.job_creation.schemas import BigFiveExtraction as _BFE
        _BF_LLM_TIMEOUT_S = float(__import__("os").environ.get(
            "LIA_BIGFIVE_TIMEOUT_S", "45"
        ))
        # NOTE: não usar `with ThreadPoolExecutor(...)` — o `__exit__` chama
        # `shutdown(wait=True)` e bloqueia até o LLM lento terminar (anula o
        # timeout). `shutdown(wait=False)` deixa a thread morrer em paz.
        # Task #1065 — flag de fallback determinístico (timeout LLM →
        # `BigFiveExtraction()` neutro 0.5). Painel renderiza banner
        # discreto pedindo revisão antes do recrutador confiar nas pistas.
        bigfive_used_fallback = False
        # Task #1067 — root-cause label propagado pro painel.
        bigfive_fallback_reason: Optional[str] = None
        _ex_bf = _cf_bf.ThreadPoolExecutor(max_workers=1)
        try:
            try:
                _fut_bf = _ex_bf.submit(generator.extract_bigfive, enriched)
                bigfive_obj = _fut_bf.result(timeout=_BF_LLM_TIMEOUT_S)
            except _cf_bf.TimeoutError:
                logger.warning(
                    "[JobCreation:bigfive] LLM timeout after %.1fs — "
                    "deterministic fallback (Task #1062)", _BF_LLM_TIMEOUT_S,
                )
                bigfive_obj = _BFE()  # defaults to 0.5 across all traits
                bigfive_used_fallback = True
                bigfive_fallback_reason = "timeout"
                _emit_wizard_fallback_metric(
                    node="bigfive", state=state, reason="llm_timeout",
                    timeout_s=_BF_LLM_TIMEOUT_S,
                    elapsed_ms=(time.time() - t0) * 1000,
                )
            except Exception as _bf_exc:  # noqa: BLE001 — fail-open
                logger.warning(
                    "[JobCreation:bigfive] LLM call failed (%s) — fallback",
                    _bf_exc,
                )
                bigfive_obj = _BFE()
                bigfive_used_fallback = True
                bigfive_fallback_reason = classify_llm_exception_reason(_bf_exc)
                _emit_wizard_fallback_metric(
                    node="bigfive", state=state,
                    reason=f"llm_{bigfive_fallback_reason}",
                    timeout_s=_BF_LLM_TIMEOUT_S,
                    elapsed_ms=(time.time() - t0) * 1000,
                )
        finally:
            _ex_bf.shutdown(wait=False)
        bigfive_profile = bigfive_obj.model_dump()

        # F3: Rank traits (deterministic — no LLM, no timeout needed)
        seniority = state.get("seniority_resolved") or state.get("parsed_seniority") or "pleno"
        trait_rankings = generator.rank_traits(bigfive_obj, seniority)
    else:
        bigfive_profile = state.get("bigfive_profile")
        trait_rankings = state.get("trait_rankings", [])

    _pending_hitl = locals().get("_pending_hitl", False)
    _policy_decisions_local = locals().get("_policy_decisions", state.get("policy_decisions") or [])
    _policy_result_local = locals().get("_policy_result", None)
    _pd_data = {}
    if _policy_result_local is not None:
        _pd_data["policy_decision"] = {
            "policy_decision": str(_policy_result_local.decision),
            "rationale": _policy_result_local.rationale,
        }
    updates: Dict[str, Any] = {
        "current_stage": "bigfive",
        "bigfive_profile": bigfive_profile,
        "trait_rankings": trait_rankings,
        "stage_history": (state.get("stage_history") or []) + ["bigfive"],
        "completeness": calculate_completeness("bigfive"),
        "requires_approval": _pending_hitl,
        "pending_human_confirmation": _pending_hitl,
        "policy_decisions": _policy_decisions_local,
        "ws_stage_payload": build_ws_stage_payload(
            stage="bigfive",
            completeness=calculate_completeness("bigfive"),
            requires_approval=_pending_hitl,
            data={
                # Task #1099 — invariant: data.message obrigatório em todo
                # retorno com current_stage setado. Sem isso o
                # WizardSessionService cai em _emit_silent_fallback
                # (Task #1089). Mensagem parametrizada por título + flag de
                # fallback, espelhando o padrão do jd_enrichment_node (Task
                # #1096).
                "message": (
                    "Mapeei o perfil Big Five para "
                    f"{(state.get('parsed_title') or 'esta vaga')}"
                    + (
                        " (sugestão mínima — revise antes de seguir)."
                        if locals().get("bigfive_used_fallback", False)
                        else "."
                    )
                    + " Quer ajustar algum traço ou seguir para a faixa salarial?"
                ),
                "bigfive_profile": bigfive_profile,
                "trait_rankings": trait_rankings,
                # Task #1065 — flag de fallback determinístico para o
                # painel renderizar o banner "Sugestão mínima — revise".
                "bigfive_used_fallback": locals().get(
                    "bigfive_used_fallback", False
                ),
                # Task #1067 — root-cause label.
                "bigfive_fallback_reason": locals().get(
                    "bigfive_fallback_reason", None
                ),
                # Task #1070 — snapshot agregado de degradação (sessão/tenant).
                "ai_degraded_mode": _emit_fallback_telemetry(
                    state,
                    "bigfive",
                    locals().get("bigfive_fallback_reason", None),
                ),
                **_pd_data,
            },
        ),
    }

    # ── Task #1061: wizard_step_completed audit (EU AI Act Art.13) ──
    _emit_wizard_step_audit(
        stage="bigfive",
        state=state,
        before={
            "bigfive_profile": state.get("bigfive_profile"),
            "trait_rankings": state.get("trait_rankings"),
        },
        after={
            "bigfive_profile": bigfive_profile,
            "trait_rankings_count": len(trait_rankings or []),
        },
        reasoning_extra=[
            f"seniority={state.get('seniority_resolved') or state.get('parsed_seniority')}",
            f"pending_hitl={_pending_hitl}",
        ],
        criteria_used=["jd_enriched", "seniority", "trait_rankings"],
        human_review_required=_pending_hitl,
    )

    elapsed = (time.time() - t0) * 1000
    logger.info("[JobCreation:bigfive] %0.fms", elapsed)
    return {**state, **updates}

