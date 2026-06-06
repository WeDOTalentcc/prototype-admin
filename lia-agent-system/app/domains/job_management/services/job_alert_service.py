"""
Job Alert Service - Monitor jobs and generate alerts.

This service monitors job vacancies and generates alerts for:
- Critical jobs (low candidates, long time open)
- Stale jobs (no activity)
- Candidate waiting feedback
- Deadlines approaching
"""
import logging
from datetime import datetime, timedelta
from typing import Any

from app.schemas.job_management import AlertSummary  # R-026

from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.communication.repositories.communication_settings_repository import CommunicationSettingsRepository
from app.domains.job_management.repositories.job_alert_repository import JobAlertRepository
from lia_models.alert import Alert, AlertSeverity, AlertStatus, AlertType

logger = logging.getLogger(__name__)


class JobAlertService:
    """
    Service for monitoring jobs and generating alerts.
    """
    
    CRITICAL_DAYS_OPEN = 30
    STALE_DAYS = 7
    MIN_CANDIDATES_THRESHOLD = 5
    FEEDBACK_OVERDUE_DAYS = 3
    
    async def check_all_alerts(
        self,
        db: AsyncSession,
        company_id: str | None = None,
    ) -> list[Alert]:
        """
        Run all alert checks and create alerts as needed.
        
        Args:
            db: Database session
            
        Returns:
            List of newly created alerts
        """
        # Ghost-setting consumer: respect tenant opt-out (P0-W1-06)
        if company_id is not None:
            settings = await CommunicationSettingsRepository(db).get_by_company_id(company_id)
            if settings is not None and not settings.alerts_enabled:
                logger.info(
                    "alert_check_skipped_by_tenant_toggle",
                    extra={"company_id": company_id, "alerts_enabled": False},
                )
                return []

        alerts = []
        
        alerts.extend(await self.check_critical_jobs(db))
        alerts.extend(await self.check_stale_jobs(db))
        alerts.extend(await self.check_low_volume_jobs(db))
        alerts.extend(await self.check_pending_feedback(db))
        # Onda 2D (audit 2026-06-06): alerta de prazo da vaga (estava morto — sem caller).
        alerts.extend(await self.check_job_expiration_alerts(db))
        
        logger.info(f"Alert check completed: {len(alerts)} new alerts created")
        
        return alerts
    
    async def check_critical_jobs(self, db: AsyncSession) -> list[Alert]:
        """Check for jobs in critical state."""
        alerts = []
        
        cutoff_date = datetime.utcnow() - timedelta(days=self.CRITICAL_DAYS_OPEN)
        
        critical_jobs = await JobAlertRepository(db).list_open_jobs_created_before(cutoff_date)
        
        for job in critical_jobs:
            existing = await self._check_existing_alert(
                db, AlertType.JOB_CRITICAL, job.id
            )
            if existing:
                continue
            
            days_open = (datetime.utcnow() - job.created_at).days
            
            alert = Alert(
                alert_type=AlertType.JOB_CRITICAL,
                severity=AlertSeverity.CRITICAL,
                title=f"Vaga crítica: {job.title}",
                message=f"A vaga '{job.title}' está aberta há {days_open} dias. "
                        f"Considere revisar os requisitos ou ampliar as fontes de sourcing.",
                job_id=job.id,
                context={
                    "days_open": days_open,
                    "job_title": job.title,
                    "department": job.department,
                },
                suggested_actions=[
                    "Revisar requisitos da vaga",
                    "Ativar sourcing automatizado",
                    "Considerar ajuste salarial",
                    "Expandir busca para banco global"
                ]
            )
            
            db.add(alert)
            alerts.append(alert)
        
        if alerts:
            await db.commit()
        
        return alerts
    
    async def check_stale_jobs(self, db: AsyncSession) -> list[Alert]:
        """Check for jobs with no recent activity."""
        alerts = []
        
        cutoff_date = datetime.utcnow() - timedelta(days=self.STALE_DAYS)
        
        stale_jobs = await JobAlertRepository(db).list_open_jobs_updated_before(cutoff_date)
        
        for job in stale_jobs:
            existing = await self._check_existing_alert(
                db, AlertType.JOB_STALE, job.id
            )
            if existing:
                continue
            
            days_inactive = (datetime.utcnow() - job.updated_at).days
            
            alert = Alert(
                alert_type=AlertType.JOB_STALE,
                severity=AlertSeverity.MEDIUM,
                title=f"Vaga sem atividade: {job.title}",
                message=f"A vaga '{job.title}' não tem atividade há {days_inactive} dias.",
                job_id=job.id,
                context={
                    "days_inactive": days_inactive,
                    "job_title": job.title,
                },
                suggested_actions=[
                    "Verificar status dos candidatos",
                    "Reativar sourcing",
                    "Contatar hiring manager"
                ]
            )
            
            db.add(alert)
            alerts.append(alert)
        
        if alerts:
            await db.commit()
        
        return alerts
    
    async def check_low_volume_jobs(self, db: AsyncSession) -> list[Alert]:
        """Check for jobs with low candidate volume."""
        alerts = []
        
        repo = JobAlertRepository(db)
        open_jobs = await repo.list_open_jobs()

        for job in open_jobs:
            count = await repo.count_candidates_for_job(job.id)
            
            if count >= self.MIN_CANDIDATES_THRESHOLD:
                continue
            
            existing = await self._check_existing_alert(
                db, AlertType.JOB_LOW_VOLUME, job.id
            )
            if existing:
                continue
            
            days_open = (datetime.utcnow() - job.created_at).days if job.created_at else 0
            
            if days_open < 7:
                continue
            
            alert = Alert(
                alert_type=AlertType.JOB_LOW_VOLUME,
                severity=AlertSeverity.HIGH,
                title=f"Poucos candidatos: {job.title}",
                message=f"A vaga '{job.title}' tem apenas {count} candidatos após {days_open} dias.",
                job_id=job.id,
                context={
                    "candidate_count": count,
                    "days_open": days_open,
                    "job_title": job.title,
                    "threshold": self.MIN_CANDIDATES_THRESHOLD,
                },
                suggested_actions=[
                    "Buscar candidatos no banco global",
                    "Flexibilizar requisitos",
                    "Publicar em mais canais",
                    "Ativar programa de indicação"
                ]
            )
            
            db.add(alert)
            alerts.append(alert)
        
        if alerts:
            await db.commit()
        
        return alerts
    
    async def check_pending_feedback(self, db: AsyncSession) -> list[Alert]:
        """Check for candidates waiting feedback too long."""
        alerts = []
        
        cutoff_date = datetime.utcnow() - timedelta(days=self.FEEDBACK_OVERDUE_DAYS)
        
        waiting_candidates = await JobAlertRepository(db).list_candidates_awaiting_feedback_before(cutoff_date)
        
        for candidate in waiting_candidates:
            existing = await self._check_existing_alert(
                db, AlertType.FEEDBACK_PENDING, candidate_id=candidate.id
            )
            if existing:
                continue
            
            days_waiting = (datetime.utcnow() - candidate.updated_at).days
            
            alert = Alert(
                alert_type=AlertType.FEEDBACK_PENDING,
                severity=AlertSeverity.HIGH,
                title=f"Feedback pendente: {candidate.name}",
                message=f"O candidato {candidate.name} aguarda feedback há {days_waiting} dias.",
                candidate_id=candidate.id,
                job_id=candidate.pipeline_job_id,
                context={
                    "days_waiting": days_waiting,
                    "candidate_name": candidate.name,
                    "candidate_email": candidate.email,
                },
                suggested_actions=[
                    "Enviar feedback ao candidato",
                    "Solicitar decisão do gestor",
                    "Mover para próxima etapa"
                ]
            )
            
            db.add(alert)
            alerts.append(alert)
        
        if alerts:
            await db.commit()
        
        return alerts
    
    async def _check_existing_alert(
        self,
        db: AsyncSession,
        alert_type: AlertType,
        job_id: str | None = None,
        candidate_id: str | None = None
    ) -> Alert | None:
        """Check if an active alert already exists."""
        return await JobAlertRepository(db).find_active_alert(
            alert_type, job_id=job_id, candidate_id=candidate_id
        )
    
    async def get_active_alerts(
        self,
        db: AsyncSession,
        user_id: str | None = None,
        severity: AlertSeverity | None = None,
        limit: int = 50
    ) -> list[Alert]:
        """Get active alerts."""
        return await JobAlertRepository(db).list_active_alerts(
            user_id=user_id, severity=severity, limit=limit
        )
    
    async def acknowledge_alert(
        self,
        db: AsyncSession,
        alert_id: str,
        user_id: str
    ) -> Alert | None:
        """Acknowledge an alert."""
        alert = await JobAlertRepository(db).get_alert_by_id(alert_id)

        if not alert:
            return None

        alert.status = AlertStatus.ACKNOWLEDGED
        alert.acknowledged_at = datetime.utcnow()
        alert.acknowledged_by = user_id
        alert.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(alert)
        
        return alert
    
    async def resolve_alert(
        self,
        db: AsyncSession,
        alert_id: str,
        user_id: str,
        resolution_note: str | None = None
    ) -> Alert | None:
        """Resolve an alert."""
        alert = await JobAlertRepository(db).get_alert_by_id(alert_id)

        if not alert:
            return None

        alert.status = AlertStatus.RESOLVED
        alert.resolved_at = datetime.utcnow()
        alert.resolved_by = user_id
        alert.updated_at = datetime.utcnow()
        
        if resolution_note:
            alert.context = {**alert.context, "resolution_note": resolution_note}
        
        await db.commit()
        await db.refresh(alert)
        
        return alert
    
    async def get_alert_summary(self, db: AsyncSession) -> AlertSummary:
        """Get summary of active alerts."""
        counts = await JobAlertRepository(db).severity_counts()
        
        return {
            "critical": counts.get("critical", 0),
            "high": counts.get("high", 0),
            "medium": counts.get("medium", 0),
            "low": counts.get("low", 0),
            "info": counts.get("info", 0),
            "total": sum(counts.values()),
        }



    EXPIRATION_WARNING_DAYS = 7
    APIFY_BUDGET_WARNING_PCT = 0.80   # 80% of budget -> INFO alert
    APIFY_BUDGET_USD_DEFAULT = 100.0  # overridden by ConsumptionTrackingService.get_tenant_budget

    async def check_job_expiration_alerts(self, db: AsyncSession) -> list[Alert]:
        """Check for jobs whose closing deadline is approaching (within EXPIRATION_WARNING_DAYS)."""
        alerts = []
        now = datetime.utcnow()
        cutoff = now + timedelta(days=self.EXPIRATION_WARNING_DAYS)

        expiring_jobs = await JobAlertRepository(db).list_jobs_with_deadline_approaching(
            from_date=now, to_date=cutoff
        )

        for job in expiring_jobs:
            existing = await self._check_existing_alert(
                db, AlertType.DEADLINE_APPROACHING, job.id
            )
            if existing:
                continue

            deadline = getattr(job, "deadline_closing", None)
            days_left = (deadline - now).days if deadline else 0
            deadline_str = deadline.strftime("%d/%m/%Y") if deadline else "N/A"

            alert = Alert(
                alert_type=AlertType.DEADLINE_APPROACHING,
                severity=AlertSeverity.HIGH,
                title=f"Prazo proximo: {job.title}",
                message=(
                    f"A vaga '{job.title}' tem prazo de fechamento em {days_left} dias ({deadline_str})."
                ),
                job_id=job.id,
                context={
                    "days_left": days_left,
                    "job_title": job.title,
                    "deadline_closing": deadline.isoformat() if deadline else None,
                },
                suggested_actions=[
                    "Revisar candidatos em etapa final",
                    "Acelerar processo de decisao",
                    "Notificar hiring manager sobre prazo",
                ],
            )
            db.add(alert)
            alerts.append(alert)

        if alerts:
            await db.commit()

        return alerts

    async def check_apify_budget_alerts(
        self,
        db: AsyncSession,
        company_id: str,
    ) -> list[Alert]:
        """Surface APIFY budget alerts in /alerts/ endpoint (P0 #7).

        Mirrors logic from ConsumptionTrackingService._check_budget_alert_inner
        but creates Alert DB records so they appear on the Decidir page.
        """
        now = datetime.utcnow()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        monthly_spend = await JobAlertRepository(db).get_apify_monthly_spend(
            company_id=company_id, month_start=month_start
        )

        try:
            from app.domains.billing.services.consumption_tracking_service import (
                ConsumptionTrackingService,
            )
            budget = ConsumptionTrackingService.get_tenant_budget(company_id, "apify")
        except Exception:
            budget = self.APIFY_BUDGET_USD_DEFAULT

        if budget <= 0:
            return []

        ratio = monthly_spend / budget
        if ratio < self.APIFY_BUDGET_WARNING_PCT:
            return []

        dedup_key = f"apify_budget:{company_id}:{now.year}-{now.month:02d}"
        existing = await self._check_existing_alert(db, AlertType.SYSTEM, job_id=dedup_key)
        if existing:
            return []

        pct = round(ratio * 100, 1)
        severity = AlertSeverity.HIGH if ratio >= 1.0 else AlertSeverity.INFO
        status_label = "esgotado" if ratio >= 1.0 else "proximo do limite"
        alert = Alert(
            alert_type=AlertType.SYSTEM,
            severity=severity,
            title=f"Orcamento APIFY {status_label}",
            message=(
                f"Consumo APIFY mensal: ${monthly_spend:.2f} ({pct}% do limite ${budget:.2f}). "
                + (
                    "Novas buscas de enriquecimento podem ser bloqueadas."
                    if ratio >= 1.0
                    else "Considere ajustar o volume de buscas."
                )
            ),
            job_id=dedup_key,
            context={
                "monthly_spend_usd": round(monthly_spend, 2),
                "budget_usd": budget,
                "usage_percentage": pct,
                "month": f"{now.year}-{now.month:02d}",
                "company_id": company_id,
            },
            suggested_actions=[
                "Revisar automacoes de sourcing APIFY",
                "Ajustar limites de enriquecimento por vaga",
                "Solicitar aumento de orcamento" if ratio >= 1.0 else "Monitorar consumo diario",
            ],
        )
        db.add(alert)
        await db.commit()
        return [alert]

job_alert_service = JobAlertService()
