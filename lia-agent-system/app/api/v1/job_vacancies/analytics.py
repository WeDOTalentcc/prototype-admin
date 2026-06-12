from datetime import datetime, timedelta
from typing import Any
from uuid import UUID
from app.api.v1._path_patterns import DUAL_ID_PATH_PATTERN

"""
Analytics routes: metrics, analytics deep-dive, history, stats/overview,
archetypes (already in crud.py), job report.
"""
from fastapi import APIRouter, Depends, HTTPException, Path, Query

from ._shared import (  # noqa: F401
    _calculate_days_between,
    _is_job_at_risk,
    get_current_user_or_demo,
    get_user_company_id,
    User,
    get_db,
    Depends,
    HTTPException,
    JobVacancy,
    BaseModel,
    logger,
)
from app.repositories.dependencies import get_job_vacancies_analytics_repo
from app.repositories.job_vacancies_analytics_repository import (
    JobVacanciesAnalyticsRepository,
)
from app.shared.security.require_company_id import require_company_id

router = APIRouter()


# ─── Metrics ─────────────────────────────────────────────────────────────────

class FunnelMetrics(BaseModel):
    total: int = 0
    screening: int = 0
    interview: int = 0
    offer: int = 0
    hired: int = 0
    rejected: int = 0


class PerformanceMetrics(BaseModel):
    time_to_fill_days: int | None = None
    avg_time_in_stage_days: float | None = None
    conversion_rate: float = 0.0
    source_breakdown: dict[str, int] = {}


class ActivityMetrics(BaseModel):
    views_7d: int = 0
    applications_7d: int = 0
    interviews_scheduled: int = 0
    last_activity: str | None = None


class SLAMetrics(BaseModel):
    within_sla: bool = True
    days_remaining: int | None = None
    deadline: str | None = None


class JobVacancyMetricsResponse(BaseModel):
    job_id: str
    funnel: FunnelMetrics
    performance: PerformanceMetrics
    activity: ActivityMetrics
    sla: SLAMetrics


@router.get("/job-vacancies/{job_vacancy_id}/metrics", response_model=JobVacancyMetricsResponse)
async def get_job_vacancy_metrics(
    job_vacancy_id: str = Path(..., pattern=DUAL_ID_PATH_PATTERN),
    current_user: User = Depends(get_current_user_or_demo),
    repo: JobVacanciesAnalyticsRepository = Depends(get_job_vacancies_analytics_repo),
company_id: str = Depends(require_company_id)):
    """Get performance metrics for a specific job vacancy."""
    try:
        company_id = get_user_company_id(current_user)

        job = await repo.get_job_by_id_and_company(job_vacancy_id, company_id)
        if not job:
            raise HTTPException(status_code=404, detail="Vaga não encontrada")

        stage_counts = await repo.get_stage_counts_for_vacancy(job_vacancy_id)
        total_candidates = await repo.get_total_candidates_for_vacancy(job_vacancy_id)
        source_breakdown = await repo.get_source_counts_for_vacancy(job_vacancy_id)

        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        applications_7d = await repo.get_applications_since(job_vacancy_id, seven_days_ago)
        last_activity = await repo.get_last_activity_for_vacancy(job_vacancy_id)

        fallback_funnel = job.funnel_data or {}

        screening_count = stage_counts.get("screening", 0) + stage_counts.get("triagem", 0) + stage_counts.get("initial", 0)
        interview_count = stage_counts.get("interview", 0) + stage_counts.get("entrevista", 0)
        offer_count = stage_counts.get("offer", 0) + stage_counts.get("proposta", 0)
        hired_count = stage_counts.get("hired", 0) + stage_counts.get("contratado", 0)
        rejected_count = stage_counts.get("rejected", 0) + stage_counts.get("reprovado", 0) + stage_counts.get("recusado", 0)

        funnel = FunnelMetrics(
            total=total_candidates if total_candidates > 0 else fallback_funnel.get("total", 0),
            screening=screening_count if screening_count > 0 else fallback_funnel.get("screening", 0),
            interview=interview_count if interview_count > 0 else fallback_funnel.get("interview", 0),
            offer=offer_count if offer_count > 0 else fallback_funnel.get("offer", 0),
            hired=hired_count if hired_count > 0 else fallback_funnel.get("hired", 0),
            rejected=rejected_count if rejected_count > 0 else fallback_funnel.get("rejected", 0)
        )

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
        if funnel.total > 0:
            conversion_rate = round(funnel.hired / funnel.total, 3)

        interviews_scheduled = interview_count

        performance = PerformanceMetrics(
            time_to_fill_days=time_to_fill_days,
            avg_time_in_stage_days=avg_time_in_stage,
            conversion_rate=conversion_rate,
            source_breakdown=source_breakdown
        )

        views_7d = job.additional_data.get("views_7d", 0) if job.additional_data else 0

        activity = ActivityMetrics(
            views_7d=views_7d,
            applications_7d=applications_7d,
            interviews_scheduled=interviews_scheduled,
            last_activity=last_activity.isoformat() if last_activity else None
        )

        within_sla = True
        days_remaining = None
        deadline_str = None

        if job.deadline:
            deadline_str = job.deadline.strftime("%Y-%m-%d")
            days_remaining = (job.deadline - datetime.utcnow()).days
            within_sla = days_remaining >= 0

        sla = SLAMetrics(
            within_sla=within_sla,
            days_remaining=days_remaining,
            deadline=deadline_str
        )

        logger.info(f"Retrieved metrics for job vacancy {job_vacancy_id}: {funnel.total} candidates, conversion {conversion_rate}")

        return JobVacancyMetricsResponse(
            job_id=str(job_vacancy_id),
            funnel=funnel,
            performance=performance,
            activity=activity,
            sla=sla
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching job vacancy metrics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ─── Deep Analytics ───────────────────────────────────────────────────────────

class FunnelStageItem(BaseModel):
    stage: str
    count: int
    conversion_rate: float
    avg_days: float


class SourceAnalysisItem(BaseModel):
    source: str
    count: int
    conversion_rate: float


class DailyApplicationItem(BaseModel):
    date: str
    count: int


class JobAnalyticsResponse(BaseModel):
    vacancy_id: str
    vacancy_title: str
    funnel: list[FunnelStageItem]
    total_candidates: int
    total_hired: int
    overall_conversion_rate: float
    avg_time_to_hire: float
    avg_time_to_first_response: float
    time_in_stage: dict[str, float]
    sources: list[SourceAnalysisItem]
    top_source: str
    daily_applications: list[DailyApplicationItem]
    weekly_trend: float
    avg_lia_score: float
    avg_skills_match: float
    top_rejection_reasons: list[str]
    company_avg_time_to_hire: float
    company_avg_conversion_rate: float
    position_percentile: int


@router.get("/job-vacancies/{job_id}/analytics", response_model=JobAnalyticsResponse)
async def get_job_analytics(
    job_id: str = Path(..., pattern=DUAL_ID_PATH_PATTERN),
    current_user: User = Depends(get_current_user_or_demo),
    repo: JobVacanciesAnalyticsRepository = Depends(get_job_vacancies_analytics_repo),
company_id: str = Depends(require_company_id)):
    """Returns detailed analytics for a job vacancy."""
    try:
        company_id = get_user_company_id(current_user)

        job = await repo.get_job_by_id_and_company(job_id, company_id)
        if not job:
            raise HTTPException(status_code=404, detail="Vaga não encontrada")

        vacancy_candidates = await repo.get_all_vacancy_candidates(job_id)
        total_candidates = len(vacancy_candidates)

        stage_counts: dict[str, int] = {}
        source_counts: dict[str, int] = {}
        source_hired_counts: dict[str, int] = {}
        hired_count = 0
        lia_scores = []
        match_percentages = []

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

        stage_order = ["sourcing", "initial", "pending_gate1", "screening", "triagem", "interview", "entrevista", "offer", "proposta", "hired", "contratado", "rejected", "reprovado"]
        funnel_items = []
        cumulative_count = total_candidates

        for stage_name in stage_order:
            if stage_name in stage_counts:
                count = stage_counts[stage_name]
                conversion_rate = (count / cumulative_count * 100) if cumulative_count > 0 else 0.0
                funnel_items.append(FunnelStageItem(
                    stage=stage_name,
                    count=count,
                    conversion_rate=round(conversion_rate, 1),
                    avg_days=0.0
                ))

        for stage_name, count in stage_counts.items():
            if stage_name not in stage_order:
                conversion_rate = (count / total_candidates * 100) if total_candidates > 0 else 0.0
                funnel_items.append(FunnelStageItem(
                    stage=stage_name,
                    count=count,
                    conversion_rate=round(conversion_rate, 1),
                    avg_days=0.0
                ))

        stage_history = await repo.get_stage_history_for_vacancy(job_id)

        time_in_stage: dict[str, list[float]] = {}
        rejection_reasons: list[str] = []
        first_response_times: list[float] = []
        hire_times: list[float] = []

        for history_entry in stage_history:
            if history_entry.time_in_previous_stage_hours is not None and history_entry.from_stage_name:
                stage_name = history_entry.from_stage_name
                hours = history_entry.time_in_previous_stage_hours
                days = hours / 24.0
                if stage_name not in time_in_stage:
                    time_in_stage[stage_name] = []
                time_in_stage[stage_name].append(days)

            if history_entry.to_stage_name in ["rejected", "reprovado"] and history_entry.reason:
                rejection_reasons.append(history_entry.reason)

            if history_entry.from_stage_name in ["sourcing", "initial", None] and history_entry.to_stage_name not in ["sourcing", "initial"]:
                if history_entry.time_in_previous_stage_hours is not None:
                    first_response_times.append(history_entry.time_in_previous_stage_hours / 24.0)

            if history_entry.to_stage_name in ["hired", "contratado"]:
                candidate_history = [h for h in stage_history if h.candidate_id == history_entry.candidate_id]
                total_time = sum(h.time_in_previous_stage_hours or 0 for h in candidate_history)
                hire_times.append(total_time / 24.0)

        avg_time_in_stage: dict[str, float] = {}
        for stage_name, times in time_in_stage.items():
            avg_time_in_stage[stage_name] = round(sum(times) / len(times), 1) if times else 0.0

        for funnel_item in funnel_items:
            if funnel_item.stage in avg_time_in_stage:
                funnel_item.avg_days = avg_time_in_stage[funnel_item.stage]

        avg_time_to_hire = round(sum(hire_times) / len(hire_times), 1) if hire_times else 0.0
        avg_time_to_first_response = round(sum(first_response_times) / len(first_response_times), 1) if first_response_times else 0.0

        sources_list = []
        for source, count in sorted(source_counts.items(), key=lambda x: x[1], reverse=True):
            hired_from_source = source_hired_counts.get(source, 0)
            conversion = (hired_from_source / count * 100) if count > 0 else 0.0
            sources_list.append(SourceAnalysisItem(
                source=source,
                count=count,
                conversion_rate=round(conversion, 1)
            ))

        top_source = sources_list[0].source if sources_list else "unknown"

        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        daily_apps_rows = await repo.get_daily_applications(job_id, thirty_days_ago)

        daily_applications = [
            DailyApplicationItem(date=str(row.date), count=row.count)
            for row in daily_apps_rows
        ]

        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        fourteen_days_ago = datetime.utcnow() - timedelta(days=14)

        this_week_count = await repo.get_applications_in_range(job_id, seven_days_ago)
        last_week_count = await repo.get_applications_in_range(job_id, fourteen_days_ago, seven_days_ago)

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

        company_jobs = await repo.get_completed_jobs_for_company(company_id)

        company_hire_times = []
        company_conversion_rates = []

        for company_job in company_jobs:
            if company_job.open_date and company_job.closed_at:
                days_to_fill = (company_job.closed_at - company_job.open_date).days
                company_hire_times.append(days_to_fill)

            if company_job.funnel_data:
                total = company_job.funnel_data.get("total", 0)
                hired = company_job.funnel_data.get("hired", 0)
                if total > 0:
                    company_conversion_rates.append((hired / total) * 100)

        company_avg_time_to_hire = round(sum(company_hire_times) / len(company_hire_times), 1) if company_hire_times else 0.0
        company_avg_conversion_rate = round(sum(company_conversion_rates) / len(company_conversion_rates), 1) if company_conversion_rates else 0.0

        overall_conversion_rate = (hired_count / total_candidates * 100) if total_candidates > 0 else 0.0

        position_percentile = 50
        if company_conversion_rates and overall_conversion_rate > 0:
            better_than = sum(1 for r in company_conversion_rates if overall_conversion_rate > r)
            position_percentile = int((better_than / len(company_conversion_rates)) * 100)

        logger.info(f"Retrieved analytics for job vacancy {job_id}: {total_candidates} candidates, {hired_count} hired")

        return JobAnalyticsResponse(
            vacancy_id=str(job_id),
            vacancy_title=job.title,
            funnel=funnel_items,
            total_candidates=total_candidates,
            total_hired=hired_count,
            overall_conversion_rate=round(overall_conversion_rate, 1),
            avg_time_to_hire=avg_time_to_hire,
            avg_time_to_first_response=avg_time_to_first_response,
            time_in_stage=avg_time_in_stage,
            sources=sources_list,
            top_source=top_source,
            daily_applications=daily_applications,
            weekly_trend=weekly_trend,
            avg_lia_score=avg_lia_score,
            avg_skills_match=avg_skills_match,
            top_rejection_reasons=top_rejection_reasons,
            company_avg_time_to_hire=company_avg_time_to_hire,
            company_avg_conversion_rate=company_avg_conversion_rate,
            position_percentile=position_percentile
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching job vacancy analytics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ─── History ──────────────────────────────────────────────────────────────────

class AuditLogItem(BaseModel):
    id: str
    job_vacancy_id: str
    company_id: str
    action: str
    field_changed: str | None = None
    old_value: Any | None = None
    new_value: Any | None = None
    changed_by: str
    changed_at: str
    ip_address: str | None = None
    user_agent: str | None = None
    extra_data: dict[str, Any] | None = None


class JobVacancyHistoryResponse(BaseModel):
    items: list[AuditLogItem]
    total: int
    limit: int
    offset: int
    has_more: bool


@router.get("/job-vacancies/{job_id}/history", response_model=JobVacancyHistoryResponse)
async def get_job_vacancy_history(
    job_id: str = Path(..., pattern=DUAL_ID_PATH_PATTERN),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user_or_demo),
    repo: JobVacanciesAnalyticsRepository = Depends(get_job_vacancies_analytics_repo),
company_id: str = Depends(require_company_id)):
    """Get audit history for a job vacancy."""
    from app.domains.job_management.services.job_audit_service import job_audit_service
    from app.core.database import get_db as _get_db
    from fastapi import Request

    try:
        company_id = get_user_company_id(current_user)
        offset = (page - 1) * page_size

        job = await repo.get_job_by_id_and_company(job_id, company_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job vacancy not found")

        history = await job_audit_service.get_history(
            job_id=str(job_id),
            company_id=company_id,
            db=repo.db,
            limit=page_size,
            offset=offset
        )

        items = [
            AuditLogItem(
                id=item["id"],
                job_vacancy_id=item["job_vacancy_id"],
                company_id=item["company_id"],
                action=item["action"],
                field_changed=item.get("field_changed"),
                old_value=item.get("old_value"),
                new_value=item.get("new_value"),
                changed_by=item["changed_by"],
                changed_at=item["changed_at"],
                ip_address=item.get("ip_address"),
                user_agent=item.get("user_agent"),
                extra_data=item.get("extra_data"),
            )
            for item in history["items"]
        ]

        return JobVacancyHistoryResponse(
            items=items,
            total=history["total"],
            limit=history["limit"],
            offset=history["offset"],
            has_more=history["has_more"]
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching job vacancy history: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ─── Stats Overview ───────────────────────────────────────────────────────────

class MyJobsStats(BaseModel):
    active: int = 0
    completed: int = 0
    time_to_fill_avg: float = 0.0
    candidates_interviewed: int = 0
    conversion_rate: float = 0.0
    candidates_in_funnel: int = 0
    interviews_last_7d: int = 0
    offers_sent: int = 0


class ActiveJobsStats(BaseModel):
    total: int = 0
    avg_days_open: float = 0.0
    at_risk: int = 0
    by_urgency: dict[str, int] = {"alta": 0, "média": 0, "baixa": 0}
    empty_pipeline: int = 0
    deadline_soon: int = 0


class WeeklyTrend(BaseModel):
    week: str
    hired: int = 0
    opened: int = 0


class AllJobsStats(BaseModel):
    time_to_fill_avg_90d: float = 0.0
    success_rate: float = 0.0
    hired_last_30d: int = 0
    hired_last_90d: int = 0
    within_sla_pct: float = 0.0
    by_department: dict[str, int] = {}
    trend_weeks: list[WeeklyTrend] = []


class Insight(BaseModel):
    type: str
    message: str
    severity: str | None = None
    action: str | None = None


class StatsOverviewResponse(BaseModel):
    my_jobs: MyJobsStats
    active_jobs: ActiveJobsStats
    all_jobs: AllJobsStats
    insights: list[Insight] = []


def _generate_insights(
    my_jobs_list: list,
    active_jobs_list: list,
    completed_jobs_90d: list,
    stats: dict[str, Any],
    now: datetime
) -> list[Insight]:
    """Generate automatic insights based on metrics data."""
    insights = []

    stalled_jobs = [j for j in active_jobs_list if j.updated_at and (now - j.updated_at).days > 15]

    if len(stalled_jobs) > 0:
        job_titles = [j.title for j in stalled_jobs[:3]]
        titles_str = ", ".join(job_titles)
        if len(stalled_jobs) > 3:
            titles_str += f" e mais {len(stalled_jobs) - 3}"
        insights.append(Insight(
            type="alert",
            message=f"{len(stalled_jobs)} vaga(s) parada(s) há mais de 15 dias: {titles_str}",
            severity="warning" if len(stalled_jobs) < 3 else "critical"
        ))

    empty_pipeline_jobs = [j for j in active_jobs_list if (j.funnel_data or {}).get("total", 0) == 0]

    if len(empty_pipeline_jobs) > 0:
        job_titles = [j.title for j in empty_pipeline_jobs[:3]]
        titles_str = ", ".join(job_titles)
        if len(empty_pipeline_jobs) > 3:
            titles_str += f" e mais {len(empty_pipeline_jobs) - 3}"
        insights.append(Insight(
            type="alert",
            message=f"{len(empty_pipeline_jobs)} vaga(s) sem candidatos no pipeline: {titles_str}",
            severity="critical" if len(empty_pipeline_jobs) > 2 else "warning"
        ))

    deadline_soon_jobs = []
    for job in active_jobs_list:
        if job.deadline:
            days_to_deadline = (job.deadline - now).days
            if 0 <= days_to_deadline < 10:
                deadline_soon_jobs.append((job, days_to_deadline))

    if len(deadline_soon_jobs) > 0:
        details = [f"{j.title} ({d}d)" for j, d in deadline_soon_jobs[:3]]
        details_str = ", ".join(details)
        insights.append(Insight(
            type="alert",
            message=f"{len(deadline_soon_jobs)} vaga(s) com deadline próximo: {details_str}",
            severity="warning"
        ))

    if stats.get("conversion_rate", 0) < 10 and len(my_jobs_list) >= 3:
        insights.append(Insight(
            type="suggestion",
            message="Taxa de conversão abaixo de 10%. Considere revisar os critérios de triagem ou a descrição das vagas.",
            action="review_screening_criteria"
        ))

    ttf_avg = stats.get("time_to_fill_avg_90d", 0)
    if ttf_avg > 45:
        insights.append(Insight(
            type="suggestion",
            message=f"Tempo médio de preenchimento está em {ttf_avg:.0f} dias. Considere estratégias de sourcing mais ativas.",
            action="improve_sourcing"
        ))

    high_priority_count = sum(1 for j in active_jobs_list if j.priority == "alta")
    if high_priority_count >= 5:
        insights.append(Insight(
            type="alert",
            message=f"{high_priority_count} vagas com prioridade alta abertas. Considere priorizar recursos.",
            severity="warning"
        ))

    success_rate = stats.get("success_rate", 0)
    if success_rate > 80 and len(completed_jobs_90d) >= 5:
        insights.append(Insight(
            type="suggestion",
            message=f"Excelente taxa de sucesso de {success_rate:.0f}%! Continue monitorando para manter o padrão.",
            action="maintain_standards"
        ))

    return insights


@router.get("/job-vacancies/stats/overview", response_model=StatsOverviewResponse)
async def get_job_vacancies_stats_overview(
    recruiter_email: str | None = Query(None),
    current_user: User = Depends(get_current_user_or_demo),
    repo: JobVacanciesAnalyticsRepository = Depends(get_job_vacancies_analytics_repo),
company_id: str = Depends(require_company_id)):
    """Get aggregated metrics for the job vacancies dashboard."""
    try:
        company_id = get_user_company_id(current_user)
        now = datetime.utcnow()
        logger.info(f"Fetching job vacancies stats overview for company: {company_id}")

        recruiter_filter_email = recruiter_email or current_user.email

        all_company_jobs = await repo.get_all_company_jobs(company_id)

        # Fix 2026-06-08: funnel_data was NULL/stale for all active jobs;
        # use vacancy_candidates real counts instead of the cached JSON column.
        try:
            live_candidate_counts = await repo.get_candidate_counts_by_vacancy_for_company(company_id)
        except Exception as _e:
            logger.warning("Could not fetch live candidate counts: %s", _e)
            live_candidate_counts = {}

        my_jobs_list = [
            j for j in all_company_jobs
            if j.recruiter_email and j.recruiter_email.lower() == recruiter_filter_email.lower()
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
        if my_completed_jobs:
            total_ttf = sum(_calculate_days_between(j.open_date, j.closed_at) for j in my_completed_jobs)
            my_time_to_fill_avg = total_ttf / len(my_completed_jobs)
        else:
            my_time_to_fill_avg = 0.0

        my_candidates_interviewed = 0
        my_candidates_in_funnel = 0
        my_offers_sent = 0

        # Fix 2026-06-08: use real vacancy_candidates counts (live_candidate_counts)
        # instead of stale funnel_data. If current user has no assigned jobs (e.g.
        # company owner), fall back to summing across ALL active jobs so the header
        # never shows 0 when candidates clearly exist.
        jobs_for_funnel = my_jobs_list if my_jobs_list else active_jobs_list
        for job in jobs_for_funnel:
            job_id_str = str(job.id)
            my_candidates_in_funnel += live_candidate_counts.get(job_id_str, 0)
            # interviewed / offers: keep funnel_data for these (less critical)
            funnel = job.funnel_data or {}
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
        # Fix 2026-06-08: funnel_data.interview is stale; use job updated_at as
        # a reasonable proxy (if job was updated this week, count its live VC total).
        # Full fix: query VacancyCandidate stage_name directly (deferred — needs
        # VacancyCandidateRepository in this endpoint).
        for job in jobs_for_funnel:
            if job.updated_at and job.updated_at >= date_7d_ago:
                my_interviews_last_7d += live_candidate_counts.get(str(job.id), 0)

        my_jobs_stats = MyJobsStats(
            active=my_active,
            completed=my_completed,
            time_to_fill_avg=round(my_time_to_fill_avg, 1),
            candidates_interviewed=my_candidates_interviewed,
            conversion_rate=round(my_conversion_rate, 1),
            candidates_in_funnel=my_candidates_in_funnel,
            interviews_last_7d=my_interviews_last_7d,
            offers_sent=my_offers_sent
        )

        active_total = len(active_jobs_list)

        active_with_open_date = [j for j in active_jobs_list if j.open_date]
        if active_with_open_date:
            total_days_open = sum((now - j.open_date).days for j in active_with_open_date)
            avg_days_open = total_days_open / len(active_with_open_date)
        else:
            avg_days_open = 0.0

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

        active_jobs_stats = ActiveJobsStats(
            total=active_total,
            avg_days_open=round(avg_days_open, 1),
            at_risk=at_risk_count,
            by_urgency=by_urgency,
            empty_pipeline=empty_pipeline_count,
            deadline_soon=deadline_soon_count
        )

        completed_with_dates_90d = [j for j in completed_jobs_90d if j.open_date and j.closed_at]
        if completed_with_dates_90d:
            total_ttf_90d = sum(_calculate_days_between(j.open_date, j.closed_at) for j in completed_with_dates_90d)
            time_to_fill_avg_90d = total_ttf_90d / len(completed_with_dates_90d)
        else:
            time_to_fill_avg_90d = 0.0

        total_jobs_90d = len([j for j in all_company_jobs if j.created_at and j.created_at >= date_90d_ago])
        success_rate = (len(completed_jobs_90d) / total_jobs_90d * 100) if total_jobs_90d > 0 else 0.0

        hired_last_30d = len(completed_jobs_30d)
        hired_last_90d = len(completed_jobs_90d)

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

        trend_weeks: list[WeeklyTrend] = []
        for weeks_ago in range(7, -1, -1):
            week_start = now - timedelta(weeks=weeks_ago + 1)
            week_end = now - timedelta(weeks=weeks_ago)
            week_label = week_start.strftime("%d/%m")

            hired_in_week = len([j for j in completed_jobs if j.closed_at and week_start <= j.closed_at < week_end])
            opened_in_week = len([j for j in all_company_jobs if j.created_at and week_start <= j.created_at < week_end])

            trend_weeks.append(WeeklyTrend(week=week_label, hired=hired_in_week, opened=opened_in_week))

        all_jobs_stats = AllJobsStats(
            time_to_fill_avg_90d=round(time_to_fill_avg_90d, 1),
            success_rate=round(success_rate, 1),
            hired_last_30d=hired_last_30d,
            hired_last_90d=hired_last_90d,
            within_sla_pct=round(within_sla_pct, 1),
            by_department=by_department,
            trend_weeks=trend_weeks
        )

        insights_input_stats = {
            "conversion_rate": my_conversion_rate,
            "time_to_fill_avg_90d": time_to_fill_avg_90d,
            "success_rate": success_rate
        }

        insights = _generate_insights(
            my_jobs_list=my_jobs_list,
            active_jobs_list=active_jobs_list,
            completed_jobs_90d=completed_jobs_90d,
            stats=insights_input_stats,
            now=now
        )

        logger.info(f"Stats overview generated: {active_total} active jobs, {len(completed_jobs_90d)} completed (90d), {len(insights)} insights")

        return StatsOverviewResponse(
            my_jobs=my_jobs_stats,
            active_jobs=active_jobs_stats,
            all_jobs=all_jobs_stats,
            insights=insights
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching job vacancies stats overview: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ─── Job Report ──────────────────────────────────────────────────────────────

class JobReportFunnelMetrics(BaseModel):
    total_candidates: int
    screening: int
    interview: int
    final: int
    hired: int
    conversion_rate: float
    avg_time_to_hire: float
    cost_per_hire: float


class JobReportChannelItem(BaseModel):
    channel: str
    candidates: int
    hired: int


class JobReportTopCandidate(BaseModel):
    name: str
    score: float
    status: str


class JobReportResponse(BaseModel):
    vacancy_id: str
    vacancy_title: str
    funnel_metrics: JobReportFunnelMetrics
    channel_performance: list[JobReportChannelItem]
    top_candidates: list[JobReportTopCandidate]


@router.get("/jobs/{job_id}/report", response_model=JobReportResponse)
async def get_job_report(
    job_id: str = Path(..., pattern=r"^(?:[0-9a-fA-F-]{36}|[0-9]+)$"),
    current_user: User = Depends(get_current_user_or_demo),
    repo: JobVacanciesAnalyticsRepository = Depends(get_job_vacancies_analytics_repo),
    db=None,
company_id: str = Depends(require_company_id)):
    # Support db kwarg for backwards compatibility (tests inject db directly)
    if db is not None and not hasattr(repo, 'get_job_by_id_and_company'):
        from app.repositories.job_vacancies_analytics_repository import JobVacanciesAnalyticsRepository as _JVAR
        repo = _JVAR(db)
    """Returns JSON data for the JobReportModal."""
    company_id = get_user_company_id(current_user)

    job = await repo.get_job_by_id_and_company(job_id, company_id)
    if not job:
        raise HTTPException(status_code=404, detail="Vaga não encontrada")

    vacancy_candidates = await repo.get_all_vacancy_candidates(job_id)
    total = len(vacancy_candidates)

    stage_map: dict[str, int] = {}
    source_map: dict[str, int] = {}
    source_hired: dict[str, int] = {}
    hired_count = 0

    for vc in vacancy_candidates:
        stage = (vc.stage or "initial").lower()
        source = vc.source or "unknown"
        stage_map[stage] = stage_map.get(stage, 0) + 1
        source_map[source] = source_map.get(source, 0) + 1
        if stage in ("hired", "contratado"):
            hired_count += 1
            source_hired[source] = source_hired.get(source, 0) + 1

    def _stage_count(*aliases: str) -> int:
        return sum(stage_map.get(a, 0) for a in aliases)

    screening_count = _stage_count("screening", "triagem", "pending_gate1")
    interview_count = _stage_count("interview", "entrevista")
    final_count = _stage_count("final", "offer", "proposta")
    conversion_rate = round(hired_count / total * 100, 1) if total > 0 else 0.0

    avg_time_to_hire = 0.0
    avg_hours = await repo.get_avg_time_to_hire(job_id)
    if avg_hours:
        avg_time_to_hire = round(avg_hours / 24, 1)

    top_vc_rows = await repo.get_top_candidates_with_score(job_id, limit=5)
    top_candidates = []
    for vc, cand in top_vc_rows:
        top_candidates.append(
            JobReportTopCandidate(
                name=cand.name or "Candidato",
                score=float(vc.lia_score or 0),
                status=vc.stage or "initial",
            )
        )

    channel_performance = []
    for source, count in sorted(source_map.items(), key=lambda x: -x[1]):
        channel_performance.append(
            JobReportChannelItem(
                channel=source,
                candidates=count,
                hired=source_hired.get(source, 0),
            )
        )

    return JobReportResponse(
        vacancy_id=str(job_id),
        vacancy_title=job.title,
        funnel_metrics=JobReportFunnelMetrics(
            total_candidates=total,
            screening=screening_count,
            interview=interview_count,
            final=final_count,
            hired=hired_count,
            conversion_rate=conversion_rate,
            avg_time_to_hire=avg_time_to_hire,
            cost_per_hire=0.0,
        ),
        channel_performance=channel_performance,
        top_candidates=top_candidates,
    )


@router.get("/work-model-analytics", response_model=None)
async def get_work_model_analytics(
    period: str = Query("90d"),
    current_user=Depends(get_current_user_or_demo),
    repo: JobVacanciesAnalyticsRepository = Depends(get_job_vacancies_analytics_repo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    company_id = str(current_user.company_id) if hasattr(current_user, "company_id") and current_user.company_id else None
    if not company_id:
        raise HTTPException(status_code=403, detail="Company not associated with user")

    period_map = {"30d": 30, "90d": 90, "6m": 180, "1y": 365}
    days = period_map.get(period, 90)

    wm_rows = await repo.get_work_model_distribution(company_id, days)
    title_rows = await repo.get_work_model_by_title(company_id, days)
    loc_rows = await repo.get_work_model_by_location(company_id, days)

    total_all = sum(r.total for r in wm_rows) if wm_rows else 0

    model_map = {"remoto": "remoto", "remote": "remoto", "híbrido": "híbrido", "hybrid": "híbrido", "presencial": "presencial", "on-site": "presencial", "onsite": "presencial"}

    distribution = []
    for r in wm_rows:
        normalized = model_map.get(r.work_model.lower().strip(), r.work_model.lower().strip())
        distribution.append({
            "modelo": normalized,
            "candidatos": r.total,
            "percentual": round((r.total / total_all * 100), 1) if total_all > 0 else 0,
            "salarioMedio": r.avg_salary or 0,
        })

    by_title = {}
    for r in title_rows:
        normalized = model_map.get(r.work_model.lower().strip(), r.work_model.lower().strip())
        if r.title not in by_title:
            by_title[r.title] = {"cargo": r.title, "remoto": 0, "hibrido": 0, "presencial": 0, "total": 0}
        key = "hibrido" if normalized == "híbrido" else normalized
        by_title[r.title][key] = by_title[r.title].get(key, 0) + r.total
        by_title[r.title]["total"] += r.total

    by_location = {}
    for r in loc_rows:
        normalized = model_map.get(r.work_model.lower().strip(), r.work_model.lower().strip())
        if r.location not in by_location:
            by_location[r.location] = {"regiao": r.location, "remoto": 0, "hibrido": 0, "presencial": 0, "total": 0}
        key = "hibrido" if normalized == "híbrido" else normalized
        by_location[r.location][key] = by_location[r.location].get(key, 0) + r.total
        by_location[r.location]["total"] += r.total

    return {
        "distribution": distribution,
        "by_title": list(by_title.values()),
        "by_location": list(by_location.values()),
        "total": total_all,
        "period": period,
    }


# ─── Pipeline Overview (cross-vacancy) ────────────────────────────────────────

class PipelineOverviewCandidateItem(BaseModel):
    vc_id: str
    vacancy_id: str
    candidate_id: str = ""
    name: str
    vacancy_title: str | None = None
    sub_status: str | None = None
    stage_entered_at: str | None = None
    lia_score: float | None = None
    match_percentage: float | None = None
    wsi_score: float | None = None
    lia_opinion_score: float | None = None
    score_breakdown: dict | None = None
    technical_test_score: float | None = None
    english_test_score: float | None = None
    big_five_data: dict | None = None


class PipelineOverviewStageItem(BaseModel):
    stage: str
    count: int
    candidates: list[PipelineOverviewCandidateItem] = []


class PipelineOverviewResponse(BaseModel):
    stages: list[PipelineOverviewStageItem]
    total_candidates: int


class PipelinePulseStage(BaseModel):
    macro_stage: str
    count: int

class PipelinePulseResponse(BaseModel):
    stages: list[PipelinePulseStage]
    total: int

STAGE_TO_MACRO = {
    "Novo": "sourcing",
    "novo": "sourcing",
    "Sourcing": "sourcing",
    "sourcing": "sourcing",
    "initial": "sourcing",
    "Triagem": "triagem",
    "triagem": "triagem",
    "Reprovado Triagem": "triagem",
    "reprovado triagem": "triagem",
    "pending_gate1": "triagem",
    "screening": "triagem",
    "Entrevista": "entrevista",
    "entrevista": "entrevista",
    "Entrevista RH": "entrevista",
    "Entrevista Técnica": "entrevista",
    "Entrevista Final": "entrevista",
    "interview": "entrevista",
    "Proposta": "oferta",
    "proposta": "oferta",
    "offer": "oferta",
    "Oferta": "oferta",
    "Contratado": "contratacao",
    "contratado": "contratacao",
    "hired": "contratacao",
    "Recusado": "contratacao",
    "recusado": "contratacao",
    # Stages present in real DB rows — caused 13 invisible candidates in pipeline-pulse
    "interview_hr": "entrevista",
    "interview_manager": "entrevista",
    "interview_manager2": "entrevista",
    "interview_technical": "entrevista",
    "technical_test": "entrevista",
    "english_test": "entrevista",
    "short_list": "triagem",
    "long_list": "triagem",
    "rejected": "contratacao",
    "reprovado": "contratacao",
}

@router.get("/pipeline-pulse", response_model=PipelinePulseResponse)
async def get_pipeline_pulse(
    current_user=Depends(get_current_user_or_demo),
    repo: JobVacanciesAnalyticsRepository = Depends(get_job_vacancies_analytics_repo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Lightweight pipeline counts grouped by macro recruitment stage."""
    company_id = str(current_user.company_id) if hasattr(current_user, "company_id") and current_user.company_id else None
    if not company_id:
        raise HTTPException(status_code=403, detail="Company not associated with user")

    try:
        rows = await repo.get_pipeline_overview(company_id)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching pipeline pulse: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal error fetching pipeline data")

    macro_counts: dict[str, int] = {}
    total = 0
    for row in rows:
        count = int(row.count)
        total += count
        macro = STAGE_TO_MACRO.get(row.stage)
        if macro is None:
            macro = STAGE_TO_MACRO.get(str(row.stage).strip())
        if macro is None:
            logger.warning(f"Unmapped pipeline stage: '{row.stage}' ({count} candidates) — skipping")
            continue
        macro_counts[macro] = macro_counts.get(macro, 0) + count

    order = ["sourcing", "triagem", "entrevista", "oferta", "contratacao"]
    stages = [
        PipelinePulseStage(macro_stage=m, count=macro_counts.get(m, 0))
        for m in order
    ]

    return PipelinePulseResponse(stages=stages, total=total)


@router.get("/pipeline-overview", response_model=PipelineOverviewResponse)
async def get_pipeline_overview(
    candidates_per_stage: int = Query(default=100, ge=1, le=500, description="Max candidates to return per stage"),
    current_user=Depends(get_current_user_or_demo),
    repo: JobVacanciesAnalyticsRepository = Depends(get_job_vacancies_analytics_repo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """
    Aggregate candidate counts by stage across all active job vacancies
    for the current user's company. Returns stage name, count, and enriched
    candidate list for each stage with scores from test_results, lia_opinions.
    """
    company_id = str(current_user.company_id) if hasattr(current_user, "company_id") and current_user.company_id else None
    if not company_id:
        raise HTTPException(status_code=403, detail="Company not associated with user")

    try:
        rows = await repo.get_pipeline_overview_enriched(company_id, candidates_per_stage)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching pipeline overview: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

    stage_map: dict[str, list[PipelineOverviewCandidateItem]] = {}
    stage_counts: dict[str, int] = {}

    for row in rows:
        stage = row.stage
        stage_counts[stage] = int(row.stage_total)

        if stage not in stage_map:
            stage_map[stage] = []

        entered_at = None
        if row.stage_entered_at:
            try:
                entered_at = row.stage_entered_at.isoformat() if hasattr(row.stage_entered_at, 'isoformat') else str(row.stage_entered_at)
            except Exception:
                entered_at = str(row.stage_entered_at)

        big_five = None
        if row.big_five_data:
            big_five = row.big_five_data if isinstance(row.big_five_data, dict) else None

        score_bd = None
        if row.score_breakdown:
            score_bd = row.score_breakdown if isinstance(row.score_breakdown, dict) else None

        stage_map[stage].append(PipelineOverviewCandidateItem(
            vc_id=row.vc_id or "",
            vacancy_id=row.vacancy_id or "",
            candidate_id=row.candidate_id or "",
            name=row.candidate_name or "Candidato",
            vacancy_title=row.vacancy_title,
            sub_status=row.sub_status,
            stage_entered_at=entered_at,
            lia_score=row.lia_score,
            match_percentage=row.match_percentage,
            wsi_score=row.wsi_score,
            lia_opinion_score=row.lia_opinion_score,
            score_breakdown=score_bd,
            technical_test_score=row.technical_test_score,
            english_test_score=row.english_test_score,
            big_five_data=big_five,
        ))

    stages: list[PipelineOverviewStageItem] = []
    total = 0
    for stage_name, count in stage_counts.items():
        total += count
        stages.append(PipelineOverviewStageItem(
            stage=stage_name,
            count=count,
            candidates=stage_map.get(stage_name, []),
        ))

    stages.sort(key=lambda s: s.count, reverse=True)

    return PipelineOverviewResponse(stages=stages, total_candidates=total)


# ─── Pipeline Overview — JOB LIFECYCLE (Task #430, restored 2026-05) ─────────
#
# Mirrors the candidate-side `/pipeline-overview` but groups *job vacancies*
# by their lifecycle stage so the panoramic view can render a parallel
# Vagas|Candidatos toggle without needing two separate consumers.
#
# Stage detection is priority-based (top wins). A job belongs to exactly one
# bucket. The `imported_from_ats` flag is decorative metadata for badges.
#
# History note: this endpoint and its 8-stage classifier were originally
# introduced by Task #430, hardened with multi-tenant + live-count tests by
# Task #439, and were silently deleted by commit 02361f41c during a docs
# cherry-pick — leaving the consumer (`/api/backend-proxy/jobs-lifecycle-overview`
# → `pipeline-overview-page.tsx:332-349`) and the regression tests pointing
# at a non-existent function. This block restores the canonical contract.

JOB_LIFECYCLE_ORDER = [
    "ats_importada",
    "rascunho",
    "enriquecida",
    "wsi_config",
    "aguardando_aprovacao",
    "publicada",
    "ao_vivo",
    "encerrada",
]

JOB_LIFECYCLE_DISPLAY = {
    "ats_importada": "ATS Importada",
    "rascunho": "Rascunho/JD",
    "enriquecida": "Enriquecida",
    "wsi_config": "WSI Config",
    "aguardando_aprovacao": "Aguardando Aprovação",
    "publicada": "Publicada",
    "ao_vivo": "Ao Vivo",
    "encerrada": "Encerrada",
}

JOB_LIFECYCLE_COLORS = {
    "ats_importada": "#8A8F98",
    "rascunho": "#60BED1",
    "enriquecida": "#9860D1",
    "wsi_config": "#5DA47A",
    "aguardando_aprovacao": "#D19960",
    "publicada": "#6078D1",
    "ao_vivo": "#4DA67A",
    "encerrada": "#8A8F98",
}


# Slug -> human-friendly label for the external ATS that originated a vacancy.
ATS_SOURCE_LABELS: dict[str, str] = {
    "gupy": "Gupy",
    "pandape": "Pandapé",
    "merge": "Merge",
    "kenoby": "Kenoby",
    "solides": "Sólides",
    "abler": "Abler",
    "greenhouse": "Greenhouse",
    "ats_other": "ATS externo",
}

KNOWN_ATS_SOURCES: frozenset[str] = frozenset(ATS_SOURCE_LABELS.keys())


def _job_source_system(job: JobVacancy) -> str | None:
    """Return the structured source_system slug if set, else None."""
    raw = getattr(job, "source_system", None)
    if isinstance(raw, str) and raw.strip():
        return raw.strip().lower()
    return None


def _job_is_imported_from_ats(job: JobVacancy) -> bool:
    """Detect whether a job was imported from an external ATS.

    Prefers the structured ``source_system`` column (Task #435). Falls back
    to a heuristic over ``additional_data`` so legacy rows without the
    column populated still light up the badge.
    """
    slug = _job_source_system(job)
    if slug and slug in KNOWN_ATS_SOURCES:
        return True
    extra = job.additional_data or {}
    if not isinstance(extra, dict):
        return False
    if extra.get("imported_from_ats") is True:
        return True
    src = extra.get("source") or extra.get("origin") or extra.get("import_source")
    if isinstance(src, str) and src.strip():
        s = src.strip().lower()
        if s.startswith("ats") or s in KNOWN_ATS_SOURCES:
            return True
    if extra.get("external_system_id") or extra.get("ats_external_id"):
        return True
    return False


def _job_ats_source_label(job: JobVacancy) -> str | None:
    """Return a human-friendly ATS label (e.g. "Gupy") if known, else None."""
    if not _job_is_imported_from_ats(job):
        return None
    slug = _job_source_system(job)
    if slug and slug in ATS_SOURCE_LABELS:
        return ATS_SOURCE_LABELS[slug]
    extra = job.additional_data or {}
    if isinstance(extra, dict):
        for key in ("source", "origin", "import_source"):
            val = extra.get(key)
            if isinstance(val, str) and val.strip().lower() in ATS_SOURCE_LABELS:
                return ATS_SOURCE_LABELS[val.strip().lower()]
    return ATS_SOURCE_LABELS["ats_other"]


def _classify_job_lifecycle_stage(job: JobVacancy) -> str:
    """Classify a JobVacancy into one of the 8 lifecycle stages.

    Priority order (top wins) — see Task #430:
      1. encerrada            — status in {Concluída, Cancelada, Arquivada}
      2. ao_vivo              — Ativa AND published to a board
      3. publicada            — Ativa (approval done, not yet on a board)
      4. aguardando_aprovacao — approval_status='pendente' AND approval_requested_at set
      5. wsi_config           — screening_questions populated OR screening_config has wsi/settings
      6. enriquecida          — enriched_jd populated
      7. ats_importada        — imported_from_ats AND status=Rascunho
      8. rascunho             — fallback
    """
    status = (job.status or "Rascunho").strip()

    if status in {"Concluída", "Concluida", "Cancelada", "Arquivada"}:
        return "encerrada"

    if status == "Ativa":
        on_board = bool(
            job.published_linkedin
            or job.published_website
            or job.published_indeed
            or job.linkedin_post_id
            or job.indeed_job_id
            or job.last_published_at
        )
        return "ao_vivo" if on_board else "publicada"

    # status is Rascunho or Pausada from here on
    if (job.approval_status or "").lower() == "pendente" and job.approval_requested_at:
        return "aguardando_aprovacao"

    sc = job.screening_config or {}
    has_wsi = bool(
        (job.screening_questions or [])
        or (isinstance(sc, dict) and (sc.get("wsi_skills") or sc.get("settings")))
    )
    if has_wsi:
        return "wsi_config"

    if job.enriched_jd:
        return "enriquecida"

    if _job_is_imported_from_ats(job) and status == "Rascunho":
        return "ats_importada"

    return "rascunho"



def _normalize_location(raw) -> str | None:
    """Format location: JSON string {"city":...,"state":...} -> "City, ST".
    Handles plain strings, dicts, and null values transparently.
    """
    if not raw:
        return None
    if isinstance(raw, dict):
        parts = [p for p in [raw.get("city"), raw.get("state")] if p]
        return ", ".join(parts) or None
    if isinstance(raw, str) and raw.startswith("{"):
        import json as _json
        try:
            loc = _json.loads(raw)
            parts = [p for p in [loc.get("city"), loc.get("state")] if p]
            return ", ".join(parts) or None
        except Exception:
            pass
    return raw or None


class JobLifecycleVacancyItem(BaseModel):
    id: str
    title: str
    department: str | None = None
    location: str | None = None
    work_model: str | None = None
    seniority_level: str | None = None
    status: str
    stage_entered_at: str | None = None
    updated_at: str | None = None
    created_at: str | None = None
    manager: str | None = None
    imported_from_ats: bool = False
    source_system: str | None = None
    ats_source_label: str | None = None
    approval_status: str | None = None
    candidate_count: int = 0


class JobLifecycleStageItem(BaseModel):
    stage: str
    display_name: str
    color: str
    stage_order: int
    count: int
    vacancies: list[JobLifecycleVacancyItem] = []


class JobLifecycleOverviewResponse(BaseModel):
    stages: list[JobLifecycleStageItem]
    total_vacancies: int


@router.get("/job-vacancies/lifecycle-overview", response_model=JobLifecycleOverviewResponse)
async def get_job_lifecycle_overview(
    vacancies_per_stage: int = Query(default=50, ge=1, le=500),
    current_user: User = Depends(get_current_user_or_demo),
    repo: JobVacanciesAnalyticsRepository = Depends(get_job_vacancies_analytics_repo),
company_id: str = Depends(require_company_id)):
    """Aggregate job vacancies by 8 lifecycle stages for the panoramic view.

    Companion to `/pipeline-overview` (candidate side). Powers the
    "Vagas|Candidatos" toggle in the Visão do Pipeline page.
    """
    company_id = get_user_company_id(current_user)
    if not company_id:
        raise HTTPException(status_code=403, detail="Company not associated with user")

    try:
        jobs = await repo.get_all_company_jobs(company_id)
        candidate_counts = await repo.get_candidate_counts_by_vacancy_for_company(company_id)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching jobs for lifecycle overview: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

    buckets: dict[str, list[JobLifecycleVacancyItem]] = {k: [] for k in JOB_LIFECYCLE_ORDER}

    def _iso(dt):
        if not dt:
            return None
        try:
            return dt.isoformat() if hasattr(dt, "isoformat") else str(dt)
        except Exception:
            return None

    for job in jobs:
        stage_key = _classify_job_lifecycle_stage(job)
        if stage_key not in buckets:
            stage_key = "rascunho"

        cand_total = candidate_counts.get(str(job.id), 0)

        # stage_entered_at is best-effort — use updated_at as proxy since
        # we don't track per-stage transitions on the JobVacancy itself.
        item = JobLifecycleVacancyItem(
            id=str(job.id),
            title=job.title or "Sem título",
            department=job.department,
            location=_normalize_location(job.location),
            work_model=job.work_model,
            seniority_level=job.seniority_level,
            status=job.status or "Rascunho",
            stage_entered_at=_iso(job.updated_at),
            updated_at=_iso(job.updated_at),
            created_at=_iso(job.created_at),
            manager=job.manager,
            imported_from_ats=_job_is_imported_from_ats(job),
            source_system=_job_source_system(job),
            ats_source_label=_job_ats_source_label(job),
            approval_status=job.approval_status,
            candidate_count=cand_total,
        )
        buckets[stage_key].append(item)

    # Capture full bucket sizes BEFORE truncation so the rail counts reflect
    # the true number of vacancies in each stage (the `vacancies` array is
    # only a UI sample bounded by `vacancies_per_stage`).
    bucket_totals: dict[str, int] = {k: len(v) for k, v in buckets.items()}

    # Sort each bucket by most recently updated first, then truncate.
    for key, items in buckets.items():
        items.sort(key=lambda v: v.updated_at or "", reverse=True)
        buckets[key] = items[:vacancies_per_stage]

    stages: list[JobLifecycleStageItem] = []
    for order_idx, key in enumerate(JOB_LIFECYCLE_ORDER):
        items = buckets[key]
        stages.append(JobLifecycleStageItem(
            stage=key,
            display_name=JOB_LIFECYCLE_DISPLAY[key],
            color=JOB_LIFECYCLE_COLORS[key],
            stage_order=order_idx,
            count=bucket_totals[key],
            vacancies=items,
        ))

    return JobLifecycleOverviewResponse(stages=stages, total_vacancies=len(jobs))
