"""
Contract sensor — TeamsOrchestratorBridge: 3 attachment processors + security guard.

WHY THIS SENSOR EXISTS
======================
Audit Recovery #7 (2026-05-23) descobriu que o merge incident 02361f41c
removeu silenciosamente:

1. 3 métodos de attachment processing em ``TeamsOrchestratorBridge``:
   - ``process_image_attachment`` (Gemini Vision)
   - ``process_general_document`` (.txt/.csv)
   - ``process_voice_attachment`` (Gemini STT)

2. Bloco ``W7.2 PromptInjectionGuard`` dentro de ``process_message``
   (security defense-in-depth — usuários podiam mandar prompt injection
   via Teams sem block).

22 dias sem ninguém notar — tests integration
(``test_teams_w9_3_multimedia.py`` + ``test_teams_w9_2_voice_stt.py``)
quebrados em CI.

Pattern: BLOCKING. Bridge multimedia é canonical pra clientes que usam
Microsoft Teams como surface de chat.
"""
from __future__ import annotations

import inspect

from app.domains.communication.services import teams_orchestrator_bridge


_REQUIRED_METHODS = {
    "process_message",
    "process_cv_attachment",
    "process_image_attachment",
    "process_general_document",
    "process_voice_attachment",
    "_resolve_company_id",
}


def test_bridge_has_all_canonical_methods():
    """
    TeamsOrchestratorBridge deve ter os 6 métodos canonical.

    Specific regression guard contra Recovery #7 incident — 3 attachment
    methods foram removidos silenciosamente. Test falha imediato se algum
    sumir de novo.
    """
    bridge_cls = teams_orchestrator_bridge.TeamsOrchestratorBridge  # type: ignore[attr-defined]
    methods_present = {
        name for name, _ in inspect.getmembers(bridge_cls, inspect.iscoroutinefunction)
    } | {
        name for name, _ in inspect.getmembers(bridge_cls, inspect.isfunction)
    }

    missing = _REQUIRED_METHODS - methods_present
    assert not missing, (
        f"TeamsOrchestratorBridge missing canonical methods: {sorted(missing)}\n"
        f"Present: {sorted(methods_present & _REQUIRED_METHODS)}\n"
        "Audit Recovery #7 (2026-05-23) restaurou esses métodos após o "
        "incident 02361f41c. Se foram removidos em refactor posterior, "
        "atualizar sensor + ADR + documentar substituto canonical."
    )


def test_process_message_has_prompt_injection_guard():
    """
    ``process_message`` deve invocar ``check_input_security`` (PromptInjectionGuard
    W7.2 — defense-in-depth contra prompt injection vinda do Teams).

    Bloco foi removido pelo merge incident 02361f41c. Sem ele, Teams aceita
    prompt injection sem block (P0 security gap).
    """
    src = inspect.getsource(
        teams_orchestrator_bridge.TeamsOrchestratorBridge.process_message  # type: ignore[attr-defined]
    )
    assert "check_input_security" in src, (
        "process_message NÃO invoca check_input_security (PromptInjectionGuard W7.2). "
        "Defense-in-depth contra prompt injection no Teams. Restaurar bloco "
        "logo após `if not text` check em process_message."
    )
    assert "get_block_response" in src, (
        "process_message NÃO usa get_block_response para responder ao usuário "
        "quando block triggers. Restaurar."
    )


def test_attachment_processors_use_gemini_native():
    """
    Image + Voice processors devem usar Gemini native API (LLM canonical).

    Garante que recovery não substituiu provider acidentalmente. Gemini Vision
    + STT é o canonical pós-Task #850.
    """
    image_src = inspect.getsource(
        teams_orchestrator_bridge.TeamsOrchestratorBridge.process_image_attachment  # type: ignore[attr-defined]
    )
    assert "generate_native_gemini" in image_src, (
        "process_image_attachment não invoca llm_service.generate_native_gemini. "
        "Provider canonical pra Vision é Gemini (Task #850)."
    )

    voice_src = inspect.getsource(
        teams_orchestrator_bridge.TeamsOrchestratorBridge.process_voice_attachment  # type: ignore[attr-defined]
    )
    assert "generate_native_gemini" in voice_src, (
        "process_voice_attachment não invoca llm_service.generate_native_gemini. "
        "Provider canonical pra STT é Gemini."
    )
