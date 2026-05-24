"""Pipeline analytics tools: pipeline stats, vacancy funnel, candidate comparison."""
import logging
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

from ._base import analytics_db, error_response, extract_context, success_response
from app.tools.context_helpers import require_company_id_from_context

logger = logging.getLogger(__name__)


async def get_pipeline_stats(
    period: str | None = "month",
    recruiter_id: str | None = None,
    department: str | None = None,
    **kwargs
) -> dict[str, Any]:
    """
    Get pipeline statistics and metrics.

    Args:
        period: Time period (week, month, quarter, year)
        recruiter_id: Filter by recruiter
        department: Filter by department

    Returns:
        Pipeline statistics including conversion rates, volume metrics
    """
    company_id = require_company_id_from_context(kwargs, "get_pipeline_stats")
    effective_recruiter = recruiter_id or (context.user_id if context else None)

    logger.info(f"📊 Getting pipeline stats (company: {company_id}, period: {period})")

    try:
        from sqlalchemy import and_, select
        from app.models.candidate import VacancyCandidate
        from app.models.job_vacancy import JobVacancy

        period_days = {
            "week": 7,
            "month": 30,
            "quarter": 90,
            "year": 365
        }.get(period, 30)

        start_date = datetime.utcnow() - timedelta(days=period_days)

        async with analytics_db() as db:
            jobs_query = select(JobVacancy).where(
                and_(
                    JobVacancy.company_id == company_id,
                    JobVacancy.created_at >= start_date
                )
            )

            if effective_recruiter:
                jobs_query = jobs_query.where(JobVacancy.recruiter == effective_recruiter)

            if department:
                jobs_query = jobs_query.where(JobVacancy.department == department)

            result = await db.execute(jobs_query)
            jobs = result.scalars().all()

            total_jobs = len(jobs)
            jobs_by_status = {}
            for j in jobs:
                status = j.status or 'Indefinido'
                jobs_by_status[status] = jobs_by_status.get(status, 0) + 1

            closed_jobs = sum(1 for j in jobs if j.status == 'Fechada')
            active_jobs = sum(1 for j in jobs if j.status == 'Ativa')

            job_ids = [j.id for j in jobs]
            if job_ids:
                vc_result = await db.execute(
                    select(VacancyCandidate).where(
                        and_(
                            VacancyCandidate.vacancy_id.in_(job_ids),
                            VacancyCandidate.company_id == company_id
                        )
                    )
                )
                vacancy_candidates = vc_result.scalars().all()

                total_candidates = len(vacancy_candidates)
                candidates_by_stage = {}
                for vc in vacancy_candidates:
                    stage = getattr(vc, 'stage', 'Indefinido') or 'Indefinido'
                    candidates_by_stage[stage] = candidates_by_stage.get(stage, 0) + 1
            else:
                total_candidates = 0
                candidates_by_stage = {}

            avg_candidates_per_job = total_candidates / total_jobs if total_jobs > 0 else 0

            stats = {
                "period": period,
                "period_start": start_date.isoformat(),
                "jobs": {
                    "total": total_jobs,
                    "by_status": jobs_by_status,
                    "active": active_jobs,
                    "closed": closed_jobs,
                    "close_rate": f"{(closed_jobs / total_jobs * 100):.1f}%" if total_jobs > 0 else "0%"
                },
                "candidates": {
                    "total": total_candidates,
                    "by_stage": candidates_by_stage,
                    "avg_per_job": round(avg_candidates_per_job, 1)
                },
                "filters": {
                    "recruiter_id": effective_recruiter,
                    "department": department
                }
            }

            return success_response(f"✅ Estatísticas do pipeline ({period})", stats)

    except Exception as e:
        logger.error(f"❌ Error getting pipeline stats: {e}", exc_info=True)
        return error_response(f"❌ Erro ao buscar estatísticas: {str(e)}", e)


async def get_vacancy_funnel(
    job_id: str,
    include_stalled: bool = True,
    stalled_days: int = 7,
    **kwargs
) -> dict[str, Any]:
    """
    Get funnel metrics for a specific vacancy.

    Args:
        job_id: UUID of the job vacancy
        include_stalled: Include candidates stalled at each stage
        stalled_days: Number of days to consider as stalled (default 7)

    Returns:
        Funnel metrics with conversion rates and stalled candidates
    """
    company_id = require_company_id_from_context(kwargs, "get_vacancy_funnel")

    logger.info(f"📊 Getting vacancy funnel: {job_id} (company: {company_id})")

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

            stages = [
                "Triagem", "Entrevista RH", "Entrevista Técnica",
                "Entrevista Final", "Oferta", "Contratado", "Reprovado"
            ]

            funnel = {stage: {"count": 0, "candidates": [], "stalled": []} for stage in stages}
            funnel["Outros"] = {"count": 0, "candidates": [], "stalled": []}

            stalled_threshold = datetime.utcnow() - timedelta(days=stalled_days)

            for vc, c in vacancy_candidates:
                stage = getattr(vc, 'stage', 'Outros') or 'Outros'
                if stage not in funnel:
                    stage = 'Outros'

                candidate_info = {
                    "id": str(c.id),
                    "name": getattr(c, 'name', 'N/A'),
                    "lia_score": getattr(c, 'lia_score', None),
                }

                funnel[stage]["count"] += 1
                funnel[stage]["candidates"].append(candidate_info)

                updated_at = getattr(vc, 'updated_at', None)
                if include_stalled and updated_at and updated_at < stalled_threshold:
                    days_stalled = (datetime.utcnow() - updated_at).days
                    funnel[stage]["stalled"].append({**candidate_info, "days_stalled": days_stalled})

            total = sum(f["count"] for f in funnel.values())
            funnel_summary = []

            for i, stage in enumerate(stages):
                stage_data = funnel[stage]
                prev_count = funnel[stages[i-1]]["count"] if i > 0 else total
                conversion = (stage_data["count"] / prev_count * 100) if prev_count > 0 else 0

                funnel_summary.append({
                    "stage": stage,
                    "count": stage_data["count"],
                    "stalled_count": len(stage_data["stalled"]),
                    "conversion_from_previous": f"{conversion:.1f}%"
                })

            return success_response(f"✅ Funil da vaga: {job.title}", {
                "job_id": job_id,
                "job_title": job.title,
                "total_candidates": total,
                "funnel_summary": funnel_summary,
                "funnel_detail": funnel,
                "stalled_total": sum(len(f["stalled"]) for f in funnel.values())
            })

    except Exception as e:
        logger.error(f"❌ Error getting vacancy funnel: {e}", exc_info=True)
        return error_response(f"❌ Erro ao buscar funil da vaga: {str(e)}", e)


async def compare_candidates(
    candidate_ids: list[str],
    job_id: str | None = None,
    **kwargs
) -> dict[str, Any]:
    """
    Compare multiple candidates side by side.

    Args:
        candidate_ids: List of candidate UUIDs to compare
        job_id: Optional job ID for context-specific comparison

    Returns:
        Side-by-side comparison of candidates
    """
    company_id = require_company_id_from_context(kwargs, "compare_candidates")

    logger.info(f"🔄 Comparing {len(candidate_ids)} candidates (company: {company_id})")

    try:
        from sqlalchemy import and_, select
        from app.models.candidate import Candidate

        async with analytics_db() as db:
            candidates_data = []

            for cid in candidate_ids[:5]:
                result = await db.execute(
                    select(Candidate).where(
                        and_(
                            Candidate.id == UUID(cid),
                            Candidate.company_id == company_id
                        )
                    )
                )
                candidate = result.scalar_one_or_none()

                if candidate:
                    candidates_data.append({
                        "id": str(candidate.id),
                        "name": getattr(candidate, 'name', 'N/A'),
                        "seniority": getattr(candidate, 'seniority_level', None),
                        "years_experience": getattr(candidate, 'years_experience', None),
                        "location": getattr(candidate, 'location', None),
                        "lia_score": getattr(candidate, 'lia_score', None),
                        "wsi_score": getattr(candidate, 'wsi_score', None),
                        "fit_score": getattr(candidate, 'fit_score', None),
                        "skills": getattr(candidate, 'skills', []) or [],
                        "languages": getattr(candidate, 'languages', []) or [],
                        "salary_expectation": getattr(candidate, 'salary_expectation', None),
                        "available_immediately": getattr(candidate, 'available_immediately', None),
                    })

            if not candidates_data:
                return {
                    "success": False,
                    "message": "Nenhum candidato encontrado para comparação",
                    "error": "no_candidates_found"
                }

            comparison = {
                "candidates": candidates_data,
                "comparison_metrics": {
                    "highest_lia_score": max((c["lia_score"] or 0) for c in candidates_data),
                    "avg_experience": sum((c["years_experience"] or 0) for c in candidates_data) / len(candidates_data),
                    "available_count": sum(1 for c in candidates_data if c["available_immediately"]),
                },
                "ranking": sorted(
                    candidates_data,
                    key=lambda x: (x.get("lia_score") or 0),
                    reverse=True
                )
            }

            return success_response(f"✅ Comparação de {len(candidates_data)} candidatos", comparison)

    except Exception as e:
        logger.error(f"❌ Error comparing candidates: {e}", exc_info=True)
        return error_response(f"❌ Erro ao comparar candidatos: {str(e)}", e)
