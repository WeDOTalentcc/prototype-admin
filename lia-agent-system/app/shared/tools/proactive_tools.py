"""
Proactive Tools - Recruitment risk detection and alerts.

These tools identify recruitment bottlenecks and risks:
- Stagnant candidates (stuck in same stage too long)
- Pending offers (awaiting candidate response)
- Overdue recruiter tasks
- Pipeline risks (stagnant candidates, empty pipelines, low conversion)

All functions are async, connect to PostgreSQL via AsyncSessionLocal,
and return Dict[str, Any] with 'success', 'data', and 'message' keys.
"""
import logging
from typing import Any

from lia_agents_core.react_loop import ToolDefinition
from sqlalchemy import text

from app.core.database import AsyncSessionLocal

logger = logging.getLogger(__name__)


async def check_stagnant_candidates(company_id: str, threshold_days: int = 7) -> dict[str, Any]:
    """Find candidates stuck in same stage for more than threshold days.

    Identifies candidates who have not progressed in the recruitment pipeline
    for a specified duration, indicating potential bottlenecks or delays.

    Args:
        company_id: The company identifier to filter data.
        threshold_days: Number of days to consider as stagnation threshold (default: 7).

    Returns:
        Dict with stagnant_count, stagnant_candidates list (with details),
        and affected_stages breakdown.
    """
    try:
        async with AsyncSessionLocal() as session:
            params: dict[str, Any] = {
                "company_id": company_id,
                "threshold_days": threshold_days,
            }

            result = await session.execute(
                text("""
                    SELECT
                        vc.candidate_id,
                        c.name,
                        c.email,
                        vc.stage,
                        jv.title,
                        EXTRACT(EPOCH FROM (NOW() - vc.updated_at)) / 86400.0 AS days_in_stage
                    FROM vacancy_candidates vc
                    JOIN job_vacancies jv ON vc.vacancy_id = jv.id
                    JOIN candidates c ON vc.candidate_id = c.id
                    WHERE jv.company_id = :company_id
                      AND EXTRACT(EPOCH FROM (NOW() - vc.updated_at)) / 86400.0 > :threshold_days
                    ORDER BY days_in_stage DESC
                """),
                params,
            )
            rows = result.mappings().all()

            stagnant_candidates_list: list[dict[str, Any]] = []
            affected_stages: dict[str, int] = {}

            for row in rows:
                stagnant_candidates_list.append({
                    "candidate_id": str(row["candidate_id"]),
                    "name": row["name"],
                    "email": row["email"],
                    "stage": row["stage"],
                    "job_title": row["title"],
                    "days_in_stage": round(float(row["days_in_stage"]), 1),
                })
                stage_key = row["stage"] or "unknown"
                affected_stages[stage_key] = affected_stages.get(stage_key, 0) + 1

            return {
                "success": True,
                "data": {
                    "stagnant_count": len(stagnant_candidates_list),
                    "stagnant_candidates": stagnant_candidates_list,
                    "affected_stages": affected_stages,
                },
                "message": (
                    f"Found {len(stagnant_candidates_list)} candidates stagnant for >"
                    f" {threshold_days} days."
                ),
            }
    except Exception as e:
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.error(f"[proactive_tools] check_stagnant_candidates error: {e}", exc_info=True)
        return {"success": False, "error": str(e)}


async def check_pending_offers(company_id: str, threshold_hours: int = 72) -> dict[str, Any]:
    """Find offers awaiting candidate response for more than threshold hours.

    Identifies offers that have been pending response for an extended period,
    indicating potential risk of candidate disengagement or withdrawal.

    Args:
        company_id: The company identifier to filter data.
        threshold_hours: Number of hours to consider as pending threshold (default: 72).

    Returns:
        Dict with pending_offers_count, pending_offers list (with details),
        and risk_level assessment.
    """
    try:
        async with AsyncSessionLocal() as session:
            params: dict[str, Any] = {
                "company_id": company_id,
                "threshold_hours": threshold_hours,
            }

            result = await session.execute(
                text("""
                    SELECT
                        vc.candidate_id,
                        c.name,
                        c.email,
                        jv.title,
                        vc.updated_at,
                        EXTRACT(EPOCH FROM (NOW() - vc.updated_at)) / 3600.0 AS hours_pending
                    FROM vacancy_candidates vc
                    JOIN job_vacancies jv ON vc.vacancy_id = jv.id
                    JOIN candidates c ON vc.candidate_id = c.id
                    WHERE jv.company_id = :company_id
                      AND vc.stage = 'offer'
                      AND EXTRACT(EPOCH FROM (NOW() - vc.updated_at)) / 3600.0 > :threshold_hours
                    ORDER BY hours_pending DESC
                """),
                params,
            )
            rows = result.mappings().all()

            pending_offers_list: list[dict[str, Any]] = []

            for row in rows:
                hours_pending = float(row["hours_pending"])
                pending_offers_list.append({
                    "candidate_id": str(row["candidate_id"]),
                    "name": row["name"],
                    "email": row["email"],
                    "job_title": row["title"],
                    "hours_pending": round(hours_pending, 1),
                    "days_pending": round(hours_pending / 24.0, 1),
                })

            risk_level = "high" if len(pending_offers_list) > 5 else "medium" if len(pending_offers_list) > 0 else "low"

            return {
                "success": True,
                "data": {
                    "pending_offers_count": len(pending_offers_list),
                    "pending_offers": pending_offers_list,
                    "risk_level": risk_level,
                },
                "message": (
                    f"Found {len(pending_offers_list)} offers pending >"
                    f" {threshold_hours} hours. Risk level: {risk_level}."
                ),
            }
    except Exception as e:
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.error(f"[proactive_tools] check_pending_offers error: {e}", exc_info=True)
        return {"success": False, "error": str(e)}


async def check_overdue_tasks(company_id: str, user_id: str) -> dict[str, Any]:
    """Find overdue tasks for a recruiter.

    Identifies tasks assigned to a recruiter that have passed their due date,
    indicating areas requiring immediate attention.

    Args:
        company_id: The company identifier to filter data.
        user_id: The recruiter user ID to filter tasks.

    Returns:
        Dict with overdue_count, overdue_tasks list (with details),
        and priority_summary.
    """
    try:
        async with AsyncSessionLocal() as session:
            params: dict[str, Any] = {
                "company_id": company_id,
                "user_id": user_id,
            }

            result = await session.execute(
                text("""
                    SELECT
                        t.id,
                        t.title,
                        t.description,
                        t.due_date,
                        t.priority,
                        t.status,
                        EXTRACT(EPOCH FROM (NOW() - t.due_date)) / 86400.0 AS days_overdue
                    FROM tasks t
                    WHERE t.company_id = :company_id
                      AND t.assigned_to = :user_id
                      AND t.status NOT IN ('completed', 'cancelled')
                      AND t.due_date < NOW()
                    ORDER BY t.priority DESC, days_overdue DESC
                """),
                params,
            )
            rows = result.mappings().all()

            overdue_tasks_list: list[dict[str, Any]] = []
            priority_summary: dict[str, int] = {}

            for row in rows:
                priority = row["priority"] or "medium"
                overdue_tasks_list.append({
                    "task_id": str(row["id"]),
                    "title": row["title"],
                    "description": row["description"],
                    "due_date": row["due_date"].isoformat() if row["due_date"] else None,
                    "priority": priority,
                    "status": row["status"],
                    "days_overdue": round(float(row["days_overdue"]), 1),
                })
                priority_summary[priority] = priority_summary.get(priority, 0) + 1

            return {
                "success": True,
                "data": {
                    "overdue_count": len(overdue_tasks_list),
                    "overdue_tasks": overdue_tasks_list,
                    "priority_summary": priority_summary,
                },
                "message": (
                    f"Found {len(overdue_tasks_list)} overdue tasks for recruiter {user_id}."
                ),
            }
    except Exception as e:
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.error(f"[proactive_tools] check_overdue_tasks error: {e}", exc_info=True)
        return {"success": False, "error": str(e)}


async def check_pipeline_risks(company_id: str) -> dict[str, Any]:
    """Comprehensive risk scan: stagnant candidates, empty pipelines, low conversion.

    Performs a holistic health check on the entire recruitment pipeline,
    identifying multiple risk factors that could impact hiring outcomes.

    Args:
        company_id: The company identifier to filter data.

    Returns:
        Dict with overall_risk_level, stagnant_candidates_count,
        empty_pipelines list, low_conversion_jobs, and recommendations.
    """
    try:
        async with AsyncSessionLocal() as session:
            params: dict[str, Any] = {"company_id": company_id}

            stagnant_result = await session.execute(
                text("""
                    SELECT COUNT(*) AS stagnant_count
                    FROM vacancy_candidates vc
                    JOIN job_vacancies jv ON vc.vacancy_id = jv.id
                    WHERE jv.company_id = :company_id
                      AND EXTRACT(EPOCH FROM (NOW() - vc.updated_at)) / 86400.0 > 7
                """),
                params,
            )
            stagnant_row = stagnant_result.mappings().first()
            stagnant_candidates_count = int(stagnant_row["stagnant_count"]) if stagnant_row else 0

            empty_pipelines_result = await session.execute(
                text("""
                    SELECT
                        jv.id,
                        jv.title,
                        jv.department,
                        COUNT(vc.candidate_id) AS candidate_count
                    FROM job_vacancies jv
                    LEFT JOIN vacancy_candidates vc ON vc.vacancy_id = jv.id
                    WHERE jv.company_id = :company_id
                      AND jv.status = 'open'
                    GROUP BY jv.id, jv.title, jv.department
                    HAVING COUNT(vc.candidate_id) < 5
                    ORDER BY candidate_count ASC
                """),
                params,
            )
            empty_pipelines_rows = empty_pipelines_result.mappings().all()

            empty_pipelines: list[dict[str, Any]] = []
            for row in empty_pipelines_rows:
                empty_pipelines.append({
                    "job_id": str(row["id"]),
                    "title": row["title"],
                    "department": row["department"],
                    "candidate_count": int(row["candidate_count"]),
                })

            low_conversion_result = await session.execute(
                text("""
                    SELECT
                        jv.id,
                        jv.title,
                        COUNT(CASE WHEN vc.stage = 'applied' THEN 1 END) AS applied_count,
                        COUNT(CASE WHEN vc.stage IN ('screening', 'interview', 'technical_test', 'offer', 'hired') THEN 1 END) AS progressed_count
                    FROM job_vacancies jv
                    LEFT JOIN vacancy_candidates vc ON vc.vacancy_id = jv.id
                    WHERE jv.company_id = :company_id
                      AND jv.status = 'open'
                    GROUP BY jv.id, jv.title
                    HAVING COUNT(CASE WHEN vc.stage = 'applied' THEN 1 END) > 0
                """),
                params,
            )
            low_conversion_rows = low_conversion_result.mappings().all()

            low_conversion_jobs: list[dict[str, Any]] = []
            for row in low_conversion_rows:
                applied = int(row["applied_count"])
                progressed = int(row["progressed_count"])
                if applied > 0:
                    conversion_rate = round(progressed / (applied + progressed), 2) if (applied + progressed) > 0 else 0.0
                    if conversion_rate < 0.3:
                        low_conversion_jobs.append({
                            "job_id": str(row["id"]),
                            "title": row["title"],
                            "conversion_rate": conversion_rate,
                            "applied_count": applied,
                            "progressed_count": progressed,
                        })

            risk_count = stagnant_candidates_count + len(empty_pipelines) + len(low_conversion_jobs)
            if risk_count > 10:
                overall_risk_level = "high"
            elif risk_count > 5:
                overall_risk_level = "medium"
            else:
                overall_risk_level = "low"

            recommendations: list[str] = []
            if stagnant_candidates_count > 0:
                recommendations.append(f"Review {stagnant_candidates_count} stagnant candidates for intervention.")
            if len(empty_pipelines) > 0:
                recommendations.append(f"Source candidates for {len(empty_pipelines)} jobs with weak pipelines.")
            if len(low_conversion_jobs) > 0:
                recommendations.append(f"Analyze {len(low_conversion_jobs)} jobs with low conversion rates.")

            return {
                "success": True,
                "data": {
                    "overall_risk_level": overall_risk_level,
                    "stagnant_candidates_count": stagnant_candidates_count,
                    "empty_pipelines": empty_pipelines,
                    "low_conversion_jobs": low_conversion_jobs,
                    "recommendations": recommendations,
                },
                "message": (
                    f"Pipeline risk scan complete. Overall risk level: {overall_risk_level}. "
                    f"Risk factors: {stagnant_candidates_count} stagnant, "
                    f"{len(empty_pipelines)} weak pipelines, "
                    f"{len(low_conversion_jobs)} low conversion."
                ),
            }
    except Exception as e:
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.error(f"[proactive_tools] check_pipeline_risks error: {e}", exc_info=True)
        return {"success": False, "error": str(e)}


def get_proactive_tools() -> list[ToolDefinition]:
    """Return all proactive tools as ToolDefinition objects for the ReAct loop.

    Each ToolDefinition includes the tool name, description, JSON Schema
    parameters, and the async callable function.

    Returns:
        List of ToolDefinition instances ready for ReActConfig.available_tools.
    """
    company_id_param = {
        "type": "string",
        "description": "Company ID to scope the analysis",
    }

    return [
        ToolDefinition(
            name="check_stagnant_candidates",
            description=(
                "Find candidates stuck in same stage for more than threshold days. "
                "Identifies bottlenecks in recruitment pipeline."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "threshold_days": {
                        "type": "integer",
                        "description": "Number of days to consider as stagnation threshold (default: 7)",
                    },
                },
                "required": [],
            },
            function=check_stagnant_candidates,
        ),
        ToolDefinition(
            name="check_pending_offers",
            description=(
                "Find offers awaiting candidate response for more than threshold hours. "
                "Identifies offers at risk of candidate withdrawal."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "threshold_hours": {
                        "type": "integer",
                        "description": "Number of hours to consider as pending threshold (default: 72)",
                    },
                },
                "required": [],
            },
            function=check_pending_offers,
        ),
        ToolDefinition(
            name="check_overdue_tasks",
            description=(
                "Find overdue tasks assigned to a recruiter. "
                "Identifies tasks requiring immediate attention."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string",
                        "description": "The recruiter user ID to filter tasks",
                    },
                },
                "required": ["user_id"],
            },
            function=check_overdue_tasks,
        ),
        ToolDefinition(
            name="check_pipeline_risks",
            description=(
                "Comprehensive risk scan: stagnant candidates, empty pipelines, low conversion. "
                "Provides holistic health check of recruitment pipeline."
            ),
            parameters={
                "type": "object",
                "properties": {
                },
                "required": [],
            },
            function=check_pipeline_risks,
        ),
    ]
