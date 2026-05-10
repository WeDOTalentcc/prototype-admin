"""
Scheduled Report Jobs - Automatic report generation and delivery.

This module provides scheduled job classes for automatic report generation.
It includes structure for integration with APScheduler or Celery.

SECURITY NOTE:
    This module uses a feature flag ENABLE_SCHEDULED_REPORTS to control
    whether scheduled reports are actually sent. By default, it is disabled
    to prevent accidental email sending in development/staging environments.
    
    Set ENABLE_SCHEDULED_REPORTS=true in environment to enable.

Usage with APScheduler:
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    from app.jobs.scheduled_reports import scheduled_report_job
    
    scheduler = AsyncIOScheduler()
    
    # Daily briefing at 7:00 AM
    scheduler.add_job(
        scheduled_report_job.run_daily_briefings,
        'cron',
        hour=7,
        minute=0,
        id='daily_briefing_job'
    )
    
    # Weekly report on Monday at 8:00 AM
    scheduler.add_job(
        scheduled_report_job.run_weekly_reports,
        'cron',
        day_of_week='mon',
        hour=8,
        minute=0,
        id='weekly_report_job'
    )
    
    # Monthly report on 1st of month at 9:00 AM
    scheduler.add_job(
        scheduled_report_job.run_monthly_reports,
        'cron',
        day=1,
        hour=9,
        minute=0,
        id='monthly_report_job'
    )
    
    scheduler.start()

Usage with Celery:
    from celery import Celery
    from celery.schedules import crontab
    from app.jobs.scheduled_reports import scheduled_report_job
    
    app = Celery('lia_tasks', broker='redis://localhost:6379/0')
    
    @app.task
    def daily_briefing_task():
        import asyncio
        asyncio.run(scheduled_report_job.run_daily_briefings())
    
    @app.task
    def weekly_report_task():
        import asyncio
        asyncio.run(scheduled_report_job.run_weekly_reports())
    
    @app.task
    def monthly_report_task():
        import asyncio
        asyncio.run(scheduled_report_job.run_monthly_reports())
    
    app.conf.beat_schedule = {
        'daily-briefing': {
            'task': 'daily_briefing_task',
            'schedule': crontab(hour=7, minute=0),
        },
        'weekly-report': {
            'task': 'weekly_report_task',
            'schedule': crontab(day_of_week=1, hour=8, minute=0),
        },
        'monthly-report': {
            'task': 'monthly_report_task',
            'schedule': crontab(day_of_month=1, hour=9, minute=0),
        },
    }
"""
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.domains.analytics.services.report_service import report_service

logger = logging.getLogger(__name__)

ENABLE_SCHEDULED_REPORTS = os.getenv("ENABLE_SCHEDULED_REPORTS", "false").lower() == "true"
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
IS_PRODUCTION = ENVIRONMENT.lower() == "production"


@dataclass
class ReportRecipient:
    """Represents a report recipient."""
    user_id: str
    email: str
    name: str
    company_id: str | None = None
    company_name: str = "Empresa"
    report_types: list[str] = field(default_factory=lambda: ["daily"])


@dataclass
class ReportJobConfig:
    """Configuration for scheduled report jobs."""
    daily_briefing_enabled: bool = True
    daily_briefing_hour: int = 7
    daily_briefing_minute: int = 0
    
    weekly_report_enabled: bool = True
    weekly_report_day: int = 0
    weekly_report_hour: int = 8
    weekly_report_minute: int = 0
    
    monthly_report_enabled: bool = True
    monthly_report_day: int = 1
    monthly_report_hour: int = 9
    monthly_report_minute: int = 0
    
    timezone: str = "America/Sao_Paulo"


class ScheduledReportJob:
    """
    Scheduled job handler for automatic report generation.
    
    This class manages the execution of scheduled reports including:
    - Daily briefings for recruiters
    - Weekly performance reports for teams
    - Monthly executive reports for managers
    
    Integration Points:
    - APScheduler: Use with AsyncIOScheduler for async job execution
    - Celery: Wrap methods in Celery tasks for distributed execution
    - Custom: Call methods directly from any scheduler
    """
    
    def __init__(self, config: ReportJobConfig | None = None):
        """
        Initialize the scheduled report job handler.
        
        Args:
            config: Optional job configuration
        """
        self.config = config or ReportJobConfig()
        self.report_service = report_service
        self._recipients_cache: dict[str, list[ReportRecipient]] = {}
        self._last_run: dict[str, datetime] = {}
    
    async def run_daily_briefings(self) -> dict[str, Any]:
        """
        Execute daily briefing job for all eligible recipients.
        
        This method should be called by the scheduler at the configured time.
        It fetches all users who should receive daily briefings and sends
        personalized reports to each.
        
        Returns:
            Job execution summary with success/failure counts
        """
        if not ENABLE_SCHEDULED_REPORTS:
            logger.warning(
                "⚠️ Scheduled reports disabled - set ENABLE_SCHEDULED_REPORTS=true to enable"
            )
            return {
                "job_type": "daily_briefing",
                "status": "disabled",
                "message": "Scheduled reports are disabled. Set ENABLE_SCHEDULED_REPORTS=true to enable.",
                "environment": ENVIRONMENT
            }
        
        if not IS_PRODUCTION:
            logger.warning(
                f"⚠️ Running daily briefings in {ENVIRONMENT} environment. "
                "Emails may be simulated or sent to test addresses only."
            )
        
        job_start = datetime.now()
        logger.info("🚀 Starting daily briefing job...")
        
        results = {
            "job_type": "daily_briefing",
            "started_at": job_start.isoformat(),
            "environment": ENVIRONMENT,
            "recipients_processed": 0,
            "emails_sent": 0,
            "emails_failed": 0,
            "errors": [],
        }
        
        try:
            recipients = await self._get_daily_briefing_recipients()
            results["recipients_processed"] = len(recipients)
            
            if not recipients:
                logger.info("ℹ️ No recipients configured for daily briefings")
                results["message"] = "No recipients configured"
                return results
            
            for recipient in recipients:
                try:
                    if not recipient.company_id:
                        # pii-logs ok: email/phone mascarado em runtime via PIIMaskingFilter (LGPD Art.46 + ADR-006 defesa em profundidade)
                        logger.warning(f"⚠️ Skipping recipient {recipient.user_id} - no company_id")
                        results["errors"].append({
                            "user_id": recipient.user_id,
                            "error": "missing_company_id"
                        })
                        continue
                    
                    async with AsyncSessionLocal() as db:
                        result = await self.report_service.generate_daily_briefing_email(
                            user_id=recipient.user_id,
                            user_email=recipient.email,
                            user_name=recipient.name,
                            company_name=recipient.company_name,
                            db=db,
                            send_email=True
                        )
                        
                        if result.get("email_sent"):
                            results["emails_sent"] += 1
                            # pii-logs ok: email/phone mascarado em runtime via PIIMaskingFilter (LGPD Art.46 + ADR-006 defesa em profundidade)
                            logger.info(f"Daily briefing sent to recipient_id={recipient.id}")
                        else:
                            results["emails_failed"] += 1
                            if result.get("email_error"):
                                results["errors"].append({
                                    "user_id": recipient.user_id,
                                    "error": result["email_error"]
                                })
                                
                except Exception as e:
                    # pii-logs ok: email/phone mascarado em runtime via PIIMaskingFilter (LGPD Art.46 + ADR-006 defesa em profundidade)
                    logger.error(f"❌ Failed to process briefing for {recipient.user_id}: {e}")
                    results["emails_failed"] += 1
                    results["errors"].append({
                        "user_id": recipient.user_id,
                        "error": str(e)
                    })
            
            self._last_run["daily_briefing"] = job_start
            
        except Exception as e:
            logger.error(f"❌ Daily briefing job failed: {e}", exc_info=True)
            results["errors"].append({"job_error": str(e)})
        
        results["completed_at"] = datetime.now().isoformat()
        results["duration_seconds"] = (datetime.now() - job_start).total_seconds()
        
        logger.info(
            f"✅ Daily briefing job completed: "
            f"{results['emails_sent']} sent, {results['emails_failed']} failed"
        )
        
        return results
    
    async def run_weekly_reports(self) -> dict[str, Any]:
        """
        Execute weekly performance report job.
        
        This method should be called by the scheduler (typically Monday morning).
        It generates team-level performance reports and sends to configured recipients.
        
        Returns:
            Job execution summary with success/failure counts
        """
        if not ENABLE_SCHEDULED_REPORTS:
            logger.warning(
                "⚠️ Scheduled reports disabled - set ENABLE_SCHEDULED_REPORTS=true to enable"
            )
            return {
                "job_type": "weekly_report",
                "status": "disabled",
                "message": "Scheduled reports are disabled. Set ENABLE_SCHEDULED_REPORTS=true to enable.",
                "environment": ENVIRONMENT
            }
        
        if not IS_PRODUCTION:
            logger.warning(
                f"⚠️ Running weekly reports in {ENVIRONMENT} environment. "
                "Emails may be simulated or sent to test addresses only."
            )
        
        job_start = datetime.now()
        logger.info("🚀 Starting weekly report job...")
        
        results = {
            "job_type": "weekly_report",
            "started_at": job_start.isoformat(),
            "environment": ENVIRONMENT,
            "teams_processed": 0,
            "emails_sent": 0,
            "emails_failed": 0,
            "errors": [],
        }
        
        try:
            team_recipients = await self._get_weekly_report_recipients()
            results["teams_processed"] = len(team_recipients)
            
            if not team_recipients:
                logger.info("ℹ️ No teams configured for weekly reports")
                results["message"] = "No teams configured"
                return results
            
            for team_name, recipients in team_recipients.items():
                try:
                    valid_recipients = [r for r in recipients if r.company_id]
                    if not valid_recipients:
                        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
                        logger.warning(f"⚠️ Skipping team {team_name} - no valid recipients with company_id")
                        continue
                    
                    emails = [r.email for r in valid_recipients]
                    company_name = valid_recipients[0].company_name if valid_recipients else "Empresa"
                    
                    result = await self.report_service.generate_weekly_performance_report(
                        recipient_emails=emails,
                        recipient_name=team_name,
                        company_name=company_name,
                        send_email=True
                    )
                    
                    results["emails_sent"] += len(result.get("emails_sent", []))
                    results["emails_failed"] += len(result.get("emails_failed", []))
                    
                    for failure in result.get("emails_failed", []):
                        results["errors"].append({
                            "team": team_name,
                            "email": failure.get("email"),
                            "error": failure.get("error")
                        })
                        
                except Exception as e:
                    # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
                    logger.error(f"❌ Failed to process weekly report for team {team_name}: {e}")
                    results["errors"].append({
                        "team": team_name,
                        "error": str(e)
                    })
            
            self._last_run["weekly_report"] = job_start
            
        except Exception as e:
            logger.error(f"❌ Weekly report job failed: {e}", exc_info=True)
            results["errors"].append({"job_error": str(e)})
        
        results["completed_at"] = datetime.now().isoformat()
        results["duration_seconds"] = (datetime.now() - job_start).total_seconds()
        
        logger.info(
            f"✅ Weekly report job completed: "
            f"{results['emails_sent']} sent, {results['emails_failed']} failed"
        )
        
        return results
    
    async def run_monthly_reports(self) -> dict[str, Any]:
        """
        Execute monthly manager/executive report job.
        
        This method should be called by the scheduler (typically 1st of month).
        It generates executive-level reports and sends to managers/directors.
        
        Returns:
            Job execution summary with success/failure counts
        """
        if not ENABLE_SCHEDULED_REPORTS:
            logger.warning(
                "⚠️ Scheduled reports disabled - set ENABLE_SCHEDULED_REPORTS=true to enable"
            )
            return {
                "job_type": "monthly_report",
                "status": "disabled",
                "message": "Scheduled reports are disabled. Set ENABLE_SCHEDULED_REPORTS=true to enable.",
                "environment": ENVIRONMENT
            }
        
        if not IS_PRODUCTION:
            logger.warning(
                f"⚠️ Running monthly reports in {ENVIRONMENT} environment. "
                "Emails may be simulated or sent to test addresses only."
            )
        
        job_start = datetime.now()
        logger.info("🚀 Starting monthly manager report job...")
        
        results = {
            "job_type": "monthly_report",
            "started_at": job_start.isoformat(),
            "environment": ENVIRONMENT,
            "companies_processed": 0,
            "emails_sent": 0,
            "emails_failed": 0,
            "errors": [],
        }
        
        try:
            company_recipients = await self._get_monthly_report_recipients()
            results["companies_processed"] = len(company_recipients)
            
            if not company_recipients:
                logger.info("ℹ️ No companies configured for monthly reports")
                results["message"] = "No companies configured"
                return results
            
            for company_name, recipients in company_recipients.items():
                try:
                    valid_recipients = [r for r in recipients if r.company_id]
                    if not valid_recipients:
                        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
                        logger.warning(f"⚠️ Skipping company {company_name} - no valid recipients with company_id")
                        continue
                    
                    emails = [r.email for r in valid_recipients]
                    
                    result = await self.report_service.generate_monthly_manager_report(
                        recipient_emails=emails,
                        recipient_name="Gestão",
                        company_name=company_name,
                        send_email=True
                    )
                    
                    results["emails_sent"] += len(result.get("emails_sent", []))
                    results["emails_failed"] += len(result.get("emails_failed", []))
                    
                    for failure in result.get("emails_failed", []):
                        results["errors"].append({
                            "company": company_name,
                            "email": failure.get("email"),
                            "error": failure.get("error")
                        })
                        
                except Exception as e:
                    # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
                    logger.error(f"❌ Failed to process monthly report for {company_name}: {e}")
                    results["errors"].append({
                        "company": company_name,
                        "error": str(e)
                    })
            
            self._last_run["monthly_report"] = job_start
            
        except Exception as e:
            logger.error(f"❌ Monthly report job failed: {e}", exc_info=True)
            results["errors"].append({"job_error": str(e)})
        
        results["completed_at"] = datetime.now().isoformat()
        results["duration_seconds"] = (datetime.now() - job_start).total_seconds()
        
        logger.info(
            f"✅ Monthly report job completed: "
            f"{results['emails_sent']} sent, {results['emails_failed']} failed"
        )
        
        return results
    
    async def _get_daily_briefing_recipients(self) -> list[ReportRecipient]:
        """
        Get list of recipients for daily briefings from database.
        
        Queries the database for users with daily briefing enabled in their
        notification preferences.
        
        Returns:
            List of ReportRecipient objects
        """
        recipients = []
        
        try:
            async with AsyncSessionLocal() as db:
                from app.models.company import Company
                from app.models.user import User
                
                result = await db.execute(
                    select(User, Company)
                    .join(Company, User.company_id == Company.id, isouter=True)
                    .where(User.is_active)
                )
                
                for user, company in result.all():
                    preferences = user.notification_preferences or {}
                    
                    if preferences.get("daily_briefing_enabled", False):
                        recipients.append(ReportRecipient(
                            user_id=str(user.id),
                            email=user.email,
                            name=user.name or user.email,
                            company_id=str(user.company_id) if user.company_id else None,
                            company_name=company.name if company else "Empresa",
                            report_types=["daily"]
                        ))
                
                # pii-logs ok: email/phone mascarado em runtime via PIIMaskingFilter (LGPD Art.46 + ADR-006 defesa em profundidade)
                logger.info(f"📋 Found {len(recipients)} daily briefing recipients from database")
                
        except Exception as e:
            logger.error(f"❌ Error fetching daily briefing recipients: {e}", exc_info=True)
        
        return recipients
    
    async def _get_weekly_report_recipients(self) -> dict[str, list[ReportRecipient]]:
        """
        Get recipients for weekly reports, grouped by team/department.
        
        Queries the database for users with weekly report enabled in their
        notification preferences, grouped by department.
        
        Returns:
            Dict mapping team/department names to list of recipients
        """
        team_recipients: dict[str, list[ReportRecipient]] = {}
        
        try:
            async with AsyncSessionLocal() as db:
                from app.models.company import Company
                from app.models.user import User
                
                result = await db.execute(
                    select(User, Company)
                    .join(Company, User.company_id == Company.id, isouter=True)
                    .where(User.is_active)
                )
                
                for user, company in result.all():
                    preferences = user.notification_preferences or {}
                    
                    if preferences.get("weekly_report_enabled", False):
                        department = getattr(user, 'department', None) or "Geral"
                        company_name = company.name if company else "Empresa"
                        team_key = f"{company_name} - {department}"
                        
                        if team_key not in team_recipients:
                            team_recipients[team_key] = []
                        
                        team_recipients[team_key].append(ReportRecipient(
                            user_id=str(user.id),
                            email=user.email,
                            name=user.name or user.email,
                            company_id=str(user.company_id) if user.company_id else None,
                            company_name=company_name,
                            report_types=["weekly"]
                        ))
                
                # pii-logs ok: email/phone mascarado em runtime via PIIMaskingFilter (LGPD Art.46 + ADR-006 defesa em profundidade)
                logger.info(f"📋 Found {len(team_recipients)} teams for weekly reports from database")
                
        except Exception as e:
            logger.error(f"❌ Error fetching weekly report recipients: {e}", exc_info=True)
        
        return team_recipients
    
    async def _get_monthly_report_recipients(self) -> dict[str, list[ReportRecipient]]:
        """
        Get recipients for monthly manager reports, grouped by company.
        
        Queries the database for managers and executives with monthly report
        enabled in their notification preferences.
        
        Returns:
            Dict mapping company names to list of recipients
        """
        company_recipients: dict[str, list[ReportRecipient]] = {}
        
        try:
            async with AsyncSessionLocal() as db:
                from app.models.company import Company
                from app.models.user import User
                
                result = await db.execute(
                    select(User, Company)
                    .join(Company, User.company_id == Company.id, isouter=True)
                    .where(User.is_active)
                )
                
                for user, company in result.all():
                    preferences = user.notification_preferences or {}
                    
                    if preferences.get("monthly_report_enabled", False):
                        company_name = company.name if company else "Empresa"
                        
                        if company_name not in company_recipients:
                            company_recipients[company_name] = []
                        
                        company_recipients[company_name].append(ReportRecipient(
                            user_id=str(user.id),
                            email=user.email,
                            name=user.name or user.email,
                            company_id=str(user.company_id) if user.company_id else None,
                            company_name=company_name,
                            report_types=["monthly"]
                        ))
                
                # pii-logs ok: email/phone mascarado em runtime via PIIMaskingFilter (LGPD Art.46 + ADR-006 defesa em profundidade)
                logger.info(f"📋 Found {len(company_recipients)} companies for monthly reports from database")
                
        except Exception as e:
            logger.error(f"❌ Error fetching monthly report recipients: {e}", exc_info=True)
        
        return company_recipients
    
    def get_job_status(self) -> dict[str, Any]:
        """
        Get current status of scheduled jobs.
        
        Returns:
            Status information including last run times and configuration
        """
        return {
            "enabled": ENABLE_SCHEDULED_REPORTS,
            "environment": ENVIRONMENT,
            "is_production": IS_PRODUCTION,
            "config": {
                "daily_enabled": self.config.daily_briefing_enabled,
                "daily_schedule": f"{self.config.daily_briefing_hour:02d}:{self.config.daily_briefing_minute:02d}",
                "weekly_enabled": self.config.weekly_report_enabled,
                "weekly_schedule": f"Day {self.config.weekly_report_day} at {self.config.weekly_report_hour:02d}:{self.config.weekly_report_minute:02d}",
                "monthly_enabled": self.config.monthly_report_enabled,
                "monthly_schedule": f"Day {self.config.monthly_report_day} at {self.config.monthly_report_hour:02d}:{self.config.monthly_report_minute:02d}",
                "timezone": self.config.timezone,
            },
            "last_runs": {
                job_type: run_time.isoformat()
                for job_type, run_time in self._last_run.items()
            },
            "security_note": "Set ENABLE_SCHEDULED_REPORTS=true to enable report sending" if not ENABLE_SCHEDULED_REPORTS else None
        }
    
    async def run_single_report(
        self,
        report_type: str,
        recipient: ReportRecipient
    ) -> dict[str, Any]:
        """
        Run a single report for a specific recipient.
        
        Useful for testing or manual triggering.
        
        Args:
            report_type: Type of report (daily, weekly, monthly)
            recipient: The recipient to send to
            
        Returns:
            Report generation result
        """
        if report_type == "daily":
            async with AsyncSessionLocal() as db:
                return await self.report_service.generate_daily_briefing_email(
                    user_id=recipient.user_id,
                    user_email=recipient.email,
                    user_name=recipient.name,
                    company_name=recipient.company_name,
                    db=db,
                    send_email=True
                )
        elif report_type == "weekly":
            return await self.report_service.generate_weekly_performance_report(
                recipient_emails=[recipient.email],
                recipient_name=recipient.name,
                company_name=recipient.company_name,
                send_email=True
            )
        elif report_type == "monthly":
            return await self.report_service.generate_monthly_manager_report(
                recipient_emails=[recipient.email],
                recipient_name=recipient.name,
                company_name=recipient.company_name,
                send_email=True
            )
        else:
            raise ValueError(f"Unknown report type: {report_type}")


scheduled_report_job = ScheduledReportJob()
