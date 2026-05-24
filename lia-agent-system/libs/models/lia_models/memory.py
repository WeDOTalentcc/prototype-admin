"""
Vector store models for persistent memory with RAG.
Uses pgvector for efficient vector similarity search.
"""
from sqlalchemy import Column, String, DateTime, Text, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from pgvector.sqlalchemy import Vector
from lia_config.database import Base
import uuid
from datetime import datetime


class ConversationMemory(Base):
    """Stores conversation messages with vector embeddings for semantic search."""
    __tablename__ = "conversation_memories"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    session_id = Column(String(100), nullable=False, index=True)
    user_id = Column(String(100), nullable=False, index=True)
    role = Column(String(20), nullable=False)  # user/assistant
    content = Column(Text, nullable=False)
    embedding = Column(Vector(768))  # 768 dimensions for text-embedding-004
    extra_data = Column("metadata", JSONB, default={})  # Renamed to avoid SQLAlchemy conflict
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    __table_args__ = (
        Index('ix_conversation_memories_company_session', 'company_id', 'session_id'),
        Index('ix_conversation_memories_user_created', 'user_id', 'created_at'),
    {"extend_existing": True}, )
    
    def to_dict(self):
        return {
            "id": str(self.id),
            "company_id": str(self.company_id),
            "session_id": self.session_id,
            "user_id": self.user_id,
            "role": self.role,
            "content": self.content,
            "metadata": self.extra_data or {},
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class KnowledgeBase(Base):
    """Stores knowledge base documents with vector embeddings for semantic search."""
    __tablename__ = "knowledge_base"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    document_type = Column(String(50), nullable=False, index=True)  # job_description, policy, faq, etc.
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    embedding = Column(Vector(768))  # 768 dimensions for text-embedding-004
    source = Column(String(255))
    chunk_index = Column(String(50))  # For chunked documents: "0", "1", etc.
    parent_id = Column(UUID(as_uuid=True), nullable=True, index=True)  # Reference to parent document
    extra_data = Column("metadata", JSONB, default={})  # Renamed to avoid SQLAlchemy conflict
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('ix_knowledge_base_company_type', 'company_id', 'document_type'),
    {"extend_existing": True}, )
    
    def to_dict(self):
        return {
            "id": str(self.id),
            "company_id": str(self.company_id),
            "document_type": self.document_type,
            "title": self.title,
            "content": self.content,
            "source": self.source,
            "chunk_index": self.chunk_index,
            "parent_id": str(self.parent_id) if self.parent_id else None,
            "metadata": self.extra_data or {},
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


# Document types for knowledge base
DOCUMENT_TYPES = [
    "job_description",
    "policy",
    "faq",
    "company_info",
    "benefit",
    "process",
    "template",
    "training",
    "guideline",
]
