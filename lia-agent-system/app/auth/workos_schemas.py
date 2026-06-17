"""
Pydantic schemas for WorkOS SSO and SCIM integration.
"""
from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field
from app.shared.types import WeDoBaseModel


class WorkOSSyncUser(BaseModel):
    """Schema for syncing a user from WorkOS SSO callback."""
    workos_id: str = Field(..., description="WorkOS profile ID")
    email: EmailStr
    first_name: str | None = None
    last_name: str | None = None
    organization_id: str | None = None
    connection_type: str | None = None
    raw_attributes: dict[str, Any] | None = None


class WorkOSSyncUserResponse(BaseModel):
    """Response after syncing a WorkOS user."""
    id: UUID
    email: str
    name: str
    workos_id: str
    is_new_user: bool
    sso_provider: str | None = None
    
    class Config:
        from_attributes = True


class SCIMUserCreated(BaseModel):
    """Schema for SCIM dsync.user.created event."""
    workos_id: str
    email: EmailStr | None = None
    first_name: str | None = None
    last_name: str | None = None
    directory_id: str | None = None
    state: str | None = None
    raw_attributes: dict[str, Any] | None = None


class SCIMUserUpdated(BaseModel):
    """Schema for SCIM dsync.user.updated event."""
    workos_id: str
    email: EmailStr | None = None
    first_name: str | None = None
    last_name: str | None = None
    state: str | None = None
    raw_attributes: dict[str, Any] | None = None


class SCIMUserDeleted(BaseModel):
    """Schema for SCIM dsync.user.deleted event."""
    workos_id: str
    email: EmailStr | None = None


class SCIMGroupAction(BaseModel):
    """Schema for SCIM group events."""
    workos_id: str
    name: str | None = None
    directory_id: str | None = None


class SCIMGroupMembership(BaseModel):
    """Schema for SCIM group membership events."""
    user_id: str
    group_id: str
    action: str = Field(..., pattern="^(added|removed)$")


class SCIMActionResponse(BaseModel):
    """Generic response for SCIM actions."""
    success: bool
    action: str
    workos_id: str
    message: str | None = None


class WorkOSGroupResponse(BaseModel):
    """Response schema for WorkOS SCIM Group."""
    id: UUID
    workos_id: str
    directory_id: str | None = None
    name: str
    raw_attributes: dict[str, Any] = {}
    is_active: bool = True
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class WorkOSGroupMembershipResponse(BaseModel):
    """Response schema for WorkOS Group Membership."""
    id: UUID
    group_id: UUID
    user_id: UUID
    added_at: datetime
    added_by: str | None = None
    
    class Config:
        from_attributes = True


class WorkOSGroupRoleMappingResponse(BaseModel):
    """Response schema for WorkOS Group to Role Mapping."""
    id: UUID
    company_id: str
    workos_group_id: UUID
    role: str
    permissions: list[str] = []
    created_at: datetime
    created_by: str | None = None
    
    class Config:
        from_attributes = True


class SSOAuditLogCreate(WeDoBaseModel):
    """Schema for creating SSO Audit Log entries."""
    company_id: str
    event_type: str = Field(..., description="Event type: sso.login, scim.user.created, scim.user.updated, scim.user.deleted, scim.group.created, scim.group.updated, scim.group.deleted, scim.group.user_added, scim.group.user_removed")
    actor_id: str | None = None
    actor_email: str | None = None
    target_id: str | None = None
    target_email: str | None = None
    source_ip: str | None = None
    user_agent: str | None = None
    workos_event_id: str | None = None
    payload: dict[str, Any] = {}


class SSOAuditLogResponse(BaseModel):
    """Response schema for SSO Audit Log."""
    id: UUID
    company_id: str
    event_type: str
    actor_id: str | None = None
    actor_email: str | None = None
    target_id: str | None = None
    target_email: str | None = None
    source_ip: str | None = None
    user_agent: str | None = None
    workos_event_id: str | None = None
    payload: dict[str, Any] = {}
    created_at: datetime
    
    class Config:
        from_attributes = True
