"""pipeline_template_node canonical - PR-10 split (2026-05-26).

Movido de graph.py durante refactor estrutural ONDA 3 sub-sprint B.
Mantem comportamento byte-identical via tests de regressao.

HITL stage canonical - sugere pipeline template ou permite skip.
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
from app.domains.job_creation.internal.pipeline_template_helpers import _apply_pipeline_template_to_state
from app.domains.job_creation.internal.audit import _emit_pipeline_template_audit
from app.domains.job_creation.audit_actions import PipelineTemplateAuditAction
from app.domains.job_creation.helpers.async_audit import (
    emit_audit_fire_and_forget,
    run_coro_in_threadpool,
)

logger = logging.getLogger(__name__)


def pipeline_template_node(state: JobCreationState) -> JobCreationState:
    """HITL stage canonical — sugere pipeline template ou permite skip.

    Fluxo canonical (Gap #7 fix 2026-05-26):
    - Primeira passagem: emite ws_stage_payload com suggestions + requires_approval=True.
    - Re-entrada (recrutador respondeu): parse raw_input para detectar action canonical:
        * "Aplicar template de pipeline <uuid>" → apply: translate stages + persist em state
        * "Template de pipeline aplicado, pode seguir" → ack apenas (frontend já fez fetch)
        * "Usar pipeline padrão da empresa" → skip: state.pipeline_template_skipped=True

    Fail-open: DB suggestion miss → legacy heuristic fallback → allow_skip.
    NUNCA crasha o graph. Apply de stages persiste em state.interview_stages
    (publish_node lê depois pra criar vacancy com pipeline_template_id correto).
    """
    # Deferred imports to avoid circular dependency with graph.py module-level state.
    from app.domains.job_creation.graph import (
        _apply_pipeline_template_to_state,
        _emit_pipeline_template_audit,
        _suggest_pipeline_template,
        _build_pipeline_template_db_suggestion,
    )

    import re as _re

    t0 = time.time()

    # ── Gap #7 fix: parse user re-entry FIRST ──
    # Se recrutador já escolheu (template_id presente OU explicit skip), pula emit.
    raw_input = (state.get("raw_input") or state.get("user_query") or "").strip()
    already_chosen = bool(state.get("pipeline_template_id")) or bool(state.get("pipeline_template_skipped"))

    if raw_input and not already_chosen:
        # PR-11 F-4.11: patterns canonical em dispatch_messages.py (TS mirror
        # em plataforma-lia/src/components/unified-chat/wizard/dispatchMessages.ts).
        # Pattern 1: explicit apply with template_id UUID
        m_apply = _re.search(
            _wizard_dispatch.APPLY_TEMPLATE_PATTERN,
            raw_input,
            _re.IGNORECASE,
        )
        # Pattern 2: ack (frontend already applied via separate fetch)
        m_ack = _re.search(
            _wizard_dispatch.APPLIED_ACK_PATTERN, raw_input, _re.IGNORECASE,
        )
        # Pattern 3: skip / use company default
        m_skip = _re.search(
            _wizard_dispatch.USE_DEFAULT_PATTERN, raw_input, _re.IGNORECASE,
        )

        if m_apply:
            template_id_str = m_apply.group(1)
            logger.info("[JobCreation:pipeline_template] APPLY detected: template_id=%s", template_id_str)
            applied = _apply_pipeline_template_to_state(state, template_id_str)
            if applied:
                _emit_pipeline_template_audit(
                    state,
                    action=PipelineTemplateAuditAction.APPLIED_IN_WIZARD.value,
                    template_id=template_id_str,
                    extra={"source": "wizard_explicit", "raw_input_preview": raw_input[:80]},
                )
                return {
                    **state,
                    "current_stage": "pipeline_template",
                    "pipeline_template_id": template_id_str,
                    "interview_stages": applied.get("interview_stages", []),
                    "stage_history": (state.get("stage_history") or []) + ["pipeline_template"],
                    "completeness": calculate_completeness("pipeline_template"),
                    "requires_approval": False,
                }
            # Apply failed (template not found / cross-tenant) → fall through to re-emit

        elif m_ack:
            logger.info("[JobCreation:pipeline_template] ACK detected (frontend already applied)")
            _emit_pipeline_template_audit(
                state,
                action=PipelineTemplateAuditAction.APPLIED_ACK.value,
                template_id=state.get("pipeline_template_id"),
                extra={"raw_input_preview": raw_input[:80]},
            )
            return {
                **state,
                "current_stage": "pipeline_template",
                "stage_history": (state.get("stage_history") or []) + ["pipeline_template"],
                "completeness": calculate_completeness("pipeline_template"),
                "requires_approval": False,
            }

        elif m_skip:
            logger.info("[JobCreation:pipeline_template] SKIP detected (use company default)")
            _emit_pipeline_template_audit(
                state,
                action=PipelineTemplateAuditAction.SKIPPED.value,
                template_id=None,
                extra={"source": "wizard_explicit", "raw_input_preview": raw_input[:80]},
            )
            return {
                **state,
                "current_stage": "pipeline_template",
                "pipeline_template_skipped": True,
                "stage_history": (state.get("stage_history") or []) + ["pipeline_template"],
                "completeness": calculate_completeness("pipeline_template"),
                "requires_approval": False,
            }
        # else: free-text não matched → cai no emit (LIA re-pergunta)

    logger.info("[JobCreation:pipeline_template] Starting (stage idx 2)")

    parsed_title = state.get("parsed_title")
    parsed_seniority = state.get("parsed_seniority")

    # 1. Canonical DB suggestion (top-3 com scoring real)
    db_sugg: Optional[Dict[str, Any]] = None
    try:
        db_sugg = _build_pipeline_template_db_suggestion(state)
    except Exception as exc:  # noqa: BLE001 — fail-open por design
        logger.warning("[JobCreation:pipeline_template] DB suggestion failed (fail-open): %s", exc)

    # 2. Legacy heuristic fallback (sem DB)
    legacy: Optional[Dict[str, Any]] = None
    try:
        legacy = _suggest_pipeline_template(parsed_title, parsed_seniority)
    except Exception as exc:  # noqa: BLE001
        logger.warning("[JobCreation:pipeline_template] legacy heuristic failed (fail-open): %s", exc)

    # 3. Build canonical templates list (preferindo DB quando should_suggest=True)
    templates: List[Dict[str, Any]] = []
    suggested_template_id: Optional[str] = None
    top_score: float = 0.0
    if isinstance(db_sugg, dict) and db_sugg.get("should_suggest") and db_sugg.get("templates"):
        templates = list(db_sugg["templates"])
        top_score = float(db_sugg.get("top_score") or 0.0)
        if templates:
            suggested_template_id = templates[0].get("template_id")

    # 4. Default pipeline stage count (proxy para mensagem "padrão da empresa tem N etapas")
    default_pipeline_stages_count = len((state.get("interview_stages") or []) or [])

    # 5. Mensagem PT-BR canonical (UX conversacional)
    if templates:
        top_name = templates[0].get("name") or "este pipeline"
        message = msg("pipeline_template.suggest_template", top_name=top_name)
    elif legacy:
        message = msg("pipeline_template.no_custom_match")
    else:
        message = msg("pipeline_template.use_default")

    ws_stage_payload = build_ws_stage_payload(
        stage="pipeline_template",
        completeness=calculate_completeness("pipeline_template"),
        requires_approval=True,
        ui_action="suggest_pipeline_template",
        data={
            "message": message,
            "templates": templates,
            "suggested_template_id": suggested_template_id,
            "allow_skip": True,
            "default_pipeline_stages_count": default_pipeline_stages_count,
            # Retrocompat com pattern legacy (jd_enrichment_node emite o mesmo shape).
            "suggestions_data": {
                "pipeline_template": legacy,
                "pipeline_template_db": db_sugg,
            },
        },
    )

    stage_history = list(state.get("stage_history") or [])
    if "pipeline_template" not in stage_history:
        stage_history.append("pipeline_template")

    updates = {
        "current_stage": "pipeline_template",
        "stage_history": stage_history,
        "completeness": calculate_completeness("pipeline_template"),
        "requires_approval": True,
        "ws_stage_payload": ws_stage_payload,
    }

    # 6. Audit canonical (EU AI Act Art.13 / SOX 7y) — fail-open
    try:
        import asyncio as _asyncio
        from app.shared.compliance.audit_service import AuditService
        _audit = AuditService()
        _company_id = str(state.get("company_id") or state.get("workspace_id") or "")
        if _company_id:
            emit_audit_fire_and_forget(
                lambda: _audit.log_decision(
                    company_id=_company_id,
                    agent_name="job_creation:pipeline_template",
                    decision_type="company_settings_change",
                    action=PipelineTemplateAuditAction.SUGGESTED.value,
                    decision="suggested" if templates else "no_match",
                    reasoning=[
                        f"db_should_suggest={bool(db_sugg and db_sugg.get('should_suggest'))}",
                        f"db_top_score={top_score:.3f}",
                        f"templates_count={len(templates)}",
                        f"suggested_template_id={suggested_template_id or 'none'}",
                        f"legacy_fallback={'yes' if legacy else 'no'}",
                    ],
                    criteria_used=["parsed_department", "parsed_seniority", "parsed_job_family"],
                    job_vacancy_id=state.get("job_id"),
                    confidence=top_score if top_score else None,
                    human_review_required=True,  # HITL — recrutador escolhe
                )
            )
    except Exception as _audit_exc:
        logger.debug(
            "[JobCreation:pipeline_template] audit log failed (fail-open): %s", _audit_exc,
        )

    elapsed = (time.time() - t0) * 1000
    logger.info(
        "[JobCreation:pipeline_template] templates=%d top_score=%.2f | %.0fms",
        len(templates), top_score, elapsed,
    )
    return {**state, **updates}



