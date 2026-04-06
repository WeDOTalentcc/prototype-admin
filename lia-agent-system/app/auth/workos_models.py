"""
SQLAlchemy ORM models for WorkOS SCIM Groups and SSO Audit Logs.
"""
import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSON, UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class WorkOSGroup(Base):
    """WorkOS SCIM Group model."""
    
    __tablename__ = "workos_groups"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workos_id = Column(String(255), unique=True, nullable=False, index=True)
    directory_id = Column(String(255), nullable=True, index=True)
    name = Column(String(255), nullable=False)
    raw_attributes = Column(JSON, default=dict, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    memberships = relationship("WorkOSGroupMembership", back_populates="group", cascade="all, delete-orphan")
    role_mappings = relationship("WorkOSGroupRoleMapping", back_populates="group", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<WorkOSGroup(id={self.id}, workos_id={self.workos_id}, name={self.name})>"


class WorkOSGroupMembership(Base):
    """WorkOS SCIM Group Membership model - links users to groups."""
    
    __tablename__ = "workos_group_memberships"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    group_id = Column(UUID(as_uuid=True), ForeignKey("workos_groups.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    added_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    added_by = Column(String(255), nullable=True)
    
    group = relationship("WorkOSGroup", back_populates="memberships")
    user = relationship("User", backref="workos_group_memberships")
    
    def __repr__(self):
        return f"<WorkOSGroupMembership(id={self.id}, group_id={self.group_id}, user_id={self.user_id})>"


class WorkOSGroupRoleMapping(Base):
    """WorkOS Group to Role Mapping - maps SCIM groups to application roles."""
    
    __tablename__ = "workos_group_role_mappings"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(String(255), nullable=False, index=True)
    workos_group_id = Column(UUID(as_uuid=True), ForeignKey("workos_groups.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(50), nullable=False)
    permissions = Column(ARRAY(String), default=list, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by = Column(String(255), nullable=True)
    
    group = relationship("WorkOSGroup", back_populates="role_mappings")
    
    def __repr__(self):
        return f"<WorkOSGroupRoleMapping(id={self.id}, company_id={self.company_id}, role={self.role})>"


class SSOAuditLog(Base):
    """SSO/SCIM Audit Log model for security event tracking."""
    
    __tablename__ = "sso_audit_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(String(255), nullable=True, index=True)
    event_type = Column(String(100), nullable=False, index=True)
    actor_id = Column(String(255), nullable=True, index=True)
    actor_email = Column(String(255), nullable=True)
    target_id = Column(String(255), nullable=True, index=True)
    target_email = Column(String(255), nullable=True)
    source_ip = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    workos_event_id = Column(String(255), nullable=True, index=True)
    payload = Column(JSON, default=dict, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    def __repr__(self):
        return f"<SSOAuditLog(id={self.id}, event_type={self.event_type}, actor_email={self.actor_email})>"


class CompanyWorkOSConfig(Base):
    """Maps a company to their WorkOS configuration for tenant isolation."""
    
    __tablename__ = "company_workos_config"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(String(255), unique=True, nullable=False, index=True)
    workos_organization_id = Column(String(255), nullable=True)
    workos_directory_id = Column(String(255), nullable=True, index=True)
    sso_connection_id = Column(String(255), nullable=True)
    sso_enabled = Column(Boolean, default=False, nullable=False)
    scim_enabled = Column(Boolean, default=False, nullable=False)
    sso_domains = Column(ARRAY(String), default=list, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<CompanyWorkOSConfig(id={self.id}, company_id={self.company_id}, directory_id={self.workos_directory_id})>"
