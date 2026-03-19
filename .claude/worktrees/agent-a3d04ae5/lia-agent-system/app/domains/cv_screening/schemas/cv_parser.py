"""
Pydantic schemas for CV Parser API.
"""
from datetime import datetime
from typing import Optional, List, Dict
from pydantic import BaseModel, Field, EmailStr
from uuid import UUID


class Experience(BaseModel):
    """Work experience entry."""
    company: str = Field(..., description="Company name")
    title: str = Field(..., description="Job title/role")
    start_date: Optional[str] = Field(None, description="Start date (e.g., 'Jan 2020' or '2020-01')")
    end_date: Optional[str] = Field(None, description="End date or 'Present'")
    is_current: bool = Field(False, description="If this is the current job")
    description: Optional[str] = Field(None, description="Role description and achievements")
    location: Optional[str] = Field(None, description="Work location")


class Education(BaseModel):
    """Education entry."""
    institution: str = Field(..., description="School/University name")
    degree: Optional[str] = Field(None, description="Degree type (e.g., 'Bachelor', 'MBA')")
    field_of_study: Optional[str] = Field(None, description="Field/Major")
    start_date: Optional[str] = Field(None, description="Start date")
    end_date: Optional[str] = Field(None, description="End date or expected graduation")
    is_completed: bool = Field(True, description="If degree is completed")
    description: Optional[str] = Field(None, description="Additional details, honors, etc.")


class ParsedCV(BaseModel):
    """Complete parsed CV data."""
    full_name: str = Field(..., description="Candidate's full name")
    email: Optional[str] = Field(None, description="Email address")
    phone: Optional[str] = Field(None, description="Phone number")
    linkedin: Optional[str] = Field(None, description="LinkedIn profile URL")
    github: Optional[str] = Field(None, description="GitHub profile URL")
    portfolio: Optional[str] = Field(None, description="Portfolio/website URL")
    location: Optional[str] = Field(None, description="Current location")
    current_title: Optional[str] = Field(None, description="Current job title")
    summary: Optional[str] = Field(None, description="Professional summary/objective")
    
    experiences: List[Experience] = Field(default_factory=list, description="Work experiences")
    education: List[Education] = Field(default_factory=list, description="Education history")
    skills: List[str] = Field(default_factory=list, description="Technical and professional skills")
    languages: List[str] = Field(default_factory=list, description="Languages spoken")
    certifications: List[str] = Field(default_factory=list, description="Certifications")
    
    soft_skills: List[str] = Field(default_factory=list, description="Soft skills (communication, leadership, etc.)")
    seniority_level: Optional[str] = Field(None, description="Seniority: junior, pleno, senior, lead, manager, director, c-level")
    date_of_birth: Optional[str] = Field(None, description="Date of birth if provided")
    interests: List[str] = Field(default_factory=list, description="Personal/professional interests")
    
    raw_text: str = Field(..., description="Original extracted text")
    file_name: Optional[str] = Field(None, description="Original file name")
    file_type: Optional[str] = Field(None, description="File type (pdf, docx, txt)")
    file_size_bytes: Optional[int] = Field(None, description="File size in bytes")
    file_url: Optional[str] = Field(None, description="URL/path to the saved CV file")
    
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="AI extraction confidence (0-1)")
    extraction_notes: List[str] = Field(default_factory=list, description="Fields that need review")
    
    parsed_at: datetime = Field(default_factory=datetime.utcnow, description="Parse timestamp")


class CVUploadResponse(BaseModel):
    """Response from CV upload endpoint."""
    success: bool
    message: str
    parsed_cv: Optional[ParsedCV] = None
    duplicate_warning: Optional[Dict] = Field(None, description="Warning if potential duplicate found")
    candidate_id: Optional[UUID] = Field(None, description="ID if candidate was auto-created")


class CVParseTextRequest(BaseModel):
    """Request for parsing plain text CV."""
    text: str = Field(..., min_length=50, description="CV text content")
    source: Optional[str] = Field("manual_text", description="Source identifier")


class CVConfirmRequest(BaseModel):
    """Request to confirm parsed CV and create candidate."""
    parsed_cv: ParsedCV
    override_duplicate: bool = Field(False, description="Create even if duplicate found")
    tags: List[str] = Field(default_factory=list, description="Tags to add")
    notes: Optional[str] = Field(None, description="Initial notes")
    job_vacancy_id: Optional[UUID] = Field(None, description="Link to job vacancy")


class CVConfirmResponse(BaseModel):
    """Response from CV confirm endpoint."""
    success: bool
    message: str
    candidate_id: Optional[UUID] = None
    candidate_name: Optional[str] = None
    candidate_email: Optional[str] = None
    was_duplicate: bool = False
    merged_with_id: Optional[UUID] = Field(None, description="If merged with existing candidate")


class DuplicateCheck(BaseModel):
    """Duplicate candidate information."""
    is_duplicate: bool
    match_type: Optional[str] = Field(None, description="'email', 'name_phone', or 'linkedin'")
    existing_candidate_id: Optional[UUID] = None
    existing_candidate_name: Optional[str] = None
    similarity_score: Optional[float] = None


class SupportedFormatsResponse(BaseModel):
    """Response with supported CV formats."""
    formats: List[Dict[str, str]]
    max_file_size_mb: float
    max_file_size_bytes: int
