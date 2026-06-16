#!/usr/bin/env python3
"""Sensor #10 Sprint 7C Part 1 v2: dispatch_* functions têm audit log canonical.

Pattern detection: AST walk em lia-agent-system/app/services/ + app/jobs/tasks/.
Find function def starting with 'dispatch_' → check body has audit_service.log_decision
OR studio_audit() OR log_decision() call (canonical dim 5 audit).

Sprint 7C Part 1 v2: warn-only baseline (legacy dispatch_* sem audit é débito
conhecido; promote BLOCKING após Part 1.5 quando todos dispatch tem audit
canonical).

Output otimizado pra consumo de LLM: file:line + nome da função + instrução de
fix em PT-BR.

Refs:
- AGENT_STUDIO_SPRINT7_PLAN.md §4 Sprint 7C
- ~/.claude/CLAUDE.md REGRA 4 anti-silent-fallback (audit é dim 5 feature-audit)
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path


AUDIT_MARKERS = (
    "audit_service.log_decision",
    "audit.log_decision",
    "studio_audit(",
    "log_decision(",
    "AuditService(",  # construção do service no body = sinal forte
)

SCAN_ROOTS = (
    Path("app/services"),
    Path("app/jobs/tasks"),
)

SKIP_PARTS = {"tests", "_archive", "__pycache__"}


def _delegates_to_impl(func_node: ast.AST, module_funcs: dict[str, ast.AST]) -> bool:
    """True se função wrapper Celery delega pra `_<name>_impl` ou `_dispatch_impl` no mesmo módulo.

    Pattern canonical: Celery task wrapper apenas chama asyncio.run(_dispatch_impl(...))
    e o `_dispatch_impl` async helper carrega o audit log_decision. Sensor aceita
    quando o delegate target ESTÁ no mesmo módulo E ele próprio passa no check.
    """
    try:
        body_text = ast.unparse(func_node)
    except AttributeError:
        return False
    for impl_name, impl_node in module_funcs.items():
        if not (impl_name.startswith("_") and impl_name.endswith("_impl")):
            continue
        # delegação aparece como chamada ao helper
        if f"{impl_name}(" not in body_text:
            continue
        try:
            impl_text = ast.unparse(impl_node)
        except AttributeError:
            continue
        if any(marker in impl_text for marker in AUDIT_MARKERS):
            return True
    return False


def _has_audit_in_body(func_node: ast.AST) -> bool:
    """True se body do func tem alguma chamada de audit canonical."""
    try:
        body_text = ast.unparse(func_node)  # py3.9+
    except AttributeError:
        return False  # py < 3.9 — assume violation
    return any(marker in body_text for marker in AUDIT_MARKERS)


def _scan_file(path: Path) -> list[str]:
    """Returns list of violation strings for one file."""
    violations: list[str] = []
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return violations
    try:
        tree = ast.parse(text, filename=str(path))
    except SyntaxError:
        return violations

    # Collect all top-level funcs no módulo pra resolver delegação.
    module_funcs: dict[str, ast.AST] = {
        n.name: n
        for n in tree.body
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
    }

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if not node.name.startswith("dispatch_"):
                continue
            if _has_audit_in_body(node):
                continue
            if _delegates_to_impl(node, module_funcs):
                continue
            rel = path.as_posix()
            violations.append(
                f"{rel}:{node.lineno}: função {node.name}() sem audit log canonical. "
                f"Wire AuditService.log_decision (dim 5 feature-audit) OR studio_audit() "
                f"OR delegar pra `_<name>_impl` que tenha audit. Audit é obrigatório em dispatch_*."
            )
    return violations


def main() -> int:
    base = Path(__file__).resolve().parent.parent  # lia-agent-system/
    violations: list[str] = []
    for root in SCAN_ROOTS:
        abs_root = base / root
        if not abs_root.exists():
            continue
        for path in abs_root.rglob("*.py"):
            if any(part in SKIP_PARTS for part in path.parts):
                continue
            violations.extend(_scan_file(path))

    if violations:
        print("\n".join(violations))
        print(
            f"\n{len(violations)} dispatch_* function(s) sem audit log canonical.\n"
            "BLOCKING (Sprint 7C Part 1.5c). Wire AuditService.log_decision em cada\n"
            "dispatch_* (decisao Paulo audit dim 5 canonical) ou delegar pra _<n>_impl."
        )
        return 1

    print("check_dispatch_has_audit: 0 violations (baseline canonical).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
