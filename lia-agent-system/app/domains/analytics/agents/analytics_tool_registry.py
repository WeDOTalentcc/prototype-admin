"""Analytics ReAct Agent — Tool Registry.

Wraps analytics domain services into ToolDefinition format so the ReActLoop
can autonomously decide which tools to call.

Services wrapped:
- JobInsightsService      → get_job_insights
- PredictiveAnalyticsService → predict_hiring_metrics
- JobReportService        → generate_job_report
- CandidateReportService  → generate_candidate_report
- SearchAnalyticsService  → get_search_analytics
- AgentMonitoringService  → get_agent_performance
"""
import logging
from typing import Any

from lia_agents_core.react_loop import ToolDefinition

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Tool wrappers
# ---------------------------------------------------------------------------


async def _wrap_get_job_insights(**kwargs: Any) -> dict[str, Any]:
    """Get salary benchmark, skills frequency and time-to-fill for a job title."""
    from app.core.database import AsyncSessionLocal
    from app.domains.analytics.services.job_insights_service import JobInsightsService

    job_title = kwargs.get("job_title", "")
    company_id = kwargs.get("company_id", "")
    location = kwargs.get("location")

    if not job_title:
        return {"success": False, "message": "job_title é obrigatório"}
    if not company_id:
        return {"success": False, "message": "company_id é obrigatório"}

    try:
        svc = JobInsightsService()
        async with AsyncSessionLocal() as db:
            salary = await svc.get_salary_benchmark(
                db=db,
                company_id=company_id,
                role=job_title,
                location=location,
            )
            skills = await svc.get_common_skills(
                db=db,
                company_id=company_id,
                role=job_title,
            )
            time_to_fill = await svc.get_time_to_fill(
                db=db,
                company_id=company_id,
                role=job_title,
            )

        return {
            "success": True,
            "job_title": job_title,
            "salary_benchmark": salary,
            "common_skills": skills,
            "time_to_fill": time_to_fill,
        }
    except Exception as e:
        logger.error(f"[analytics_tools] get_job_insights error: {e}", exc_info=True)
        return {"success": False, "message": str(e)}


async def _wrap_predict_hiring_metrics(**kwargs: Any) -> dict[str, Any]:
    """Predict hiring probability and time to fill for a job vacancy."""
    from app.core.database import AsyncSessionLocal
    from app.domains.analytics.services.predictive_analytics_service import PredictiveAnalyticsService

    job_id = kwargs.get("job_id", "")
    company_id = kwargs.get("company_id", "")

    if not job_id:
        return {"success": False, "message": "job_id é obrigatório"}
    if not company_id:
        return {"success": False, "message": "company_id é obrigatório"}

    try:
        svc = PredictiveAnalyticsService()
        async with AsyncSessionLocal() as db:
            ttf = await svc.predict_time_to_fill(job_id=job_id, db=db)
            forecast = await svc.generate_pipeline_forecast(job_id=job_id, weeks_ahead=4, db=db)

        return {
            "success": True,
            "job_id": job_id,
            "time_to_fill_prediction": ttf,
            "pipeline_forecast": forecast,
        }
    except Exception as e:
        logger.error(f"[analytics_tools] predict_hiring_metrics error: {e}", exc_info=True)
        return {"success": False, "message": str(e)}


async def _wrap_generate_job_report(**kwargs: Any) -> dict[str, Any]:
    """Generate a full analytics report for a job vacancy."""
    from uuid import UUID

    from app.core.database import AsyncSessionLocal
    from app.domains.analytics.services.job_report_service import JobReportService
    from app.domains.analytics.services.predictive_analytics_service import PredictiveAnalyticsService

    job_id = kwargs.get("job_id", "")
    company_id = kwargs.get("company_id", "")
    include_predictions = kwargs.get("include_predictions", True)

    if not job_id:
        return {"success": False, "message": "job_id é obrigatório"}
    if not company_id:
        return {"success": False, "message": "company_id é obrigatório"}

    try:
        report_svc = JobReportService()
        async with AsyncSessionLocal() as db:
            try:
                job_uuid = UUID(job_id)
            except ValueError:
                return {"success": False, "message": f"job_id inválido: {job_id}"}

            # Retrieve funnel data and source analysis for the report summary
            funnel_data = await report_svc._get_funnel_data(job_uuid, db)
            source_data = await report_svc._get_source_analysis(job_uuid, db)
            time_metrics = await report_svc._get_time_metrics(job_uuid, db)

            result: dict[str, Any] = {
                "success": True,
                "job_id": job_id,
                "company_id": company_id,
                "funnel_data": funnel_data,
                "source_analysis": source_data,
                "time_metrics": time_metrics,
            }

            if include_predictions:
                pred_svc = PredictiveAnalyticsService()
                ttf = await pred_svc.predict_time_to_fill(job_id=job_id, db=db)
                result["predictions"] = {"time_to_fill": ttf}

        return result
    except Exception as e:
        logger.error(f"[analytics_tools] generate_job_report error: {e}", exc_info=True)
        return {"success": False, "message": str(e)}


async def _wrap_generate_candidate_report(**kwargs: Any) -> dict[str, Any]:
    """Generate comparative candidate report / parecer for one or more candidates."""
    from app.core.database import AsyncSessionLocal
    from app.domains.analytics.services.candidate_report_service import CandidateReportService

    candidate_ids: list[int] = kwargs.get("candidate_ids", [])
    job_id: str = kwargs.get("job_id", "") or ""

    if not candidate_ids:
        return {"success": False, "message": "candidate_ids é obrigatório (lista de IDs)"}

    try:
        svc = CandidateReportService()
        reports = []
        async with AsyncSessionLocal() as db:
            for cid in candidate_ids:
                try:
                    parecer = await svc.generate_parecer(
                        db=db,
                        candidate_id=str(cid),
                        job_id=job_id if job_id else None,
                    )
                    reports.append(parecer)
                except Exception as inner_exc:
                    logger.warning(
                        f"[analytics_tools] parecer failed for candidate {cid}: {inner_exc}"
                    )
                    reports.append({"candidate_id": cid, "error": str(inner_exc)})

        return {
            "success": True,
            "candidate_count": len(reports),
            "job_id": job_id or None,
            "reports": reports,
        }
    except Exception as e:
        logger.error(f"[analytics_tools] generate_candidate_report error: {e}", exc_info=True)
        return {"success": False, "message": str(e)}


async def _wrap_get_search_analytics(**kwargs: Any) -> dict[str, Any]:
    """Get search performance metrics for a company over the past N days."""
    from sqlalchemy import text

    from app.core.database import AsyncSessionLocal
    from app.domains.analytics.services.search_analytics_service import SearchAnalyticsService

    company_id = kwargs.get("company_id", "")
    days = int(kwargs.get("days", 30))

    if not company_id:
        return {"success": False, "message": "company_id é obrigatório"}

    try:
        svc = SearchAnalyticsService()
        async with AsyncSessionLocal() as db:
            # Retrieve recent candidate search snapshots from the DB as proxy data
            text("""
                SELECT id, name, current_title, current_company, email, phone, location,
                       skills, experience_years, created_at
                FROM candidates
                WHERE company_id = :company_id
                  AND created_at >= NOW() - INTERVAL ':days days'
                ORDER BY created_at DESC
                LIMIT 200
            """)
            try:
                result = await db.execute(
                    text(
                        "SELECT id, name, current_title, current_company, email, phone, "
                        "location, skills, experience_years "
                        "FROM candidates "
                        "WHERE company_id = :company_id "
                        "  AND created_at >= NOW() - :days * INTERVAL '1 day' "
                        "ORDER BY created_at DESC LIMIT 200"
                    ),
                    {"company_id": company_id, "days": days},
                )
                rows = result.fetchall()
            except Exception:
                rows = []

            candidates = []
            for row in rows:
                candidates.append({
                    "id": str(row[0]) if row[0] else "",
                    "name": row[1] or "",
                    "current_title": row[2] or "",
                    "current_company": row[3] or "",
                    "email": row[4] or "",
                    "phone": row[5] or "",
                    "location": row[6] or "",
                    "skills": row[7] or [],
                    "experience_years": row[8] or 0,
                })

        analytics = svc.analyze_search_results(
            candidates=candidates,
            search_criteria={"company_id": company_id, "days": days},
        )
        return {
            "success": True,
            "company_id": company_id,
            "period_days": days,
            "analytics": analytics,
        }
    except Exception as e:
        logger.error(f"[analytics_tools] get_search_analytics error: {e}", exc_info=True)
        return {"success": False, "message": str(e)}


async def _wrap_get_agent_performance(**kwargs: Any) -> dict[str, Any]:
    """Get AI agent performance and cost metrics for a company."""
    from app.core.database import AsyncSessionLocal
    from app.shared.governance.agent_monitoring_service import AgentMonitoringService

    company_id = kwargs.get("company_id", "")
    agent_type = kwargs.get("agent_type")

    if not company_id:
        return {"success": False, "message": "company_id é obrigatório"}

    try:
        svc = AgentMonitoringService()
        async with AsyncSessionLocal() as db:
            dashboard = await svc.get_agents_dashboard(db=db, company_id=company_id)

        # Filter by agent_type if specified
        if agent_type and isinstance(dashboard, dict):
            agents = dashboard.get("agents", [])
            filtered = [a for a in agents if a.get("id") == agent_type or a.get("name", "").lower() == agent_type.lower()]
            if filtered:
                dashboard["agents"] = filtered

        return {
            "success": True,
            "company_id": company_id,
            "agent_type": agent_type,
            "dashboard": dashboard,
        }
    except Exception as e:
        logger.error(f"[analytics_tools] get_agent_performance error: {e}", exc_info=True)
        return {"success": False, "message": str(e)}


# ---------------------------------------------------------------------------
# Public registry
# ---------------------------------------------------------------------------

def get_analytics_tools() -> list[ToolDefinition]:
    """Return all ToolDefinitions for the Analytics domain."""
    return [
        ToolDefinition(
            name="get_job_insights",
            description=(
                "Obter benchmark salarial, frequência de skills e tempo médio de fechamento "
                "para um cargo. Parâmetros: job_title (str, obrigatório), company_id (str, obrigatório), "
                "location (str, opcional)."
            ),
            function=_wrap_get_job_insights,
        ),
        ToolDefinition(
            name="predict_hiring_metrics",
            description=(
                "Prever probabilidade de contratação e tempo de fechamento de uma vaga usando IA. "
                "Parâmetros: job_id (str, obrigatório), company_id (str, obrigatório)."
            ),
            function=_wrap_predict_hiring_metrics,
        ),
        ToolDefinition(
            name="generate_job_report",
            description=(
                "Gerar relatório completo de uma vaga: funil, fontes, tempo por etapa e previsões. "
                "Parâmetros: job_id (str, obrigatório), company_id (str, obrigatório), "
                "include_predictions (bool, padrão True)."
            ),
            function=_wrap_generate_job_report,
        ),
        ToolDefinition(
            name="generate_candidate_report",
            description=(
                "Gerar parecer automático e comparação entre candidatos. "
                "Parâmetros: candidate_ids (list[int], obrigatório), job_id (str, opcional)."
            ),
            function=_wrap_generate_candidate_report,
        ),
        ToolDefinition(
            name="get_search_analytics",
            description=(
                "Obter métricas de performance das buscas de candidatos: qualidade de contato, "
                "distribuições, top skills e alertas. "
                "Parâmetros: company_id (str, obrigatório), days (int, padrão 30)."
            ),
            function=_wrap_get_search_analytics,
        ),
        ToolDefinition(
            name="get_agent_performance",
            description=(
                "Obter métricas de performance e custo dos agentes de IA. "
                "Parâmetros: company_id (str, obrigatório), agent_type (str, opcional — "
                "ex: sourcing, screening, scheduling)."
            ),
            function=_wrap_get_agent_performance,
        ),
    ]


def get_stage_tools(stage: str) -> list[ToolDefinition]:
    """Return tools available for a given analytics stage."""
    from app.domains.analytics.agents.analytics_stage_context import get_stage_tools as _stage_tools
    stage_tool_names = set(_stage_tools(stage))
    return [t for t in get_analytics_tools() if t.name in stage_tool_names]
