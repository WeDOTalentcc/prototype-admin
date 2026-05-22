"""
VoiceCoreOrchestrator — canonical import location (Sprint 3.2).

Sprint 3.2 refactor (audit 2026-05-22 W4-1 V2): re-exports VoiceCoreOrchestrator
e tipos relacionados da location historica voice_screening_orchestrator.py.
Decisao de arquitetura (vide docstring de voice_screening_orchestrator.py):
classes ficam no modulo historico pra preservar module-level symbol binding
usado por dezenas de tests (`patch("...voice_screening_orchestrator.X")`).

Para callers que querem usar o nucleo voz generico (sem WSI hardcoded):
    from app.domains.voice.services.voice_core_orchestrator import VoiceCoreOrchestrator

Para o subclass legacy (WSI-aware, backward-compat):
    from app.domains.voice.services.voice_screening_orchestrator import VoiceScreeningOrchestrator
"""
from app.domains.voice.services.voice_screening_orchestrator import (
    ConsentNotGrantedError,
    VoiceCoreOrchestrator,
    VoiceScreeningOrchestrator,
    VoiceScreeningOrchestratorError,
    VoiceScreeningSession,
)

__all__ = [
    "ConsentNotGrantedError",
    "VoiceCoreOrchestrator",
    "VoiceScreeningOrchestrator",
    "VoiceScreeningOrchestratorError",
    "VoiceScreeningSession",
]
