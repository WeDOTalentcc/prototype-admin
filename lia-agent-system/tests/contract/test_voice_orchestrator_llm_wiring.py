"""F-01 P0 contract: VoiceScreeningOrchestrator must wire canonical llm_service.

Audit ref: AUDIT_VOICE_SCREENING_ORCHESTRATOR_2026-05-22.md F-01

Bug: self._llm_service.generate_native_gemini_sync(...) called at line ~1109 but
self._llm_service was never assigned in __init__. AttributeError caught by generic
except → scripted fallback. LIA voice degraded in production.

These contract tests fail (RED) on the bug, green after F-01 fix.
"""
import pytest
from unittest.mock import patch, MagicMock

from app.domains.voice.services.voice_screening_orchestrator import (
    VoiceScreeningOrchestrator,
    VoiceScreeningSession,
)


def test_orchestrator_has_llm_service_attribute():
    """F-01: orchestrator.__init__ must assign self._llm_service."""
    orch = VoiceScreeningOrchestrator()
    assert hasattr(orch, "_llm_service"), (
        "F-01 regression: VoiceScreeningOrchestrator must set self._llm_service "
        "in __init__. Sem isso, generate_lia_response lança AttributeError."
    )
    assert orch._llm_service is not None, (
        "F-01 regression: self._llm_service must not be None."
    )


def test_llm_service_is_canonical_singleton():
    """F-01: self._llm_service must BE the canonical app.domains.ai.services.llm.llm_service."""
    from app.domains.ai.services.llm import llm_service as canonical_llm_service

    orch = VoiceScreeningOrchestrator()
    assert orch._llm_service is canonical_llm_service, (
        "F-01: orchestrator._llm_service must be the canonical singleton "
        "(app.domains.ai.services.llm.llm_service), not a new instance. "
        "Singleton pattern ensures shared rate limit + telemetry."
    )


def test_llm_service_has_generate_native_gemini_sync_method():
    """F-01 contract: the wired llm_service must expose generate_native_gemini_sync."""
    orch = VoiceScreeningOrchestrator()
    assert hasattr(orch._llm_service, "generate_native_gemini_sync"), (
        "F-01: wired _llm_service must have generate_native_gemini_sync — "
        "method used in generate_lia_response at line ~1109."
    )
    assert callable(orch._llm_service.generate_native_gemini_sync)
