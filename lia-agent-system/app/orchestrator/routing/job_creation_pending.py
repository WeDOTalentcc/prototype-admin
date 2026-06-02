"""Pending job-creation disambiguation store (Task #1204).

When :func:`decide_job_creation` returns ``action="clarify"``, the orchestrator
asks the recruiter which path they want and stores a lightweight record here,
keyed by conversation/session id. On the next turn the orchestrator classifies
the recruiter's free-text reply against this pending record.

Intentionally **separate** from ``pending_action_store`` (Phase 0): that store is
consumed by the ActionExecutor confirmation/param flow, which would mis-handle a
disambiguation record. This is a transient, single-turn hand-off, so an in-memory
L1 cache with a short TTL is sufficient (mirrors the in-memory layer of
``PendingActionStore``).
"""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from datetime import datetime, timedelta


@dataclass
class PendingJobCreation:
    conversation_id: str
    original_message: str
    option_paths: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: datetime = field(
        default_factory=lambda: datetime.utcnow() + timedelta(minutes=5)
    )
    reasked: bool = False

    @property
    def is_expired(self) -> bool:
        return datetime.utcnow() > self.expires_at


class PendingJobCreationStore:
    def __init__(self) -> None:
        self._store: dict[str, PendingJobCreation] = {}
        self._lock = threading.Lock()

    def get(self, conversation_id: str) -> PendingJobCreation | None:
        with self._lock:
            state = self._store.get(conversation_id)
            if state and state.is_expired:
                del self._store[conversation_id]
                return None
            return state

    def save(self, conversation_id: str, state: PendingJobCreation) -> None:
        with self._lock:
            self._store[conversation_id] = state

    def remove(self, conversation_id: str) -> None:
        with self._lock:
            self._store.pop(conversation_id, None)


pending_job_creation_store = PendingJobCreationStore()
