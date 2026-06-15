"""

# ADR-001-EXEMPT: Background apscheduler service performs cross-tenant
# periodic scans (e.g., overdue interviews, no-movement vacancies). Multi-tenancy
# enforced downstream when results are dispatched to per-tenant handlers.
# TODO Sprint 6: extract to dedicated CrossTenantSchedulerRepository with  # R-048: needs owner + ticket
# explicit  audit log + scoped methods per scan.

Automation Scheduler Service
Runs periodic jobs to check for conditions and trigger automation handlers.
"""
import logging
from datetime import UTC, datetime, timedelta
from typing import Any

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy import and_, select

from app.core.database import async_session_factory
from lia_models.candidate import Candidate, VacancyCandidate
from lia_models.interview import Interview
from lia_models.job_vacancy import JobVacancy

logger = logging.getLogger(__name__)

_event_dispatcher = None


def get_event_dispatcher():
    """Lazy load EventDispatcher to avoid circular imports."""
    global _event_dispatcher
    if _event_dispatcher is None:
        from app.shared.services.event_dispatcher import event_dispatcher
        _event_dispatcher = event_dispatcher
    return _event_dispatcher


class AutomationScheduler:
    """
    Scheduler service that runs periodic automation jobs.

    Jobs include:
    - Checking for inactive candidates (7+ days without activity)
    - Detecting interview no-shows
    - Sending interview reminders (24h and 1h before)
    - Checking for expiring vacancies

    Multi-instância: usa Redis jobstore quando disponível para garantir que cada
    job executa em apenas UMA instância por vez (coalesce=True, max_instances=1).
    Fallback automático para MemoryJobStore quando Redis indisponível.
    """

    def __init__(self):
        self.scheduler = self._build_scheduler()
        self._is_running = False
        self._email_service = None
        self._whatsapp_service = None
        self._activity_service = None
        self._notification_service = None
        self._pipeline_monitor = None
        self._learning_automation = None

    @staticmethod
    def _check_redis_available() -> bool:
        """Verifica se o Redis está acessível antes de tentar usar como jobstore."""
        try:
            import os
            import socket
            import urllib.parse
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
            parsed = urllib.parse.urlparse(redis_url)
            host = parsed.hostname or "localhost"
            port = parsed.port or 6379
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex((host, port))
            sock.close()
            return result == 0
        except Exception:
            return False

    def _build_scheduler(self) -> AsyncIOScheduler:
        """Constrói scheduler com MemoryJobStore.

        Redis jobstore desativado por incompatibilidade de pickle com ZoneInfo
        nos triggers CronTrigger/IntervalTrigger do APScheduler. Em ambiente
        single-instance (Replit / Cloud Run com 1 réplica), MemoryJobStore é
        suficiente. Para multi-instância, usar solução externa (Cloud Scheduler,
        Celery Beat com Redis backend, ou APScheduler 4.x quando estável).
        """
        import zoneinfo
        from apscheduler.jobstores.memory import MemoryJobStore
        jobstores = {"default": MemoryJobStore()}
        logger.info("[AutomationScheduler] Usando MemoryJobStore")
        job_defaults = {"coalesce": True, "max_instances": 1, "misfire_grace_time": 60}
        return AsyncIOScheduler(
            jobstores=jobstores,
            job_defaults=job_defaults,
            timezone=zoneinfo.ZoneInfo("America/Sao_Paulo"),
        )
    
    def _get_email_service(self):
        """Lazy load EmailService."""
        if self._email_service is None:
            try:
                from app.domains.communication.services.email_service import EmailService
                self._email_service = EmailService()
            except Exception as e:
                logger.warning(f"Could not load EmailService: {e}")
        return self._email_service
    
    def _get_whatsapp_service(self):
        """Lazy load WhatsAppService."""
        if self._whatsapp_service is None:
            try:
                from app.domains.communication.services.whatsapp_service import WhatsAppService
                self._whatsapp_service = WhatsAppService()
            except Exception as e:
                logger.warning(f"Could not load WhatsAppService: {e}")
        return self._whatsapp_service
    
    def _get_activity_service(self):
        """Lazy load ActivityService."""
        if self._activity_service is None:
            try:
                from app.domains.analytics.services.activity_service import ActivityService
                self._activity_service = ActivityService()
            except Exception as e:
                logger.warning(f"Could not load ActivityService: {e}")
        return self._activity_service
    
    def _get_notification_service(self):
        """Lazy load NotificationService."""
        if self._notification_service is None:
            try:
                from app.services.notification_service import NotificationService
                self._notification_service = NotificationService()
            except Exception as e:
                logger.warning(f"Could not load NotificationService: {e}")
        return self._notification_service
    
    def _get_pipeline_monitor(self):
        """Lazy load PipelineMonitor."""
        if self._pipeline_monitor is None:
            try:
                from app.domains.automation.services.pipeline_monitor import PipelineMonitor
                self._pipeline_monitor = PipelineMonitor()
            except Exception as e:
                logger.warning(f"Could not load PipelineMonitor: {e}")
        return self._pipeline_monitor
    
    def _get_learning_automation(self):
        """Lazy load LearningAutomationService."""
        if self._learning_automation is None:
            try:
                from app.domains.automation.services.learning_automation import LearningAutomationService
                self._learning_automation = LearningAutomationService()
            except Exception as e:
                logger.warning(f"Could not load LearningAutomationService: {e}")
        return self._learning_automation
    
    def start(self):
        """Start the scheduler with all jobs."""
        if self._is_running:
            logger.info("Automation Scheduler already running")
            return

        if not self._check_redis_available():
            logger.warning("[AutomationScheduler] Redis indisponível — scheduler usando MemoryJobStore (jobs não persistem entre restarts)")
        
        try:
            self.scheduler.add_job(
                self.check_inactive_candidates,
                IntervalTrigger(hours=1),
                id="check_inactive_candidates",
                name="Check for inactive candidates (7+ days)",
                replace_existing=True
            )
            
            self.scheduler.add_job(
                self.check_interview_no_shows,
                IntervalTrigger(minutes=30),
                id="check_interview_no_shows",
                name="Check for interview no-shows",
                replace_existing=True
            )
            
            self.scheduler.add_job(
                self.send_interview_reminders,
                IntervalTrigger(minutes=15),
                id="send_interview_reminders",
                name="Send interview reminders",
                replace_existing=True
            )
            
            self.scheduler.add_job(
                self.check_expiring_vacancies,
                CronTrigger(hour=9, minute=0),
                id="check_expiring_vacancies",
                name="Check for expiring vacancies",
                replace_existing=True
            )
            
            self.scheduler.add_job(
                self.cleanup_stale_reminders,
                CronTrigger(hour=0, minute=0),
                id="cleanup_stale_reminders",
                name="Daily cleanup of stale reminder flags",
                replace_existing=True
            )
            
            self.scheduler.add_job(
                self.auto_complete_expired_screenings,
                IntervalTrigger(hours=1),
                id="auto_complete_expired_screenings",
                name="Auto-complete screenings with expired end date",
                replace_existing=True
            )
            
            self.scheduler.add_job(
                self.run_pipeline_monitor,
                IntervalTrigger(minutes=30),
                id="pipeline_monitor",
                name="Monitor pipeline per company (proactive alerts)",
                replace_existing=True
            )
            
            self.scheduler.add_job(
                self.run_proactive_alerts,
                IntervalTrigger(hours=1),
                id="proactive_alerts",
                name="Proactive threshold alerts per company (P0-3)",
                replace_existing=True
            )

            self.scheduler.add_job(
                self.run_learning_automation,
                IntervalTrigger(hours=6),
                id="learning_automation",
                name="Run pattern detection and skill promotion",
                replace_existing=True
            )
            
            # M2 — Trial expiry check (daily at 01:00 BRT)
            self.scheduler.add_job(
                self.expire_trials,
                CronTrigger(hour=1, minute=0),
                id="expire_trials",
                name="M2 — Mark expired trials as suspended",
                replace_existing=True,
            )

            # L4 — LGPD data cleanup (daily at 02:00 BRT — after trial job)
            self.scheduler.add_job(
                self.run_lgpd_cleanup,
                CronTrigger(hour=2, minute=0),
                id="lgpd_cleanup",
                name="L4 — LGPD data retention cleanup",
                replace_existing=True,
            )

            self.scheduler.add_job(
                self.run_teams_proactive_checks,
                IntervalTrigger(hours=4),
                id="teams_proactive_checks",
                name="A2 — Teams proactive cards (stalled pipelines + deadlines)",
                replace_existing=True,
            )

            # Frente C — detectores proativos (15) por empresa, independente do MonitoringLoop

            self.scheduler.add_job(
                self.run_expire_pending_offers,
                IntervalTrigger(hours=1),
                id="expire_pending_offers",
                name="2.13 — Expirar propostas com deadline vencido",
                replace_existing=True,
            )

            self.scheduler.add_job(
                self.run_proactive_detection,
                IntervalTrigger(hours=1),
                id="proactive_detection",
                name="Proactive detectors (15) por empresa — independente do MonitoringLoop",
                replace_existing=True,
            )

            # F3 — AutonomousActionsEngine: executa ações de baixo risco automaticamente
            self.scheduler.add_job(
                self._run_autonomous_actions,
                IntervalTrigger(minutes=30),
                id="autonomous_actions",
                name="F3 — AutonomousActionsEngine (low-risk auto-execute)",
                replace_existing=True,
            )

            self.scheduler.start()
            # Daily digest — 08:00 BRT, Mon–Fri
            self.scheduler.add_job(
                self._run_daily_digest,
                CronTrigger(day_of_week="mon-fri", hour=8, minute=0),
                id="daily_platform_digest",
                replace_existing=True,
            )

            # A2 — Teams daily digest (DM do bot), 08:00 BRT Mon-Fri (Sao Paulo tz explicit)
            self.scheduler.add_job(
                self.run_teams_daily_digest,
                CronTrigger(
                    day_of_week="mon-fri",
                    hour=8,
                    minute=0,
                    timezone="America/Sao_Paulo",
                ),
                id="teams_daily_digest",
                name="A2 — Teams daily digest per recruiter",
                replace_existing=True,
                misfire_grace_time=3600,
            )

            self._is_running = True
            logger.info("✅ Automation Scheduler started with 10 periodic jobs")
            
        except Exception as e:
            logger.error(f"❌ Failed to start Automation Scheduler: {e}")
            raise
    
    @staticmethod
    def _is_digest_due(frequency: str) -> bool:
        """Verifica se é hora de enviar o digest conforme frequência configurada.

        O scheduler cron roda Mon-Fri às 08h. A decisão:
        - daily / twice_daily: sempre (cron já limita a dias úteis)
        - weekly: somente segunda-feira (weekday == 0)
        - monthly: somente dia 1 do mês

        Qualquer valor desconhecido → True (fail-open, envia por segurança).
        """
        now = datetime.now(UTC)
        if frequency == "weekly":
            return now.weekday() == 0  # somente segunda-feira
        if frequency == "monthly":
            return now.day == 1
        # daily, twice_daily, ou desconhecido → enviar
        return True

    async def _run_daily_digest(self):
        """Cron job: send daily morning digest to all recruiters (08:00 BRT Mon-Fri)."""
        logger.info("[AutomationScheduler] Running daily platform digest...")
        try:
            from app.domains.analytics.services.weekly_digest_service import WeeklyDigestService
            async with async_session_factory() as db:
                svc = WeeklyDigestService()
                result = await svc.send_to_all_recruiters(db)
                logger.info("[AutomationScheduler] Daily digest complete: %s", result)
        except Exception as exc:
            logger.error("[AutomationScheduler] Daily digest failed: %s", exc, exc_info=True)

    def stop(self):
        """Stop the scheduler gracefully."""
        if self._is_running:
            try:
                self.scheduler.shutdown(wait=True)
                self._is_running = False
                logger.info("🛑 Automation Scheduler stopped")
            except Exception as e:
                logger.error(f"Error stopping Automation Scheduler: {e}")
    
    @property
    def is_running(self) -> bool:
        """Check if scheduler is currently running."""
        return self._is_running
    
    def get_jobs_status(self) -> list[dict[str, Any]]:
        """Get status of all scheduled jobs."""
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append({
                "id": job.id,
                "name": job.name,
                "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
                "trigger": str(job.trigger)
            })
        return jobs
    
    async def check_inactive_candidates(self):
        """
        Check for candidates inactive for 7+ days and trigger follow-up.
        
        Looks at vacancy_candidates where:
        - Last update > 7 days ago
        - Not in final stage (hired, rejected, withdrawn)
        - Status is active (sourced, screening, interviewing)
        """
        logger.info("🔍 [Scheduler] Running check_inactive_candidates job")
        
        try:
            async with async_session_factory() as db:
                cutoff_date = datetime.utcnow() - timedelta(days=7)
                
                final_stages = ['hired', 'rejected', 'withdrawn', 'declined', 'offer_declined']
                
                result = await db.execute(
                    # TENANT-EXEMPT: automation_scheduler runs system-wide cron polling all tenants; per-tenant ops happen downstream with proper company_id
                    # TENANT-EXEMPT: automation_scheduler runs system-wide cron polling all tenants; per-tenant ops happen downstream with proper company_id
                    select(VacancyCandidate, Candidate, JobVacancy)
                    .join(Candidate, VacancyCandidate.candidate_id == Candidate.id)
                    .join(JobVacancy, VacancyCandidate.vacancy_id == JobVacancy.id)
                    .where(
                        and_(
                            VacancyCandidate.updated_at < cutoff_date,
                            ~VacancyCandidate.stage.in_(final_stages),
                            JobVacancy.status.in_(['Ativa', 'active', 'open'])
                        )
                    )
                    .limit(100)
                )
                
                inactive_candidates = result.all()
                
                if not inactive_candidates:
                    logger.info("✅ [Scheduler] No inactive candidates found")
                    return
                
                logger.info(f"📋 [Scheduler] Found {len(inactive_candidates)} inactive candidates")
                
                self._get_activity_service()
                self._get_notification_service()
                
                dispatcher = get_event_dispatcher()
                
                for vc, candidate, vacancy in inactive_candidates:
                    try:
                        days_inactive = (datetime.utcnow() - vc.updated_at).days
                        company_id = str(vacancy.company_id) if vacancy.company_id else vc.company_id
                        
                        await dispatcher.on_candidate_inactive(
                            candidate_id=str(vc.candidate_id),
                            vacancy_id=str(vc.vacancy_id),
                            company_id=company_id,
                            days_inactive=days_inactive,
                            current_stage=vc.stage,
                            candidate_name=candidate.name,
                            candidate_email=candidate.email,
                            candidate_phone=candidate.phone,
                            vacancy_title=vacancy.title,
                            recruiter_email=vacancy.recruiter_email
                        )
                        
                    except Exception as e:
                        logger.error(f"Error processing inactive candidate {vc.candidate_id}: {e}")
                
                logger.info(f"✅ [Scheduler] Processed {len(inactive_candidates)} inactive candidates")
                
        except Exception as e:
            logger.error(f"❌ [Scheduler] Error in check_inactive_candidates: {e}")
    
    async def check_interview_no_shows(self):
        """
        Check for interviews that happened but candidate didn't show.
        
        Looks at interviews where:
        - end_time < now (interview should be completed)
        - status is still 'scheduled' or 'confirmed'
        - More than 30 minutes past end time
        """
        logger.info("🔍 [Scheduler] Running check_interview_no_shows job")
        
        try:
            async with async_session_factory() as db:
                grace_period = datetime.utcnow() - timedelta(minutes=30)
                
                # TENANT-EXEMPT: automation_scheduler runs system-wide cron polling all tenants; per-tenant ops happen downstream with proper company_id
                result = await db.execute(
                    # TENANT-EXEMPT: automation_scheduler runs system-wide cron polling all tenants; per-tenant ops happen downstream with proper company_id
                    select(Interview)
                    .where(
                        and_(
                            Interview.end_time < grace_period,
                            Interview.status.in_(['scheduled', 'confirmed']),
                            Interview.status != 'no_show'
                        )
                    )
                    .limit(50)
                )
                
                potential_no_shows = result.scalars().all()
                
                if not potential_no_shows:
                    logger.info("✅ [Scheduler] No interview no-shows detected")
                    return
                
                logger.info(f"⚠️ [Scheduler] Found {len(potential_no_shows)} potential no-shows")
                
                dispatcher = get_event_dispatcher()
                
                for interview in potential_no_shows:
                    try:
                        interview.status = "no_show"
                        
                        vacancy_id = str(interview.job_vacancy_id) if interview.job_vacancy_id else "unknown"
                        candidate_id = str(interview.candidate_id) if interview.candidate_id else "unknown"
                        
                        company_id = None
                        if interview.job_vacancy_id:
                            vacancy_result = await db.execute(
                                select(JobVacancy.company_id).where(JobVacancy.id == interview.job_vacancy_id)
                            )
                            vacancy_company = vacancy_result.scalar_one_or_none()
                            if vacancy_company:
                                company_id = str(vacancy_company)
                        
                        await dispatcher.on_candidate_no_show(
                            candidate_id=candidate_id,
                            vacancy_id=vacancy_id,
                            company_id=company_id,
                            interview_id=str(interview.id),
                            scheduled_datetime=interview.start_time.isoformat(),
                            interview_type=interview.interview_type,
                            candidate_name=interview.candidate_name,
                            interviewer_name=interview.interviewer_name,
                            interviewer_email=interview.interviewer_email,
                            job_title=interview.job_title
                        )
                        
                    except Exception as e:
                        logger.error(f"Error processing no-show interview {interview.id}: {e}")
                
                await db.commit()
                logger.info(f"✅ [Scheduler] Processed {len(potential_no_shows)} no-show interviews")
                
        except Exception as e:
            try:
                await db.rollback()
            except Exception:
                pass
            logger.error(f"❌ [Scheduler] Error in check_interview_no_shows: {e}")
    
    async def send_interview_reminders(self):
        """
        Send reminders for upcoming interviews.
        
        - 24h before: send email + WhatsApp reminder
        - 1h before: send WhatsApp reminder only
        """
        logger.info("🔍 [Scheduler] Running send_interview_reminders job")
        
        try:
            async with async_session_factory() as db:
                now = datetime.utcnow()
                
                window_24h_start = now + timedelta(hours=23, minutes=45)
                window_24h_end = now + timedelta(hours=24, minutes=15)
                
                window_1h_start = now + timedelta(minutes=45)
                window_1h_end = now + timedelta(hours=1, minutes=15)
                # TENANT-EXEMPT: automation_scheduler runs system-wide cron polling all tenants; per-tenant ops happen downstream with proper company_id
                
                result_24h = await db.execute(
                    # TENANT-EXEMPT: automation_scheduler runs system-wide cron polling all tenants; per-tenant ops happen downstream with proper company_id
                    select(Interview)
                    .where(
                        and_(
                            Interview.start_time >= window_24h_start,
                            Interview.start_time <= window_24h_end,
                            Interview.status.in_(['scheduled', 'confirmed']),
                            not Interview.reminder_sent
                        )
                    )
                    .limit(50)
                )
                # TENANT-EXEMPT: automation_scheduler runs system-wide cron polling all tenants; per-tenant ops happen downstream with proper company_id
                interviews_24h = result_24h.scalars().all()
                
                result_1h = await db.execute(
                    # TENANT-EXEMPT: automation_scheduler runs system-wide cron polling all tenants; per-tenant ops happen downstream with proper company_id
                    select(Interview)
                    .where(
                        and_(
                            Interview.start_time >= window_1h_start,
                            Interview.start_time <= window_1h_end,
                            Interview.status.in_(['scheduled', 'confirmed'])
                        )
                    )
                    .limit(50)
                )
                interviews_1h = result_1h.scalars().all()
                
                email_service = self._get_email_service()
                whatsapp_service = self._get_whatsapp_service()
                activity_service = self._get_activity_service()
                
                for interview in interviews_24h:
                    try:
                        if email_service and interview.candidate_email:
                            await self._send_reminder_email(
                                email_service,
                                interview,
                                hours_until=24
                            )
                        
                        interview.reminder_sent = True
                        interview.reminder_sent_at = now
                        
                        if activity_service:
                            await activity_service.create_activity(
                                activity_type="interview_reminder_sent",
                                title="Lembrete de entrevista enviado (24h)",
                                description=f"Lembrete enviado para {interview.candidate_name} sobre entrevista amanhã.",
                                actor_id="automation_scheduler",
                                actor_name="LIA Automation",
                                actor_type="system",
                                target_id=str(interview.candidate_id) if interview.candidate_id else "unknown",
                                target_type="interview",
                                extra_data={
                                    "interview_id": str(interview.id),
                                    "reminder_type": "24h",
                                    "channel": "email"
                                },
                                category="communication"
                            )
                        
                    except Exception as e:
                        logger.error(f"Error sending 24h reminder for interview {interview.id}: {e}")
                
                for interview in interviews_1h:
                    try:
                        if whatsapp_service and hasattr(interview, 'candidate_phone') and interview.candidate_email:
                            pass
                        
                        if activity_service:
                            await activity_service.create_activity(
                                activity_type="interview_reminder_sent",
                                title="Lembrete de entrevista enviado (1h)",
                                description=f"Lembrete enviado para {interview.candidate_name} sobre entrevista em 1 hora.",
                                actor_id="automation_scheduler",
                                actor_name="LIA Automation",
                                actor_type="system",
                                target_id=str(interview.candidate_id) if interview.candidate_id else "unknown",
                                target_type="interview",
                                extra_data={
                                    "interview_id": str(interview.id),
                                    "reminder_type": "1h",
                                    "channel": "whatsapp"
                                },
                                category="communication"
                            )
                        
                    except Exception as e:
                        logger.error(f"Error sending 1h reminder for interview {interview.id}: {e}")
                
                await db.commit()
                
                total_sent = len(interviews_24h) + len(interviews_1h)
                if total_sent > 0:
                    logger.info(f"✅ [Scheduler] Sent {len(interviews_24h)} 24h reminders, {len(interviews_1h)} 1h reminders")
                else:
                    logger.info("✅ [Scheduler] No interview reminders needed at this time")
                
        except Exception as e:
            try:
                await db.rollback()
            except Exception:
                pass
            logger.error(f"❌ [Scheduler] Error in send_interview_reminders: {e}")
    
    async def _send_reminder_email(self, email_service, interview: Interview, hours_until: int):
        """Send interview reminder email."""
        try:
            subject = f"Lembrete: Entrevista em {hours_until} horas - {interview.job_title or 'Vaga'}"
            
            interview_time = interview.start_time.strftime("%d/%m/%Y às %H:%M")
            meeting_info = f"\n\nLink da reunião: {interview.meeting_url}" if interview.meeting_url else ""
            
            body = f"""
Olá {interview.candidate_name},

Este é um lembrete de que você tem uma entrevista agendada:

📅 Data e hora: {interview_time}
📝 Tipo: {interview.interview_type}
👤 Entrevistador(a): {interview.interviewer_name}
{meeting_info}

Por favor, confirme sua presença respondendo a este e-mail.

Boa sorte!

Atenciosamente,
Equipe de Recrutamento
"""
            
            await email_service.send_email(
                to_email=interview.candidate_email,
                subject=subject,
                body=body
            )
            
            logger.info("✉️ Reminder email sent")
            
        except Exception as e:
            logger.error(f"Failed to send reminder email: {e}")
    
    async def check_expiring_vacancies(self):
        """
        Check for vacancies expiring in next 7 days.
        Notify recruiters about vacancies that need attention.
        """
        logger.info("🔍 [Scheduler] Running check_expiring_vacancies job")
        
        try:
            async with async_session_factory() as db:
                # TENANT-EXEMPT: automation_scheduler runs system-wide cron polling all tenants; per-tenant ops happen downstream with proper company_id
                now = datetime.utcnow()
                seven_days_from_now = now + timedelta(days=7)
                
                result = await db.execute(
                    # TENANT-EXEMPT: automation_scheduler runs system-wide cron polling all tenants; per-tenant ops happen downstream with proper company_id
                    select(JobVacancy)
                    .where(
                        and_(
                            JobVacancy.deadline.isnot(None),
                            JobVacancy.deadline >= now,
                            JobVacancy.deadline <= seven_days_from_now,
                            JobVacancy.status.in_(['Ativa', 'active', 'open'])
                        )
                    )
                    .limit(50)
                )
                
                expiring_vacancies = result.scalars().all()
                
                if not expiring_vacancies:
                    logger.info("✅ [Scheduler] No expiring vacancies found")
                    return
                
                logger.info(f"⚠️ [Scheduler] Found {len(expiring_vacancies)} vacancies expiring soon")
                
                activity_service = self._get_activity_service()
                notification_service = self._get_notification_service()
                
                for vacancy in expiring_vacancies:
                    try:
                        days_until_deadline = (vacancy.deadline - now).days
                        
                        if activity_service:
                            await activity_service.create_activity(
                                activity_type="vacancy_expiring_alert",
                                title=f"Vaga expira em {days_until_deadline} dias",
                                description=f"A vaga '{vacancy.title}' tem prazo até {vacancy.deadline.strftime('%d/%m/%Y')}.",
                                actor_id="automation_scheduler",
                                actor_name="LIA Automation",
                                actor_type="system",
                                target_id=str(vacancy.id),
                                target_type="job_vacancy",
                                extra_data={
                                    "vacancy_id": str(vacancy.id),
                                    "vacancy_title": vacancy.title,
                                    "company_id": vacancy.company_id,
                                    "deadline": vacancy.deadline.isoformat(),
                                    "days_until_deadline": days_until_deadline,
                                    "recruiter_email": vacancy.recruiter_email
                                },
                                category="automation"
                            )
                        
                        if notification_service and vacancy.recruiter_email:
                            await notification_service.create_notification(
                                user_id=vacancy.recruiter_email,
                                company_id=vacancy.company_id,
                                title=f"Vaga expirando em {days_until_deadline} dias",
                                message=f"A vaga '{vacancy.title}' tem prazo até {vacancy.deadline.strftime('%d/%m/%Y')}. Considere tomar ação.",
                                notification_type="vacancy_expiring",
                                priority="high" if days_until_deadline <= 3 else "medium",
                                action_url=f"/jobs/{vacancy.id}"
                            )
                        
                    except Exception as e:
                        logger.error(f"Error processing expiring vacancy {vacancy.id}: {e}")
                
                logger.info(f"✅ [Scheduler] Processed {len(expiring_vacancies)} expiring vacancies")
                
        except Exception as e:
            logger.error(f"❌ [Scheduler] Error in check_expiring_vacancies: {e}")
    
    async def cleanup_stale_reminders(self):
        """
        Daily cleanup job to reset reminder flags for old interviews.
        This prevents data bloat and ensures reminders work for rescheduled interviews.
        """
        logger.info("🔍 [Scheduler] Running cleanup_stale_reminders job")
        
        try:
            async with async_session_factory() as db:
                # TENANT-EXEMPT: automation_scheduler runs system-wide cron polling all tenants; per-tenant ops happen downstream with proper company_id
                cutoff = datetime.utcnow() - timedelta(days=7)
                
                from sqlalchemy import update
                
                await db.execute(
                    # TENANT-EXEMPT: automation_scheduler runs system-wide cron polling all tenants; per-tenant ops happen downstream with proper company_id
                    update(Interview)
                    .where(
                        and_(
                            Interview.end_time < cutoff,
                            Interview.reminder_sent
                        )
                    )
                    .values(reminder_sent=False, reminder_sent_at=None)
                )
                
                await db.commit()
                logger.info("✅ [Scheduler] Cleaned up stale reminder flags")
                
        except Exception as e:
            try:
                await db.rollback()
            except Exception:
                pass
            logger.error(f"❌ [Scheduler] Error in cleanup_stale_reminders: {e}")
    
    async def auto_complete_expired_screenings(self):
        """
        Auto-complete screenings with expired scheduled_end_date.
        
        Checks for job vacancies where:
        - screening_config.status.screening_status = 'active'
        - screening_config.status.scheduled_end_date is in the past
        
        Sets them to 'completed' and disables screening.
        """
        logger.info("🔍 [Scheduler] Running auto_complete_expired_screenings job")
        # TENANT-EXEMPT: automation_scheduler runs system-wide cron polling all tenants; per-tenant ops happen downstream with proper company_id
        
        try:
            async with async_session_factory() as db:
                now = datetime.utcnow()
                
                result = await db.execute(
                    # TENANT-EXEMPT: automation_scheduler runs system-wide cron polling all tenants; per-tenant ops happen downstream with proper company_id
                    select(JobVacancy).where(
                        JobVacancy.screening_config.isnot(None)
                    )
                )
                
                jobs = result.scalars().all()
                completed_count = 0
                
                for job in jobs:
                    try:
                        config = job.screening_config
                        if not config or not isinstance(config, dict):
                            continue
                        
                        status = config.get("status", {})
                        if not isinstance(status, dict):
                            continue
                        
                        screening_status = status.get("screening_status")
                        scheduled_end_date = status.get("scheduled_end_date")
                        
                        if screening_status != "active" or not scheduled_end_date:
                            continue
                        
                        try:
                            if isinstance(scheduled_end_date, str):
                                end_date_str_clean = scheduled_end_date.replace('Z', '+00:00')
                                end_date = datetime.fromisoformat(end_date_str_clean)
                                if end_date.tzinfo is None:
                                    end_date = end_date.replace(tzinfo=UTC)
                            else:
                                end_date = scheduled_end_date
                                if hasattr(end_date, 'tzinfo') and end_date.tzinfo is None:
                                    end_date = end_date.replace(tzinfo=UTC)
                            now_tz = datetime.now(UTC)
                        except (ValueError, TypeError):
                            logger.warning(f"Invalid scheduled_end_date for job {job.id}: {scheduled_end_date}")
                            continue
                        
                        if end_date > now_tz:
                            continue
                        
                        updated_config = dict(config)
                        updated_status = dict(status)
                        updated_status["screening_status"] = "completed"
                        updated_status["enabled"] = False
                        updated_status["completed_at"] = now.isoformat()
                        updated_status["last_updated"] = now.isoformat()
                        updated_config["status"] = updated_status
                        job.screening_config = updated_config
                        
                        completed_count += 1
                        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
                        logger.info(f"✅ [Scheduler] Auto-completed screening for job {job.id} ({job.title}) - end date was {scheduled_end_date}")
                        
                    except Exception as e:
                        logger.error(f"Error processing screening auto-completion for job {job.id}: {e}")
                
                if completed_count > 0:
                    await db.commit()
                    logger.info(f"✅ [Scheduler] Auto-completed {completed_count} expired screenings")
                else:
                    logger.info("✅ [Scheduler] No expired screenings found")
                
        except Exception as e:
            try:
                await db.rollback()
            except Exception:
                pass
            logger.error(f"❌ [Scheduler] Error in auto_complete_expired_screenings: {e}")
    
    async def run_pipeline_monitor(self):
        """Run PipelineMonitor scan for all companies and process events."""
        logger.info("🔍 [Scheduler] Running pipeline_monitor job")
        try:
            monitor = self._get_pipeline_monitor()
            if monitor:
                events = await monitor.scan_all_companies()
                logger.info(f"📊 [Scheduler] Pipeline monitor found {len(events)} events")
                
                if events:
                    try:
                        from app.domains.automation.services.event_action_connector import event_action_connector
                        stats = await event_action_connector.process_events(events)
                        logger.info(f"✅ [Scheduler] Pipeline monitor completed: {stats}")
                    except Exception as e:
                        logger.error(f"⚠️ [Scheduler] Error processing events: {e}")
                else:
                    logger.info("✅ [Scheduler] Pipeline monitor completed: no events")
            else:
                logger.warning("⚠️ [Scheduler] PipelineMonitor not available")
        except Exception as e:
            logger.error(f"❌ [Scheduler] Error in pipeline_monitor: {e}")
    
    # E5 (2026-06-09): destinatarios de alertas proativos = TODOS os recrutadores
    # ativos (admin/manager/recruiter), nao so 1 admin/empresa. Decisao Paulo:
    # cada recrutador recebe conforme sua preferencia (cooldown por-user evita spam).
    # Strings literais (StrEnum.value) p/ nao exigir import de UserRole no nivel de classe.
    PROACTIVE_ALERT_RECIPIENT_ROLES = ("admin", "manager", "recruiter")

    @staticmethod
    async def _select_proactive_alert_recipients(db):
        """Retorna [(company_id, user_id)] de todos os recrutadores ativos.

        Substitui a antiga query func.min(User.id) group by company_id (que
        limitava a 1 admin/empresa). Sem group_by: cada admin/manager/recruiter
        ativo recebe seus alertas conforme AlertPreference + cooldown por-user.
        """
        from sqlalchemy import select as _select
        from app.auth.models import User

        res = await db.execute(
            _select(User.company_id, User.id).where(
                User.role.in_(AutomationScheduler.PROACTIVE_ALERT_RECIPIENT_ROLES),
                User.is_active.is_(True),
                User.company_id.isnot(None),
            )
        )
        return list(res.all())

    @staticmethod
    async def _select_active_company_ids(db) -> list:
        """Retorna company_ids distintos com pelo menos um usuario ativo.

        Usado por run_proactive_detection para iterar por empresa sem repetir.
        Diferente de _select_proactive_alert_recipients (que retorna pares user+company
        para envio de alertas individuais): aqui queremos 1 execucao de detectores por empresa.
        """
        from sqlalchemy import select as _select
        from app.auth.models import User

        res = await db.execute(
            _select(User.company_id)
            .where(User.is_active.is_(True), User.company_id.isnot(None))
            .distinct()
        )
        return [str(row[0]) for row in res.all()]

    async def run_proactive_alerts(self):
        """P0-3 (auditoria Configuracoes): dispara ProactiveAlertService autonomamente.

        Antes os 15 tipos de alerta configuraveis so rodavam se o recrutador
        digitasse no chat. Agora roda 1x/hora para 1 admin representativo de cada
        empresa (cooldown por-usuario em _can_send_alert evita spam entre runs).
        """
        logger.info("[Scheduler] Running proactive_alerts job")
        try:
            from app.domains.automation.services.proactive_alert_service import (
                proactive_alert_service,
            )
            async with async_session_factory() as db:
                # TENANT-EXEMPT: cron system-wide; check_all_conditions reaplica company_id por tenant
                # E5 (2026-06-09): TODOS os recrutadores ativos (admin/manager/recruiter),
                # nao so 1 admin/empresa. Cada um recebe conforme sua preferencia.
                pairs = await AutomationScheduler._select_proactive_alert_recipients(db)
                logger.info(f"[Scheduler] proactive_alerts: {len(pairs)} destinatarios")
                for company_id, user_id in pairs:
                    try:
                        await proactive_alert_service.check_all_conditions(
                            user_id=str(user_id),
                            company_id=str(company_id),
                            db=db,
                        )
                    except Exception as e:
                        await db.rollback()
                        logger.error(f"[Scheduler] proactive_alerts company={company_id} falhou: {e}")
        except Exception as e:
            logger.error(f"[Scheduler] Error in proactive_alerts: {e}")

    async def run_teams_proactive_checks(self):
        """A2 (2026-06-09): aciona TeamsProactivityEngine periodicamente.

        Antes so via REST manual (teams.py) — nenhum scheduler acionava, entao os
        cards proativos do Teams (DM do bot por recrutador) nunca eram postados.
        company_id=None => processa todas as empresas. Posta pipelines parados +
        deadlines proximos. Complementa o canal compartilhado (webhook via E4).
        """
        logger.info("[Scheduler] Running teams_proactive_checks job")
        try:
            from app.domains.communication.services.teams_proactivity_engine import (
                teams_proactivity_engine,
            )

            stalled = await teams_proactivity_engine.check_stalled_pipelines()
            deadlines = await teams_proactivity_engine.check_approaching_deadlines()
            logger.info(
                "[Scheduler] teams_proactive_checks: stalled=%s deadlines=%s",
                stalled,
                deadlines,
            )
        except Exception as e:
            logger.error(f"[Scheduler] Error in teams_proactive_checks: {e}")

    async def run_proactive_detection(self):
        """Frente C: executa os 15 detectores proativos por empresa.

        Roda independente do MonitoringLoop (que era o unico trigger em dev).
        O MonitoringLoop mantem seu piggyback como defesa-em-profundidade.
        Cada empresa e isolada: erro em uma nao afeta as outras.
        """
        logger.info("[Scheduler] Running proactive_detection job")
        try:
            from app.shared.services.proactive_detector_service import (
                proactive_detector_service,
            )
            async with async_session_factory() as db:
                company_ids = await AutomationScheduler._select_active_company_ids(db)
                logger.info(
                    "[Scheduler] proactive_detection: %s companies para detectar",
                    len(company_ids),
                )
                detected_total = 0
                for company_id in company_ids:
                    try:
                        result = await proactive_detector_service.run_for_company(
                            db, company_id
                        )
                        detected_total += result.get("hints_persisted", 0)
                    except Exception as exc:
                        await db.rollback()
                        logger.error(
                            "[Scheduler] proactive_detection company=%s falhou: %s",
                            company_id,
                            exc,
                        )
                logger.info(
                    "[Scheduler] proactive_detection: %s hints persistidos total",
                    detected_total,
                )
        except Exception as exc:
            logger.error("[Scheduler] Error in proactive_detection: %s", exc)

    async def run_teams_daily_digest(self):
        """A2 (2026-06-09): digest diario do TeamsProactivityEngine (DM do bot)."""
        logger.info("[Scheduler] Running teams_daily_digest job")
        try:
            from app.domains.communication.services.teams_proactivity_engine import (
                teams_proactivity_engine,
            )

            sent = await teams_proactivity_engine.send_daily_digest()
            logger.info(f"[Scheduler] teams_daily_digest: {sent} enviados")
        except Exception as e:
            logger.error(f"[Scheduler] Error in teams_daily_digest: {e}")

    async def run_learning_automation(self):
        """Run learning automation: pattern detection and skill promotion for all companies."""
        logger.info("🔍 [Scheduler] Running learning_automation job")
        try:
            service = self._get_learning_automation()
            if service:
                summary = await service.run_all_companies()
                logger.info(
                    f"✅ [Scheduler] Learning automation completed: "
                    f"{summary.get('companies_processed', 0)} companies, "
                    f"{summary.get('total_correction_patterns', 0)} patterns, "
                    f"{summary.get('total_skills_promoted', 0)} skills promoted"
                )
            else:
                logger.warning("⚠️ [Scheduler] LearningAutomationService not available")
        except Exception as e:
            logger.error(f"❌ [Scheduler] Error in learning_automation: {e}")
    
    async def run_job_now(self, job_id: str) -> dict[str, Any]:
        """
        Manually trigger a specific job to run immediately.
        Useful for testing or forcing an immediate check.
        """
        job_map = {
            "check_inactive_candidates": self.check_inactive_candidates,
            "check_interview_no_shows": self.check_interview_no_shows,
            "send_interview_reminders": self.send_interview_reminders,
            "check_expiring_vacancies": self.check_expiring_vacancies,
            "cleanup_stale_reminders": self.cleanup_stale_reminders,
            "auto_complete_expired_screenings": self.auto_complete_expired_screenings,
            "pipeline_monitor": self.run_pipeline_monitor,
            "learning_automation": self.run_learning_automation
        }
        
        if job_id not in job_map:
            return {"success": False, "error": f"Unknown job: {job_id}"}
        
        try:
            await job_map[job_id]()
            return {"success": True, "message": f"Job {job_id} executed successfully"}
        except Exception as e:
            logger.error(f"Error manually running job {job_id}: {e}")
            return {"success": False, "error": str(e)}


    async def expire_trials(self):
        """
        M2 — Mark TRIALING subscriptions whose trial_end has passed as SUSPENDED.
        Runs daily at 01:00. The trial_enforcement dependency handles per-request
        blocking; this job ensures the DB status stays consistent overnight.
        """
        try:
            from datetime import datetime as _dt

            from sqlalchemy import update

            from app.core.database import async_session_factory
            from lia_models.billing import Subscription, SubscriptionStatus

            async with async_session_factory() as db:
                now = _dt.utcnow()
                result = await db.execute(
                    update(Subscription)
                    .where(
                        Subscription.status == SubscriptionStatus.TRIALING.value,
                        Subscription.trial_end.isnot(None),
                        Subscription.trial_end < now,
                    )
                    .values(status=SubscriptionStatus.SUSPENDED.value)
                    .returning(Subscription.id, Subscription.client_id)
                )
                expired = result.all()
                await db.commit()
                logger.info("M2 expire_trials: %d subscriptions suspended", len(expired))
        except Exception as exc:
            try:
                await db.rollback()
            except Exception:
                pass
            logger.error("M2 expire_trials failed: %s", exc)

    async def run_expire_pending_offers(self) -> None:
        """2.13 — Mark offers as expired when response_deadline passed.

        Runs hourly. Queries ALL tenants for pending offers with deadline < now.
        For each: marks status=expired + fires OFFER_EXPIRED trigger (fail-soft).
        """
        try:
            from app.core.database import async_session_factory
            from app.domains.offer.repositories.offer_repository import OfferRepository
            from app.domains.offer.services.offer_service import OfferService

            async with async_session_factory() as db:
                repo = OfferRepository(db)
                expired_offers = await repo.list_deadline_passed(limit=500)

                if not expired_offers:
                    logger.debug("[expire_offers] no pending expired offers found")
                    return

                logger.info("[expire_offers] found %d offers to expire", len(expired_offers))

                for offer in expired_offers:
                    try:
                        svc = OfferService(db)
                        await svc.mark_expired(
                            offer_id=offer.id,
                            company_id=offer.company_id,
                        )
                        await db.commit()
                        logger.info(
                            "[expire_offers] expired offer=%s company=%s candidate=%s",
                            offer.id, offer.company_id, offer.candidate_name,
                        )
                    except Exception as _e:
                        await db.rollback()
                        logger.warning(
                            "[expire_offers] failed to expire offer=%s: %s",
                            offer.id, _e,
                        )

        except Exception as exc:
            logger.error("[expire_offers] scheduler job failed: %s", exc)


    async def run_lgpd_cleanup(self):
        """
        L4 — Execute LGPD data retention cleanup (real deletions, not dry-run).
        Runs daily at 02:00, after expire_trials.
        """
        try:
            from app.shared.services.lgpd_cleanup_service import run_cleanup
            summary = await run_cleanup(dry_run=False)
            logger.info(
                "L4 lgpd_cleanup: candidates=%d vacancy_candidates=%d errors=%d",
                summary["candidates_deleted"],
                summary["vacancy_candidates_deleted"],
                len(summary["errors"]),
            )
        except Exception as exc:
            logger.error("L4 lgpd_cleanup failed: %s", exc)


    async def _run_autonomous_actions(self) -> None:
        """F3 — Wire AutonomousActionsEngine no scheduler.

        Para cada empresa ativa, coleta os alerts do MonitoringLoop (via run_checks)
        e os repassa para AutonomousActionsEngine.process_monitoring_alerts().
        Ações de baixo risco com confidence >= 0.85 são executadas automaticamente.
        Ações de médio risco geram notificação. Alto risco requer confirmação.
        """
        logger.info("[Scheduler] Running autonomous_actions job")
        try:
            from app.domains.recruiter_assistant.services.autonomous_actions_engine import (
                AutonomousActionsEngine,
            )
            from app.domains.recruiter_assistant.services.monitoring_loop import (
                MonitoringLoop,
            )

            engine = AutonomousActionsEngine.get_instance()
            monitoring = MonitoringLoop.get_instance()

            async with async_session_factory() as db:
                company_ids = await AutomationScheduler._select_active_company_ids(db)

            logger.info(
                "[Scheduler] autonomous_actions: %s companies para processar",
                len(company_ids),
            )
            actions_total = 0
            for company_id in company_ids:
                try:
                    # Obtém alerts já armazenados no MonitoringLoop (sem novo I/O por empresa)
                    alerts = monitoring.get_alerts(company_id)
                    if not alerts:
                        # Se não há alerts em memória, roda run_checks para popula-los
                        alerts = await monitoring.run_checks(company_id)
                    if alerts:
                        actions = await engine.process_monitoring_alerts(
                            company_id=company_id,
                            alerts=alerts,
                        )
                        actions_total += len(actions)
                        logger.debug(
                            "[Scheduler] autonomous_actions company=%s alerts=%s actions=%s",
                            company_id,
                            len(alerts),
                            len(actions),
                        )
                except Exception as exc:
                    logger.warning(
                        "[Scheduler] autonomous_actions company=%s falhou: %s",
                        company_id,
                        exc,
                    )
            logger.info(
                "[Scheduler] autonomous_actions concluído: %s actions propostas",
                actions_total,
            )
        except Exception as exc:
            logger.error("[Scheduler] Error in autonomous_actions: %s", exc, exc_info=True)


automation_scheduler = AutomationScheduler()
