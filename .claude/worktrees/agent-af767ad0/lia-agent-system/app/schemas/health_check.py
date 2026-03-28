"""
Pydantic schemas for Compliance Health Check API.
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from enum import Enum


class ChecklistItem(BaseModel):
    """A single checklist item within a requirement."""
    text: str = Field(..., description="Description of the checklist item")
    completed: bool = Field(False, description="Whether this item is completed")


class ComplianceFrameworkEnum(str, Enum):
    """Supported compliance frameworks."""
    SOX = "SOX"
    SOC2 = "SOC2"
    ISO27001 = "ISO27001"
    LGPD = "LGPD"
    BCB498 = "BCB498"
    EUAI = "EUAI"
    NYC144 = "NYC144"


class HealthCheckStatusEnum(str, Enum):
    """Status options for health check items."""
    IMPLEMENTED = "implemented"
    PARTIAL = "partial"
    PENDING = "pending"
    NOT_APPLICABLE = "not_applicable"
    NOT_CHECKED = "not_checked"


class ReviewFrequencyEnum(str, Enum):
    """Review frequency options."""
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUAL = "annual"


class PriorityEnum(str, Enum):
    """Priority levels for health check items."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class HealthCheckItemResponse(BaseModel):
    """Response schema for a single health check item."""
    id: str
    framework: str
    category: str
    req_id: str
    requirement: str
    evidence: Optional[str] = None
    evidence_details: Optional[str] = None
    checklist_items: Optional[List[ChecklistItem]] = []
    gap_observation: Optional[str] = None
    status: str
    last_checked_at: Optional[datetime] = None
    checked_by_id: Optional[str] = None
    checked_by_name: Optional[str] = None
    next_review_date: Optional[datetime] = None
    review_frequency: str
    check_comments: Optional[str] = None
    priority: str
    reference_url: Optional[str] = None
    reference_label: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class HealthCheckItemListResponse(BaseModel):
    """Paginated list of health check items."""
    items: List[HealthCheckItemResponse]
    total: int
    limit: int
    offset: int
    has_more: bool = False


class HealthCheckItemCreate(BaseModel):
    """Schema for creating a new health check item."""
    framework: ComplianceFrameworkEnum = Field(..., description="Compliance framework")
    category: str = Field(..., description="Category within the framework", max_length=100)
    req_id: str = Field(..., description="Unique requirement ID", max_length=50)
    requirement: str = Field(..., description="Requirement description", max_length=500)
    evidence: Optional[str] = Field(None, description="Expected evidence", max_length=500)
    evidence_details: Optional[str] = Field(None, description="Detailed evidence description")
    checklist_items: Optional[List[ChecklistItem]] = Field(None, description="List of sub-items to check")
    gap_observation: Optional[str] = Field(None, description="Gap observation notes")
    status: HealthCheckStatusEnum = Field(HealthCheckStatusEnum.NOT_CHECKED, description="Current status")
    priority: PriorityEnum = Field(PriorityEnum.MEDIUM, description="Priority level")
    review_frequency: ReviewFrequencyEnum = Field(ReviewFrequencyEnum.MONTHLY, description="Review frequency")

    class Config:
        json_schema_extra = {
            "example": {
                "framework": "SOX",
                "category": "ITGCs",
                "req_id": "SOX-ITGC-01",
                "requirement": "Controles de acesso lógico implementados",
                "evidence": "Matriz de acessos, logs de autenticação",
                "priority": "critical",
                "review_frequency": "monthly"
            }
        }


class HealthCheckItemUpdate(BaseModel):
    """Schema for updating a health check item."""
    requirement: Optional[str] = Field(None, description="Requirement description", max_length=500)
    evidence: Optional[str] = Field(None, description="Expected evidence", max_length=500)
    gap_observation: Optional[str] = Field(None, description="Gap observation notes")
    priority: Optional[PriorityEnum] = Field(None, description="Priority level")
    review_frequency: Optional[ReviewFrequencyEnum] = Field(None, description="Review frequency")


class HealthCheckVerifyRequest(BaseModel):
    """Schema for marking an item as verified."""
    checked_by_id: Optional[str] = Field(None, description="ID of the user performing verification")
    checked_by_name: Optional[str] = Field(None, description="Name of the user performing verification")
    check_comments: Optional[str] = Field(None, description="Comments about the verification")
    next_review_date: Optional[datetime] = Field(None, description="Next review date")

    class Config:
        json_schema_extra = {
            "example": {
                "checked_by_id": "550e8400-e29b-41d4-a716-446655440000",
                "checked_by_name": "João Silva",
                "check_comments": "Verificado conforme evidências apresentadas",
                "next_review_date": "2025-03-20T00:00:00Z"
            }
        }


class HealthCheckStatusUpdateRequest(BaseModel):
    """Schema for updating item status."""
    status: HealthCheckStatusEnum = Field(..., description="New status")
    changed_by_id: Optional[str] = Field(None, description="ID of user making the change")
    changed_by_name: Optional[str] = Field(None, description="Name of user making the change")
    comments: Optional[str] = Field(None, description="Comments about the status change")
    gap_observation: Optional[str] = Field(None, description="Gap observation if status is partial or pending")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "implemented",
                "changed_by_id": "550e8400-e29b-41d4-a716-446655440000",
                "changed_by_name": "Maria Santos",
                "comments": "Controle implementado após auditoria"
            }
        }


class HealthCheckHistoryResponse(BaseModel):
    """Response schema for a history entry."""
    id: str
    item_id: str
    old_status: Optional[str] = None
    new_status: str
    changed_by_id: Optional[str] = None
    changed_by_name: Optional[str] = None
    comments: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class HealthCheckHistoryListResponse(BaseModel):
    """List of history entries."""
    history: List[HealthCheckHistoryResponse]
    total: int


class FrameworkSummary(BaseModel):
    """Summary statistics for a single framework."""
    framework: str
    total: int
    implemented: int
    partial: int
    pending: int
    not_applicable: int
    not_checked: int
    compliance_percentage: float
    critical_pending: int
    overdue_reviews: int


class HealthCheckSummaryResponse(BaseModel):
    """Overall summary of health check status."""
    total_items: int
    by_framework: List[FrameworkSummary]
    overall_compliance_percentage: float
    total_critical_pending: int
    total_overdue_reviews: int
    last_updated: Optional[datetime] = None


class SeedHealthCheckResponse(BaseModel):
    """Response for seeding default health check items."""
    created_count: int
    skipped_count: int
    message: str


class HealthCheckExportRequest(BaseModel):
    """Request schema for exporting health check data."""
    framework: Optional[ComplianceFrameworkEnum] = Field(None, description="Filter by framework")
    status: Optional[HealthCheckStatusEnum] = Field(None, description="Filter by status")
    format: str = Field("csv", description="Export format: csv or json")


class HealthCheckExportResponse(BaseModel):
    """Response for export request."""
    format: str
    record_count: int
    generated_at: datetime
