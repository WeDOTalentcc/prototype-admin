"""
Route service facade for job vacancy management.
Encapsulates business logic from API routes (app/api/v1/job_vacancies.py) for portability.
"""
import logging
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.candidate import VacancyCandidate
from app.models.job_vacancy import JobVacancy
from app.models.recruitment_stages import CandidateStageHistory

logger = logging.getLogger(__name__)


def _calculate_days_between(start_date: datetime | None, end_date: datetime | None) -> int:
    if not start_date or not end_date:
        return 0
    delta = end_date - start_date
    return max(0, delta.days)


def _is_job_at_risk(job: Any, now: datetime) -> bool:
    funnel = job.funnel_data or {}
    total_candidates = funnel.get("total", 0) or 0
    has_empty_pipeline = total_candidates == 0

    days_since_update = 0
    if job.updated_at:
        days_since_update = (now - job.updated_at).days
    is_stalled = days_since_update > 15

    days_to_deadline = float('inf')
    if job.deadline:
        days_to_deadline = (job.deadline - now).days
    deadline_soon = 0 <= days_to_deadline < 10

    return has_empty_pipeline or is_stalled or deadline_soon


def _generate_insights(
    my_jobs_list: list[Any],
    active_jobs_list: list[Any],
    completed_jobs_90d: list[Any],
    stats: dict[str, Any],
    now: datetime
) -> list[dict[str, Any]]:
    insights: list[dict[str, Any]] = []

    stalled_jobs = [
        job for job in active_jobs_list
        if job.updated_at and (now - job.updated_at).days > 15
    ]
    if stalled_jobs:
        job_titles = [j.title for j in stalled_jobs[:3]]
        titles_str = ", ".join(job_titles)
        if len(stalled_jobs) > 3:
            titles_str += f" e mais {len(stalled_jobs) - 3}"
        insights.append({
            "type": "alert",
            "message": f"{len(stalled_jobs)} vaga(s) parada(s) há mais de 15 dias: {titles_str}",
            "severity": "warning" if len(stalled_jobs) < 3 else "critical"
        })

    empty_pipeline_jobs = [
        job for job in active_jobs_list
        if (job.funnel_data or {}).get("total", 0) == 0 or job.funnel_data is None
    ]
    if empty_pipeline_jobs:
        job_titles = [j.title for j in empty_pipeline_jobs[:3]]
        titles_str = ", ".join(job_titles)
        if len(empty_pipeline_jobs) > 3:
            titles_str += f" e mais {len(empty_pipeline_jobs) - 3}"
        insights.append({
            "type": "alert",
            "message": f"{len(empty_pipeline_jobs)} vaga(s) sem candidatos no pipeline: {titles_str}",
            "severity": "critical" if len(empty_pipeline_jobs) > 2 else "warning"
        })

    deadline_soon_jobs = []
    for job in active_jobs_list:
        if job.deadline:
            days_to_deadline = (job.deadline - now).days
            if 0 <= days_to_deadline < 10:
                deadline_soon_jobs.append((job, days_to_deadline))
    if deadline_soon_jobs:
        details = [f"{j.title} ({d}d)" for j, d in deadline_soon_jobs[:3]]
        details_str = ", ".join(details)
        insights.append({
            "type": "alert",
            "message": f"{len(deadline_soon_jobs)} vaga(s) com deadline próximo: {details_str}",
            "severity": "warning"
        })

    if stats.get("conversion_rate", 0) < 10 and len(my_jobs_list) >= 3:
        insights.append({
            "type": "suggestion",
            "message": "Taxa de conversão abaixo de 10%. Considere revisar os critérios de triagem ou a descrição das vagas.",
            "action": "review_screening_criteria"
        })

    ttf_avg = stats.get("time_to_fill_avg_90d", 0)
    if ttf_avg > 45:
        insights.append({
            "type": "suggestion",
            "message": f"Tempo médio de preenchimento está em {ttf_avg:.0f} dias. Considere estratégias de sourcing mais ativas.",
            "action": "improve_sourcing"
        })

    high_priority_count = sum(1 for j in active_jobs_list if j.priority == "alta")
    if high_priority_count >= 5:
        insights.append({
            "type": "alert",
            "message": f"{high_priority_count} vagas com prioridade alta abertas. Considere priorizar recursos.",
            "severity": "warning"
        })

    success_rate = stats.get("success_rate", 0)
    if success_rate > 80 and len(completed_jobs_90d) >= 5:
        insights.append({
            "type": "suggestion",
            "message": f"Excelente taxa de sucesso de {success_rate:.0f}%! Continue monitorando para manter o padrão.",
            "action": "maintain_standards"
        })

    return insights


class JobVacancyRouteService:
    """Encapsulates business logic from job vacancy API routes."""

    async def get_job_vacancy_metrics(
        self, db: AsyncSession, job_vacancy_id: UUID, company_id: UUID
    ) -> dict[str, Any]:
        """Calculate comprehensive job vacancy metrics.

        Extracted from GET /job-vacancies/{job_vacancy_id}/metrics (lines 682-839).

        Returns:
            Dict with keys: job_id, funnel, performance, activity, sla
        """
        result = await db.execute(
            select(JobVacancy).where(
                and_(
                    JobVacancy.id == job_vacancy_id,
                    JobVacancy.company_id == company_id
                )
            )
        )
        job = result.scalar_one_or_none()
        if not job:
            return None

        stage_counts_result = await db.execute(
            select(
                VacancyCandidate.stage,
                func.count(VacancyCandidate.id).label("count")
            )
            .where(VacancyCandidate.vacancy_id == job_vacancy_id)
            .group_by(VacancyCandidate.stage)
        )
        stage_counts = {row.stage: row.count for row in stage_counts_result.all()}

        total_count_result = await db.execute(
            select(func.count(VacancyCandidate.id))
            .where(VacancyCandidate.vacancy_id == job_vacancy_id)
        )
        total_candidates = total_count_result.scalar() or 0

        source_counts_result = await db.execute(
            select(
                VacancyCandidate.source,
                func.count(VacancyCandidate.id).label("count")
            )
            .where(VacancyCandidate.vacancy_id == job_vacancy_id)
            .group_by(VacancyCandidate.source)
        )
        source_breakdown = {row.source: row.count for row in source_counts_result.all()}

        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        applications_7d_result = await db.execute(
            select(func.count(VacancyCandidate.id))
            .where(
                and_(
                    VacancyCandidate.vacancy_id == job_vacancy_id,
                    VacancyCandidate.created_at >= seven_days_ago
                )
            )
        )
        applications_7d = applications_7d_result.scalar() or 0

        last_activity_result = await db.execute(
            select(func.max(VacancyCandidate.updated_at))
            .where(VacancyCandidate.vacancy_id == job_vacancy_id)
        )
        last_activity = last_activity_result.scalar()

        fallback_funnel = job.funnel_data or {}

        screening_count = stage_counts.get("screening", 0) + stage_counts.get("triagem", 0) + stage_counts.get("initial", 0)
        interview_count = stage_counts.get("interview", 0) + stage_counts.get("entrevista", 0)
        offer_count = stage_counts.get("offer", 0) + stage_counts.get("proposta", 0)
        hired_count = stage_counts.get("hired", 0) + stage_counts.get("contratado", 0)
        rejected_count = stage_counts.get("rejected", 0) + stage_counts.get("reprovado", 0) + stage_counts.get("recusado", 0)

        funnel = {
            "total": total_candidates if total_candidates > 0 else fallback_funnel.get("total", 0),
            "screening": screening_count if screening_count > 0 else fallback_funnel.get("screening", 0),
            "interview": interview_count if interview_count > 0 else fallback_funnel.get("interview", 0),
            "offer": offer_count if offer_count > 0 else fallback_funnel.get("offer", 0),
            "hired": hired_count if hired_count > 0 else fallback_funnel.get("hired", 0),
            "rejected": rejected_count if rejected_count > 0 else fallback_funnel.get("rejected", 0),
        }

        time_to_fill_days = None
        if job.closed_at and job.open_date:
            time_to_fill_days = (job.closed_at - job.open_date).days
        elif job.closed_at and job.created_at:
            time_to_fill_days = (job.closed_at - job.created_at).days

        avg_time_in_stage = None
        if total_candidates > 0 and job.created_at:
            days_open = (datetime.utcnow() - job.created_at).days or 1
            stages_passed = sum([1 for v in [screening_count, interview_count, offer_count, hired_count] if v > 0])
            if stages_passed > 0:
                avg_time_in_stage = round(days_open / (stages_passed * max(total_candidates, 1)), 1)

        conversion_rate = 0.0
        if funnel["total"] > 0:
            conversion_rate = round(funnel["hired"] / funnel["total"], 3)

        views_7d = job.additional_data.get("views_7d", 0) if job.additional_data else 0

        within_sla = True
        days_remaining = None
        deadline_str = None
        if job.deadline:
            deadline_str = job.deadline.strftime("%Y-%m-%d")
            days_remaining = (job.deadline - datetime.utcnow()).days
            within_sla = days_remaining >= 0

        return {
            "job_id": str(job_vacancy_id),
            "funnel": funnel,
            "performance": {
                "time_to_fill_days": time_to_fill_days,
                "avg_time_in_stage_days": avg_time_in_stage,
                "conversion_rate": conversion_rate,
                "source_breakdown": source_breakdown,
            },
            "activity": {
                "views_7d": views_7d,
                "applications_7d": applications_7d,
                "interviews_scheduled": interview_count,
                "last_activity": last_activity.isoformat() if last_activity else None,
            },
            "sla": {
                "within_sla": within_sla,
                "days_remaining": days_remaining,
                "deadline": deadline_str,
            },
        }

    async def get_job_analytics(
        self, db: AsyncSession, job_id: UUID, company_id: UUID
    ) -> dict[str, Any] | None:
        """Calculate detailed analytics for a job vacancy.

        Extracted from GET /job-vacancies/{job_id}/analytics (lines 896-1157).
        Includes funnel analysis, time-based metrics, source analysis,
        performance trends, and company benchmarks.

        Returns:
            Dict with comprehensive analytics or None if vacancy not found.
        """
        result = await db.execute(
            select(JobVacancy).where(
                and_(JobVacancy.id == job_id, JobVacancy.company_id == company_id)
            )
        )
        job = result.scalar_one_or_none()
        if not job:
            return None

        candidates_result = await db.execute(
            select(VacancyCandidate).where(VacancyCandidate.vacancy_id == job_id)
        )
        vacancy_candidates = candidates_result.scalars().all()
        total_candidates = len(vacancy_candidates)

        stage_counts: dict[str, int] = {}
        source_counts: dict[str, int] = {}
        source_hired_counts: dict[str, int] = {}
        hired_count = 0
        lia_scores: list[float] = []
        match_percentages: list[float] = []

        for vc in vacancy_candidates:
            stage = vc.stage or "initial"
            source = vc.source or "unknown"
            stage_counts[stage] = stage_counts.get(stage, 0) + 1
            source_counts[source] = source_counts.get(source, 0) + 1

            if stage in ["hired", "contratado"]:
                hired_count += 1
                source_hired_counts[source] = source_hired_counts.get(source, 0) + 1

            if vc.lia_score is not None:
                lia_scores.append(vc.lia_score)
            if vc.match_percentage is not None:
                match_percentages.append(vc.match_percentage)

        stage_order = [
            "sourcing", "initial", "screening", "triagem",
            "interview", "entrevista", "offer", "proposta",
            "hired", "contratado", "rejected", "reprovado",
        ]
        funnel_items: list[dict[str, Any]] = []
        cumulative_count = total_candidates

        for stage_name in stage_order:
            if stage_name in stage_counts:
                count = stage_counts[stage_name]
                conversion_rate = (count / cumulative_count * 100) if cumulative_count > 0 else 0.0
                funnel_items.append({
                    "stage": stage_name,
                    "count": count,
                    "conversion_rate": round(conversion_rate, 1),
                    "avg_days": 0.0,
                })

        for stage_name, count in stage_counts.items():
            if stage_name not in stage_order:
                conversion_rate = (count / total_candidates * 100) if total_candidates > 0 else 0.0
                funnel_items.append({
                    "stage": stage_name,
                    "count": count,
                    "conversion_rate": round(conversion_rate, 1),
                    "avg_days": 0.0,
                })

        history_result = await db.execute(
            select(CandidateStageHistory)
            .where(CandidateStageHistory.vacancy_id == job_id)
            .order_by(CandidateStageHistory.created_at.asc())
        )
        stage_history = history_result.scalars().all()

        time_in_stage: dict[str, list[float]] = {}
        rejection_reasons: list[str] = []
        first_response_times: list[float] = []
        hire_times: list[float] = []

        for history_entry in stage_history:
            if history_entry.time_in_previous_stage_hours is not None and history_entry.from_stage_name:
                sn = history_entry.from_stage_name
                days = history_entry.time_in_previous_stage_hours / 24.0
                if sn not in time_in_stage:
                    time_in_stage[sn] = []
                time_in_stage[sn].append(days)

            if history_entry.to_stage_name in ["rejected", "reprovado"] and history_entry.reason:
                rejection_reasons.append(history_entry.reason)

            if (
                history_entry.from_stage_name in ["sourcing", "initial", None]
                and history_entry.to_stage_name not in ["sourcing", "initial"]
            ):
                if history_entry.time_in_previous_stage_hours is not None:
                    first_response_times.append(history_entry.time_in_previous_stage_hours / 24.0)

            if history_entry.to_stage_name in ["hired", "contratado"]:
                candidate_history = [
                    h for h in stage_history if h.candidate_id == history_entry.candidate_id
                ]
                total_time = sum(h.time_in_previous_stage_hours or 0 for h in candidate_history)
                hire_times.append(total_time / 24.0)

        avg_time_in_stage: dict[str, float] = {}
        for sn, times in time_in_stage.items():
            avg_time_in_stage[sn] = round(sum(times) / len(times), 1) if times else 0.0

        for fi in funnel_items:
            if fi["stage"] in avg_time_in_stage:
                fi["avg_days"] = avg_time_in_stage[fi["stage"]]

        avg_time_to_hire = round(sum(hire_times) / len(hire_times), 1) if hire_times else 0.0
        avg_time_to_first_response = round(sum(first_response_times) / len(first_response_times), 1) if first_response_times else 0.0

        sources_list: list[dict[str, Any]] = []
        for source, count in sorted(source_counts.items(), key=lambda x: x[1], reverse=True):
            hired_from_source = source_hired_counts.get(source, 0)
            conversion = (hired_from_source / count * 100) if count > 0 else 0.0
            sources_list.append({
                "source": source,
                "count": count,
                "conversion_rate": round(conversion, 1),
            })
        top_source = sources_list[0]["source"] if sources_list else "unknown"

        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        daily_apps_result = await db.execute(
            select(
                func.date(VacancyCandidate.created_at).label("date"),
                func.count(VacancyCandidate.id).label("count"),
            )
            .where(
                and_(
                    VacancyCandidate.vacancy_id == job_id,
                    VacancyCandidate.created_at >= thirty_days_ago,
                )
            )
            .group_by(func.date(VacancyCandidate.created_at))
            .order_by(func.date(VacancyCandidate.created_at))
        )
        daily_apps_rows = daily_apps_result.all()
        daily_applications = [{"date": str(row.date), "count": row.count} for row in daily_apps_rows]

        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        fourteen_days_ago = datetime.utcnow() - timedelta(days=14)

        this_week_result = await db.execute(
            select(func.count(VacancyCandidate.id))
            .where(and_(VacancyCandidate.vacancy_id == job_id, VacancyCandidate.created_at >= seven_days_ago))
        )
        this_week_count = this_week_result.scalar() or 0

        last_week_result = await db.execute(
            select(func.count(VacancyCandidate.id))
            .where(
                and_(
                    VacancyCandidate.vacancy_id == job_id,
                    VacancyCandidate.created_at >= fourteen_days_ago,
                    VacancyCandidate.created_at < seven_days_ago,
                )
            )
        )
        last_week_count = last_week_result.scalar() or 0

        weekly_trend = 0.0
        if last_week_count > 0:
            weekly_trend = round(((this_week_count - last_week_count) / last_week_count) * 100, 1)
        elif this_week_count > 0:
            weekly_trend = 100.0

        avg_lia_score = round(sum(lia_scores) / len(lia_scores), 1) if lia_scores else 0.0
        avg_skills_match = round(sum(match_percentages) / len(match_percentages), 1) if match_percentages else 0.0

        reason_counts: dict[str, int] = {}
        for reason in rejection_reasons:
            reason_counts[reason] = reason_counts.get(reason, 0) + 1
        top_rejection_reasons = sorted(reason_counts.keys(), key=lambda x: reason_counts[x], reverse=True)[:5]

        company_jobs_result = await db.execute(
            select(JobVacancy).where(
                and_(
                    JobVacancy.company_id == company_id,
                    JobVacancy.status.in_(["Concluída", "Encerrada"]),
                )
            )
        )
        company_jobs = company_jobs_result.scalars().all()

        company_hire_times: list[float] = []
        company_conversion_rates: list[float] = []
        for cj in company_jobs:
            if cj.open_date and cj.closed_at:
                company_hire_times.append((cj.closed_at - cj.open_date).days)
            if cj.funnel_data:
                total = cj.funnel_data.get("total", 0)
                hired = cj.funnel_data.get("hired", 0)
                if total > 0:
                    company_conversion_rates.append((hired / total) * 100)

        company_avg_time_to_hire = round(sum(company_hire_times) / len(company_hire_times), 1) if company_hire_times else 0.0
        company_avg_conversion_rate = round(sum(company_conversion_rates) / len(company_conversion_rates), 1) if company_conversion_rates else 0.0

        overall_conversion_rate = (hired_count / total_candidates * 100) if total_candidates > 0 else 0.0

        position_percentile = 50
        if company_conversion_rates and overall_conversion_rate > 0:
            better_than = sum(1 for r in company_conversion_rates if overall_conversion_rate > r)
            position_percentile = int((better_than / len(company_conversion_rates)) * 100)

        return {
            "vacancy_id": str(job_id),
            "vacancy_title": job.title,
            "funnel": funnel_items,
            "total_candidates": total_candidates,
            "total_hired": hired_count,
            "overall_conversion_rate": round(overall_conversion_rate, 1),
            "avg_time_to_hire": avg_time_to_hire,
            "avg_time_to_first_response": avg_time_to_first_response,
            "time_in_stage": avg_time_in_stage,
            "sources": sources_list,
            "top_source": top_source,
            "daily_applications": daily_applications,
            "weekly_trend": weekly_trend,
            "avg_lia_score": avg_lia_score,
            "avg_skills_match": avg_skills_match,
            "top_rejection_reasons": top_rejection_reasons,
            "company_avg_time_to_hire": company_avg_time_to_hire,
            "company_avg_conversion_rate": company_avg_conversion_rate,
            "position_percentile": position_percentile,
        }

    async def get_stats_overview(
        self, db: AsyncSession, company_id: UUID, recruiter_email: str | None = None
    ) -> dict[str, Any]:
        """Calculate aggregated dashboard metrics for job vacancies.

        Extracted from GET /job-vacancies/stats/overview (lines 1533-1759).
        Includes my_jobs, active_jobs, all_jobs (90d), and insights.

        Args:
            db: Async database session.
            company_id: Company UUID for multi-tenant isolation.
            recruiter_email: Optional filter for "My Jobs" section.

        Returns:
            Dict with keys: my_jobs, active_jobs, all_jobs, insights
        """
        now = datetime.utcnow()

        result = await db.execute(
            select(JobVacancy).where(JobVacancy.company_id == company_id)
        )
        all_company_jobs = result.scalars().all()

        my_jobs_list = []
        if recruiter_email:
            my_jobs_list = [
                j for j in all_company_jobs
                if j.recruiter_email and j.recruiter_email.lower() == recruiter_email.lower()
            ]

        active_jobs_list = [j for j in all_company_jobs if j.status == "Ativa"]
        completed_jobs = [j for j in all_company_jobs if j.status == "Concluída"]

        date_90d_ago = now - timedelta(days=90)
        date_30d_ago = now - timedelta(days=30)
        date_7d_ago = now - timedelta(days=7)

        completed_jobs_90d = [j for j in completed_jobs if j.closed_at and j.closed_at >= date_90d_ago]
        completed_jobs_30d = [j for j in completed_jobs if j.closed_at and j.closed_at >= date_30d_ago]

        my_active = len([j for j in my_jobs_list if j.status == "Ativa"])
        my_completed = len([j for j in my_jobs_list if j.status == "Concluída"])

        my_completed_jobs = [j for j in my_jobs_list if j.status == "Concluída" and j.open_date and j.closed_at]
        my_time_to_fill_avg = 0.0
        if my_completed_jobs:
            total_ttf = sum(_calculate_days_between(j.open_date, j.closed_at) for j in my_completed_jobs)
            my_time_to_fill_avg = total_ttf / len(my_completed_jobs)

        my_candidates_interviewed = 0
        my_candidates_in_funnel = 0
        my_offers_sent = 0
        for job in my_jobs_list:
            funnel = job.funnel_data or {}
            my_candidates_in_funnel += funnel.get("total", 0) or 0
            my_candidates_interviewed += funnel.get("interview", 0) or funnel.get("entrevista", 0) or 0
            my_offers_sent += funnel.get("offer", 0) or funnel.get("proposta", 0) or 0

        my_conversion_rate = 0.0
        if my_candidates_in_funnel > 0:
            hired_count = sum(
                (j.funnel_data or {}).get("hired", 0) or (j.funnel_data or {}).get("contratado", 0) or 0
                for j in my_jobs_list
            )
            my_conversion_rate = (hired_count / my_candidates_in_funnel) * 100

        my_interviews_last_7d = 0
        for job in my_jobs_list:
            if job.updated_at and job.updated_at >= date_7d_ago:
                funnel = job.funnel_data or {}
                my_interviews_last_7d += funnel.get("interview", 0) or funnel.get("entrevista", 0) or 0

        my_jobs_stats = {
            "active": my_active,
            "completed": my_completed,
            "time_to_fill_avg": round(my_time_to_fill_avg, 1),
            "candidates_interviewed": my_candidates_interviewed,
            "conversion_rate": round(my_conversion_rate, 1),
            "candidates_in_funnel": my_candidates_in_funnel,
            "interviews_last_7d": my_interviews_last_7d,
            "offers_sent": my_offers_sent,
        }

        active_total = len(active_jobs_list)
        active_with_open_date = [j for j in active_jobs_list if j.open_date]
        avg_days_open = 0.0
        if active_with_open_date:
            total_days_open = sum((now - j.open_date).days for j in active_with_open_date)
            avg_days_open = total_days_open / len(active_with_open_date)

        at_risk_count = sum(1 for j in active_jobs_list if _is_job_at_risk(j, now))

        by_urgency = {"alta": 0, "média": 0, "baixa": 0}
        for job in active_jobs_list:
            priority = (job.priority or "média").lower()
            if priority in by_urgency:
                by_urgency[priority] += 1
            else:
                by_urgency["média"] += 1

        empty_pipeline_count = sum(
            1 for j in active_jobs_list
            if (j.funnel_data or {}).get("total", 0) == 0 or j.funnel_data is None
        )
        deadline_soon_count = sum(
            1 for j in active_jobs_list
            if j.deadline and 0 <= (j.deadline - now).days < 10
        )

        active_jobs_stats = {
            "total": active_total,
            "avg_days_open": round(avg_days_open, 1),
            "at_risk": at_risk_count,
            "by_urgency": by_urgency,
            "empty_pipeline": empty_pipeline_count,
            "deadline_soon": deadline_soon_count,
        }

        completed_with_dates_90d = [j for j in completed_jobs_90d if j.open_date and j.closed_at]
        time_to_fill_avg_90d = 0.0
        if completed_with_dates_90d:
            total_ttf_90d = sum(_calculate_days_between(j.open_date, j.closed_at) for j in completed_with_dates_90d)
            time_to_fill_avg_90d = total_ttf_90d / len(completed_with_dates_90d)

        total_jobs_90d = len([j for j in all_company_jobs if j.created_at and j.created_at >= date_90d_ago])
        success_rate = (len(completed_jobs_90d) / total_jobs_90d * 100) if total_jobs_90d > 0 else 0.0

        within_sla_count = 0
        for job in completed_jobs_90d:
            if job.deadline and job.closed_at:
                if job.closed_at <= job.deadline:
                    within_sla_count += 1
        within_sla_pct = (within_sla_count / len(completed_jobs_90d) * 100) if completed_jobs_90d else 0.0

        by_department: dict[str, int] = {}
        for job in active_jobs_list:
            dept = job.department or "Não definido"
            by_department[dept] = by_department.get(dept, 0) + 1

        trend_weeks: list[dict[str, Any]] = []
        for weeks_ago in range(7, -1, -1):
            week_start = now - timedelta(weeks=weeks_ago + 1)
            week_end = now - timedelta(weeks=weeks_ago)
            week_label = week_start.strftime("%d/%m")
            hired_in_week = len([j for j in completed_jobs if j.closed_at and week_start <= j.closed_at < week_end])
            opened_in_week = len([j for j in all_company_jobs if j.created_at and week_start <= j.created_at < week_end])
            trend_weeks.append({"week": week_label, "hired": hired_in_week, "opened": opened_in_week})

        all_jobs_stats = {
            "time_to_fill_avg_90d": round(time_to_fill_avg_90d, 1),
            "success_rate": round(success_rate, 1),
            "hired_last_30d": len(completed_jobs_30d),
            "hired_last_90d": len(completed_jobs_90d),
            "within_sla_pct": round(within_sla_pct, 1),
            "by_department": by_department,
            "trend_weeks": trend_weeks,
        }

        insights_input_stats = {
            "conversion_rate": my_conversion_rate,
            "time_to_fill_avg_90d": time_to_fill_avg_90d,
            "success_rate": success_rate,
        }
        insights = _generate_insights(
            my_jobs_list=my_jobs_list,
            active_jobs_list=active_jobs_list,
            completed_jobs_90d=completed_jobs_90d,
            stats=insights_input_stats,
            now=now,
        )

        return {
            "my_jobs": my_jobs_stats,
            "active_jobs": active_jobs_stats,
            "all_jobs": all_jobs_stats,
            "insights": insights,
        }

    async def get_job_vacancy_history(
        self,
        db: AsyncSession,
        job_id: UUID,
        company_id: UUID,
        page: int = 1,
        page_size: int = 50,
    ) -> dict[str, Any] | None:
        """Get audit history for a job vacancy.

        Extracted from GET /job-vacancies/{job_id}/history (lines 1189-1255).
        NOTE: Delegates to job_audit_service.get_history() for the actual history retrieval.

        Returns:
            Dict with keys: items, total, limit, offset, has_more
        """
        from app.domains.job_management.services.job_audit_service import job_audit_service

        result = await db.execute(
            select(JobVacancy).where(
                and_(JobVacancy.id == job_id, JobVacancy.company_id == company_id)
            )
        )
        job = result.scalar_one_or_none()
        if not job:
            return None

        offset = (page - 1) * page_size
        history = await job_audit_service.get_history(
            job_id=str(job_id),
            company_id=company_id,
            db=db,
            limit=page_size,
            offset=offset,
        )

        items = [
            {
                "id": item["id"],
                "job_vacancy_id": item["job_vacancy_id"],
                "company_id": item["company_id"],
                "action": item["action"],
                "field_changed": item.get("field_changed"),
                "old_value": item.get("old_value"),
                "new_value": item.get("new_value"),
                "changed_by": item["changed_by"],
                "changed_at": item["changed_at"],
                "ip_address": item.get("ip_address"),
                "user_agent": item.get("user_agent"),
                "extra_data": item.get("extra_data"),
            }
            for item in history["items"]
        ]

        return {
            "items": items,
            "total": history["total"],
            "limit": history["limit"],
            "offset": history["offset"],
            "has_more": history["has_more"],
        }

    async def search_job_vacancies(
        self,
        db: AsyncSession,
        company_id: UUID,
        query: str = "",
        page: int = 1,
        page_size: int = 10,
    ) -> dict[str, Any]:
        """Search job vacancies by title or job_id.

        Extracted from GET /job-vacancies/search (lines 367-443).

        Returns:
            Dict with keys: items, total_count, has_more
        """
        offset = (page - 1) * page_size
        base_filter = JobVacancy.company_id == company_id

        if query and len(query) >= 2:
            search_term = f"%{query}%"
            search_filter = and_(
                base_filter,
                or_(
                    JobVacancy.title.ilike(search_term),
                    JobVacancy.job_id.ilike(search_term),
                ),
            )
        else:
            search_filter = base_filter

        count_stmt = select(func.count(JobVacancy.id)).where(search_filter)
        count_result = await db.execute(count_stmt)
        total_count = count_result.scalar() or 0

        stmt = (
            select(
                JobVacancy.id,
                JobVacancy.job_id,
                JobVacancy.title,
                JobVacancy.status,
                JobVacancy.created_at,
                JobVacancy.description,
            )
            .where(search_filter)
            .order_by(JobVacancy.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        result = await db.execute(stmt)
        rows = result.all()

        items: list[dict[str, Any]] = []
        for row in rows:
            description_preview = None
            if row.description:
                description_preview = row.description[:150] + "..." if len(row.description) > 150 else row.description
            items.append({
                "id": str(row.id),
                "job_id": row.job_id,
                "title": row.title,
                "status": row.status or "Rascunho",
                "created_at": row.created_at.isoformat() if row.created_at else "",
                "description_preview": description_preview,
            })

        return {
            "items": items,
            "total_count": total_count,
            "has_more": (offset + len(items)) < total_count,
        }

    async def finalize_job_vacancy(
        self,
        db: AsyncSession,
        job_vacancy_state: Any,
        conversation_id: str,
        created_by: str,
        company_id: UUID,
        current_user: Any,
        pipeline_template_id: str | None = None,
    ) -> dict[str, Any]:
        """Finalize job vacancy creation and persist to database.

        Extracted from POST /job-vacancies/finalize (lines 286-343).
        NOTE: Delegates the core persistence to job_vacancy_service.finalize_job_vacancy().
        This facade validates readiness, calls the existing service, and logs the audit event.

        Returns:
            Dict with keys: success, job_vacancy_id, title, status, message
        """
        from app.domains.job_management.services.job_audit_service import job_audit_service
        from app.domains.job_management.services.job_vacancy_service import job_vacancy_service

        if not job_vacancy_state.is_ready_for_publication():
            return {
                "success": False,
                "error": "Job vacancy is not ready for publication. Missing required fields.",
            }

        job_vacancy = await job_vacancy_service.finalize_job_vacancy(
            state=job_vacancy_state,
            conversation_id=conversation_id,
            created_by=created_by,
            company_id=company_id,
            db=db,
            current_user=current_user,
            pipeline_template_id=pipeline_template_id,
        )

        job_id = str(job_vacancy.id)
        job_title = str(job_vacancy.title)
        job_status = str(job_vacancy.status)

        await job_audit_service.log_creation(
            job_id=job_id,
            created_by=created_by,
            company_id=company_id,
            db=db,
            job_data={"title": job_title, "status": job_status},
        )
        await db.commit()

        return {
            "success": True,
            "job_vacancy_id": job_id,
            "title": job_title,
            "status": job_status,
            "message": f"Vaga '{job_title}' criada com sucesso!",
        }


job_vacancy_route_service = JobVacancyRouteService()
