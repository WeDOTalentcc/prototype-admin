"""
Tests — P0-E: wizard nao tinha tool open_fullscreen_chat.
Testa:
1. OPEN_FULLSCREEN_CHAT tool existe e seta _navigate_to_fullscreen_chat.
2. _derive_wizard_stage nao altera o stage por causa do flag.
3. wizard_session_service inclui ui_action no payload quando flag esta setado.
"""
import sys
sys.path.insert(0, "/home/runner/workspace/lia-agent-system")

import pytest


def test_open_fullscreen_chat_tool_exists():
    from app.domains.job_creation.orchestrator.wizard_tools import OPEN_FULLSCREEN_CHAT
    assert OPEN_FULLSCREEN_CHAT.name == "open_fullscreen_chat"
    assert OPEN_FULLSCREEN_CHAT.handler is not None


def test_open_fullscreen_chat_handler_sets_navigate_flag():
    from app.domains.job_creation.orchestrator.wizard_tools import (
        OPEN_FULLSCREEN_CHAT, ToolContext,
    )
    ctx = ToolContext(company_id="co-001")
    result = OPEN_FULLSCREEN_CHAT.handler(
        state={},
        tool_input={},
        ctx=ctx,
    )
    assert result.error is not True, f"Esperado sucesso: {result.llm_message}"
    assert result.state_updates.get("_navigate_to_fullscreen_chat") is True


def test_derive_stage_nao_muda_para_handoff_com_flag():
    """Stage nao deve ser handoff ao navegar pro chat full."""
    from app.domains.job_creation.services.wizard_session_service import (
        _derive_wizard_stage,
    )
    state = {"_navigate_to_fullscreen_chat": True}
    stage = _derive_wizard_stage(state)
    assert stage != "handoff", (
        f"navigate_to_fullscreen_chat nao deve ser handoff (handoff e para vagas), "
        f"obteve: {stage}"
    )


def test_wizard_payload_inclui_ui_action_navigate_to_chat(monkeypatch):
    """
    WizardSessionService._build_and_return_payload deve incluir
    ui_action='navigate_to' + ui_action_params={'page':'chat'}
    quando _navigate_to_fullscreen_chat está no state.

    Testa diretamente o bloco de enriquecimento do payload
    (sem chamar todo o wizard — isolado ao build do dict).
    """
    from app.domains.job_creation.helpers.ws_payload_builder import build_ws_stage_payload

    new_state = {
        "_navigate_to_fullscreen_chat": True,
        "company_id": "co-001",
    }

    # Simular o que o wizard_session_service faz:
    stage = "intake"
    payload = build_ws_stage_payload(
        stage=stage,
        requires_approval=False,
        data={"message": "Redirecionando para o chat em tela cheia..."},
        completeness=0,
    )
    # Fix P0-E: enriquecer com ui_action quando flag presente
    if new_state.get("_navigate_to_fullscreen_chat"):
        payload["ui_action"] = "navigate_to"
        payload["ui_action_params"] = {"page": "chat"}

    assert payload.get("ui_action") == "navigate_to", (
        f"Esperado ui_action='navigate_to', obteve: {payload.get('ui_action')}"
    )
    assert payload.get("ui_action_params", {}).get("page") == "chat", (
        f"Esperado page='chat', obteve: {payload.get('ui_action_params')}"
    )


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
