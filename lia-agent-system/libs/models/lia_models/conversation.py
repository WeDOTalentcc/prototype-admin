"""
Conversation models for LIA chat system with persistent memory.
"""
from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, String, Integer, DateTime, Text, JSON, ForeignKey, Boolean, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid
import enum

from lia_config.database import Base


class ConversationContextType(str, enum.Enum):
    """Types of conversation contexts."""
    JOB_CHAT = "job_chat"
    TALENT_CHAT = "talent_chat"
    PIPELINE_CHAT = "pipeline_chat"
    KANBAN_CHAT = "kanban_chat"
    CANDIDATES_CHAT = "candidates_chat"
    WIZARD = "wizard"
    GENERAL = "general"
    SCREENING = "screening"
    ANALYTICS = "analytics"
    SETTINGS_CONFIG = "settings_config"  # S02 — company_settings agent context
    AGENT_STUDIO = "agent_studio"  # PR2 — agent_studio domain context


class Conversation(Base):
    """
    Represents a conversation thread between user and LIA.
    Enhanced with context types for persistent memory across sessions.
    """
    __tablename__ = "conversations"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(255), nullable=False, index=True)
    # TENANT-EXEMPT: Conversation legacy pre-multi-tenancy migration 082 (user_id ja scope per-user)
    company_id = Column(String(255), nullable=True, index=True)
    user_role = Column(String(50), default="recruiter")
    
    session_id = Column(String(255), nullable=True, index=True)
    context_type = Column(String(50), default="general", index=True)
    context_id = Column(String(255), nullable=True, index=True)
    
    title = Column(String(500), nullable=True)
    summary = Column(Text, nullable=True)
    intent = Column(String(100), nullable=True)
    workflow_type = Column(String(100), nullable=True)
    workflow_step = Column(Integer, default=0)
    workflow_data = Column(JSON, default=dict)
    
    status = Column(String(50), default="active")
    is_active = Column(Boolean, default=True, index=True)
    is_archived = Column(Boolean, default=False)
    
    message_count = Column(Integer, default=0)
    last_summary_at_count = Column(Integer, default=0)
    
    conversation_metadata = Column(JSON, default=dict)
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan", order_by="Message.created_at")
    summaries = relationship("ConversationSummary", back_populates="conversation", cascade="all, delete-orphan", order_by="ConversationSummary.created_at.desc()")
    
    def __repr__(self):
        return f"<Conversation {self.id} - {self.user_id} - {self.context_type}>"
    
    def to_dict(self) -> dict:
        """Convert to dictionary for API responses."""
        return {
            "id": str(self.id),
            "user_id": self.user_id,
            "company_id": self.company_id,
            "context_type": self.context_type,
            "context_id": self.context_id,
            "title": self.title,
            "summary": self.summary,
            "intent": self.intent,
            "status": self.status,
            "is_active": self.is_active,
            "message_count": self.message_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class Message(Base):
    """
    Individual message in a conversation.
    Enhanced with intent and tool_calls for agent memory.
    """
    __tablename__ = "messages"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id"), nullable=False, index=True)
    
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    intent = Column(String(100), nullable=True)
    prompt_version = Column(String(16), nullable=True)
    
    tool_calls = Column(JSON, nullable=True)
    message_metadata = Column(JSON, default=dict)
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    conversation = relationship("Conversation", back_populates="messages")
    
    def __repr__(self):
        return f"<Message {self.id} - {self.role}>"
    
    def to_dict(self) -> dict:
        """Convert to dictionary for API responses."""
        return {
            "id": str(self.id),
            "conversation_id": str(self.conversation_id),
            "role": self.role,
            "content": self.content,
            "intent": self.intent,
            "prompt_version": self.prompt_version,
            "tool_calls": self.tool_calls,
            "metadata": self.message_metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
    
    def to_llm_format(self) -> dict:
        """Convert to format suitable for LLM context."""
        role_mapping = {
            "human": "user",
            "user": "user",
            "ai": "assistant",
            "assistant": "assistant",
            "system": "system",
            "tool": "tool",
        }
        return {
            "role": role_mapping.get(self.role, self.role),
            "content": self.content,
        }


class ConversationSummary(Base):
    """
    Stores conversation summaries for context management.
    Summaries are generated periodically to compress long conversations.
    """
    __tablename__ = "conversation_summaries"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id"), nullable=False, index=True)
    
    summary = Column(Text, nullable=False)
    message_count = Column(Integer, default=0)
    messages_start_id = Column(UUID(as_uuid=True), nullable=True)
    messages_end_id = Column(UUID(as_uuid=True), nullable=True)
    
    key_entities = Column(JSON, default=dict)
    user_preferences = Column(JSON, default=dict)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    conversation = relationship("Conversation", back_populates="summaries")
    
    def __repr__(self):
        return f"<ConversationSummary {self.id} - {self.message_count} msgs>"
    
    def to_dict(self) -> dict:
        """Convert to dictionary for API responses."""
        return {
            "id": str(self.id),
            "conversation_id": str(self.conversation_id),
            "summary": self.summary,
            "message_count": self.message_count,
            "key_entities": self.key_entities,
            "user_preferences": self.user_preferences,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
