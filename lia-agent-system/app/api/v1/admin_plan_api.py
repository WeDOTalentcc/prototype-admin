"""
Admin Plan API — Integration endpoints for the external admin panel.

Service-to-service auth via INTERNAL_API_TOKEN (Bearer header).
No JWT, no user context — these are machine-to-machine calls.

Endpoints:
  GET  /api/v1/admin-api/subscription/{company_id}       — plan + features + quotas
  GET  /api/v1/admin-api/usage/{company_id}               — current period consumption
  POST /api/v1/admin-api/usage/{company_id}/record         — record external metering
  PUT  /api/v1/admin-api/subscription/{company_id}/plan    — change company plan
"""
import logging
import os
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.shared.types import WeDoBaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin-api", tags=["admin-integration"])


# ---------------------------------------------------------------------------
# Auth dependency: INTERNAL_API_TOKEN
# ---------------------------------------------------------------------------

async def require_internal_token(request: Request) -> None:
    """Validate Bearer token matches INTERNAL_API_TOKEN env var."""
    token = os.environ.get("INTERNAL_API_TOKEN")
    if not token:
        logger.error("[AdminPlanAPI] INTERNAL_API_TOKEN not configured")
        raise HTTPException(status_code=503, detail="Service not configured")

    auth_header = request.headers.get("Authorization", "")
    provided = auth_header.removeprefix("Bearer ").strip()
    if not provided or provided != token:
        raise HTTPException(status_code=401, detail="Invalid internal token")


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class LLMUsageInfo(WeDoBaseModel):
    embedding_monthly_cap: int
    general_monthly_cap: int
    byok_active: bool = False
    byok_provider: str | None = None


class PearchInfo(WeDoBaseModel):
    monthly_included_credits: int
    credits_rollover: bool = False


class ApifyInfo(WeDoBaseModel):
    monthly_included_credits: int
    credits_rollover: bool = False


class AgentQuotasInfo(WeDoBaseModel):
    custom_agents: int
    sourcing_agents: int
    digital_twins: int
    campaigns: int


class SubscriptionResponse(WeDoBaseModel):
    plan_name: str
    plan_code: str
    status: str
    seats_contracted: int
    features_enabled: list[str]
    llm: LLMUsageInfo
    pearch: PearchInfo
    apify: ApifyInfo
    agent_quotas: AgentQuotasInfo
    overrides: dict[str, Any] = Field(default_factory=dict)


class UsageResponse(WeDoBaseModel):
    period: dict[str, str]
    embedding_tokens_used: int = 0
    llm_general_tokens_used: int = 0
    pearch_credits_used: int = 0
    apify_credits_used: int = 0
    agent_executions_used: int = 0
    actions_used: dict[str, int] = Field(default_factory=dict)


class RecordUsageRequest(WeDoBaseModel):
    meter_type: str = Field(..., pattern="^(embedding|llm_general|pearch|apify|action|agent_execution)$")
    amount: int = Field(..., gt=0)
    action_type: str | None = None


class ChangePlanRequest(WeDoBaseModel):
    plan_code: str


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _get_company_or_404(company_id: str, db: AsyncSession):
    """Verify company exists."""
    from app.models.client_account import ClientAccount
    result = await db.execute(
        select(ClientAccount).where(ClientAccount.id == company_id)
    )
    company = result.scalar_one_or_none()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return company


async def _get_subscription(company_id: str, db: AsyncSession):
    """Get active/trialing subscription for company."""
    from app.models.billing import Subscription
    result = await db.execute(
        select(Subscription).where(
            and_(
                Subscription.client_id == company_id,
                Subscription.status.in_(["active", "trialing"]),
            )
        ).order_by(Subscription.created_at.desc()).limit(1)
    )
    return result.scalar_one_or_none()


async def _get_plan_config(plan_code: str, db: AsyncSession):
    """Get plan config from company_plan_configs."""
    from lia_models.plan_config import CompanyPlanConfig
    result = await db.execute(
        select(CompanyPlanConfig).where(
            CompanyPlanConfig.plan_code == plan_code.lower().strip()
        ).limit(1)
    )
    return result.scalar_one_or_none()


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get(
    "/subscription/{company_id}",
    response_model=SubscriptionResponse,
    summary="Get company subscription details",
    description="Returns plan, features, quotas and overrides for a company.",
    dependencies=[Depends(require_internal_token)],
)
async def get_subscription(company_id: str, db: AsyncSession = Depends(get_db)):
    company = await _get_company_or_404(company_id, db)
    subscription = await _get_subscription(company_id, db)

    if not subscription:
        raise HTTPException(status_code=404, detail="No active subscription found")

    plan_code = (subscription.plan_code or "starter").lower().strip()
    plan_config = await _get_plan_config(plan_code, db)

    if plan_config:
        features = [k for k, v in (plan_config.feature_flags or {}).items() if v]
        response = SubscriptionResponse(
            plan_name=plan_config.plan_name or plan_code,
            plan_code=plan_code,
            status=subscription.status or "active",
            seats_contracted=plan_config.max_seats,
            features_enabled=features,
            llm=LLMUsageInfo(
                embedding_monthly_cap=plan_config.embedding_monthly_cap,
                general_monthly_cap=plan_config.llm_monthly_cap,
                byok_active=plan_config.byok_enabled,
            ),
            pearch=PearchInfo(
                monthly_included_credits=plan_config.pearch_credits_monthly,
                credits_rollover=plan_config.pearch_credits_rollover,
            ),
            apify=ApifyInfo(
                monthly_included_credits=plan_config.apify_credits_monthly,
                credits_rollover=plan_config.apify_credits_rollover,
            ),
            agent_quotas=AgentQuotasInfo(
                custom_agents=plan_config.max_custom_agents,
                sourcing_agents=plan_config.max_sourcing_agents,
                digital_twins=plan_config.max_digital_twins,
                campaigns=plan_config.max_campaigns,
            ),
        )
    else:
        response = SubscriptionResponse(
            plan_name=plan_code,
            plan_code=plan_code,
            status=subscription.status or "active",
            seats_contracted=5,
            features_enabled=[],
            llm=LLMUsageInfo(embedding_monthly_cap=50_000_000, general_monthly_cap=2_000_000),
            pearch=PearchInfo(monthly_included_credits=500),
            apify=ApifyInfo(monthly_included_credits=500),
            agent_quotas=AgentQuotasInfo(custom_agents=2, sourcing_agents=1, digital_twins=0, campaigns=0),
        )

    # Apply per-company overrides from ClientAccount.settings
    settings = company.settings if hasattr(company, "settings") and company.settings else {}
    if settings:
        overrides = {}
        if "agent_quotas" in settings:
            overrides["agent_quotas"] = settings["agent_quotas"]
            aq = settings["agent_quotas"]
            response.agent_quotas = AgentQuotasInfo(
                custom_agents=aq.get("custom_agents", response.agent_quotas.custom_agents),
                sourcing_agents=aq.get("sourcing_agents", response.agent_quotas.sourcing_agents),
                digital_twins=aq.get("digital_twins", response.agent_quotas.digital_twins),
                campaigns=aq.get("campaigns", response.agent_quotas.campaigns),
            )
        response.overrides = overrides

    return response


@router.get(
    "/usage/{company_id}",
    response_model=UsageResponse,
    summary="Get company usage for current period",
    description="Returns token/credit consumption for the current billing period.",
    dependencies=[Depends(require_internal_token)],
)
async def get_usage(
    company_id: str,
    month: str | None = Query(None, pattern=r"^\d{4}-\d{2}$"),
    db: AsyncSession = Depends(get_db),
):
    await _get_company_or_404(company_id, db)

    # Determine period
    if month:
        year, m = month.split("-")
        period_start = datetime(int(year), int(m), 1, tzinfo=UTC)
        if int(m) == 12:
            period_end = datetime(int(year) + 1, 1, 1, tzinfo=UTC)
        else:
            period_end = datetime(int(year), int(m) + 1, 1, tzinfo=UTC)
    else:
        now = datetime.now(UTC)
        period_start = datetime(now.year, now.month, 1, tzinfo=UTC)
        if now.month == 12:
            period_end = datetime(now.year + 1, 1, 1, tzinfo=UTC)
        else:
            period_end = datetime(now.year, now.month + 1, 1, tzinfo=UTC)

    # Aggregate token usage from ai_consumptions
    embedding_used = 0
    llm_used = 0
    try:
        from app.models.ai_consumption import AiConsumption
        result = await db.execute(
            select(
                func.coalesce(func.sum(AiConsumption.total_tokens), 0),
            ).where(
                and_(
                    AiConsumption.company_id == company_id,
                    AiConsumption.created_at >= period_start,
                    AiConsumption.created_at < period_end,
                )
            )
        )
        llm_used = result.scalar() or 0
    except Exception as exc:
        logger.debug("[AdminPlanAPI] Could not aggregate token usage: %s", exc)

    # Aggregate credit usage from credit_transactions
    pearch_used = 0
    apify_used = 0
    actions: dict[str, int] = {}
    try:
        from app.models.billing import CreditTransaction
        txns = await db.execute(
            select(CreditTransaction.transaction_type, CreditTransaction.reference_type, CreditTransaction.amount).where(
                and_(
                    CreditTransaction.company_id == company_id,
                    CreditTransaction.created_at >= period_start,
                    CreditTransaction.created_at < period_end,
                    CreditTransaction.transaction_type == "consumption",
                )
            )
        )
        for row in txns.all():
            ref_type = row.reference_type or ""
            amount = abs(row.amount or 0)
            if "pearch" in ref_type.lower():
                pearch_used += amount
            elif "apify" in ref_type.lower():
                apify_used += amount
            else:
                actions[ref_type] = actions.get(ref_type, 0) + amount
    except Exception as exc:
        logger.debug("[AdminPlanAPI] Could not aggregate credit usage: %s", exc)

    return UsageResponse(
        period={"start": period_start.isoformat(), "end": period_end.isoformat()},
        embedding_tokens_used=embedding_used,
        llm_general_tokens_used=llm_used,
        pearch_credits_used=pearch_used,
        apify_credits_used=apify_used,
        actions_used=actions,
    )


@router.post(
    "/usage/{company_id}/record",
    summary="Record external metering",
    description="Record consumption from external systems (admin panel).",
    dependencies=[Depends(require_internal_token)],
)
async def record_usage(
    company_id: str,
    body: RecordUsageRequest,
    db: AsyncSession = Depends(get_db),
):
    await _get_company_or_404(company_id, db)

    if body.meter_type == "action" and not body.action_type:
        raise HTTPException(400, detail="action_type required when meter_type=action")

    try:
        from app.domains.credits.services.credit_service import CreditService
        credit_svc = CreditService()
        await credit_svc.consume(
            db=db,
            company_id=company_id,
            amount=body.amount,
            description=f"External metering: {body.meter_type} ({body.amount})",
            action_type=body.action_type,
            reference_type=body.action_type or body.meter_type,
        )
        await db.commit()
    except Exception as exc:
        logger.error("[AdminPlanAPI] Failed to record usage: %s", exc)
        raise HTTPException(500, detail="Failed to record usage")

    return {"ok": True, "recorded": body.amount, "meter_type": body.meter_type}


@router.put(
    "/subscription/{company_id}/plan",
    summary="Change company plan",
    description="Updates subscription plan_code and invalidates caches.",
    dependencies=[Depends(require_internal_token)],
)
async def change_plan(
    company_id: str,
    body: ChangePlanRequest,
    db: AsyncSession = Depends(get_db),
):
    await _get_company_or_404(company_id, db)

    # Validate plan exists
    plan_config = await _get_plan_config(body.plan_code, db)
    if not plan_config:
        raise HTTPException(400, detail=f"Unknown plan_code: {body.plan_code}")

    # Update subscription
    subscription = await _get_subscription(company_id, db)
    if not subscription:
        raise HTTPException(404, detail="No active subscription found")

    old_plan = subscription.plan_code
    subscription.plan_code = body.plan_code.lower().strip()
    await db.commit()

    # Log plan change in credit transactions
    try:
        from app.models.billing import CreditTransaction
        log_entry = CreditTransaction(
            company_id=company_id,
            transaction_type="adjustment",
            reference_type="plan_change",
            amount=0,
            description=f"Plan changed: {old_plan} -> {body.plan_code}",
        )
        db.add(log_entry)
        await db.commit()
    except Exception as exc:
        logger.warning("[AdminPlanAPI] Could not log plan change: %s", exc)

    # Invalidate caches
    try:
        from app.domains.credits.services.token_budget_service import invalidate_plan_cache
        invalidate_plan_cache(company_id)
    except Exception:
        pass

    # Reconcile AgentQuota if exists
    try:
        from app.models.agent_quota import AgentQuota
        aq_result = await db.execute(
            select(AgentQuota).where(AgentQuota.company_id == company_id)
        )
        aq = aq_result.scalar_one_or_none()
        if aq:
            aq.plan_code = body.plan_code.lower().strip()
            await db.commit()
    except Exception as exc:
        logger.debug("[AdminPlanAPI] AgentQuota reconcile skipped: %s", exc)

    return {
        "ok": True,
        "company_id": company_id,
        "old_plan": old_plan,
        "new_plan": body.plan_code,
    }
