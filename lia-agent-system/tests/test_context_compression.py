"""
Tests for Context Compression and History Summarization.

Tests the CONTEXT_COMPRESSION_CONFIG, summarize_history, and get_compressed_context
methods in ConversationMemory.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.domains.recruiter_assistant.services.conversation_memory import (
    ConversationMemory,
    CONTEXT_COMPRESSION_CONFIG,
    MAX_CONTEXT_MESSAGES
)


class TestContextCompressionConfig:
    """Tests for CONTEXT_COMPRESSION_CONFIG settings."""
    
    def test_config_has_required_keys(self):
        """Test that config has all required keys."""
        assert "max_messages_before_summarize" in CONTEXT_COMPRESSION_CONFIG
        assert "keep_recent_messages" in CONTEXT_COMPRESSION_CONFIG
        assert "summary_max_tokens" in CONTEXT_COMPRESSION_CONFIG
        assert "total_context_max_tokens" in CONTEXT_COMPRESSION_CONFIG
    
    def test_config_values_are_valid(self):
        """Test that config values are sensible."""
        assert CONTEXT_COMPRESSION_CONFIG["max_messages_before_summarize"] == 10
        assert CONTEXT_COMPRESSION_CONFIG["keep_recent_messages"] == 5
        assert CONTEXT_COMPRESSION_CONFIG["summary_max_tokens"] == 500
        assert CONTEXT_COMPRESSION_CONFIG["total_context_max_tokens"] == 2000
    
    def test_keep_recent_less_than_max_before_summarize(self):
        """Test that keep_recent is less than max_before_summarize."""
        assert CONTEXT_COMPRESSION_CONFIG["keep_recent_messages"] < \
               CONTEXT_COMPRESSION_CONFIG["max_messages_before_summarize"]


class TestSummarizeHistory:
    """Tests for summarize_history method."""
    
    @pytest.fixture
    def memory(self):
        """Create ConversationMemory instance without LLM service."""
        return ConversationMemory(llm_service=None)
    
    @pytest.fixture
    def short_messages(self):
        """Create a short message list (under threshold)."""
        return [
            {"role": "user", "content": "Olá"},
            {"role": "assistant", "content": "Oi! Como posso ajudar?"},
            {"role": "user", "content": "Quero ver vagas"},
        ]
    
    @pytest.fixture
    def long_messages(self):
        """Create a long message list (over threshold)."""
        messages = []
        for i in range(15):
            messages.append({"role": "user", "content": f"Mensagem do usuário {i}"})
            messages.append({"role": "assistant", "content": f"Resposta {i}"})
        return messages
    
    @pytest.mark.asyncio
    async def test_short_history_no_summarization(self, memory, short_messages):
        """Test that short history is not summarized."""
        result = await memory.summarize_history(short_messages)
        
        assert result["summary"] is None
        assert result["recent_messages"] == short_messages
        assert result["total_messages"] == 3
        assert result["summarized_count"] == 0
    
    @pytest.mark.asyncio
    async def test_long_history_is_summarized(self, memory, long_messages):
        """Test that long history is summarized."""
        result = await memory.summarize_history(long_messages)
        
        assert result["summary"] is not None
        assert len(result["recent_messages"]) == 5
        assert result["total_messages"] == 30
        assert result["summarized_count"] == 25
    
    @pytest.mark.asyncio
    async def test_custom_max_messages(self, memory, long_messages):
        """Test summarization with custom max_messages."""
        result = await memory.summarize_history(long_messages, max_messages=10)
        
        assert len(result["recent_messages"]) == 10
        assert result["summarized_count"] == 20
    
    @pytest.mark.asyncio
    async def test_empty_messages(self, memory):
        """Test handling of empty message list."""
        result = await memory.summarize_history([])
        
        assert result["summary"] is None
        assert result["recent_messages"] == []
        assert result["total_messages"] == 0
        assert result["summarized_count"] == 0
    
    @pytest.mark.asyncio
    async def test_exact_threshold_messages(self, memory):
        """Test messages at exactly the threshold."""
        messages = [{"role": "user", "content": f"Msg {i}"} for i in range(5)]
        
        result = await memory.summarize_history(messages, max_messages=5)
        
        assert result["summary"] is None
        assert len(result["recent_messages"]) == 5
        assert result["summarized_count"] == 0
    
    @pytest.mark.asyncio
    async def test_summary_contains_topics(self, memory, long_messages):
        """Test that summary contains relevant topics."""
        result = await memory.summarize_history(long_messages)
        
        assert "mensagens" in result["summary"].lower()
    
    @pytest.mark.asyncio
    async def test_recent_messages_are_last_ones(self, memory, long_messages):
        """Test that recent_messages are the last ones."""
        result = await memory.summarize_history(long_messages, max_messages=5)
        
        assert result["recent_messages"] == long_messages[-5:]


class TestGetCompressedContext:
    """Tests for get_compressed_context method."""
    
    @pytest.fixture
    def memory(self):
        """Create ConversationMemory instance."""
        return ConversationMemory(llm_service=None)
    
    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        return AsyncMock()
    
    @pytest.fixture
    def mock_messages(self):
        """Create mock Message objects."""
        messages = []
        for i in range(15):
            msg = MagicMock()
            msg.role = "user" if i % 2 == 0 else "assistant"
            msg.content = f"Mensagem {i}"
            msg.to_llm_format = MagicMock(return_value={
                "role": msg.role,
                "content": msg.content
            })
            messages.append(msg)
        return messages
    
    @pytest.mark.asyncio
    async def test_empty_conversation_returns_empty_string(self, memory, mock_db):
        """Test that empty conversation returns empty string."""
        with patch.object(memory, 'get_recent_messages', return_value=[]):
            result = await memory.get_compressed_context(mock_db, str(uuid4()))
        
        assert result == ""
    
    @pytest.mark.asyncio
    async def test_short_conversation_returns_full_context(self, memory, mock_db):
        """Test that short conversation returns full context."""
        short_messages = []
        for i in range(5):
            msg = MagicMock()
            msg.role = "user" if i % 2 == 0 else "assistant"
            msg.content = f"Mensagem {i}"
            short_messages.append(msg)
        
        with patch.object(memory, 'get_recent_messages', return_value=short_messages):
            result = await memory.get_compressed_context(mock_db, str(uuid4()))
        
        assert "[USER]:" in result or "[ASSISTANT]:" in result
        assert "RESUMO" not in result
    
    @pytest.mark.asyncio
    async def test_long_conversation_includes_summary(self, memory, mock_db, mock_messages):
        """Test that long conversation includes summary."""
        with patch.object(memory, 'get_recent_messages', return_value=mock_messages):
            result = await memory.get_compressed_context(mock_db, str(uuid4()))
        
        assert "RESUMO DO HISTÓRICO ANTERIOR" in result
        assert "MENSAGENS RECENTES" in result
    
    @pytest.mark.asyncio
    async def test_custom_max_tokens(self, memory, mock_db, mock_messages):
        """Test compression with custom max_tokens."""
        with patch.object(memory, 'get_recent_messages', return_value=mock_messages):
            result = await memory.get_compressed_context(
                mock_db, 
                str(uuid4()), 
                max_tokens=100
            )
        
        assert len(result) <= 100 * 4 + 50


class TestTruncation:
    """Tests for text truncation functionality."""
    
    @pytest.fixture
    def memory(self):
        """Create ConversationMemory instance."""
        return ConversationMemory(llm_service=None)
    
    def test_truncate_short_text(self, memory):
        """Test that short text is not truncated."""
        text = "Short text"
        result = memory._truncate_to_tokens(text, 100)
        
        assert result == text
    
    def test_truncate_long_text(self, memory):
        """Test that long text is truncated."""
        text = "A" * 10000
        result = memory._truncate_to_tokens(text, 100)
        
        assert len(result) < 10000
        assert "[...contexto truncado...]" in result
    
    def test_estimate_tokens(self, memory):
        """Test token estimation."""
        text = "This is a test message"
        tokens = memory._estimate_tokens(text)
        
        assert tokens > 0
        assert tokens == len(text) // 4


class TestSimpleSummaryFromDicts:
    """Tests for simple summary generation from dict messages."""
    
    @pytest.fixture
    def memory(self):
        """Create ConversationMemory instance without LLM."""
        return ConversationMemory(llm_service=None)
    
    def test_empty_messages(self, memory):
        """Test summary of empty messages."""
        result = memory._generate_simple_summary_from_dicts([])
        
        assert "0 mensagens" in result
    
    def test_user_messages_extracted(self, memory):
        """Test that user messages are processed."""
        messages = [
            {"role": "user", "content": "vagas candidatos recrutamento"},
            {"role": "assistant", "content": "Posso ajudar"},
        ]
        
        result = memory._generate_simple_summary_from_dicts(messages)
        
        assert "mensagens" in result.lower()
    
    def test_handles_missing_content(self, memory):
        """Test handling of messages with missing content."""
        messages = [
            {"role": "user"},
            {"role": "assistant", "content": "Response"},
        ]
        
        result = memory._generate_simple_summary_from_dicts(messages)
        
        assert result is not None


class TestLLMSummaryGeneration:
    """Tests for LLM-based summary generation."""
    
    @pytest.fixture
    def mock_llm_service(self):
        """Create mock LLM service."""
        mock = MagicMock()
        mock.claude = MagicMock()
        mock.claude.ainvoke = AsyncMock(return_value=MagicMock(
            content="Resumo da conversa sobre vagas e candidatos."
        ))
        return mock
    
    @pytest.fixture
    def memory_with_llm(self, mock_llm_service):
        """Create ConversationMemory with mock LLM."""
        return ConversationMemory(llm_service=mock_llm_service)
    
    @pytest.mark.asyncio
    async def test_llm_summary_called(self, memory_with_llm, mock_llm_service):
        """Test that LLM is called for summary."""
        messages = [
            {"role": "user", "content": "Quero ver vagas"},
            {"role": "assistant", "content": "Claro, tenho 5 vagas"},
        ]
        
        result = await memory_with_llm._generate_summary_from_dicts(messages)
        
        mock_llm_service.claude.ainvoke.assert_called_once()
        assert "vagas" in result.lower() or "candidatos" in result.lower()
    
    @pytest.mark.asyncio
    async def test_llm_error_fallback(self, memory_with_llm, mock_llm_service):
        """Test fallback to simple summary on LLM error."""
        mock_llm_service.claude.ainvoke.side_effect = Exception("API Error")
        
        messages = [
            {"role": "user", "content": "Teste"},
        ]
        
        result = await memory_with_llm._generate_summary_from_dicts(messages)
        
        assert result is not None
        assert "mensagens" in result.lower()


class TestIntegration:
    """Integration tests for context compression."""
    
    @pytest.fixture
    def memory(self):
        """Create ConversationMemory instance."""
        return ConversationMemory(llm_service=None)
    
    @pytest.mark.asyncio
    async def test_full_compression_flow(self, memory):
        """Test complete compression flow."""
        messages = []
        for i in range(20):
            messages.append({
                "role": "user" if i % 2 == 0 else "assistant",
                "content": f"Mensagem número {i} sobre recrutamento"
            })
        
        result = await memory.summarize_history(messages)
        
        assert result["summary"] is not None
        assert len(result["recent_messages"]) == 5
        assert result["total_messages"] == 20
        assert result["summarized_count"] == 15
        
        context_parts = []
        if result["summary"]:
            context_parts.append(f"[RESUMO]: {result['summary']}")
        for msg in result["recent_messages"]:
            context_parts.append(f"[{msg['role'].upper()}]: {msg['content']}")
        
        context = "\n".join(context_parts)
        assert len(context) > 0
