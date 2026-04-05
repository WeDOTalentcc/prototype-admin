"""
Conversations API - Endpoints for managing LIA conversations with persistent memory.

Provides:
- List conversations for a user
- Get conversation details with messages
- Delete/archive conversations
- Clear conversation history
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.domains.recruiter_assistant.services.conversation_memory import ConversationMemory, conversation_memory
from app.models.conversation import ConversationContextType

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/conversations", tags=["conversations"])


class ConversationResponse(BaseModel):
    """Response model for a conversation."""
    id: str
    user_id: str
    context_type: str
    context_id: Optional[str] = None
    title: Optional[str] = None
    summary: Optional[str] = None
    intent: Optional[str] = None
    status: str
    is_active: bool
    message_count: int
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class MessageResponse(BaseModel):
    """Response model for a message."""
    id: str
    conversation_id: str
    role: str
    content: str
    intent: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: Optional[str] = None


class ConversationDetailResponse(BaseModel):
    """Detailed conversation with messages."""
    conversation: ConversationResponse
    messages: List[MessageResponse]
    summary: Optional[str] = None


class ConversationListResponse(BaseModel):
    """List of conversations."""
    conversations: List[ConversationResponse]
    total: int
    offset: int
    limit: int


class CreateConversationRequest(BaseModel):
    """Request to create a new conversation.

    user_id é opcional — quando ausente, o backend usa 'anonymous' ou
    extrai de JWT em implementações futuras com auth middleware.
    O float (LiaChatPanel) não envia user_id; o WebSocket usa JWT separadamente.
    """
    user_id: Optional[str] = None
    context_type: str = "general"
    context_id: Optional[str] = None
    title: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class AddMessageRequest(BaseModel):
    """Request to add a message to a conversation."""
    role: str = Field(..., description="Message role: user, assistant, system, tool")
    content: str = Field(..., description="Message content")
    intent: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    metadata: Optional[Dict[str, Any]] = None


class UpdateSummaryRequest(BaseModel):
    """Request to update conversation summary."""
    force: bool = False


@router.get("", response_model=ConversationListResponse)
async def list_conversations(
    user_id: str = Query(..., description="User ID to get conversations for"),
    context_type: Optional[str] = Query(None, description="Filter by context type"),
    include_archived: bool = Query(False, description="Include archived conversations"),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """
    List conversations for a user.
    
    Returns paginated list of conversations, optionally filtered by context type.
    """
    try:
        conversations = await conversation_memory.get_user_conversations(
            db=db,
            user_id=user_id,
            context_type=context_type,
            include_archived=include_archived,
            limit=limit,
            offset=offset,
        )
        
        return ConversationListResponse(
            conversations=[
                ConversationResponse(
                    id=str(c.id),
                    user_id=c.user_id,
                    context_type=c.context_type or "general",
                    context_id=c.context_id,
                    title=c.title,
                    summary=c.summary,
                    intent=c.intent,
                    status=c.status or "active",
                    is_active=c.is_active if c.is_active is not None else True,
                    message_count=c.message_count or 0,
                    created_at=c.created_at.isoformat() if c.created_at else None,
                    updated_at=c.updated_at.isoformat() if c.updated_at else None,
                )
                for c in conversations
            ],
            total=len(conversations),
            offset=offset,
            limit=limit,
        )
    except Exception as e:
        logger.error(f"Error listing conversations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{conversation_id}", response_model=ConversationDetailResponse)
async def get_conversation(
    conversation_id: str,
    include_messages: bool = Query(True, description="Include messages"),
    include_summaries: bool = Query(True, description="Include conversation summaries"),
    message_limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    """
    Get a conversation by ID with its messages and summaries.
    
    Query params:
    - include_messages: Whether to include conversation messages (default: true)
    - include_summaries: Whether to include conversation summaries (default: true)
    - message_limit: Maximum number of messages to return (1-200, default: 50)
    """
    try:
        conversation = await conversation_memory.get_conversation(
            db=db,
            conversation_id=conversation_id,
            include_messages=include_messages,
            include_summaries=include_summaries,
        )
        
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        messages = []
        if include_messages:
            recent_messages = await conversation_memory.get_recent_messages(
                db=db,
                conversation_id=conversation_id,
                limit=message_limit,
            )
            messages = [
                MessageResponse(
                    id=str(m.id),
                    conversation_id=str(m.conversation_id),
                    role=m.role,
                    content=m.content,
                    intent=m.intent,
                    tool_calls=m.tool_calls,
                    metadata=m.message_metadata,
                    created_at=m.created_at.isoformat() if m.created_at else None,
                )
                for m in recent_messages
            ]
        
        summary = None
        if include_summaries:
            summary = await conversation_memory.get_context_summary(db, conversation_id)
        
        return ConversationDetailResponse(
            conversation=ConversationResponse(
                id=str(conversation.id),
                user_id=conversation.user_id,
                context_type=conversation.context_type or "general",
                context_id=conversation.context_id,
                title=conversation.title,
                summary=conversation.summary,
                intent=conversation.intent,
                status=conversation.status or "active",
                is_active=conversation.is_active if conversation.is_active is not None else True,
                message_count=conversation.message_count or 0,
                created_at=conversation.created_at.isoformat() if conversation.created_at else None,
                updated_at=conversation.updated_at.isoformat() if conversation.updated_at else None,
            ),
            messages=messages,
            summary=summary,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("", response_model=ConversationResponse)
async def create_conversation(
    request: CreateConversationRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new conversation.
    """
    try:
        effective_user_id = request.user_id or "anonymous"
        conversation = await conversation_memory.get_or_create_conversation(
            db=db,
            user_id=effective_user_id,
            context_type=request.context_type,
            context_id=request.context_id,
            title=request.title,
            metadata=request.metadata,
        )
        
        await db.commit()
        
        return ConversationResponse(
            id=str(conversation.id),
            user_id=conversation.user_id,
            context_type=conversation.context_type or "general",
            context_id=conversation.context_id,
            title=conversation.title,
            summary=conversation.summary,
            intent=conversation.intent,
            status=conversation.status or "active",
            is_active=conversation.is_active if conversation.is_active is not None else True,
            message_count=conversation.message_count or 0,
            created_at=conversation.created_at.isoformat() if conversation.created_at else None,
            updated_at=conversation.updated_at.isoformat() if conversation.updated_at else None,
        )
    except Exception as e:
        logger.error(f"Error creating conversation: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{conversation_id}/messages", response_model=MessageResponse)
async def add_message(
    conversation_id: str,
    request: AddMessageRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Add a message to a conversation.
    """
    try:
        message = await conversation_memory.add_message(
            db=db,
            conversation_id=conversation_id,
            role=request.role,
            content=request.content,
            intent=request.intent,
            tool_calls=request.tool_calls,
            metadata=request.metadata,
        )
        
        await db.commit()
        
        return MessageResponse(
            id=str(message.id),
            conversation_id=str(message.conversation_id),
            role=message.role,
            content=message.content,
            intent=message.intent,
            tool_calls=message.tool_calls,
            metadata=message.message_metadata,
            created_at=message.created_at.isoformat() if message.created_at else None,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error adding message: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{conversation_id}/summary", response_model=Dict[str, Any])
async def update_summary(
    conversation_id: str,
    request: UpdateSummaryRequest = UpdateSummaryRequest(),
    db: AsyncSession = Depends(get_db),
):
    """
    Generate or update conversation summary.
    """
    try:
        summary = await conversation_memory.update_summary(
            db=db,
            conversation_id=conversation_id,
            force=request.force,
        )
        
        await db.commit()
        
        return {
            "conversation_id": conversation_id,
            "summary": summary,
            "updated": summary is not None,
        }
    except Exception as e:
        logger.error(f"Error updating summary: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a conversation and all its messages.
    """
    try:
        success = await conversation_memory.delete_conversation(
            db=db,
            conversation_id=conversation_id,
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        await db.commit()
        
        return {"success": True, "message": "Conversation deleted"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting conversation: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{conversation_id}/archive")
async def archive_conversation(
    conversation_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Archive a conversation (soft delete).
    """
    try:
        success = await conversation_memory.archive_conversation(
            db=db,
            conversation_id=conversation_id,
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        await db.commit()
        
        return {"success": True, "message": "Conversation archived"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error archiving conversation: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{conversation_id}/clear")
async def clear_conversation(
    conversation_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Clear all messages from a conversation (reset).
    """
    try:
        success = await conversation_memory.clear_conversation(
            db=db,
            conversation_id=conversation_id,
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        await db.commit()
        
        return {"success": True, "message": "Conversation cleared"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error clearing conversation: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{conversation_id}/context")
async def get_conversation_context(
    conversation_id: str,
    max_messages: int = Query(20, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    """
    Get conversation context formatted for LLM usage.
    
    Returns messages and summary in a format ready for LLM prompts.
    """
    try:
        context = await conversation_memory.get_context_for_llm(
            db=db,
            conversation_id=conversation_id,
            max_messages=max_messages,
        )
        
        return context
    except Exception as e:
        logger.error(f"Error getting conversation context: {e}")
        raise HTTPException(status_code=500, detail=str(e))
