"""Canonical AuditService.log_decision wrapper for Agent Studio lifecycle events.

P0-3 audit 2026-05-21: prior code path emitted ZERO audit_logs for the entire
agent lifecycle (create / update / delete / execute / publish / install / 
review / approve / etc). Violates EU AI Act Art. 12 (6-month decision registry)
and LGPD Art. 20 (review of automated decisions).

This helper provides a single import for studio sites. Catches errors so audit
failures don't break the operation, but logs at WARNING level so monitoring can
detect drift. decision_type is fixed to 'agent_studio_lifecycle'; agent_name
is studio:{target_type}:{action} for queryability.
"""
import logging
from typing import Any

logger = logging.getLogger(__name__)


async def studio_audit(
    *,
    company_id: str,
    action: str,
    decision: str,
    reasoning: list[str],
    actor_user_id: str | None = None,
    target_id: str | None = None,
    target_type: str = "custom_agent",
    criteria_used: list[str] | None = None,
    score: float | None = None,
    confidence: float | None = None,
) -> None:
    """Best-effort canonical audit row for agent_studio lifecycle events.

    Args:
        company_id: tenant whose action is being audited (canonical, never trusted from payload).
        action: short verb, e.g. 'studio_agent_create', 'studio_agent_execute'.
        decision: outcome, e.g. 'created', 'updated', 'rejected', 'approved'.
        reasoning: bullet list of strings explaining WHY (LGPD Art. 20).
        actor_user_id: user who performed the action.
        target_id: ID of the agent / twin / listing affected.
        target_type: 'custom_agent' | 'sourcing_agent' | 'digital_twin' | 'marketplace_listing' | 'agent_approval'.
        criteria_used: optional list of criteria evaluated.
        score: optional score (used by execute path).
        confidence: optional confidence (used by execute path).
    """
    try:
        from app.shared.compliance.audit_service import AuditService
        svc = AuditService()
        await svc.log_decision(
            company_id=company_id,
            agent_name=f"studio:{target_type}:{action}",
            decision_type="agent_studio_lifecycle",
            action=action,
            decision=decision,
            reasoning=reasoning,
            criteria_used=criteria_used or [],
            candidate_id=target_id,  # overload field for target_id (audit_logs schema reuse)
            actor_user_id=actor_user_id,
            score=score,
            confidence=confidence,
            human_review_required=False,
        )
    except Exception as exc:
        logger.warning(
            "[studio_audit] Failed to log action=%s decision=%s for company=%s: %s",
            action, decision, company_id, exc,
        )
