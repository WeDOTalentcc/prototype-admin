"""
Context Management - Handle conversation context, cancellation, and agent handoffs.

This module provides:
- Context persistence and versioning
- Mid-flow cancellation handling
- Agent handoff contracts
- Idempotency key management
"""
import hashlib
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any


logger = logging.getLogger(__name__)


class ContextStatus(str, Enum):
    """Status of a conversation context."""
    ACTIVE = "active"
    PAUSED = "paused"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    EXPIRED = "expired"


CANCELLATION_KEYWORDS = [
    "cancelar", "parar", "desistir", "esquecer", "não quero mais",
    "pare", "stop", "cancel", "abort", "nevermind", "deixa pra lá",
    "esquece", "volta", "sair", "encerrar", "finalizar", "acabou"
]

RESTART_KEYWORDS = [
    "recomeçar", "começar de novo", "restart", "reset", "do zero",
    "nova tentativa", "limpar", "apagar", "reiniciar"
]

CONFIRMATION_KEYWORDS = [
    "sim", "yes", "ok", "confirmo", "pode ser", "vamos", "isso",
    "correto", "exato", "certo", "confirmar", "aceito", "concordo"
]

DENIAL_KEYWORDS = [
    "não", "no", "nope", "errado", "incorreto", "negativo",
    "recuso", "discordo", "de jeito nenhum"
]


@dataclass
class HandoffContract:
    """Contract for data passed between agents during handoffs."""
    source_agent: str
    target_agent: str
    shared_data: dict[str, Any] = field(default_factory=dict)
    required_keys: list[str] = field(default_factory=list)
    optional_keys: list[str] = field(default_factory=list)
    ttl_seconds: int = 3600
    created_at: datetime = field(default_factory=datetime.utcnow)
    handoff_reason: str = ""
    
    def is_valid(self) -> bool:
        """Check if all required keys are present."""
        return all(key in self.shared_data for key in self.required_keys)
    
    def is_expired(self) -> bool:
        """Check if the handoff contract has expired."""
        return datetime.utcnow() > self.created_at + timedelta(seconds=self.ttl_seconds)
    
    def get_missing_keys(self) -> list[str]:
        """Get list of missing required keys."""
        return [key for key in self.required_keys if key not in self.shared_data]


STANDARD_HANDOFF_KEYS = {
    "job_context": ["job_id", "job_title", "job_requirements"],
    "candidate_context": ["candidate_id", "candidate_name", "candidate_email"],
    "interview_context": ["interview_id", "scheduled_at", "interview_type"],
    "wsi_context": ["wsi_score", "bloom_level", "dreyfus_level"],
    "user_context": ["user_id", "user_role", "company_id"],
}


@dataclass
class ContextSnapshot:
    """A snapshot of conversation context at a point in time."""
    version: int
    timestamp: datetime
    data: dict[str, Any]
    agent_type: str
    action: str
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "timestamp": self.timestamp.isoformat(),
            "data": self.data,
            "agent_type": self.agent_type,
            "action": self.action
        }


class ContextManager:
    """
    Manages conversation context with versioning and recovery.
    """
    
    def __init__(self, session_id: str, user_id: str):
        self.session_id = session_id
        self.user_id = user_id
        self.context: dict[str, Any] = {}
        self.status = ContextStatus.ACTIVE
        self.current_agent: str | None = None
        self.current_workflow: str | None = None
        self.workflow_step: int = 0
        self.snapshots: list[ContextSnapshot] = []
        self.version = 0
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self.idempotency_keys: set[str] = set()
    
    def update(self, key: str, value: Any, agent_type: str = "", action: str = "update") -> None:
        """Update a context value and create a snapshot."""
        self.version += 1
        self.context[key] = value
        self.updated_at = datetime.utcnow()
        
        self.snapshots.append(ContextSnapshot(
            version=self.version,
            timestamp=self.updated_at,
            data={key: value},
            agent_type=agent_type,
            action=action
        ))
        
        if len(self.snapshots) > 50:
            self.snapshots = self.snapshots[-50:]
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a context value."""
        return self.context.get(key, default)
    
    def set_workflow(self, workflow_name: str, initial_step: int = 0) -> None:
        """Set the current workflow."""
        self.current_workflow = workflow_name
        self.workflow_step = initial_step
        self.update("current_workflow", workflow_name, action="workflow_start")
    
    def advance_workflow(self) -> int:
        """Advance to the next workflow step."""
        self.workflow_step += 1
        return self.workflow_step
    
    def cancel(self, reason: str = "") -> None:
        """Cancel the current context/workflow."""
        self.status = ContextStatus.CANCELLED
        self.update("cancellation_reason", reason, action="cancel")
        logger.info(f"Context cancelled for session {self.session_id}: {reason}")
    
    def complete(self) -> None:
        """Mark the context as completed."""
        self.status = ContextStatus.COMPLETED
        self.update("completed_at", datetime.utcnow().isoformat(), action="complete")
    
    def rollback_to_version(self, target_version: int) -> bool:
        """Rollback context to a specific version."""
        if target_version < 1 or target_version > self.version:
            return False
        
        new_context = {}
        for snapshot in self.snapshots:
            if snapshot.version <= target_version:
                new_context.update(snapshot.data)
        
        self.context = new_context
        self.version = target_version
        logger.info(f"Context rolled back to version {target_version}")
        return True
    
    def check_idempotency(self, operation_key: str) -> bool:
        """
        Check if an operation has already been executed.
        
        Returns True if this is a new operation, False if duplicate.
        """
        if operation_key in self.idempotency_keys:
            logger.warning(f"Duplicate operation detected: {operation_key}")
            return False
        
        self.idempotency_keys.add(operation_key)
        return True
    
    def generate_idempotency_key(self, operation: str, params: dict[str, Any]) -> str:
        """Generate an idempotency key for an operation."""
        key_data = {
            "session_id": self.session_id,
            "operation": operation,
            "params": sorted(params.items())
        }
        key_str = json.dumps(key_data, sort_keys=True, default=str)
        return hashlib.sha256(key_str.encode()).hexdigest()[:16]
    
    def create_handoff(
        self,
        target_agent: str,
        shared_keys: list[str],
        reason: str = ""
    ) -> HandoffContract:
        """Create a handoff contract for passing context to another agent."""
        shared_data = {key: self.context.get(key) for key in shared_keys if key in self.context}
        
        return HandoffContract(
            source_agent=self.current_agent or "unknown",
            target_agent=target_agent,
            shared_data=shared_data,
            required_keys=[k for k in shared_keys if self.context.get(k) is not None],
            optional_keys=[k for k in shared_keys if self.context.get(k) is None],
            handoff_reason=reason
        )
    
    def to_dict(self) -> dict[str, Any]:
        """Serialize context for storage/transfer."""
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "context": self.context,
            "status": self.status.value,
            "current_agent": self.current_agent,
            "current_workflow": self.current_workflow,
            "workflow_step": self.workflow_step,
            "version": self.version,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }


class CancellationHandler:
    """
    Handles mid-flow cancellation requests.
    """
    
    @staticmethod
    def is_cancellation_request(message: str) -> bool:
        """Check if a message is a cancellation request."""
        message_lower = message.lower().strip()
        return any(keyword in message_lower for keyword in CANCELLATION_KEYWORDS)
    
    @staticmethod
    def is_restart_request(message: str) -> bool:
        """Check if a message is a restart request."""
        message_lower = message.lower().strip()
        return any(keyword in message_lower for keyword in RESTART_KEYWORDS)
    
    @staticmethod
    def is_confirmation(message: str) -> bool:
        """Check if a message is a confirmation."""
        message_lower = message.lower().strip()
        if any(denial in message_lower for denial in DENIAL_KEYWORDS):
            return False
        return any(keyword in message_lower for keyword in CONFIRMATION_KEYWORDS)
    
    @staticmethod
    def is_denial(message: str) -> bool:
        """Check if a message is a denial."""
        message_lower = message.lower().strip()
        return any(keyword in message_lower for keyword in DENIAL_KEYWORDS)
    
    @staticmethod
    def get_cancellation_response() -> str:
        """Get a user-friendly cancellation confirmation message."""
        return "Entendido! Cancelei a operação atual. Posso ajudar com outra coisa?"
    
    @staticmethod
    def get_restart_response() -> str:
        """Get a user-friendly restart confirmation message."""
        return "Ok, vamos recomeçar do início. O que você gostaria de fazer?"
    
    @staticmethod
    def handle_cancellation(context_manager: ContextManager, message: str) -> str | None:
        """
        Handle a potential cancellation/restart request.
        
        Returns a response message if handled, None otherwise.
        """
        if CancellationHandler.is_cancellation_request(message):
            context_manager.cancel(reason=message)
            return CancellationHandler.get_cancellation_response()
        
        if CancellationHandler.is_restart_request(message):
            context_manager.rollback_to_version(1)
            context_manager.status = ContextStatus.ACTIVE
            context_manager.workflow_step = 0
            return CancellationHandler.get_restart_response()
        
        return None
