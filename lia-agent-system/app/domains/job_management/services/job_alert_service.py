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
from typing import Any, List

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.alert import Alert, AlertSeverity, AlertStatus, AlertType
from app.models.candidate import Candidate
from app.models.job_vacancy import JobVacancy

logger = logging.getLogger(__name__)


class JobAlertService:
    """
    Service for monitoring jobs and generating alerts.
    """
    
    CRITICAL_DAYS_OPEN = 30
    STALE_DAYS = 7
    MIN_CANDIDATES_THRESHOLD = 5
    FEEDBACK_OVERDUE_DAYS = 3
    
    async def check_all_alerts(self, db: AsyncSession) -> list[Alert]:
        """
        Run all alert checks and create alerts as needed.
        
        Args:
            db: Database session
            
        Returns:
            List of newly created alerts
        """
        alerts = []
        
        alerts.extend(await self.check_critical_jobs(db))
        alerts.extend(await self.check_stale_jobs(db))
        alerts.extend(await self.check_low_volume_jobs(db))
        alerts.extend(await self.check_pending_feedback(db))
        
        logger.info(f"Alert check completed: {len(alerts)} new alerts created")
        
        return alerts
    
    async def check_critical_jobs(self, db: AsyncSession) -> list[Alert]:
        """Check for jobs in critical state."""
        alerts = []
        
        cutoff_date = datetime.utcnow() - timedelta(days=self.CRITICAL_DAYS_OPEN)
        
        result = await db.execute(
            select(JobVacancy).where(
                and_(
                    JobVacancy.status == "open",
                    JobVacancy.created_at < cutoff_date
                )
            )
        )
        critical_jobs = result.scalars().all()
        
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
        
        result = await db.execute(
            select(JobVacancy).where(
                and_(
                    JobVacancy.status == "open",
                    JobVacancy.updated_at < cutoff_date
                )
            )
        )
        stale_jobs = result.scalars().all()
        
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
        
        result = await db.execute(
            select(JobVacancy).where(JobVacancy.status == "open")
        )
        open_jobs = result.scalars().all()
        
        for job in open_jobs:
            candidate_count = await db.execute(
                select(func.count(Candidate.id)).where(
                    Candidate.pipeline_job_id == job.id
                )
            )
            count = candidate_count.scalar() or 0
            
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
        
        result = await db.execute(
            select(Candidate).where(
                and_(
                    Candidate.pipeline_stage == "awaiting_feedback",
                    Candidate.updated_at < cutoff_date
                )
            )
        )
        waiting_candidates = result.scalars().all()
        
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
        query = select(Alert).where(
            and_(
                Alert.alert_type == alert_type,
                Alert.status == AlertStatus.ACTIVE
            )
        )
        
        if job_id:
            query = query.where(Alert.job_id == job_id)
        if candidate_id:
            query = query.where(Alert.candidate_id == candidate_id)
        
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    async def get_active_alerts(
        self,
        db: AsyncSession,
        user_id: str | None = None,
        severity: AlertSeverity | None = None,
        limit: int = 50
    ) -> list[Alert]:
        """Get active alerts."""
        query = select(Alert).where(Alert.status == AlertStatus.ACTIVE)
        
        if user_id:
            query = query.where(Alert.user_id == user_id)
        if severity:
            query = query.where(Alert.severity == severity)
        
        query = query.order_by(
            Alert.severity.desc(),
            Alert.created_at.desc()
        ).limit(limit)
        
        result = await db.execute(query)
        return list(result.scalars().all())
    
    async def acknowledge_alert(
        self,
        db: AsyncSession,
        alert_id: str,
        user_id: str
    ) -> Alert | None:
        """Acknowledge an alert."""
        result = await db.execute(
            select(Alert).where(Alert.id == alert_id)
        )
        alert = result.scalar_one_or_none()
        
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
        result = await db.execute(
            select(Alert).where(Alert.id == alert_id)
        )
        alert = result.scalar_one_or_none()
        
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
    
    async def get_alert_summary(self, db: AsyncSession) -> dict[str, Any]:
        """Get summary of active alerts."""
        result = await db.execute(
            select(
                Alert.severity,
                func.count(Alert.id).label("count")
            ).where(
                Alert.status == AlertStatus.ACTIVE
            ).group_by(Alert.severity)
        )
        
        counts = {row.severity.value: row.count for row in result.all()}
        
        return {
            "critical": counts.get("critical", 0),
            "high": counts.get("high", 0),
            "medium": counts.get("medium", 0),
            "low": counts.get("low", 0),
            "info": counts.get("info", 0),
            "total": sum(counts.values()),
        }


job_alert_service = JobAlertService()
