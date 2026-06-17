"""
Job Audit Service for tracking all changes to job vacancies.
Provides complete audit trail for compliance and transparency.
"""
import logging
from datetime import datetime
from typing import Any

from sqlalchemy import and_, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.job_management.repositories.job_audit_repository import JobAuditRepository

from lia_models.job_vacancy_audit import AuditAction, JobVacancyAuditLog

logger = logging.getLogger(__name__)


class JobAuditService:
    """Service for logging and retrieving job vacancy audit trails."""

    async def log_creation(
        self,
        job_id: str,
        created_by: str,
        company_id: str,
        db: AsyncSession,
        job_data: dict[str, Any] | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> JobVacancyAuditLog:
        """
        Log job vacancy creation.
        
        Args:
            job_id: The job vacancy ID
            created_by: User email or ID who created the job
            company_id: Company/tenant ID
            db: Database session
            job_data: Optional dict with job details for the audit record
            ip_address: Optional client IP address
            user_agent: Optional client user agent
        """
        audit_log = JobVacancyAuditLog(
            job_vacancy_id=job_id,
            company_id=company_id,
            action=AuditAction.CREATED.value,
            field_changed=None,
            old_value=None,
            new_value=job_data,
            changed_by=created_by,
            changed_at=datetime.utcnow(),
            ip_address=ip_address,
            user_agent=user_agent,
            extra_data={"action_description": "Job vacancy created"},
        )
        
        db.add(audit_log)
        await db.flush()
        
        logger.info(f"📋 Audit log created: Job {job_id} created by {created_by}")
        return audit_log

    async def log_update(
        self,
        job_id: str,
        changes: dict[str, dict[str, Any]],
        changed_by: str,
        company_id: str,
        db: AsyncSession,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> list[JobVacancyAuditLog]:
        """
        Log job vacancy updates. Creates one audit record per field changed.
        
        Args:
            job_id: The job vacancy ID
            changes: Dict of {field_name: {"old": old_value, "new": new_value}}
            changed_by: User email or ID who made the changes
            company_id: Company/tenant ID
            db: Database session
            ip_address: Optional client IP address
            user_agent: Optional client user agent
            
        Returns:
            List of created audit log entries
        """
        audit_logs = []
        timestamp = datetime.utcnow()
        
        for field_name, change_data in changes.items():
            old_value = change_data.get("old")
            new_value = change_data.get("new")
            
            if old_value == new_value:
                continue
            
            audit_log = JobVacancyAuditLog(
                job_vacancy_id=job_id,
                company_id=company_id,
                action=AuditAction.UPDATED.value,
                field_changed=field_name,
                old_value=old_value,
                new_value=new_value,
                changed_by=changed_by,
                changed_at=timestamp,
                ip_address=ip_address,
                user_agent=user_agent,
                extra_data={"action_description": f"Field '{field_name}' updated"},
            )
            
            db.add(audit_log)
            audit_logs.append(audit_log)
        
        if audit_logs:
            await db.flush()
            logger.info(f"📋 Audit logs created: {len(audit_logs)} fields updated for job {job_id} by {changed_by}")
        
        return audit_logs

    async def log_status_change(
        self,
        job_id: str,
        old_status: str,
        new_status: str,
        changed_by: str,
        company_id: str,
        db: AsyncSession,
        ip_address: str | None = None,
        user_agent: str | None = None,
        extra_data: dict[str, Any] | None = None,
    ) -> JobVacancyAuditLog:
        """
        Log job vacancy status change.
        
        Args:
            job_id: The job vacancy ID
            old_status: Previous status
            new_status: New status
            changed_by: User email or ID who changed the status
            company_id: Company/tenant ID
            db: Database session
            ip_address: Optional client IP address
            user_agent: Optional client user agent
            extra_data: Optional additional context
        """
        merged_extra = {"action_description": f"Status changed from '{old_status}' to '{new_status}'"}
        if extra_data:
            merged_extra.update(extra_data)
        
        audit_log = JobVacancyAuditLog(
            job_vacancy_id=job_id,
            company_id=company_id,
            action=AuditAction.STATUS_CHANGED.value,
            field_changed="status",
            old_value=old_status,
            new_value=new_status,
            changed_by=changed_by,
            changed_at=datetime.utcnow(),
            ip_address=ip_address,
            user_agent=user_agent,
            extra_data=merged_extra,
        )
        
        db.add(audit_log)
        await db.flush()
        
        logger.info(f"📋 Audit log created: Job {job_id} status changed {old_status} → {new_status} by {changed_by}")
        return audit_log

    async def log_publication(
        self,
        job_id: str,
        platform: str,
        changed_by: str,
        company_id: str,
        db: AsyncSession,
        ip_address: str | None = None,
        user_agent: str | None = None,
        extra_data: dict[str, Any] | None = None,
    ) -> JobVacancyAuditLog:
        """
        Log job vacancy publication to a platform.
        
        Args:
            job_id: The job vacancy ID
            platform: Platform where job was published (e.g., 'linkedin', 'internal', 'website')
            changed_by: User email or ID who published
            company_id: Company/tenant ID
            db: Database session
            ip_address: Optional client IP address
            user_agent: Optional client user agent
            extra_data: Optional additional context (e.g., sourcing results)
        """
        merged_extra = {"action_description": f"Job published to {platform}", "platform": platform}
        if extra_data:
            merged_extra.update(extra_data)
        
        audit_log = JobVacancyAuditLog(
            job_vacancy_id=job_id,
            company_id=company_id,
            action=AuditAction.PUBLISHED.value,
            field_changed=None,
            old_value=None,
            new_value={"platform": platform, "published_at": datetime.utcnow().isoformat()},
            changed_by=changed_by,
            changed_at=datetime.utcnow(),
            ip_address=ip_address,
            user_agent=user_agent,
            extra_data=merged_extra,
        )
        
        db.add(audit_log)
        await db.flush()
        
        logger.info(f"📋 Audit log created: Job {job_id} published to {platform} by {changed_by}")
        return audit_log

    async def log_archive(
        self,
        job_id: str,
        changed_by: str,
        company_id: str,
        db: AsyncSession,
        ip_address: str | None = None,
        user_agent: str | None = None,
        reason: str | None = None,
    ) -> JobVacancyAuditLog:
        """
        Log job vacancy archival/deletion.
        
        Args:
            job_id: The job vacancy ID
            changed_by: User email or ID who archived
            company_id: Company/tenant ID
            db: Database session
            ip_address: Optional client IP address
            user_agent: Optional client user agent
            reason: Optional reason for archival
        """
        extra_data = {"action_description": "Job vacancy archived"}
        if reason:
            extra_data["reason"] = reason
        
        audit_log = JobVacancyAuditLog(
            job_vacancy_id=job_id,
            company_id=company_id,
            action=AuditAction.ARCHIVED.value,
            field_changed="status",
            old_value=None,
            new_value="Arquivada",
            changed_by=changed_by,
            changed_at=datetime.utcnow(),
            ip_address=ip_address,
            user_agent=user_agent,
            extra_data=extra_data,
        )
        
        db.add(audit_log)
        await db.flush()
        
        logger.info(f"📋 Audit log created: Job {job_id} archived by {changed_by}")
        return audit_log

    async def get_history(
        self,
        job_id: str,
        company_id: str,
        db: AsyncSession,
        limit: int = 100,
        offset: int = 0,
    ) -> dict[str, Any]:
        """
        Get full audit trail for a job vacancy.
        
        Args:
            job_id: The job vacancy ID
            company_id: Company/tenant ID for access control
            db: Database session
            limit: Maximum number of records to return
            offset: Pagination offset
            
        Returns:
            Dict with audit logs and pagination info
        """
        from sqlalchemy import func
        
        where_conditions = and_(
            JobVacancyAuditLog.job_vacancy_id == job_id,
            JobVacancyAuditLog.company_id == company_id,
        )
        
        repo = JobAuditRepository(db)
        total = await repo.count_for_job(where_conditions)
        audit_logs = await repo.list_for_job(where_conditions, limit=limit, offset=offset)
        
        logger.info(f"📋 Retrieved {len(audit_logs)} audit logs for job {job_id}")
        
        return {
            "items": [log.to_dict() for log in audit_logs],
            "total": total,
            "limit": limit,
            "offset": offset,
            "has_more": (offset + len(audit_logs)) < total,
        }


job_audit_service = JobAuditService()
