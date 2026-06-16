"""audit canonical — PR-17 step 4 extract (2026-05-26 ONDA 3 follow-up).

Audit emitters movidos de graph.py:
- _emit_wizard_step_audit (Task #1061 — EU AI Act Art.13 / SOX)
- _emit_pipeline_template_audit (REGRA #1 ACH-026 + LGPD trail)
- _emit_jd_gate_audit (gate LLM audit row)
- _emit_competency_gate_audit (competency gate audit)
- _emit_wsi_questions_gate_audit (WSI questions gate audit)
- _emit_review_gate_audit (review gate audit w/ confirmation_method)

Todos fail-open: audit failure NUNCA bloqueia o wizard.
"""

import logging
from typing import Any, Dict, Optional

from app.domains.job_creation.helpers.async_audit import emit_audit_fire_and_forget
from app.domains.job_creation.state import JobCreationState

logger = logging.getLogger(__name__)


def _emit_wizard_step_audit(
    *,
    stage: str,
    state: dict,
    before: Any,
    after: Any,
    reasoning_extra: Optional[list[str]] = None,
    criteria_used: Optional[list[str]] = None,
    human_review_required: bool = False,
) -> None:
    """Emit `wizard_step_completed` audit row for a JobCreationGraph node."""
    try:
        import json as _json
        import uuid as _uuid

        from app.shared.compliance.audit_service import AuditService

        company_id = str(
            state.get("workspace_id") or state.get("company_id") or ""
        )
        if not company_id:
            _ws = state.get("workspace_id")
            _cid = state.get("company_id")
            _keys = sorted(list(state.keys()))[:15]
            logger.warning(
                "[JobCreation:%s] audit skipped — missing company_id (ws=%r cid=%r keys=%s)",
                stage, _ws, _cid, _keys,
            )
            return

        target_id = str(
            state.get("job_id") or state.get("session_id") or ""
        ) or "∅"
        trace_id = str(_uuid.uuid4())

        def _ser(v: Any) -> str:
            try:
                s = _json.dumps(v, default=str, ensure_ascii=False, sort_keys=True)
            except Exception:
                s = str(v)
            return s if len(s) <= 1000 else f"{s[:1000]}…"

        reasoning: list[str] = [
            f"trace_id={trace_id}",
            f"stage={stage}",
            f"target_id={target_id}",
            f"before={_ser(before)}",
            f"after={_ser(after)}",
        ]
        if reasoning_extra:
            reasoning.extend(reasoning_extra)

        criteria = list(criteria_used or []) + [
            "wizard_step",
            f"stage:{stage}",
            f"trace_id:{trace_id}",
            f"target_id:{target_id}",
        ]

        emit_audit_fire_and_forget(
            lambda: AuditService().log_decision(
                company_id=company_id,
                agent_name=f"job_creation:{stage}",
                decision_type="wizard_step_completed",
                action=f"complete_{stage}",
                decision="completed",
                reasoning=reasoning,
                criteria_used=criteria,
                job_vacancy_id=state.get("job_id"),
                human_review_required=human_review_required,
            )
        )
    except Exception as _audit_exc:  # noqa: BLE001 — fail-open
        logger.warning(
            "[JobCreation:%s] wizard_step_completed audit failed (fail-open): %s",
            stage, _audit_exc,
        )


def _emit_pipeline_template_audit(
    state: dict,
    *,
    action: str,
    template_id: Optional[str],
    extra: Optional[Dict[str, Any]] = None,
) -> None:
    """Emit audit log canonical (REGRA #1 ACH-026 + LGPD trail).

    Fail-open: audit failure NUNCA bloqueia graph (igual ao bloco de audit
    do jd_enrichment_node).
    """
    try:
        from app.shared.compliance.audit_service import audit_service
        from app.models.audit_log import DecisionType

        company_id = str(state.get("workspace_id") or state.get("company_id") or "")
        if not company_id:
            return
        reasoning = [
            f"action: {action}",
            f"template_id: {template_id}",
            f"stage: pipeline_template",
        ]
        if extra:
            for k, v in extra.items():
                reasoning.append(f"{k}: {v}")
        emit_audit_fire_and_forget(
            lambda: audit_service.log_decision(
                company_id=company_id,
                agent_name="job_creation:pipeline_template",
                decision_type=DecisionType.COMPANY_SETTINGS_CHANGE.value,
                action=action,
                decision=f"{action}: {template_id or 'default'}",
                reasoning=reasoning,
                criteria_used=["template_id", "company_id", "stage"],
                actor_user_id=state.get("user_id") or state.get("created_by"),
                human_review_required=False,
            )
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "[pipeline_template] audit emission failed (fail-open): %s", exc,
        )


def _emit_jd_gate_audit(
    state: JobCreationState, user_message: str, output,
) -> None:
    """Emite audit row (decision_type=wizard_step_completed) para o gate LLM.

    Best-effort: falha NÃO bloqueia o resume. Inclui ``intent``,
    ``confidence``, ``thread_id`` e preview do reply para correlação no
    trail. Mantém EU AI Act Art. 13 (decisões automatizadas rastreáveis).
    """
    company_id = str(
        state.get("workspace_id") or state.get("company_id") or ""
    )
    if not company_id:
        return
    try:
        from app.shared.compliance.audit_service import audit_service
    except Exception:
        return

    # T2 fix #9 (code review #6 comment 3): EU AI Act Art. 13 — incluir
    # snapshot before/after compacto do state mutado pelo gate. Sem isso, o
    # audit row registra a decisão (intent/confidence) mas não a mutação,
    # quebrando rastreabilidade de "qual decisão automatizada alterou o
    # quê". Snapshot mínimo: jd_approved + gate_last_intent (campos
    # determinísticos da intent map) + jd_quality_score.
    _intent = str(output.intent)
    _before = {
        "jd_approved": state.get("jd_approved"),
        "gate_last_intent": state.get("gate_last_intent"),
        "jd_quality_score": state.get("jd_quality_score"),
        "jd_enriched_present": bool(state.get("jd_enriched")),
    }
    _after_jd_approved = _before["jd_approved"]
    if _intent == "approve":
        _after_jd_approved = True
    elif _intent in ("reject_with_feedback", "provide_new_content"):
        _after_jd_approved = False
    _after = {
        "jd_approved": _after_jd_approved,
        "gate_last_intent": _intent,
        "jd_quality_score": 0.0 if _intent == "provide_new_content" else _before["jd_quality_score"],
        "jd_enriched_present": False if _intent == "provide_new_content" else _before["jd_enriched_present"],
    }
    emit_audit_fire_and_forget(
        lambda: audit_service.log_decision(
            company_id=company_id,
            agent_name="wizard_jd_gate_classifier",
            decision_type="wizard_step_completed",
            action="jd_gate_classify",
            decision=_intent,
            reasoning=[
                f"intent={_intent}",
                f"confidence={float(output.confidence or 0.0):.2f}",
                f"thread_id={state.get('session_id') or ''}",
                f"user_msg_preview={user_message[:120]}",
                f"reply_preview={(output.conversational_reply or '')[:120]}",
                f"state_before={_before}",
                f"state_after={_after}",
            ],
            criteria_used=["llm_intent_classifier", "wizard_jd_enrichment"],
            confidence=float(output.confidence or 0.0),
        )
    )


def _emit_competency_gate_audit(
    state: JobCreationState, user_message: str, output,
) -> None:
    """Emite audit row (decision_type=wizard_step_completed) para o competency gate.

    Best-effort: falha NÃO bloqueia o resume. EU AI Act Art. 13.
    """
    company_id = str(state.get("workspace_id") or state.get("company_id") or "")
    if not company_id:
        return
    try:
        from app.shared.compliance.audit_service import audit_service
    except Exception:
        return

    _intent = str(output.intent)
    _before = {
        "screening_mode": state.get("screening_mode"),
        "gate_last_intent": state.get("gate_last_intent"),
        "seniority_resolved": state.get("seniority_resolved"),
    }
    _after_mode = _before["screening_mode"]
    if _intent == "select_compact":
        _after_mode = "compact"
    elif _intent == "select_full":
        _after_mode = "full"
    _after = {
        "screening_mode": _after_mode,
        "gate_last_intent": _intent,
        "seniority_resolved": _before["seniority_resolved"],
    }
    emit_audit_fire_and_forget(
        lambda: audit_service.log_decision(
            company_id=company_id,
            agent_name="wizard_competency_gate_classifier",
            decision_type="wizard_step_completed",
            action="competency_gate_classify",
            decision=_intent,
            reasoning=[
                f"intent={_intent}",
                f"confidence={float(output.confidence or 0.0):.2f}",
                f"thread_id={state.get('session_id') or ''}",
                f"user_msg_preview={user_message[:120]}",
                f"reply_preview={(output.conversational_reply or '')[:120]}",
                f"state_before={_before}",
                f"state_after={_after}",
            ],
            criteria_used=["llm_intent_classifier", "wizard_competency"],
            confidence=float(output.confidence or 0.0),
        )
    )


def _emit_wsi_questions_gate_audit(
    state: JobCreationState, user_message: str, output,
) -> None:
    """Emite audit row (decision_type=wizard_step_completed) para o
    wsi_questions gate. Best-effort: falha NÃO bloqueia o resume.
    EU AI Act Art. 13."""
    company_id = str(state.get("workspace_id") or state.get("company_id") or "")
    if not company_id:
        return
    try:
        from app.shared.compliance.audit_service import audit_service
    except Exception:
        return

    _intent = str(output.intent)
    _before = {
        "questions_approved": state.get("questions_approved"),
        "wsi_questions_count": len(state.get("wsi_questions") or []),
        "gate_last_intent": state.get("gate_last_intent"),
    }
    _after_approved = _before["questions_approved"]
    if _intent == "approve_all":
        _after_approved = True
    elif _intent in ("regenerate_all", "edit_specific_question", "add_question"):
        _after_approved = False
    _after = {
        "questions_approved": _after_approved,
        "gate_last_intent": _intent,
    }
    emit_audit_fire_and_forget(
        lambda: audit_service.log_decision(
            company_id=company_id,
            agent_name="wizard_wsi_questions_gate_classifier",
            decision_type="wizard_step_completed",
            action="wsi_questions_gate_classify",
            decision=_intent,
            reasoning=[
                f"intent={_intent}",
                f"confidence={float(output.confidence or 0.0):.2f}",
                f"thread_id={state.get('session_id') or ''}",
                f"user_msg_preview={user_message[:120]}",
                f"reply_preview={(output.conversational_reply or '')[:120]}",
                f"state_before={_before}",
                f"state_after={_after}",
                f"extracted_data_keys={sorted((output.extracted_data or {}).keys())}",
            ],
            criteria_used=["llm_intent_classifier", "wizard_wsi_questions"],
            confidence=float(output.confidence or 0.0),
        )
    )


def _emit_review_gate_audit(
    state: JobCreationState,
    user_message: str,
    output,
    *,
    confirmation_method: str = "chat",
) -> None:
    """Emite audit row (decision_type=wizard_step_completed) para o
    review gate. Best-effort: falha NÃO bloqueia o resume.

    SOX 7 anos retention: ``confirmation_method`` ∈ {chat, button, dual}
    é registrado em ``criteria_used`` para auditar o caminho exato pelo
    qual a decisão de publicação foi tomada (rastreabilidade EU AI Act
    Art. 13 + ISO 27001 control trail).
    """
    company_id = str(state.get("workspace_id") or state.get("company_id") or "")
    if not company_id:
        return
    try:
        from app.shared.compliance.audit_service import audit_service
    except Exception:
        return

    _intent = str(output.intent)
    _before = {
        "policy_confirmed_publish": bool(state.get("policy_confirmed_publish")),
        "pending_publish_confirmation": bool(state.get("pending_publish_confirmation")),
        "publish_platforms": list(state.get("publish_platforms") or []),
        "gate_last_intent": state.get("gate_last_intent"),
    }
    _after_confirmed = _before["policy_confirmed_publish"]
    _after_pending = _before["pending_publish_confirmation"]
    if _intent == "publish_now":
        if confirmation_method == "dual":
            _after_confirmed = True
            _after_pending = False
        else:
            _after_pending = True
    _after = {
        "policy_confirmed_publish": _after_confirmed,
        "pending_publish_confirmation": _after_pending,
        "gate_last_intent": _intent,
    }
    emit_audit_fire_and_forget(
        lambda: audit_service.log_decision(
            company_id=company_id,
            agent_name="wizard_review_gate_classifier",
            decision_type="wizard_step_completed",
            action="review_gate_classify",
            decision=_intent,
            reasoning=[
                f"intent={_intent}",
                f"confidence={float(output.confidence or 0.0):.2f}",
                f"thread_id={state.get('session_id') or ''}",
                f"user_msg_preview={user_message[:120]}",
                f"reply_preview={(output.conversational_reply or '')[:120]}",
                f"state_before={_before}",
                f"state_after={_after}",
                f"extracted_data_keys={sorted((output.extracted_data or {}).keys())}",
            ],
            criteria_used=[
                "llm_intent_classifier",
                "wizard_review",
                f"confirmation_method:{confirmation_method}",
            ],
            confidence=float(output.confidence or 0.0),
        )
    )
