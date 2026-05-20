"""
Pydantic schemas for ClientUser endpoints.
"""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class ClientUserBase(BaseModel):
    email: EmailStr
    name: str = Field(..., min_length=1, max_length=255)
    role: str = Field(default="viewer", description="Role: admin, recruiter, viewer, manager")
    permissions: list[str] | None = []


class ClientUserCreate(ClientUserBase):
    pass


class ClientUserUpdate(BaseModel):
    email: EmailStr | None = None
    name: str | None = Field(None, min_length=1, max_length=255)
    permissions: list[str] | None = None
    status: str | None = Field(None, description="Status: active, inactive, pending")
    resend_invitation: bool | None = Field(None, description="Set to true to resend invitation email")


class AcceptInvitationRequest(BaseModel):
    token: str = Field(..., description="Invitation token from the email link")


class AcceptInvitationResponse(BaseModel):
    success: bool
    message: str
    redirect_url: str | None = None
    user: dict | None = None


class ClientUserRoleUpdate(BaseModel):
    role: str = Field(..., description="New role: admin, recruiter, viewer, manager")


class ClientUserResponse(ClientUserBase):
    id: UUID
    company_id: UUID
    user_id: UUID | None = None
    status: str
    invited_at: datetime | None = None
    accepted_at: datetime | None = None
    last_login_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ClientUserListResponse(BaseModel):
    success: bool
    data: dict
    
    class Config:
        from_attributes = True


class ClientUserDetailResponse(BaseModel):
    success: bool
    data: ClientUserResponse
    
    class Config:
        from_attributes = True
