import logging
import os
from datetime import datetime
from typing import Any

from sqlalchemy import and_, case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from lia_models.external_api_consumption import ExternalApiConsumption

logger = logging.getLogger(__name__)

APIFY_USD_TO_BRL_RATE = float(os.environ.get("APIFY_USD_TO_BRL_RATE", "5.50"))
PEARCH_CREDIT_PRICE_BRL = float(os.environ.get("PEARCH_CREDIT_PRICE_BRL", "0.50"))


class ConsumptionReportService:

    @staticmethod
    async def get_report_by_period(
        db: AsyncSession,
        company_id: str,
        start: datetime,
        end: datetime,
    ) -> dict[str, Any]:
        base_conds = and_(
            ExternalApiConsumption.company_id == company_id,
            ExternalApiConsumption.created_at >= start,
            ExternalApiConsumption.created_at < end,
        )

        apify_query = select(
            func.count(ExternalApiConsumption.id).label("total_calls"),
            func.sum(ExternalApiConsumption.cost_usd).label("total_cost_usd"),
            func.sum(ExternalApiConsumption.cost_brl).label("total_cost_brl"),
            func.sum(
                case((ExternalApiConsumption.success == True, 1), else_=0)
            ).label("successful_calls"),
        ).where(
            and_(base_conds, ExternalApiConsumption.provider == "apify")
        )
        apify_result = await db.execute(apify_query)
        apify = apify_result.one()

        pearch_query = select(
            func.count(ExternalApiConsumption.id).label("total_calls"),
            func.sum(
                case((ExternalApiConsumption.success == True, 1), else_=0)
            ).label("successful_calls"),
        ).where(
            and_(base_conds, ExternalApiConsumption.provider == "pearch")
        )
        pearch_result = await db.execute(pearch_query)
        pearch = pearch_result.one()

        pearch_total_calls = int(pearch.total_calls or 0)

        pearch_credits_query = select(
            func.sum(ExternalApiConsumption.credits_consumed).label("total_credits"),
        ).where(
            and_(base_conds, ExternalApiConsumption.provider == "pearch")
        )
        pearch_credits_result = await db.execute(pearch_credits_query)
        pearch_estimated_credits = int(pearch_credits_result.scalar() or 0)

        breakdown_query = select(
            ExternalApiConsumption.provider,
            ExternalApiConsumption.operation,
            func.count(ExternalApiConsumption.id).label("count"),
            func.sum(ExternalApiConsumption.cost_usd).label("cost_usd"),
            func.sum(ExternalApiConsumption.cost_brl).label("cost_brl"),
        ).where(base_conds).group_by(
            ExternalApiConsumption.provider,
            ExternalApiConsumption.operation,
        )
        breakdown_result = await db.execute(breakdown_query)
        breakdown = [
            {
                "provider": row.provider,
                "operation": row.operation,
                "count": row.count,
                "cost_usd": round(float(row.cost_usd or 0), 4),
                "cost_brl": round(float(row.cost_brl or 0), 2),
            }
            for row in breakdown_result.all()
        ]

        return {
            "company_id": company_id,
            "period_start": start.isoformat(),
            "period_end": end.isoformat(),
            "pearch": {
                "total_calls": pearch_total_calls,
                "successful_calls": int(pearch.successful_calls or 0),
                "total_credits_consumed": pearch_estimated_credits,
                "estimated_cost_brl": round(pearch_estimated_credits * PEARCH_CREDIT_PRICE_BRL, 2),
            },
            "apify": {
                "total_calls": int(apify.total_calls or 0),
                "successful_calls": int(apify.successful_calls or 0),
                "total_cost_usd": round(float(apify.total_cost_usd or 0), 4),
                "total_cost_brl": round(float(apify.total_cost_brl or 0), 2),
            },
            "breakdown": breakdown,
        }

    @staticmethod
    async def get_invoice_data(
        db: AsyncSession,
        company_id: str,
        year: int,
        month: int,
    ) -> dict[str, Any]:
        if month == 12:
            start = datetime(year, month, 1)
            end = datetime(year + 1, 1, 1)
        else:
            start = datetime(year, month, 1)
            end = datetime(year, month + 1, 1)

        report = await ConsumptionReportService.get_report_by_period(
            db, company_id, start, end
        )

        pearch_cost_brl = report["pearch"]["estimated_cost_brl"]
        apify_cost_usd = report["apify"]["total_cost_usd"]
        apify_cost_brl = report["apify"]["total_cost_brl"]
        total_brl = round(pearch_cost_brl + apify_cost_brl, 2)

        return {
            "company_id": company_id,
            "period": f"{year}-{month:02d}",
            "period_start": start.isoformat(),
            "period_end": end.isoformat(),
            "pearch_credits": report["pearch"]["total_credits_consumed"],
            "pearch_cost_brl": pearch_cost_brl,
            "apify_calls": report["apify"]["total_calls"],
            "apify_cost_usd": apify_cost_usd,
            "apify_cost_brl": apify_cost_brl,
            "total_brl": total_brl,
            "exchange_rate": APIFY_USD_TO_BRL_RATE,
            "breakdown": report["breakdown"],
        }
