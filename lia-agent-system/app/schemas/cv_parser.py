"""
Pydantic schemas for CV Parser API.
"""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field
from app.shared.types import WeDoBaseModel


class Experience(BaseModel):
    """Work experience entry."""
    company: str = Field(..., description="Company name")
    title: str = Field(..., description="Job title/role")
    start_date: str | None = Field(None, description="Start date (e.g., 'Jan 2020' or '2020-01')")
    end_date: str | None = Field(None, description="End date or 'Present'")
    is_current: bool = Field(False, description="If this is the current job")
    description: str | None = Field(None, description="Role description and achievements")
    location: str | None = Field(None, description="Work location")


class Education(BaseModel):
    """Education entry."""
    institution: str = Field(..., description="School/University name")
    degree: str | None = Field(None, description="Degree type (e.g., 'Bachelor', 'MBA')")
    field_of_study: str | None = Field(None, description="Field/Major")
    start_date: str | None = Field(None, description="Start date")
    end_date: str | None = Field(None, description="End date or expected graduation")
    is_completed: bool = Field(True, description="If degree is completed")
    description: str | None = Field(None, description="Additional details, honors, etc.")


class ParsedCV(BaseModel):
    """Complete parsed CV data."""
    full_name: str = Field(..., description="Candidate's full name")
    email: str | None = Field(None, description="Email address")
    phone: str | None = Field(None, description="Phone number")
    linkedin: str | None = Field(None, description="LinkedIn profile URL")
    github: str | None = Field(None, description="GitHub profile URL")
    portfolio: str | None = Field(None, description="Portfolio/website URL")
    location: str | None = Field(None, description="Current location")
    current_title: str | None = Field(None, description="Current job title")
    summary: str | None = Field(None, description="Professional summary/objective")
    
    experiences: list[Experience] = Field(default_factory=list, description="Work experiences")
    education: list[Education] = Field(default_factory=list, description="Education history")
    skills: list[str] = Field(default_factory=list, description="Technical and professional skills")
    languages: list[str] = Field(default_factory=list, description="Languages spoken")
    certifications: list[str] = Field(default_factory=list, description="Certifications")
    
    soft_skills: list[str] = Field(default_factory=list, description="Soft skills (communication, leadership, etc.)")
    seniority_level: str | None = Field(None, description="Seniority: junior, pleno, senior, lead, manager, director, c-level")
    date_of_birth: str | None = Field(None, description="Date of birth if provided")
    interests: list[str] = Field(default_factory=list, description="Personal/professional interests")
    
    raw_text: str = Field(..., description="Original extracted text")
    file_name: str | None = Field(None, description="Original file name")
    file_type: str | None = Field(None, description="File type (pdf, docx, txt)")
    file_size_bytes: int | None = Field(None, description="File size in bytes")
    file_url: str | None = Field(None, description="URL/path to the saved CV file")
    file_hash: str | None = Field(None, description="SHA-256 hex digest for file dedup (GAP-05-006)")
    
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="AI extraction confidence (0-1)")
    extraction_notes: list[str] = Field(default_factory=list, description="Fields that need review")
    
    parsed_at: datetime = Field(default_factory=datetime.utcnow, description="Parse timestamp")


class CVUploadResponse(BaseModel):
    """Response from CV upload endpoint."""
    success: bool
    message: str
    parsed_cv: ParsedCV | None = None
    duplicate_warning: dict | None = Field(None, description="Warning if potential duplicate found")
    candidate_id: UUID | None = Field(None, description="ID if candidate was auto-created")
    file_duplicate_warning: dict | None = Field(None, description="Warning if identical file already uploaded (GAP-05-006)")


class CVParseTextRequest(WeDoBaseModel):
    """Request for parsing plain text CV."""
    text: str = Field(..., min_length=50, description="CV text content")
    source: str | None = Field("manual_text", description="Source identifier")


class CVConfirmRequest(WeDoBaseModel):
    """Request to confirm parsed CV and create candidate."""
    parsed_cv: ParsedCV
    override_duplicate: bool = Field(False, description="Create even if duplicate found")
    tags: list[str] = Field(default_factory=list, description="Tags to add")
    notes: str | None = Field(None, description="Initial notes")
    job_vacancy_id: UUID | None = Field(None, description="Link to job vacancy")


class CVConfirmResponse(BaseModel):
    """Response from CV confirm endpoint."""
    success: bool
    message: str
    candidate_id: UUID | None = None
    candidate_name: str | None = None
    candidate_email: str | None = None
    was_duplicate: bool = False
    merged_with_id: UUID | None = Field(None, description="If merged with existing candidate")


class DuplicateCheck(BaseModel):
    """Duplicate candidate information."""
    is_duplicate: bool
    match_type: str | None = Field(None, description="'email', 'name_phone', or 'linkedin'")
    existing_candidate_id: UUID | None = None
    existing_candidate_name: str | None = None
    similarity_score: float | None = None


class SupportedFormatsResponse(BaseModel):
    """Response with supported CV formats."""
    formats: list[dict[str, str]]
    max_file_size_mb: float
    max_file_size_bytes: int
