"""
Briefing Service - Intelligent daily briefing generation for recruiters.

This service generates personalized daily briefings including:
- Urgent actions required
- Pipeline summary
- Scheduled activities
- AI-powered insights
- Anomaly detection
"""

# RAILS-DEPRECATED: This service performs CRUD for Rails-owned entities.
# Will be deleted after ats-api-rails handoff is complete.
# Do NOT migrate to a domain -- route through integrations_hub/rails_adapter instead.

import warnings
warnings.warn(
    "briefing_service is deprecated and will be removed once Rails adapter routes are complete. "
    "Migrate callers to rails_adapter equivalents. "
    "See UC-P1-22 in the remediation plan (CROSS_CUTTING_AUDIT_AND_REMEDIATION_PLAN.md).",
    DeprecationWarning,
    stacklevel=2,
)

import logging
from datetime import datetime, time, timedelta
from typing import Any

from sqlalchemy import and_, case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from lia_models.alert import Alert, AlertSeverity, AlertStatus
from lia_models.candidate import Candidate
from lia_models.interview import Interview
from lia_models.job_vacancy import JobVacancy
from lia_models.task import Task, TaskPriority, TaskStatus, TaskType
from app.shared.services.recruiter_metrics_service import recruiter_metrics_service

logger = logging.getLogger(__name__)


class BriefingService:
    """
    Service for generating intelligent daily briefings.
    """
    
    async def generate_daily_briefing(
        self,
        user_id: str,
        db: AsyncSession | None = None,
        company_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Generate a comprehensive daily briefing for a recruiter.
        
        Args:
            user_id: The recruiter's user ID
            db: Optional database session
            company_id: Tenant scoping (WT-2022 P0.TASK). Quando ausente,
                _get_pending_tasks emite warning e cai em path legacy SQL inline.
                Callers novos devem propagar company_id do JWT/agent context.
            
        Returns:
            Complete briefing data structure
        """
        should_close = False
        if db is None:
            db = AsyncSessionLocal()
            should_close = True
            
        try:
            now = datetime.utcnow()
            today_start = datetime.combine(now.date(), time.min)
            today_end = datetime.combine(now.date(), time.max)
            
            urgent_actions = await self._get_urgent_actions(db, user_id)
            pipeline_summary = await self._get_pipeline_summary(db, user_id)
            today_schedule = await self._get_today_schedule(db, user_id, today_start, today_end)
            pending_tasks = await self._get_pending_tasks(db, user_id, company_id=company_id)
            active_alerts = await self._get_active_alerts(db, user_id)
            recruiter_metrics = await self._get_recruiter_metrics(db, user_id)
            recruiter_benchmark = await self._get_recruiter_benchmark(db, user_id, recruiter_metrics)
            pipeline_prediction = await self._get_pipeline_prediction(db, user_id, recruiter_metrics)
            insights = await self._generate_insights(db, user_id, pipeline_summary, recruiter_metrics, recruiter_benchmark, pipeline_prediction)

            greeting = self._get_greeting(now)

            briefing = {
                "id": f"briefing_{user_id}_{now.strftime('%Y%m%d')}",
                "generated_at": now.isoformat(),
                "user_id": user_id,
                "greeting": greeting,
                "summary": {
                    "urgent_count": len(urgent_actions),
                    "tasks_today": len(pending_tasks),
                    "interviews_today": len([s for s in today_schedule if s.get("type") == "interview"]),
                    "alerts_active": len(active_alerts),
                    "backlog_count": recruiter_metrics.get("backlog_count", 0),
                },
                "urgent_actions": urgent_actions[:5],
                "pipeline": pipeline_summary,
                "schedule": today_schedule,
                "tasks": pending_tasks[:10],
                "alerts": active_alerts[:5],
                "recruiter_metrics": recruiter_metrics,
                "recruiter_benchmark": recruiter_benchmark,
                "pipeline_prediction": pipeline_prediction,
                "insights": insights,
                "next_refresh": (now + timedelta(hours=1)).isoformat(),
            }
            
            logger.info(f"📋 Daily briefing generated for user {user_id}")
            return briefing
            
        finally:
            if should_close:
                await db.close()
    
    def _get_greeting(self, now: datetime) -> str:
        """Generate time-appropriate greeting."""
        hour = now.hour
        if hour < 12:
            return "Bom dia"
        elif hour < 18:
            return "Boa tarde"
        else:
            return "Boa noite"
    
    async def _get_urgent_actions(
        self,
        db: AsyncSession,
        user_id: str
    ) -> list[dict[str, Any]]:
        """Get urgent actions requiring immediate attention."""
        now = datetime.utcnow()
        now - timedelta(days=1)
        two_days_ago = now - timedelta(days=2)
        
        urgent_items = []
        
        try:
            overdue_tasks = await db.execute(
                select(Task).where(
                    and_(
                        Task.assigned_to_user_id == user_id,
                        Task.status == TaskStatus.PENDING,
                        Task.due_date < now
                    )
                ).order_by(Task.due_date.asc()).limit(10)
            )
            
            for task in overdue_tasks.scalars():
                days_overdue = (now - task.due_date).days if task.due_date else 0
                urgent_items.append({
                    "id": task.id,
                    "type": "overdue_task",
                    "title": task.title,
                    "description": task.description,
                    "priority": "critical" if days_overdue > 2 else "high",
                    "days_overdue": days_overdue,
                    "task_type": task.task_type.value if task.task_type else "general",
                    "related_job_id": task.related_job_id,
                    "related_candidate_id": task.related_candidate_id,
                    "action_label": "Resolver",
                    "action_type": "complete_task"
                })
        except Exception as e:
            logger.warning(f"Error fetching overdue tasks: {e}", exc_info=True)
        
        try:
            feedback_pending = await db.execute(
                select(Task).where(
                    and_(
                        Task.assigned_to_user_id == user_id,
                        Task.task_type == TaskType.FEEDBACK_PENDING,
                        Task.status == TaskStatus.PENDING,
                        Task.created_at < two_days_ago
                    )
                ).limit(5)
            )
            
            for task in feedback_pending.scalars():
                hours_pending = (now - task.created_at).total_seconds() / 3600
                urgent_items.append({
                    "id": task.id,
                    "type": "feedback_pending",
                    "title": f"Feedback pendente: {task.title}",
                    "description": f"Aguardando há {int(hours_pending)}h",
                    "priority": "high",
                    "hours_pending": int(hours_pending),
                    "related_candidate_id": task.related_candidate_id,
                    "action_label": "Avaliar",
                    "action_type": "provide_feedback"
                })
        except Exception as e:
            logger.warning(f"Error fetching feedback tasks: {e}", exc_info=True)
        
        try:
            critical_alerts = await db.execute(
                select(Alert).where(
                    and_(
                        Alert.status == AlertStatus.ACTIVE,
                        Alert.severity.in_([AlertSeverity.CRITICAL, AlertSeverity.HIGH]),
                        Alert.acknowledged_at.is_(None)
                    )
                ).limit(5)
            )
            
            for alert in critical_alerts.scalars():
                urgent_items.append({
                    "id": alert.id,
                    "type": "critical_alert",
                    "title": alert.title,
                    "description": alert.message,
                    "priority": alert.severity.value if alert.severity else "medium",
                    "alert_type": alert.alert_type.value if alert.alert_type else None,
                    "related_job_id": alert.job_id,
                    "action_label": "Verificar",
                    "action_type": "acknowledge_alert"
                })
        except Exception as e:
            logger.warning(f"Error fetching alerts: {e}", exc_info=True)
        
        urgent_items.sort(key=lambda x: {"critical": 0, "high": 1, "medium": 2}.get(x.get("priority", "medium"), 3))
        
        return urgent_items
    
    async def _get_pipeline_summary(
        self,
        db: AsyncSession,
        user_id: str
    ) -> dict[str, Any]:
        """Get summary of recruitment pipeline."""
        try:
            active_jobs = await db.execute(
                select(func.count(JobVacancy.id)).where(
                    JobVacancy.status.in_(["Ativa", "Publicada", "open"])
                )
            )
            active_jobs_count = active_jobs.scalar() or 0
            
            candidate_stats = await db.execute(
                select(
                    Candidate.status,
                    func.count(Candidate.id)
                ).where(Candidate.is_active).group_by(Candidate.status)
            )
            
            stages = {}
            total_candidates = 0
            for row in candidate_stats:
                stage, count = row
                if stage:
                    stages[stage] = count
                    total_candidates += count
            
            return {
                "active_jobs": active_jobs_count,
                "total_candidates": total_candidates,
                "stages": stages,
                "stages_summary": [
                    {"stage": "new", "count": stages.get("new", 0), "label": "Novos"},
                    {"stage": "screening", "count": stages.get("screening", 0), "label": "Triagem"},
                    {"stage": "interview", "count": stages.get("interview", 0), "label": "Entrevista"},
                    {"stage": "offer", "count": stages.get("offer", 0), "label": "Oferta"},
                    {"stage": "hired", "count": stages.get("hired", 0), "label": "Contratado"},
                ],
                "candidates_to_contact": stages.get("new", 0) + stages.get("screening", 0),
                "awaiting_feedback": stages.get("interview", 0),
                "offers_pending": stages.get("offer", 0),
            }
        except Exception as e:
            logger.warning(f"Error getting pipeline summary: {e}", exc_info=True)
            return {
                "active_jobs": 0,
                "total_candidates": 0,
                "stages": {},
                "stages_summary": [],
                "candidates_to_contact": 0,
                "awaiting_feedback": 0,
                "offers_pending": 0,
                "degraded": True,
                "degraded_reason": type(e).__name__,
            }
    
    async def _get_today_schedule(
        self,
        db: AsyncSession,
        user_id: str,
        today_start: datetime,
        today_end: datetime
    ) -> list[dict[str, Any]]:
        """Get today's scheduled activities."""
        schedule = []
        
        try:
            interviews = await db.execute(
                select(Interview).where(
                    and_(
                        Interview.start_time >= today_start,
                        Interview.start_time <= today_end,
                        Interview.status.in_(["scheduled", "confirmed"])
                    )
                ).order_by(Interview.start_time.asc())
            )
            
            for interview in interviews.scalars():
                schedule.append({
                    "id": str(interview.id),
                    "type": "interview",
                    "title": f"Entrevista: {interview.candidate_name or 'Candidato'}",
                    "time": interview.start_time.strftime("%H:%M") if interview.start_time else None,
                    "datetime": interview.start_time.isoformat() if interview.start_time else None,
                    "duration_minutes": interview.duration_minutes or 60,
                    "location": interview.location or "Virtual",
                    "candidate_id": str(interview.candidate_id) if interview.candidate_id else None,
                    "job_id": str(interview.job_vacancy_id) if interview.job_vacancy_id else None,
                    "status": interview.status,
                    "action_label": "Ver Detalhes",
                })
        except Exception as e:
            logger.warning(f"Error fetching interviews: {e}", exc_info=True)
        
        try:
            scheduled_tasks = await db.execute(
                select(Task).where(
                    and_(
                        Task.assigned_to_user_id == user_id,
                        Task.due_date >= today_start,
                        Task.due_date <= today_end,
                        Task.status == TaskStatus.PENDING
                    )
                ).order_by(Task.due_date.asc())
            )
            
            for task in scheduled_tasks.scalars():
                schedule.append({
                    "id": task.id,
                    "type": "task",
                    "title": task.title,
                    "time": task.due_date.strftime("%H:%M") if task.due_date else None,
                    "datetime": task.due_date.isoformat() if task.due_date else None,
                    "priority": task.priority.value if task.priority else "medium",
                    "task_type": task.task_type.value if task.task_type else "general",
                    "action_label": "Iniciar",
                })
        except Exception as e:
            logger.warning(f"Error fetching scheduled tasks: {e}", exc_info=True)
        
        try:
            from sqlalchemy import text as sql_text
            # calendar_events e RAILS-OWNED e pode nao existir neste DB (ex: dev
            # sem as migrations Rails de calendar). Pre-checar com to_regclass
            # evita a UndefinedTableError, que ABORTARIA a transacao
            # compartilhada e cascatearia em _get_active_alerts /
            # _get_recruiter_metrics (InFailedSQLTransactionError). 2026-06-06.
            _ce_tbl = await db.execute(
                sql_text("SELECT to_regclass('public.calendar_events')")
            )
            if _ce_tbl.scalar() is not None:
                events_result = await db.execute(
                    sql_text("""
                        SELECT id, title, description, location, start_time, duration_minutes
                        FROM calendar_events
                        WHERE organizer_id = CAST(:uid AS uuid)
                          AND event_type = 'generic'
                          AND start_time >= :today_start
                          AND start_time <= :today_end
                        ORDER BY start_time ASC
                        LIMIT 20
                    """),
                    {
                        "uid": user_id,
                        "today_start": today_start,
                        "today_end": today_end,
                    },
                )
                for row in events_result.fetchall():
                    start_dt = row[4]
                    schedule.append({
                        "id": str(row[0]),
                        "type": "commitment",
                        "title": row[1] or "Compromisso",
                        "description": row[2],
                        "time": start_dt.strftime("%H:%M") if start_dt else None,
                        "datetime": start_dt.isoformat() if start_dt else None,
                        "duration_minutes": row[5] or 60,
                        "location": row[3] or "",
                        "action_label": "Ver Compromisso",
                    })
        except Exception as e:
            logger.warning(f"Error fetching calendar events for briefing: {e}", exc_info=True)

        schedule.sort(key=lambda x: x.get("datetime") or "")
        
        return schedule
    
    async def _get_pending_tasks(
        self,
        db: AsyncSession,
        user_id: str,
        company_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """Get pending tasks for user.

        WT-2022 P0.TASK gap fix: usar TasksRepository canonical (ADR-001 +
        multi-tenancy) em vez de SQL inline cross-tenant. Quando company_id
        presente, delega ao repo que enforca tenant scoping. Quando ausente
        (caller legacy), cai no path antigo com warning -- briefing_service e
        deprecated (removal 2026-07-16), nao quebrar callers nao atualizados.
        """
        tasks: list[dict[str, Any]] = []

        if company_id:
            try:
                from app.domains.tasks.repositories.tasks_repository import TasksRepository
                repo = TasksRepository(db)
                repo_tasks = await repo.get_pending_tasks(
                    company_id=company_id,
                    user_id=user_id,
                    limit=15,
                )
                for task in repo_tasks:
                    tasks.append({
                        "id": task.id,
                        "title": task.title,
                        "description": task.description,
                        "type": task.task_type.value if task.task_type else "general",
                        "priority": task.priority.value if task.priority else "medium",
                        "due_date": task.due_date.isoformat() if task.due_date else None,
                        "created_at": task.created_at.isoformat() if task.created_at else None,
                        "related_job_id": task.related_job_id,
                        "related_candidate_id": task.related_candidate_id,
                        "created_by_agent": task.created_by_agent,
                        "is_automated": task.is_automated,
                    })
            except Exception as e:
                logger.warning(f"Error fetching pending tasks via TasksRepository: {e}", exc_info=True)
            return tasks

        # Legacy path (caller nao propagou company_id - cross-tenant gap)
        logger.warning(
            "briefing_service._get_pending_tasks: company_id ausente - usando "
            "path legacy SQL inline cross-tenant (multi-tenancy gap). Caller "
            "deve propagar company_id do JWT. WT-2022 P0.TASK."
        )
        try:
            result = await db.execute(
                select(Task).where(
                    and_(
                        Task.assigned_to_user_id == user_id,
                        Task.status == TaskStatus.PENDING
                    )
                ).order_by(
                    case(
                        (Task.priority == TaskPriority.CRITICAL, 1),
                        (Task.priority == TaskPriority.HIGH, 2),
                        (Task.priority == TaskPriority.MEDIUM, 3),
                        else_=4
                    ),
                    Task.due_date.asc().nullslast()
                ).limit(15)
            )

            for task in result.scalars():
                tasks.append({
                    "id": task.id,
                    "title": task.title,
                    "description": task.description,
                    "type": task.task_type.value if task.task_type else "general",
                    "priority": task.priority.value if task.priority else "medium",
                    "due_date": task.due_date.isoformat() if task.due_date else None,
                    "created_at": task.created_at.isoformat() if task.created_at else None,
                    "related_job_id": task.related_job_id,
                    "related_candidate_id": task.related_candidate_id,
                    "created_by_agent": task.created_by_agent,
                    "is_automated": task.is_automated,
                })
        except Exception as e:
            logger.warning(f"Error fetching pending tasks: {e}", exc_info=True)

        return tasks
    
    async def _get_active_alerts(
        self,
        db: AsyncSession,
        user_id: str
    ) -> list[dict[str, Any]]:
        """Get active alerts."""
        alerts = []
        
        try:
            result = await db.execute(
                select(Alert).where(
                    Alert.status == AlertStatus.ACTIVE
                ).order_by(
                    case(
                        (Alert.severity == AlertSeverity.CRITICAL, 1),
                        (Alert.severity == AlertSeverity.HIGH, 2),
                        (Alert.severity == AlertSeverity.MEDIUM, 3),
                        else_=4
                    ),
                    Alert.created_at.desc()
                ).limit(10)
            )
            
            for alert in result.scalars():
                alerts.append({
                    "id": alert.id,
                    "title": alert.title,
                    "message": alert.message,
                    "severity": alert.severity.value if alert.severity else "medium",
                    "alert_type": alert.alert_type.value if alert.alert_type else None,
                    "related_job_id": alert.job_id,
                    "created_at": alert.created_at.isoformat() if alert.created_at else None,
                    "acknowledged": alert.acknowledged_at is not None,
                    "resolved": alert.resolved_at is not None,
                })
        except Exception as e:
            logger.warning(f"Error fetching alerts: {e}", exc_info=True)
        
        return alerts
    
    async def _get_recruiter_metrics(
        self,
        db: AsyncSession,
        user_id: str,
    ) -> dict[str, Any]:
        """
        Retorna resumo de produtividade do recrutador para o Daily Briefing.
        Requer company_id — tenta extrair de vagas ativas do user. Degrada silenciosamente.
        """
        try:
            from sqlalchemy import text
            result = await db.execute(
                text(
                    "SELECT company_id::text FROM job_vacancies "
                    "WHERE (created_by = :user_id "
                    "  OR recruiter_email = (SELECT email FROM users WHERE id::text = :user_id LIMIT 1)) "
                    "AND status IN ('open', 'Ativa', 'Publicada') "
                    "LIMIT 1"
                ),
                {"user_id": user_id},
            )
            row = result.fetchone()
            if not row:
                return {"backlog_count": 0, "critical_count": 0, "most_urgent": None,
                        "avg_response_time_days": None, "candidates_advanced_this_week": 0,
                        "offers_pending": 0}

            company_id = row[0]
            summary = await recruiter_metrics_service.get_weekly_summary(
                recruiter_id=user_id,
                company_id=company_id,
                db=db,
            )
            summary["_company_id"] = company_id  # interno — usado pelo _get_recruiter_benchmark
            return summary
        except Exception as e:
            logger.warning(f"_get_recruiter_metrics failed silently: {e}", exc_info=True)
            return {"backlog_count": 0, "critical_count": 0, "most_urgent": None,
                    "avg_response_time_days": None, "candidates_advanced_this_week": 0,
                    "offers_pending": 0, "_company_id": None,
                    "degraded": True, "degraded_reason": type(e).__name__}

    async def _get_recruiter_benchmark(
        self,
        db: AsyncSession,
        user_id: str,
        recruiter_metrics: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Retorna comparação do recrutador com a mediana da empresa.
        Degrada silenciosamente — nunca lança exceção.
        """
        company_id = recruiter_metrics.get("_company_id")
        if not company_id:
            return {"benchmark_available": False}
        try:
            return await recruiter_metrics_service.get_recruiter_benchmark_comparison(
                recruiter_id=user_id,
                company_id=company_id,
                db=db,
            )
        except Exception as e:
            logger.warning(f"_get_recruiter_benchmark failed silently: {e}", exc_info=True)
            return {"benchmark_available": False, "degraded": True, "degraded_reason": type(e).__name__}

    async def _get_pipeline_prediction(
        self,
        db: AsyncSession,
        user_id: str,
        recruiter_metrics: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Retorna previsão de fechamento das vagas do recrutador.
        Degrada silenciosamente — nunca lança exceção.
        """
        company_id = recruiter_metrics.get("_company_id")
        if not company_id:
            return {"available": False, "vacancies": []}
        try:
            from app.shared.services.pipeline_prediction_service import pipeline_prediction_service
            vacancies = await pipeline_prediction_service.get_recruiter_vacancies_prediction(
                company_id=company_id,
                recruiter_id=user_id,
            )
            at_risk = [v for v in vacancies if v["closure_probability"] < 30]
            near_close = [v for v in vacancies if v["closure_probability"] >= 80]
            return {
                "available": True,
                "vacancies": sorted(vacancies, key=lambda x: x["closure_probability"]),
                "at_risk_count": len(at_risk),
                "near_closure_count": len(near_close),
            }
        except Exception as e:
            logger.warning(f"_get_pipeline_prediction failed silently: {e}", exc_info=True)
            return {"available": False, "vacancies": [], "degraded": True, "degraded_reason": type(e).__name__}

    async def _generate_insights(
        self,
        db: AsyncSession,
        user_id: str,
        pipeline: dict[str, Any],
        recruiter_metrics: dict[str, Any] | None = None,
        recruiter_benchmark: dict[str, Any] | None = None,
        pipeline_prediction: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Generate AI-powered insights based on data patterns."""
        insights = []

        # Backlog do recrutador — mais urgente que pipeline genérico
        if recruiter_metrics:
            backlog_count = recruiter_metrics.get("backlog_count", 0)
            critical_count = recruiter_metrics.get("critical_count", 0)
            most_urgent = recruiter_metrics.get("most_urgent")
            offers_pending = recruiter_metrics.get("offers_pending", 0)

            if critical_count > 0 and most_urgent:
                insights.append({
                    "type": "critical",
                    "icon": "AlertCircle",
                    "title": f"{critical_count} candidato(s) em situação crítica",
                    "description": (
                        f"Mais urgente: {most_urgent['candidate_name']} está na etapa "
                        f"'{most_urgent['stage']}' há {most_urgent['days_in_stage']} dias "
                        f"(limite: {most_urgent['threshold_days']} dias)."
                    ),
                    "priority": "critical",
                    "action": "Ver backlog",
                    "action_type": "view_recruiter_backlog",
                })
            elif backlog_count > 0 and most_urgent:
                insights.append({
                    "type": "attention",
                    "icon": "Clock",
                    "title": f"{backlog_count} candidato(s) aguardando sua ação",
                    "description": (
                        f"Mais antigo: {most_urgent['candidate_name']} na etapa "
                        f"'{most_urgent['stage']}' há {most_urgent['days_in_stage']} dias."
                    ),
                    "priority": "high",
                    "action": "Ver candidatos",
                    "action_type": "view_recruiter_backlog",
                })

            if offers_pending > 0:
                insights.append({
                    "type": "opportunity",
                    "icon": "TrendingUp",
                    "title": f"{offers_pending} oferta(s) aguardando resposta",
                    "description": "Candidatos na etapa de oferta precisam de retorno rápido para não perder o interesse.",
                    "priority": "high",
                    "action": "Ver ofertas",
                    "action_type": "view_offers_backlog",
                })

        if pipeline.get("awaiting_feedback", 0) > 3:
            insights.append({
                "type": "attention",
                "icon": "AlertTriangle",
                "title": "Feedbacks acumulados",
                "description": f"{pipeline['awaiting_feedback']} candidatos aguardando avaliação. Considere priorizar para não perder talentos.",
                "priority": "high",
                "action": "Ver candidatos",
                "action_type": "view_awaiting_feedback"
            })
        
        if pipeline.get("offers_pending", 0) > 0:
            insights.append({
                "type": "opportunity",
                "icon": "TrendingUp",
                "title": "Ofertas pendentes",
                "description": f"{pipeline['offers_pending']} candidato(s) com oferta. Acompanhe para garantir aceite.",
                "priority": "high",
                "action": "Ver ofertas",
                "action_type": "view_offers"
            })
        
        if pipeline.get("candidates_to_contact", 0) > 10:
            insights.append({
                "type": "suggestion",
                "icon": "Lightbulb",
                "title": "Alto volume em triagem",
                "description": f"{pipeline['candidates_to_contact']} candidatos para contatar. LIA pode ajudar com mensagens automatizadas.",
                "priority": "medium",
                "action": "Automatizar",
                "action_type": "automate_outreach"
            })
        
        if pipeline.get("active_jobs", 0) > 5:
            insights.append({
                "type": "info",
                "icon": "BarChart3",
                "title": "Vagas ativas",
                "description": f"Você tem {pipeline['active_jobs']} vagas abertas. Considere priorizar as mais urgentes.",
                "priority": "low",
                "action": "Ver vagas",
                "action_type": "view_jobs"
            })
        
        if not insights:
            insights.append({
                "type": "success",
                "icon": "CheckCircle",
                "title": "Tudo em dia!",
                "description": "Seu pipeline está saudável. Continue o bom trabalho!",
                "priority": "low",
            })

        # Sprint 2D — insights de benchmark
        if recruiter_benchmark and recruiter_benchmark.get("benchmark_available"):
            cmp = recruiter_benchmark.get("comparison", {})
            overall = recruiter_benchmark.get("overall_performance", "unknown")

            rt = cmp.get("response_time", {})
            cmp.get("advanced_per_week", {})

            if overall == "above_average":
                insights.append({
                    "type": "success",
                    "icon": "TrendingUp",
                    "title": "Performance acima da média da empresa",
                    "description": (
                        f"Você está acima da mediana em "
                        f"{sum(1 for c in cmp.values() if c.get('performance') == 'better')} "
                        f"de {len(cmp)} métricas acompanhadas."
                    ),
                    "priority": "low",
                    "action_type": "view_benchmark",
                })
            elif overall == "below_average":
                worst = next(
                    (
                        (k, v) for k, v in cmp.items()
                        if v.get("performance") == "worse" and v.get("delta") is not None
                    ),
                    None,
                )
                if worst:
                    k, v = worst
                    label_map = {
                        "response_time": "tempo de resposta",
                        "advanced_per_week": "candidatos avançados/semana",
                        "backlog_count": "backlog",
                        "offers_pending": "ofertas pendentes",
                    }
                    insights.append({
                        "type": "warning",
                        "icon": "TrendingDown",
                        "title": "Oportunidade de melhoria identificada",
                        "description": (
                            f"Seu {label_map.get(k, k)}: {v['personal']} "
                            f"(mediana da empresa: {v['benchmark']}). "
                            f"Pergunte à LIA: 'Como melhorar minha performance?' para dicas."
                        ),
                        "priority": "medium",
                        "action_type": "view_benchmark",
                    })

            # Insight específico de tempo de resposta se for destaque
            if rt.get("performance") == "better" and rt.get("personal") is not None:
                insights.append({
                    "type": "info",
                    "icon": "Clock",
                    "title": f"Tempo de resposta: {rt['personal']}d (mediana: {rt['benchmark']}d)",
                    "description": "Seu tempo de resposta está abaixo da mediana. Candidatos bem acompanhados.",
                    "priority": "low",
                    "action_type": "view_benchmark",
                })

        # Sprint 3A — insights de previsão de fechamento de vagas
        if pipeline_prediction and pipeline_prediction.get("available"):
            vacancies = pipeline_prediction.get("vacancies", [])
            at_risk_count = pipeline_prediction.get("at_risk_count", 0)
            near_count = pipeline_prediction.get("near_closure_count", 0)

            if at_risk_count > 0:
                at_risk = [v for v in vacancies if v["closure_probability"] < 30]
                worst = at_risk[0] if at_risk else {}
                insights.append({
                    "type": "warning",
                    "icon": "AlertTriangle",
                    "title": f"{at_risk_count} vaga(s) com pipeline em risco de não fechar",
                    "description": (
                        f"Mais crítica: '{worst.get('vacancy_title', 'Vaga')}' "
                        f"com {worst.get('closure_probability', 0)}% de probabilidade. "
                        f"Pergunte à LIA: 'O que está impedindo o fechamento?'"
                    ),
                    "priority": "high",
                    "action": "Ver vagas em risco",
                    "action_type": "view_pipeline_prediction",
                })

            if near_count > 0:
                near = [v for v in vacancies if v["closure_probability"] >= 80]
                best = near[-1] if near else {}
                est = best.get("estimated_days_to_close")
                days_str = f" em ~{est} dias" if est else ""
                insights.append({
                    "type": "success",
                    "icon": "TrendingUp",
                    "title": f"{near_count} vaga(s) prestes a fechar!",
                    "description": (
                        f"'{best.get('vacancy_title', 'Vaga')}' tem "
                        f"{best.get('closure_probability', 0)}% de probabilidade{days_str}. "
                        f"Prepare a proposta e alinhe com o gestor."
                    ),
                    "priority": "medium",
                    "action": "Ver previsões",
                    "action_type": "view_pipeline_prediction",
                })

        return insights


briefing_service = BriefingService()
