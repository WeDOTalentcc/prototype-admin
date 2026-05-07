import logging
import os
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import Date, and_, case, cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from lia_models.external_api_consumption import ExternalApiConsumption

logger = logging.getLogger(__name__)

APIFY_USD_TO_BRL_RATE = float(os.environ.get("APIFY_USD_TO_BRL_RATE", "5.50"))
PEARCH_CREDIT_PRICE_BRL = float(os.environ.get("PEARCH_CREDIT_PRICE_BRL", "0.50"))


# ADR-001-EXEMPT: External-API consumption analytics (cost/usage rollups for apify, pearch,
# scraping providers). Every select() in this service is a heavy reporting aggregation —
# func.sum(cost_usd|cost_brl|credits_consumed), func.count(id), case() success counters,
# cast(created_at, Date) for daily trend, multi-column GROUP BY (provider, operation,
# company_id, user_id, day), and ORDER BY computed sum() expressions. These do not map to
# generic per-tenant CRUD repo methods; pushing each into billing_repository would create
# 15 single-use thin wrappers around the same SQLAlchemy expressions and would hide the
# analytic intent without adding safety.
#
# Tenant scoping rationale (per query category):
#   - get_report_by_period / get_invoice_data / get_dashboard / get_detailed_invoice:
#     ALWAYS tenant-scoped; company_id passed as required arg from API layer
#     (app/api/v1/consumption.py: company_id = Depends(get_verified_company_id)).
#     The /invoice endpoint adds an extra target_company_id == company_id assertion
#     before calling get_detailed_invoice (line 194-195). Fail-closed at the route.
#   - get_tenant_summary / get_pricing_analytics: BY DESIGN cross-tenant capable
#     (company_id: str | None = None). When None, produces platform-wide rollups
#     (group by company_id, total_platform_cost_usd) used for admin/billing dashboards
#     and finance reconciliation. _require_company_id at the repo layer would block
#     this legitimate aggregation. Tenant scope is a passed parameter, not implicit.
#
# Multi-tenancy invariant is preserved at the API boundary (get_verified_company_id),
# never trusting payload-supplied company_id; this file is the analytic engine and
# trusts its caller to pass the verified value (or explicitly None for admin reports).


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

    @staticmethod
    async def get_dashboard(
        db: AsyncSession,
        company_id: str,
    ) -> dict[str, Any]:
        now = datetime.utcnow()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        base_conds = and_(
            ExternalApiConsumption.company_id == company_id,
            ExternalApiConsumption.created_at >= month_start,
        )

        total_query = select(
            func.sum(ExternalApiConsumption.cost_usd).label("total_usd"),
            func.sum(ExternalApiConsumption.cost_brl).label("total_brl"),
            func.count(ExternalApiConsumption.id).label("total_ops"),
        ).where(base_conds)
        total_result = await db.execute(total_query)
        total = total_result.one()

        provider_query = select(
            ExternalApiConsumption.provider,
            func.sum(ExternalApiConsumption.cost_usd).label("cost_usd"),
            func.count(ExternalApiConsumption.id).label("count"),
            func.sum(case((ExternalApiConsumption.success == True, 1), else_=0)).label("success_count"),
        ).where(base_conds).group_by(ExternalApiConsumption.provider)
        provider_result = await db.execute(provider_query)
        by_provider = {
            row.provider: {
                "cost_usd": round(float(row.cost_usd or 0), 4),
                "count": row.count,
                "success_count": row.success_count,
                "success_rate": round(row.success_count / row.count * 100, 1) if row.count > 0 else 0,
            }
            for row in provider_result.all()
        }

        op_query = select(
            ExternalApiConsumption.operation,
            func.sum(ExternalApiConsumption.cost_usd).label("cost_usd"),
            func.count(ExternalApiConsumption.id).label("count"),
        ).where(base_conds).group_by(ExternalApiConsumption.operation)
        op_result = await db.execute(op_query)
        by_operation = {
            row.operation: {
                "cost_usd": round(float(row.cost_usd or 0), 4),
                "count": row.count,
            }
            for row in op_result.all()
        }

        top_users_query = select(
            ExternalApiConsumption.user_id,
            func.sum(ExternalApiConsumption.cost_usd).label("cost_usd"),
            func.count(ExternalApiConsumption.id).label("count"),
        ).where(
            and_(base_conds, ExternalApiConsumption.user_id.isnot(None))
        ).group_by(
            ExternalApiConsumption.user_id
        ).order_by(
            func.sum(ExternalApiConsumption.cost_usd).desc()
        ).limit(10)
        top_users_result = await db.execute(top_users_query)
        top_users = [
            {
                "user_id": row.user_id,
                "cost_usd": round(float(row.cost_usd or 0), 4),
                "count": row.count,
            }
            for row in top_users_result.all()
        ]

        thirty_days_ago = now - timedelta(days=30)
        daily_query = select(
            cast(ExternalApiConsumption.created_at, Date).label("day"),
            func.sum(ExternalApiConsumption.cost_usd).label("cost_usd"),
            func.count(ExternalApiConsumption.id).label("count"),
        ).where(
            and_(
                ExternalApiConsumption.company_id == company_id,
                ExternalApiConsumption.created_at >= thirty_days_ago,
            )
        ).group_by("day").order_by("day")
        daily_result = await db.execute(daily_query)
        daily_trend = [
            {
                "date": str(row.day),
                "cost_usd": round(float(row.cost_usd or 0), 4),
                "count": row.count,
            }
            for row in daily_result.all()
        ]

        return {
            "company_id": company_id,
            "period": f"{now.year}-{now.month:02d}",
            "total_cost_usd": round(float(total.total_usd or 0), 4),
            "total_cost_brl": round(float(total.total_brl or 0), 2),
            "total_operations": int(total.total_ops or 0),
            "by_provider": by_provider,
            "by_operation": by_operation,
            "top_users": top_users,
            "daily_trend": daily_trend,
        }

    @staticmethod
    async def get_tenant_summary(
        db: AsyncSession,
        company_id: str | None = None,
    ) -> dict[str, Any]:
        now = datetime.utcnow()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        conditions = [ExternalApiConsumption.created_at >= month_start]
        if company_id:
            conditions.append(ExternalApiConsumption.company_id == company_id)

        tenant_query = select(
            ExternalApiConsumption.company_id,
            func.sum(ExternalApiConsumption.cost_usd).label("cost_usd"),
            func.sum(ExternalApiConsumption.cost_brl).label("cost_brl"),
            func.count(ExternalApiConsumption.id).label("count"),
            func.sum(case((ExternalApiConsumption.success == True, 1), else_=0)).label("success_count"),
        ).where(
            and_(*conditions),
        ).group_by(
            ExternalApiConsumption.company_id
        ).order_by(
            func.sum(ExternalApiConsumption.cost_usd).desc()
        )
        tenant_result = await db.execute(tenant_query)
        tenants = []
        total_platform_usd = 0.0
        for row in tenant_result.all():
            cost = float(row.cost_usd or 0)
            total_platform_usd += cost
            days_elapsed = max((now - month_start).days, 1)
            days_in_month = 30
            projected = round(cost / days_elapsed * days_in_month, 2)
            tenants.append({
                "company_id": row.company_id,
                "cost_usd": round(cost, 4),
                "cost_brl": round(float(row.cost_brl or 0), 2),
                "operations": row.count,
                "success_rate": round(row.success_count / row.count * 100, 1) if row.count > 0 else 0,
                "projected_monthly_usd": projected,
            })

        return {
            "period": f"{now.year}-{now.month:02d}",
            "total_platform_cost_usd": round(total_platform_usd, 4),
            "tenant_count": len(tenants),
            "tenants": tenants,
        }

    @staticmethod
    async def get_detailed_invoice(
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

        base_conds = and_(
            ExternalApiConsumption.company_id == company_id,
            ExternalApiConsumption.created_at >= start,
            ExternalApiConsumption.created_at < end,
        )

        lines_query = select(ExternalApiConsumption).where(base_conds).order_by(
            ExternalApiConsumption.created_at
        )
        lines_result = await db.execute(lines_query)
        records = lines_result.scalars().all()

        line_items = []
        subtotals: dict[str, dict] = {}
        total_usd = 0.0
        total_brl = 0.0

        for r in records:
            line_items.append(r.to_dict())
            cat_key = r.provider
            if cat_key not in subtotals:
                subtotals[cat_key] = {"count": 0, "cost_usd": 0.0, "cost_brl": 0.0}
            subtotals[cat_key]["count"] += 1
            subtotals[cat_key]["cost_usd"] += r.cost_usd
            subtotals[cat_key]["cost_brl"] += r.cost_brl
            total_usd += r.cost_usd
            total_brl += r.cost_brl

        for k in subtotals:
            subtotals[k]["cost_usd"] = round(subtotals[k]["cost_usd"], 4)
            subtotals[k]["cost_brl"] = round(subtotals[k]["cost_brl"], 2)

        from app.domains.billing.services.consumption_logger import ConsumptionAuditLogger
        ConsumptionAuditLogger.log_invoice_generated(
            company_id=company_id,
            year=year,
            month=month,
            total_usd=total_usd,
            total_brl=total_brl,
            line_count=len(line_items),
        )

        return {
            "company_id": company_id,
            "period": f"{year}-{month:02d}",
            "period_start": start.isoformat(),
            "period_end": end.isoformat(),
            "line_items": line_items,
            "subtotals": subtotals,
            "total_usd": round(total_usd, 4),
            "total_brl": round(total_brl, 2),
            "exchange_rate": APIFY_USD_TO_BRL_RATE,
            "line_count": len(line_items),
        }

    @staticmethod
    async def get_pricing_analytics(
        db: AsyncSession,
        company_id: str | None = None,
    ) -> dict[str, Any]:
        now = datetime.utcnow()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        conds = [ExternalApiConsumption.created_at >= month_start]
        if company_id:
            conds.append(ExternalApiConsumption.company_id == company_id)
        base = and_(*conds)

        search_ops = ["search", "apify_search"]
        search_conds = and_(base, ExternalApiConsumption.operation.in_(search_ops))

        search_query = select(
            func.sum(ExternalApiConsumption.cost_usd).label("total_cost"),
            func.count(ExternalApiConsumption.id).label("total_calls"),
            func.sum(case((ExternalApiConsumption.success == True, 1), else_=0)).label("success_count"),
        ).where(search_conds)
        search_result = await db.execute(search_query)
        search = search_result.one()
        search_cost = float(search.total_cost or 0)
        search_calls = int(search.total_calls or 0)
        search_success = int(search.success_count or 0)

        enrich_ops = ["enrich", "profile_scrape"]
        enrich_conds = and_(base, ExternalApiConsumption.operation.in_(enrich_ops))
        enrich_query = select(
            func.sum(ExternalApiConsumption.cost_usd).label("total_cost"),
            func.count(ExternalApiConsumption.id).label("total_calls"),
            func.sum(case((ExternalApiConsumption.success == True, 1), else_=0)).label("success_count"),
        ).where(enrich_conds)
        enrich_result = await db.execute(enrich_query)
        enrich = enrich_result.one()
        enrich_cost = float(enrich.total_cost or 0)
        enrich_calls = int(enrich.total_calls or 0)

        email_ops = ["reveal_email", "email_finder"]
        email_conds = and_(base, ExternalApiConsumption.operation.in_(email_ops))
        email_query = select(
            func.sum(ExternalApiConsumption.cost_usd).label("total_cost"),
            func.count(ExternalApiConsumption.id).label("total_calls"),
            func.sum(case((ExternalApiConsumption.success == True, 1), else_=0)).label("success_count"),
        ).where(email_conds)
        email_result = await db.execute(email_query)
        email = email_result.one()
        email_cost = float(email.total_cost or 0)
        email_calls = int(email.total_calls or 0)
        email_success = int(email.success_count or 0)

        total_pipeline_cost = search_cost + enrich_cost + email_cost
        total_candidates = enrich_calls
        candidates_with_email = int(email.success_count or 0)

        provider_success = {}
        ps_query = select(
            ExternalApiConsumption.provider,
            ExternalApiConsumption.operation,
            func.count(ExternalApiConsumption.id).label("total"),
            func.sum(case((ExternalApiConsumption.success == True, 1), else_=0)).label("successes"),
        ).where(base).group_by(
            ExternalApiConsumption.provider,
            ExternalApiConsumption.operation,
        )
        ps_result = await db.execute(ps_query)
        for row in ps_result.all():
            key = f"{row.provider}/{row.operation}"
            provider_success[key] = {
                "total": row.total,
                "successes": row.successes,
                "success_rate": round(row.successes / row.total * 100, 1) if row.total > 0 else 0,
            }

        return {
            "period": f"{now.year}-{now.month:02d}",
            "cost_per_candidate_found": round(total_pipeline_cost / total_candidates, 4) if total_candidates > 0 else 0,
            "cost_per_candidate_with_contact": round(total_pipeline_cost / candidates_with_email, 4) if candidates_with_email > 0 else 0,
            "search": {
                "total_cost": round(search_cost, 4),
                "total_calls": search_calls,
                "success_rate": round(search_success / search_calls * 100, 1) if search_calls > 0 else 0,
            },
            "enrichment": {
                "total_cost": round(enrich_cost, 4),
                "total_calls": enrich_calls,
            },
            "email_discovery": {
                "total_cost": round(email_cost, 4),
                "total_calls": email_calls,
                "success_rate": round(email_success / email_calls * 100, 1) if email_calls > 0 else 0,
            },
            "provider_success_rates": provider_success,
        }
