"""
Workforce Planning / Demand Forecasting — Predict hiring needs based on
turnover data, pipeline velocity, growth targets, and seasonality.

ADR-001 T9 (2026-06-09): raw SQL queries extracted to WorkforceRepository
(app/domains/workforce/repositories/workforce_repository.py). The 3 analytical
methods — get_open_jobs_summary, get_historical_hire_metrics,
get_internal_employee_count — are the canonical place for those queries.
ADR-001-EXEMPT markers removed; tool now delegates to the repository.
"""
import logging
from datetime import datetime, timedelta
from typing import Any

from app.shared.tool_handler import tool_handler

logger = logging.getLogger(__name__)


@tool_handler("talent_intelligence", module="workforce_planning")
async def forecast_hiring_needs(
    period: str = "quarter",
    department: str | None = None,
    growth_rate: float | None = None,
    include_backfills: bool = True,
    **kwargs,
) -> dict[str, Any]:
    """
    Forecast hiring needs based on historical data, turnover, and growth targets.

    Args:
        period: Forecast horizon — "month", "quarter", "half_year", "year"
        department: Filter by department
        growth_rate: Expected headcount growth rate (e.g. 0.10 for 10%)
        include_backfills: Include estimated backfills from turnover
    """
    from app.core.database import AsyncSessionLocal
    from app.domains.workforce.repositories.workforce_repository import WorkforceRepository

    company_id = kwargs.get("company_id", "")

    period_months = {"month": 1, "quarter": 3, "half_year": 6, "year": 12}.get(period, 3)
    forecast_end = datetime.utcnow() + timedelta(days=period_months * 30)  # noqa: F841

    try:
        async with AsyncSessionLocal() as session:
            repo = WorkforceRepository(session)

            job_data = await repo.get_open_jobs_summary(
                company_id=company_id,
                department=department,
            )
            hist_data = await repo.get_historical_hire_metrics(
                company_id=company_id,
                lookback_days=180,
                department=department,
            )
            total_employees = await repo.get_internal_employee_count(
                company_id=company_id,
                department=department,
            )

            total_hires_6m = hist_data["total_hires"]
            avg_ttf = hist_data["avg_time_to_fill"]
            open_positions = job_data["open_positions"]
            active_positions = job_data["active_count"]
            pipeline_positions = job_data["pipeline_count"]

    except Exception as e:
        logger.error(f"Error fetching workforce data: {e}", exc_info=True)
        total_employees = 0
        total_hires_6m = 0
        avg_ttf = 45
        open_positions = 0
        active_positions = 0
        pipeline_positions = 0

    monthly_hire_rate = total_hires_6m / 6.0 if total_hires_6m else 0
    estimated_turnover_rate = 0.15
    if total_employees > 0 and total_hires_6m > 0:
        annualized_hires = total_hires_6m * 2
        estimated_turnover_rate = min(annualized_hires / total_employees, 0.40)

    backfill_estimate = 0
    if include_backfills and total_employees > 0:
        monthly_turnover = total_employees * (estimated_turnover_rate / 12)
        backfill_estimate = round(monthly_turnover * period_months)

    growth_hires = 0
    effective_growth = growth_rate if growth_rate is not None else 0.05
    if total_employees > 0:
        growth_hires = round(total_employees * effective_growth * (period_months / 12))

    total_forecast = open_positions + backfill_estimate + growth_hires

    capacity_per_month = max(monthly_hire_rate, 1)
    months_needed = total_forecast / capacity_per_month if capacity_per_month > 0 else period_months

    if total_forecast <= capacity_per_month * period_months:
        feasibility = "achievable"
    elif total_forecast <= capacity_per_month * period_months * 1.3:
        feasibility = "challenging"
    else:
        feasibility = "at_risk"

    recommendations = []
    if backfill_estimate > growth_hires:
        recommendations.append(
            "Taxa de turnover acima da média — investir em retenção pode reduzir necessidade de contratação."
        )
    if avg_ttf > 45:
        recommendations.append(
            f"Tempo médio de preenchimento ({avg_ttf:.0f} dias) está acima do benchmark (45 dias). "
            "Considere otimizar processo seletivo."
        )
    if feasibility == "at_risk":
        recommendations.append(
            "Capacidade de contratação insuficiente para a demanda projetada. "
            "Considere aumentar equipe de recrutamento ou usar sourcing externo."
        )
    if open_positions > 10:
        recommendations.append(
            f"Há {open_positions} vagas abertas. Priorizar por impacto de negócio."
        )

    return {
        "success": True,
        "data": {
            "forecast_period": period,
            "forecast_months": period_months,
            "department_filter": department,
            "current_state": {
                "total_employees": total_employees,
                "open_positions": open_positions,
                "active_positions": active_positions,
                "pipeline_positions": pipeline_positions,
            },
            "historical_metrics": {
                "hires_last_6_months": total_hires_6m,
                "monthly_hire_rate": round(monthly_hire_rate, 1),
                "avg_time_to_fill_days": round(avg_ttf, 1),
                "estimated_annual_turnover_rate": round(estimated_turnover_rate * 100, 1),
            },
            "forecast": {
                "backfill_needs": backfill_estimate,
                "growth_hires": growth_hires,
                "currently_open": open_positions,
                "total_hiring_need": total_forecast,
                "monthly_hiring_target": round(total_forecast / period_months, 1),
            },
            "capacity_analysis": {
                "current_monthly_capacity": round(capacity_per_month, 1),
                "months_to_fill_all": round(months_needed, 1),
                "feasibility": feasibility,
            },
            "recommendations": recommendations,
        },
        "message": (
            f"Previsão de contratação ({period}): {total_forecast} posições no total "
            f"({open_positions} abertas + {backfill_estimate} backfills + {growth_hires} crescimento). "
            f"Viabilidade: {feasibility}."
        ),
    }
