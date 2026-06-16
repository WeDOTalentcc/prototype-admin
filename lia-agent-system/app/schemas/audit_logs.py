"""
Pydantic schemas for SOX-Compliant Audit Logs API.
"""
from datetime import datetime
from enum import Enum, StrEnum
from typing import Any

from pydantic import BaseModel, Field
from app.shared.types import WeDoBaseModel


class ActionCategoryEnum(StrEnum):
    """Categories of auditable actions."""
    AUTHENTICATION = "authentication"
    DATA_ACCESS = "data_access"
    CONFIGURATION = "configuration"
    AI_DECISION = "ai_decision"
    FINANCIAL = "financial"
    USER_MANAGEMENT = "user_management"
    SYSTEM = "system"


class AuditStatusEnum(StrEnum):
    """Status of audited actions."""
    SUCCESS = "success"
    FAILED = "failed"
    PENDING = "pending"
    PARTIAL = "partial"


class AuditLogResponse(BaseModel):
    """Response schema for a single audit log entry."""
    id: str
    timestamp: datetime | None = None
    user_id: str | None = None
    user_email: str | None = None
    client_id: str | None = None
    client_name: str | None = None
    action: str
    action_category: str
    resource_type: str | None = None
    resource_id: str | None = None
    ip_address: str | None = None
    user_agent: str | None = None
    status: str
    details: dict[str, Any] = {}
    retention_years: int = 7
    retention_until: datetime | None = None
    request_id: str | None = None
    session_id: str | None = None
    created_at: datetime | None = None

    class Config:
        from_attributes = True


class AuditLogListResponse(BaseModel):
    """Paginated list of audit logs."""
    logs: list[AuditLogResponse]
    total: int
    limit: int
    offset: int
    has_more: bool = False


class AuditLogCreate(WeDoBaseModel):
    """Schema for creating a new audit log entry."""
    user_id: str | None = Field(None, description="User ID performing the action")
    user_email: str | None = Field(None, description="User email")
    client_id: str | None = Field(None, description="Client/Company ID")
    client_name: str | None = Field(None, description="Client/Company name")
    action: str = Field(..., description="Action performed", max_length=255)
    action_category: ActionCategoryEnum = Field(..., description="Category of the action")
    resource_type: str | None = Field(None, description="Type of resource affected")
    resource_id: str | None = Field(None, description="ID of resource affected")
    ip_address: str | None = Field(None, description="Client IP address")
    user_agent: str | None = Field(None, description="Client user agent")
    status: AuditStatusEnum = Field(AuditStatusEnum.SUCCESS, description="Action status")
    details: dict[str, Any] | None = Field(default_factory=dict, description="Additional details")
    request_id: str | None = Field(None, description="Request correlation ID")
    session_id: str | None = Field(None, description="Session ID")

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "550e8400-e29b-41d4-a716-446655440000",
                "user_email": "user@example.com",
                "client_id": "example_company",
                "client_name": "Demo Company",
                "action": "user.login",
                "action_category": "authentication",
                "resource_type": "user",
                "resource_id": "550e8400-e29b-41d4-a716-446655440000",
                "ip_address": "192.168.1.1",
                "status": "success",
                "details": {"method": "password", "mfa_used": False}
            }
        }


class AuditLogFilter(BaseModel):
    """Filter options for querying audit logs."""
    date_from: datetime | None = Field(None, description="Start date for filtering")
    date_to: datetime | None = Field(None, description="End date for filtering")
    client_id: str | None = Field(None, description="Filter by client ID")
    user_id: str | None = Field(None, description="Filter by user ID")
    action_category: ActionCategoryEnum | None = Field(None, description="Filter by action category")
    status: AuditStatusEnum | None = Field(None, description="Filter by status")
    action: str | None = Field(None, description="Filter by action name (partial match)")
    resource_type: str | None = Field(None, description="Filter by resource type")


class AuditStatsResponse(BaseModel):
    """Aggregated statistics for audit logs."""
    total_logs: int
    logs_by_category: dict[str, int] = {}
    logs_by_status: dict[str, int] = {}
    failed_actions_count: int
    ai_decisions_count: int
    unique_users: int
    unique_clients: int
    period_start: datetime | None = None
    period_end: datetime | None = None
    top_actions: list[dict[str, Any]] = []
    # WT-2022 P5.1: novos campos canonical (eram esperados pelo FE mas não populados)
    recent_24h: int = 0
    by_severity: dict[str, int] = {}  # vazio até model SOXAuditLog ter severity column (separate migration)


class AuditRetentionPolicyResponse(BaseModel):
    """Response schema for retention policy."""
    id: str
    category: str
    retention_months: int
    description: str | None = None
    is_sox_required: bool = False
    legal_basis: str | None = None
    is_active: bool = True
    created_at: datetime | None = None
    updated_at: datetime | None = None

    class Config:
        from_attributes = True


class AuditRetentionPolicyListResponse(BaseModel):
    """List of retention policies."""
    policies: list[AuditRetentionPolicyResponse]
    total: int


class AuditRetentionPolicyCreate(WeDoBaseModel):
    """Schema for creating a retention policy."""
    category: str = Field(..., description="Audit category", max_length=50)
    retention_months: int = Field(..., ge=1, le=1200, description="Retention period in months")
    description: str | None = Field(None, description="Policy description")
    is_sox_required: bool = Field(False, description="Whether SOX compliance requires this retention")
    legal_basis: str | None = Field(None, description="Legal basis for retention")

    class Config:
        json_schema_extra = {
            "example": {
                "category": "financial",
                "retention_months": 84,
                "description": "Financial records retention",
                "is_sox_required": True,
                "legal_basis": "SOX Section 802"
            }
        }


class AuditRetentionPolicyUpdate(WeDoBaseModel):
    """Schema for updating a retention policy."""
    retention_months: int | None = Field(None, ge=1, le=1200, description="Retention period in months")
    description: str | None = Field(None, description="Policy description")
    is_sox_required: bool | None = Field(None, description="Whether SOX compliance requires this retention")
    legal_basis: str | None = Field(None, description="Legal basis for retention")
    is_active: bool | None = Field(None, description="Whether policy is active")


class AuditExportRequest(WeDoBaseModel):
    """Request schema for exporting audit logs."""
    date_from: datetime | None = Field(None, description="Start date for export")
    date_to: datetime | None = Field(None, description="End date for export")
    client_id: str | None = Field(None, description="Filter by client ID")
    action_category: ActionCategoryEnum | None = Field(None, description="Filter by category")
    format: str = Field("csv", description="Export format: csv or json")


class AuditExportResponse(BaseModel):
    """Response schema for export request."""
    export_id: str
    status: str
    file_url: str | None = None
    record_count: int
    created_at: datetime


class SeedRetentionPoliciesResponse(BaseModel):
    """Response for seeding default retention policies."""
    created_count: int
    skipped_count: int
    message: str
