"""
Pydantic schemas for Attachment API.
"""

from datetime import datetime

from pydantic import BaseModel, Field
from app.shared.types import WeDoBaseModel


class AttachmentCreate(WeDoBaseModel):
    """Schema for creating a new attachment record."""
    candidate_id: str = Field(..., description="Candidate ID")
    candidate_name: str = Field(..., description="Candidate name")
    file_name: str = Field(..., description="Original file name")
    file_type: str = Field(..., description="Type: cv, document, certificate, video, transcript, other")
    file_url: str = Field(..., description="URL where file is stored")
    file_size: int | None = Field(None, description="File size in bytes")
    mime_type: str | None = Field(None, description="MIME type of file")
    upload_source: str = Field(..., description="Source: candidate, recruiter, lia, ats")
    related_entity_type: str | None = Field(None, description="Type of related entity")
    related_entity_id: str | None = Field(None, description="ID of related entity")
    description: str | None = Field(None, description="Description of the attachment")
    uploaded_by: str = Field(..., description="ID of uploader")
    uploaded_by_name: str | None = Field(None, description="Display name of uploader")

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
                "uploaded_by_name": "Maria Santos"
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
    file_size: int | None = None
    mime_type: str | None = None
    upload_source: str
    related_entity_type: str | None = None
    related_entity_id: str | None = None
    description: str | None = None
    is_active: bool
    uploaded_by: str
    uploaded_by_name: str | None = None
    company_id: str
    created_at: datetime | None = None
    updated_at: datetime | None = None

    class Config:
        from_attributes = True


class AttachmentListResponse(BaseModel):
    """Schema for paginated attachments list response."""
    attachments: list[AttachmentResponse]
    total: int
    limit: int
    offset: int


class FileUploadResponse(BaseModel):
    """Schema for file upload response."""
    success: bool
    message: str
    attachment: AttachmentResponse | None = None
    error: str | None = None


class CategoryCount(BaseModel):
    """Category count for UI display."""
    category: str
    label: str
    count: int
    icon: str


class CandidateFilesResponse(BaseModel):
    """Schema for candidate files with categories."""
    attachments: list[AttachmentResponse]
    total: int
    categories: list[CategoryCount]
