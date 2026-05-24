"""Recruiter performance tools: recruiter metrics, velocity, efficiency, comparative."""
import logging
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

from ._base import analytics_db, error_response, extract_context, success_response
from app.tools.context_helpers import require_company_id_from_context

logger = logging.getLogger(__name__)


async def get_recruiter_metrics(
    recruiter_id: str | None = None,
    period: str = "month",
    compare_with_team: bool = False,
    **kwargs
) -> dict[str, Any]:
    """
    Get recruiter performance metrics.

    Args:
        recruiter_id: Recruiter ID (uses context user if not provided)
        period: Time period (week, month, quarter, year)
        compare_with_team: Include team comparison

    Returns:
        Recruiter metrics including jobs closed, time-to-fill, efficiency
    """
    company_id = require_company_id_from_context(kwargs, "get_recruiter_metrics")
    effective_recruiter = recruiter_id or (context.user_id if context else None)

    logger.info(f"📊 Getting recruiter metrics for {effective_recruiter} (company: {company_id})")

    try:
        from sqlalchemy import and_, select
        from app.models.candidate import VacancyCandidate
        from app.models.job_vacancy import JobVacancy

        period_days = {"week": 7, "month": 30, "quarter": 90, "year": 365}.get(period, 30)
        start_date = datetime.utcnow() - timedelta(days=period_days)

        async with analytics_db() as db:
            query = select(JobVacancy).where(
                and_(
                    JobVacancy.company_id == company_id,
                    JobVacancy.created_at >= start_date
                )
            )

            if effective_recruiter:
                query = query.where(JobVacancy.recruiter == effective_recruiter)

            result = await db.execute(query)
            jobs = result.scalars().all()

            total_jobs = len(jobs)
            closed_jobs = [j for j in jobs if j.status == "Fechada"]
            active_jobs = [j for j in jobs if j.status == "Ativa"]

            ttf_values = []
            for j in closed_jobs:
                if hasattr(j, 'closed_at') and j.closed_at and j.created_at:
                    ttf = (j.closed_at - j.created_at).days
                    ttf_values.append(ttf)

            avg_time_to_fill = sum(ttf_values) / len(ttf_values) if ttf_values else 0

            job_ids = [j.id for j in jobs]
            if job_ids:
                # TENANT-EXEMPT: job_ids derivado de query tenant-gated em L44-46 acima (JobVacancy.company_id == company_id); vc query .in_(job_ids) é defense-in-depth implícita
                vc_result = await db.execute(
                    select(VacancyCandidate).where(
                        VacancyCandidate.vacancy_id.in_(job_ids)
                    )
                )
                all_candidates = vc_result.scalars().all()
                total_candidates = len(all_candidates)
                hired = len([vc for vc in all_candidates if getattr(vc, 'stage', '') == 'Contratado'])
            else:
                total_candidates = 0
                hired = 0

            efficiency = (hired / total_candidates * 100) if total_candidates > 0 else 0

            metrics = {
                "recruiter_id": effective_recruiter,
                "period": period,
                "period_start": start_date.isoformat(),
                "jobs": {
                    "total": total_jobs,
                    "active": len(active_jobs),
                    "closed": len(closed_jobs),
                    "close_rate": f"{(len(closed_jobs) / total_jobs * 100):.1f}%" if total_jobs > 0 else "0%"
                },
                "velocity": {
                    "avg_time_to_fill_days": round(avg_time_to_fill, 1),
                    "fastest_close_days": min(ttf_values) if ttf_values else 0,
                    "slowest_close_days": max(ttf_values) if ttf_values else 0
                },
                "efficiency": {
                    "total_candidates_processed": total_candidates,
                    "total_hired": hired,
                    "conversion_rate": f"{efficiency:.1f}%",
                    "avg_candidates_per_hire": round(total_candidates / hired, 1) if hired > 0 else 0
                },
                "workload": {
                    "active_jobs": len(active_jobs),
                    "avg_candidates_per_job": round(total_candidates / total_jobs, 1) if total_jobs > 0 else 0
                }
            }

            return success_response(f"✅ Métricas do recrutador ({period})", metrics)

    except Exception as e:
        logger.error(f"❌ Error getting recruiter metrics: {e}", exc_info=True)
        return error_response(f"❌ Erro ao buscar métricas: {str(e)}", e)


async def get_velocity_metrics(
    period: str = "month",
    recruiter_id: str | None = None,
    sla_days: int = 30,
    **kwargs
) -> dict[str, Any]:
    """
    Get hiring velocity metrics for vacancies.

    Args:
        period: Time period (month, quarter, year)
        recruiter_id: Optional recruiter filter
        sla_days: SLA threshold in days (default 30)

    Returns:
        Velocity metrics including average_time_to_fill_days, sla_compliance_rate,
        jobs_within_sla, jobs_outside_sla
    """
    company_id = require_company_id_from_context(kwargs, "get_velocity_metrics")
    effective_recruiter = recruiter_id or (context.user_id if context else None)

    logger.info(f"⏱️ Getting velocity metrics (company: {company_id}, period: {period})")

    try:
        from sqlalchemy import and_, select
        from app.models.job_vacancy import JobVacancy

        period_days = {"month": 30, "quarter": 90, "year": 365}.get(period, 30)
        start_date = datetime.utcnow() - timedelta(days=period_days)

        async with analytics_db() as db:
            conditions = [
                JobVacancy.company_id == company_id,
                JobVacancy.status == "Fechada",
                JobVacancy.closed_at.isnot(None)
            ]

            if effective_recruiter:
                conditions.append(JobVacancy.recruiter == effective_recruiter)

            conditions.append(JobVacancy.closed_at >= start_date)

            # TENANT-EXEMPT: analytics tool builds conditions=[Model.company_id==X, ...] then where(and_(*conditions)); AST sensor cannot trace dynamic builder; T-RATCHET tenant_filter
            query = select(JobVacancy).where(and_(*conditions))
            result = await db.execute(query)
            closed_jobs = result.scalars().all()

            ttf_values = []
            jobs_within_sla = 0
            jobs_outside_sla = 0

            for job in closed_jobs:
                if job.created_at and job.closed_at:
                    ttf = (job.closed_at - job.created_at).days
                    ttf_values.append(ttf)

                    if ttf <= sla_days:
                        jobs_within_sla += 1
                    else:
                        jobs_outside_sla += 1

            total_jobs = len(ttf_values)
            avg_ttf = sum(ttf_values) / len(ttf_values) if ttf_values else 0
            min_ttf = min(ttf_values) if ttf_values else 0
            max_ttf = max(ttf_values) if ttf_values else 0
            sla_compliance = (jobs_within_sla / total_jobs * 100) if total_jobs > 0 else 0

            return success_response(f"✅ Métricas de velocidade de contratação ({period})", {
                "period": period,
                "sla_threshold_days": sla_days,
                "total_closed_jobs": total_jobs,
                "average_time_to_fill_days": round(avg_ttf, 1),
                "min_time_to_fill_days": min_ttf,
                "max_time_to_fill_days": max_ttf,
                "jobs_within_sla": jobs_within_sla,
                "jobs_outside_sla": jobs_outside_sla,
                "sla_compliance_rate": round(sla_compliance, 2),
                "recruiter_filter": effective_recruiter
            })

    except Exception as e:
        logger.error(f"❌ Error getting velocity metrics: {e}", exc_info=True)
        return error_response(f"❌ Erro ao buscar métricas de velocidade: {str(e)}", e)


async def get_efficiency_metrics(
    period: str = "month",
    job_id: str | None = None,
    **kwargs
) -> dict[str, Any]:
    """
    Get recruitment efficiency metrics.

    Args:
        period: Time period (month, quarter)
        job_id: Optional job filter

    Returns:
        Efficiency metrics including candidates_per_hire, interviews_per_hire,
        screening_to_offer_ratio
    """
    company_id = require_company_id_from_context(kwargs, "get_efficiency_metrics")

    logger.info(f"📈 Getting efficiency metrics (company: {company_id}, period: {period})")

    try:
        from sqlalchemy import and_, select
        from app.models.candidate import VacancyCandidate

        period_days = {"month": 30, "quarter": 90}.get(period, 30)
        start_date = datetime.utcnow() - timedelta(days=period_days)

        async with analytics_db() as db:
            conditions = [
                VacancyCandidate.company_id == company_id,
                VacancyCandidate.created_at >= start_date
            ]

            if job_id:
                conditions.append(VacancyCandidate.vacancy_id == UUID(job_id))

            # TENANT-EXEMPT: analytics tool builds conditions=[Model.company_id==X, ...] then where(and_(*conditions)); AST sensor cannot trace dynamic builder; T-RATCHET tenant_filter
            query = select(VacancyCandidate).where(and_(*conditions))
            result = await db.execute(query)
            vacancy_candidates = result.scalars().all()

            total_candidates = len(vacancy_candidates)

            screening_stages = {"Triagem", "Screening", "sourced", "initial"}
            interview_stages = {"Entrevista RH", "Entrevista Técnica", "Entrevista Final", "interview"}
            offer_stages = {"Oferta", "offer"}
            hired_stages = {"Contratado", "hired"}

            in_screening = 0
            in_interview = 0
            in_offer = 0
            hired = 0

            for vc in vacancy_candidates:
                stage = getattr(vc, 'stage', '') or ''
                status = getattr(vc, 'status', '') or ''

                if stage in screening_stages or status in screening_stages:
                    in_screening += 1
                if stage in interview_stages or status in interview_stages:
                    in_interview += 1
                if stage in offer_stages:
                    in_offer += 1
                if stage in hired_stages or status in hired_stages:
                    hired += 1

            candidates_per_hire = round(total_candidates / hired, 1) if hired > 0 else 0
            interviews_per_hire = round(in_interview / hired, 1) if hired > 0 else 0
            screening_to_offer = round(in_offer / in_screening * 100, 2) if in_screening > 0 else 0
            screening_to_interview = round(in_interview / in_screening * 100, 2) if in_screening > 0 else 0
            interview_to_offer = round(in_offer / in_interview * 100, 2) if in_interview > 0 else 0
            offer_to_hire = round(hired / in_offer * 100, 2) if in_offer > 0 else 0

            return success_response(f"✅ Métricas de eficiência de recrutamento ({period})", {
                "period": period,
                "job_filter": job_id,
                "total_candidates": total_candidates,
                "stage_breakdown": {
                    "in_screening": in_screening,
                    "in_interview": in_interview,
                    "in_offer": in_offer,
                    "hired": hired
                },
                "efficiency_metrics": {
                    "candidates_per_hire": candidates_per_hire,
                    "interviews_per_hire": interviews_per_hire,
                    "screening_to_offer_ratio": screening_to_offer,
                    "screening_to_interview_rate": screening_to_interview,
                    "interview_to_offer_rate": interview_to_offer,
                    "offer_to_hire_rate": offer_to_hire
                }
            })

    except Exception as e:
        logger.error(f"❌ Error getting efficiency metrics: {e}", exc_info=True)
        return error_response(f"❌ Erro ao buscar métricas de eficiência: {str(e)}", e)


async def get_comparative_metrics(
    recruiter_id: str | None = None,
    comparison_type: str = "team",
    period: str = "month",
    **kwargs
) -> dict[str, Any]:
    """
    Get comparative metrics for recruiter performance.

    Args:
        recruiter_id: Recruiter to analyze (uses context if not provided)
        comparison_type: Type of comparison (team or previous_period)
        period: Time period (week, month, quarter)

    Returns:
        Comparative metrics including my_metrics, comparison_metrics, difference_percentage
    """
    company_id = require_company_id_from_context(kwargs, "get_comparative_metrics")
    effective_recruiter = recruiter_id or (context.user_id if context else None)

    logger.info(f"📊 Getting comparative metrics (company: {company_id}, type: {comparison_type})")

    try:
        from sqlalchemy import and_, distinct, select
        from app.models.candidate import VacancyCandidate
        from app.models.job_vacancy import JobVacancy

        period_days = {"week": 7, "month": 30, "quarter": 90}.get(period, 30)
        start_date = datetime.utcnow() - timedelta(days=period_days)
        previous_start = start_date - timedelta(days=period_days)

        async with analytics_db() as db:
            async def get_recruiter_stats(recruiter: str | None, from_date: datetime, to_date: datetime):
                conditions = [
                    JobVacancy.company_id == company_id,
                    JobVacancy.created_at >= from_date,
                    JobVacancy.created_at < to_date
                ]
                if recruiter:
                    conditions.append(JobVacancy.recruiter == recruiter)

                # TENANT-EXEMPT: analytics tool builds conditions=[Model.company_id==X, ...] then where(and_(*conditions)); AST sensor cannot trace dynamic builder; T-RATCHET tenant_filter
                jobs_query = select(JobVacancy).where(and_(*conditions))
                result = await db.execute(jobs_query)
                jobs = result.scalars().all()

                total_jobs = len(jobs)
                closed_jobs = [j for j in jobs if j.status == "Fechada"]

                ttf_values = []
                for j in closed_jobs:
                    if j.created_at and getattr(j, 'closed_at', None):
                        ttf_values.append((j.closed_at - j.created_at).days)

                job_ids = [j.id for j in jobs]
                total_candidates = 0
                hired = 0

                if job_ids:
                    vc_result = await db.execute(
                        select(VacancyCandidate).where(
                            and_(
                                VacancyCandidate.vacancy_id.in_(job_ids),
                                VacancyCandidate.company_id == company_id
                            )
                        )
                    )
                    candidates = vc_result.scalars().all()
                    total_candidates = len(candidates)
                    hired = sum(1 for c in candidates if getattr(c, 'stage', '') == 'Contratado')

                return {
                    "jobs_created": total_jobs,
                    "jobs_closed": len(closed_jobs),
                    "avg_time_to_fill": round(sum(ttf_values) / len(ttf_values), 1) if ttf_values else 0,
                    "total_candidates": total_candidates,
                    "hires": hired,
                    "close_rate": round(len(closed_jobs) / total_jobs * 100, 2) if total_jobs > 0 else 0,
                    "conversion_rate": round(hired / total_candidates * 100, 2) if total_candidates > 0 else 0
                }

            my_metrics = await get_recruiter_stats(effective_recruiter, start_date, datetime.utcnow())

            if comparison_type == "team":
                team_metrics = await get_recruiter_stats(None, start_date, datetime.utcnow())

                all_recruiters_result = await db.execute(
                    select(distinct(JobVacancy.recruiter)).where(
                        and_(
                            JobVacancy.company_id == company_id,
                            JobVacancy.created_at >= start_date,
                            JobVacancy.recruiter.isnot(None)
                        )
                    )
                )
                recruiter_count = len(all_recruiters_result.scalars().all())
                recruiter_count = max(recruiter_count, 1)

                team_avg = {
                    key: round(val / recruiter_count, 2) if isinstance(val, (int, float)) else val
                    for key, val in team_metrics.items()
                }
                comparison_metrics = team_avg
                comparison_label = "team_average"
            else:
                comparison_metrics = await get_recruiter_stats(effective_recruiter, previous_start, start_date)
                comparison_label = "previous_period"

            differences = {}
            for key in my_metrics:
                my_val = my_metrics[key]
                comp_val = comparison_metrics.get(key, 0)
                if isinstance(my_val, (int, float)) and isinstance(comp_val, (int, float)) and comp_val != 0:
                    diff_pct = round((my_val - comp_val) / comp_val * 100, 2)
                    differences[key] = {
                        "my_value": my_val,
                        "comparison_value": comp_val,
                        "difference_percentage": diff_pct,
                        "trend": "up" if diff_pct > 0 else "down" if diff_pct < 0 else "stable"
                    }

            return success_response(f"✅ Métricas comparativas ({comparison_type})", {
                "period": period,
                "comparison_type": comparison_type,
                "recruiter_id": effective_recruiter,
                "my_metrics": my_metrics,
                "comparison_label": comparison_label,
                "comparison_metrics": comparison_metrics,
                "differences": differences
            })

    except Exception as e:
        logger.error(f"❌ Error getting comparative metrics: {e}", exc_info=True)
        return error_response(f"❌ Erro ao buscar métricas comparativas: {str(e)}", e)
