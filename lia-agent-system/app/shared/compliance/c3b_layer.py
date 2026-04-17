"""
C3b Compliance Layer — Strangler pattern for WS/SSE compliance.

Pre-compliance: PII stripping + FairnessGuard L3 for HR-sensitive domains.
Post-compliance: FactChecker + AuditService logging.

Feature flag: LIA_DISABLE_C3B=1 disables both functions (passthrough).
"""
import logging
import os
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

_C3B_DISABLED = os.environ.get("LIA_DISABLE_C3B", "0") == "1"

_FAIRNESS_DOMAINS = frozenset({
    "recruitment",
    "talent_ranking",
    "talent_pool",
    "job_scoring",
    "performance",
    "salary_benchmark",
    "job_management",
    "candidate_evaluation",
    # Audit A2 (task #316): hiring-policy authoring is a high-risk surface —
    # discriminatory policy text must be blocked at the API edge with HTTP 422.
    "hiring_policy",
    "policy",
    "policy_setup",
})


@dataclass
class PreComplianceResult:
    clean_message: str
    original_message: str
    pii_stripped: bool = False
    fairness_blocked: bool = False
    block_reason: str = ""
    fairness_flags: list[str] = field(default_factory=list)


@dataclass
class ComplianceContext:
    company_id: str
    user_id: str
    session_id: str
    domain: str
    agent_id: str
    original_message: str
    fairness_flags: list[str] = field(default_factory=list)


async def pre_compliance(
    message: str,
    company_id: str,
    domain: str,
) -> PreComplianceResult:
    if _C3B_DISABLED:
        return PreComplianceResult(
            clean_message=message,
            original_message=message,
        )

    clean = message
    pii_stripped = False

    try:
        from app.shared.pii_masking import strip_pii_for_llm_prompt
        stripped = strip_pii_for_llm_prompt(message)
        if stripped != message:
            clean = stripped
            pii_stripped = True
    except Exception:
        logger.debug("[C3b] PII strip skipped (silent)")

    fairness_blocked = False
    block_reason = ""
    fairness_flags: list[str] = []

    if domain in _FAIRNESS_DOMAINS:
        try:
            from app.shared.compliance.fairness_guard import FairnessGuard
            fg = FairnessGuard()
            result = fg.check(clean)
            if result.soft_warnings:
                fairness_flags = list(result.soft_warnings)
            if result.is_blocked:
                fairness_blocked = True
                block_reason = result.educational_message or "Solicitação bloqueada por critérios de equidade."
                fairness_flags.extend(result.blocked_terms or [])
        except Exception:
            logger.debug("[C3b] FairnessGuard L3 skipped (silent)")

    return PreComplianceResult(
        clean_message=clean,
        original_message=message,
        pii_stripped=pii_stripped,
        fairness_blocked=fairness_blocked,
        block_reason=block_reason,
        fairness_flags=fairness_flags,
    )


async def post_compliance(response: str, ctx: ComplianceContext) -> str:
    if _C3B_DISABLED:
        return response

    try:
        from app.shared.compliance.fact_checker import FactChecker
        fc = FactChecker()
        fc.check_response(response, {"domain": ctx.domain})
    except Exception:
        logger.debug("[C3b] FactChecker skipped (silent)")

    try:
        from app.shared.compliance.audit_service import audit_service
        await audit_service.log_decision(
            company_id=ctx.company_id,
            agent_name=ctx.agent_id or "c3b_layer",
            decision_type="generate_feedback",
            action=f"c3b_post_compliance:{ctx.domain}",
            decision="logged",
            reasoning=["C3b post-compliance audit log"],
            criteria_used=[ctx.domain],
        )
    except Exception:
        logger.debug("[C3b] AuditService log skipped (silent)")

    return response
