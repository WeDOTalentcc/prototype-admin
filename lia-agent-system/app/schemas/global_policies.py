"""
Pydantic schemas for Global Policies API.

Includes schemas for:
- Policy CRUD operations
- Policy audit trail
- Category listings
"""
from datetime import datetime
from enum import Enum, StrEnum

from pydantic import BaseModel, Field
from app.shared.types import WeDoBaseModel


class PolicyCategoryEnum(StrEnum):
    """Categories for global policies."""
    DATA_RETENTION = "data_retention"
    AI_LIMITS = "ai_limits"
    SECURITY = "security"
    COMPLIANCE = "compliance"


class PolicyValueTypeEnum(StrEnum):
    """Value types for policies."""
    BOOLEAN = "boolean"
    NUMBER = "number"
    STRING = "string"
    SELECT = "select"


class PolicyResponse(BaseModel):
    """Response schema for a global policy."""
    id: str
    name: str
    description: str | None = None
    category: str
    value_type: str
    current_value: str
    unit: str | None = None
    min_value: float | None = None
    max_value: float | None = None
    options: list[str] | None = None
    is_active: bool = True
    updated_at: datetime | None = None
    updated_by: str | None = None
    created_at: datetime | None = None

    class Config:
        from_attributes = True


class PolicyWithHistoryResponse(PolicyResponse):
    """Response schema for a policy with its audit history."""
    audit_history: list["PolicyAuditLogResponse"] = []


class PolicyListResponse(BaseModel):
    """Paginated list of policies."""
    policies: list[PolicyResponse]
    total: int
    limit: int
    offset: int


class PolicyUpdate(WeDoBaseModel):
    """Schema for updating a policy value."""
    current_value: str = Field(..., description="New value for the policy")
    change_reason: str | None = Field(None, description="Reason for the change")


class PolicyAuditLogResponse(BaseModel):
    """Response schema for policy audit log entry."""
    id: str
    policy_id: str
    previous_value: str | None = None
    new_value: str
    changed_by: str | None = None
    changed_at: datetime | None = None
    change_reason: str | None = None

    class Config:
        from_attributes = True


class PolicyAuditLogListResponse(BaseModel):
    """Paginated list of audit log entries."""
    logs: list[PolicyAuditLogResponse]
    total: int
    limit: int
    offset: int


class PolicyCategoryCount(BaseModel):
    """Count of policies per category."""
    category: str
    count: int
    active_count: int


class CategoryListResponse(BaseModel):
    """Response schema for category listing with counts."""
    categories: list[PolicyCategoryCount]
    total_policies: int


class SeedPoliciesResponse(BaseModel):
    """Response schema for seeding policies."""
    created: int
    skipped: int
    message: str


PolicyWithHistoryResponse.model_rebuild()
