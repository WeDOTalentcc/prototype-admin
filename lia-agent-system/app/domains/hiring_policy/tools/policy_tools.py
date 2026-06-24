"""Hiring Policy Tools — LIA Sprint 3 T05
Policy enforcement: diversity targets, discriminatory language checks,
LGPD Art. 20 explanations, SOX-compliant audit trails, and compliance reports.
"""
import json
import logging
import uuid
from datetime import UTC, datetime

from langchain_core.tools import tool

logger = logging.getLogger(__name__)


@tool
def check_diversity_targets(job_id: str, current_pipeline: str) -> dict:
    """Checks whether the current hiring pipeline meets diversity and inclusion targets.

    Computes the disparate impact ratio (min_group_rate / max_group_rate) per
    IEEE 7003-2023. A ratio below 0.8 indicates potential adverse impact and
    triggers a recommendation to adjust sourcing or screening criteria.

    Args:
        job_id: Unique identifier of the job/requisition.
        current_pipeline: JSON string with stage counts broken down by demographic group
                          (e.g. '{"group_a": 10, "group_b": 5}').

    Returns:
        dict with job_id, targets_met, gaps, recommendations, and disparate_impact_ratio.
    """
    logger.info("check_diversity_targets: job_id=%s", job_id)
    try:
        pipeline_data = json.loads(current_pipeline) if current_pipeline else {}
    except (json.JSONDecodeError, TypeError):
        pipeline_data = {}

    group_rates = {}
    if pipeline_data:
        total = sum(pipeline_data.values()) or 1
        group_rates = {k: v / total for k, v in pipeline_data.items() if isinstance(v, (int, float))}

    disparate_impact_ratio = 1.0
    if len(group_rates) >= 2:
        rates = list(group_rates.values())
        max_rate = max(rates)
        min_rate = min(rates)
        disparate_impact_ratio = round(min_rate / max_rate, 4) if max_rate > 0 else 1.0

    targets_met = disparate_impact_ratio >= 0.8
    gaps = [] if targets_met else ["Disparate impact ratio below IEEE 7003 threshold of 0.8"]
    recommendations = (
        []
        if targets_met
        else [
            "Review sourcing channels to reach underrepresented groups",
            "Audit screening criteria for potential bias",
        ]
    )

    # P2-1 fix (2026-05-10): emit audit row para anti-discrimination tracking (LGPD Art.20 + EU AI Act Art.13)
    try:
        if not targets_met:
            from app.shared.compliance.audit_service import AuditService
            import asyncio
            service = AuditService()
            coro = service.log_decision(
                company_id="",  # contextvar resolve
                agent_name="hiring_policy_tools",
                decision_type="diversity_check",
                action="check_diversity_targets",
                decision="adverse_impact_detected",
                reasoning=[
                    f"job_id={job_id}",
                    f"disparate_impact_ratio={disparate_impact_ratio}",
                    f"groups={list(group_rates.keys())}",
                ],
                criteria_used=["IEEE_7003", "four_fifths_rule"],
                job_vacancy_id=str(job_id),
                confidence=disparate_impact_ratio,
                human_review_required=True,
                criteria_ignored=None,
            )
            # Fire-and-forget audit (non-blocking)
            try:
                loop = asyncio.get_event_loop()
                loop.create_task(coro)
            except Exception:
                pass
    except Exception as exc:
        logger.debug("[policy_tools] audit emission deferred: %s", exc)

    return {
        "job_id": job_id,
        "targets_met": targets_met,
        "gaps": gaps,
        "recommendations": recommendations,
        "disparate_impact_ratio": disparate_impact_ratio,
    }


@tool
def validate_job_requirements(job_id: str, requirements_text: str) -> dict:
    """Validates job requirements text for potentially discriminatory language.

    Scans the requirements for patterns that may violate LGPD, the EU AI Act
    Annex III, or local anti-discrimination laws. Returns a list of flagged issues
    and an overall severity rating.

    Args:
        job_id: Unique identifier of the job/requisition.
        requirements_text: The full text of job requirements or description to validate.

    Returns:
        dict with job_id, issues list, severity ('none'|'low'|'high'), and compliant flag.
    """
    logger.info("validate_job_requirements: job_id=%s", job_id)
    _DISCRIMINATORY_PATTERNS = [
        ("young", "Age-related language may discriminate against older candidates"),
        ("jovem", "Linguagem relacionada a idade pode discriminar candidatos mais velhos"),
        ("native speaker", "Native speaker requirement may constitute nationality discrimination"),
        ("fluente nativo", "Requisito de falante nativo pode constituir discriminação"),
        ("attractive", "Appearance-based requirements are discriminatory"),
        ("atraente", "Requisitos baseados em aparência são discriminatórios"),
        ("recent graduate", "Recency requirements may indirectly discriminate by age"),
    ]

    issues = []
    text_lower = requirements_text.lower()
    for pattern, message in _DISCRIMINATORY_PATTERNS:
        if pattern in text_lower:
            issues.append({"pattern": pattern, "message": message})

    # P2-1 fix (2026-05-10): FairnessGuard como SECONDARY check (1.122 LOC + 3 camadas)
    # complementar ao scan local de _DISCRIMINATORY_PATTERNS. FairnessGuard cobre
    # patterns mais completos (gênero, raça, idade, religião, orientação, etc.) +
    # léxico implícito + (Layer 3) LLM semantic.
    try:
        from app.shared.compliance.fairness_guard import FairnessGuard
        fg = FairnessGuard()
        fg_result = fg.check(requirements_text)
        if fg_result and getattr(fg_result, "is_blocked", False):
            for term in (getattr(fg_result, "blocked_terms", []) or []):
                issues.append({
                    "pattern": term,
                    "message": f"FairnessGuard: {getattr(fg_result, 'category', 'discriminatory')} — {getattr(fg_result, 'educational_message', 'discriminação detectada')}",
                    "source": "fairness_guard",
                })
    except Exception as exc:
        # Fail-open: FairnessGuard não pode bloquear validação local
        logger.warning("[policy_tools] FairnessGuard fallback: %s", exc)

    severity = "none"
    if len(issues) >= 3:
        severity = "high"
    elif len(issues) >= 1:
        severity = "low"

    return {
        "job_id": job_id,
        "issues": issues,
        "severity": severity,
        "compliant": len(issues) == 0,
    }


@tool
def generate_explanation_report(
    candidate_id: str, decision: str, decision_factors: str
) -> dict:
    """Generates a human-readable explanation report for an automated hiring decision.

    Fulfils the LGPD Art. 20 right-to-explanation requirement for automated decisions.
    The report details which factors influenced the decision in plain language.

    Args:
        candidate_id: Unique identifier of the candidate.
        decision: The automated decision made (e.g. 'advance', 'reject', 'hire').
        decision_factors: JSON string or comma-separated list of factors that drove the decision.

    Returns:
        dict with report_id, candidate_id, decision, explanation, factors, model_version, timestamp.
    """
    logger.info(
        "generate_explanation_report: candidate=%s decision=%s", candidate_id, decision
    )
    try:
        factors = json.loads(decision_factors)
        if not isinstance(factors, list):
            factors = [str(factors)]
    except (json.JSONDecodeError, TypeError):
        factors = [f.strip() for f in str(decision_factors).split(",") if f.strip()]

    explanation = (
        f"A decisão '{decision}' foi baseada nos seguintes fatores: "
        + ", ".join(factors[:5])
        + ". Esta análise foi realizada de forma automatizada pela LIA v1 em conformidade "
          "com o Art. 20 da LGPD (Lei 13.709/2018)."
    )

    return {
        "report_id": f"EXP-{str(uuid.uuid4())[:8].upper()}",
        "candidate_id": candidate_id,
        "decision": decision,
        "explanation": explanation,
        "factors": factors,
        "model_version": "lia-v1",
        "timestamp": datetime.now(UTC).isoformat(),
    }


@tool
def audit_hiring_decision(
    job_id: str, candidate_id: str, decision: str, reviewer_id: str
) -> dict:
    """Creates an immutable audit record for a hiring decision (SOX compliance).

    Generates a tamper-evident audit entry capturing the job, candidate, decision,
    and the human reviewer who approved or logged the action.

    Args:
        job_id: Unique identifier of the job/requisition.
        candidate_id: Unique identifier of the candidate.
        decision: The decision being audited (e.g. 'hire', 'reject', 'advance').
        reviewer_id: ID of the human reviewer responsible for this decision.

    Returns:
        dict with audit_id, job_id, candidate_id, decision, reviewer_id, timestamp, immutable.
    """
    logger.info(
        "audit_hiring_decision: job=%s candidate=%s decision=%s reviewer=%s",
        job_id, candidate_id, decision, reviewer_id,
    )
    return {
        "audit_id": f"AUD-{str(uuid.uuid4())[:8].upper()}",
        "job_id": job_id,
        "candidate_id": candidate_id,
        "decision": decision,
        "reviewer_id": reviewer_id,
        "timestamp": datetime.now(UTC).isoformat(),
        "immutable": True,
    }


@tool
def get_compliance_report(job_id: str) -> dict:
    """Generates a full compliance report for a hiring process.

    Evaluates the hiring process against LGPD, EU AI Act Annex III (high-risk AI),
    IEEE 7003 disparate impact standards, and internal audit trail completeness.

    Args:
        job_id: Unique identifier of the job/requisition.

    Returns:
        dict with job_id, lgpd_compliant, eu_ai_act_compliant, disparate_impact_ok,
        audit_trail_complete, and issues list.
    """
    # S02 defuse (census 2026-06-20): stub was returning lgpd_compliant=True unconditionally,
    # which would constitute a compliance-lie if this tool were ever registered with an LLM agent.
    # Until real compliance checks are implemented, this function MUST fail loudly
    # so that accidental registration produces an observable failure (not silent False-True).
    raise NotImplementedError(
        "get_compliance_report: compliance checks not implemented. "
        "This tool must NOT be registered in any tool registry until real audit trail "
        "and compliance service checks replace this stub. "
        "See app/domains/compliance/services/compliance_reporter.py for the real service."
    )
