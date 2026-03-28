"""
Pydantic schemas for Global Policies API.

Includes schemas for:
- Policy CRUD operations
- Policy audit trail
- Category listings
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Any
from datetime import datetime
from enum import Enum


class PolicyCategoryEnum(str, Enum):
    """Categories for global policies."""
    DATA_RETENTION = "data_retention"
    AI_LIMITS = "ai_limits"
    SECURITY = "security"
    COMPLIANCE = "compliance"


class PolicyValueTypeEnum(str, Enum):
    """Value types for policies."""
    BOOLEAN = "boolean"
    NUMBER = "number"
    STRING = "string"
    SELECT = "select"


class PolicyResponse(BaseModel):
    """Response schema for a global policy."""
    id: str
    name: str
    description: Optional[str] = None
    category: str
    value_type: str
    current_value: str
    unit: Optional[str] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    options: Optional[List[str]] = None
    is_active: bool = True
    updated_at: Optional[datetime] = None
    updated_by: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PolicyWithHistoryResponse(PolicyResponse):
    """Response schema for a policy with its audit history."""
    audit_history: List["PolicyAuditLogResponse"] = []


class PolicyListResponse(BaseModel):
    """Paginated list of policies."""
    policies: List[PolicyResponse]
    total: int
    limit: int
    offset: int


class PolicyUpdate(BaseModel):
    """Schema for updating a policy value."""
    current_value: str = Field(..., description="New value for the policy")
    change_reason: Optional[str] = Field(None, description="Reason for the change")


class PolicyAuditLogResponse(BaseModel):
    """Response schema for policy audit log entry."""
    id: str
    policy_id: str
    previous_value: Optional[str] = None
    new_value: str
    changed_by: Optional[str] = None
    changed_at: Optional[datetime] = None
    change_reason: Optional[str] = None

    class Config:
        from_attributes = True


class PolicyAuditLogListResponse(BaseModel):
    """Paginated list of audit log entries."""
    logs: List[PolicyAuditLogResponse]
    total: int
    limit: int
    offset: int


class CategoryCount(BaseModel):
    """Count of policies per category."""
    category: str
    count: int
    active_count: int


class CategoryListResponse(BaseModel):
    """Response schema for category listing with counts."""
    categories: List[CategoryCount]
    total_policies: int


class SeedPoliciesResponse(BaseModel):
    """Response schema for seeding policies."""
    created: int
    skipped: int
    message: str


PolicyWithHistoryResponse.model_rebuild()
