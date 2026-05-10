"""
Insight Tools - Cross-reference analytics for consultive-quality recruitment insights.

These tools query multiple tables (vacancy_candidates, job_vacancies, candidates)
to produce aggregated metrics such as pipeline health, conversion rates,
time-to-fill statistics, and candidate quality distributions.

All functions are async, connect to PostgreSQL via AsyncSessionLocal,
and return Dict[str, Any] with 'success', 'data', and 'message' keys.
"""
import logging
from typing import Any

from lia_agents_core.react_loop import ToolDefinition
from sqlalchemy import text

from app.core.database import AsyncSessionLocal

logger = logging.getLogger(__name__)

STAGE_ORDER = [
    "applied",
    "screening",
    "interview",
    "technical_test",
    "offer",
    "hired",
]


async def get_pipeline_health(company_id: str, job_id: str | None = None) -> dict[str, Any]:
    """Analyse pipeline health for a company or specific job vacancy.

    Counts candidates per stage, calculates average days in each stage,
    and identifies stalled candidates (>7 days without stage change).

    Args:
        company_id: The company identifier to filter data.
        job_id: Optional job vacancy ID to narrow the analysis.

    Returns:
        Dict with total_candidates, by_stage counts, stalled_candidates,
        avg_days_in_stage, and bottleneck_stage.
    """
    try:
        async with AsyncSessionLocal() as session:
            params: dict[str, Any] = {"company_id": company_id}
            job_filter = ""
            if job_id:
                job_filter = "AND vc.vacancy_id = :job_id"
                params["job_id"] = job_id

            stage_result = await session.execute(
                text(f"""
                    SELECT
                        vc.stage,
                        COUNT(*) AS cnt,
                        COALESCE(AVG(
                            EXTRACT(EPOCH FROM (NOW() - vc.updated_at)) / 86400.0
                        ), 0) AS avg_days
                    FROM vacancy_candidates vc
                    JOIN job_vacancies jv ON vc.vacancy_id = jv.id
                    WHERE jv.company_id = :company_id
                      {job_filter}
                    GROUP BY vc.stage
                """),
                params,
            )
            stage_rows = stage_result.mappings().all()

            stalled_result = await session.execute(
                text(f"""
                    SELECT COUNT(*) AS stalled
                    FROM vacancy_candidates vc
                    JOIN job_vacancies jv ON vc.vacancy_id = jv.id
                    WHERE jv.company_id = :company_id
                      {job_filter}
                      AND EXTRACT(EPOCH FROM (NOW() - vc.updated_at)) / 86400.0 > 7
                """),
                params,
            )
            stalled_row = stalled_result.mappings().first()

            by_stage: dict[str, int] = {}
            avg_days_in_stage: dict[str, float] = {}
            total_candidates = 0

            for row in stage_rows:
                stage_name = row["stage"] or "unknown"
                count = int(row["cnt"])
                by_stage[stage_name] = count
                avg_days_in_stage[stage_name] = round(float(row["avg_days"]), 1)
                total_candidates += count

            bottleneck_stage = max(avg_days_in_stage, key=lambda k: avg_days_in_stage[k]) if avg_days_in_stage else None
            stalled_candidates = int(stalled_row["stalled"]) if stalled_row else 0

            return {
                "success": True,
                "data": {
                    "total_candidates": total_candidates,
                    "by_stage": by_stage,
                    "stalled_candidates": stalled_candidates,
                    "avg_days_in_stage": avg_days_in_stage,
                    "bottleneck_stage": bottleneck_stage,
                },
                "message": f"Pipeline health analysis complete: {total_candidates} candidates, {stalled_candidates} stalled.",
            }
    except Exception as e:
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.error(f"[insight_tools] get_pipeline_health error: {e}", exc_info=True)
        return {"success": False, "error": str(e)}


async def get_conversion_rates(company_id: str, job_id: str | None = None) -> dict[str, Any]:
    """Calculate stage-to-stage conversion rates for the recruitment funnel.

    For each consecutive pair of stages, computes the ratio of candidates
    that reached the later stage versus the earlier one.

    Args:
        company_id: The company identifier to filter data.
        job_id: Optional job vacancy ID to narrow the analysis.

    Returns:
        Dict with conversion_rates per transition, overall_funnel_rate,
        and weakest_stage transition name.
    """
    try:
        async with AsyncSessionLocal() as session:
            params: dict[str, Any] = {"company_id": company_id}
            job_filter = ""
            if job_id:
                job_filter = "AND vc.vacancy_id = :job_id"
                params["job_id"] = job_id

            result = await session.execute(
                text(f"""
                    SELECT vc.stage, COUNT(*) AS cnt
                    FROM vacancy_candidates vc
                    JOIN job_vacancies jv ON vc.vacancy_id = jv.id
                    WHERE jv.company_id = :company_id
                      {job_filter}
                    GROUP BY vc.stage
                """),
                params,
            )
            rows = result.mappings().all()

            stage_counts: dict[str, int] = {row["stage"]: int(row["cnt"]) for row in rows if row["stage"]}

            conversion_rates: dict[str, float] = {}
            for i in range(len(STAGE_ORDER) - 1):
                from_stage = STAGE_ORDER[i]
                to_stage = STAGE_ORDER[i + 1]
                from_count = stage_counts.get(from_stage, 0)
                to_count = stage_counts.get(to_stage, 0)
                key = f"{from_stage}_to_{to_stage}"
                if from_count > 0:
                    conversion_rates[key] = round(to_count / from_count, 2)
                else:
                    conversion_rates[key] = 0.0

            first_count = stage_counts.get(STAGE_ORDER[0], 0)
            last_count = stage_counts.get(STAGE_ORDER[-1], 0)
            overall_funnel_rate = round(last_count / first_count, 2) if first_count > 0 else 0.0

            weakest_stage = min(conversion_rates, key=lambda k: conversion_rates[k]) if conversion_rates else None

            return {
                "success": True,
                "data": {
                    "conversion_rates": conversion_rates,
                    "overall_funnel_rate": overall_funnel_rate,
                    "weakest_stage": weakest_stage,
                },
                "message": f"Conversion rates calculated. Overall funnel rate: {overall_funnel_rate}.",
            }
    except Exception as e:
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.error(f"[insight_tools] get_conversion_rates error: {e}", exc_info=True)
        return {"success": False, "error": str(e)}


async def get_time_to_fill(company_id: str, job_id: str | None = None) -> dict[str, Any]:
    """Calculate time-to-fill statistics for closed/filled job vacancies.

    Measures the number of days between job creation and the closed_at or
    updated_at timestamp for vacancies with status 'filled' or 'closed'.

    Args:
        company_id: The company identifier to filter data.
        job_id: Optional job vacancy ID to narrow the analysis.

    Returns:
        Dict with avg_days_to_fill, median_days, fastest, slowest,
        and by_department breakdown.
    """
    try:
        async with AsyncSessionLocal() as session:
            params: dict[str, Any] = {"company_id": company_id}
            job_filter = ""
            if job_id:
                job_filter = "AND jv.id = :job_id"
                params["job_id"] = job_id

            result = await session.execute(
                text(f"""
                    SELECT
                        jv.department,
                        EXTRACT(EPOCH FROM (
                            COALESCE(jv.closed_at, jv.updated_at) - jv.created_at
                        )) / 86400.0 AS days_to_fill
                    FROM job_vacancies jv
                    WHERE jv.company_id = :company_id
                      AND jv.status IN ('filled', 'closed')
                      {job_filter}
                """),
                params,
            )
            rows = result.mappings().all()

            if not rows:
                return {
                    "success": True,
                    "data": {
                        "avg_days_to_fill": 0,
                        "median_days": 0,
                        "fastest": 0,
                        "slowest": 0,
                        "by_department": {},
                    },
                    "message": "No filled/closed vacancies found for this company.",
                }

            all_days = [round(float(r["days_to_fill"]), 1) for r in rows]
            all_days.sort()

            dept_days: dict[str, list[float]] = {}
            for r in rows:
                dept = r["department"] or "unknown"
                dept_days.setdefault(dept, []).append(float(r["days_to_fill"]))

            by_department = {
                dept: round(sum(vals) / len(vals), 1)
                for dept, vals in dept_days.items()
            }

            n = len(all_days)
            median = all_days[n // 2] if n % 2 == 1 else round((all_days[n // 2 - 1] + all_days[n // 2]) / 2, 1)

            return {
                "success": True,
                "data": {
                    "avg_days_to_fill": round(sum(all_days) / n, 1),
                    "median_days": median,
                    "fastest": all_days[0],
                    "slowest": all_days[-1],
                    "by_department": by_department,
                },
                "message": f"Time-to-fill analysis for {n} filled vacancies.",
            }
    except Exception as e:
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.error(f"[insight_tools] get_time_to_fill error: {e}", exc_info=True)
        return {"success": False, "error": str(e)}


async def get_candidate_quality_distribution(company_id: str, job_id: str | None = None) -> dict[str, Any]:
    """Analyse the distribution of candidate scores across score buckets.

    Groups candidates by LIA score ranges (0-20, 21-40, etc.) and
    returns the top-scoring candidates.

    Args:
        company_id: The company identifier to filter data.
        job_id: Optional job vacancy ID to narrow the analysis.

    Returns:
        Dict with score_distribution histogram, avg_score,
        and top_candidates list.
    """
    try:
        async with AsyncSessionLocal() as session:
            params: dict[str, Any] = {"company_id": company_id}
            job_filter = ""
            if job_id:
                job_filter = "AND vc.vacancy_id = :job_id"
                params["job_id"] = job_id

            result = await session.execute(
                text(f"""
                    SELECT
                        vc.candidate_id,
                        c.name,
                        c.email,
                        COALESCE(vc.lia_score, 0) AS score
                    FROM vacancy_candidates vc
                    JOIN job_vacancies jv ON vc.vacancy_id = jv.id
                    JOIN candidates c ON vc.candidate_id = c.id
                    WHERE jv.company_id = :company_id
                      {job_filter}
                      AND vc.lia_score IS NOT NULL
                """),
                params,
            )
            rows = result.mappings().all()

            buckets = {
                "0-20": 0,
                "21-40": 0,
                "41-60": 0,
                "61-80": 0,
                "81-100": 0,
            }
            scores: list[float] = []
            candidates_list: list[dict[str, Any]] = []

            for row in rows:
                s = float(row["score"])
                scores.append(s)
                candidates_list.append({
                    "candidate_id": str(row["candidate_id"]),
                    "name": row["name"],
                    "email": row["email"],
                    "score": round(s, 1),
                })
                if s <= 20:
                    buckets["0-20"] += 1
                elif s <= 40:
                    buckets["21-40"] += 1
                elif s <= 60:
                    buckets["41-60"] += 1
                elif s <= 80:
                    buckets["61-80"] += 1
                else:
                    buckets["81-100"] += 1

            candidates_list.sort(key=lambda x: x["score"], reverse=True)
            top_candidates = candidates_list[:10]
            avg_score = round(sum(scores) / len(scores), 1) if scores else 0.0

            return {
                "success": True,
                "data": {
                    "score_distribution": buckets,
                    "avg_score": avg_score,
                    "top_candidates": top_candidates,
                },
                "message": f"Quality distribution for {len(scores)} scored candidates. Avg: {avg_score}.",
            }
    except Exception as e:
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.error(f"[insight_tools] get_candidate_quality_distribution error: {e}", exc_info=True)
        return {"success": False, "error": str(e)}


def get_insight_tools() -> list[ToolDefinition]:
    """Return all insight tools as ToolDefinition objects for the ReAct loop.

    Each ToolDefinition includes the tool name, description, JSON Schema
    parameters, and the async callable function.

    Returns:
        List of ToolDefinition instances ready for ReActConfig.available_tools.
    """
    job_id_param = {
        "type": "string",
        "description": "Optional job vacancy ID to filter analysis to a specific job",
    }
    company_id_param = {
        "type": "string",
        "description": "Company ID to scope the analysis",
    }

    return [
        ToolDefinition(
            name="get_pipeline_health",
            description=(
                "Analyse pipeline health: candidates per stage, average days in stage, "
                "stalled candidates (>7 days), and bottleneck identification."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "job_id": job_id_param,
                },
                "required": [],
            },
            function=get_pipeline_health,
        ),
        ToolDefinition(
            name="get_conversion_rates",
            description=(
                "Calculate stage-to-stage conversion rates for the recruitment funnel, "
                "overall funnel rate, and identify the weakest conversion point."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "job_id": job_id_param,
                },
                "required": [],
            },
            function=get_conversion_rates,
        ),
        ToolDefinition(
            name="get_time_to_fill",
            description=(
                "Calculate time-to-fill statistics for filled/closed vacancies: "
                "average, median, fastest, slowest, and breakdown by department."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "job_id": job_id_param,
                },
                "required": [],
            },
            function=get_time_to_fill,
        ),
        ToolDefinition(
            name="get_candidate_quality_distribution",
            description=(
                "Analyse candidate score distribution across buckets (0-20, 21-40, etc.), "
                "average score, and list top-scoring candidates."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "job_id": job_id_param,
                },
                "required": [],
            },
            function=get_candidate_quality_distribution,
        ),
    ]
