"""
Pydantic schemas for ClientUser endpoints.
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, EmailStr
from uuid import UUID


class ClientUserBase(BaseModel):
    email: EmailStr
    name: str = Field(..., min_length=1, max_length=255)
    role: str = Field(default="viewer", description="Role: admin, recruiter, viewer, manager")
    permissions: Optional[List[str]] = []


class ClientUserCreate(ClientUserBase):
    pass


class ClientUserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    permissions: Optional[List[str]] = None
    status: Optional[str] = Field(None, description="Status: active, inactive, pending")
    resend_invitation: Optional[bool] = Field(None, description="Set to true to resend invitation email")


class AcceptInvitationRequest(BaseModel):
    token: str = Field(..., description="Invitation token from the email link")


class AcceptInvitationResponse(BaseModel):
    success: bool
    message: str
    redirect_url: Optional[str] = None
    user: Optional[dict] = None


class ClientUserRoleUpdate(BaseModel):
    role: str = Field(..., description="New role: admin, recruiter, viewer, manager")


class ClientUserResponse(ClientUserBase):
    id: UUID
    company_id: UUID
    user_id: Optional[UUID] = None
    status: str
    invited_at: Optional[datetime] = None
    accepted_at: Optional[datetime] = None
    last_login_at: Optional[datetime] = None
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
