"""
Pydantic schemas for Attachment API.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class AttachmentCreate(BaseModel):
    """Schema for creating a new attachment record."""
    candidate_id: str = Field(..., description="Candidate ID")
    candidate_name: str = Field(..., description="Candidate name")
    file_name: str = Field(..., description="Original file name")
    file_type: str = Field(..., description="Type: cv, document, certificate, video, transcript, other")
    file_url: str = Field(..., description="URL where file is stored")
    file_size: Optional[int] = Field(None, description="File size in bytes")
    mime_type: Optional[str] = Field(None, description="MIME type of file")
    upload_source: str = Field(..., description="Source: candidate, recruiter, lia, ats")
    related_entity_type: Optional[str] = Field(None, description="Type of related entity")
    related_entity_id: Optional[str] = Field(None, description="ID of related entity")
    description: Optional[str] = Field(None, description="Description of the attachment")
    uploaded_by: str = Field(..., description="ID of uploader")
    uploaded_by_name: Optional[str] = Field(None, description="Display name of uploader")
    company_id: str = Field(..., description="Company ID for multi-tenancy")

    class Config:
        json_schema_extra = {
            "example": {
                "candidate_id": "cand_123",
                "candidate_name": "João Silva",
                "file_name": "curriculum_joao_silva.pdf",
                "file_type": "cv",
                "file_url": "https://storage.example.com/cvs/curriculum_joao_silva.pdf",
                "file_size": 245678,
                "mime_type": "application/pdf",
                "upload_source": "candidate",
                "uploaded_by": "user_456",
                "uploaded_by_name": "Maria Santos",
                "company_id": "company_789"
            }
        }


class AttachmentResponse(BaseModel):
    """Schema for attachment response."""
    id: str
    candidate_id: str
    candidate_name: str
    file_name: str
    file_type: str
    file_url: str
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    upload_source: str
    related_entity_type: Optional[str] = None
    related_entity_id: Optional[str] = None
    description: Optional[str] = None
    is_active: bool
    uploaded_by: str
    uploaded_by_name: Optional[str] = None
    company_id: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AttachmentListResponse(BaseModel):
    """Schema for paginated attachments list response."""
    attachments: List[AttachmentResponse]
    total: int
    limit: int
    offset: int


class FileUploadResponse(BaseModel):
    """Schema for file upload response."""
    success: bool
    message: str
    attachment: Optional[AttachmentResponse] = None
    error: Optional[str] = None


class CategoryCount(BaseModel):
    """Category count for UI display."""
    category: str
    label: str
    count: int
    icon: str


class CandidateFilesResponse(BaseModel):
    """Schema for candidate files with categories."""
    attachments: List[AttachmentResponse]
    total: int
    categories: List[CategoryCount]
