"""publish_node canonical — PR-10 split (2026-05-26).

Movido de graph.py durante refactor estrutural ONDA 3 sub-sprint B+C.
Mantém comportamento byte-identical via tests de regressão.

Publish job via Rails API + save screening config + get share link.
"""

import logging
import time
from typing import Any, Dict

from app.domains.job_creation.state import (
    JobCreationState,
    calculate_completeness,
)
from app.domains.job_creation.helpers.ws_payload_builder import (
    build_ws_stage_payload,
)
from app.domains.job_creation.helpers.i18n import msg
from app.domains.job_creation.helpers.async_audit import emit_audit_fire_and_forget

logger = logging.getLogger(__name__)


def publish_node(state: JobCreationState) -> JobCreationState:
    """Publish job via Rails API + save screening config + get share link.

    Steps:
    1. Create job in Rails (if no job_id yet)
    2. Save WSI screening questions + eligibility
    3. Publish to selected platforms
    4. Get share link
    5. Auto-dispatch screening if enabled

    Governance: circuit breaker wraps all API calls.
    """
    # Lazy import of helpers defined in graph.py (avoids circular import).
    from app.domains.job_creation.graph import (  # noqa: E402
        _get_api_client,
        emit_policy_block_audit,
        evaluate_wizard_policy,
        lia_wizard_sourcing_mode_default_total,
    )

    t0 = time.time()
    logger.info("[JobCreation:publish] Starting publish")

    # Policy gate check — publish is side-effecting (irreversible), so HITL pauses
    # the wizard UNLESS the recruiter has explicitly confirmed via policy_confirmed_publish.
    from app.domains.job_creation.policy_gate import PolicyDecision, WizardIntent
    _pub_quality = state.get("jd_quality_score")
    _pub_policy = evaluate_wizard_policy(
        WizardIntent.PUBLISH_JOB, state,
        score=(_pub_quality / 100.0) if _pub_quality is not None else None,
    )
    _pub_pd_decisions = (state.get("policy_decisions") or []) + [{
        "stage": "publish",
        "policy_decision": str(_pub_policy.decision),
        "rationale": _pub_policy.rationale,
    }]
    _pub_confirmed = state.get("policy_confirmed_publish", False)
    _pub_pd_dict = {"policy_decision": str(_pub_policy.decision), "rationale": _pub_policy.rationale}

    if _pub_policy.decision == PolicyDecision.DENY:
        logger.warning("[PolicyGate:publish] DENY — %s", _pub_policy.rationale)
        emit_policy_block_audit(stage="publish", decision=_pub_policy)
        return {
            **state,
            "policy_decisions": _pub_pd_decisions,
            "error": _pub_policy.rationale,
            "pending_human_confirmation": False,
            "requires_approval": False,
            "ws_stage_payload": build_ws_stage_payload(
                stage="publish",
                completeness=0,
                requires_approval=False,
                data={
                    # Task #1099 — invariant: data.message obrigatório.
                    "message": msg("publish.policy_deny", rationale=_pub_policy.rationale),
                    "policy_blocked": True,
                    "policy_decision": _pub_pd_dict,
                },
            ),
        }

    if _pub_policy.decision == PolicyDecision.HITL_REQUIRED and not _pub_confirmed:
        logger.info("[PolicyGate:publish] HITL pause — awaiting recruiter confirmation")
        emit_policy_block_audit(stage="publish", decision=_pub_policy)
        return {
            **state,
            "policy_decisions": _pub_pd_decisions,
            "pending_human_confirmation": True,
            "requires_approval": True,
            "job_id": None,
            "ws_stage_payload": build_ws_stage_payload(
                stage="publish",
                completeness=0,
                requires_approval=True,
                data={
                    # Task #1099 — invariant: data.message obrigatório.
                    "message": msg("publish.policy_hitl", rationale=_pub_policy.rationale),
                    "policy_decision": _pub_pd_dict,
                    "policy_pending_confirmation": True,
                },
            ),
        }

    api = _get_api_client(state)
    job_id = state.get("job_id")
    job_uid = state.get("job_uid")
    share_link = state.get("share_link")
    error = None

    try:
        from app.shared.services.circuit_breaker import circuit_breaker_call, CircuitBreakerOpenError
        cb_wrap = lambda fn, *a, **kw: circuit_breaker_call(fn, *a, circuit_key="job_creation:publish", **kw)
    except ImportError:
        cb_wrap = lambda fn, *a, **kw: fn(*a, **kw)

    try:
        # Step 1: Create job if not yet created
        if not job_id:
            jd = state.get("jd_enriched", {})
            job_data = {
                "title": jd.get("titulo_padronizado", state.get("parsed_title", "")),
                "description": jd.get("about_role", ""),
                "seniority": state.get("seniority_resolved", ""),
                "department": state.get("parsed_department", ""),
                "location": state.get("parsed_location", ""),
                "work_model": state.get("parsed_model", ""),
                # P0-A: regime de contratação (coluna employment_type já existe).
                "employment_type": state.get("parsed_employment_type"),
                "salary_min": state.get("salary_min"),
                "salary_max": state.get("salary_max"),
                "salary_currency": state.get("salary_currency", "BRL"),
                # P0-B: coluna canônica salary_range JSON {min,max,currency}.
                "salary_range": (
                    {
                        "min": state.get("salary_min"),
                        "max": state.get("salary_max"),
                        "currency": state.get("salary_currency", "BRL"),
                    }
                    if state.get("salary_min") is not None
                    else None
                ),
                "benefits": state.get("benefits", []),
                "technical_requirements": jd.get("skills_obrigatorias", []),
                "behavioral_competencies": jd.get("competencias_comportamentais", []),
                "responsibilities": jd.get("responsabilidades", []),
            }
            resp = cb_wrap(api.create_job, job_data)
            if resp.success and resp.data:
                data = resp.data.get("data", resp.data)
                attrs = data.get("attributes", data)
                job_id = attrs.get("id") or data.get("id")
                job_uid = attrs.get("uid") or data.get("uid")
                logger.info("[JobCreation:publish] Job created: id=%s", job_id)

        if job_id:
            # Step 2: Save screening config (WSI questions + eligibility)
            questions = state.get("wsi_questions", [])
            eligibility = state.get("eligibility_questions", [])
            mode = state.get("screening_mode", "compact")
            if questions:
                cb_wrap(api.save_screening_config, job_id, questions, mode, eligibility)

            # Step 3: Publish to platforms
            platforms = state.get("publish_platforms", ["website"])
            # PR-8 ONDA 3 / F-3.5: warn + count quando UI nao setou sourcing_mode.
            _sourcing_raw = state.get("sourcing_mode")
            if _sourcing_raw is None:
                sourcing_mode = "local"
                if lia_wizard_sourcing_mode_default_total is not None:
                    try:
                        lia_wizard_sourcing_mode_default_total.labels(stage="publish").inc()
                    except Exception:  # pragma: no cover
                        pass
                logger.warning(
                    "[JobCreation:publish] sourcing_mode nao setado pelo recrutador -- "
                    "default=local. Considere exigir selector explicito em review stage."
                )
            else:
                sourcing_mode = _sourcing_raw
            cb_wrap(api.publish_job, job_id, platforms, sourcing_mode)

            # Step 4: Get share link
            link_resp = cb_wrap(api.get_share_link, job_id)
            if link_resp.success and link_resp.data:
                share_link = link_resp.data.get("share_link") or link_resp.data.get("public_url")

    except Exception as e:
        error = str(e)
        logger.error("[JobCreation:publish] Error: %s", e)

    updates: Dict[str, Any] = {
        "current_stage": "publish",
        "job_id": job_id,
        "job_uid": job_uid,
        "share_link": share_link,
        "error": error,
        "stage_history": (state.get("stage_history") or []) + ["publish"],
        "completeness": calculate_completeness("publish"),
        "requires_approval": False,
        "pending_human_confirmation": False,
        "policy_decisions": locals().get("_pub_pd_decisions", state.get("policy_decisions") or []),
        "ws_stage_payload": build_ws_stage_payload(
            stage="publish",
            completeness=calculate_completeness("publish"),
            requires_approval=False,
            data={
                # Task #1099 — invariant: data.message obrigatório.
                "message": (
                    msg("publish.error", error=error)
                    if error
                    else (
                        msg("publish.success_with_share_link", share_link=share_link)
                        if share_link
                        else msg("publish.success")
                    )
                ),
                "job_id": job_id,
                "platforms": state.get("publish_platforms", []),
                "sourcing_mode": state.get("sourcing_mode"),
                "contact_channels": state.get("contact_channels", []),
                "share_link": share_link,
                "auto_screen": state.get("auto_screen_enabled", True),
                "error": error,
            },
        ),
    }

    # ── Audit EU AI Act Art.13 — publish job decision ──
    try:
        import asyncio as _asyncio
        from app.shared.compliance.audit_service import AuditService
        _audit = AuditService()
        _company_id = str(state.get("workspace_id") or state.get("company_id") or "")
        if _company_id:
            emit_audit_fire_and_forget(
                lambda: _audit.log_decision(
                    company_id=_company_id,
                    agent_name="job_creation:publish",
                    decision_type="move_stage",
                    action="publish_job",
                    decision="published" if job_id and not error else "failed",
                    reasoning=[
                        f"platforms={state.get('publish_platforms', [])}",
                        f"sourcing_mode={state.get('sourcing_mode')}",
                        # T6 (Task #1088) — confirmation_method propagado pelo
                        # review_gate_node (chat | dual | button). Default "button"
                        # preserva o caminho legacy (UI button → policy_confirmed_publish
                        # direto, sem passar pelo gate LLM).
                        f"confirmation_method={state.get('publish_confirmation_method') or 'button'}",
                        *([f"error={error}"] if error else []),
                    ],
                    criteria_used=[
                        "job_data", "screening_config", "publish_platforms",
                        f"confirmation_method:{state.get('publish_confirmation_method') or 'button'}",
                    ],
                    job_vacancy_id=job_id,
                    human_review_required=False,
                )
            )
    except Exception as _audit_exc:
        logger.warning(
            "[JobCreation:publish] audit log failed (fail-open): %s", _audit_exc,
        )

    elapsed = (time.time() - t0) * 1000
    logger.info("[JobCreation:publish] job_id=%s share=%s | %0.fms", job_id, bool(share_link), elapsed)

    # Sprint B Phase 1 - JD Similar History: fire-and-forget record after publish
    if not error and job_id:
        try:
            from app.domains.job_creation.services.jd_similar_service import (
                record_jd_fire_and_forget,
            )
            company_id = str(state.get("workspace_id") or state.get("company_id") or "")
            jd_enriched_payload = state.get("jd_enriched") or {}
            title = (
                jd_enriched_payload.get("titulo_padronizado")
                or state.get("parsed_title")
                or ""
            )
            if company_id and title:
                record_jd_fire_and_forget(
                    company_id=company_id,
                    job_id=str(job_id),
                    title=title,
                    jd_enriched=jd_enriched_payload,
                    seniority_level=state.get("seniority_resolved"),
                    department=state.get("parsed_department"),
                )
        except Exception as exc:  # pragma: no cover - never block publish
            logger.warning(
                "[JobCreation:publish] JdSimilar wire failed (non-blocking): %s",
                str(exc)[:200],
            )

    return {**state, **updates}
