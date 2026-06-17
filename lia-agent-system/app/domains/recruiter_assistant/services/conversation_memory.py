"""

# ADR-001-EXEMPT: Conversation memory persists Conversation/Message lifecycle
# (get_or_create, get_by_id, recent_messages, list_for_user). Tenant scope
# inherited from authenticated user context.
# TODO Sprint 6: extract to ConversationRepository + MessageRepository.  # R-048: needs owner + ticket

Conversation Memory Service - Persistent memory for LIA conversations.

Provides:
- Conversation management (create, get, update, delete)
- Message storage with role/content/intent
- Automatic summary generation for long conversations
- Context retrieval for LLM prompt construction
- User preference tracking across sessions
"""
import logging
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import and_, delete, desc, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from lia_models.conversation import Conversation, ConversationSummary, Message

from app.shared.observability.tracing import trace_span

logger = logging.getLogger(__name__)

SUMMARY_TRIGGER_COUNT = 10
MAX_CONTEXT_MESSAGES = 20
MAX_CONTEXT_TOKENS_ESTIMATE = 4000

CONTEXT_COMPRESSION_CONFIG = {
    "max_messages_before_summarize": 10,
    "keep_recent_messages": 5,
    "summary_max_tokens": 500,
    "total_context_max_tokens": 2000
}


class ConversationMemory:
    """
    Service for managing persistent conversation memory.
    
    Handles:
    - Conversation lifecycle (create, update, archive)
    - Message storage and retrieval
    - Automatic summary generation
    - Context building for LLM prompts
    """
    
    def __init__(self, llm_service=None):
        """
        Initialize ConversationMemory.
        
        Args:
            llm_service: Optional LLM service for summary generation
        """
        self.llm_service = llm_service
        self._cache: dict[str, dict[str, Any]] = {}
    
    async def get_or_create_conversation(
        self,
        db: AsyncSession,
        user_id: str,
        company_id: str,
        context_type: str = "general",
        context_id: str | None = None,
        session_id: str | None = None,
        title: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Conversation:
        """
        Get existing active conversation or create a new one.
        
        If context_type and context_id match an existing active conversation,
        returns that conversation. Otherwise creates a new one.
        
        Args:
            db: Database session
            user_id: User ID
            context_type: Type of conversation context
            context_id: Optional context identifier (job_id, pipeline_id, etc.)
            session_id: Optional session ID for grouping
            title: Optional conversation title
            metadata: Optional metadata dict
            
        Returns:
            Conversation object

        Raises:
            ValueError: if company_id is empty (multi-tenancy fail-closed).
        """
        if not company_id:
            raise ValueError(
                "company_id is required (multi-tenancy fail-closed). "
                "conversations table has RLS policy — INSERT without "
                "company_id raises InsufficientPrivilegeError at runtime."
            )
        if context_id:
            query = select(Conversation).where(
                and_(
                    Conversation.company_id == company_id,
                    Conversation.user_id == user_id,
                    Conversation.context_type == context_type,
                    Conversation.context_id == context_id,
                    Conversation.is_active,
                )
            ).order_by(desc(Conversation.updated_at))
            
            result = await db.execute(query)
            conversation = result.scalar_one_or_none()
            
            if conversation:
                logger.info(f"📝 Found existing conversation: {conversation.id}")
                return conversation
        
        conversation = Conversation(
            user_id=user_id,
            company_id=company_id,
            context_type=context_type,
            context_id=context_id,
            session_id=session_id,
            title=title,
            conversation_metadata=metadata or {},
            is_active=True,
            status="active",
        )
        
        db.add(conversation)
        await db.flush()
        
        logger.info(f"🆕 Created new conversation: {conversation.id} for {user_id}")
        return conversation
    
    async def get_conversation(
        self,
        db: AsyncSession,
        conversation_id: str,
        include_messages: bool = False,
        include_summaries: bool = False,
        company_id: str | None = None,
    ) -> Conversation | None:
        """
        Get a conversation by ID.

        Args:
            db: Database session
            conversation_id: Conversation ID
            include_messages: Whether to load messages
            include_summaries: Whether to load summaries
            company_id: When provided, enforces tenant isolation (P0 multi-tenancy fix).

        Returns:
            Conversation or None
        """
        try:
            conv_uuid = UUID(conversation_id) if isinstance(conversation_id, str) else conversation_id
        except (ValueError, TypeError):
            logger.warning(f"Invalid conversation ID format: {conversation_id}")
            return None

        query = select(Conversation).where(Conversation.id == conv_uuid)
        if company_id:
            query = query.where(Conversation.company_id == company_id)
        
        if include_messages:
            query = query.options(selectinload(Conversation.messages))
        if include_summaries:
            query = query.options(selectinload(Conversation.summaries))
        
        result = await db.execute(query)
        conv = result.scalar_one_or_none()

        # Defense in depth: reject if returned conv belongs to different tenant
        if conv is not None and company_id and conv.company_id and conv.company_id != company_id:
            logger.warning(
                "get_conversation tenant mismatch — conv.company_id=%s requested=%s",
                conv.company_id, company_id,
            )
            return None

        return conv

    async def add_message(
        self,
        db: AsyncSession,
        conversation_id: str,
        role: str,
        content: str,
        intent: str | None = None,
        tool_calls: list[dict] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Message:
        """
        Add a message to a conversation.
        
        Args:
            db: Database session
            conversation_id: Conversation ID
            role: Message role (user, assistant, system, tool)
            content: Message content
            intent: Optional detected intent
            tool_calls: Optional tool calls made
            metadata: Optional metadata
            
        Returns:
            Created Message object
        """
        try:
            conv_uuid = UUID(conversation_id) if isinstance(conversation_id, str) else conversation_id
        except (ValueError, TypeError):
            raise ValueError(f"Invalid conversation ID: {conversation_id}")
        
        message = Message(
            conversation_id=conv_uuid,
            role=role,
            content=content,
            intent=intent,
            tool_calls=tool_calls,
            message_metadata=metadata or {},
        )
        
        db.add(message)
        # TENANT-EXEMPT: conversation_memory queries user-scoped messages (user_id authoritative), not company-scoped row data
        
        await db.execute(
            # TENANT-EXEMPT: conversation_memory queries user-scoped messages (user_id authoritative), not company-scoped row data
            update(Conversation)
            .where(Conversation.id == conv_uuid)
            .values(
                message_count=Conversation.message_count + 1,
                updated_at=datetime.utcnow()
            )
        )
        
        await db.flush()
        
        conversation = await self.get_conversation(db, conversation_id)
        if conversation and self._should_generate_summary(conversation):
            await self._trigger_summary_generation(db, conversation)
        
        logger.debug(f"💬 Added {role} message to conversation {conversation_id}")
        return message
    
    async def get_recent_messages(
        self,
        db: AsyncSession,
        conversation_id: str,
        limit: int = MAX_CONTEXT_MESSAGES,
    ) -> list[Message]:
        """
        Get recent messages from a conversation.
        
        Args:
            db: Database session
            conversation_id: Conversation ID
            limit: Maximum number of messages to return
            
        Returns:
            List of Message objects (oldest first)
        """
        try:
            conv_uuid = UUID(conversation_id) if isinstance(conversation_id, str) else conversation_id
        except (ValueError, TypeError):
            return []
        
        query = (
            select(Message)
            .where(Message.conversation_id == conv_uuid)
            .order_by(desc(Message.created_at))
            .limit(limit)
        )
        
        result = await db.execute(query)
        messages = result.scalars().all()
        
        return list(reversed(messages))
    
    @trace_span("memory.get_context_for_llm", attributes={"component": "conversation_memory"})
    async def get_context_for_llm(
        self,
        db: AsyncSession,
        conversation_id: str,
        max_messages: int = MAX_CONTEXT_MESSAGES,
        include_summary: bool = True,
    ) -> dict[str, Any]:
        """
        Build context for LLM prompt from conversation history.
        
        Returns a dict with:
        - messages: List of messages in LLM format
        - summary: Latest conversation summary (if available)
        - context_type: Type of conversation
        - context_id: Related entity ID
        
        Args:
            db: Database session
            conversation_id: Conversation ID
            max_messages: Maximum messages to include
            include_summary: Whether to include summary
            
        Returns:
            Context dict for LLM
        """
        conversation = await self.get_conversation(
            db, conversation_id,
            include_messages=True,
            include_summaries=include_summary
        )
        
        if not conversation:
            return {
                "messages": [],
                "summary": None,
                "context_type": "general",
                "context_id": None,
            }
        
        messages = conversation.messages[-max_messages:] if conversation.messages else []
        
        llm_messages = [msg.to_llm_format() for msg in messages]
        
        summary = None
        if include_summary and conversation.summaries:
            latest_summary = conversation.summaries[0]
            summary = latest_summary.summary
        elif conversation.summary:
            summary = conversation.summary
        
        return {
            "messages": llm_messages,
            "summary": summary,
            "context_type": conversation.context_type,
            "context_id": conversation.context_id,
            "title": conversation.title,
            "metadata": conversation.conversation_metadata,
        }
    
    async def get_context_summary(
        self,
        db: AsyncSession,
        conversation_id: str,
    ) -> str | None:
        """
        Get the latest summary for a conversation.
        
        Args:
            db: Database session
            conversation_id: Conversation ID
            
        Returns:
            Summary text or None
        """
        conversation = await self.get_conversation(
            db, conversation_id,
            include_summaries=True
        )
        
        if not conversation:
            return None
        
        if conversation.summaries:
            return conversation.summaries[0].summary
        
        return conversation.summary
    
    async def update_summary(
        self,
        db: AsyncSession,
        conversation_id: str,
        force: bool = False,
    ) -> str | None:
        """
        Generate and update conversation summary using LLM.
        
        Args:
            db: Database session
            conversation_id: Conversation ID
            force: Force summary update even if not needed
            
        Returns:
            Generated summary or None
        """
        conversation = await self.get_conversation(
            db, conversation_id,
            include_messages=True
        )
        
        if not conversation:
            return None
        
        if not force and not self._should_generate_summary(conversation):
            return conversation.summary
        
        messages = conversation.messages or []
        if len(messages) < 3:
            return None
        
        summary_text = await self._generate_summary(messages)
        
        if summary_text:
            summary = ConversationSummary(
                conversation_id=conversation.id,
                summary=summary_text,
                message_count=len(messages),
                messages_start_id=messages[0].id if messages else None,
                messages_end_id=messages[-1].id if messages else None,
            )
            # TENANT-EXEMPT: conversation_memory queries user-scoped messages (user_id authoritative), not company-scoped row data
            db.add(summary)
            
            await db.execute(
                # TENANT-EXEMPT: conversation_memory queries user-scoped messages (user_id authoritative), not company-scoped row data
                update(Conversation)
                .where(Conversation.id == conversation.id)
                .values(
                    summary=summary_text,
                    last_summary_at_count=len(messages)
                )
            )
            
            await db.flush()
            logger.info(f"📊 Generated summary for conversation {conversation_id}")
        
        return summary_text
    
    async def get_user_conversations(
        self,
        db: AsyncSession,
        user_id: str,
        context_type: str | None = None,
        include_archived: bool = False,
        limit: int = 10,
        offset: int = 0,
    ) -> list[Conversation]:
        """
        Get conversations for a user.
        
        Args:
            db: Database session
            user_id: User ID
            context_type: Optional filter by context type
            include_archived: Include archived conversations
            limit: Maximum results
            offset: Pagination offset
            
        Returns:
            List of Conversation objects
        """
        conditions = [Conversation.user_id == user_id]
        
        if context_type:
            conditions.append(Conversation.context_type == context_type)
        
        # TENANT-EXEMPT: conversation_memory queries user-scoped messages (user_id authoritative), not company-scoped row data
        if not include_archived:
            conditions.append(not Conversation.is_archived)
        
        query = (
            # TENANT-EXEMPT: conversation_memory queries user-scoped messages (user_id authoritative), not company-scoped row data
            select(Conversation)
            .where(and_(*conditions))
            .order_by(desc(Conversation.updated_at))
            .limit(limit)
            .offset(offset)
        )
        
        result = await db.execute(query)
        return list(result.scalars().all())
    
    async def archive_conversation(
        self,
        db: AsyncSession,
        conversation_id: str,
    ) -> bool:
        """
        Archive a conversation.
        
        Args:
            db: Database session
            conversation_id: Conversation ID
            
        Returns:
            True if successful
        """
        try:
            # TENANT-EXEMPT: conversation_memory queries user-scoped messages (user_id authoritative), not company-scoped row data
            conv_uuid = UUID(conversation_id) if isinstance(conversation_id, str) else conversation_id
        except (ValueError, TypeError):
            return False
        
        await db.execute(
            # TENANT-EXEMPT: conversation_memory queries user-scoped messages (user_id authoritative), not company-scoped row data
            update(Conversation)
            .where(Conversation.id == conv_uuid)
            .values(
                is_archived=True,
                is_active=False,
                status="archived",
                updated_at=datetime.utcnow()
            )
        )
        
        await db.flush()
        logger.info(f"📁 Archived conversation {conversation_id}")
        return True
    
    async def delete_conversation(
        self,
        db: AsyncSession,
        conversation_id: str,
        company_id: str | None = None,
    ) -> bool:
        """
        Delete a conversation and all its messages.

        Args:
            db: Database session
            conversation_id: Conversation ID
            company_id: When provided, enforces tenant isolation — prevents IDOR delete.

        Returns:
            True if successful, False if not found or wrong tenant.
        """
        try:
            conv_uuid = UUID(conversation_id) if isinstance(conversation_id, str) else conversation_id
        except (ValueError, TypeError):
            return False

        # Tenant check before destructive operation
        if company_id:
            conv = await self.get_conversation(db, conversation_id, company_id=company_id)
            if conv is None:
                logger.warning("delete_conversation: tenant mismatch or not found — %s / %s", conversation_id, company_id)
                return False
        
        await db.execute(
            delete(ConversationSummary)
            .where(ConversationSummary.conversation_id == conv_uuid)
        )
        
        # ADR-001-EXEMPT: Rails-owned Message table — conversation lifecycle cleanup (cascade delete)
        await db.execute(
            delete(Message)
            .where(Message.conversation_id == conv_uuid)
        )
        
        await db.execute(
            delete(Conversation)
            .where(Conversation.id == conv_uuid)
        )
        
        await db.flush()
        logger.info(f"🗑️ Deleted conversation {conversation_id}")
        return True
    
    async def clear_conversation(
        self,
        db: AsyncSession,
        conversation_id: str,
    ) -> bool:
        """
        Clear all messages from a conversation (reset).
        
        Args:
            db: Database session
            conversation_id: Conversation ID
            
        Returns:
            True if successful
        """
        try:
            conv_uuid = UUID(conversation_id) if isinstance(conversation_id, str) else conversation_id
        except (ValueError, TypeError):
            return False
        
        await db.execute(
            delete(ConversationSummary)
            .where(ConversationSummary.conversation_id == conv_uuid)
        )
        
        # TENANT-EXEMPT: conversation_memory queries user-scoped messages (user_id authoritative), not company-scoped row data
        # ADR-001-EXEMPT: Rails-owned Message table — conversation reset (clear history, preserve Conversation metadata)
        await db.execute(
            delete(Message)
            .where(Message.conversation_id == conv_uuid)
        )
        
        await db.execute(
            # TENANT-EXEMPT: conversation_memory queries user-scoped messages (user_id authoritative), not company-scoped row data
            update(Conversation)
            .where(Conversation.id == conv_uuid)
            .values(
                message_count=0,
                summary=None,
                last_summary_at_count=0,
                updated_at=datetime.utcnow()
            )
        )
        
        await db.flush()
        logger.info(f"🔄 Cleared conversation {conversation_id}")
        return True
    
    def _should_generate_summary(self, conversation: Conversation) -> bool:
        """Check if summary should be generated based on message count."""
        if not conversation.message_count:
            return False
        
        messages_since_summary = conversation.message_count - (conversation.last_summary_at_count or 0)
        return messages_since_summary >= SUMMARY_TRIGGER_COUNT
    
    async def _trigger_summary_generation(
        self,
        db: AsyncSession,
        conversation: Conversation,
    ) -> None:
        """Trigger async summary generation."""
        try:
            await self.update_summary(db, str(conversation.id))
        except Exception as e:
            logger.warning(f"Summary generation failed: {e}")
    
    async def _generate_summary(self, messages: list[Message]) -> str | None:
        """
        Generate a summary of messages using LLM.
        
        Args:
            messages: List of messages to summarize
            
        Returns:
            Summary text
        """
        if not self.llm_service:
            return self._generate_simple_summary(messages)
        
        try:
            messages_text = "\n".join([
                f"{msg.role}: {msg.content[:500]}"
                for msg in messages[-30:]
            ])
            
            prompt = f"""Resuma esta conversa de forma concisa, destacando:
1. Principais tópicos discutidos
2. Decisões ou ações tomadas
3. Preferências do usuário identificadas
4. Contexto importante para futuras interações

Conversa:
{messages_text}

Resumo (máximo 200 palavras):"""

            return await self.llm_service.safe_invoke(prompt, provider="claude")
            
        except Exception as e:
            logger.error(f"LLM summary generation failed: {e}")
            return self._generate_simple_summary(messages)
    
    def _generate_simple_summary(self, messages: list[Message]) -> str:
        """Generate a simple summary without LLM."""
        user_messages = [m for m in messages if m.role in ("user", "human")]
        
        topics = set()
        for msg in user_messages[:10]:
            words = msg.content.lower().split()[:5]
            topics.update(words)
        
        intents = [m.intent for m in messages if m.intent]
        unique_intents = list(set(intents))[:5]
        
        summary_parts = []
        summary_parts.append(f"Conversa com {len(messages)} mensagens.")
        
        if unique_intents:
            summary_parts.append(f"Intenções detectadas: {', '.join(unique_intents)}.")
        
        return " ".join(summary_parts)
    
    async def summarize_history(
        self,
        messages: list[dict],
        max_messages: int = None
    ) -> dict[str, Any]:
        """
        Summariza histórico longo mantendo últimas N mensagens.
        
        Args:
            messages: Lista de mensagens no formato dict (role, content)
            max_messages: Número de mensagens recentes a manter (default: config)
            
        Returns:
            {
                "summary": "Resumo do histórico anterior...",
                "recent_messages": [...últimas N mensagens...],
                "total_messages": X,
                "summarized_count": Y
            }
        """
        if max_messages is None:
            max_messages = CONTEXT_COMPRESSION_CONFIG["keep_recent_messages"]
        
        total_messages = len(messages)
        
        if total_messages <= max_messages:
            return {
                "summary": None,
                "recent_messages": messages,
                "total_messages": total_messages,
                "summarized_count": 0
            }
        
        messages_to_summarize = messages[:-max_messages]
        recent_messages = messages[-max_messages:]
        summarized_count = len(messages_to_summarize)
        
        summary = await self._generate_summary_from_dicts(messages_to_summarize)
        
        return {
            "summary": summary,
            "recent_messages": recent_messages,
            "total_messages": total_messages,
            "summarized_count": summarized_count
        }
    
    def _extract_structured_ids(self, messages: list[dict]) -> str:
        """Extract structured IDs (UUIDs, labeled refs, long numerics) from messages.

        Returns a comma-separated string of found IDs, or "" if none found.
        Labeled references (e.g. "vaga 1776373052020", "candidato 42") are kept
        intact; the numeric portion is not duplicated as a standalone entry.
        """
        import re as _re
        if not messages:
            return ""

        content = " ".join(str(m.get("content", "")) for m in messages)

        # Labeled reference patterns (Brazilian Portuguese)
        LABELED_PATTERNS = [
            r"vaga\s+[\w\-]+",
            r"candidato\s+[\w\-]+",
            r"job\s+[\w\-]+",
            r"empresa\s+[\w\-]+",
            r"processo\s+[\w\-]+",
            r"ticket\s+[\w\-]+",
        ]
        UUID_PATTERN = r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"
        LONG_NUMERIC = r"\b\d{8,}\b"

        found: list[str] = []
        labeled_nums: set[str] = set()

        # Collect labeled refs first
        for pat in LABELED_PATTERNS:
            for m in _re.finditer(pat, content, _re.IGNORECASE):
                match_text = m.group(0)
                found.append(match_text)
                # Track numerics inside labels to avoid duplication
                for num in _re.findall(r"\d{5,}", match_text):
                    labeled_nums.add(num)

        # Collect UUIDs
        for m in _re.finditer(UUID_PATTERN, content, _re.IGNORECASE):
            uid = m.group(0)
            found.append(uid)
            labeled_nums.add(uid)

        # Collect long standalone numerics not already in a labeled ref
        for m in _re.finditer(LONG_NUMERIC, content):
            num = m.group(0)
            if num not in labeled_nums:
                found.append(num)
                labeled_nums.add(num)

        if not found:
            return ""

        # Deduplicate while preserving order
        seen: set[str] = set()
        unique: list[str] = []
        for item in found:
            key = item.lower()
            if key not in seen:
                seen.add(key)
                unique.append(item)

        return ", ".join(unique)

    async def _generate_summary_from_dicts(self, messages: list[dict]) -> str:
        """
        Generate summary from dict-format messages.

        Prepends ``[IDs preservados: ...]`` to the summary so downstream
        context windows retain references to structured IDs even after
        compression.

        Args:
            messages: List of message dicts with role/content

        Returns:
            Summary text (may start with [IDs preservados: ...] prefix)
        """
        if not messages:
            return ""

        structured_ids = self._extract_structured_ids(messages)

        def _prefix(body: str) -> str:
            if structured_ids:
                return f"[IDs preservados: {structured_ids}]\n{body}"
            return body

        if not self.llm_service:
            return _prefix(self._generate_simple_summary_from_dicts(messages))

        try:
            messages_text = "\n".join([
                f"{msg.get('role', 'unknown')}: {str(msg.get('content', ''))[:500]}"
                for msg in messages[-30:]
            ])

            max_tokens = CONTEXT_COMPRESSION_CONFIG["summary_max_tokens"]
            max_words = max_tokens // 2

            prompt = f"""Resuma esta conversa de forma concisa em no máximo {max_words} palavras, destacando:
1. Principais tópicos discutidos
2. Decisões ou ações tomadas
3. Preferências do usuário identificadas
4. Contexto importante para futuras interações

Conversa:
{messages_text}

Resumo conciso:"""

            llm_result = await self.llm_service.safe_invoke(prompt, provider="claude")
            return _prefix(llm_result)

        except Exception as e:
            logger.error(f"LLM summary generation from dicts failed: {e}")
            return _prefix(self._generate_simple_summary_from_dicts(messages))
    
    def _generate_simple_summary_from_dicts(self, messages: list[dict]) -> str:
        """Generate a simple summary from dict-format messages without LLM."""
        user_messages = [
            m for m in messages 
            if m.get("role") in ("user", "human")
        ]
        
        topics = set()
        for msg in user_messages[:10]:
            content = str(msg.get("content", ""))
            words = content.lower().split()[:5]
            topics.update(words)
        
        summary_parts = [f"Conversa com {len(messages)} mensagens anteriores."]
        
        if topics:
            topic_list = list(topics)[:10]
            summary_parts.append(f"Tópicos: {', '.join(topic_list)}.")
        
        return " ".join(summary_parts)
    
    async def get_compressed_context(
        self,
        db: AsyncSession,
        conversation_id: str,
        max_tokens: int = None
    ) -> str:
        """
        Retorna contexto comprimido para prompt.
        
        - Se histórico curto: retorna completo
        - Se histórico longo: resumo + últimas mensagens
        
        Args:
            db: Database session
            conversation_id: Conversation ID
            max_tokens: Maximum tokens for context (default: config)
            
        Returns:
            Compressed context string for LLM prompt
        """
        if max_tokens is None:
            max_tokens = CONTEXT_COMPRESSION_CONFIG["total_context_max_tokens"]
        
        max_before_summarize = CONTEXT_COMPRESSION_CONFIG["max_messages_before_summarize"]
        keep_recent = CONTEXT_COMPRESSION_CONFIG["keep_recent_messages"]
        
        messages = await self.get_recent_messages(
            db, 
            conversation_id, 
            limit=MAX_CONTEXT_MESSAGES
        )
        
        if not messages:
            return ""
        
        if len(messages) <= max_before_summarize:
            context_parts = []
            for msg in messages:
                role = msg.role.upper()
                content = msg.content
                context_parts.append(f"[{role}]: {content}")
            
            context = "\n".join(context_parts)
            return self._truncate_to_tokens(context, max_tokens)
        
        messages_dicts = [msg.to_llm_format() for msg in messages]
        
        compressed = await self.summarize_history(
            messages_dicts, 
            max_messages=keep_recent
        )
        
        context_parts = []
        
        if compressed["summary"]:
            context_parts.append(f"[RESUMO DO HISTÓRICO ANTERIOR ({compressed['summarized_count']} mensagens)]:")
            context_parts.append(compressed["summary"])
            context_parts.append("")
            context_parts.append("[MENSAGENS RECENTES]:")
        
        for msg in compressed["recent_messages"]:
            role = msg.get("role", "unknown").upper()
            content = msg.get("content", "")
            context_parts.append(f"[{role}]: {content}")
        
        context = "\n".join(context_parts)
        return self._truncate_to_tokens(context, max_tokens)
    
    def _truncate_to_tokens(self, text: str, max_tokens: int) -> str:
        """
        Truncate text to approximate token limit.
        
        Uses rough estimate of ~4 chars per token for Portuguese.
        
        Args:
            text: Text to truncate
            max_tokens: Maximum tokens allowed
            
        Returns:
            Truncated text
        """
        max_chars = max_tokens * 4
        
        if len(text) <= max_chars:
            return text
        
        truncated = text[:max_chars]
        
        last_newline = truncated.rfind('\n')
        if last_newline > max_chars * 0.8:
            truncated = truncated[:last_newline]
        
        truncated += "\n[...contexto truncado...]"
        
        logger.debug(f"📝 Context truncated from {len(text)} to {len(truncated)} chars")
        return truncated
    
    def _estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for text.
        
        Uses rough estimate of ~4 chars per token for Portuguese.
        
        Args:
            text: Text to estimate
            
        Returns:
            Estimated token count
        """
        return len(text) // 4


conversation_memory = ConversationMemory()
