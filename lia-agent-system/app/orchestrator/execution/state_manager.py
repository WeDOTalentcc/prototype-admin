"""
State Manager - Manages conversation state across agents with persistent storage.

Provides shared memory store for:
- Conversation history (with DB persistence)
- Agent execution state
- Intermediate results
- Cross-agent context
"""

import logging
import uuid
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


class StateManager:
    """
    Manages shared state across multiple agents in a conversation.
    
    Uses in-memory cache for fast access with periodic persistence
    to database via ConversationMemory service.
    """
    
    def __init__(self, db_service=None, conversation_memory=None):
        """
        Initialize State Manager.
        
        Args:
            db_service: Optional database service for persistence
            conversation_memory: Optional ConversationMemory service
        """
        self.db = db_service
        self.conversation_memory = conversation_memory
        self.state_store: dict[str, dict[str, Any]] = {}

        # LIA-M05: Warn if in-memory fallback is used in production
        import os
        if os.getenv("ENVIRONMENT", "development") == "production":
            logger.warning(
                "[LIA-M05] StateManager using in-memory dict fallback in PRODUCTION. "
                "State will be lost on restart. Ensure Redis is configured."
            )
        
    def set_conversation_memory(self, conversation_memory):
        """Set the ConversationMemory service for persistent storage."""
        self.conversation_memory = conversation_memory
        
    def create_conversation(self, user_id: str, initial_message: str) -> str:
        """
        Create new conversation state.
        
        Args:
            user_id: User initiating conversation
            initial_message: First message in conversation
            
        Returns:
            conversation_id: Unique identifier for conversation
        """
        conversation_id = str(uuid.uuid4())
        
        self.state_store[conversation_id] = {
            "user_id": user_id,
            "created_at": datetime.now().isoformat(),
            "messages": [{
                "role": "user",
                "content": initial_message,
                "timestamp": datetime.now().isoformat()
            }],
            "agent_results": {},
            "current_plan": None,
            "execution_status": "initialized",
            "context_type": "general",
            "context_id": None,
        }
        
        logger.info(f"🆕 Conversation created: {conversation_id}")
        return conversation_id
    
    def create_conversation_with_context(
        self,
        user_id: str,
        initial_message: str,
        context_type: str = "general",
        context_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """
        Create new conversation state with context information.
        
        Args:
            user_id: User initiating conversation
            initial_message: First message in conversation
            context_type: Type of conversation (job_chat, talent_chat, etc.)
            context_id: Related entity ID (job_id, candidate_id, etc.)
            metadata: Additional metadata
            
        Returns:
            conversation_id: Unique identifier for conversation
        """
        conversation_id = str(uuid.uuid4())
        
        self.state_store[conversation_id] = {
            "user_id": user_id,
            "created_at": datetime.now().isoformat(),
            "messages": [{
                "role": "user",
                "content": initial_message,
                "timestamp": datetime.now().isoformat()
            }],
            "agent_results": {},
            "current_plan": None,
            "execution_status": "initialized",
            "context_type": context_type,
            "context_id": context_id,
            "metadata": metadata or {},
        }
        
        logger.info(f"🆕 Conversation created with context: {conversation_id} ({context_type})")
        return conversation_id
    
    def get_state(self, conversation_id: str) -> dict[str, Any] | None:
        """Get current state for conversation."""
        return self.state_store.get(conversation_id)
    
    def update_state(
        self, 
        conversation_id: str,
        updates: dict[str, Any]
    ):
        """
        Update conversation state.
        
        Args:
            conversation_id: Conversation to update
            updates: Dict of state updates
        """
        if conversation_id not in self.state_store:
            logger.warning(f"⚠️  Conversation not found: {conversation_id}")
            return
        
        state = self.state_store[conversation_id]
        state.update(updates)
        state["updated_at"] = datetime.now().isoformat()
        
        logger.debug(f"🔄 State updated for {conversation_id}")
    
    def add_message(
        self, 
        conversation_id: str,
        role: str,
        content: str,
        metadata: dict[str, Any] | None = None
    ):
        """Add message to conversation history."""
        if conversation_id not in self.state_store:
            self.state_store[conversation_id] = {
                "messages": [],
                "agent_results": {},
                "execution_status": "active",
            }
        
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        }
        
        if metadata:
            message["metadata"] = metadata
        
        self.state_store[conversation_id]["messages"].append(message)
        self.state_store[conversation_id]["updated_at"] = datetime.now().isoformat()
    
    def store_agent_result(
        self, 
        conversation_id: str,
        agent_name: str,
        result: Any
    ):
        """
        Store result from agent execution.
        
        Args:
            conversation_id: Conversation ID
            agent_name: Name of agent that produced result
            result: Result data from agent
        """
        if conversation_id not in self.state_store:
            logger.warning(f"⚠️  Conversation not found: {conversation_id}")
            return
        
        state = self.state_store[conversation_id]
        state["agent_results"][agent_name] = {
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
        
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.info(f"💾 Agent result stored: {agent_name}")
    
    def get_agent_result(
        self, 
        conversation_id: str,
        agent_name: str
    ) -> Any | None:
        """Retrieve result from specific agent."""
        state = self.get_state(conversation_id)
        if not state:
            return None
        
        agent_data = state.get("agent_results", {}).get(agent_name)
        return agent_data.get("result") if agent_data else None
    
    def get_conversation_history(
        self, 
        conversation_id: str,
        limit: int = 20
    ) -> list[dict[str, Any]]:
        """Get recent conversation messages."""
        state = self.get_state(conversation_id)
        if not state:
            return []
        
        messages = state.get("messages", [])
        return messages[-limit:]
    
    def get_context_info(self, conversation_id: str) -> dict[str, Any]:
        """Get context information for a conversation."""
        state = self.get_state(conversation_id)
        if not state:
            return {}
        
        return {
            "context_type": state.get("context_type", "general"),
            "context_id": state.get("context_id"),
            "metadata": state.get("metadata", {}),
            "last_agent": state.get("last_agent"),
            "current_job": state.get("current_job"),
            "current_candidate": state.get("current_candidate"),
        }
    
    def cleanup_conversation(self, conversation_id: str):
        """Remove conversation from memory (after persistence)."""
        if conversation_id in self.state_store:
            del self.state_store[conversation_id]
            logger.info(f"🗑️  Conversation cleaned up: {conversation_id}")
    
    def clear_state(self, conversation_id: str):
        """Clear state for a conversation (restart flow)."""
        if conversation_id in self.state_store:
            user_id = self.state_store[conversation_id].get("user_id")
            context_type = self.state_store[conversation_id].get("context_type", "general")
            context_id = self.state_store[conversation_id].get("context_id")
            
            self.state_store[conversation_id] = {
                "user_id": user_id,
                "created_at": self.state_store[conversation_id].get("created_at"),
                "messages": [],
                "agent_results": {},
                "current_plan": None,
                "execution_status": "restarted",
                "restarted_at": datetime.now().isoformat(),
                "context_type": context_type,
                "context_id": context_id,
            }
            logger.info(f"🔄 State cleared for: {conversation_id}")
    
    def load_from_db(self, conversation_id: str, conversation_data: dict[str, Any]):
        """
        Load conversation state from database.
        
        Args:
            conversation_id: Conversation ID
            conversation_data: Data from ConversationMemory
        """
        self.state_store[conversation_id] = {
            "user_id": conversation_data.get("user_id"),
            "created_at": conversation_data.get("created_at"),
            "messages": conversation_data.get("messages", []),
            "agent_results": {},
            "current_plan": None,
            "execution_status": "loaded",
            "context_type": conversation_data.get("context_type", "general"),
            "context_id": conversation_data.get("context_id"),
            "metadata": conversation_data.get("metadata", {}),
            "summary": conversation_data.get("summary"),
        }
        logger.info(f"📂 Loaded conversation from DB: {conversation_id}")
    
    def get_summary(self, conversation_id: str) -> str | None:
        """Get conversation summary if available."""
        state = self.get_state(conversation_id)
        if not state:
            return None
        return state.get("summary")
    
    def set_summary(self, conversation_id: str, summary: str):
        """Set conversation summary."""
        if conversation_id in self.state_store:
            self.state_store[conversation_id]["summary"] = summary
            logger.info(f"📊 Summary updated for: {conversation_id}")
    
    def get_all_active_conversations(self) -> list[str]:
        """Get list of all active conversation IDs in memory."""
        return list(self.state_store.keys())
    
    def get_conversations_by_user(self, user_id: str) -> list[str]:
        """Get conversation IDs for a specific user."""
        return [
            conv_id for conv_id, state in self.state_store.items()
            if state.get("user_id") == user_id
        ]
