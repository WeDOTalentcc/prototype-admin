"""
Pydantic schemas for authentication.
"""
from datetime import datetime
from enum import Enum, StrEnum
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field
from app.shared.types import WeDoBaseModel


class UserRole(StrEnum):
    """User role enumeration."""
    admin = "admin"
    recruiter = "recruiter"
    viewer = "viewer"


class UserCreate(WeDoBaseModel):
    """Schema for user registration."""
    email: EmailStr
    password: str = Field(..., min_length=8, description="Password must be at least 8 characters")
    name: str = Field(..., min_length=2, max_length=255)


class UserLogin(BaseModel):
    """Schema for user login."""
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """Schema for user response."""
    id: UUID
    email: str
    name: str
    role: UserRole
    company_id: str | None = None
    is_active: bool
    avatar_url: str | None = None
    sso_provider: str | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """Schema for token response."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = Field(..., description="Access token expiration in seconds")


class TokenRefresh(BaseModel):
    """Schema for token refresh request."""
    refresh_token: str


class TokenPayload(WeDoBaseModel):
    """Schema for JWT token payload."""
    sub: str
    exp: datetime
    type: str
    role: str | None = None


class UserUpdate(WeDoBaseModel):
    """Schema for updating a user."""
    email: EmailStr | None = None
    name: str | None = Field(None, min_length=2, max_length=255)
    role: UserRole | None = None
    is_active: bool | None = None


class UserManagementCreate(WeDoBaseModel):
    """Schema for creating users from admin panel."""
    email: EmailStr
    name: str = Field(..., min_length=2, max_length=255)
    role: UserRole = UserRole.viewer
    company_id: str | None = None
    permissions: list[str] = Field(default_factory=list)
    password: str | None = Field(None, description="Password for the user. If not provided, a default will be used.")


class UserManagementResponse(BaseModel):
    """Schema for user management response (includes company_id)."""
    id: UUID
    email: str
    name: str
    role: UserRole
    company_id: str | None = None
    is_active: bool
    permissions: list[str] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserManagementUpdate(WeDoBaseModel):
    """Schema for updating a user from admin panel."""
    email: EmailStr | None = None
    name: str | None = Field(None, min_length=2, max_length=255)
    role: UserRole | None = None
    is_active: bool | None = None
    company_id: str | None = None
    permissions: list[str] | None = None


class ProfileUpdate(WeDoBaseModel):
    """Schema for user updating their own profile."""
    name: str | None = Field(None, min_length=2, max_length=255)
    avatar_url: str | None = Field(None, max_length=1024)


class PasswordChange(BaseModel):
    """Schema for authenticated password change."""
    current_password: str
    new_password: str = Field(..., min_length=8, description="New password must be at least 8 characters")


class PasswordResetRequest(WeDoBaseModel):
    """Schema for password reset request."""
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Schema for password reset confirmation."""
    token: str
    new_password: str = Field(..., min_length=8, description="New password must be at least 8 characters")


class EmailVerificationRequest(WeDoBaseModel):
    """Schema for email verification."""
    token: str


class UserPublicRegister(BaseModel):
    """Schema for public self-registration."""
    email: EmailStr
    name: str = Field(..., min_length=2, max_length=255)
    password: str = Field(..., min_length=8, description="Password must be at least 8 characters")


class InvitationAccept(BaseModel):
    """Schema for accepting an invitation."""
    token: str
    password: str = Field(..., min_length=8, description="Password must be at least 8 characters")


class InvitationInfo(BaseModel):
    """Schema for invitation info response."""
    email: str
    name: str
    company_id: str | None = None
    valid: bool = True
    message: str | None = None
