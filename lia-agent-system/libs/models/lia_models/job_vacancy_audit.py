"""
Job Vacancy Audit Log model for tracking all changes to job vacancies.
"""
from datetime import datetime
from typing import Optional
from enum import Enum
from sqlalchemy import Column, String, DateTime, Text, JSON, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
import uuid

from lia_config.database import Base


class AuditAction(str, Enum):
    """Actions that can be logged for job vacancies."""
    CREATED = "created"
    UPDATED = "updated"
    STATUS_CHANGED = "status_changed"
    PUBLISHED = "published"
    ARCHIVED = "archived"
    DELETED = "deleted"


class JobVacancyAuditLog(Base):
    """
    Audit log for tracking all changes to job vacancies.
    Provides complete history for compliance, debugging, and user transparency.
    """
    __tablename__ = "job_vacancy_audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_vacancy_id = Column(UUID(as_uuid=True), ForeignKey("job_vacancies.id"), nullable=False, index=True)
    company_id = Column(String(255), nullable=False, index=True)
    
    action = Column(String(50), nullable=False, index=True)
    field_changed = Column(String(255), nullable=True)
    
    old_value = Column(JSON, nullable=True)
    new_value = Column(JSON, nullable=True)
    
    changed_by = Column(String(255), nullable=False)
    changed_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    
    extra_data = Column(JSON, nullable=True, default=dict)

    __table_args__ = (
        Index('ix_job_vacancy_audit_company_job', 'company_id', 'job_vacancy_id'),
        Index('ix_job_vacancy_audit_changed_at_desc', 'changed_at'),
    {"extend_existing": True}, )

    def __repr__(self):
        return f"<JobVacancyAuditLog {self.id} - {self.action} by {self.changed_by}>"

    def to_dict(self) -> dict:
        """Convert audit log to dictionary for API responses."""
        return {
            "id": str(self.id),
            "job_vacancy_id": str(self.job_vacancy_id),
            "company_id": self.company_id,
            "action": self.action,
            "field_changed": self.field_changed,
            "old_value": self.old_value,
            "new_value": self.new_value,
            "changed_by": self.changed_by,
            "changed_at": self.changed_at.isoformat() if self.changed_at else None,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "extra_data": self.extra_data or {},
        }
