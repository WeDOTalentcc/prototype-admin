"""Canonical session helpers shared across transports (WS, SSE, REST)."""
from app.shared.sessions.thread_id import (
    derive_thread_id,
    is_wizard_session_active,
    is_greeting_only,
    should_pin_to_wizard,
)

__all__ = [
    "derive_thread_id",
    "is_wizard_session_active",
    "is_greeting_only",
    "should_pin_to_wizard",
]
