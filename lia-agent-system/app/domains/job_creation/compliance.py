"""
Compliance helpers for the Job Creation wizard graph.

These helpers wrap the enterprise gates (PII masking, FairnessGuard,
AuditService) so that each LLM-emitting node in `graph.py` can apply
them without duplicating boilerplate.

Three concerns:

1. ``mask_pii_for_llm`` — strips direct identifiers and quasi-identifiers
   from any free-text the recruiter sends to the wizard before the
   payload reaches the LLM (LGPD Art. 12 / EU AI Act Art. 13).

2. ``check_input_fairness`` / ``check_output_fairness`` — runs the
   FairnessGuard regex layer over recruiter input *and* over generated
   text (job description, requirements, screening questions). If a
   discriminatory pattern is detected the caller is responsible for
   blocking or flagging the result.

3. ``emit_job_creation_audit`` — writes a single ``decision_type =
   "job_creation"`` row at the end of a wizard run so AI Governance
   has a per-job audit trail (company_id, prompt_hash, model).

All helpers are sync-friendly so they can be called from the LangGraph
nodes (which are sync) without bubbling up coroutine warnings. Failures
in compliance helpers are logged but never block the wizard — the gates
fail open so recruiters never see opaque crashes.
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
import threading
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Layer 1 — PII masking
# ---------------------------------------------------------------------------

def mask_pii_for_llm(text: Optional[str]) -> str:
    """Mask PII / quasi-identifiers before sending text to an LLM.

    Wraps :func:`app.shared.pii_masking.strip_pii_for_llm_prompt` with a
    fail-open guard so the wizard never crashes if the masking module is
    unavailable (e.g. test environments without Presidio).
    """
    if not text:
        return text or ""
    try:
        from app.shared.pii_masking import strip_pii_for_llm_prompt
        return strip_pii_for_llm_prompt(text)
    except Exception as exc:  # pragma: no cover — defensive
        logger.warning("[JobCreation:Compliance] PII masking failed (fail-open): %s", exc)
        return text


# ---------------------------------------------------------------------------
# Layer 2 — FairnessGuard pre/post checks
# ---------------------------------------------------------------------------

@dataclass
class FairnessCheck:
    """Lightweight result returned by the wrapper around FairnessGuard."""

    is_blocked: bool = False
    category: Optional[str] = None
    blocked_terms: List[str] = field(default_factory=list)
    educational_message: Optional[str] = None


def _run_fairness_guard(text: str) -> FairnessCheck:
    if not text:
        return FairnessCheck()
    try:
        from app.shared.compliance.fairness_guard import FairnessGuard

        guard = FairnessGuard()
        result = guard.check(text)
        if result is None:
            return FairnessCheck()
        return FairnessCheck(
            is_blocked=bool(getattr(result, "is_blocked", False)),
            category=getattr(result, "category", None),
            blocked_terms=list(getattr(result, "blocked_terms", []) or []),
            educational_message=getattr(result, "educational_message", None),
        )
    except Exception as exc:  # pragma: no cover — defensive
        logger.warning("[JobCreation:Compliance] FairnessGuard check failed (fail-open): %s", exc)
        return FairnessCheck()


def check_input_fairness(text: Optional[str]) -> FairnessCheck:
    """FairnessGuard on what the recruiter provided to the wizard."""
    return _run_fairness_guard(text or "")


def check_output_fairness(text: Optional[str]) -> FairnessCheck:
    """FairnessGuard on text produced by the LLM (JD, questions, etc.)."""
    return _run_fairness_guard(text or "")


# ---------------------------------------------------------------------------
# Layer 3 — Audit emission
# ---------------------------------------------------------------------------

def _prompt_hash(payload: str) -> str:
    return hashlib.sha256((payload or "").encode("utf-8", errors="ignore")).hexdigest()[:16]


def _resolve_company_id(state: Dict[str, Any]) -> str:
    """Wizard state stores ``workspace_id`` (int) — coerce to the audit key."""
    raw = state.get("company_id") or state.get("workspace_id") or ""
    return str(raw) if raw else ""


def _resolve_model(state: Dict[str, Any]) -> str:
    """Best-effort lookup of the LLM model used during the wizard run."""
    try:
        from lia_config.config import settings
        return getattr(settings, "LLM_PRIMARY_MODEL", "unknown") or "unknown"
    except Exception:  # pragma: no cover — defensive
        return state.get("model") or "unknown"


def _run_async(coro, *, timeout: float = 5.0) -> None:
    """Run an async coroutine from a sync context, **deterministically**.

    The wizard's audit row must be persisted before ``handoff_node``
    returns, otherwise the "1 audit row per successful run" guarantee
    becomes flaky under short-lived workers. We always execute the
    coroutine in a fresh event loop on a worker thread and join with a
    bounded timeout so the caller blocks until persistence completes
    (success or failure). Failures are logged but never raised.
    """
    result: Dict[str, Any] = {"error": None}

    def _runner() -> None:
        try:
            asyncio.run(coro)
        except Exception as exc:
            result["error"] = exc

    thread = threading.Thread(target=_runner, daemon=True)
    thread.start()
    thread.join(timeout=timeout)
    if thread.is_alive():
        logger.warning(
            "[JobCreation:Compliance] audit emission did not complete within %.1fs",
            timeout,
        )
    elif result["error"] is not None:
        logger.warning(
            "[JobCreation:Compliance] audit emission failed: %s", result["error"]
        )


def emit_policy_block_audit(
    state: Dict[str, Any],
    *,
    stage: str,
    decision: Any,
) -> None:
    """Write a per-turn audit row for a blocked wizard turn (DENY or
    HITL pause on a side-effecting action). Required by the EU AI Act
    high-risk flow contract: every gate decision that prevents a
    sensitive operation must be traceable in the audit log even when
    the wizard never reaches the final ``handoff_node``.

    ``decision`` is a ``WizardPolicyResult`` (kept loose to avoid an
    import cycle).
    """
    company_id = _resolve_company_id(state)
    if not company_id:
        logger.debug(
            "[JobCreation:Audit] policy_block skipped — no company_id/workspace_id"
        )
        return

    decision_kind = getattr(getattr(decision, "decision", None), "value", "unknown")
    rationale = getattr(decision, "rationale", "") or ""
    intent = getattr(decision, "intent", "") or ""
    band = getattr(decision, "confidence_band", "n/a")

    reasoning: List[Any] = [
        f"stage={stage}",
        f"intent={intent}",
        f"policy_decision={decision_kind}",
        f"confidence_band={band}",
        f"rationale={rationale}",
    ]

    try:
        from app.shared.compliance.audit_service import AuditService

        service = AuditService()
        coro = service.log_decision(
            company_id=company_id,
            agent_name="job_creation_wizard",
            decision_type="job_creation_policy_block",
            action=intent or f"wizard.{stage}",
            decision=decision_kind,
            reasoning=reasoning,
            criteria_used=["policy_gate", "confidence_policy"],
            job_vacancy_id=str(state.get("job_id")) if state.get("job_id") else None,
            confidence=(
                float(state.get("jd_quality_score")) / 100.0
                if state.get("jd_quality_score") is not None
                else 0.0
            ),
            human_review_required=bool(
                getattr(decision, "requires_human_confirmation", False)
            ),
            criteria_ignored=None,
        )
        _run_async(coro)
        logger.info(
            "[JobCreation:Audit] policy_block stage=%s decision=%s rationale=%s",
            stage, decision_kind, rationale,
        )
    except Exception as exc:
        logger.warning(
            "[JobCreation:Audit] failed to emit policy_block audit row: %s", exc
        )


def emit_job_creation_audit(
    state: Dict[str, Any],
    *,
    success: bool = True,
    extra_reasoning: Optional[List[str]] = None,
    fairness_blocked: Optional[List[str]] = None,
) -> None:
    """Write a single ``job_creation`` audit row summarising the wizard run.

    Captures the company_id, the model used, a stable hash of the prompts
    (raw input + enriched JD), the screening mode + seniority chosen, and
    whether any FairnessGuard rule blocked the output. Failures are logged
    but never propagated — auditing must not break job creation.
    """
    company_id = _resolve_company_id(state)
    if not company_id:
        logger.debug("[JobCreation:Audit] skipped — no company_id/workspace_id in state")
        return

    model = _resolve_model(state)
    raw_input = state.get("raw_input") or state.get("user_query") or ""
    enriched = state.get("jd_enriched") or {}
    prompt_payload = "\n".join([
        raw_input,
        str(enriched.get("about_role", "")),
        str(state.get("seniority_resolved", "")),
        str(state.get("screening_mode", "")),
    ])
    prompt_hash = _prompt_hash(prompt_payload)

    reasoning: List[Any] = [
        f"prompt_hash={prompt_hash}",
        f"model={model}",
        f"seniority={state.get('seniority_resolved', '')}",
        f"screening_mode={state.get('screening_mode', '')}",
        f"questions_generated={len(state.get('wsi_questions') or [])}",
    ]
    if extra_reasoning:
        reasoning.extend(extra_reasoning)
    if fairness_blocked:
        reasoning.append({"fairness_blocked": fairness_blocked})

    # Per-turn wizard policy decisions (resolves N-09 + M-06): each entry
    # already carries policy_decision, confidence_band and rationale —
    # surface them in the audit row so AI Governance can replay the run.
    policy_decisions = state.get("policy_decisions") or []
    if policy_decisions:
        reasoning.append({"policy_decisions": list(policy_decisions)})

    job_id = state.get("job_id")
    job_vacancy_id = str(job_id) if job_id else None

    try:
        from app.shared.compliance.audit_service import AuditService

        service = AuditService()
        coro = service.log_decision(
            company_id=company_id,
            agent_name="job_creation_wizard",
            decision_type="job_creation",
            action="create_job",
            decision="completed" if success else "failed",
            reasoning=reasoning,
            criteria_used=[
                "jd_quality_score",
                "seniority",
                "screening_mode",
                "wsi_distribution",
            ],
            job_vacancy_id=job_vacancy_id,
            confidence=float(state.get("jd_quality_score") or 0.0) / 100.0,
            human_review_required=False,
            criteria_ignored=None,
        )
        _run_async(coro)
        logger.info(
            "[JobCreation:Audit] decision_type=job_creation company=%s job=%s prompt_hash=%s model=%s",
            company_id, job_vacancy_id, prompt_hash, model,
        )
    except Exception as exc:
        logger.warning("[JobCreation:Audit] failed to emit audit row: %s", exc)
