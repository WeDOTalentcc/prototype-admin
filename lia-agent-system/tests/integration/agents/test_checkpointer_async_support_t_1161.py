"""Task #1161 — Bug B root cause sentinel.

Garante que `get_checkpointer()` NUNCA retorna um saver sync-only (que
herda `aget_tuple` do stub abstrato `BaseCheckpointSaver`). Se o wizard
chamar `await self._graph.ainvoke(Command(resume=...))` com um
checkpointer sync-only, langgraph dispara `NotImplementedError` dentro
de `AsyncPregelLoop.__aenter__` — exatamente o bug que causou o
`silent_fallback` no Task #1161.
"""
from __future__ import annotations

import ast
from pathlib import Path


CHECKPOINTER_PATH = (
    Path(__file__).resolve().parents[3]
    / "libs"
    / "agents-core"
    / "lia_agents_core"
    / "checkpointer.py"
)


def test_supports_async_helper_is_defined():
    src = CHECKPOINTER_PATH.read_text(encoding="utf-8")
    tree = ast.parse(src)
    names = {n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)}
    assert "_supports_async" in names, (
        "_supports_async() removido — Task #1161 Bug B sentinel quebrado."
    )


def test_get_checkpointer_calls_supports_async_guard():
    src = CHECKPOINTER_PATH.read_text(encoding="utf-8")
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "get_checkpointer":
            body_src = ast.unparse(node)
            assert "_supports_async(" in body_src, (
                "get_checkpointer() nao chama _supports_async() — checkpointer "
                "sync-only voltaria e wizard.aresume quebraria com NIE."
            )
            return
    raise AssertionError("get_checkpointer() nao encontrado")


def test_runtime_checkpointer_supports_aget_tuple():
    """Runtime: o saver retornado por get_checkpointer() em dev DEVE expor
    aget_tuple sobrescrito (não o stub abstrato)."""
    from lia_agents_core.checkpointer import _supports_async, get_checkpointer

    saver = get_checkpointer()
    assert _supports_async(saver), (
        f"get_checkpointer() retornou {type(saver).__name__} sem aget_tuple "
        "real — wizard.aresume_with_message dispararia NotImplementedError."
    )
