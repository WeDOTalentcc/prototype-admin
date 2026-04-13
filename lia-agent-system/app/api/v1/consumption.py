import logging
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.domains.billing.services.consumption_report_service import ConsumptionReportService
from app.domains.billing.services.consumption_tracking_service import (
    APIFY_MONTHLY_BUDGET_USD,
    APIFY_USD_TO_BRL_RATE,
    ConsumptionTrackingService,
)
from app.shared.tenant_guard import get_verified_company_id

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


@router.get("/report", response_model=ConsumptionReportResponse)
async def get_consumption_report(
    start_date: datetime = Query(..., description="Start date (ISO format)"),
    end_date: datetime = Query(..., description="End date (ISO format)"),
    company_id: str = Depends(get_verified_company_id),
    db: AsyncSession = Depends(get_db),
):
    try:
        report = await ConsumptionReportService.get_report_by_period(
            db, company_id, start_date, end_date
        )
        return ConsumptionReportResponse(**report)
    except Exception as e:
        logger.error("Error generating consumption report: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to generate consumption report")


@router.get("/invoice-data", response_model=InvoiceDataResponse)
async def get_invoice_data(
    year: int = Query(..., ge=2024, le=2030, description="Invoice year"),
    month: int = Query(..., ge=1, le=12, description="Invoice month"),
    company_id: str = Depends(get_verified_company_id),
    db: AsyncSession = Depends(get_db),
):
    try:
        data = await ConsumptionReportService.get_invoice_data(
            db, company_id, year, month
        )
        return InvoiceDataResponse(**data)
    except Exception as e:
        logger.error("Error generating invoice data: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to generate invoice data")


@router.get("/budget-status", response_model=BudgetStatusResponse)
async def get_budget_status(
    company_id: str = Depends(get_verified_company_id),
    db: AsyncSession = Depends(get_db),
):
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
    except Exception as e:
        logger.error("Error getting budget status: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get budget status")
