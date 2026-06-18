"""Workload analysis tools: workload distribution and bottleneck analysis."""
import logging
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

from ._base import analytics_db, error_response, extract_context, success_response
from app.shared.tool_guards import validate_uuid_params
from app.shared.tool_handler import tool_handler
from app.tools.context_helpers import require_company_id_from_context

logger = logging.getLogger(__name__)


@tool_handler("analytics")
async def get_workload_distribution(
    team_id: str | None = None,
    include_details: bool = False,
    **kwargs
) -> dict[str, Any]:
    """
    Get team workload distribution metrics.

    Args:
        team_id: Optional team/department filter
        include_details: Include detailed job list per recruiter

    Returns:
        Workload metrics including total_active_jobs, jobs_per_recruiter,
        overloaded_recruiters, underloaded_recruiters
    """
    company_id = require_company_id_from_context(kwargs, "get_workload_distribution")

    logger.info(f"📊 Getting workload distribution (company: {company_id}, team: {team_id})")

    try:
        from sqlalchemy import and_, select
        from app.models.job_vacancy import JobVacancy

        async with analytics_db() as db:
            conditions = [
                JobVacancy.company_id == company_id,
                JobVacancy.status == "Ativa"
            ]

            if team_id:
                conditions.append(JobVacancy.department == team_id)

            # TENANT-EXEMPT: analytics tool builds conditions=[Model.company_id==X, ...] then where(and_(*conditions)); AST sensor cannot trace dynamic builder; T-RATCHET tenant_filter
            query = select(JobVacancy).where(and_(*conditions))
            result = await db.execute(query)
            jobs = result.scalars().all()

            total_active_jobs = len(jobs)
            jobs_per_recruiter: dict[str, Any] = {}

            for job in jobs:
                recruiter = getattr(job, 'recruiter', 'Não atribuído') or 'Não atribuído'
                if recruiter not in jobs_per_recruiter:
                    jobs_per_recruiter[recruiter] = {"count": 0, "jobs": []}
                jobs_per_recruiter[recruiter]["count"] += 1
                if include_details:
                    jobs_per_recruiter[recruiter]["jobs"].append({
                        "id": str(job.id),
                        "title": job.title,
                        "priority": getattr(job, 'priority', 'média'),
                        "created_at": job.created_at.isoformat() if job.created_at else None
                    })

            avg_jobs = total_active_jobs / len(jobs_per_recruiter) if jobs_per_recruiter else 0
            overload_threshold = avg_jobs * 1.5
            underload_threshold = avg_jobs * 0.5

            overloaded_recruiters = [
                {"recruiter": r, "job_count": d["count"], "excess": d["count"] - avg_jobs}
                for r, d in jobs_per_recruiter.items()
                if d["count"] > overload_threshold
            ]

            underloaded_recruiters = [
                {"recruiter": r, "job_count": d["count"], "capacity": avg_jobs - d["count"]}
                for r, d in jobs_per_recruiter.items()
                if d["count"] < underload_threshold and r != 'Não atribuído'
            ]

            if not include_details:
                jobs_per_recruiter = {r: d["count"] for r, d in jobs_per_recruiter.items()}

            return success_response(
                f"✅ Distribuição de carga: {total_active_jobs} vagas ativas entre {len(jobs_per_recruiter)} recrutadores",
                {
                    "total_active_jobs": total_active_jobs,
                    "recruiter_count": len(jobs_per_recruiter),
                    "average_jobs_per_recruiter": round(avg_jobs, 1),
                    "jobs_per_recruiter": jobs_per_recruiter,
                    "overloaded_recruiters": overloaded_recruiters,
                    "underloaded_recruiters": underloaded_recruiters,
                    "team_id": team_id
                }
            )

    except Exception as e:
        logger.error(f"❌ Error getting workload distribution: {e}", exc_info=True)
        return error_response(f"❌ Erro ao buscar distribuição de carga: {str(e)}", e)


@tool_handler("analytics")
async def get_bottleneck_analysis(
    job_id: str,
    period: str = "month",
    **kwargs
) -> dict[str, Any]:
    """
    Analyze pipeline bottlenecks for a specific job.

    Args:
        job_id: UUID of the job vacancy (required)
        period: Time period for analysis (week/month)

    Returns:
        Bottleneck analysis including highest_rejection_stage, average_time_per_stage,
        slowest_stage, and recommendations
    """
    company_id = require_company_id_from_context(kwargs, "get_bottleneck_analysis")

    _err = validate_uuid_params(job_id=job_id)
    if _err:
        return _err

    logger.info(f"🔍 Analyzing bottlenecks for job: {job_id} (company: {company_id})")

    try:
        from sqlalchemy import and_, select
        from app.models.candidate import Candidate, VacancyCandidate
        from app.models.job_vacancy import JobVacancy

        async with analytics_db() as db:
            job_result = await db.execute(
                select(JobVacancy).where(
                    and_(
                        JobVacancy.id == UUID(job_id),
                        JobVacancy.company_id == company_id
                    )
                )
            )
            job = job_result.scalar_one_or_none()

            if not job:
                return {"success": False, "message": f"Vaga não encontrada: {job_id}", "error": "job_not_found"}

            vc_result = await db.execute(
                select(VacancyCandidate, Candidate).join(
                    Candidate,
                    and_(
                        VacancyCandidate.candidate_id == Candidate.id,
                        Candidate.company_id == company_id
                    )
                ).where(
                    and_(
                        VacancyCandidate.vacancy_id == UUID(job_id),
                        VacancyCandidate.company_id == company_id
                    )
                )
            )
            vacancy_candidates = vc_result.all()

            stages = ["Triagem", "Entrevista RH", "Entrevista Técnica", "Entrevista Final", "Oferta", "Contratado", "Reprovado"]
            stage_stats: dict[str, dict[str, Any]] = {s: {"count": 0, "rejected": 0, "time_in_stage": []} for s in stages}

            for vc, c in vacancy_candidates:
                stage = getattr(vc, 'stage', 'Triagem') or 'Triagem'
                status = getattr(vc, 'status', '') or ''

                if stage in stage_stats:
                    stage_stats[stage]["count"] += 1

                    if status.lower() in ['rejected', 'reprovado', 'declined']:
                        stage_stats[stage]["rejected"] += 1

                    if hasattr(vc, 'created_at') and hasattr(vc, 'updated_at'):
                        if vc.created_at and vc.updated_at:
                            days_in_stage = (vc.updated_at - vc.created_at).days
                            stage_stats[stage]["time_in_stage"].append(days_in_stage)

            rejection_rates = {}
            average_time_per_stage = {}

            for stage, stats in stage_stats.items():
                if stats["count"] > 0:
                    rejection_rates[stage] = round(stats["rejected"] / stats["count"] * 100, 1)
                    if stats["time_in_stage"]:
                        average_time_per_stage[stage] = round(sum(stats["time_in_stage"]) / len(stats["time_in_stage"]), 1)
                    else:
                        average_time_per_stage[stage] = 0

            highest_rejection_stage = max(rejection_rates.items(), key=lambda x: x[1], default=("N/A", 0))
            slowest_stage = max(average_time_per_stage.items(), key=lambda x: x[1], default=("N/A", 0))

            recommendations = []
            if highest_rejection_stage[1] > 50:
                recommendations.append(f"⚠️ Alta rejeição em '{highest_rejection_stage[0]}' ({highest_rejection_stage[1]}%). Revisar critérios de triagem ou perfil da vaga.")
            if slowest_stage[1] > 7:
                recommendations.append(f"⏰ Etapa '{slowest_stage[0]}' está lenta (média {slowest_stage[1]} dias). Considere acelerar agendamentos.")
            if stage_stats.get("Triagem", {}).get("count", 0) > 0 and stage_stats.get("Entrevista RH", {}).get("count", 0) == 0:
                recommendations.append("📋 Candidatos parados na Triagem. Avaliar e mover para próximas etapas.")
            if not recommendations:
                recommendations.append("✅ Pipeline fluindo normalmente. Continue monitorando.")

            return success_response(f"✅ Análise de gargalos para '{job.title}'", {
                "job_id": job_id,
                "job_title": job.title,
                "period": period,
                "total_candidates": len(vacancy_candidates),
                "stage_distribution": {s: stats["count"] for s, stats in stage_stats.items()},
                "rejection_rates": rejection_rates,
                "highest_rejection_stage": {"stage": highest_rejection_stage[0], "rate": highest_rejection_stage[1]},
                "average_time_per_stage": average_time_per_stage,
                "slowest_stage": {"stage": slowest_stage[0], "avg_days": slowest_stage[1]},
                "recommendations": recommendations
            })

    except Exception as e:
        logger.error(f"❌ Error analyzing bottlenecks: {e}", exc_info=True)
        return error_response(f"❌ Erro ao analisar gargalos: {str(e)}", e)
