"""Pydantic schemas for agent approval workflow."""
from typing import Literal, Optional

from pydantic import BaseModel, Field
from app.shared.types import WeDoBaseModel


class RequestApprovalRequest(WeDoBaseModel):
    """Empty body — agent_id comes from URL path."""
    pass


class ReviewApprovalRequest(WeDoBaseModel):
    action: Literal["approve", "reject"]
    notes: Optional[str] = Field(None, max_length=2000)


class ApprovalResponse(BaseModel):
    id: str
    agent_id: str
    company_id: str
    requested_by: str
    reviewed_by: Optional[str] = None
    status: str
    review_notes: Optional[str] = None
    requested_at: Optional[str] = None
    reviewed_at: Optional[str] = None
    # Enriched fields
    agent_name: Optional[str] = None


class ApprovalListResponse(BaseModel):
    approvals: list[ApprovalResponse]
    total: int
