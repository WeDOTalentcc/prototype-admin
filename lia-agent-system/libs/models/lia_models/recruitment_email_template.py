"""
Recruitment Email Template models for pipeline stage communications.
Provides email templates for each recruitment stage with multi-tenancy support.
"""
from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy import Column, String, DateTime, Text, Boolean, Integer, Index, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid
import enum

from lia_config.database import Base


class TemplateType(str, enum.Enum):
    """Type of recipient for the template."""
    CANDIDATE = "candidate"
    RECRUITER = "recruiter"
    MANAGER = "manager"


class RecruitmentStageName(str, enum.Enum):
    """Standard recruitment pipeline stages."""
    CANDIDATE_APPLIED = "candidate_applied"
    SCREENING_SCHEDULED = "screening_scheduled"
    SCREENING_COMPLETED = "screening_completed"
    INTERVIEW_SCHEDULED = "interview_scheduled"
    INTERVIEW_REMINDER = "interview_reminder"
    INTERVIEW_COMPLETED = "interview_completed"
    OFFER_SENT = "offer_sent"
    CANDIDATE_HIRED = "candidate_hired"
    CANDIDATE_REJECTED = "candidate_rejected"
    STAGE_CHANGED = "stage_changed"


class RecruitmentEmailTemplate(Base):
    """
    Email templates for recruitment pipeline stages.
    Supports multi-tenancy with company_id and multiple recipient types.
    """
    __tablename__ = "recruitment_email_templates"
    __table_args__ = (
        Index('ix_recruitment_email_templates_company_stage', 'company_id', 'stage_name'),
        Index('ix_recruitment_email_templates_company_type', 'company_id', 'template_type'),
        Index('ix_recruitment_email_templates_active', 'is_active'),
        Index('ix_recruitment_email_templates_default', 'is_default'),
    {"extend_existing": True}, )
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # WT-2022 P0.TENANT: TENANT-EXEMPT - templates podem ser global default (company_id NULL = template padrao WeDOTalent compartilhado entre tenants)
    company_id = Column(String(255), nullable=True, index=True)
    
    stage_name = Column(String(50), nullable=False, index=True)
    template_type = Column(String(20), nullable=False, default="candidate", index=True)
    
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    subject = Column(String(500), nullable=False)
    body_html = Column(Text, nullable=False)
    body_text = Column(Text, nullable=True)
    
    variables = Column(JSONB, default=list)
    
    is_active = Column(Boolean, default=True, index=True)
    is_default = Column(Boolean, default=False, index=True)
    is_system = Column(Boolean, default=False, index=True)
    
    version = Column(Integer, default=1)
    
    created_by = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": str(self.id),
            "company_id": self.company_id,
            "stage_name": self.stage_name,
            "template_type": self.template_type,
            "name": self.name,
            "description": self.description,
            "subject": self.subject,
            "body_html": self.body_html,
            "body_text": self.body_text,
            "variables": self.variables or [],
            "is_active": self.is_active,
            "is_default": self.is_default,
            "is_system": self.is_system,
            "version": self.version,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
    
    def __repr__(self):
        return f"<RecruitmentEmailTemplate {self.id} - {self.stage_name} ({self.template_type})>"
