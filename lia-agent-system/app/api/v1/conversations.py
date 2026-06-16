"""
Conversations API - Endpoints for managing LIA conversations with persistent memory.

Provides:
- List conversations for a user
- Get conversation details with messages
- Delete/archive conversations
- Clear conversation history
"""
import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db, get_tenant_db
from app.domains.recruiter_assistant.services.conversation_memory import conversation_memory
from app.shared.security.require_company_id import require_company_id
from app.shared.types import WeDoBaseModel
from typing import Annotated
from fastapi import Path
from app.api.v1._path_patterns import DUAL_ID_PATH_PATTERN, reorder_collection_before_item
from app.shared.errors import LIAError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/conversations", tags=["conversations"])


# DUPLICATE_OF_INTENT: app/schemas/chat.py:31 — REST handler-side response with extra context_type/context_id fields (Sprint Q.4: M-bucket pending merge)
class ConversationResponse(BaseModel):
    """Response model for a conversation."""
    id: str
    user_id: str
    context_type: str
    context_id: str | None = None
    title: str | None = None
    summary: str | None = None
    intent: str | None = None
    status: str
    is_active: bool
    message_count: int
    created_at: str | None = None
    updated_at: str | None = None


# DUPLICATE_OF_INTENT: app/schemas/chat.py:18 — REST handler-side response with extra intent field (Sprint Q.4: M-bucket pending merge)
class MessageResponse(BaseModel):
    """Response model for a message."""
    id: str
    conversation_id: str
    role: str
    content: str
    intent: str | None = None
    tool_calls: list[dict[str, Any]] | None = None
    metadata: dict[str, Any] | None = None
    created_at: str | None = None


class ConversationDetailResponse(BaseModel):
    """Detailed conversation with messages."""
    conversation: ConversationResponse
    messages: list[MessageResponse]
    summary: str | None = None


# DUPLICATE_OF_INTENT: app/schemas/chat.py:49 — REST uses offset+limit pagination; canonical uses page+page_size (Sprint Q.4: M-bucket pending merge)
class ConversationListResponse(BaseModel):
    """List of conversations."""
    conversations: list[ConversationResponse]
    total: int
    offset: int
    limit: int


class CreateConversationRequest(WeDoBaseModel):
    """Request to create a new conversation.

    user_id é opcional — quando ausente, o backend usa 'anonymous' ou
    extrai de JWT em implementações futuras com auth middleware.
    O float (LiaChatPanel) não envia user_id; o WebSocket usa JWT separadamente.
    """
    user_id: str | None = None
    context_type: str = "general"
    context_id: str | None = None
    title: str | None = None
    metadata: dict[str, Any] | None = None


class AddMessageRequest(WeDoBaseModel):
    """Request to add a message to a conversation."""
    role: str = Field(..., description="Message role: user, assistant, system, tool")
    content: str = Field(..., description="Message content")
    intent: str | None = None
    tool_calls: list[dict[str, Any]] | None = None
    metadata: dict[str, Any] | None = None


class UpdateSummaryRequest(WeDoBaseModel):
    """Request to update conversation summary."""
    force: bool = False

class RenameConversationRequest(WeDoBaseModel):
    title: str = Field(..., min_length=1, max_length=500)



@router.get("", response_model=ConversationListResponse)
async def list_conversations(
    user_id: str = Query(..., description="User ID to get conversations for"),
    context_type: str | None = Query(None, description="Filter by context type"),
    include_archived: bool = Query(False, description="Include archived conversations"),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
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
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing conversations: {e}")
        raise LIAError(message="Erro interno do servidor")


@router.get("/{conversation_id}", response_model=ConversationDetailResponse)
async def get_conversation(
    conversation_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    include_messages: bool = Query(True, description="Include messages"),
    include_summaries: bool = Query(True, description="Include conversation summaries"),
    message_limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
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
        raise LIAError(message="Erro interno do servidor")


@router.post("", response_model=ConversationResponse)
async def create_conversation(
    request: CreateConversationRequest,
    db: AsyncSession = Depends(get_db),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Create a new conversation.
    """
    try:
        effective_user_id = request.user_id or "anonymous"
        conversation = await conversation_memory.get_or_create_conversation(
            db=db,
            user_id=effective_user_id,
            company_id=company_id,
            context_type=request.context_type,
            context_id=request.context_id,
            title=request.title,
            metadata=request.metadata,
        )
        
        
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
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating conversation: {e}")
        await db.rollback()
        raise LIAError(message="Erro interno do servidor")


@router.post("/{conversation_id}/messages", response_model=MessageResponse)
async def add_message(
    conversation_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    request: AddMessageRequest,
    db: AsyncSession = Depends(get_tenant_db),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
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
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding message: {e}")
        await db.rollback()
        raise LIAError(message="Erro interno do servidor")


@router.post("/{conversation_id}/summary", response_model=dict[str, Any])
async def update_summary(
    conversation_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    request: UpdateSummaryRequest = UpdateSummaryRequest(),
    db: AsyncSession = Depends(get_tenant_db),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Generate or update conversation summary.
    """
    try:
        summary = await conversation_memory.update_summary(
            db=db,
            conversation_id=conversation_id,
            force=request.force,
        )
        
        
        return {
            "conversation_id": conversation_id,
            "summary": summary,
            "updated": summary is not None,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating summary: {e}")
        await db.rollback()
        raise LIAError(message="Erro interno do servidor")



@router.patch("/{conversation_id}")
async def rename_conversation(
    conversation_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    request: RenameConversationRequest,
    db: AsyncSession = Depends(get_db),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    from lia_models.conversation import Conversation
    from sqlalchemy import select
    result = await db.execute(select(Conversation).where(Conversation.id == conversation_id, Conversation.company_id == company_id))
    conversation = result.scalar_one_or_none()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    conversation.title = request.title
    await db.commit()
    await db.refresh(conversation)
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

@router.delete("/{conversation_id}", response_model=None)
async def delete_conversation(
    conversation_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    db: AsyncSession = Depends(get_tenant_db),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
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
        
        
        return {"success": True, "message": "Conversation deleted"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting conversation: {e}")
        await db.rollback()
        raise LIAError(message="Erro interno do servidor")


@router.post("/{conversation_id}/archive", response_model=None)
async def archive_conversation(
    conversation_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    db: AsyncSession = Depends(get_db),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
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
        
        
        return {"success": True, "message": "Conversation archived"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error archiving conversation: {e}")
        await db.rollback()
        raise LIAError(message="Erro interno do servidor")


@router.post("/{conversation_id}/clear", response_model=None)
async def clear_conversation(
    conversation_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    db: AsyncSession = Depends(get_db),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
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
        
        
        return {"success": True, "message": "Conversation cleared"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error clearing conversation: {e}")
        await db.rollback()
        raise LIAError(message="Erro interno do servidor")


@router.get("/{conversation_id}/context", response_model=None)
async def get_conversation_context(
    conversation_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    max_messages: int = Query(20, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
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
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting conversation context: {e}")
        raise LIAError(message="Erro interno do servidor")

reorder_collection_before_item(router)
