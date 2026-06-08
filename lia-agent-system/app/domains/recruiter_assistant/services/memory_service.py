"""
Memory service for managing conversation memory and knowledge base.
Provides storage and semantic search capabilities using pgvector.
"""
import logging
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import and_, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.domains.recruiter_assistant.repositories.conversation_memory_repository import (
    ConversationMemoryRepository,
)
from app.shared.services.embedding_service import embedding_service
from lia_models.memory import DOCUMENT_TYPES, ConversationMemory, KnowledgeBase

logger = logging.getLogger(__name__)


class MemoryService:
    """Service for managing conversation memory and knowledge base."""
    
    def __init__(self):
        self.embedding_service = embedding_service
    
    async def store_message(
        self,
        session_id: str,
        role: str,
        content: str,
        company_id: UUID,
        user_id: str,
        metadata: dict[str, Any] | None = None,
        db: AsyncSession | None = None
    ) -> ConversationMemory:
        """
        Store a message with its embedding.
        
        Args:
            session_id: Unique session identifier
            role: Message role (user/assistant)
            content: Message content
            company_id: Company UUID for multi-tenancy
            user_id: User identifier
            metadata: Optional metadata dict
            db: Optional database session
            
        Returns:
            Created ConversationMemory instance
        """
        should_close = db is None
        if db is None:
            db = AsyncSessionLocal()
        
        try:
            embedding = await self.embedding_service.generate_embedding(content, mask_names=True, company_id=str(company_id))
            
            memory = ConversationMemory(
                id=uuid4(),
                company_id=company_id,
                session_id=session_id,
                user_id=user_id,
                role=role,
                content=content,
                embedding=embedding,
                extra_data=metadata or {},
                created_at=datetime.utcnow()
            )
            
            db.add(memory)
            await db.commit()
            await db.refresh(memory)
            
            logger.debug(f"Stored message in session {session_id}, role={role}")
            return memory
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Error storing message: {e}")
            raise
        finally:
            if should_close:
                await db.close()
    
    async def search_similar_messages(
        self,
        query: str,
        company_id: UUID,
        limit: int = 5,
        session_id: str | None = None,
        user_id: str | None = None,
        min_similarity: float = 0.7,
        db: AsyncSession | None = None
    ) -> list[dict[str, Any]]:
        """
        Search for similar previous messages using vector similarity.
        
        Args:
            query: Search query text
            company_id: Company UUID for filtering
            limit: Maximum number of results
            session_id: Optional session filter
            user_id: Optional user filter
            min_similarity: Minimum cosine similarity threshold
            db: Optional database session
            
        Returns:
            List of similar messages with similarity scores
        """
        should_close = db is None
        if db is None:
            db = AsyncSessionLocal()
        
        try:
            query_embedding = await self.embedding_service.generate_embedding(query, mask_names=True, company_id=str(company_id))
            repo = ConversationMemoryRepository(db)
            results = await repo.search_similar_messages(
                company_id=company_id,
                query_embedding=query_embedding,
                session_id=session_id,
                user_id=user_id,
                limit=limit,
                min_similarity=min_similarity,
            )

            messages = []
            for memory, similarity in results:
                msg_dict = memory.to_dict()
                msg_dict["similarity"] = similarity
                messages.append(msg_dict)
            return messages

        except Exception as e:
            logger.error(f"Error searching similar messages: {e}")
            return []
        finally:
            if should_close:
                await db.close()
    
    async def get_conversation_context(
        self,
        session_id: str,
        company_id: UUID,
        limit: int = 10,
        db: AsyncSession | None = None
    ) -> list[dict[str, Any]]:
        """
        Get recent conversation history for a session.
        
        Args:
            session_id: Session identifier
            company_id: Company UUID
            limit: Maximum messages to return
            db: Optional database session
            
        Returns:
            List of messages in chronological order
        """
        should_close = db is None
        if db is None:
            db = AsyncSessionLocal()
        
        try:
            repo = ConversationMemoryRepository(db)
            memories = await repo.get_recent_for_session(
                company_id=company_id,
                session_id=session_id,
                limit=limit,
            )
            messages = [m.to_dict() for m in memories]
            return messages

        except Exception as e:
            logger.error(f"Error getting conversation context: {e}")
            return []
        finally:
            if should_close:
                await db.close()
    
    async def add_to_knowledge_base(
        self,
        document_type: str,
        title: str,
        content: str,
        company_id: UUID,
        source: str | None = None,
        metadata: dict[str, Any] | None = None,
        chunk_size: int = 1000,
        db: AsyncSession | None = None
    ) -> list[KnowledgeBase]:
        """
        Add a document to the knowledge base with chunking for long documents.
        
        Args:
            document_type: Type of document (job_description, policy, etc.)
            title: Document title
            content: Document content
            company_id: Company UUID
            source: Optional source reference
            metadata: Optional metadata
            chunk_size: Maximum chunk size for long documents
            db: Optional database session
            
        Returns:
            List of created KnowledgeBase entries (one per chunk)
        """
        if document_type not in DOCUMENT_TYPES:
            raise ValueError(f"Invalid document type: {document_type}. Must be one of {DOCUMENT_TYPES}")
        
        should_close = db is None
        if db is None:
            db = AsyncSessionLocal()
        
        try:
            chunks = self.embedding_service.chunk_text(content, chunk_size=chunk_size)
            
            embeddings = await self.embedding_service.generate_batch_embeddings(chunks, mask_names=True)
            
            parent_id = uuid4()
            entries = []
            
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                entry = KnowledgeBase(
                    id=parent_id if i == 0 else uuid4(),
                    company_id=company_id,
                    document_type=document_type,
                    title=title,
                    content=chunk,
                    embedding=embedding,
                    source=source,
                    chunk_index=str(i) if len(chunks) > 1 else None,
                    parent_id=None if i == 0 else parent_id,
                    extra_data=metadata or {},
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                db.add(entry)
                entries.append(entry)
            
            await db.commit()
            
            for entry in entries:
                await db.refresh(entry)
            
            logger.info(f"Added {len(entries)} chunks to knowledge base: {title}")
            return entries
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Error adding to knowledge base: {e}")
            raise
        finally:
            if should_close:
                await db.close()
    
    async def search_knowledge_base(
        self,
        query: str,
        company_id: UUID,
        document_types: list[str] | None = None,
        limit: int = 5,
        min_similarity: float = 0.7,
        db: AsyncSession | None = None
    ) -> list[dict[str, Any]]:
        """
        Search the knowledge base for relevant documents.
        
        Args:
            query: Search query
            company_id: Company UUID
            document_types: Optional list of document types to filter
            limit: Maximum results
            min_similarity: Minimum similarity threshold
            db: Optional database session
            
        Returns:
            List of relevant documents with similarity scores
        """
        should_close = db is None
        if db is None:
            db = AsyncSessionLocal()
        
        try:
            query_embedding = await self.embedding_service.generate_embedding(query, mask_names=True, company_id=str(company_id))
            repo = ConversationMemoryRepository(db)
            results = await repo.search_knowledge_base(
                company_id=company_id,
                query_embedding=query_embedding,
                document_types=document_types,
                limit=limit,
                min_similarity=min_similarity,
            )

            documents = []
            for kb_entry, similarity in results:
                doc_dict = kb_entry.to_dict()
                doc_dict["similarity"] = similarity
                documents.append(doc_dict)
            return documents

        except Exception as e:
            logger.error(f"Error searching knowledge base: {e}")
            return []
        finally:
            if should_close:
                await db.close()
    
    async def delete_session_memory(
        self,
        session_id: str,
        company_id: UUID,
        db: AsyncSession | None = None
    ) -> int:
        """
        Delete all messages for a session.
        
        Returns:
            Number of deleted messages
        """
        should_close = db is None
        if db is None:
            db = AsyncSessionLocal()
        
        try:
            stmt = delete(ConversationMemory).where(
                and_(
                    ConversationMemory.session_id == session_id,
                    ConversationMemory.company_id == company_id
                )
            )
            result = await db.execute(stmt)
            await db.commit()
            
            return result.rowcount
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Error deleting session memory: {e}")
            raise
        finally:
            if should_close:
                await db.close()
    
    async def delete_knowledge_base_document(
        self,
        document_id: UUID,
        company_id: UUID,
        db: AsyncSession | None = None
    ) -> int:
        """
        Delete a document and all its chunks from the knowledge base.
        
        Returns:
            Number of deleted entries
        """
        should_close = db is None
        if db is None:
            db = AsyncSessionLocal()
        
        try:
            stmt = delete(KnowledgeBase).where(
                and_(
                    KnowledgeBase.company_id == company_id,
                    (KnowledgeBase.id == document_id) | (KnowledgeBase.parent_id == document_id)
                )
            )
            result = await db.execute(stmt)
            await db.commit()
            
            return result.rowcount
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Error deleting knowledge base document: {e}")
            raise
        finally:
            if should_close:
                await db.close()


memory_service = MemoryService()
