"""
Real-Time Market Intelligence — Salary benchmarks and market trends from
external data sources (web search APIs, LLM estimation) instead of hardcoded
dictionaries.

Wraps the existing MarketBenchmarkService into an agent-callable tool,
providing real-time market data including salary ranges, demand trends,
in-demand skills, and competitive positioning.
"""
import logging
from typing import Any

from app.shared.tool_handler import tool_handler

logger = logging.getLogger(__name__)


@tool_handler("talent_intelligence", require_company=False, module="talent_intelligence_pro")  # kept: external/market data aggregator, no tenant scope
async def get_market_intelligence(
    job_title: str = "",
    seniority: str | None = None,
    location: str | None = None,
    industry: str | None = None,
    include_trends: bool = True,
    **kwargs,
) -> dict[str, Any]:
    """
    Get real-time market intelligence for a role: salary benchmarks from
    external sources, demand trends, in-demand skills, and competitive analysis.

    Uses MarketBenchmarkService (web search + LLM parsing) to fetch salary data
    from Glassdoor, LinkedIn, Indeed, and other public sources rather than
    relying on hardcoded salary dictionaries.

    Args:
        job_title: Job title to research (e.g., "Desenvolvedor Python Senior")
        seniority: Seniority level (Junior, Pleno, Senior, etc.)
        location: Location for regional adjustment (e.g., "São Paulo")
        industry: Industry sector (e.g., "Tecnologia", "Financeiro")
        include_trends: Whether to also fetch market trends
    """
    if not job_title:
        return {
            "success": False,
            "data": {},
            "message": "Parâmetro 'job_title' é obrigatório.",
        }

    from app.domains.analytics.services.market_benchmark_service import MarketBenchmarkService

    service = MarketBenchmarkService()

    salary_data = await service.search_salary_benchmark(
        role=job_title,
        seniority=seniority,
        location=location,
    )

    trends_data = {}
    if include_trends:
        trends_data = await service.search_market_trends(
            role=job_title,
            industry=industry,
        )

    competitive_position = "at_market"
    if salary_data.get("confidence") == "high":
        competitive_position = "data_backed"
    elif salary_data.get("is_estimate"):
        competitive_position = "estimated"

    result = {
        "job_title": job_title,
        "seniority": seniority,
        "location": location or "Brasil",
        "industry": industry,
        "salary_benchmark": {
            "min": salary_data.get("min"),
            "max": salary_data.get("max"),
            "median": salary_data.get("median"),
            "currency": salary_data.get("currency", "BRL"),
            "confidence": salary_data.get("confidence", "low"),
            "sources": salary_data.get("sources", []),
            "search_date": salary_data.get("search_date"),
            "is_estimate": salary_data.get("is_estimate", False),
            "trend": salary_data.get("trend", "estável"),
        },
        "market_trends": {},
        "competitive_position": competitive_position,
        "disclaimer": salary_data.get("disclaimer", "Estimativa baseada em dados públicos."),
    }

    if trends_data:
        result["market_trends"] = {
            "demand": trends_data.get("demand", "média"),
            "trend": trends_data.get("trend", "estável"),
            "skills_in_demand": trends_data.get("skills_in_demand", []),
            "salary_trend": trends_data.get("salary_trend", "stable"),
            "market_outlook": trends_data.get("market_outlook", "neutro"),
            "hiring_volume": trends_data.get("hiring_volume", "moderado"),
            "competition": trends_data.get("competition", "média"),
            "confidence": trends_data.get("confidence", "medium"),
        }

    sal = result["salary_benchmark"]
    trend_info = ""
    if result["market_trends"]:
        trend_info = f" Demanda: {result['market_trends']['demand']}. Tendência: {result['market_trends']['trend']}."

    return {
        "success": True,
        "data": result,
        "message": (
            f"Market intelligence para '{job_title}'"
            f"{' ' + seniority if seniority else ''}"
            f"{' em ' + location if location else ''}: "
            f"R$ {int(sal.get('min') or 0):,} - R$ {int(sal.get('max') or 0):,} "
            f"(confiança: {sal.get('confidence', 'low')})."
            f"{trend_info}"
        ),
    }
