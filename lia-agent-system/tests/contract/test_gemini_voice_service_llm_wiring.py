"""F-12 P0 contract: GeminiVoiceService must wire canonical llm_service.

Audit ref: AUDIT_VOICE_SCREENING_ORCHESTRATOR_2026-05-22.md F-12

Bug: self._get_llm_service() called at lines 130, 220, 301 but _get_llm_service
method never defined. Every transcribe_audio / analyze_audio / transcribe_interview
call lances AttributeError. Active callers:
- app/api/v1/voice.py (endpoints REST de voz)
- app/services/twin_knowledge_indexer.py
- app/services/voice_interview_state_machine.py

Fix: substitute _get_llm_service() with direct reference to canonical llm_service
singleton (mesmo pattern do F-01 fix em VoiceScreeningOrchestrator).
"""
import pytest
from unittest.mock import patch

from app.domains.voice.services.gemini_voice_service import GeminiVoiceService


def test_gemini_voice_service_has_llm_service_attribute():
    """F-12: GeminiVoiceService.__init__ must assign self._llm_service (canonical)."""
    svc = GeminiVoiceService(company_id="")
    assert hasattr(svc, "_llm_service"), (
        "F-12 regression: GeminiVoiceService must set self._llm_service in __init__. "
        "Sem isso, transcribe_audio/analyze_audio/transcribe_interview lancam AttributeError."
    )
    assert svc._llm_service is not None


def test_gemini_voice_service_llm_is_canonical_singleton():
    """F-12: self._llm_service must BE the canonical app.domains.ai.services.llm.llm_service."""
    from app.domains.ai.services.llm import llm_service as canonical_llm_service

    svc = GeminiVoiceService(company_id="")
    assert svc._llm_service is canonical_llm_service, (
        "F-12: GeminiVoiceService._llm_service must be canonical singleton. "
        "Garante shared rate limit + telemetria tenant-aware."
    )


def test_gemini_voice_service_no_ghost_method_calls():
    """F-12 regression guard: AST check for self._get_llm_service() call expressions.

    Inspects the source via AST to find Attribute(value=Name(id='self'), attr='_get_llm_service')
    inside Call nodes. Comments/docstrings que ainda mencionam o nome do bug nao
    contam (sao explicacao historica), so calls reais.
    """
    import ast
    import inspect
    source = inspect.getsource(GeminiVoiceService)
    tree = ast.parse(source)

    ghost_call_sites = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            # Match self._get_llm_service(...) calls
            if (isinstance(func, ast.Attribute)
                and func.attr == "_get_llm_service"
                and isinstance(func.value, ast.Name)
                and func.value.id == "self"):
                ghost_call_sites.append(node.lineno)

    assert ghost_call_sites == [], (
        f"F-12 regression: self._get_llm_service() ghost calls at lines {ghost_call_sites}. "
        f"Use self._llm_service direct reference (canonical singleton)."
    )
