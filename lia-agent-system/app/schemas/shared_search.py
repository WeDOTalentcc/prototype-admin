"""
Pydantic schemas for Shared Searches feature.
"""
from datetime import datetime
from enum import Enum, StrEnum
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field
from app.shared.types import WeDoBaseModel


class ShareType(StrEnum):
    """Type of shared content."""
    search = "search"
    list = "list"


class ShareStatus(StrEnum):
    """Status of a shared search."""
    active = "active"
    expired = "expired"
    revoked = "revoked"


class ShareChannel(StrEnum):
    """Channel used for sharing."""
    email = "email"
    whatsapp = "whatsapp"
    both = "both"


class FeedbackDecision(StrEnum):
    """Decision made by reviewer on a candidate."""
    approved = "approved"
    maybe = "maybe"
    rejected = "rejected"


class RecipientInput(WeDoBaseModel):
    """Input schema for adding a recipient to a shared search."""
    email: EmailStr
    name: str | None = None
    phone: str | None = Field(None, description="Optional phone number for WhatsApp channel")
    role: str = Field(default="hiring_manager", description="Role of the recipient")


class CreateSharedSearchRequest(WeDoBaseModel):
    """Request schema for creating a new shared search."""
    share_type: ShareType
    title: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    source_query: str | None = Field(None, description="Original search query if share_type=search")
    source_list_id: str | None = Field(None, description="Source list ID if share_type=list")
    candidate_ids: list[str] = Field(..., min_length=1, description="List of candidate IDs to share")
    recipients: list[RecipientInput] = Field(..., min_length=1, description="List of recipients")
    expires_at: datetime | None = Field(None, description="Expiration date for the shared search")
    message: str | None = Field(None, description="Optional message to include in the invitation")
    subject: str | None = Field(None, max_length=500, description="Custom email subject override")
    channel: ShareChannel = Field(ShareChannel.email, description="Communication channel: email, whatsapp, or both")
    can_comment: bool = Field(True, description="Whether recipients can leave comments")
    can_rate: bool = Field(True, description="Whether recipients can rate/decide on candidates")


class SubmitFeedbackRequest(WeDoBaseModel):
    """Request schema for submitting feedback on a candidate."""
    candidate_id: UUID
    decision: FeedbackDecision
    rating: int | None = Field(None, ge=1, le=5, description="Rating from 1 to 5")
    comment: str | None = None


class RequestOTPRequest(WeDoBaseModel):
    """Request schema for requesting an OTP."""
    email: EmailStr


class VerifyOTPRequest(WeDoBaseModel):
    """Request schema for verifying an OTP."""
    email: EmailStr
    otp: str = Field(..., min_length=6, max_length=6)


class FeedbackSummary(BaseModel):
    """Summary of feedback counts."""
    approved: int = 0
    maybe: int = 0
    rejected: int = 0
    pending: int = 0


class RecipientSummary(BaseModel):
    """Summary of a recipient's activity."""
    email: str
    name: str | None = None
    role: str
    first_accessed_at: datetime | None = None
    last_accessed_at: datetime | None = None
    total_views: int = 0
    feedback_count: int = 0

    class Config:
        from_attributes = True


class FeedbackResponse(BaseModel):
    """Response schema for feedback on a candidate."""
    id: UUID
    candidate_id: UUID
    reviewer_email: str
    decision: FeedbackDecision
    rating: int | None = None
    comment: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class CandidateSnapshot(BaseModel):
    """Snapshot of candidate data for shared searches."""
    id: UUID
    name: str
    title: str | None = None
    company: str | None = None
    location: str | None = None
    experience_years: int | None = None
    skills: list[str] = Field(default_factory=list)
    wsi_score: float | None = None
    linkedin_url: str | None = None
    resume_url: str | None = None
    feedback: FeedbackResponse | None = None

    class Config:
        from_attributes = True


class SharedSearchResponse(BaseModel):
    """Response schema for a shared search."""
    id: UUID
    company_id: UUID
    share_type: ShareType
    title: str
    description: str | None = None
    status: ShareStatus
    expires_at: datetime | None = None
    created_at: datetime
    candidate_count: int = 0
    feedback_summary: FeedbackSummary = Field(default_factory=FeedbackSummary)
    recipients: list[RecipientSummary] = Field(default_factory=list)

    class Config:
        from_attributes = True


class SharedSearchDetailResponse(SharedSearchResponse):
    """Detailed response schema for a shared search with candidates and feedbacks."""
    candidates: list[CandidateSnapshot] = Field(default_factory=list)
    feedbacks: list[FeedbackResponse] = Field(default_factory=list)


class PublicSharedSearchResponse(BaseModel):
    """Response schema for public shared search page (before auth)."""
    title: str
    description: str | None = None
    expires_at: datetime | None = None
    shared_by_name: str | None = None
    shared_by_email: str | None = None
    company_name: str | None = None
    company_logo_url: str | None = None
    candidate_count: int = 0
    candidates: list[CandidateSnapshot] = Field(default_factory=list, description="Limited preview without auth")
    can_comment: bool = True
    can_rate: bool = True

    class Config:
        from_attributes = True


class OTPResponse(BaseModel):
    """Response schema for OTP operations."""
    success: bool
    message: str


class SessionResponse(BaseModel):
    """Response schema for session after OTP verification."""
    access_token: str
    expires_at: datetime
