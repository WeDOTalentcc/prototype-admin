#!/usr/bin/env python3
"""Sensor R5: detecta `asyncio.run()` ou `_asyncio.run()` em sync functions.

Background: 20+ sites em graph.py usam asyncio.run em sync nodes — anti-pattern
que bloqueia event loop ou raise RuntimeError em Python 3.12+. Helper canonical
existe em app/domains/job_creation/helpers/async_audit.py:
- emit_audit_fire_and_forget() para audit logs fire-and-forget
- run_coro_in_threadpool() para coros que precisam de resultado

Allowlist: marker `# ASYNCIO-RUN-EXEMPT: <reason>` na mesma linha ou +/- 2 linhas.

Modo: BLOCKING por default (post-PR-14 2026-05-26). `--warn-only` para opt-out.

Baseline esperado pos-PR-14: 0 violations (P0-#2 fechado 100%).

Ratchet historico:
- PR-4 baseline: 19 violations (apenas site C-1 graph.py:1396 fixado)
- PR-5: 19 -> 13 (6 sites Tipo A migrados para emit_audit_fire_and_forget)
- PR-6: 13 -> 9  (4 sites Tipo E migrados)
- PR-7: 9 -> 4 (4 isolated get_event_loop refactor)
- PR-14: 10 -> 0 (4 gates + salary_node Tipo B migration) -> BLOCKING default

Exit:
  0 — todas as invariantes OK (ou warn-only)
  1 — violacao (apenas se --blocking e count > --max-violations)
"""
from __future__ import annotations

import argparse
import ast
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
TARGET_FILES = [
    PROJECT_ROOT / "app" / "domains" / "job_creation" / "graph.py",
    # Adicione mais files se descobrir antipattern noutros nodes
]
EXEMPT_MARKER = "ASYNCIO-RUN-EXEMPT"


def _is_asyncio_run_call(call: ast.Call) -> bool:
    """Match `asyncio.run(...)` ou `_asyncio.run(...)`."""
    func = call.func
    if not isinstance(func, ast.Attribute):
        return False
    if func.attr != "run":
        return False
    value = func.value
    if not isinstance(value, ast.Name):
        return False
    return value.id in ("asyncio", "_asyncio")


def find_violations(filepath: Path) -> list[dict]:
    """Scan AST: encontra asyncio.run dentro de sync FunctionDefs."""
    source = filepath.read_text()
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        print(f"❌ SyntaxError em {filepath}: {exc}", file=sys.stderr)
        return []
    lines = source.split("\n")
    violations: list[dict] = []

    # Coletar todos FunctionDef sync (nao AsyncFunctionDef)
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef):
            continue
        # Walk dentro: nao re-descer em AsyncFunctionDef aninhadas
        for sub in ast.walk(node):
            # Pular calls dentro de AsyncFunctionDef nested
            if isinstance(sub, ast.AsyncFunctionDef):
                # Nao iterar nos descendentes async-defs (sao OK)
                continue
            if not isinstance(sub, ast.Call):
                continue
            if not _is_asyncio_run_call(sub):
                continue
            lineno = sub.lineno
            # Allowlist: marker em +/- 2 linhas
            start = max(0, lineno - 3)
            end = min(len(lines), lineno + 2)
            context_block = "\n".join(lines[start:end])
            if EXEMPT_MARKER in context_block:
                continue
            violations.append(
                {
                    "file": str(filepath.relative_to(PROJECT_ROOT)),
                    "line": lineno,
                    "function": node.name,
                    "snippet": lines[lineno - 1].strip()[:120],
                },
            )
    return violations


def main() -> int:
    parser = argparse.ArgumentParser(description="Sensor R5 asyncio.run em sync nodes")
    # PR-14 (2026-05-26): default e BLOCKING agora que baseline = 0.
    # Use --warn-only para reverter ao comportamento antigo (legacy ratchet).
    parser.add_argument(
        "--blocking",
        action="store_true",
        default=True,
        help="(default) Exit 1 se violations > max-violations (CI gating)",
    )
    parser.add_argument(
        "--warn-only",
        dest="blocking",
        action="store_false",
        help="Opt-out de blocking (legacy mode, exit 0 mesmo com violations)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output JSON em vez de texto",
    )
    parser.add_argument(
        "--max-violations",
        type=int,
        default=0,
        help="Threshold baseline (0 post-PR-14). Default: 0",
    )
    args = parser.parse_args()

    all_violations: list[dict] = []
    for f in TARGET_FILES:
        if f.exists():
            all_violations.extend(find_violations(f))

    if args.json:
        print(
            json.dumps(
                {
                    "count": len(all_violations),
                    "baseline_max": args.max_violations,
                    "violations": all_violations,
                },
                indent=2,
            ),
        )
    else:
        for v in all_violations:
            print(
                f"[{v['file']}:{v['line']}] in {v['function']}() | {v['snippet']}",
            )
            print(
                "  -> Fix: usar `emit_audit_fire_and_forget()` (audit) ou "
                "`run_coro_in_threadpool()` (precisa resultado) de "
                "app.domains.job_creation.helpers.async_audit",
            )
            print(
                "  -> Allowlist: adicione comentario `# ASYNCIO-RUN-EXEMPT: "
                "<reason>` proximo se for caso justificado",
            )
        mode = "BLOCKING" if args.blocking else "warn-only"
        print(
            f"\nTotal: {len(all_violations)} violations "
            f"(baseline max: {args.max_violations}, mode: {mode})",
        )

    if args.blocking and len(all_violations) > args.max_violations:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
