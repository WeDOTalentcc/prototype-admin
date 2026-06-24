"""
T5 — close_ui tool BE + FE (inspeção estática).

RED tests antes da implementação.
"""


def test_close_ui_tool_in_get_open_ui_tools():
    """get_open_ui_tools() deve incluir tool close_ui."""
    from app.domains.recruiter_assistant.agents.ui_tool_registry import (
        get_open_ui_tools,
    )
    tools = get_open_ui_tools()
    names = [t.name for t in tools]
    assert "close_ui" in names, (
        f"close_ui não encontrado em get_open_ui_tools(). Tools: {names}"
    )


def test_close_ui_returns_close_modal_action():
    """_wrap_close_ui deve retornar ui_action='close_modal'."""
    import asyncio
    from app.domains.recruiter_assistant.agents.ui_tool_registry import (
        get_open_ui_tools,
    )
    tools = get_open_ui_tools()
    close_tool = next((t for t in tools if t.name == "close_ui"), None)
    assert close_tool is not None, "close_ui tool não encontrado"
    result = asyncio.get_event_loop().run_until_complete(close_tool.function())
    assert result.get("success") is True, f"success should be True: {result}"
    data = result.get("data", {})
    assert data.get("ui_action") == "close_modal", (
        f"ui_action deve ser 'close_modal': {data}"
    )


def test_useUIAction_has_close_modal_case():
    """useUIAction.ts deve ter case 'close_modal' com lia:close_modal event."""
    path = "/home/runner/workspace/plataforma-lia/src/hooks/chat/useUIAction.ts"
    with open(path) as f:
        src = f.read()
    assert 'case "close_modal"' in src, (
        "useUIAction.ts deve ter case 'close_modal'"
    )
    assert "lia:close_modal" in src, (
        "useUIAction.ts deve dispatch CustomEvent 'lia:close_modal'"
    )


def test_LiaEntityModalHost_listens_close_modal():
    """LiaEntityModalHost.tsx deve escutar lia:close_modal para fechar modal."""
    path = "/home/runner/workspace/plataforma-lia/src/components/lia-global-modals/LiaEntityModalHost.tsx"
    with open(path) as f:
        src = f.read()
    assert "lia:close_modal" in src, (
        "LiaEntityModalHost.tsx deve ter listener para 'lia:close_modal'"
    )
