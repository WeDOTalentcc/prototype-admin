"""
Pydantic schemas for SOX-Compliant Audit Logs API.
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class ActionCategoryEnum(str, Enum):
    """Categories of auditable actions."""
    AUTHENTICATION = "authentication"
    DATA_ACCESS = "data_access"
    CONFIGURATION = "configuration"
    AI_DECISION = "ai_decision"
    FINANCIAL = "financial"
    USER_MANAGEMENT = "user_management"
    SYSTEM = "system"


class AuditStatusEnum(str, Enum):
    """Status of audited actions."""
    SUCCESS = "success"
    FAILED = "failed"
    PENDING = "pending"
    PARTIAL = "partial"


class AuditLogResponse(BaseModel):
    """Response schema for a single audit log entry."""
    id: str
    timestamp: Optional[datetime] = None
    user_id: Optional[str] = None
    user_email: Optional[str] = None
    client_id: Optional[str] = None
    client_name: Optional[str] = None
    action: str
    action_category: str
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    status: str
    details: Dict[str, Any] = {}
    retention_years: int = 7
    retention_until: Optional[datetime] = None
    request_id: Optional[str] = None
    session_id: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AuditLogListResponse(BaseModel):
    """Paginated list of audit logs."""
    logs: List[AuditLogResponse]
    total: int
    limit: int
    offset: int
    has_more: bool = False


class AuditLogCreate(BaseModel):
    """Schema for creating a new audit log entry."""
    user_id: Optional[str] = Field(None, description="User ID performing the action")
    user_email: Optional[str] = Field(None, description="User email")
    client_id: Optional[str] = Field(None, description="Client/Company ID")
    client_name: Optional[str] = Field(None, description="Client/Company name")
    action: str = Field(..., description="Action performed", max_length=255)
    action_category: ActionCategoryEnum = Field(..., description="Category of the action")
    resource_type: Optional[str] = Field(None, description="Type of resource affected")
    resource_id: Optional[str] = Field(None, description="ID of resource affected")
    ip_address: Optional[str] = Field(None, description="Client IP address")
    user_agent: Optional[str] = Field(None, description="Client user agent")
    status: AuditStatusEnum = Field(AuditStatusEnum.SUCCESS, description="Action status")
    details: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional details")
    request_id: Optional[str] = Field(None, description="Request correlation ID")
    session_id: Optional[str] = Field(None, description="Session ID")

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "550e8400-e29b-41d4-a716-446655440000",
                "user_email": "user@example.com",
                "client_id": "demo_company",
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
    date_from: Optional[datetime] = Field(None, description="Start date for filtering")
    date_to: Optional[datetime] = Field(None, description="End date for filtering")
    client_id: Optional[str] = Field(None, description="Filter by client ID")
    user_id: Optional[str] = Field(None, description="Filter by user ID")
    action_category: Optional[ActionCategoryEnum] = Field(None, description="Filter by action category")
    status: Optional[AuditStatusEnum] = Field(None, description="Filter by status")
    action: Optional[str] = Field(None, description="Filter by action name (partial match)")
    resource_type: Optional[str] = Field(None, description="Filter by resource type")


class AuditStatsResponse(BaseModel):
    """Aggregated statistics for audit logs."""
    total_logs: int
    logs_by_category: Dict[str, int] = {}
    logs_by_status: Dict[str, int] = {}
    failed_actions_count: int
    ai_decisions_count: int
    unique_users: int
    unique_clients: int
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None
    top_actions: List[Dict[str, Any]] = []


class AuditRetentionPolicyResponse(BaseModel):
    """Response schema for retention policy."""
    id: str
    category: str
    retention_months: int
    description: Optional[str] = None
    is_sox_required: bool = False
    legal_basis: Optional[str] = None
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AuditRetentionPolicyListResponse(BaseModel):
    """List of retention policies."""
    policies: List[AuditRetentionPolicyResponse]
    total: int


class AuditRetentionPolicyCreate(BaseModel):
    """Schema for creating a retention policy."""
    category: str = Field(..., description="Audit category", max_length=50)
    retention_months: int = Field(..., ge=1, le=1200, description="Retention period in months")
    description: Optional[str] = Field(None, description="Policy description")
    is_sox_required: bool = Field(False, description="Whether SOX compliance requires this retention")
    legal_basis: Optional[str] = Field(None, description="Legal basis for retention")

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


class AuditRetentionPolicyUpdate(BaseModel):
    """Schema for updating a retention policy."""
    retention_months: Optional[int] = Field(None, ge=1, le=1200, description="Retention period in months")
    description: Optional[str] = Field(None, description="Policy description")
    is_sox_required: Optional[bool] = Field(None, description="Whether SOX compliance requires this retention")
    legal_basis: Optional[str] = Field(None, description="Legal basis for retention")
    is_active: Optional[bool] = Field(None, description="Whether policy is active")


class AuditExportRequest(BaseModel):
    """Request schema for exporting audit logs."""
    date_from: Optional[datetime] = Field(None, description="Start date for export")
    date_to: Optional[datetime] = Field(None, description="End date for export")
    client_id: Optional[str] = Field(None, description="Filter by client ID")
    action_category: Optional[ActionCategoryEnum] = Field(None, description="Filter by category")
    format: str = Field("csv", description="Export format: csv or json")


class AuditExportResponse(BaseModel):
    """Response schema for export request."""
    export_id: str
    status: str
    file_url: Optional[str] = None
    record_count: int
    created_at: datetime


class SeedRetentionPoliciesResponse(BaseModel):
    """Response for seeding default retention policies."""
    created_count: int
    skipped_count: int
    message: str
