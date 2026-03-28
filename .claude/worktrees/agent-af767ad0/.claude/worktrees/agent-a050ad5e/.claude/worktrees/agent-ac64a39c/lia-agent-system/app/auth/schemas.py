"""
Pydantic schemas for authentication.
"""
from datetime import datetime
from typing import Optional
from uuid import UUID
from enum import Enum

from pydantic import BaseModel, EmailStr, Field
from typing import List


class UserRole(str, Enum):
    """User role enumeration."""
    admin = "admin"
    recruiter = "recruiter"
    viewer = "viewer"


class UserCreate(BaseModel):
    """Schema for user registration."""
    email: EmailStr
    password: str = Field(..., min_length=8, description="Password must be at least 8 characters")
    name: str = Field(..., min_length=2, max_length=255)
    role: UserRole = UserRole.viewer


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
    is_active: bool
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


class TokenPayload(BaseModel):
    """Schema for JWT token payload."""
    sub: str
    exp: datetime
    type: str
    role: Optional[str] = None


class UserUpdate(BaseModel):
    """Schema for updating a user."""
    email: Optional[EmailStr] = None
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None


class UserManagementCreate(BaseModel):
    """Schema for creating users from admin panel."""
    email: EmailStr
    name: str = Field(..., min_length=2, max_length=255)
    role: UserRole = UserRole.viewer
    company_id: Optional[str] = "demo_company"
    permissions: List[str] = Field(default_factory=list)
    password: Optional[str] = Field(None, description="Password for the user. If not provided, a default will be used.")


class UserManagementResponse(BaseModel):
    """Schema for user management response (includes company_id)."""
    id: UUID
    email: str
    name: str
    role: UserRole
    company_id: Optional[str] = None
    is_active: bool
    permissions: List[str] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserManagementUpdate(BaseModel):
    """Schema for updating a user from admin panel."""
    email: Optional[EmailStr] = None
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    company_id: Optional[str] = None
    permissions: Optional[List[str]] = None


class PasswordResetRequest(BaseModel):
    """Schema for password reset request."""
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Schema for password reset confirmation."""
    token: str
    new_password: str = Field(..., min_length=8, description="New password must be at least 8 characters")


class EmailVerificationRequest(BaseModel):
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
    company_id: Optional[str] = None
    valid: bool = True
    message: Optional[str] = None
