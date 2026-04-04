"""
User model for authentication.
"""
import uuid
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import Column, String, Boolean, DateTime, Enum
from sqlalchemy.dialects.postgresql import UUID, ARRAY, JSONB

from app.core.database import Base


class UserRole(str, PyEnum):
    """User role enumeration."""
    admin = "admin"
    recruiter = "recruiter"
    viewer = "viewer"


class User(Base):
    """User model for authentication."""
    
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=True)
    name = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.viewer, nullable=False)
    company_id = Column(String(255), nullable=True, index=True, default=None)
    is_active = Column(Boolean, default=True, nullable=False)
    permissions = Column(ARRAY(String), default=[], nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    email_verified = Column(Boolean, default=False, nullable=False)
    email_verification_token = Column(String(255), nullable=True)
    email_verification_token_expires = Column(DateTime, nullable=True)
    password_reset_token = Column(String(255), nullable=True)
    password_reset_token_expires = Column(DateTime, nullable=True)
    invitation_token = Column(String(255), nullable=True)
    invitation_sent_at = Column(DateTime, nullable=True)
    
    notification_preferences = Column(JSONB, nullable=True, default=dict, server_default="{}")

    azure_ad_object_id = Column(String(255), nullable=True, index=True)
    workos_id = Column(String(255), unique=True, nullable=True, index=True)
    workos_directory_id = Column(String(255), nullable=True, index=True)
    workos_organization_id = Column(String(255), nullable=True, index=True)
    sso_provider = Column(String(100), nullable=True)
    is_scim_managed = Column(Boolean, default=False, nullable=False)
    last_sso_login_at = Column(DateTime, nullable=True)
    
    def can_access_company(self, company_id: str) -> bool:
        """Check if user can access the given company."""
        if self.role == UserRole.admin:
            return True
        return self.company_id == company_id
    
    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, role={self.role}, company={self.company_id})>"
