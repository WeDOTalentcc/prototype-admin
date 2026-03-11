"""
Pydantic schemas for WorkOS SSO and SCIM integration.
"""
from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class WorkOSSyncUser(BaseModel):
    """Schema for syncing a user from WorkOS SSO callback."""
    workos_id: str = Field(..., description="WorkOS profile ID")
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    organization_id: Optional[str] = None
    connection_type: Optional[str] = None
    raw_attributes: Optional[Dict[str, Any]] = None


class WorkOSSyncUserResponse(BaseModel):
    """Response after syncing a WorkOS user."""
    id: UUID
    email: str
    name: str
    workos_id: str
    is_new_user: bool
    sso_provider: Optional[str] = None
    
    class Config:
        from_attributes = True


class SCIMUserCreated(BaseModel):
    """Schema for SCIM dsync.user.created event."""
    workos_id: str
    email: Optional[EmailStr] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    directory_id: Optional[str] = None
    state: Optional[str] = None
    raw_attributes: Optional[Dict[str, Any]] = None


class SCIMUserUpdated(BaseModel):
    """Schema for SCIM dsync.user.updated event."""
    workos_id: str
    email: Optional[EmailStr] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    state: Optional[str] = None
    raw_attributes: Optional[Dict[str, Any]] = None


class SCIMUserDeleted(BaseModel):
    """Schema for SCIM dsync.user.deleted event."""
    workos_id: str
    email: Optional[EmailStr] = None


class SCIMGroupAction(BaseModel):
    """Schema for SCIM group events."""
    workos_id: str
    name: Optional[str] = None
    directory_id: Optional[str] = None


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
    message: Optional[str] = None


class WorkOSGroupResponse(BaseModel):
    """Response schema for WorkOS SCIM Group."""
    id: UUID
    workos_id: str
    directory_id: Optional[str] = None
    name: str
    raw_attributes: Dict[str, Any] = {}
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
    added_by: Optional[str] = None
    
    class Config:
        from_attributes = True


class WorkOSGroupRoleMappingResponse(BaseModel):
    """Response schema for WorkOS Group to Role Mapping."""
    id: UUID
    company_id: str
    workos_group_id: UUID
    role: str
    permissions: List[str] = []
    created_at: datetime
    created_by: Optional[str] = None
    
    class Config:
        from_attributes = True


class SSOAuditLogCreate(BaseModel):
    """Schema for creating SSO Audit Log entries."""
    company_id: str
    event_type: str = Field(..., description="Event type: sso.login, scim.user.created, scim.user.updated, scim.user.deleted, scim.group.created, scim.group.updated, scim.group.deleted, scim.group.user_added, scim.group.user_removed")
    actor_id: Optional[str] = None
    actor_email: Optional[str] = None
    target_id: Optional[str] = None
    target_email: Optional[str] = None
    source_ip: Optional[str] = None
    user_agent: Optional[str] = None
    workos_event_id: Optional[str] = None
    payload: Dict[str, Any] = {}


class SSOAuditLogResponse(BaseModel):
    """Response schema for SSO Audit Log."""
    id: UUID
    company_id: str
    event_type: str
    actor_id: Optional[str] = None
    actor_email: Optional[str] = None
    target_id: Optional[str] = None
    target_email: Optional[str] = None
    source_ip: Optional[str] = None
    user_agent: Optional[str] = None
    workos_event_id: Optional[str] = None
    payload: Dict[str, Any] = {}
    created_at: datetime
    
    class Config:
        from_attributes = True
