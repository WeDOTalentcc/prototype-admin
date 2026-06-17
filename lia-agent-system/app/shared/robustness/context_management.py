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
from enum import Enum, StrEnum
from typing import Any


logger = logging.getLogger(__name__)


class ContextStatus(StrEnum):
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
    
    # Recovery Tri-2 (2026-05-23) — restaurar idempotency dual-ID canonical.
    # Removed silenciosamente pelo merge incident 02361f41c. idempotency.py:76
    # chama ``await ctx.generate_idempotency_key_async()`` mas o método havia
    # sumido daqui, causando 24 test failures em test_idempotency_dual_id.py
    # desde 2026-05-01 (W2-009 dual-ID idempotency broken).
    #
    # ID-shaped param keys → resolver method name on the adapter.
    #
    # Dual-ID entities accept both a fork UUID and a Rails bigint; without
    # canonicalization, an idempotent operation that retries with the other
    # ID format hashes to a different key and runs twice (ADR 003).
    #
    # Only entries whose resolver is actually implemented on `RailsAdapter`
    # are listed here — adding a key for which no resolver exists would be
    # dead weight that gives a false sense of coverage. Candidates, jobs
    # and applications all have `_resolve_rails_*_id` resolvers backed by
    # Rails' `fork_uuid` columns (ADR 003 / Task #479).
    _DUAL_ID_PARAM_RESOLVERS: dict[str, str] = {
        "candidate_id": "_resolve_rails_candidate_id",
        "candidate": "_resolve_rails_candidate_id",
        "job_id": "_resolve_rails_job_id",
        "vacancy_id": "_resolve_rails_job_id",
        # Task #486 — `update_job_vacancy` (and other vacancy CRUD routes)
        # spell the path param `job_vacancy_id`; without an entry here the
        # canonicalization branch silently no-ops and a UUID/bigint retry
        # hashes to two distinct keys.
        "job_vacancy_id": "_resolve_rails_job_id",
        "application_id": "_resolve_rails_application_id",
        "apply_id": "_resolve_rails_application_id",
    }

    @classmethod
    async def _canonicalize_params(
        cls,
        params: dict[str, Any],
        adapter: Any | None,
    ) -> dict[str, Any]:
        """Return a copy of `params` with dual-ID fields collapsed to the
        canonical Rails bigint when an adapter is provided. UUIDs that can't
        be resolved (no adapter, Rails offline, no `fork_uuid` row yet) are
        passed through verbatim so behavior matches the legacy hash for
        non-dual-ID params and unresolvable IDs."""
        if not params:
            return {}
        canonical: dict[str, Any] = dict(params)
        if adapter is None:
            return canonical
        for key, raw_value in params.items():
            resolver_name = cls._DUAL_ID_PARAM_RESOLVERS.get(key)
            if resolver_name is None or not isinstance(raw_value, str) or not raw_value:
                continue
            resolver = getattr(adapter, resolver_name, None)
            if not callable(resolver):
                continue
            try:
                rails_id = await resolver(raw_value)
            except Exception as exc:  # pragma: no cover - defensive
                logger.debug(
                    "Idempotency canonicalization: %s(%r) failed: %s",
                    resolver_name, raw_value, exc,
                )
                rails_id = None
            if rails_id is not None:
                canonical[key] = int(rails_id)
        return canonical

    def generate_idempotency_key(self, operation: str, params: dict[str, Any]) -> str:
        """Generate an idempotency key for an operation.

        This sync variant hashes the params verbatim. For dual-ID entities
        (currently candidates, jobs, applications), use
        :meth:`generate_idempotency_key_async` with a ``RailsAdapter`` so
        retries that switch between UUID and Rails bigint collapse to the
        same key.
        """
        key_data = {
            "session_id": self.session_id,
            "operation": operation,
            "params": sorted((params or {}).items())
        }
        key_str = json.dumps(key_data, sort_keys=True, default=str)
        return hashlib.sha256(key_str.encode()).hexdigest()[:16]

    async def generate_idempotency_key_async(
        self,
        operation: str,
        params: dict[str, Any],
        adapter: Any | None = None,
    ) -> str:
        """Async variant that canonicalizes dual-ID params via the adapter
        before hashing, so retries that switch between UUID and Rails bigint
        collapse to the same idempotency key (ADR 003).

        With ``adapter=None``, behavior is identical to the sync version.
        """
        canonical = await self._canonicalize_params(params or {}, adapter)
        key_data = {
            "session_id": self.session_id,
            "operation": operation,
            "params": sorted(canonical.items()),
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
