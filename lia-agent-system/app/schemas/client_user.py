"""
Pydantic schemas for ClientUser endpoints.
"""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field
from app.shared.types import WeDoBaseModel


class ClientUserBase(BaseModel):
    email: EmailStr
    name: str = Field(..., min_length=1, max_length=255)
    role: str = Field(default="viewer", description="Role: admin, recruiter, viewer, manager")
    permissions: list[str] | None = []


class ClientUserCreate(ClientUserBase):
    pass


class ClientUserUpdate(WeDoBaseModel):
    email: EmailStr | None = None
    name: str | None = Field(None, min_length=1, max_length=255)
    permissions: list[str] | None = None
    status: str | None = Field(None, description="Status: active, inactive, pending")
    resend_invitation: bool | None = Field(None, description="Set to true to resend invitation email")
    # RBAC Sprint 2 (2026-05-25): department + manager FKs.
    # Plan canonical: ~/.claude/plans/jolly-roaming-moler.md
    # NB: backend endpoint deve sync client_users.department_id → users.department_id
    # quando client_users.user_id matches (filter logic em crud.py lê users.department_id).
    department_id: str | None = Field(None, description="Department UUID (FK to departments.id)")
    manager_id: str | None = Field(None, description="Manager UUID (FK to client_users.id) — reserved for approval chains")
    # RBAC Sprint 5.5 (2026-05-25): financial PII privilege grant (LGPD Art. 6 III minimização).
    # Tenant admin grants per-user via UI; sync to users.can_view_salary (auth table).
    # Backend gate: only current_user.role == 'admin' can mutate this field.
    can_view_salary: bool | None = Field(None, description="Grant: allow this user to view salary fields. Tenant admin only.")
    # RBAC Sprint 8 (2026-05-26): sensitive PII grant (LGPD Art. 5 II).
    # Covers CPF + DoB + address + secondary contacts. Tenant admin only.
    can_view_sensitive_pii: bool | None = Field(None, description="Grant: allow this user to view sensitive PII (CPF, DoB, address, secondary contacts). Tenant admin only.")


class AcceptInvitationRequest(WeDoBaseModel):
    token: str = Field(..., description="Invitation token from the email link")


class AcceptInvitationResponse(BaseModel):
    success: bool
    message: str
    redirect_url: str | None = None
    user: dict | None = None


class ClientUserRoleUpdate(WeDoBaseModel):
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
