import logging
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.domains.billing.services.consumption_report_service import ConsumptionReportService
from app.domains.billing.services.consumption_tracking_service import (
    APIFY_MONTHLY_BUDGET_USD,
    APIFY_USD_TO_BRL_RATE,
    CATEGORY_BUDGETS,
    ConsumptionTrackingService,
)
from app.shared.tenant_guard import get_verified_company_id
from app.shared.security.require_company_id import require_company_id

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/consumption", tags=["consumption"])


class ConsumptionReportResponse(BaseModel):
    company_id: str
    period_start: str
    period_end: str
    pearch: dict[str, Any]
    apify: dict[str, Any]
    breakdown: list[dict[str, Any]]


class InvoiceDataResponse(BaseModel):
    company_id: str
    period: str
    period_start: str
    period_end: str
    pearch_credits: int
    pearch_cost_brl: float
    apify_calls: int
    apify_cost_usd: float
    apify_cost_brl: float
    total_brl: float
    exchange_rate: float
    breakdown: list[dict[str, Any]]


class BudgetStatusResponse(BaseModel):
    company_id: str
    monthly_budget_usd: float
    current_spend_usd: float
    remaining_usd: float
    usage_percentage: float
    exchange_rate: float


class DashboardResponse(BaseModel):
    company_id: str
    period: str
    total_cost_usd: float
    total_cost_brl: float
    total_operations: int
    by_provider: dict[str, Any]
    by_operation: dict[str, Any]
    top_users: list[dict[str, Any]]
    daily_trend: list[dict[str, Any]]


class TenantSummaryResponse(BaseModel):
    period: str
    total_platform_cost_usd: float
    tenant_count: int
    tenants: list[dict[str, Any]]


class DetailedInvoiceResponse(BaseModel):
    company_id: str
    period: str
    period_start: str
    period_end: str
    line_items: list[dict[str, Any]]
    subtotals: dict[str, Any]
    total_usd: float
    total_brl: float
    exchange_rate: float
    line_count: int


class PricingAnalyticsResponse(BaseModel):
    period: str
    cost_per_candidate_found: float
    cost_per_candidate_with_contact: float
    search: dict[str, Any]
    enrichment: dict[str, Any]
    email_discovery: dict[str, Any]
    provider_success_rates: dict[str, Any]


@router.get("/report", response_model=ConsumptionReportResponse)
async def get_consumption_report(
    start_date: datetime = Query(..., description="Start date (ISO format)"),
    end_date: datetime = Query(..., description="End date (ISO format)"),
    company_id: str = Depends(get_verified_company_id),
    db: AsyncSession = Depends(get_db),
_company_gate: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    try:
        report = await ConsumptionReportService.get_report_by_period(
            db, company_id, start_date, end_date
        )
        return ConsumptionReportResponse(**report)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error generating consumption report: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to generate consumption report")


@router.get("/invoice-data", response_model=InvoiceDataResponse)
async def get_invoice_data(
    year: int = Query(..., ge=2024, le=2030, description="Invoice year"),
    month: int = Query(..., ge=1, le=12, description="Invoice month"),
    company_id: str = Depends(get_verified_company_id),
    db: AsyncSession = Depends(get_db),
_company_gate: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    try:
        data = await ConsumptionReportService.get_invoice_data(
            db, company_id, year, month
        )
        return InvoiceDataResponse(**data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error generating invoice data: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to generate invoice data")


@router.get("/budget-status", response_model=BudgetStatusResponse)
async def get_budget_status(
    company_id: str = Depends(get_verified_company_id),
    db: AsyncSession = Depends(get_db),
_company_gate: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    try:
        current_spend = await ConsumptionTrackingService.get_monthly_apify_spend(
            db, company_id
        )
        remaining = max(0.0, APIFY_MONTHLY_BUDGET_USD - current_spend)
        usage_pct = round((current_spend / APIFY_MONTHLY_BUDGET_USD) * 100, 1) if APIFY_MONTHLY_BUDGET_USD > 0 else 0.0
        return BudgetStatusResponse(
            company_id=company_id,
            monthly_budget_usd=APIFY_MONTHLY_BUDGET_USD,
            current_spend_usd=round(current_spend, 4),
            remaining_usd=round(remaining, 4),
            usage_percentage=usage_pct,
            exchange_rate=APIFY_USD_TO_BRL_RATE,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error getting budget status: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get budget status")


@router.get("/dashboard", response_model=DashboardResponse)
async def get_consumption_dashboard(
    company_id: str = Depends(get_verified_company_id),
    db: AsyncSession = Depends(get_db),
_company_gate: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    try:
        data = await ConsumptionReportService.get_dashboard(db, company_id)
        return DashboardResponse(**data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error generating dashboard: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to generate consumption dashboard")


@router.get("/tenant-summary", response_model=TenantSummaryResponse)
async def get_tenant_summary(
    company_id: str = Depends(get_verified_company_id),
    db: AsyncSession = Depends(get_db),
_company_gate: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    try:
        data = await ConsumptionReportService.get_tenant_summary(db, company_id=company_id)
        return TenantSummaryResponse(**data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error generating tenant summary: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to generate tenant summary")


@router.get(
    "/invoice/{target_company_id}/{year}/{month}",
    response_model=DetailedInvoiceResponse,
)
async def get_detailed_invoice(
    target_company_id: str = Path(..., description="Company ID"),
    year: int = Path(..., ge=2024, le=2030, description="Invoice year"),
    month: int = Path(..., ge=1, le=12, description="Invoice month"),
    company_id: str = Depends(get_verified_company_id),
    db: AsyncSession = Depends(get_db),
_company_gate: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    if target_company_id != company_id:
        raise HTTPException(status_code=403, detail="Access denied to this company's invoice")
    try:
        data = await ConsumptionReportService.get_detailed_invoice(
            db, target_company_id, year, month
        )
        return DetailedInvoiceResponse(**data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error generating detailed invoice: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to generate detailed invoice")


@router.get("/pricing-analytics", response_model=PricingAnalyticsResponse)
async def get_pricing_analytics(
    company_id: str = Depends(get_verified_company_id),
    db: AsyncSession = Depends(get_db),
_company_gate: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    try:
        data = await ConsumptionReportService.get_pricing_analytics(db, company_id)
        return PricingAnalyticsResponse(**data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error generating pricing analytics: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to generate pricing analytics")


class PearchConsumptionResponse(BaseModel):
    """Response schema for dedicated Pearch consumption endpoint."""
    company_id: str
    period_start: str
    period_end: str
    period_days: int
    total_searches: int
    successful_searches: int
    total_credits_consumed: int
    estimated_cost_brl: float


@router.get("/pearch", response_model=PearchConsumptionResponse)
async def get_pearch_consumption(
    days: int = Query(30, ge=1, le=365, description="Number of days to include"),
    company_id: str = Depends(get_verified_company_id),
    db: AsyncSession = Depends(get_db),
_company_gate: str = Depends(require_company_id)):
    # multi-tenancy: company_id from JWT via get_verified_company_id (REGRA 2 Pydantic canonical)
    """Get Pearch (external candidate search) consumption for the current period.

    Returns aggregated Pearch API call statistics from external_api_consumption table
    (provider='pearch'), NOT from ai_consumption/LLM token tracking.

    This is the canonical source for PearchTab.tsx — replaces client-side filter
    of /ai-credits?endpoint=by-agent&agent_type=search which reads the wrong table.
    """
    from datetime import timedelta as _timedelta
    end_date = datetime.utcnow()
    start_date = end_date - _timedelta(days=days)
    try:
        report = await ConsumptionReportService.get_report_by_period(
            db, company_id, start_date, end_date
        )
        pearch = report.get("pearch", {})
        return PearchConsumptionResponse(
            company_id=company_id,
            period_start=start_date.date().isoformat(),
            period_end=end_date.date().isoformat(),
            period_days=days,
            total_searches=pearch.get("total_calls", 0),
            successful_searches=pearch.get("successful_calls", 0),
            total_credits_consumed=pearch.get("total_credits_consumed", 0),
            estimated_cost_brl=pearch.get("estimated_cost_brl", 0.0),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error getting pearch consumption: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get Pearch consumption data")
