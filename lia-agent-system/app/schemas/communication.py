"""
Pydantic schemas for Communication API.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field
from app.shared.types import WeDoBaseModel


class CommunicationCreate(WeDoBaseModel):
    """Schema for creating a new communication record."""
    candidate_id: str = Field(..., description="Candidate ID")
    candidate_name: str = Field(..., description="Candidate name")
    candidate_email: str | None = Field(None, description="Candidate email")
    candidate_phone: str | None = Field(None, description="Candidate phone")
    vacancy_id: str | None = Field(None, description="Related vacancy ID")
    vacancy_title: str | None = Field(None, description="Related vacancy title")
    communication_type: str = Field(..., description="Type: email, whatsapp, triagem_invite, agendamento_invite, feedback")
    channel: str = Field(..., description="Channel: email, whatsapp")
    direction: str = Field(..., description="Direction: outbound, inbound")
    subject: str | None = Field(None, description="Message subject")
    message_content: str = Field(..., description="Full message content")
    template_id: str | None = Field(None, description="Template ID if used")
    template_name: str | None = Field(None, description="Template name if used")
    attachments: list[dict[str, Any]] | None = Field(default_factory=list, description="List of attachments")
    sent_by: str = Field(..., description="ID of sender")
    sent_by_name: str | None = Field(None, description="Display name of sender")
    extra_data: dict[str, Any] | None = Field(default_factory=dict, description="Additional metadata")

    class Config:
        json_schema_extra = {
            "example": {
                "candidate_id": "cand_123",
                "candidate_name": "João Silva",
                "candidate_email": "joao.silva@email.com",
                "communication_type": "email",
                "channel": "email",
                "direction": "outbound",
                "subject": "Convite para entrevista",
                "message_content": "Olá João, gostaríamos de convidá-lo para uma entrevista...",
                "sent_by": "user_456",
                "sent_by_name": "Maria Santos"
            }
        }


class CommunicationResponse(BaseModel):
    """Schema for communication response."""
    id: str
    candidate_id: str
    candidate_name: str
    candidate_email: str | None = None
    candidate_phone: str | None = None
    vacancy_id: str | None = None
    vacancy_title: str | None = None
    communication_type: str
    channel: str
    direction: str
    subject: str | None = None
    message_content: str
    message_preview: str | None = None
    template_id: str | None = None
    template_name: str | None = None
    status: str
    sent_at: datetime | None = None
    delivered_at: datetime | None = None
    read_at: datetime | None = None
    failed_at: datetime | None = None
    error_message: str | None = None
    extra_data: dict[str, Any] = Field(default_factory=dict)
    attachments: list[dict[str, Any]] = Field(default_factory=list)
    sent_by: str
    sent_by_name: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    company_id: str

    class Config:
        from_attributes = True


class CommunicationListResponse(BaseModel):
    """Schema for paginated communications list response."""
    communications: list[CommunicationResponse]
    total: int
    limit: int
    offset: int


class CommunicationStatusUpdate(WeDoBaseModel):
    """Schema for updating communication status."""
    status: str = Field(..., description="New status: sent, delivered, read, failed")
    error_message: str | None = Field(None, description="Error message for failed status")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "delivered",
                "error_message": None
            }
        }
