"""Sensor PR-14: gates do wizard nao devem chamar _asyncio.run inline.

Background: PR-14 (2026-05-26) migrou os 4 gates (jd, competency, wsi_questions,
review) + salary_node para o helper canonical `run_coro_in_threadpool()` em
app/domains/job_creation/helpers/async_audit. Este sensor trava regressao
futura via AST walk no graph.py.

Sites cobertos:
  - jd_gate_node
  - competency_gate_node
  - wsi_questions_gate_node
  - review_gate_node
  - salary_node

Pattern proibido:
    output = _asyncio.run(coro_factory())
    _ex.submit(lambda: _asyncio.run(coro_factory()))

Pattern canonical:
    output = run_coro_in_threadpool(coro_factory, timeout=30.0)
"""
from __future__ import annotations

import ast
import pathlib


GATE_NODE_NAMES = {
    "jd_gate_node",
    "competency_gate_node",
    "wsi_questions_gate_node",
    "review_gate_node",
    "salary_node",
}

GRAPH_PATH = (
    pathlib.Path(__file__).resolve().parents[2]
    / "app"
    / "domains"
    / "job_creation"
    / "graph.py"
)


def _collect_asyncio_run_calls_in_node(
    func_node: ast.FunctionDef,
) -> list[tuple[str, int]]:
    """Walks function body looking for asyncio.run / _asyncio.run calls.

    Includes nested functions (lambdas, inner defs) which is desirable —
    `lambda: _asyncio.run(...)` patterns are exactly what PR-14 removed.
    """
    violations: list[tuple[str, int]] = []
    for sub in ast.walk(func_node):
        if not isinstance(sub, ast.Call):
            continue
        if not isinstance(sub.func, ast.Attribute):
            continue
        if sub.func.attr != "run":
            continue
        if not isinstance(sub.func.value, ast.Name):
            continue
        if sub.func.value.id in ("asyncio", "_asyncio"):
            violations.append((func_node.name, sub.lineno))
    return violations


def test_gate_nodes_dont_call_asyncio_run_directly():
    """Asserts gates use run_coro_in_threadpool(), not direct _asyncio.run()."""
    assert GRAPH_PATH.exists(), f"graph.py not found at {GRAPH_PATH}"

    source = GRAPH_PATH.read_text()
    tree = ast.parse(source)

    violations: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef):
            continue
        if node.name not in GATE_NODE_NAMES:
            continue

        nested = _collect_asyncio_run_calls_in_node(node)
        for fname, lineno in nested:
            violations.append(f"{fname}:{lineno}")

    assert not violations, (
        "PR-14 regression: os gates devem usar `run_coro_in_threadpool()` do "
        "helper async_audit em vez de `_asyncio.run()` inline.\n"
        "Violations found:\n  "
        + "\n  ".join(violations)
        + "\n\nFix: substituir bloco `running_loop + ThreadPoolExecutor + "
        "_asyncio.run(coro_factory())` por:\n"
        "    output = run_coro_in_threadpool(coro_factory, timeout=30.0)"
    )


def test_helper_import_present_in_graph_py():
    """Garante que graph.py importa o helper canonical (defesa profunda)."""
    source = GRAPH_PATH.read_text()
    assert (
        "from app.domains.job_creation.helpers.async_audit import" in source
        and "run_coro_in_threadpool" in source
    ), (
        "graph.py deve importar run_coro_in_threadpool de async_audit. "
        "Sem o import top-level, os gates nao podem usar o helper canonical."
    )
