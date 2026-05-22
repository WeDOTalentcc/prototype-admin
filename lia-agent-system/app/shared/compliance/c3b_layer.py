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
})


@dataclass
class PreComplianceResult:
    clean_message: str
    original_message: str
    pii_stripped: bool = False
    fairness_blocked: bool = False
    injection_blocked: bool = False  # W1-005 (2026-05-22)
    block_reason: str = ""
    fairness_flags: list[str] = field(default_factory=list)
    injection_categories: list[str] = field(default_factory=list)


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

    # W1-005 (2026-05-22) · PromptInjectionGuard wiring
    # Pre-audit: tests/security/test_red_team_c3b_injection_wiring.py
    # Gap original: c3b nunca chamava injection guard. Plus regex DoS + adversarial bypass.
    injection_blocked = False
    injection_categories: list[str] = []
    try:
        from app.shared.compliance.prompt_injection_guard import PromptInjectionGuard
        guard = PromptInjectionGuard()
        ig_result = guard.check(clean)
        if ig_result.is_blocked:
            injection_blocked = True
            injection_categories = list(ig_result.matched_patterns)
            logger.warning(
                "[C3b] PromptInjection BLOCKED · company_id=%s domain=%s categories=%s risk=%s",
                company_id, domain, injection_categories, ig_result.risk_level,
            )
            return PreComplianceResult(
                clean_message=clean,
                original_message=message,
                pii_stripped=pii_stripped,
                injection_blocked=True,
                block_reason=f"Prompt injection detectado: categorias={injection_categories}, risco={ig_result.risk_level}",
                injection_categories=injection_categories,
            )
    except Exception as exc:
        logger.warning("[C3b] PromptInjectionGuard skipped — input NOT validated: %s", exc)

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
        injection_blocked=injection_blocked,
        block_reason=block_reason,
        fairness_flags=fairness_flags,
        injection_categories=injection_categories,
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
