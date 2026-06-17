"""
Pydantic schemas for SoD (Segregation of Duties) Matrix API.

Includes schemas for:
- Role management
- Conflict definitions
- Violation tracking
- SoD matrix and statistics
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from enum import Enum


class RoleTypeEnum(str, Enum):
    """Types of roles."""
    SYSTEM = "system"
    BUSINESS = "business"
    TECHNICAL = "technical"
    ADMINISTRATIVE = "administrative"


class ConflictSeverityEnum(str, Enum):
    """Severity of SoD conflicts."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ConflictStatusEnum(str, Enum):
    """Status of conflicts."""
    ACTIVE = "active"
    EXCEPTION_APPROVED = "exception_approved"
    MITIGATED = "mitigated"
    INACTIVE = "inactive"


class ViolationStatusEnum(str, Enum):
    """Status of violations."""
    DETECTED = "detected"
    UNDER_REVIEW = "under_review"
    RESOLVED = "resolved"
    ACCEPTED = "accepted"


class SoDRoleResponse(BaseModel):
    """Response schema for SoD role."""
    id: str
    company_id: str
    name: str
    description: Optional[str] = None
    role_type: str
    permissions: List[str] = []
    is_sensitive: bool = False
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SoDRoleListResponse(BaseModel):
    """Paginated list of roles."""
    roles: List[SoDRoleResponse]
    total: int
    limit: int
    offset: int


class SoDRoleCreate(BaseModel):
    """Schema for creating a role."""
    name: str = Field(..., min_length=2, max_length=100, description="Role name")
    description: Optional[str] = Field(None, description="Role description")
    role_type: RoleTypeEnum = Field(default=RoleTypeEnum.BUSINESS, description="Role type")
    permissions: List[str] = Field(default=[], description="Role permissions")
    is_sensitive: bool = Field(default=False, description="Whether role is sensitive")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Approver",
                "description": "Can approve financial transactions",
                "role_type": "business",
                "permissions": ["approve_payment", "view_transactions"],
                "is_sensitive": True
            }
        }


class SoDRoleUpdate(BaseModel):
    """Schema for updating a role."""
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    description: Optional[str] = None
    role_type: Optional[RoleTypeEnum] = None
    permissions: Optional[List[str]] = None
    is_sensitive: Optional[bool] = None
    is_active: Optional[bool] = None


class SoDConflictResponse(BaseModel):
    """Response schema for SoD conflict."""
    id: str
    company_id: str
    role_a_id: str
    role_a_name: Optional[str] = None
    role_b_id: str
    role_b_name: Optional[str] = None
    conflict_description: str
    severity: str
    status: str
    mitigation_control: Optional[str] = None
    exception_approved_by: Optional[str] = None
    exception_approved_at: Optional[datetime] = None
    exception_expires_at: Optional[date] = None
    exception_reason: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SoDConflictListResponse(BaseModel):
    """Paginated list of conflicts."""
    conflicts: List[SoDConflictResponse]
    total: int
    limit: int
    offset: int


class SoDConflictCreate(BaseModel):
    """Schema for creating a conflict."""
    role_a_id: str = Field(..., description="First role ID")
    role_b_id: str = Field(..., description="Second role ID")
    conflict_description: str = Field(..., min_length=10, description="Description of the conflict")
    severity: ConflictSeverityEnum = Field(default=ConflictSeverityEnum.MEDIUM, description="Conflict severity")
    mitigation_control: Optional[str] = Field(None, description="Mitigation control if any")

    class Config:
        json_schema_extra = {
            "example": {
                "role_a_id": "550e8400-e29b-41d4-a716-446655440000",
                "role_b_id": "550e8400-e29b-41d4-a716-446655440001",
                "conflict_description": "User cannot both create and approve payment requests",
                "severity": "high",
                "mitigation_control": "Dual approval required for amounts over R$10.000"
            }
        }


class SoDExceptionApproval(BaseModel):
    """Schema for approving an exception."""
    approved_by: str = Field(..., description="Approver ID")
    reason: str = Field(..., min_length=10, description="Reason for exception")
    expires_at: Optional[date] = Field(None, description="Exception expiration date")

    class Config:
        json_schema_extra = {
            "example": {
                "approved_by": "770e8400-e29b-41d4-a716-446655440002",
                "reason": "Temporary assignment during vacation period with additional monitoring",
                "expires_at": "2024-03-31"
            }
        }


class SoDViolationResponse(BaseModel):
    """Response schema for SoD violation."""
    id: str
    company_id: str
    conflict_id: str
    user_id: str
    user_name: Optional[str] = None
    user_email: Optional[str] = None
    detected_at: datetime
    status: str
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None
    resolution_notes: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SoDViolationListResponse(BaseModel):
    """Paginated list of violations."""
    violations: List[SoDViolationResponse]
    total: int
    limit: int
    offset: int


class SoDViolationResolve(BaseModel):
    """Schema for resolving a violation."""
    resolved_by: str = Field(..., description="Resolver ID")
    resolution_notes: str = Field(..., min_length=10, description="Resolution notes")

    class Config:
        json_schema_extra = {
            "example": {
                "resolved_by": "770e8400-e29b-41d4-a716-446655440002",
                "resolution_notes": "User's secondary role was removed to eliminate the conflict"
            }
        }


class SoDMatrixCell(BaseModel):
    """Cell in SoD matrix."""
    role_a_id: str
    role_a_name: str
    role_b_id: str
    role_b_name: str
    has_conflict: bool
    conflict_id: Optional[str] = None
    severity: Optional[str] = None
    status: Optional[str] = None


class SoDMatrixResponse(BaseModel):
    """SoD matrix response."""
    roles: List[SoDRoleResponse]
    conflicts: List[SoDMatrixCell]
    total_conflicts: int


class SoDStats(BaseModel):
    """SoD statistics."""
    total_roles: int = 0
    sensitive_roles: int = 0
    total_conflicts: int = 0
    active_conflicts: int = 0
    approved_exceptions: int = 0
    total_violations: int = 0
    open_violations: int = 0
    resolved_violations: int = 0
    by_severity: Dict[str, int] = {}
