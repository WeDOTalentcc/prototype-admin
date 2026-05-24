"""Activity metrics tools: activity summary and pending actions."""
import logging
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

from ._base import analytics_db, error_response, extract_context, success_response
from app.tools.context_helpers import require_company_id_from_context

logger = logging.getLogger(__name__)


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
    company_id = require_company_id_from_context(kwargs, "get_activity_summary")

    logger.info(f"📊 Getting activity summary (company: {company_id}, period: {period})")

    try:
        from sqlalchemy import and_, select
        from app.models.candidate import VacancyCandidate

        period_days = {"today": 1, "week": 7, "month": 30}.get(period, 7)
        start_date = datetime.utcnow() - timedelta(days=period_days)

        async with analytics_db() as db:
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

            # TENANT-EXEMPT: dynamic builder — conditions[0] is VacancyCandidate.company_id == company_id (next line); .where(and_(*conditions)) aplica filter; sensor AST não traça
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

            return success_response(f"✅ Resumo de atividades ({period})", activities)

    except Exception as e:
        logger.error(f"❌ Error getting activity summary: {e}", exc_info=True)
        return error_response(f"❌ Erro ao buscar atividades: {str(e)}", e)


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
    company_id = require_company_id_from_context(kwargs, "get_pending_actions")

    logger.info(f"📋 Getting pending actions (company: {company_id})")

    try:
        from sqlalchemy import and_, select
        from app.models.candidate import Candidate, VacancyCandidate
        from app.models.job_vacancy import JobVacancy

        overdue_threshold = datetime.utcnow() - timedelta(days=overdue_days)

        async with analytics_db() as db:
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

            return success_response(
                f"✅ {pending['summary']['total_pending']} ações pendentes encontradas",
                pending
            )

    except Exception as e:
        logger.error(f"❌ Error getting pending actions: {e}", exc_info=True)
        return error_response(f"❌ Erro ao buscar pendências: {str(e)}", e)
