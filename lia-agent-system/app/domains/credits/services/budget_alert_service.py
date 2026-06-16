"""
Token Budget Alert Service — dispatches notifications when budget thresholds are breached.

Graceful degradation: never raises, never blocks the budget check path.
Called from token_budget_service.increment_usage() after the 80% and 100%
thresholds are detected.

Sprint N TODO: lookup billing_email from Subscription and send HTML email.
"""
import logging
from typing import Optional

logger = logging.getLogger(__name__)


async def send_budget_alert(
    company_id: str,
    threshold_pct: int,
    used: int,
    limit: int,
    plan_code: Optional[str] = None,
) -> None:
    """
    Notify when token budget reaches threshold_pct (80 or 100).

    Current implementation: Sentry capture + structured log.
    Never raises — fire-and-forget contract.

    Args:
        company_id: Tenant identifier.
        threshold_pct: Threshold that triggered the alert (80 or 100).
        used: Tokens consumed so far today.
        limit: Daily token limit for the plan.
        plan_code: Plan code string (e.g. "starter", "pro").
    """
    level = "warning" if threshold_pct < 100 else "error"

    # Sentry (best-effort — never blocks)
    try:
        import sentry_sdk

        sentry_sdk.capture_message(
            f"Token budget {threshold_pct}% alert: company={company_id} used={used}/{limit}",
            level=level,
            tags={
                "company_id": str(company_id),
                "alert_type": f"token_budget_{threshold_pct}pct",
                "plan_code": str(plan_code or "unknown"),
            },
        )
    except Exception as exc:
        logger.debug("[BudgetAlert] Sentry unavailable: %s", exc)

    # Structured log (always emitted regardless of Sentry)
    log_fn = logger.error if threshold_pct >= 100 else logger.warning
    log_fn(
        "[TOKEN-BUDGET] %d%% threshold: company=%s used=%d limit=%d plan=%s",
        threshold_pct,
        company_id,
        used,
        limit,
        plan_code,
    )
