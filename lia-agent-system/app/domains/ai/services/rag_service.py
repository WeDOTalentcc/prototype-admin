"""
RAG (Retrieval-Augmented Generation) service.
Combines memory and knowledge base search with LLM generation.
"""
import logging
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from app.domains.recruiter_assistant.services.memory_service import memory_service
from app.domains.ai.services.llm import LLMProvider, llm_service

logger = logging.getLogger(__name__)


@dataclass
class RAGContext:
    """Context retrieved for RAG generation."""
    conversation_history: list[dict[str, Any]]
    similar_messages: list[dict[str, Any]]
    knowledge_base_docs: list[dict[str, Any]]
    formatted_context: str


class RAGService:
    """Retrieval-Augmented Generation service."""
    
    def __init__(self):
        self.memory_service = memory_service
    
    async def augment_with_context(
        self,
        query: str,
        session_id: str,
        company_id: UUID,
        user_id: str | None = None,
        include_knowledge_base: bool = True,
        include_conversation_history: bool = True,
        include_similar_messages: bool = True,
        knowledge_base_types: list[str] | None = None,
        conversation_limit: int = 10,
        similar_limit: int = 5,
        knowledge_limit: int = 5
    ) -> RAGContext:
        """
        Get relevant context for a query.
        
        Args:
            query: The user's query
            session_id: Current session ID
            company_id: Company UUID
            user_id: Optional user ID for filtering
            include_knowledge_base: Whether to search knowledge base
            include_conversation_history: Whether to include conversation history
            include_similar_messages: Whether to search for similar past messages
            knowledge_base_types: Document types to search
            conversation_limit: Max conversation messages
            similar_limit: Max similar messages
            knowledge_limit: Max knowledge base docs
            
        Returns:
            RAGContext with all retrieved context
        """
        conversation_history = []
        similar_messages = []
        knowledge_docs = []
        
        if include_conversation_history:
            conversation_history = await self.memory_service.get_conversation_context(
                session_id=session_id,
                company_id=company_id,
                limit=conversation_limit
            )
        
        if include_similar_messages:
            similar_messages = await self.memory_service.search_similar_messages(
                query=query,
                company_id=company_id,
                limit=similar_limit,
                user_id=user_id,
                min_similarity=0.7
            )
            
            similar_messages = [
                m for m in similar_messages
                if m.get("session_id") != session_id
            ]
        
        if include_knowledge_base:
            knowledge_docs = await self.memory_service.search_knowledge_base(
                query=query,
                company_id=company_id,
                document_types=knowledge_base_types,
                limit=knowledge_limit,
                min_similarity=0.6
            )
        
        formatted_context = self._format_context(
            conversation_history=conversation_history,
            similar_messages=similar_messages,
            knowledge_docs=knowledge_docs
        )
        
        return RAGContext(
            conversation_history=conversation_history,
            similar_messages=similar_messages,
            knowledge_base_docs=knowledge_docs,
            formatted_context=formatted_context
        )
    
    def _format_context(
        self,
        conversation_history: list[dict[str, Any]],
        similar_messages: list[dict[str, Any]],
        knowledge_docs: list[dict[str, Any]]
    ) -> str:
        """Format retrieved context into a string for the LLM."""
        sections = []
        
        if knowledge_docs:
            kb_section = "## Relevant Knowledge:\n"
            for doc in knowledge_docs:
                kb_section += f"\n### {doc.get('title', 'Document')} ({doc.get('document_type', 'unknown')})\n"
                kb_section += f"{doc.get('content', '')}\n"
            sections.append(kb_section)
        
        if similar_messages:
            similar_section = "## Related Past Conversations:\n"
            for msg in similar_messages[:3]:
                role = msg.get('role', 'unknown')
                content = msg.get('content', '')[:500]
                similarity = msg.get('similarity', 0)
                similar_section += f"\n[{role}] (relevance: {similarity:.2f}): {content}\n"
            sections.append(similar_section)
        
        if conversation_history:
            history_section = "## Current Conversation:\n"
            for msg in conversation_history[-5:]:
                role = msg.get('role', 'unknown')
                content = msg.get('content', '')
                history_section += f"\n[{role}]: {content}\n"
            sections.append(history_section)
        
        return "\n".join(sections) if sections else ""
    
    async def generate_with_rag(
        self,
        query: str,
        session_id: str,
        company_id: UUID,
        system_prompt: str,
        user_id: str | None = None,
        provider: LLMProvider = "gemini",
        include_knowledge_base: bool = True,
        include_conversation_history: bool = True,
        knowledge_base_types: list[str] | None = None,
        store_response: bool = True
    ) -> dict[str, Any]:
        """
        Generate a response using RAG.
        
        Args:
            query: The user's query
            session_id: Current session ID
            company_id: Company UUID
            system_prompt: System prompt for the LLM
            user_id: Optional user ID
            provider: LLM provider to use
            include_knowledge_base: Whether to include KB context
            include_conversation_history: Whether to include history
            knowledge_base_types: Document types to search
            store_response: Whether to store the response in memory
            
        Returns:
            Dict with response text and context used
        """
        try:
            if store_response and user_id:
                await self.memory_service.store_message(
                    session_id=session_id,
                    role="user",
                    content=query,
                    company_id=company_id,
                    user_id=user_id
                )
            
            context = await self.augment_with_context(
                query=query,
                session_id=session_id,
                company_id=company_id,
                user_id=user_id,
                include_knowledge_base=include_knowledge_base,
                include_conversation_history=include_conversation_history,
                knowledge_base_types=knowledge_base_types
            )
            
            augmented_prompt = f"""{system_prompt}

{context.formatted_context}

User Query: {query}

Please provide a helpful and accurate response based on the context provided."""
            
            response_text = await llm_service.generate(
                prompt=augmented_prompt,
                provider=provider
            )
            
            if store_response and user_id:
                await self.memory_service.store_message(
                    session_id=session_id,
                    role="assistant",
                    content=response_text,
                    company_id=company_id,
                    user_id=user_id
                )
            
            return {
                "response": response_text,
                "context_used": {
                    "conversation_history_count": len(context.conversation_history),
                    "similar_messages_count": len(context.similar_messages),
                    "knowledge_docs_count": len(context.knowledge_base_docs),
                    "knowledge_docs": [
                        {"title": d.get("title"), "type": d.get("document_type"), "similarity": d.get("similarity")}
                        for d in context.knowledge_base_docs
                    ]
                },
                "session_id": session_id
            }
            
        except Exception as e:
            logger.error(f"Error in RAG generation: {e}")
            raise
    
    async def generate_simple(
        self,
        query: str,
        company_id: UUID,
        system_prompt: str,
        provider: LLMProvider = "gemini",
        knowledge_base_types: list[str] | None = None
    ) -> dict[str, Any]:
        """
        Generate a response using only knowledge base context (no conversation history).
        
        Useful for one-off queries that don't need session tracking.
        
        Args:
            query: The query
            company_id: Company UUID
            system_prompt: System prompt
            provider: LLM provider
            knowledge_base_types: Document types to search
            
        Returns:
            Dict with response and context
        """
        knowledge_docs = await self.memory_service.search_knowledge_base(
            query=query,
            company_id=company_id,
            document_types=knowledge_base_types,
            limit=5,
            min_similarity=0.6
        )
        
        context = self._format_context(
            conversation_history=[],
            similar_messages=[],
            knowledge_docs=knowledge_docs
        )
        
        augmented_prompt = f"""{system_prompt}

{context}

Query: {query}

Please provide a helpful response based on the available knowledge."""
        
        response_text = await llm_service.generate(
            prompt=augmented_prompt,
            provider=provider
        )
        
        return {
            "response": response_text,
            "knowledge_docs_used": len(knowledge_docs),
            "docs": [
                {"title": d.get("title"), "type": d.get("document_type")}
                for d in knowledge_docs
            ]
        }


rag_service = RAGService()
