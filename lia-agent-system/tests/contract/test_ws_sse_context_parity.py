"""Sensor canonical P0.1 (2026-06-04) — paridade WS/SSE/REST de view-context.

Bug (auditoria 2026-06-04): o handler WebSocket (websocket_endpoint em chat.py)
recebia o frame do FE com  mas NAO extraia  nem
passava  ao _invoke_orchestrator_legacy. Resultado: bolha WS e
chat-page em fallback WS ficavam cegos ao estado da tela, enquanto SSE/REST
funcionavam (SSE via view_context ~L1207; REST via page_context ~L323).

Este sensor pina a PARIDADE: os transportes que invocam o orquestrador legacy
threadam o view-context. Computacional (AST) — nao sobe WS/DB. Mensagem de erro
otimizada pra consumo de LLM (aponta produtor + linha + fix exato).
"""
import ast
from pathlib import Path

CHAT_PY = Path(__file__).resolve().parents[2] / "app" / "api" / "v1" / "chat.py"


def _tree():
    return ast.parse(CHAT_PY.read_text(encoding="utf-8"))


def _find_func(tree, name):
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            return node
    return None


def _calls_to(func_node, callee):
    out = []
    for node in ast.walk(func_node):
        if isinstance(node, ast.Call):
            f = node.func
            fname = getattr(f, "id", None) or getattr(f, "attr", None)
            if fname == callee:
                out.append(node)
    return out


def _has_page_context_kw(call):
    for kw in call.keywords:
        if kw.arg == "page_context":
            if isinstance(kw.value, ast.Constant) and kw.value.value is None:
                return False
            return True
    return False


def _reads_data_context(func_node):
    for node in ast.walk(func_node):
        if isinstance(node, ast.Call):
            f = node.func
            if isinstance(f, ast.Attribute) and f.attr == "get":
                if node.args and isinstance(node.args[0], ast.Constant) and node.args[0].value == "context":
                    if getattr(f.value, "id", None) == "data":
                        return True
        if isinstance(node, ast.Subscript):
            if getattr(node.value, "id", None) == "data":
                val = getattr(node.slice, "value", None)
                if val == "context":
                    return True
    return False


def test_ws_handler_reads_frame_context():
    ws = _find_func(_tree(), "websocket_endpoint")
    assert ws is not None, "websocket_endpoint nao encontrado em chat.py"
    assert _reads_data_context(ws), (
        "[P0.1 paridade] websocket_endpoint NAO le data.get(\"context\"). "
        "O FE manda o estado da tela no frame WS (useChatTransport.ts: context). "
        "FIX em app/api/v1/chat.py (handler WS): adicione "
        "page_context = data.get(\"context\") or {} apos user_content = data[\"content\"]."
    )


def test_ws_handler_threads_page_context_to_orchestrator():
    ws = _find_func(_tree(), "websocket_endpoint")
    calls = _calls_to(ws, "_invoke_orchestrator_legacy")
    assert calls, "websocket_endpoint nao chama _invoke_orchestrator_legacy"
    assert any(_has_page_context_kw(c) for c in calls), (
        "[P0.1 paridade] a chamada a _invoke_orchestrator_legacy no handler WS "
        "NAO passa page_context -> agente fica cego ao estado da tela. "
        "FIX em app/api/v1/chat.py: adicione page_context=page_context, na chamada. "
        "SSE faz isso via view_context (~L1207); REST via page_context (~L323)."
    )
