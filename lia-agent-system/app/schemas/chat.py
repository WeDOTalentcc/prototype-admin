"""
Pydantic schemas for chat API.
"""
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field
from app.shared.types import WeDoBaseModel


class MessageCreate(WeDoBaseModel):
    """Request to create a new message."""
    content: str = Field(..., min_length=1, max_length=10000)
    conversation_id: str | None = None
    context: dict[str, Any] | None = None


class MessageResponse(BaseModel):
    """Response message from LIA."""
    id: str
    conversation_id: str
    role: str
    content: str
    message_metadata: dict[str, Any] = {}
    created_at: datetime
    
    class Config:
        from_attributes = True


class ConversationResponse(BaseModel):
    """Response with conversation details."""
    id: str
    user_id: str
    user_role: str
    title: str | None
    intent: str | None
    workflow_type: str | None
    workflow_step: int
    workflow_data: dict[str, Any] = {}
    status: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ConversationListResponse(BaseModel):
    """List of conversations."""
    conversations: list[ConversationResponse]
    total: int
    page: int
    page_size: int


class ChatResponse(BaseModel):
    """Response from chat endpoint."""
    message: MessageResponse
    conversation: ConversationResponse
