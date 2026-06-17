"""T-1170 (Bug 4): `initialize_tools()` deve ser idempotente.

Causa raiz: `initialize_tools()` é chamada 3x no startup (main.py,
orchestrator/legacy/orchestrator.py, job_management/agents/job_wizard_graph.py).
Cada call re-registra todo o catálogo → ~80 warnings 'already registered,
overwriting' por reload.

Esta sentinela garante:
  1) AST guard: o módulo `app/tools/__init__.py` mantém a flag `_INITIALIZED`
     e o early-return. Renomear/remover a guarda quebra a build.
  2) Runtime: chamadas adicionais a `initialize_tools()` não emitem warnings
     de re-registro no `ToolRegistry`.
"""
from __future__ import annotations

import ast
import logging
from pathlib import Path

import pytest


TOOLS_INIT = Path(__file__).resolve().parents[3] / "app" / "tools" / "__init__.py"


def test_initialize_tools_has_idempotency_guard_ast() -> None:
    """AST: confere flag módulo-level `_INITIALIZED` + early return em `initialize_tools`."""
    source = TOOLS_INIT.read_text(encoding="utf-8")
    tree = ast.parse(source)

    module_flag_present = any(
        isinstance(node, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id == "_INITIALIZED" for t in node.targets)
        for node in tree.body
    )
    assert module_flag_present, (
        "T-1170 REGRESSÃO: módulo `app/tools/__init__.py` deve declarar "
        "`_INITIALIZED = False` no nível módulo (guard idempotente)."
    )

    init_fn = next(
        (n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "initialize_tools"),
        None,
    )
    assert init_fn is not None, "função `initialize_tools` deve existir."

    # Procura `if _INITIALIZED: return` no início.
    has_early_return = False
    for node in ast.walk(init_fn):
        if isinstance(node, ast.If) and isinstance(node.test, ast.Name) and node.test.id == "_INITIALIZED":
            for stmt in node.body:
                if isinstance(stmt, ast.Return):
                    has_early_return = True
                    break
    assert has_early_return, (
        "T-1170 REGRESSÃO: `initialize_tools` deve fazer `if _INITIALIZED: return` "
        "no topo. Sem isso, chamadas múltiplas re-registram tools (ruído + risco "
        "de overrides silenciosos)."
    )

    # Confere `_INITIALIZED = True` ao final (state atomicamente após registros).
    sets_true = False
    for node in ast.walk(init_fn):
        if (
            isinstance(node, ast.Assign)
            and any(isinstance(t, ast.Name) and t.id == "_INITIALIZED" for t in node.targets)
            and isinstance(node.value, ast.Constant)
            and node.value.value is True
        ):
            sets_true = True
            break
    assert sets_true, (
        "T-1170 REGRESSÃO: `initialize_tools` deve setar `_INITIALIZED = True` "
        "após registrar todas as tools (caso contrário a guarda nunca dispara)."
    )


def test_initialize_tools_runtime_no_duplicate_warnings(caplog: pytest.LogCaptureFixture) -> None:
    """Runtime: 2ª chamada NÃO emite warnings `already registered`."""
    from app.tools import initialize_tools

    # 1ª chamada (pode ou não rodar — depende de quem importou antes).
    initialize_tools()

    with caplog.at_level(logging.WARNING, logger="ToolRegistry"):
        initialize_tools()  # 2ª chamada deve ser no-op
        initialize_tools()  # 3ª também

    offending = [
        record.message
        for record in caplog.records
        if "already registered" in record.message
    ]
    assert not offending, (
        f"T-1170 REGRESSÃO: chamadas extras a `initialize_tools()` emitiram "
        f"{len(offending)} warnings de re-registro:\n  - "
        + "\n  - ".join(offending[:5])
    )
