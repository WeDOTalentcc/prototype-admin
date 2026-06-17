"""
Admin Settings models for RBAC, notifications, and security.
"""
from datetime import datetime
from typing import Optional, Dict, List
from sqlalchemy import Column, String, Integer, DateTime, Text, JSON, Boolean, Float, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
import uuid
import enum

from lia_config.database import Base


class PermissionLevel(str, enum.Enum):
    NONE = "none"
    READ = "read"
    WRITE = "write"
    ADMIN = "admin"


AVAILABLE_PERMISSIONS = {
    "candidates": {
        "name": "Candidatos",
        "description": "Gerenciar candidatos e perfis",
        "levels": ["none", "read", "write", "admin"]
    },
    "jobs": {
        "name": "Vagas",
        "description": "Gerenciar vagas de emprego",
        "levels": ["none", "read", "write", "admin"]
    },
    "pipeline": {
        "name": "Pipeline",
        "description": "Gerenciar funil de recrutamento",
        "levels": ["none", "read", "write", "admin"]
    },
    "interviews": {
        "name": "Entrevistas",
        "description": "Agendar e gerenciar entrevistas",
        "levels": ["none", "read", "write", "admin"]
    },
    "reports": {
        "name": "Relatórios",
        "description": "Visualizar e gerar relatórios",
        "levels": ["none", "read", "write", "admin"]
    },
    "settings": {
        "name": "Configurações",
        "description": "Configurações da empresa",
        "levels": ["none", "read", "write", "admin"]
    },
    "users": {
        "name": "Usuários",
        "description": "Gerenciar usuários e permissões",
        "levels": ["none", "read", "write", "admin"]
    },
    "integrations": {
        "name": "Integrações",
        "description": "Gerenciar integrações ATS e APIs",
        "levels": ["none", "read", "write", "admin"]
    },
    "templates": {
        "name": "Templates",
        "description": "Gerenciar templates de email e comunicação",
        "levels": ["none", "read", "write", "admin"]
    },
    "analytics": {
        "name": "Analytics",
        "description": "Visualizar analytics e métricas",
        "levels": ["none", "read", "write", "admin"]
    },
    "lia_chat": {
        "name": "Chat LIA",
        "description": "Usar assistente LIA",
        "levels": ["none", "read", "write", "admin"]
    },
    "bulk_actions": {
        "name": "Ações em Massa",
        "description": "Executar ações em massa",
        "levels": ["none", "read", "write", "admin"]
    }
}


DEFAULT_ROLES = [
    {
        "name": "Admin",
        "description": "Administrador com acesso total ao sistema",
        "is_system_role": True,
        "permissions": {
            "candidates": "admin",
            "jobs": "admin",
            "pipeline": "admin",
            "interviews": "admin",
            "reports": "admin",
            "settings": "admin",
            "users": "admin",
            "integrations": "admin",
            "templates": "admin",
            "analytics": "admin",
            "lia_chat": "admin",
            "bulk_actions": "admin"
        }
    },
    {
        "name": "Recruiter",
        "description": "Recrutador com acesso completo a candidatos e vagas",
        "is_system_role": True,
        "permissions": {
            "candidates": "write",
            "jobs": "write",
            "pipeline": "write",
            "interviews": "write",
            "reports": "read",
            "settings": "read",
            "users": "none",
            "integrations": "read",
            "templates": "write",
            "analytics": "read",
            "lia_chat": "write",
            "bulk_actions": "write"
        }
    },
    {
        "name": "Hiring Manager",
        "description": "Gestor de contratação com foco em avaliação",
        "is_system_role": True,
        "permissions": {
            "candidates": "read",
            "jobs": "read",
            "pipeline": "read",
            "interviews": "write",
            "reports": "read",
            "settings": "none",
            "users": "none",
            "integrations": "none",
            "templates": "read",
            "analytics": "read",
            "lia_chat": "read",
            "bulk_actions": "none"
        }
    },
    {
        "name": "Viewer",
        "description": "Visualizador com acesso somente leitura",
        "is_system_role": True,
        "permissions": {
            "candidates": "read",
            "jobs": "read",
            "pipeline": "read",
            "interviews": "read",
            "reports": "read",
            "settings": "none",
            "users": "none",
            "integrations": "none",
            "templates": "read",
            "analytics": "read",
            "lia_chat": "read",
            "bulk_actions": "none"
        }
    }
]


class AdminRole(Base):
    """Admin roles with permissions."""
    __tablename__ = "admin_roles"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("company_profiles.id"), nullable=False)
    
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    permissions = Column(JSON, default={})
    
    is_system_role = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            "id": str(self.id),
            "company_id": str(self.company_id),
            "name": self.name,
            "description": self.description,
            "permissions": self.permissions,
            "is_system_role": self.is_system_role,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class AdminUserRole(Base):
    """User-Role assignments."""
    __tablename__ = "admin_user_roles"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    role_id = Column(UUID(as_uuid=True), ForeignKey("admin_roles.id"), nullable=False)
    company_id = Column(UUID(as_uuid=True), ForeignKey("company_profiles.id"), nullable=False)
    
    assigned_at = Column(DateTime, default=datetime.utcnow)
    assigned_by = Column(String(255), nullable=True)
    
    role = relationship("AdminRole")
    
    def to_dict(self):
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "role_id": str(self.role_id),
            "company_id": str(self.company_id),
            "assigned_at": self.assigned_at.isoformat() if self.assigned_at else None,
            "assigned_by": self.assigned_by,
            "role": self.role.to_dict() if self.role else None
        }


class NotificationPolicy(Base):
    """Notification policies for different events."""
    __tablename__ = "notification_policies"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("company_profiles.id"), nullable=False)
    
    name = Column(String(255), nullable=False)
    event_type = Column(String(100), nullable=False)
    
    channels = Column(ARRAY(String), default=[])
    
    recipient_type = Column(String(50))
    recipients = Column(ARRAY(String), default=[])
    
    subject_template = Column(String(500), nullable=True)
    body_template = Column(Text, nullable=True)
    
    is_enabled = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            "id": str(self.id),
            "company_id": str(self.company_id),
            "name": self.name,
            "event_type": self.event_type,
            "channels": self.channels or [],
            "recipient_type": self.recipient_type,
            "recipients": self.recipients or [],
            "subject_template": self.subject_template,
            "body_template": self.body_template,
            "is_enabled": self.is_enabled,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


NOTIFICATION_EVENT_TYPES = [
    {"value": "candidate_applied", "label": "Candidato se inscreveu"},
    {"value": "candidate_stage_changed", "label": "Candidato mudou de etapa"},
    {"value": "interview_scheduled", "label": "Entrevista agendada"},
    {"value": "interview_reminder", "label": "Lembrete de entrevista"},
    {"value": "sla_warning", "label": "Alerta de SLA"},
    {"value": "sla_violation", "label": "Violação de SLA"},
    {"value": "job_published", "label": "Vaga publicada"},
    {"value": "job_closed", "label": "Vaga encerrada"},
    {"value": "candidate_hired", "label": "Candidato contratado"},
    {"value": "candidate_rejected", "label": "Candidato rejeitado"},
    {"value": "approval_required", "label": "Aprovação necessária"},
    {"value": "approval_completed", "label": "Aprovação concluída"},
    {"value": "task_assigned", "label": "Tarefa atribuída"},
    {"value": "task_overdue", "label": "Tarefa atrasada"},
    {"value": "new_user_added", "label": "Novo usuário adicionado"},
    {"value": "daily_digest", "label": "Resumo diário"},
    {"value": "weekly_report", "label": "Relatório semanal"}
]


class SecuritySetting(Base):
    """Security configurations."""
    __tablename__ = "security_settings"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("company_profiles.id"), nullable=False, unique=True)
    
    require_2fa = Column(Boolean, default=False)
    session_timeout_minutes = Column(Integer, default=480)
    max_login_attempts = Column(Integer, default=5)
    
    password_min_length = Column(Integer, default=8)
    password_require_uppercase = Column(Boolean, default=True)
    password_require_numbers = Column(Boolean, default=True)
    password_require_special = Column(Boolean, default=False)
    password_expiry_days = Column(Integer, default=90)
    
    ip_whitelist = Column(ARRAY(String), default=[])
    ip_blacklist = Column(ARRAY(String), default=[])
    
    audit_logging_enabled = Column(Boolean, default=True)
    audit_retention_days = Column(Integer, default=365)
    
    data_export_allowed = Column(Boolean, default=True)
    data_retention_days = Column(Integer, default=730)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            "id": str(self.id),
            "company_id": str(self.company_id),
            "require_2fa": self.require_2fa,
            "session_timeout_minutes": self.session_timeout_minutes,
            "max_login_attempts": self.max_login_attempts,
            "password_min_length": self.password_min_length,
            "password_require_uppercase": self.password_require_uppercase,
            "password_require_numbers": self.password_require_numbers,
            "password_require_special": self.password_require_special,
            "password_expiry_days": self.password_expiry_days,
            "ip_whitelist": self.ip_whitelist or [],
            "ip_blacklist": self.ip_blacklist or [],
            "audit_logging_enabled": self.audit_logging_enabled,
            "audit_retention_days": self.audit_retention_days,
            "data_export_allowed": self.data_export_allowed,
            "data_retention_days": self.data_retention_days,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class AdminAuditLog(Base):
    """Audit logs for admin actions."""
    __tablename__ = "admin_audit_logs"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), nullable=False)
    user_id = Column(UUID(as_uuid=True), nullable=True)
    user_email = Column(String(255), nullable=True)
    
    action = Column(String(100), nullable=False)
    resource_type = Column(String(100), nullable=True)
    resource_id = Column(String(255), nullable=True)
    
    old_value = Column(JSON, default={})
    new_value = Column(JSON, default={})
    
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            "id": str(self.id),
            "company_id": str(self.company_id),
            "user_id": str(self.user_id) if self.user_id else None,
            "user_email": self.user_email,
            "action": self.action,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "old_value": self.old_value,
            "new_value": self.new_value,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
