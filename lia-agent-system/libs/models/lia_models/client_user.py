"""
ClientUser model for managing users within a client company.

Multi-tenant user management with roles and permissions.
"""
from datetime import datetime, timedelta
from sqlalchemy import Column, String, DateTime, Boolean, JSON, Index, ForeignKey, LargeBinary
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
import secrets
import enum
from typing import Dict, Any, List, Optional

from lia_config.database import Base
from app.shared.encryption.encrypted_field_mixin import EncryptedFieldMixin

INVITATION_TOKEN_EXPIRY_DAYS = 7


class ClientUserRole(str, enum.Enum):
    """Available roles for client users."""
    ADMIN = "admin"
    RECRUITER = "recruiter"
    VIEWER = "viewer"
    MANAGER = "manager"


class ClientUserStatus(str, enum.Enum):
    """Status of a client user."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"


class ClientUser(EncryptedFieldMixin, Base):
    """
    ClientUser model.
    
    Represents a user within a client company with specific roles and permissions.

    PII encryption (transparent dual-write via EncryptedFieldMixin):
      - Every write to ``email`` also writes Fernet-encrypted bytes into
        ``email_encrypted`` and a SHA-256 hash into ``email_hash``.
    """
    __tablename__ = "client_users"

    # "_email_raw" → hybrid_property "email" registered by EncryptedFieldMixin
    _pii_encrypt_fields = [
        ("_email_raw", "_email_encrypted", "email_hash"),
    ]

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey('client_accounts.id'), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), nullable=True)
    
    # Raw DB column for email — NULL for new writes (post-migration 060).
    # Pre-migration rows retain plaintext until pii.backfill_encrypt_existing completes.
    # DB column name is "email" for schema backward compat. Access via hybrid "email".
    _email_raw = Column("email", String(255), nullable=True)
    # PII-encrypted backing columns (added by migration 060)
    _email_encrypted = Column("email_encrypted", LargeBinary, nullable=True)
    email_hash = Column(String(64), nullable=True, index=True)
    name = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default=ClientUserRole.VIEWER.value)
    # RBAC Sprint 2 (2026-05-25): department + manager FK. Plan: ~/.claude/plans/jolly-roaming-moler.md
    department_id = Column(UUID(as_uuid=True), ForeignKey("departments.id", ondelete="SET NULL"), nullable=True, index=True)
    manager_id = Column(UUID(as_uuid=True), ForeignKey("client_users.id", ondelete="SET NULL"), nullable=True, index=True)
    permissions = Column(JSON, nullable=True, default=list)
    status = Column(String(20), default=ClientUserStatus.PENDING.value, index=True)
    
    invitation_token = Column(String(255), nullable=True, index=True)
    invitation_expires_at = Column(DateTime, nullable=True)
    
    invited_at = Column(DateTime, default=datetime.utcnow)
    accepted_at = Column(DateTime, nullable=True)
    last_login_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    is_deleted = Column(Boolean, default=False, index=True)
    deleted_at = Column(DateTime, nullable=True)
    deleted_by = Column(String(255), nullable=True)
    
    __table_args__ = (
        Index('idx_client_user_company', 'company_id'),
        Index('idx_client_user_email', 'email'),
        Index('idx_client_user_status', 'status'),
        Index('idx_client_user_role', 'role'),
        Index('idx_client_user_not_deleted', 'is_deleted'),
        # Retained during dual-write phase; dropped in migration 063 (Phase 4).
        Index('idx_client_user_company_email', 'company_id', 'email', unique=True),
        Index('idx_client_user_invitation_token', 'invitation_token'),
    {"extend_existing": True}, )
    
    def __repr__(self):
        return f"<ClientUser {self.id} - {self.email} ({self.role})>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "id": str(self.id),
            "company_id": str(self.company_id),
            "user_id": str(self.user_id) if self.user_id else None,
            "email": self.email,
            "name": self.name,
            "role": self.role,
            "permissions": self.permissions or [],
            "status": self.status,
            "has_pending_invitation": self.has_pending_invitation(),
            "invitation_expires_at": self.invitation_expires_at.isoformat() if self.invitation_expires_at else None,
            "invited_at": self.invited_at.isoformat() if self.invited_at else None,
            "accepted_at": self.accepted_at.isoformat() if self.accepted_at else None,
            "last_login_at": self.last_login_at.isoformat() if self.last_login_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
    
    def generate_invitation_token(self) -> str:
        """Generate a new invitation token and set expiry."""
        self.invitation_token = secrets.token_urlsafe(32)
        self.invitation_expires_at = datetime.utcnow() + timedelta(days=INVITATION_TOKEN_EXPIRY_DAYS)
        self.invited_at = datetime.utcnow()
        return self.invitation_token
    
    def is_invitation_valid(self) -> bool:
        """Check if the invitation token is still valid."""
        if not self.invitation_token:
            return False
        if not self.invitation_expires_at:
            return False
        return datetime.utcnow() < self.invitation_expires_at
    
    def has_pending_invitation(self) -> bool:
        """Check if user has a pending invitation."""
        return (
            self.status == ClientUserStatus.PENDING.value 
            and self.invitation_token is not None 
            and self.is_invitation_valid()
        )
    
    def clear_invitation(self) -> None:
        """Clear invitation token after acceptance."""
        self.invitation_token = None
        self.invitation_expires_at = None
        self.accepted_at = datetime.utcnow()
        self.status = ClientUserStatus.ACTIVE.value


CLIENT_USER_ROLE_OPTIONS = [
    {"value": ClientUserRole.ADMIN.value, "label": "Administrador", "description": "Acesso total ao sistema"},
    {"value": ClientUserRole.MANAGER.value, "label": "Gerente", "description": "Gerenciar vagas e equipe"},
    {"value": ClientUserRole.RECRUITER.value, "label": "Recrutador", "description": "Gerenciar processos seletivos"},
    {"value": ClientUserRole.VIEWER.value, "label": "Visualizador", "description": "Apenas visualização"},
]

CLIENT_USER_STATUS_OPTIONS = [
    {"value": ClientUserStatus.ACTIVE.value, "label": "Ativo", "description": "Usuário ativo no sistema"},
    {"value": ClientUserStatus.INACTIVE.value, "label": "Inativo", "description": "Usuário desativado"},
    {"value": ClientUserStatus.PENDING.value, "label": "Pendente", "description": "Aguardando aceite do convite"},
]
