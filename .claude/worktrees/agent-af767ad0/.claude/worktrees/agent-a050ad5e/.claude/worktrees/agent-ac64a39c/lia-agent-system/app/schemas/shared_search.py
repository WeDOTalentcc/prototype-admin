"""
Pydantic schemas for Shared Searches feature.
"""
from datetime import datetime
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field, EmailStr, field_validator
from uuid import UUID


class ShareType(str, Enum):
    """Type of shared content."""
    search = "search"
    list = "list"


class ShareStatus(str, Enum):
    """Status of a shared search."""
    active = "active"
    expired = "expired"
    revoked = "revoked"


class ShareChannel(str, Enum):
    """Channel used for sharing."""
    email = "email"
    whatsapp = "whatsapp"
    both = "both"


class FeedbackDecision(str, Enum):
    """Decision made by reviewer on a candidate."""
    approved = "approved"
    maybe = "maybe"
    rejected = "rejected"


class RecipientInput(BaseModel):
    """Input schema for adding a recipient to a shared search."""
    email: EmailStr
    name: Optional[str] = None
    phone: Optional[str] = Field(None, description="Optional phone number for WhatsApp channel")
    role: str = Field(default="hiring_manager", description="Role of the recipient")


class CreateSharedSearchRequest(BaseModel):
    """Request schema for creating a new shared search."""
    share_type: ShareType
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    source_query: Optional[str] = Field(None, description="Original search query if share_type=search")
    source_list_id: Optional[str] = Field(None, description="Source list ID if share_type=list")
    candidate_ids: List[str] = Field(..., min_length=1, description="List of candidate IDs to share")
    recipients: List[RecipientInput] = Field(..., min_length=1, description="List of recipients")
    expires_at: Optional[datetime] = Field(None, description="Expiration date for the shared search")
    message: Optional[str] = Field(None, description="Optional message to include in the invitation")
    subject: Optional[str] = Field(None, max_length=500, description="Custom email subject override")
    channel: ShareChannel = Field(ShareChannel.email, description="Communication channel: email, whatsapp, or both")
    can_comment: bool = Field(True, description="Whether recipients can leave comments")
    can_rate: bool = Field(True, description="Whether recipients can rate/decide on candidates")


class SubmitFeedbackRequest(BaseModel):
    """Request schema for submitting feedback on a candidate."""
    candidate_id: UUID
    decision: FeedbackDecision
    rating: Optional[int] = Field(None, ge=1, le=5, description="Rating from 1 to 5")
    comment: Optional[str] = None


class RequestOTPRequest(BaseModel):
    """Request schema for requesting an OTP."""
    email: EmailStr


class VerifyOTPRequest(BaseModel):
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
    name: Optional[str] = None
    role: str
    first_accessed_at: Optional[datetime] = None
    last_accessed_at: Optional[datetime] = None
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
    rating: Optional[int] = None
    comment: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class CandidateSnapshot(BaseModel):
    """Snapshot of candidate data for shared searches."""
    id: UUID
    name: str
    title: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    experience_years: Optional[int] = None
    skills: List[str] = Field(default_factory=list)
    wsi_score: Optional[float] = None
    linkedin_url: Optional[str] = None
    resume_url: Optional[str] = None
    feedback: Optional[FeedbackResponse] = None

    class Config:
        from_attributes = True


class SharedSearchResponse(BaseModel):
    """Response schema for a shared search."""
    id: UUID
    company_id: UUID
    share_type: ShareType
    title: str
    description: Optional[str] = None
    status: ShareStatus
    expires_at: Optional[datetime] = None
    created_at: datetime
    candidate_count: int = 0
    feedback_summary: FeedbackSummary = Field(default_factory=FeedbackSummary)
    recipients: List[RecipientSummary] = Field(default_factory=list)

    class Config:
        from_attributes = True


class SharedSearchDetailResponse(SharedSearchResponse):
    """Detailed response schema for a shared search with candidates and feedbacks."""
    candidates: List[CandidateSnapshot] = Field(default_factory=list)
    feedbacks: List[FeedbackResponse] = Field(default_factory=list)


class PublicSharedSearchResponse(BaseModel):
    """Response schema for public shared search page (before auth)."""
    title: str
    description: Optional[str] = None
    expires_at: Optional[datetime] = None
    shared_by_name: Optional[str] = None
    shared_by_email: Optional[str] = None
    company_name: Optional[str] = None
    company_logo_url: Optional[str] = None
    candidate_count: int = 0
    candidates: List[CandidateSnapshot] = Field(default_factory=list, description="Limited preview without auth")
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
