#!/usr/bin/env python3
"""Sensor canonical: detecta trace_id=str(uuid4()) ad-hoc em call sites de AuditService.

Anti-pattern: gerar UUID novo a cada chamada destroi a rastreabilidade cross-domain.
Fix: usar get_correlation_id() do ContextVar (app/middleware/request_id.py).

Uso:
    python scripts/check_no_adhoc_trace_id.py [--block]
"""
from __future__ import annotations
import ast, sys
from pathlib import Path

AUDIT_CALL_NAMES = {"log_action", "log_decision", "log_decision_in_session"}
ADHOC_PATTERNS = {"uuid4", "uuid.uuid4"}


def check(block: bool = False) -> int:
    repo_root = Path(__file__).resolve().parent.parent
    violations: list[tuple[str, int, str]] = []

    for py_file in (repo_root / "app").rglob("*.py"):
        if "__pycache__" in str(py_file):
            continue
        try:
            source = py_file.read_text(encoding="utf-8")
            tree = ast.parse(source)
        except Exception:
            continue

        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            # Check if it's a call to log_action / log_decision
            func_name = ""
            if isinstance(node.func, ast.Attribute):
                func_name = node.func.attr
            elif isinstance(node.func, ast.Name):
                func_name = node.func.id
            if func_name not in AUDIT_CALL_NAMES:
                continue

            # Check kwargs for trace_id=str(uuid4()) or session_id=str(uuid4())
            for kw in node.keywords:
                if kw.arg not in ("trace_id", "session_id"):
                    continue
                kw_src = ast.unparse(kw.value)
                if any(p in kw_src for p in ADHOC_PATTERNS):
                    rel = py_file.relative_to(repo_root)
                    violations.append((str(rel), node.lineno, f"{kw.arg}={kw_src}"))

    if violations:
        print(f"[TRACE-ID-ADHOC] {len(violations)} violations detectadas:")
        for f, line, expr in violations:
            print(f"  {f}:{line} -- {expr}")
        print()
        print("CORRECAO: substituir por:")
        print("  from app.middleware.request_id import get_correlation_id")
        print("  trace_id=get_correlation_id()  # le do ContextVar do request atual")
        return 1 if block else 0

    print("[TRACE-ID-ADHOC] OK -- 0 violations: nenhum uuid4() ad-hoc em trace_id/session_id")
    return 0


if __name__ == "__main__":
    block_mode = "--block" in sys.argv
    sys.exit(check(block=block_mode))
