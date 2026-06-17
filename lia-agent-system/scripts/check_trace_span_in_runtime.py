#!/usr/bin/env python3
"""Wave E Sensor 5 — Detecta métodos execute/run/invoke/_run_graph sem @trace_span nos runtimes.

Pattern canonical (Wave D observabilidade): todo método de execução em runtime
classes do Agent Studio DEVE ter @trace_span para rastreamento de latência e erros.
Sem isso, falhas são invisíveis no dashboard de observabilidade.

Verifica em *runtime*.py sob app/domains/:
- Classes com métodos `execute`, `run`, `invoke`, `_run_graph`
- Cada método DEVE ter @trace_span logo antes da definição

Honra marker: # TRACE-SPAN-EXEMPT: <reason>

Exit 0 = OK. Exit 1 = violations (BLOCKING).
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DOMAINS_ROOT = REPO_ROOT / "app" / "domains"

RUNTIME_METHODS = {"execute", "run", "invoke", "_run_graph", "run_graph"}

EXEMPT_MARKER = "TRACE-SPAN-EXEMPT"


def check_runtime_file(path: Path) -> list[tuple[int, str]]:
    """Verifica se métodos de runtime têm @trace_span."""
    content = path.read_text(encoding="utf-8", errors="replace")
    lines = content.splitlines()
    violations = []

    try:
        tree = ast.parse(content)
    except SyntaxError as e:
        return [(0, f"Erro de parse: {e}")]

    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if node.name not in RUNTIME_METHODS:
            continue

        # Verificar marker de isenção na linha antes
        lineno = node.lineno
        # Checar 3 linhas antes por marker
        start_check = max(0, lineno - 4)
        surrounding = "\n".join(lines[start_check:lineno])
        if EXEMPT_MARKER in surrounding:
            continue

        # Verificar se tem @trace_span como decorator
        has_trace_span = any(
            (
                isinstance(d, ast.Call) and
                isinstance(d.func, ast.Name) and
                d.func.id == "trace_span"
            ) or (
                isinstance(d, ast.Call) and
                isinstance(d.func, ast.Attribute) and
                d.func.attr == "trace_span"
            ) or (
                isinstance(d, ast.Name) and d.id == "trace_span"
            )
            for d in node.decorator_list
        )

        if not has_trace_span:
            violations.append((
                lineno,
                f"Método '{node.name}' em runtime sem @trace_span decorator",
            ))

    return violations


def main() -> int:
    blocking = "--warn-only" not in sys.argv
    all_violations: list[tuple[Path, int, str]] = []

    # Buscar todos *runtime*.py em domains/
    runtime_files = list(DOMAINS_ROOT.rglob("*runtime*.py"))
    if not runtime_files:
        print(f"[check_trace_span_in_runtime] ✅ Nenhum arquivo *runtime*.py encontrado — OK.")
        return 0

    for path in sorted(runtime_files):
        if "__pycache__" in str(path):
            continue
        for lineno, msg in check_runtime_file(path):
            rel = path.relative_to(REPO_ROOT)
            all_violations.append((rel, lineno, msg))

    if not all_violations:
        print(f"[check_trace_span_in_runtime] ✅ 0 violations — todos runtimes com @trace_span.")
        return 0

    print(f"[check_trace_span_in_runtime] {'❌' if blocking else '⚠️'} {len(all_violations)} violation(s):\n")
    for rel_path, lineno, msg in all_violations:
        print(f"  [{rel_path}:{lineno}] {msg}")
        print(f"    → Fix: adicionar decorator @trace_span('dominio.método') antes da def:")
        print(f"      from app.shared.observability.tracing import trace_span")
        print(f"      @trace_span('agent_studio.nome_do_metodo')")
        print(f"      async def execute(self, ...):")
        print(f"      Se método não deve ser rastreado, adicionar # TRACE-SPAN-EXEMPT: <razão> acima.")
        print()

    if blocking:
        print(f"[check_trace_span_in_runtime] BLOCKING — corrija antes de commitar.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
