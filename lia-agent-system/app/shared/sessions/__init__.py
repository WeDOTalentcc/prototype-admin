"""Canonical session helpers shared across transports (WS, SSE, REST)."""
from app.shared.sessions.thread_id import derive_thread_id, is_wizard_session_active

__all__ = ["derive_thread_id", "is_wizard_session_active"]
