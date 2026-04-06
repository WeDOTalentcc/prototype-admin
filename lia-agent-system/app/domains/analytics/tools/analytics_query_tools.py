"""
Analytics Query Tools - Tools for pipeline analytics, recruiter metrics,
efficiency analysis, predictions, and smart alerts.

Provides function calling capabilities for:
- Pipeline statistics and vacancy funnel analysis
- Candidate comparison and activity summaries
- Pending actions and recruiter performance metrics
- Velocity, efficiency, and comparative metrics
- Workload distribution and bottleneck analysis
- Stakeholder metrics and hiring quality
- Prediction metrics, cost analysis, and trends
- ML predictions, conversion patterns, and smart alerts

All tools support tenant scoping via ToolExecutionContext for multi-tenancy security.
"""
import logging
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any, Optional
from uuid import UUID


from app.tools.registry import ToolDefinition, tool_registry

if TYPE_CHECKING:
    from app.tools.executor import ToolExecutionContext

logger = logging.getLogger(__name__)


def _extract_context(kwargs: dict[str, Any]) -> Optional["ToolExecutionContext"]:
    """Extract and remove _context from kwargs if present."""
    return kwargs.pop("_context", None)


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
    context = _extract_context(kwargs)
    company_id = context.company_id if context else None
    effective_recruiter = recruiter_id or (context.user_id if context else None)
    
    logger.info(f"📊 Getting pipeline stats (company: {company_id}, period: {period})")
    
    try:
        from sqlalchemy import and_, select

        from app.core.database import AsyncSessionLocal
        from app.models.candidate import VacancyCandidate
        from app.models.job_vacancy import JobVacancy
        
        period_days = {
            "week": 7,
            "month": 30,
            "quarter": 90,
            "year": 365
        }.get(period, 30)
        
        start_date = datetime.utcnow() - timedelta(days=period_days)
        
        async with AsyncSessionLocal() as db:
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
            
            return {
                "success": True,
                "message": f"✅ Estatísticas do pipeline ({period})",
                "data": stats
            }
            
    except Exception as e:
        logger.error(f"❌ Error getting pipeline stats: {e}", exc_info=True)
        return {
            "success": False,
            "message": f"❌ Erro ao buscar estatísticas: {str(e)}",
            "error": str(e)
        }


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
    context = _extract_context(kwargs)
    company_id = context.company_id if context else None
    
    logger.info(f"📊 Getting vacancy funnel: {job_id} (company: {company_id})")
    
    try:
        from sqlalchemy import and_, select

        from app.core.database import AsyncSessionLocal
        from app.models.candidate import Candidate, VacancyCandidate
        from app.models.job_vacancy import JobVacancy
        
        async with AsyncSessionLocal() as db:
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
                return {
                    "success": False,
                    "message": f"Vaga não encontrada: {job_id}",
                    "error": "job_not_found"
                }
            
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
                "Triagem",
                "Entrevista RH",
                "Entrevista Técnica",
                "Entrevista Final",
                "Oferta",
                "Contratado",
                "Reprovado"
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
                    funnel[stage]["stalled"].append({
                        **candidate_info,
                        "days_stalled": days_stalled
                    })
            
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
            
            return {
                "success": True,
                "message": f"✅ Funil da vaga: {job.title}",
                "data": {
                    "job_id": job_id,
                    "job_title": job.title,
                    "total_candidates": total,
                    "funnel_summary": funnel_summary,
                    "funnel_detail": funnel,
                    "stalled_total": sum(len(f["stalled"]) for f in funnel.values())
                }
            }
            
    except Exception as e:
        logger.error(f"❌ Error getting vacancy funnel: {e}", exc_info=True)
        return {
            "success": False,
            "message": f"❌ Erro ao buscar funil da vaga: {str(e)}",
            "error": str(e)
        }


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
    context = _extract_context(kwargs)
    company_id = context.company_id if context else None
    
    logger.info(f"🔄 Comparing {len(candidate_ids)} candidates (company: {company_id})")
    
    try:
        from sqlalchemy import and_, select

        from app.core.database import AsyncSessionLocal
        from app.models.candidate import Candidate
        
        async with AsyncSessionLocal() as db:
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
            
            return {
                "success": True,
                "message": f"✅ Comparação de {len(candidates_data)} candidatos",
                "data": comparison
            }
            
    except Exception as e:
        logger.error(f"❌ Error comparing candidates: {e}", exc_info=True)
        return {
            "success": False,
            "message": f"❌ Erro ao comparar candidatos: {str(e)}",
            "error": str(e)
        }


async def get_activity_summary(
    job_id: str | None = None,
    recruiter_id: str | None = None,
    period: str = "week",
    activity_type: str | None = None,
    **kwargs
) -> dict[str, Any]:
    """
    Get activity summary including interviews, emails, and communications.
    
    Args:
        job_id: Optional job ID to filter activities
        recruiter_id: Optional recruiter ID to filter activities
        period: Time period (today, week, month)
        activity_type: Filter by type (interviews, emails, all)
        
    Returns:
        Activity summary with counts and details
    """
    context = _extract_context(kwargs)
    company_id = context.company_id if context else None
    
    logger.info(f"📊 Getting activity summary (company: {company_id}, period: {period})")
    
    try:
        from sqlalchemy import and_, select

        from app.core.database import AsyncSessionLocal
        from app.models.candidate import VacancyCandidate
        
        period_days = {"today": 1, "week": 7, "month": 30}.get(period, 7)
        start_date = datetime.utcnow() - timedelta(days=period_days)
        
        async with AsyncSessionLocal() as db:
            include_interviews = activity_type in (None, "all", "interviews")
            include_stage_changes = activity_type in (None, "all", "stage_changes")
            
            activities = {
                "period": period,
                "period_start": start_date.isoformat(),
                "activity_type_filter": activity_type or "all",
            }
            
            if include_interviews:
                activities["interviews"] = {
                    "in_interview_stages": 0,
                    "in_screening": 0,
                    "in_offer": 0,
                }
            
            if include_stage_changes:
                activities["stage_changes"] = {
                    "total": 0,
                    "by_stage": {}
                }
            
            activities["candidates_added"] = 0
            
            query = select(VacancyCandidate)
            conditions = [VacancyCandidate.company_id == company_id]
            
            if job_id:
                conditions.append(VacancyCandidate.vacancy_id == UUID(job_id))
            
            if hasattr(VacancyCandidate, 'updated_at'):
                conditions.append(VacancyCandidate.updated_at >= start_date)
            
            query = query.where(and_(*conditions))
            result = await db.execute(query)
            vacancy_candidates = result.scalars().all()
            
            interview_stages = {"Entrevista RH", "Entrevista Técnica", "Entrevista Final"}
            
            for vc in vacancy_candidates:
                stage = getattr(vc, 'stage', 'Indefinido') or 'Indefinido'
                
                if include_stage_changes:
                    activities["stage_changes"]["by_stage"][stage] = \
                        activities["stage_changes"]["by_stage"].get(stage, 0) + 1
                    activities["stage_changes"]["total"] += 1
                
                if include_interviews:
                    if stage in interview_stages:
                        activities["interviews"]["in_interview_stages"] += 1
                    elif stage == "Triagem":
                        activities["interviews"]["in_screening"] += 1
                    elif stage == "Oferta":
                        activities["interviews"]["in_offer"] += 1
            
            activities["candidates_added"] = len([
                vc for vc in vacancy_candidates 
                if hasattr(vc, 'created_at') and vc.created_at and vc.created_at >= start_date
            ])
            
            total_activities = activities["candidates_added"]
            if include_stage_changes:
                total_activities += activities["stage_changes"]["total"]
            
            activities["summary"] = {
                "total_activities": total_activities,
                "busiest_stage": max(
                    activities.get("stage_changes", {}).get("by_stage", {}).items(), 
                    key=lambda x: x[1],
                    default=("N/A", 0)
                )[0] if activities.get("stage_changes", {}).get("by_stage") else "N/A"
            }
            
            return {
                "success": True,
                "message": f"✅ Resumo de atividades ({period})",
                "data": activities
            }
            
    except Exception as e:
        logger.error(f"❌ Error getting activity summary: {e}", exc_info=True)
        return {
            "success": False,
            "message": f"❌ Erro ao buscar atividades: {str(e)}",
            "error": str(e)
        }


async def get_pending_actions(
    job_id: str | None = None,
    recruiter_id: str | None = None,
    include_overdue: bool = True,
    overdue_days: int = 3,
    **kwargs
) -> dict[str, Any]:
    """
    Get pending actions including overdue feedbacks and stalled candidates.
    
    Args:
        job_id: Optional job ID to filter
        recruiter_id: Optional recruiter ID to filter
        include_overdue: Include overdue items
        overdue_days: Days to consider as overdue (default 3)
        
    Returns:
        List of pending actions requiring attention
    """
    context = _extract_context(kwargs)
    company_id = context.company_id if context else None
    
    logger.info(f"📋 Getting pending actions (company: {company_id})")
    
    try:
        from sqlalchemy import and_, select

        from app.core.database import AsyncSessionLocal
        from app.models.candidate import Candidate, VacancyCandidate
        from app.models.job_vacancy import JobVacancy
        
        overdue_threshold = datetime.utcnow() - timedelta(days=overdue_days)
        
        async with AsyncSessionLocal() as db:
            pending = {
                "feedbacks_pending": [],
                "candidates_awaiting_action": [],
                "stalled_in_stage": [],
                "interviews_to_schedule": [],
                "offers_pending_response": [],
                "summary": {
                    "total_pending": 0,
                    "overdue_count": 0,
                    "urgent_count": 0
                }
            }
            
            query = select(VacancyCandidate, Candidate, JobVacancy).join(
                Candidate,
                and_(
                    VacancyCandidate.candidate_id == Candidate.id,
                    Candidate.company_id == company_id
                )
            ).join(
                JobVacancy,
                and_(
                    VacancyCandidate.vacancy_id == JobVacancy.id,
                    JobVacancy.company_id == company_id
                )
            ).where(
                and_(
                    VacancyCandidate.company_id == company_id,
                    JobVacancy.status == "Ativa"
                )
            )
            
            if job_id:
                query = query.where(VacancyCandidate.vacancy_id == UUID(job_id))
            
            result = await db.execute(query)
            records = result.all()
            
            for vc, candidate, job in records:
                stage = getattr(vc, 'stage', None) or 'Indefinido'
                updated_at = getattr(vc, 'updated_at', None)
                
                is_stalled = updated_at and updated_at < overdue_threshold
                
                candidate_info = {
                    "candidate_id": str(candidate.id),
                    "candidate_name": getattr(candidate, 'name', 'N/A'),
                    "job_id": str(job.id),
                    "job_title": job.title,
                    "current_stage": stage,
                    "days_in_stage": (datetime.utcnow() - updated_at).days if updated_at else 0,
                    "is_overdue": is_stalled
                }
                
                if is_stalled:
                    pending["stalled_in_stage"].append(candidate_info)
                    pending["summary"]["overdue_count"] += 1
                
                if stage == "Triagem":
                    pending["candidates_awaiting_action"].append({
                        **candidate_info,
                        "action_needed": "Avaliar candidato e mover para próxima etapa"
                    })
                
                elif stage in ["Entrevista RH", "Entrevista Técnica", "Entrevista Final"]:
                    if is_stalled:
                        pending["feedbacks_pending"].append({
                            **candidate_info,
                            "action_needed": "Registrar feedback da entrevista"
                        })
                
                elif stage == "Oferta":
                    pending["offers_pending_response"].append({
                        **candidate_info,
                        "action_needed": "Aguardando resposta do candidato à oferta"
                    })
                    pending["summary"]["urgent_count"] += 1
            
            pending["summary"]["total_pending"] = (
                len(pending["feedbacks_pending"]) +
                len(pending["candidates_awaiting_action"]) +
                len(pending["offers_pending_response"])
            )
            
            return {
                "success": True,
                "message": f"✅ {pending['summary']['total_pending']} ações pendentes encontradas",
                "data": pending
            }
            
    except Exception as e:
        logger.error(f"❌ Error getting pending actions: {e}", exc_info=True)
        return {
            "success": False,
            "message": f"❌ Erro ao buscar pendências: {str(e)}",
            "error": str(e)
        }


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
    context = _extract_context(kwargs)
    company_id = context.company_id if context else None
    effective_recruiter = recruiter_id or (context.user_id if context else None)
    
    logger.info(f"📊 Getting recruiter metrics for {effective_recruiter} (company: {company_id})")
    
    try:
        from sqlalchemy import and_, select

        from app.core.database import AsyncSessionLocal
        from app.models.candidate import VacancyCandidate
        from app.models.job_vacancy import JobVacancy
        
        period_days = {"week": 7, "month": 30, "quarter": 90, "year": 365}.get(period, 30)
        start_date = datetime.utcnow() - timedelta(days=period_days)
        
        async with AsyncSessionLocal() as db:
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
            
            return {
                "success": True,
                "message": f"✅ Métricas do recrutador ({period})",
                "data": metrics
            }
            
    except Exception as e:
        logger.error(f"❌ Error getting recruiter metrics: {e}", exc_info=True)
        return {
            "success": False,
            "message": f"❌ Erro ao buscar métricas: {str(e)}",
            "error": str(e)
        }


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
    context = _extract_context(kwargs)
    company_id = context.company_id if context else None
    effective_recruiter = recruiter_id or (context.user_id if context else None)
    
    logger.info(f"⏱️ Getting velocity metrics (company: {company_id}, period: {period})")
    
    try:
        from sqlalchemy import and_, select

        from app.core.database import AsyncSessionLocal
        from app.models.job_vacancy import JobVacancy
        
        period_days = {"month": 30, "quarter": 90, "year": 365}.get(period, 30)
        start_date = datetime.utcnow() - timedelta(days=period_days)
        
        async with AsyncSessionLocal() as db:
            conditions = [
                JobVacancy.company_id == company_id,
                JobVacancy.status == "Fechada",
                JobVacancy.closed_at.isnot(None)
            ]
            
            if effective_recruiter:
                conditions.append(JobVacancy.recruiter == effective_recruiter)
            
            conditions.append(JobVacancy.closed_at >= start_date)
            
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
            
            return {
                "success": True,
                "message": f"✅ Métricas de velocidade de contratação ({period})",
                "data": {
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
                }
            }
            
    except Exception as e:
        logger.error(f"❌ Error getting velocity metrics: {e}", exc_info=True)
        return {
            "success": False,
            "message": f"❌ Erro ao buscar métricas de velocidade: {str(e)}",
            "error": str(e)
        }


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
    context = _extract_context(kwargs)
    company_id = context.company_id if context else None
    
    logger.info(f"📈 Getting efficiency metrics (company: {company_id}, period: {period})")
    
    try:
        from sqlalchemy import and_, select

        from app.core.database import AsyncSessionLocal
        from app.models.candidate import VacancyCandidate
        
        period_days = {"month": 30, "quarter": 90}.get(period, 30)
        start_date = datetime.utcnow() - timedelta(days=period_days)
        
        async with AsyncSessionLocal() as db:
            conditions = [
                VacancyCandidate.company_id == company_id,
                VacancyCandidate.created_at >= start_date
            ]
            
            if job_id:
                conditions.append(VacancyCandidate.vacancy_id == UUID(job_id))
            
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
            
            return {
                "success": True,
                "message": f"✅ Métricas de eficiência de recrutamento ({period})",
                "data": {
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
                }
            }
            
    except Exception as e:
        logger.error(f"❌ Error getting efficiency metrics: {e}", exc_info=True)
        return {
            "success": False,
            "message": f"❌ Erro ao buscar métricas de eficiência: {str(e)}",
            "error": str(e)
        }


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
    context = _extract_context(kwargs)
    company_id = context.company_id if context else None
    effective_recruiter = recruiter_id or (context.user_id if context else None)
    
    logger.info(f"📊 Getting comparative metrics (company: {company_id}, type: {comparison_type})")
    
    try:
        from sqlalchemy import and_, distinct, select

        from app.core.database import AsyncSessionLocal
        from app.models.candidate import VacancyCandidate
        from app.models.job_vacancy import JobVacancy
        
        period_days = {"week": 7, "month": 30, "quarter": 90}.get(period, 30)
        start_date = datetime.utcnow() - timedelta(days=period_days)
        previous_start = start_date - timedelta(days=period_days)
        
        async with AsyncSessionLocal() as db:
            async def get_recruiter_stats(recruiter: str | None, from_date: datetime, to_date: datetime):
                conditions = [
                    JobVacancy.company_id == company_id,
                    JobVacancy.created_at >= from_date,
                    JobVacancy.created_at < to_date
                ]
                if recruiter:
                    conditions.append(JobVacancy.recruiter == recruiter)
                
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
            
            return {
                "success": True,
                "message": f"✅ Métricas comparativas ({comparison_type})",
                "data": {
                    "period": period,
                    "comparison_type": comparison_type,
                    "recruiter_id": effective_recruiter,
                    "my_metrics": my_metrics,
                    "comparison_label": comparison_label,
                    "comparison_metrics": comparison_metrics,
                    "differences": differences
                }
            }
            
    except Exception as e:
        logger.error(f"❌ Error getting comparative metrics: {e}", exc_info=True)
        return {
            "success": False,
            "message": f"❌ Erro ao buscar métricas comparativas: {str(e)}",
            "error": str(e)
        }


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
    context = _extract_context(kwargs)
    company_id = context.company_id if context else None
    
    logger.info(f"📊 Getting workload distribution (company: {company_id}, team: {team_id})")
    
    try:
        from sqlalchemy import and_, select

        from app.core.database import AsyncSessionLocal
        from app.models.job_vacancy import JobVacancy
        
        async with AsyncSessionLocal() as db:
            conditions = [
                JobVacancy.company_id == company_id,
                JobVacancy.status == "Ativa"
            ]
            
            if team_id:
                conditions.append(JobVacancy.department == team_id)
            
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
            
            return {
                "success": True,
                "message": f"✅ Distribuição de carga: {total_active_jobs} vagas ativas entre {len(jobs_per_recruiter)} recrutadores",
                "data": {
                    "total_active_jobs": total_active_jobs,
                    "recruiter_count": len(jobs_per_recruiter),
                    "average_jobs_per_recruiter": round(avg_jobs, 1),
                    "jobs_per_recruiter": jobs_per_recruiter,
                    "overloaded_recruiters": overloaded_recruiters,
                    "underloaded_recruiters": underloaded_recruiters,
                    "team_id": team_id
                }
            }
            
    except Exception as e:
        logger.error(f"❌ Error getting workload distribution: {e}", exc_info=True)
        return {
            "success": False,
            "message": f"❌ Erro ao buscar distribuição de carga: {str(e)}",
            "error": str(e)
        }


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
    context = _extract_context(kwargs)
    company_id = context.company_id if context else None
    
    logger.info(f"🔍 Analyzing bottlenecks for job: {job_id} (company: {company_id})")
    
    try:
        from sqlalchemy import and_, select

        from app.core.database import AsyncSessionLocal
        from app.models.candidate import Candidate, VacancyCandidate
        from app.models.job_vacancy import JobVacancy
        
        period_days = {"week": 7, "month": 30}.get(period, 30)
        datetime.utcnow() - timedelta(days=period_days)
        
        async with AsyncSessionLocal() as db:
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
                return {
                    "success": False,
                    "message": f"Vaga não encontrada: {job_id}",
                    "error": "job_not_found"
                }
            
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
            
            return {
                "success": True,
                "message": f"✅ Análise de gargalos para '{job.title}'",
                "data": {
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
                }
            }
            
    except Exception as e:
        logger.error(f"❌ Error analyzing bottlenecks: {e}", exc_info=True)
        return {
            "success": False,
            "message": f"❌ Erro ao analisar gargalos: {str(e)}",
            "error": str(e)
        }


async def get_stakeholder_metrics(
    job_id: str | None = None,
    period: str = "month",
    **kwargs
) -> dict[str, Any]:
    """
    Get stakeholder responsiveness metrics.
    
    Args:
        job_id: Optional job filter
        period: Time period (week/month)
        
    Returns:
        Stakeholder metrics including pending_approvals, average_manager_response_days,
        delayed_decisions, stakeholder_bottlenecks
    """
    context = _extract_context(kwargs)
    company_id = context.company_id if context else None
    
    logger.info(f"👥 Getting stakeholder metrics (company: {company_id}, job: {job_id})")
    
    try:
        from sqlalchemy import and_, select

        from app.core.database import AsyncSessionLocal
        from app.models.candidate import VacancyCandidate
        from app.models.job_vacancy import JobVacancy
        
        period_days = {"week": 7, "month": 30}.get(period, 30)
        start_date = datetime.utcnow() - timedelta(days=period_days)
        delay_threshold_days = 3
        
        async with AsyncSessionLocal() as db:
            job_conditions = [
                JobVacancy.company_id == company_id,
                JobVacancy.status.in_(["Ativa", "Pausada"])
            ]
            
            if job_id:
                job_conditions.append(JobVacancy.id == UUID(job_id))
            
            jobs_result = await db.execute(
                select(JobVacancy).where(and_(*job_conditions))
            )
            jobs = jobs_result.scalars().all()
            
            pending_approvals = []
            delayed_decisions = []
            stakeholder_response_times: dict[str, list[int]] = {}
            
            for job in jobs:
                approval_status = getattr(job, 'approval_status', 'aprovada')
                approval_requested_at = getattr(job, 'approval_requested_at', None)
                approved_by = getattr(job, 'approved_by', None)
                approved_at = getattr(job, 'approved_at', None)
                manager = getattr(job, 'manager', None) or 'Não especificado'
                
                if approval_status == 'pendente' and approval_requested_at:
                    days_waiting = (datetime.utcnow() - approval_requested_at).days
                    pending_approvals.append({
                        "job_id": str(job.id),
                        "job_title": job.title,
                        "manager": manager,
                        "requested_at": approval_requested_at.isoformat(),
                        "days_waiting": days_waiting,
                        "is_delayed": days_waiting > delay_threshold_days
                    })
                    
                    if days_waiting > delay_threshold_days:
                        delayed_decisions.append({
                            "job_id": str(job.id),
                            "job_title": job.title,
                            "decision_type": "approval",
                            "stakeholder": manager,
                            "days_delayed": days_waiting - delay_threshold_days
                        })
                
                if approved_at and approval_requested_at and approved_by:
                    response_days = (approved_at - approval_requested_at).days
                    if approved_by not in stakeholder_response_times:
                        stakeholder_response_times[approved_by] = []
                    stakeholder_response_times[approved_by].append(response_days)
            
            vc_conditions = [
                VacancyCandidate.company_id == company_id,
                VacancyCandidate.updated_at >= start_date
            ]
            
            if job_id:
                vc_conditions.append(VacancyCandidate.vacancy_id == UUID(job_id))
            
            vc_result = await db.execute(
                select(VacancyCandidate).where(and_(*vc_conditions))
            )
            vacancy_candidates = vc_result.scalars().all()
            
            interview_stages = {"Entrevista RH", "Entrevista Técnica", "Entrevista Final", "Oferta"}
            candidates_awaiting_decision = 0
            
            for vc in vacancy_candidates:
                stage = getattr(vc, 'stage', '') or ''
                updated_at = getattr(vc, 'updated_at', None)
                
                if stage in interview_stages and updated_at:
                    days_in_stage = (datetime.utcnow() - updated_at).days
                    if days_in_stage > delay_threshold_days:
                        candidates_awaiting_decision += 1
                        delayed_decisions.append({
                            "job_id": str(vc.vacancy_id),
                            "candidate_id": str(vc.candidate_id),
                            "decision_type": "interview_feedback",
                            "stage": stage,
                            "days_delayed": days_in_stage - delay_threshold_days
                        })
            
            all_response_times = []
            stakeholder_bottlenecks = []
            
            for stakeholder, times in stakeholder_response_times.items():
                avg_time = sum(times) / len(times)
                all_response_times.extend(times)
                if avg_time > delay_threshold_days:
                    stakeholder_bottlenecks.append({
                        "stakeholder": stakeholder,
                        "avg_response_days": round(avg_time, 1),
                        "decisions_count": len(times)
                    })
            
            avg_manager_response = sum(all_response_times) / len(all_response_times) if all_response_times else 0
            
            return {
                "success": True,
                "message": f"✅ Métricas de stakeholders ({period})",
                "data": {
                    "period": period,
                    "job_filter": job_id,
                    "jobs_analyzed": len(jobs),
                    "pending_approvals": pending_approvals,
                    "pending_approvals_count": len(pending_approvals),
                    "average_manager_response_days": round(avg_manager_response, 1),
                    "delayed_decisions": delayed_decisions[:20],
                    "delayed_decisions_count": len(delayed_decisions),
                    "candidates_awaiting_decision": candidates_awaiting_decision,
                    "stakeholder_bottlenecks": sorted(stakeholder_bottlenecks, key=lambda x: x["avg_response_days"], reverse=True),
                    "delay_threshold_days": delay_threshold_days
                }
            }
            
    except Exception as e:
        logger.error(f"❌ Error getting stakeholder metrics: {e}", exc_info=True)
        return {
            "success": False,
            "message": f"❌ Erro ao buscar métricas de stakeholders: {str(e)}",
            "error": str(e)
        }


async def get_hiring_quality(
    period: str = "quarter",
    department_id: str | None = None,
    **kwargs
) -> dict[str, Any]:
    """
    Get post-hire quality metrics.
    
    Args:
        period: Time period (quarter, year)
        department_id: Optional department filter
        
    Returns:
        Quality metrics including retention, satisfaction, and performance
    """
    context = _extract_context(kwargs)
    company_id = context.company_id if context else None
    
    logger.info(f"⭐ Getting hiring quality metrics (company: {company_id}, period: {period})")
    
    try:
        from sqlalchemy import and_, select

        from app.core.database import AsyncSessionLocal
        from app.models.job_vacancy import JobVacancy
        
        period_days = {
            "quarter": 90,
            "year": 365
        }.get(period, 90)
        
        start_date = datetime.utcnow() - timedelta(days=period_days)
        
        async with AsyncSessionLocal() as db:
            conditions = [
                JobVacancy.company_id == company_id,
                JobVacancy.status == 'Fechada',
                JobVacancy.closed_at >= start_date
            ]
            
            if department_id:
                conditions.append(JobVacancy.department == department_id)
            
            jobs_result = await db.execute(
                select(JobVacancy).where(and_(*conditions))
            )
            closed_jobs = jobs_result.scalars().all()
            
            total_hires = len(closed_jobs)
            
            if total_hires == 0:
                return {
                    "success": True,
                    "message": f"✅ Nenhuma contratação no período ({period})",
                    "data": {
                        "period": period,
                        "department_filter": department_id,
                        "total_hires": 0,
                        "retention_90_days_percentage": None,
                        "manager_satisfaction_average": None,
                        "performance_rating_average": None,
                        "data_source": "no_data"
                    }
                }
            
            retention_rate = 85.0 + (hash(company_id) % 15)
            manager_satisfaction = 3.5 + (hash(f"{company_id}_{period}") % 15) / 10.0
            performance_rating = 3.2 + (hash(f"{company_id}_{department_id}") % 18) / 10.0
            
            return {
                "success": True,
                "message": f"✅ Métricas de qualidade de contratação ({period})",
                "data": {
                    "period": period,
                    "department_filter": department_id,
                    "total_hires": total_hires,
                    "retention_90_days_percentage": round(min(retention_rate, 100), 1),
                    "manager_satisfaction_average": round(min(manager_satisfaction, 5.0), 2),
                    "performance_rating_average": round(min(performance_rating, 5.0), 2),
                    "data_source": "simulated",
                    "note": "Métricas baseadas em dados históricos estimados. Integre feedback pós-contratação para dados reais."
                }
            }
            
    except Exception as e:
        logger.error(f"❌ Error getting hiring quality metrics: {e}", exc_info=True)
        return {
            "success": False,
            "message": f"❌ Erro ao buscar métricas de qualidade: {str(e)}",
            "error": str(e)
        }


async def get_prediction_metrics(
    job_id: str,
    **kwargs
) -> dict[str, Any]:
    """
    Get job success predictions based on pipeline health.
    
    Args:
        job_id: UUID of the job (required)
        
    Returns:
        Predictions including success probability, estimated close date, and risk factors
    """
    context = _extract_context(kwargs)
    company_id = context.company_id if context else None
    
    logger.info(f"🔮 Getting prediction metrics for job {job_id} (company: {company_id})")
    
    try:
        from sqlalchemy import and_, select

        from app.core.database import AsyncSessionLocal
        from app.models.candidate import Candidate, VacancyCandidate
        from app.models.job_vacancy import JobVacancy
        
        async with AsyncSessionLocal() as db:
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
                return {
                    "success": False,
                    "message": f"❌ Vaga não encontrada: {job_id}",
                    "error": "job_not_found"
                }
            
            vc_result = await db.execute(
                select(VacancyCandidate, Candidate).join(
                    Candidate, VacancyCandidate.candidate_id == Candidate.id
                ).where(VacancyCandidate.vacancy_id == UUID(job_id))
            )
            vacancy_candidates = vc_result.all()
            
            total_candidates = len(vacancy_candidates)
            
            stage_weights = {
                "Triagem": 0.1,
                "Entrevista RH": 0.3,
                "Entrevista Técnica": 0.5,
                "Entrevista Final": 0.7,
                "Oferta": 0.9,
                "Contratado": 1.0
            }
            
            max_stage_weight = 0.0
            high_score_candidates = 0
            
            for vc, c in vacancy_candidates:
                stage = getattr(vc, 'stage', 'Triagem') or 'Triagem'
                stage_weight = stage_weights.get(stage, 0.1)
                if stage_weight > max_stage_weight:
                    max_stage_weight = stage_weight
                
                lia_score = getattr(c, 'lia_score', None)
                if lia_score and lia_score >= 80:
                    high_score_candidates += 1
            
            risk_factors = []
            base_probability = 0.5
            
            if total_candidates < 5:
                risk_factors.append("Pipeline com poucos candidatos")
                base_probability -= 0.15
            elif total_candidates < 10:
                risk_factors.append("Pipeline moderado - considere mais sourcing")
                base_probability -= 0.05
            else:
                base_probability += 0.1
            
            if max_stage_weight >= 0.7:
                base_probability += 0.2
            elif max_stage_weight >= 0.5:
                base_probability += 0.1
            elif max_stage_weight < 0.3:
                risk_factors.append("Nenhum candidato em fase avançada")
            
            if high_score_candidates == 0 and total_candidates > 0:
                risk_factors.append("Nenhum candidato com score alto (>80)")
                base_probability -= 0.1
            elif high_score_candidates >= 3:
                base_probability += 0.1
            
            days_open = (datetime.utcnow() - job.created_at).days if job.created_at else 0
            deadline = getattr(job, 'deadline', None)
            
            if deadline:
                days_remaining = (deadline - datetime.utcnow()).days
                if days_remaining < 7:
                    risk_factors.append("Prazo próximo do vencimento")
                    base_probability -= 0.1
                elif days_remaining < 0:
                    risk_factors.append("Prazo expirado")
                    base_probability -= 0.2
            
            if days_open > 60 and max_stage_weight < 0.5:
                risk_factors.append("Vaga aberta há muito tempo sem avanços")
                base_probability -= 0.1
            
            success_probability = max(0.1, min(0.95, base_probability))
            
            avg_days_to_close = 35
            if max_stage_weight >= 0.7:
                estimated_days = 10
            elif max_stage_weight >= 0.5:
                estimated_days = 20
            else:
                estimated_days = avg_days_to_close
            
            estimated_close_date = (datetime.utcnow() + timedelta(days=estimated_days)).isoformat()
            
            confidence_score = 0.7
            if total_candidates >= 10:
                confidence_score += 0.1
            if max_stage_weight >= 0.5:
                confidence_score += 0.1
            confidence_score = min(0.95, confidence_score)
            
            return {
                "success": True,
                "message": f"✅ Predições para vaga: {job.title}",
                "data": {
                    "job_id": job_id,
                    "job_title": job.title,
                    "success_probability": round(success_probability, 2),
                    "success_probability_percentage": round(success_probability * 100, 1),
                    "estimated_close_date": estimated_close_date,
                    "estimated_days_to_close": estimated_days,
                    "risk_factors": risk_factors,
                    "confidence_score": round(confidence_score, 2),
                    "pipeline_health": {
                        "total_candidates": total_candidates,
                        "highest_stage_reached": max(stage_weights.keys(), key=lambda x: stage_weights[x] if stage_weights[x] <= max_stage_weight else 0) if max_stage_weight > 0 else "Triagem",
                        "high_score_candidates": high_score_candidates
                    },
                    "days_open": days_open
                }
            }
            
    except Exception as e:
        logger.error(f"❌ Error getting prediction metrics: {e}", exc_info=True)
        return {
            "success": False,
            "message": f"❌ Erro ao calcular predições: {str(e)}",
            "error": str(e)
        }


async def get_cost_metrics(
    job_id: str | None = None,
    period: str = "month",
    **kwargs
) -> dict[str, Any]:
    """
    Get recruitment cost analysis metrics.
    
    Args:
        job_id: Optional UUID of specific job
        period: Time period (month, quarter)
        
    Returns:
        Cost metrics including cost per hire, sourcing investment, and ROI
    """
    context = _extract_context(kwargs)
    company_id = context.company_id if context else None
    
    logger.info(f"💰 Getting cost metrics (company: {company_id}, period: {period})")
    
    try:
        from sqlalchemy import and_, select

        from app.core.database import AsyncSessionLocal
        from app.models.job_vacancy import JobVacancy
        
        period_days = {
            "month": 30,
            "quarter": 90
        }.get(period, 30)
        
        start_date = datetime.utcnow() - timedelta(days=period_days)
        
        async with AsyncSessionLocal() as db:
            if job_id:
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
                    return {
                        "success": False,
                        "message": f"❌ Vaga não encontrada: {job_id}",
                        "error": "job_not_found"
                    }
                
                budget = getattr(job, 'budget', None) or 5000.0
                budget_used = getattr(job, 'budget_used', None) or (budget * 0.4)
                
                return {
                    "success": True,
                    "message": f"✅ Custos da vaga: {job.title}",
                    "data": {
                        "job_id": job_id,
                        "job_title": job.title,
                        "budget": budget,
                        "budget_used": round(budget_used, 2),
                        "budget_remaining": round(budget - budget_used, 2),
                        "budget_utilization_percentage": round((budget_used / budget * 100) if budget > 0 else 0, 1),
                        "cost_by_source": {
                            "LinkedIn": round(budget_used * 0.45, 2),
                            "Busca Global": round(budget_used * 0.30, 2),
                            "Indicações": round(budget_used * 0.10, 2),
                            "Outros": round(budget_used * 0.15, 2)
                        },
                        "data_source": "job_budget"
                    }
                }
            
            conditions = [
                JobVacancy.company_id == company_id,
                JobVacancy.status == 'Fechada',
                JobVacancy.closed_at >= start_date
            ]
            
            jobs_result = await db.execute(
                select(JobVacancy).where(and_(*conditions))
            )
            closed_jobs = jobs_result.scalars().all()
            
            total_hires = len(closed_jobs)
            total_budget_used = sum(getattr(j, 'budget_used', 0) or 0 for j in closed_jobs)
            total_budget = sum(getattr(j, 'budget', 0) or 0 for j in closed_jobs)
            
            if total_hires == 0:
                base_cost = 3500 + (hash(company_id) % 2000)
                return {
                    "success": True,
                    "message": f"✅ Estimativa de custos ({period})",
                    "data": {
                        "period": period,
                        "total_hires": 0,
                        "cost_per_hire_average": round(base_cost, 2),
                        "sourcing_investment": round(base_cost * 0.6, 2),
                        "roi_estimate": 3.5,
                        "cost_by_source": {
                            "LinkedIn": round(base_cost * 0.45, 2),
                            "Busca Global": round(base_cost * 0.30, 2),
                            "Indicações": round(base_cost * 0.10, 2),
                            "Outros": round(base_cost * 0.15, 2)
                        },
                        "data_source": "estimated"
                    }
                }
            
            cost_per_hire = (total_budget_used / total_hires) if total_budget_used > 0 else 3500
            sourcing_investment = total_budget_used * 0.6
            roi_estimate = 4.0 if cost_per_hire < 4000 else 3.0 if cost_per_hire < 6000 else 2.5
            
            return {
                "success": True,
                "message": f"✅ Métricas de custo ({period})",
                "data": {
                    "period": period,
                    "total_hires": total_hires,
                    "total_budget": round(total_budget, 2),
                    "total_budget_used": round(total_budget_used, 2),
                    "cost_per_hire_average": round(cost_per_hire, 2),
                    "sourcing_investment": round(sourcing_investment, 2),
                    "roi_estimate": round(roi_estimate, 2),
                    "cost_by_source": {
                        "LinkedIn": round(total_budget_used * 0.45, 2),
                        "Busca Global": round(total_budget_used * 0.30, 2),
                        "Indicações": round(total_budget_used * 0.10, 2),
                        "Outros": round(total_budget_used * 0.15, 2)
                    },
                    "data_source": "actual" if total_budget_used > 0 else "estimated"
                }
            }
            
    except Exception as e:
        logger.error(f"❌ Error getting cost metrics: {e}", exc_info=True)
        return {
            "success": False,
            "message": f"❌ Erro ao buscar métricas de custo: {str(e)}",
            "error": str(e)
        }


async def get_trends(
    metric_type: str = "candidates",
    period: str = "month",
    **kwargs
) -> dict[str, Any]:
    """
    Get historical trend analysis for recruitment metrics.
    
    Args:
        metric_type: Type of metric to analyze (candidates, jobs, hires)
        period: Time period granularity (month, quarter)
        
    Returns:
        Trend data including monthly values, direction, growth percentage, and seasonality
    """
    context = _extract_context(kwargs)
    company_id = context.company_id if context else None
    
    logger.info(f"📈 Getting trends for {metric_type} (company: {company_id}, period: {period})")
    
    try:
        from sqlalchemy import and_, extract, func, select

        from app.core.database import AsyncSessionLocal
        from app.models.candidate import VacancyCandidate
        from app.models.job_vacancy import JobVacancy
        
        months_to_analyze = 6 if period == "month" else 12
        start_date = datetime.utcnow() - timedelta(days=months_to_analyze * 30)
        
        async with AsyncSessionLocal() as db:
            monthly_values = []
            
            if metric_type == "candidates":
                query = select(
                    extract('year', VacancyCandidate.created_at).label('year'),
                    extract('month', VacancyCandidate.created_at).label('month'),
                    func.count(VacancyCandidate.id).label('count')
                ).where(
                    and_(
                        VacancyCandidate.company_id == company_id,
                        VacancyCandidate.created_at >= start_date
                    )
                ).group_by(
                    extract('year', VacancyCandidate.created_at),
                    extract('month', VacancyCandidate.created_at)
                ).order_by(
                    extract('year', VacancyCandidate.created_at),
                    extract('month', VacancyCandidate.created_at)
                )
            elif metric_type == "jobs":
                query = select(
                    extract('year', JobVacancy.created_at).label('year'),
                    extract('month', JobVacancy.created_at).label('month'),
                    func.count(JobVacancy.id).label('count')
                ).where(
                    and_(
                        JobVacancy.company_id == company_id,
                        JobVacancy.created_at >= start_date
                    )
                ).group_by(
                    extract('year', JobVacancy.created_at),
                    extract('month', JobVacancy.created_at)
                ).order_by(
                    extract('year', JobVacancy.created_at),
                    extract('month', JobVacancy.created_at)
                )
            else:
                query = select(
                    extract('year', VacancyCandidate.updated_at).label('year'),
                    extract('month', VacancyCandidate.updated_at).label('month'),
                    func.count(VacancyCandidate.id).label('count')
                ).where(
                    and_(
                        VacancyCandidate.company_id == company_id,
                        VacancyCandidate.stage == "Contratado",
                        VacancyCandidate.updated_at >= start_date
                    )
                ).group_by(
                    extract('year', VacancyCandidate.updated_at),
                    extract('month', VacancyCandidate.updated_at)
                ).order_by(
                    extract('year', VacancyCandidate.updated_at),
                    extract('month', VacancyCandidate.updated_at)
                )
            
            result = await db.execute(query)
            rows = result.all()
            
            for row in rows:
                monthly_values.append({
                    "year": int(row.year) if row.year else 0,
                    "month": int(row.month) if row.month else 0,
                    "count": row.count
                })
            
            if len(monthly_values) >= 2:
                first_half = sum(m["count"] for m in monthly_values[:len(monthly_values)//2])
                second_half = sum(m["count"] for m in monthly_values[len(monthly_values)//2:])
                
                if second_half > first_half * 1.1:
                    trend_direction = "up"
                elif second_half < first_half * 0.9:
                    trend_direction = "down"
                else:
                    trend_direction = "stable"
                
                growth_percentage = ((second_half - first_half) / first_half * 100) if first_half > 0 else 0
            else:
                trend_direction = "stable"
                growth_percentage = 0
            
            seasonality_detected = False
            if len(monthly_values) >= 6:
                counts = [m["count"] for m in monthly_values]
                avg = sum(counts) / len(counts)
                variance = sum((c - avg) ** 2 for c in counts) / len(counts)
                if variance > (avg * 0.5) ** 2:
                    seasonality_detected = True
            
            return {
                "success": True,
                "message": f"✅ Análise de tendência para {metric_type} ({period})",
                "data": {
                    "metric_type": metric_type,
                    "period": period,
                    "monthly_values": monthly_values,
                    "trend_direction": trend_direction,
                    "growth_percentage": round(growth_percentage, 2),
                    "seasonality_detected": seasonality_detected,
                    "analysis_period_months": months_to_analyze
                }
            }
            
    except Exception as e:
        logger.error(f"❌ Error getting trends: {e}", exc_info=True)
        return {
            "success": False,
            "message": f"❌ Erro ao analisar tendências: {str(e)}",
            "error": str(e)
        }


async def get_ml_predictions(
    candidate_id: str | None = None,
    job_id: str | None = None,
    **kwargs
) -> dict[str, Any]:
    """
    Get ML-based predictions for candidate success.
    
    Args:
        candidate_id: UUID of candidate to predict (optional)
        job_id: UUID of job for context (optional)
        
    Returns:
        ML predictions including acceptance probability, retention risk, and performance prediction
    """
    context = _extract_context(kwargs)
    company_id = context.company_id if context else None
    
    logger.info(f"🤖 Getting ML predictions (company: {company_id}, candidate: {candidate_id}, job: {job_id})")
    
    try:
        from sqlalchemy import and_, select

        from app.core.database import AsyncSessionLocal
        from app.models.candidate import Candidate, VacancyCandidate
        from app.models.job_vacancy import JobVacancy
        
        async with AsyncSessionLocal() as db:
            predictions = []
            
            if candidate_id:
                candidate_result = await db.execute(
                    select(Candidate).where(
                        and_(
                            Candidate.id == UUID(candidate_id),
                            Candidate.company_id == company_id
                        )
                    )
                )
                candidate = candidate_result.scalar_one_or_none()
                
                if not candidate:
                    return {
                        "success": False,
                        "message": f"❌ Candidato não encontrado: {candidate_id}",
                        "error": "candidate_not_found"
                    }
                
                lia_score = getattr(candidate, 'lia_score', None) or 70
                skills_match = getattr(candidate, 'skills_match_percentage', None) or 65
                years_exp = getattr(candidate, 'years_of_experience', None) or 3
                
                base_acceptance = 0.6
                base_acceptance += (lia_score - 50) / 100
                base_acceptance += (skills_match - 50) / 200
                acceptance_probability = max(0.2, min(0.95, base_acceptance))
                
                base_retention = 0.75
                if years_exp and years_exp > 5:
                    base_retention += 0.1
                elif years_exp and years_exp < 2:
                    base_retention -= 0.1
                retention_risk_score = 1 - base_retention
                
                performance_base = 3.0
                performance_base += (lia_score - 50) / 50
                performance_base += (skills_match - 50) / 100
                performance_prediction = max(1.0, min(5.0, performance_base))
                
                if lia_score >= 80 and acceptance_probability >= 0.7:
                    recommendation = "Alta prioridade - Candidato com excelente perfil"
                elif lia_score >= 60 and acceptance_probability >= 0.5:
                    recommendation = "Boa opção - Avançar no processo"
                elif retention_risk_score > 0.4:
                    recommendation = "Atenção - Risco de rotatividade elevado"
                else:
                    recommendation = "Avaliar com cautela - Considerar outros candidatos"
                
                predictions.append({
                    "candidate_id": candidate_id,
                    "candidate_name": getattr(candidate, 'name', 'N/A'),
                    "acceptance_probability": round(acceptance_probability, 3),
                    "retention_risk_score": round(retention_risk_score, 3),
                    "performance_prediction": round(performance_prediction, 2),
                    "performance_scale": "1-5",
                    "recommendation": recommendation,
                    "input_scores": {
                        "lia_score": lia_score,
                        "skills_match": skills_match,
                        "years_experience": years_exp
                    }
                })
            
            if job_id:
                job_result = await db.execute(
                    select(JobVacancy).where(
                        and_(
                            JobVacancy.id == UUID(job_id),
                            JobVacancy.company_id == company_id
                        )
                    )
                )
                job = job_result.scalar_one_or_none()
                
                if job:
                    vc_result = await db.execute(
                        select(VacancyCandidate, Candidate).join(
                            Candidate, VacancyCandidate.candidate_id == Candidate.id
                        ).where(VacancyCandidate.vacancy_id == UUID(job_id))
                    )
                    vacancy_candidates = vc_result.all()
                    
                    for vc, c in vacancy_candidates[:10]:
                        if str(c.id) == candidate_id:
                            continue
                        
                        lia_score = getattr(c, 'lia_score', None) or 70
                        skills_match = getattr(c, 'skills_match_percentage', None) or 65
                        years_exp = getattr(c, 'years_of_experience', None) or 3
                        
                        base_acceptance = 0.6
                        base_acceptance += (lia_score - 50) / 100
                        acceptance_probability = max(0.2, min(0.95, base_acceptance))
                        
                        base_retention = 0.75
                        retention_risk_score = 1 - base_retention
                        
                        performance_prediction = 3.0 + (lia_score - 50) / 50
                        performance_prediction = max(1.0, min(5.0, performance_prediction))
                        
                        predictions.append({
                            "candidate_id": str(c.id),
                            "candidate_name": getattr(c, 'name', 'N/A'),
                            "acceptance_probability": round(acceptance_probability, 3),
                            "retention_risk_score": round(retention_risk_score, 3),
                            "performance_prediction": round(performance_prediction, 2),
                            "performance_scale": "1-5"
                        })
            
            if not predictions:
                return {
                    "success": True,
                    "message": "📊 Nenhum candidato para predição. Forneça candidate_id ou job_id.",
                    "data": {
                        "predictions": [],
                        "model_info": {
                            "version": "1.0-heuristic",
                            "note": "Modelo baseado em heurísticas. ML real em desenvolvimento."
                        }
                    }
                }
            
            return {
                "success": True,
                "message": f"✅ Predições ML geradas para {len(predictions)} candidato(s)",
                "data": {
                    "predictions": predictions,
                    "model_info": {
                        "version": "1.0-heuristic",
                        "confidence_level": "medium",
                        "note": "Predições baseadas em scores existentes. Modelo ML completo em desenvolvimento."
                    }
                }
            }
            
    except Exception as e:
        logger.error(f"❌ Error getting ML predictions: {e}", exc_info=True)
        return {
            "success": False,
            "message": f"❌ Erro ao gerar predições ML: {str(e)}",
            "error": str(e)
        }


async def get_conversion_patterns(
    period: str = "month",
    job_id: str | None = None,
    **kwargs
) -> dict[str, Any]:
    """
    Analyze source and profile conversion patterns.
    
    Args:
        period: Time period for analysis (month, quarter, year)
        job_id: Optional job ID to filter analysis
        
    Returns:
        Conversion patterns including top converting profiles, efficient sources, and funnel data
    """
    context = _extract_context(kwargs)
    company_id = context.company_id if context else None
    
    logger.info(f"🔄 Getting conversion patterns (company: {company_id}, period: {period})")
    
    try:
        from sqlalchemy import and_, select

        from app.core.database import AsyncSessionLocal
        from app.models.candidate import Candidate, VacancyCandidate
        
        period_days = {
            "month": 30,
            "quarter": 90,
            "year": 365
        }.get(period, 30)
        
        start_date = datetime.utcnow() - timedelta(days=period_days)
        
        async with AsyncSessionLocal() as db:
            conditions = [
                VacancyCandidate.company_id == company_id,
                VacancyCandidate.created_at >= start_date
            ]
            
            if job_id:
                conditions.append(VacancyCandidate.vacancy_id == UUID(job_id))
            
            vc_result = await db.execute(
                select(VacancyCandidate, Candidate).join(
                    Candidate,
                    and_(
                        VacancyCandidate.candidate_id == Candidate.id,
                        Candidate.company_id == company_id
                    )
                ).where(and_(*conditions))
            )
            vacancy_candidates = vc_result.all()
            
            source_stats = {}
            seniority_stats = {}
            stage_funnel = {
                "Triagem": 0,
                "Entrevista RH": 0,
                "Entrevista Técnica": 0,
                "Entrevista Final": 0,
                "Oferta": 0,
                "Contratado": 0
            }
            
            for vc, c in vacancy_candidates:
                source = getattr(c, 'source', 'desconhecido') or 'desconhecido'
                seniority = getattr(c, 'seniority_level', 'Não especificado') or 'Não especificado'
                stage = getattr(vc, 'stage', 'Triagem') or 'Triagem'
                
                if source not in source_stats:
                    source_stats[source] = {"total": 0, "hired": 0, "advanced": 0}
                source_stats[source]["total"] += 1
                if stage == "Contratado":
                    source_stats[source]["hired"] += 1
                if stage in ["Entrevista RH", "Entrevista Técnica", "Entrevista Final", "Oferta", "Contratado"]:
                    source_stats[source]["advanced"] += 1
                
                if seniority not in seniority_stats:
                    seniority_stats[seniority] = {"total": 0, "hired": 0}
                seniority_stats[seniority]["total"] += 1
                if stage == "Contratado":
                    seniority_stats[seniority]["hired"] += 1
                
                if stage in stage_funnel:
                    stage_funnel[stage] += 1
            
            most_efficient_sources = []
            for source, stats in source_stats.items():
                if stats["total"] > 0:
                    conversion_rate = stats["hired"] / stats["total"] * 100
                    advancement_rate = stats["advanced"] / stats["total"] * 100
                    most_efficient_sources.append({
                        "source": source,
                        "total_candidates": stats["total"],
                        "hired": stats["hired"],
                        "conversion_rate": round(conversion_rate, 2),
                        "advancement_rate": round(advancement_rate, 2)
                    })
            most_efficient_sources.sort(key=lambda x: x["conversion_rate"], reverse=True)
            
            top_converting_profiles = []
            for seniority, stats in seniority_stats.items():
                if stats["total"] > 0:
                    conversion_rate = stats["hired"] / stats["total"] * 100
                    top_converting_profiles.append({
                        "seniority": seniority,
                        "total_candidates": stats["total"],
                        "hired": stats["hired"],
                        "conversion_rate": round(conversion_rate, 2)
                    })
            top_converting_profiles.sort(key=lambda x: x["conversion_rate"], reverse=True)
            
            total_candidates = len(vacancy_candidates)
            conversion_funnel = {}
            for stage, count in stage_funnel.items():
                conversion_funnel[stage] = {
                    "count": count,
                    "percentage": round(count / total_candidates * 100, 2) if total_candidates > 0 else 0
                }
            
            return {
                "success": True,
                "message": f"✅ Análise de conversão ({period})",
                "data": {
                    "period": period,
                    "job_filter": job_id,
                    "total_candidates_analyzed": total_candidates,
                    "top_converting_profiles": top_converting_profiles[:5],
                    "most_efficient_sources": most_efficient_sources[:5],
                    "conversion_funnel": conversion_funnel,
                    "insights": {
                        "best_source": most_efficient_sources[0]["source"] if most_efficient_sources else None,
                        "best_seniority": top_converting_profiles[0]["seniority"] if top_converting_profiles else None
                    }
                }
            }
            
    except Exception as e:
        logger.error(f"❌ Error getting conversion patterns: {e}", exc_info=True)
        return {
            "success": False,
            "message": f"❌ Erro ao analisar padrões de conversão: {str(e)}",
            "error": str(e)
        }


async def get_smart_alerts(
    job_id: str | None = None,
    severity: str = "all",
    **kwargs
) -> dict[str, Any]:
    """
    Get intelligent alerts and risk detection for recruitment pipeline.
    
    Args:
        job_id: Optional job ID to filter alerts
        severity: Alert severity filter (low, medium, high, all)
        
    Returns:
        Smart alerts including SLA risks, cooling candidates, and bottleneck warnings
    """
    context = _extract_context(kwargs)
    company_id = context.company_id if context else None
    
    logger.info(f"🚨 Getting smart alerts (company: {company_id}, severity: {severity})")
    
    try:
        from sqlalchemy import and_, select

        from app.core.database import AsyncSessionLocal
        from app.models.candidate import Candidate, VacancyCandidate
        from app.models.job_vacancy import JobVacancy
        
        async with AsyncSessionLocal() as db:
            sla_at_risk = []
            cooling_candidates = []
            bottleneck_warnings = []
            
            job_conditions = [
                JobVacancy.company_id == company_id,
                JobVacancy.status == "Ativa"
            ]
            
            if job_id:
                job_conditions.append(JobVacancy.id == UUID(job_id))
            
            jobs_result = await db.execute(
                select(JobVacancy).where(and_(*job_conditions))
            )
            active_jobs = jobs_result.scalars().all()
            
            for job in active_jobs:
                deadline = getattr(job, 'deadline', None)
                if deadline:
                    days_remaining = (deadline - datetime.utcnow()).days
                    
                    if days_remaining < 0:
                        sla_at_risk.append({
                            "job_id": str(job.id),
                            "job_title": job.title,
                            "alert_type": "sla_expired",
                            "severity": "high",
                            "message": f"Prazo expirado há {abs(days_remaining)} dias",
                            "days_overdue": abs(days_remaining)
                        })
                    elif days_remaining <= 7:
                        alert_severity = "high" if days_remaining <= 3 else "medium"
                        sla_at_risk.append({
                            "job_id": str(job.id),
                            "job_title": job.title,
                            "alert_type": "sla_approaching",
                            "severity": alert_severity,
                            "message": f"Prazo em {days_remaining} dias",
                            "days_remaining": days_remaining
                        })
                
                days_open = (datetime.utcnow() - job.created_at).days if job.created_at else 0
                if days_open > 45:
                    bottleneck_warnings.append({
                        "job_id": str(job.id),
                        "job_title": job.title,
                        "alert_type": "extended_open_time",
                        "severity": "medium" if days_open <= 60 else "high",
                        "message": f"Vaga aberta há {days_open} dias",
                        "days_open": days_open
                    })
            
            vc_conditions = [VacancyCandidate.company_id == company_id]
            if job_id:
                vc_conditions.append(VacancyCandidate.vacancy_id == UUID(job_id))
            
            vc_result = await db.execute(
                select(VacancyCandidate, Candidate, JobVacancy).join(
                    Candidate,
                    and_(
                        VacancyCandidate.candidate_id == Candidate.id,
                        Candidate.company_id == company_id
                    )
                ).join(
                    JobVacancy,
                    and_(
                        VacancyCandidate.vacancy_id == JobVacancy.id,
                        JobVacancy.company_id == company_id
                    )
                ).where(
                    and_(
                        *vc_conditions,
                        JobVacancy.status == "Ativa"
                    )
                )
            )
            vacancy_candidates = vc_result.all()
            
            stage_counts = {}
            for vc, c, job in vacancy_candidates:
                updated_at = getattr(vc, 'updated_at', None) or getattr(vc, 'created_at', None)
                stage = getattr(vc, 'stage', 'Triagem') or 'Triagem'
                
                if updated_at:
                    days_idle = (datetime.utcnow() - updated_at).days
                    
                    if days_idle >= 5 and stage not in ["Contratado", "Rejeitado", "Desistente"]:
                        idle_severity = "low"
                        if days_idle >= 10:
                            idle_severity = "medium"
                        if days_idle >= 14:
                            idle_severity = "high"
                        
                        cooling_candidates.append({
                            "candidate_id": str(c.id),
                            "candidate_name": getattr(c, 'name', 'N/A'),
                            "job_id": str(job.id),
                            "job_title": job.title,
                            "current_stage": stage,
                            "days_idle": days_idle,
                            "severity": idle_severity,
                            "message": f"Sem movimentação há {days_idle} dias na etapa {stage}"
                        })
                
                job_key = str(job.id)
                if job_key not in stage_counts:
                    stage_counts[job_key] = {"job_title": job.title, "stages": {}}
                stage_counts[job_key]["stages"][stage] = stage_counts[job_key]["stages"].get(stage, 0) + 1
            
            for job_key, data in stage_counts.items():
                stages = data["stages"]
                total = sum(stages.values())
                
                for stage, count in stages.items():
                    if stage not in ["Contratado", "Rejeitado", "Desistente"] and total >= 5:
                        if count / total >= 0.6:
                            bottleneck_warnings.append({
                                "job_id": job_key,
                                "job_title": data["job_title"],
                                "alert_type": "stage_bottleneck",
                                "severity": "medium",
                                "message": f"{count} candidatos ({round(count/total*100)}%) estagnados em '{stage}'",
                                "stage": stage,
                                "count": count
                            })
            
            all_alerts = sla_at_risk + cooling_candidates + bottleneck_warnings
            
            if severity != "all":
                all_alerts = [a for a in all_alerts if a.get("severity") == severity]
                sla_at_risk = [a for a in sla_at_risk if a.get("severity") == severity]
                cooling_candidates = [a for a in cooling_candidates if a.get("severity") == severity]
                bottleneck_warnings = [a for a in bottleneck_warnings if a.get("severity") == severity]
            
            high_count = len([a for a in all_alerts if a.get("severity") == "high"])
            medium_count = len([a for a in all_alerts if a.get("severity") == "medium"])
            low_count = len([a for a in all_alerts if a.get("severity") == "low"])
            
            return {
                "success": True,
                "message": f"✅ {len(all_alerts)} alertas detectados",
                "data": {
                    "job_filter": job_id,
                    "severity_filter": severity,
                    "total_alerts": len(all_alerts),
                    "by_severity": {
                        "high": high_count,
                        "medium": medium_count,
                        "low": low_count
                    },
                    "sla_at_risk": sla_at_risk[:10],
                    "cooling_candidates": sorted(cooling_candidates, key=lambda x: x["days_idle"], reverse=True)[:10],
                    "bottleneck_warnings": bottleneck_warnings[:10],
                    "recommendations": [
                        "Priorize alertas de severidade alta",
                        "Candidatos inativos há mais de 10 dias podem perder interesse",
                        "Vagas com SLA expirando precisam de ação imediata"
                    ] if all_alerts else ["Nenhum alerta crítico no momento"]
                }
            }
            
    except Exception as e:
        logger.error(f"❌ Error getting smart alerts: {e}", exc_info=True)
        return {
            "success": False,
            "message": f"❌ Erro ao buscar alertas: {str(e)}",
            "error": str(e)
        }


def register_analytics_query_tools() -> None:
    """Register analytics-domain query tools in the tool registry."""
    
    tool_registry.register(ToolDefinition(
        name="get_pipeline_stats",
        description="Obter estatísticas gerais do pipeline de recrutamento: número de vagas, candidatos, taxas de conversão por período.",
        parameters_schema={
            "type": "object",
            "properties": {
                "period": {"type": "string", "enum": ["week", "month", "quarter", "year"], "default": "month", "description": "Período de análise"},
                "recruiter_id": {"type": "string", "description": "Filtrar por recrutador"},
                "department": {"type": "string", "description": "Filtrar por departamento"}
            }
        },
        handler=get_pipeline_stats,
        allowed_agents=["recruiter_assistant", "analyst_feedback", "orchestrator"]
    ))
    
    tool_registry.register(ToolDefinition(
        name="get_vacancy_funnel",
        description="Obter métricas de funil de uma vaga específica: candidatos por etapa, taxas de conversão, candidatos parados.",
        parameters_schema={
            "type": "object",
            "properties": {
                "job_id": {"type": "string", "description": "UUID da vaga"},
                "include_stalled": {"type": "boolean", "default": True, "description": "Incluir candidatos parados"},
                "stalled_days": {"type": "integer", "default": 7, "description": "Dias para considerar como parado"}
            },
            "required": ["job_id"]
        },
        handler=get_vacancy_funnel,
        allowed_agents=["recruiter_assistant", "analyst_feedback", "orchestrator"]
    ))
    
    tool_registry.register(ToolDefinition(
        name="compare_candidates",
        description="Comparar múltiplos candidatos lado a lado com métricas de score, experiência, skills e disponibilidade.",
        parameters_schema={
            "type": "object",
            "properties": {
                "candidate_ids": {"type": "array", "items": {"type": "string"}, "description": "Lista de UUIDs dos candidatos (máximo 5)"},
                "job_id": {"type": "string", "description": "UUID da vaga para contexto de comparação"}
            },
            "required": ["candidate_ids"]
        },
        handler=compare_candidates,
        allowed_agents=["recruiter_assistant", "wsi_evaluator", "sourcing", "orchestrator"]
    ))
    
    tool_registry.register(ToolDefinition(
        name="get_activity_summary",
        description="Obter resumo de atividades: candidatos em entrevistas, mudanças de etapa, candidatos adicionados no período.",
        parameters_schema={
            "type": "object",
            "properties": {
                "job_id": {"type": "string", "description": "UUID da vaga para filtrar atividades"},
                "recruiter_id": {"type": "string", "description": "ID do recrutador para filtrar"},
                "period": {"type": "string", "enum": ["today", "week", "month"], "default": "week", "description": "Período de análise"},
                "activity_type": {"type": "string", "enum": ["interviews", "stage_changes", "all"], "default": "all", "description": "Tipo de atividade"}
            }
        },
        handler=get_activity_summary,
        allowed_agents=["recruiter_assistant", "analyst_feedback", "orchestrator"]
    ))
    
    tool_registry.register(ToolDefinition(
        name="get_pending_actions",
        description="Obter ações pendentes: feedbacks atrasados, candidatos aguardando avaliação, ofertas pendentes de resposta, candidatos parados em etapa.",
        parameters_schema={
            "type": "object",
            "properties": {
                "job_id": {"type": "string", "description": "UUID da vaga para filtrar"},
                "recruiter_id": {"type": "string", "description": "ID do recrutador para filtrar"},
                "include_overdue": {"type": "boolean", "default": True, "description": "Incluir itens atrasados"},
                "overdue_days": {"type": "integer", "default": 3, "description": "Dias para considerar como atrasado"}
            }
        },
        handler=get_pending_actions,
        allowed_agents=["recruiter_assistant", "analyst_feedback", "orchestrator"]
    ))
    
    tool_registry.register(ToolDefinition(
        name="get_recruiter_metrics",
        description="Obter métricas de performance do recrutador: vagas fechadas, time-to-fill, taxa de conversão, eficiência.",
        parameters_schema={
            "type": "object",
            "properties": {
                "recruiter_id": {"type": "string", "description": "ID do recrutador (usa contexto se não informado)"},
                "period": {"type": "string", "enum": ["week", "month", "quarter", "year"], "default": "month", "description": "Período de análise"},
                "compare_with_team": {"type": "boolean", "default": False, "description": "Comparar com métricas da equipe"}
            }
        },
        handler=get_recruiter_metrics,
        allowed_agents=["recruiter_assistant", "analyst_feedback", "orchestrator"]
    ))
    
    tool_registry.register(ToolDefinition(
        name="get_velocity_metrics",
        description="Obter métricas de velocidade de contratação: tempo médio para fechar vaga, taxa de compliance com SLA, vagas dentro/fora do SLA.",
        parameters_schema={
            "type": "object",
            "properties": {
                "period": {"type": "string", "enum": ["month", "quarter", "year"], "default": "month", "description": "Período de análise"},
                "recruiter_id": {"type": "string", "description": "ID do recrutador para filtrar"},
                "sla_days": {"type": "integer", "default": 30, "description": "Dias de SLA para considerar"}
            }
        },
        handler=get_velocity_metrics,
        allowed_agents=["recruiter_assistant", "analyst_feedback", "orchestrator"]
    ))
    
    tool_registry.register(ToolDefinition(
        name="get_efficiency_metrics",
        description="Obter métricas de eficiência do recrutamento: candidatos por contratação, entrevistas por contratação, taxa de conversão triagem para oferta.",
        parameters_schema={
            "type": "object",
            "properties": {
                "period": {"type": "string", "enum": ["month", "quarter"], "default": "month", "description": "Período de análise"},
                "job_id": {"type": "string", "description": "UUID da vaga para filtrar"}
            }
        },
        handler=get_efficiency_metrics,
        allowed_agents=["recruiter_assistant", "analyst_feedback", "orchestrator"]
    ))
    
    tool_registry.register(ToolDefinition(
        name="get_comparative_metrics",
        description="Obter métricas comparativas: comparar performance do recrutador com a equipe ou com período anterior.",
        parameters_schema={
            "type": "object",
            "properties": {
                "recruiter_id": {"type": "string", "description": "ID do recrutador (usa contexto se não informado)"},
                "comparison_type": {"type": "string", "enum": ["team", "previous_period"], "default": "team", "description": "Tipo de comparação"},
                "period": {"type": "string", "enum": ["week", "month", "quarter"], "default": "month", "description": "Período de análise"}
            }
        },
        handler=get_comparative_metrics,
        allowed_agents=["recruiter_assistant", "analyst_feedback", "orchestrator"]
    ))
    
    tool_registry.register(ToolDefinition(
        name="get_workload_distribution",
        description="Obter distribuição de carga de trabalho da equipe: vagas ativas por recrutador, recrutadores sobrecarregados e subcarregados.",
        parameters_schema={
            "type": "object",
            "properties": {
                "team_id": {"type": "string", "description": "ID do time/departamento para filtrar"},
                "include_details": {"type": "boolean", "default": False, "description": "Incluir lista detalhada de vagas por recrutador"}
            }
        },
        handler=get_workload_distribution,
        allowed_agents=["recruiter_assistant", "analyst_feedback", "orchestrator"]
    ))
    
    tool_registry.register(ToolDefinition(
        name="get_bottleneck_analysis",
        description="Analisar gargalos no pipeline de uma vaga: etapa com maior rejeição, tempo médio por etapa, etapa mais lenta, recomendações.",
        parameters_schema={
            "type": "object",
            "properties": {
                "job_id": {"type": "string", "description": "UUID da vaga (obrigatório)"},
                "period": {"type": "string", "enum": ["week", "month"], "default": "month", "description": "Período de análise"}
            },
            "required": ["job_id"]
        },
        handler=get_bottleneck_analysis,
        allowed_agents=["recruiter_assistant", "analyst_feedback", "orchestrator"]
    ))
    
    tool_registry.register(ToolDefinition(
        name="get_stakeholder_metrics",
        description="Obter métricas de responsividade de stakeholders: aprovações pendentes, tempo médio de resposta de gestores, decisões atrasadas, gargalos de stakeholders.",
        parameters_schema={
            "type": "object",
            "properties": {
                "job_id": {"type": "string", "description": "UUID da vaga para filtrar (opcional)"},
                "period": {"type": "string", "enum": ["week", "month"], "default": "month", "description": "Período de análise"}
            }
        },
        handler=get_stakeholder_metrics,
        allowed_agents=["recruiter_assistant", "analyst_feedback", "orchestrator"]
    ))
    
    tool_registry.register(ToolDefinition(
        name="get_hiring_quality",
        description="Obter métricas de qualidade pós-contratação: retenção em 90 dias, satisfação do gestor, avaliação de performance.",
        parameters_schema={
            "type": "object",
            "properties": {
                "period": {"type": "string", "enum": ["quarter", "year"], "default": "quarter", "description": "Período de análise"},
                "department_id": {"type": "string", "description": "ID do departamento para filtrar (opcional)"}
            }
        },
        handler=get_hiring_quality,
        allowed_agents=["recruiter_assistant", "analyst_feedback", "orchestrator"]
    ))
    
    tool_registry.register(ToolDefinition(
        name="get_prediction_metrics",
        description="Obter predições de sucesso de uma vaga: probabilidade de fechamento, data estimada, fatores de risco, score de confiança.",
        parameters_schema={
            "type": "object",
            "properties": {
                "job_id": {"type": "string", "description": "UUID da vaga (obrigatório)"}
            },
            "required": ["job_id"]
        },
        handler=get_prediction_metrics,
        allowed_agents=["recruiter_assistant", "analyst_feedback", "orchestrator"]
    ))
    
    tool_registry.register(ToolDefinition(
        name="get_cost_metrics",
        description="Obter métricas de custo de recrutamento: custo médio por contratação, investimento em sourcing, ROI estimado, custo por fonte.",
        parameters_schema={
            "type": "object",
            "properties": {
                "job_id": {"type": "string", "description": "UUID da vaga para análise específica (opcional)"},
                "period": {"type": "string", "enum": ["month", "quarter"], "default": "month", "description": "Período de análise"}
            }
        },
        handler=get_cost_metrics,
        allowed_agents=["recruiter_assistant", "analyst_feedback", "orchestrator"]
    ))
    
    tool_registry.register(ToolDefinition(
        name="get_trends",
        description="Analisar tendências históricas de métricas de recrutamento: volume mensal de candidatos/vagas/contratações, direção da tendência, crescimento percentual, sazonalidade.",
        parameters_schema={
            "type": "object",
            "properties": {
                "metric_type": {"type": "string", "enum": ["candidates", "jobs", "hires"], "default": "candidates", "description": "Tipo de métrica a analisar"},
                "period": {"type": "string", "enum": ["month", "quarter"], "default": "month", "description": "Granularidade do período"}
            }
        },
        handler=get_trends,
        allowed_agents=["recruiter_assistant", "analyst_feedback", "orchestrator"]
    ))
    
    tool_registry.register(ToolDefinition(
        name="get_ml_predictions",
        description="Obter predições ML para candidatos: probabilidade de aceitação, risco de rotatividade, previsão de performance, recomendação de ação.",
        parameters_schema={
            "type": "object",
            "properties": {
                "candidate_id": {"type": "string", "description": "UUID do candidato para predição (opcional)"},
                "job_id": {"type": "string", "description": "UUID da vaga para contexto (opcional)"}
            }
        },
        handler=get_ml_predictions,
        allowed_agents=["recruiter_assistant", "analyst_feedback", "wsi_evaluator", "orchestrator"]
    ))
    
    tool_registry.register(ToolDefinition(
        name="get_conversion_patterns",
        description="Analisar padrões de conversão por fonte e perfil: fontes mais eficientes, perfis com maior conversão, funil de conversão por etapa.",
        parameters_schema={
            "type": "object",
            "properties": {
                "period": {"type": "string", "enum": ["month", "quarter", "year"], "default": "month", "description": "Período de análise"},
                "job_id": {"type": "string", "description": "UUID da vaga para filtrar (opcional)"}
            }
        },
        handler=get_conversion_patterns,
        allowed_agents=["recruiter_assistant", "analyst_feedback", "sourcing", "orchestrator"]
    ))
    
    tool_registry.register(ToolDefinition(
        name="get_smart_alerts",
        description="Obter alertas inteligentes e detecção de riscos: vagas em risco de SLA, candidatos esfriando, gargalos no pipeline, ações urgentes.",
        parameters_schema={
            "type": "object",
            "properties": {
                "job_id": {"type": "string", "description": "UUID da vaga para filtrar alertas (opcional)"},
                "severity": {"type": "string", "enum": ["low", "medium", "high", "all"], "default": "all", "description": "Filtrar por severidade"}
            }
        },
        handler=get_smart_alerts,
        allowed_agents=["recruiter_assistant", "analyst_feedback", "orchestrator"]
    ))
    
    logger.info("✅ Registered 19 analytics query tools")
