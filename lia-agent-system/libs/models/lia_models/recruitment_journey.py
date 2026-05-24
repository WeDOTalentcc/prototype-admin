"""
Recruitment Journey models for process configuration, templates, and SLAs.
"""
from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy import Column, String, Integer, DateTime, Text, JSON, Boolean, Float, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
import uuid
import enum

from lia_config.database import Base


class TemplateType(str, enum.Enum):
    EXECUTIVE = "executive"
    TECHNICAL = "technical"
    OPERATIONAL = "operational"
    MASS_HIRING = "mass_hiring"
    INTERN = "intern"
    CONSULTANT = "consultant"


class AutomationType(str, enum.Enum):
    EMAIL_NOTIFICATION = "email_notification"
    STATUS_CHANGE = "status_change"
    TASK_CREATION = "task_creation"
    ALERT_TRIGGER = "alert_trigger"
    WEBHOOK_CALL = "webhook_call"
    AI_SCREENING = "ai_screening"


class RecruitmentTemplate(Base):
    """Templates for different job types with pre-configured stages and settings."""
    __tablename__ = "recruitment_templates"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("company_profiles.id"), nullable=False, index=True)
    
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    template_type = Column(String(100), default="technical")
    
    stages_config = Column(JSON, default=list)
    required_fields = Column(ARRAY(String), default=list)
    optional_fields = Column(ARRAY(String), default=list)
    
    default_priority = Column(String(50), default="normal")
    default_sla_days = Column(Integer, default=30)
    
    ai_screening_enabled = Column(Boolean, default=True)
    ai_matching_enabled = Column(Boolean, default=True)
    ai_config = Column(JSON, default=dict)
    
    is_default = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(255), nullable=True)
    
    __table_args__ = (
        Index('ix_recruitment_templates_company', 'company_id'),
        Index('ix_recruitment_templates_type', 'template_type'),
    {"extend_existing": True}, )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "company_id": str(self.company_id),
            "name": self.name,
            "description": self.description,
            "template_type": self.template_type,
            "stages_config": self.stages_config or [],
            "required_fields": self.required_fields or [],
            "optional_fields": self.optional_fields or [],
            "default_priority": self.default_priority,
            "default_sla_days": self.default_sla_days,
            "ai_screening_enabled": self.ai_screening_enabled,
            "ai_matching_enabled": self.ai_matching_enabled,
            "ai_config": self.ai_config or {},
            "is_default": self.is_default,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "created_by": self.created_by,
        }
    
    def __repr__(self):
        return f"<RecruitmentTemplate {self.name} ({self.template_type})>"


class RecruitmentSLA(Base):
    """SLA definitions for recruitment stages."""
    __tablename__ = "recruitment_slas"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("company_profiles.id"), nullable=False, index=True)
    
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    stage_id = Column(UUID(as_uuid=True), nullable=True)
    stage_name = Column(String(100), nullable=True)
    
    target_days = Column(Integer, nullable=False)
    warning_days = Column(Integer, nullable=True)
    critical_days = Column(Integer, nullable=True)
    
    applies_to_job_types = Column(ARRAY(String), default=list)
    applies_to_priority = Column(ARRAY(String), default=list)
    
    warning_action = Column(JSON, default=dict)
    critical_action = Column(JSON, default=dict)
    
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('ix_recruitment_slas_company', 'company_id'),
        Index('ix_recruitment_slas_stage', 'stage_id'),
    {"extend_existing": True}, )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "company_id": str(self.company_id),
            "name": self.name,
            "description": self.description,
            "stage_id": str(self.stage_id) if self.stage_id else None,
            "stage_name": self.stage_name,
            "target_days": self.target_days,
            "warning_days": self.warning_days,
            "critical_days": self.critical_days,
            "applies_to_job_types": self.applies_to_job_types or [],
            "applies_to_priority": self.applies_to_priority or [],
            "warning_action": self.warning_action or {},
            "critical_action": self.critical_action or {},
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
    
    def __repr__(self):
        return f"<RecruitmentSLA {self.name} (target={self.target_days}d)>"


class RecruitmentAutomation(Base):
    """Automation rules for recruitment workflow."""
    __tablename__ = "recruitment_automations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("company_profiles.id"), nullable=False, index=True)
    
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    automation_type = Column(String(100), nullable=False)
    
    trigger_event = Column(String(100), nullable=False)
    trigger_conditions = Column(JSON, default=dict)
    
    action_config = Column(JSON, default=dict)
    
    is_enabled = Column(Boolean, default=True)
    execution_count = Column(Integer, default=0)
    last_executed_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('ix_recruitment_automations_company', 'company_id'),
        Index('ix_recruitment_automations_type', 'automation_type'),
        Index('ix_recruitment_automations_trigger', 'trigger_event'),
    {"extend_existing": True}, )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "company_id": str(self.company_id),
            "name": self.name,
            "description": self.description,
            "automation_type": self.automation_type,
            "trigger_event": self.trigger_event,
            "trigger_conditions": self.trigger_conditions or {},
            "action_config": self.action_config or {},
            "is_enabled": self.is_enabled,
            "execution_count": self.execution_count,
            "last_executed_at": self.last_executed_at.isoformat() if self.last_executed_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
    
    def __repr__(self):
        return f"<RecruitmentAutomation {self.name} ({self.automation_type})>"


class SLAViolation(Base):
    """Track SLA violations for reporting."""
    __tablename__ = "sla_violations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sla_id = Column(UUID(as_uuid=True), ForeignKey("recruitment_slas.id"), nullable=False, index=True)
    job_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    candidate_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    company_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    violation_type = Column(String(50))
    stage_name = Column(String(100))
    
    days_elapsed = Column(Integer)
    target_days = Column(Integer)
    
    resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime, nullable=True)
    resolution_notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('ix_sla_violations_sla', 'sla_id'),
        Index('ix_sla_violations_job', 'job_id'),
        Index('ix_sla_violations_company', 'company_id'),
        Index('ix_sla_violations_resolved', 'resolved'),
    {"extend_existing": True}, )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "sla_id": str(self.sla_id),
            "job_id": str(self.job_id),
            "candidate_id": str(self.candidate_id) if self.candidate_id else None,
            "company_id": str(self.company_id),
            "violation_type": self.violation_type,
            "stage_name": self.stage_name,
            "days_elapsed": self.days_elapsed,
            "target_days": self.target_days,
            "resolved": self.resolved,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "resolution_notes": self.resolution_notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
    
    def __repr__(self):
        return f"<SLAViolation {self.violation_type} (stage={self.stage_name})>"


DEFAULT_TEMPLATES = [
    {
        "name": "Processo Técnico",
        "description": "Template padrão para vagas técnicas com entrevistas técnicas e de competências",
        "template_type": "technical",
        "stages_config": [
            {"name": "sourcing", "order": 1},
            {"name": "screening", "order": 2},
            {"name": "interview_technical", "order": 3},
            {"name": "interview_hr", "order": 4},
            {"name": "offer", "order": 5},
        ],
        "required_fields": ["skills", "experience_years", "education"],
        "default_priority": "normal",
        "default_sla_days": 30,
        "ai_screening_enabled": True,
        "ai_matching_enabled": True,
    },
    {
        "name": "Processo Executivo",
        "description": "Template para posições de liderança e C-level",
        "template_type": "executive",
        "stages_config": [
            {"name": "sourcing", "order": 1},
            {"name": "screening", "order": 2},
            {"name": "interview_hr", "order": 3},
            {"name": "interview_manager", "order": 4},
            {"name": "interview_executive", "order": 5},
            {"name": "offer", "order": 6},
        ],
        "required_fields": ["leadership_experience", "strategic_vision", "education"],
        "default_priority": "high",
        "default_sla_days": 45,
        "ai_screening_enabled": True,
        "ai_matching_enabled": True,
    },
    {
        "name": "Processo Operacional",
        "description": "Template simplificado para vagas operacionais",
        "template_type": "operational",
        "stages_config": [
            {"name": "sourcing", "order": 1},
            {"name": "screening", "order": 2},
            {"name": "interview_hr", "order": 3},
            {"name": "offer", "order": 4},
        ],
        "required_fields": ["availability", "location"],
        "default_priority": "normal",
        "default_sla_days": 15,
        "ai_screening_enabled": True,
        "ai_matching_enabled": False,
    },
    {
        "name": "Recrutamento em Massa",
        "description": "Template otimizado para alto volume de contratações",
        "template_type": "mass_hiring",
        "stages_config": [
            {"name": "sourcing", "order": 1},
            {"name": "screening", "order": 2},
            {"name": "offer", "order": 3},
        ],
        "required_fields": ["availability"],
        "default_priority": "normal",
        "default_sla_days": 10,
        "ai_screening_enabled": True,
        "ai_matching_enabled": False,
    },
    {
        "name": "Programa de Estágio",
        "description": "Template para programas de estágio e trainee",
        "template_type": "intern",
        "stages_config": [
            {"name": "sourcing", "order": 1},
            {"name": "screening", "order": 2},
            {"name": "group_dynamics", "order": 3},
            {"name": "interview_hr", "order": 4},
            {"name": "offer", "order": 5},
        ],
        "required_fields": ["education", "graduation_date"],
        "default_priority": "normal",
        "default_sla_days": 60,
        "ai_screening_enabled": True,
        "ai_matching_enabled": True,
    },
]


DEFAULT_SLAS = [
    {
        "name": "SLA Triagem Inicial",
        "description": "Tempo máximo para primeira análise do candidato",
        "stage_name": "screening",
        "target_days": 3,
        "warning_days": 2,
        "critical_days": 4,
        "warning_action": {"notify": ["recruiter"], "type": "email"},
        "critical_action": {"notify": ["recruiter", "manager"], "type": "email", "escalate": True},
    },
    {
        "name": "SLA Entrevista RH",
        "description": "Tempo máximo para agendar entrevista RH",
        "stage_name": "interview_hr",
        "target_days": 5,
        "warning_days": 3,
        "critical_days": 7,
        "warning_action": {"notify": ["recruiter"], "type": "email"},
        "critical_action": {"notify": ["recruiter", "manager"], "type": "email", "escalate": True},
    },
    {
        "name": "SLA Entrevista Técnica",
        "description": "Tempo máximo para completar entrevista técnica",
        "stage_name": "interview_technical",
        "target_days": 7,
        "warning_days": 5,
        "critical_days": 10,
        "warning_action": {"notify": ["recruiter", "interviewer"], "type": "email"},
        "critical_action": {"notify": ["recruiter", "manager", "interviewer"], "type": "email", "escalate": True},
    },
    {
        "name": "SLA Proposta",
        "description": "Tempo máximo para enviar proposta após aprovação",
        "stage_name": "offer",
        "target_days": 2,
        "warning_days": 1,
        "critical_days": 3,
        "warning_action": {"notify": ["recruiter"], "type": "email"},
        "critical_action": {"notify": ["recruiter", "manager"], "type": "email", "escalate": True},
    },
]


DEFAULT_AUTOMATIONS = [
    {
        "name": "Notificação de Nova Candidatura",
        "description": "Envia notificação quando um novo candidato se inscreve",
        "automation_type": "email_notification",
        "trigger_event": "candidate_applied",
        "trigger_conditions": {},
        "action_config": {
            "template": "new_application",
            "recipients": ["recruiter"],
        },
    },
    {
        "name": "Triagem Automática AI",
        "description": "Executa triagem automática usando IA quando candidato entra na etapa de screening",
        "automation_type": "ai_screening",
        "trigger_event": "stage_changed",
        "trigger_conditions": {"to_stage": "screening"},
        "action_config": {
            "run_cv_analysis": True,
            "run_skills_match": True,
            "auto_advance_threshold": 80,
        },
    },
    {
        "name": "Alerta de SLA",
        "description": "Dispara alerta quando SLA está próximo do limite",
        "automation_type": "alert_trigger",
        "trigger_event": "sla_warning",
        "trigger_conditions": {},
        "action_config": {
            "alert_type": "sla_warning",
            "notify": ["recruiter"],
        },
    },
    {
        "name": "Criar Tarefa de Follow-up",
        "description": "Cria tarefa de follow-up após entrevista",
        "automation_type": "task_creation",
        "trigger_event": "interview_completed",
        "trigger_conditions": {},
        "action_config": {
            "task_type": "follow_up",
            "due_days": 2,
            "assign_to": "recruiter",
        },
    },
]
