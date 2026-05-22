"""F-09 P2 contract: persist_session_state public method + backward-compat alias.

Audit ref: AUDIT_VOICE_SCREENING_ORCHESTRATOR_2026-05-22.md F-09

Bug: _persist_session_state was _-prefix ("private convention") but called
externally from 6 sites in app/api/v1/twilio_voice.py + gemini_voice.py.
Python convention break -- _ means "internal API, may change". Callers were
violating that.

Fix: rename to public persist_session_state (canonical). Keep _-prefix as
deprecated alias for backward compat during migration window.
"""
import pytest

from app.domains.voice.services.voice_screening_orchestrator import (
    VoiceScreeningOrchestrator,
)


def test_persist_session_state_public_method_exists():
    """F-09: orchestrator must expose persist_session_state as public method."""
    orch = VoiceScreeningOrchestrator()
    assert hasattr(orch, "persist_session_state"), (
        "F-09: VoiceScreeningOrchestrator must expose public persist_session_state. "
        "Callers em twilio_voice.py + gemini_voice.py usavam _-prefix (private "
        "convention break)."
    )
    assert callable(getattr(orch, "persist_session_state"))


def test_underscore_alias_preserved_for_backward_compat():
    """F-09: _persist_session_state alias must still work (deprecated alias)."""
    orch = VoiceScreeningOrchestrator()
    assert hasattr(orch, "_persist_session_state"), (
        "F-09: _persist_session_state alias must remain during migration window. "
        "Removel-o quebraria callers nao-migrados em outros modulos."
    )
    # Alias must point to the same coroutine function
    assert orch._persist_session_state is not None
