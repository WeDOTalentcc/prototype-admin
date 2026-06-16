"""Sensor — path REST do chat tem bound de duração (auditoria 2026-06-03 #6).

Bug: "aprovo ou reprovo e seguimos?" → HTTP 502. Causa: o orquestrador era
awaited SEM timeout no path REST (o WS já envolvia em asyncio.wait_for). Uma
chamada pendurada (resume re-rodando classifier/regeneração) ficava pendurada
até o gateway da plataforma estourar e devolver 502 OPACO.

Este sensor (AST, computacional) pina que os dois handlers REST que chamam o
orquestrador envolvem a chamada em asyncio.wait_for e falham com 504 estruturado.

Se falhar: envolva `_get_chat_adapter().process_message(...)` em
`asyncio.wait_for(..., timeout=_CHAT_ORCH_TIMEOUT_S)` e, no `except
asyncio.TimeoutError`, levante `HTTPException(status_code=504, ...)`.
"""
import ast
import inspect

import pytest

from app.api.v1 import chat as chat_mod

_HANDLERS = ("send_message", "send_message_with_attachments")


def _module_tree() -> ast.AST:
    src = inspect.getsource(chat_mod)
    return ast.parse(src)


def _find_async_func(tree: ast.AST, name: str) -> ast.AsyncFunctionDef | None:
    for node in ast.walk(tree):
        if isinstance(node, ast.AsyncFunctionDef) and node.name == name:
            return node
    return None


def _calls_process_message(fn: ast.AST) -> bool:
    return any(
        isinstance(n, ast.Call) and getattr(n.func, "attr", None) == "process_message"
        for n in ast.walk(fn)
    )


def _wait_for_wraps_process_message(fn: ast.AST) -> bool:
    """True se existe um asyncio.wait_for(...) cuja subárvore contém uma
    chamada .process_message (i.e., a chamada ao orquestrador está envolvida).
    """
    for node in ast.walk(fn):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        is_wait_for = getattr(func, "attr", None) == "wait_for" or getattr(func, "id", None) == "wait_for"
        if not is_wait_for:
            continue
        for sub in ast.walk(node):
            if isinstance(sub, ast.Call) and getattr(sub.func, "attr", None) == "process_message":
                return True
    return False


def _raises_504(fn: ast.AST) -> bool:
    for node in ast.walk(fn):
        if isinstance(node, ast.Call) and getattr(node.func, "id", None) == "HTTPException":
            for kw in node.keywords:
                if (
                    kw.arg == "status_code"
                    and isinstance(kw.value, ast.Constant)
                    and kw.value.value == 504
                ):
                    return True
    return False


@pytest.mark.parametrize("handler", _HANDLERS)
def test_rest_orchestrator_call_is_time_bounded(handler: str) -> None:
    tree = _module_tree()
    fn = _find_async_func(tree, handler)
    assert fn is not None, f"handler '{handler}' não encontrado em chat.py"

    if not _calls_process_message(fn):
        pytest.skip(f"{handler} não chama process_message diretamente")

    assert _wait_for_wraps_process_message(fn), (
        f"{handler}: chamada ao orquestrador (process_message) NÃO está envolvida "
        "em asyncio.wait_for — uma chamada pendurada vira 502 opaco do gateway. "
        "Envolva em asyncio.wait_for(..., timeout=_CHAT_ORCH_TIMEOUT_S)."
    )
    assert _raises_504(fn), (
        f"{handler}: falta HTTPException(status_code=504) no except "
        "asyncio.TimeoutError — o timeout deve falhar-loud com 504 estruturado."
    )
