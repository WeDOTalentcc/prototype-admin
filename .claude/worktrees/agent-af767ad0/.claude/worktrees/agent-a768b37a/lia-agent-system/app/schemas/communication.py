"""
Pydantic schemas for Communication API.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class CommunicationCreate(BaseModel):
    """Schema for creating a new communication record."""
    candidate_id: str = Field(..., description="Candidate ID")
    candidate_name: str = Field(..., description="Candidate name")
    candidate_email: Optional[str] = Field(None, description="Candidate email")
    candidate_phone: Optional[str] = Field(None, description="Candidate phone")
    vacancy_id: Optional[str] = Field(None, description="Related vacancy ID")
    vacancy_title: Optional[str] = Field(None, description="Related vacancy title")
    communication_type: str = Field(..., description="Type: email, whatsapp, triagem_invite, agendamento_invite, feedback")
    channel: str = Field(..., description="Channel: email, whatsapp")
    direction: str = Field(..., description="Direction: outbound, inbound")
    subject: Optional[str] = Field(None, description="Message subject")
    message_content: str = Field(..., description="Full message content")
    template_id: Optional[str] = Field(None, description="Template ID if used")
    template_name: Optional[str] = Field(None, description="Template name if used")
    attachments: Optional[List[Dict[str, Any]]] = Field(default_factory=list, description="List of attachments")
    sent_by: str = Field(..., description="ID of sender")
    sent_by_name: Optional[str] = Field(None, description="Display name of sender")
    company_id: str = Field(..., description="Company ID for multi-tenancy")
    extra_data: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")

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
                "sent_by_name": "Maria Santos",
                "company_id": "company_789"
            }
        }


class CommunicationResponse(BaseModel):
    """Schema for communication response."""
    id: str
    candidate_id: str
    candidate_name: str
    candidate_email: Optional[str] = None
    candidate_phone: Optional[str] = None
    vacancy_id: Optional[str] = None
    vacancy_title: Optional[str] = None
    communication_type: str
    channel: str
    direction: str
    subject: Optional[str] = None
    message_content: str
    message_preview: Optional[str] = None
    template_id: Optional[str] = None
    template_name: Optional[str] = None
    status: str
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    failed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    extra_data: Dict[str, Any] = Field(default_factory=dict)
    attachments: List[Dict[str, Any]] = Field(default_factory=list)
    sent_by: str
    sent_by_name: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    company_id: str

    class Config:
        from_attributes = True


class CommunicationListResponse(BaseModel):
    """Schema for paginated communications list response."""
    communications: List[CommunicationResponse]
    total: int
    limit: int
    offset: int


class CommunicationStatusUpdate(BaseModel):
    """Schema for updating communication status."""
    status: str = Field(..., description="New status: sent, delivered, read, failed")
    error_message: Optional[str] = Field(None, description="Error message for failed status")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "delivered",
                "error_message": None
            }
        }
