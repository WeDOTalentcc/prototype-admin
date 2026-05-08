"""
Shared FairnessGuard + AuditService helpers for candidate-scoring services.

Used by the cv_screening services (cv_scoring_service, lia_score_service,
pre_qualification_service, eligibility_verification_service,
evaluation_criteria_service) to guarantee the C1-C5 compliance gates required
by LGPD Art. 20 and the EU AI Act:

  1. FairnessGuard.check(...) is run on the candidate-facing input before
     any score / eligibility decision is produced.
  2. audit_service.log_decision(...) is emitted with criteria_used,
     score_breakdown and subject_id (candidate_id / job_vacancy_id) for
     every decision (including FairnessGuard blocks).
  3. When FairnessGuard blocks, callers get a controlled error (raised
     FairnessBlockedError or returned dict) and the block is audited.

The helpers are deliberately tolerant of synchronous callers: best-effort
audit logging never raises, and never blocks the scoring flow on its own
failures.
"""
from __future__ import annotations

import asyncio
import hashlib
import logging
from typing import Any

from app.shared.compliance.audit_service import audit_service
from app.shared.compliance.fairness_guard import (
    FairnessCheckResult,
    FairnessGuard,
)

logger = logging.getLogger(__name__)


_fairness_guard = FairnessGuard()


class FairnessBlockedError(Exception):
    """Raised by sync scoring services when FairnessGuard blocks input.

    Carries the FairnessCheckResult so callers (or the surrounding HTTP
    layer) can surface the educational message and category to the user.
    """

    def __init__(self, result: FairnessCheckResult, message: str | None = None):
        self.result = result
        super().__init__(
            message
            or result.educational_message
            or f"FairnessGuard blocked input (category={result.category})"
        )


def hash_payload(payload: str) -> str:
    return hashlib.sha256((payload or "").encode("utf-8")).hexdigest()


def run_fairness_check(payload: str | None) -> tuple[FairnessCheckResult | None, bool]:
    """Run FairnessGuard.check defensively.

    Returns (result, unavailable). When ``unavailable`` is True the guard
    raised — callers MUST fail closed (block the scoring decision).
    """
    if not payload or not str(payload).strip():
        return None, False
    try:
        return _fairness_guard.check(str(payload)), False
    except Exception as exc:  # pragma: no cover - defensive
        logger.error("FairnessGuard execution failed; failing closed: %s", exc)
        return None, True


async def log_scoring_decision(
    *,
    company_id: str | None,
    agent_name: str,
    decision_type: str,
    action: str,
    decision: str,
    reasoning: list[str],
    criteria_used: list[str],
    candidate_id: str | None = None,
    job_vacancy_id: str | None = None,
    score: float | None = None,
    score_breakdown: dict[str, Any] | None = None,
    human_review_required: bool = False,
) -> None:
    """Best-effort wrapper around audit_service.log_decision.

    Never raises. Embeds ``score_breakdown`` and ``subject_id`` in the
    reasoning trail (as required by the C1-C5 finding) so the AuditLog
    row carries the complete decision context.
    """
    try:
        full_reasoning: list[Any] = list(reasoning)
        if score_breakdown is not None:
            full_reasoning.append(f"score_breakdown={score_breakdown}")
        subject_id = candidate_id or job_vacancy_id
        if subject_id:
            full_reasoning.append(f"subject_id={subject_id}")
        # Regulator-facing evidence trail for fairness blocks (EU AI Act / LGPD).
        # Persists the regulatory_basis inside the audit row's reasoning JSON so
        # auditors can prove the block was anchored on the high-risk AI Act
        # category and the LGPD Art. 20 right to review of automated decisions.
        persisted_action = action
        if action == "fairness_block":
            persisted_action = "cv_screening.fairness_block"
            full_reasoning.append({
                "regulatory_basis": ["EU_AI_ACT_HIGH_RISK", "LGPD_ART_20"],
                "evidence_type": "fairness_block",
            })
        await audit_service.log_decision(
            company_id=str(company_id) if company_id else "unknown",
            agent_name=agent_name,
            decision_type=decision_type,
            action=persisted_action,
            decision=decision,
            reasoning=full_reasoning,
            criteria_used=criteria_used,
            candidate_id=candidate_id,
            job_vacancy_id=job_vacancy_id,
            score=score,
            human_review_required=human_review_required,
        )
    except Exception as exc:
        logger.warning(
            "scoring_safeguards: audit log_decision failed agent=%s action=%s err=%s",
            agent_name, action, exc,
        )


def schedule_audit_log(coro) -> None:
    """Fire-and-forget audit logging from sync code.

    If a running asyncio loop is detected, schedule the coroutine on it.
    Otherwise spin a temporary loop via asyncio.run. Never raises.
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop is not None and loop.is_running():
        try:
            loop.create_task(coro)
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("scoring_safeguards: failed to schedule audit task: %s", exc)
            try:
                coro.close()
            except Exception as close_exc:
                logger.warning(
                    "[scoring_safeguards] coro.close() after schedule failure failed (compliance): %s",
                    close_exc, exc_info=True,
                )
        return

    try:
        asyncio.run(coro)
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("scoring_safeguards: failed to run audit coroutine: %s", exc)
        try:
            coro.close()
        except Exception as close_exc:
            logger.warning(
                "[scoring_safeguards] coro.close() after asyncio.run failure failed (compliance): %s",
                close_exc, exc_info=True,
            )
