"""
Pydantic schemas for chat API.
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class MessageCreate(BaseModel):
    """Request to create a new message."""
    content: str = Field(..., min_length=1, max_length=10000)
    conversation_id: Optional[str] = None  # If None, creates new conversation


class MessageResponse(BaseModel):
    """Response message from LIA."""
    id: str
    conversation_id: str
    role: str
    content: str
    message_metadata: Dict[str, Any] = {}
    created_at: datetime
    
    class Config:
        from_attributes = True


class ConversationResponse(BaseModel):
    """Response with conversation details."""
    id: str
    user_id: str
    user_role: str
    title: Optional[str]
    intent: Optional[str]
    workflow_type: Optional[str]
    workflow_step: int
    workflow_data: Dict[str, Any] = {}
    status: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ConversationListResponse(BaseModel):
    """List of conversations."""
    conversations: List[ConversationResponse]
    total: int
    page: int
    page_size: int


class ChatResponse(BaseModel):
    """Response from chat endpoint."""
    message: MessageResponse
    conversation: ConversationResponse
