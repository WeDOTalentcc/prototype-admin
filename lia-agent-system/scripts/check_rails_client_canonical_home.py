#!/usr/bin/env python3
"""
Sensor anti-regressão · W2-010 Phase A (2026-05-22)

Verifica que canonical Rails client está em `app/shared/integration/rails_client.py`:

1. Diretório `app/shared/integration/` existe (canonical home)
2. `rails_client.py` exporta classe `RailsClient` + 3 helpers async
3. Métodos HTTP têm `@trace_span` decorator (OTel observability wired)
4. `app/shared/rails_client.py` (legacy path) é shim re-exportando do canonical
5. Shim emite DeprecationWarning na import

Pattern violação:
- Deletar `app/shared/integration/rails_client.py` (perde canonical home)
- Remover `@trace_span` (perde observability — única instrumentação no path Rails)
- Restaurar `app/shared/rails_client.py` com implementação inline (perde shim)

Mensagem PT-BR + fix sugerido em sintaxe exata (harness CLAUDE.md).
Modo: BLOCKING por default · --warn-only opt-out.
"""
from __future__ import annotations

import argparse
import ast
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CANONICAL_FILE = REPO_ROOT / "app/shared/integration/rails_client.py"
CANONICAL_INIT = REPO_ROOT / "app/shared/integration/__init__.py"
SHIM_FILE = REPO_ROOT / "app/shared/rails_client.py"


def check_canonical_home() -> list[str]:
    errors: list[str] = []

    if not CANONICAL_INIT.exists():
        errors.append(
            "❌ `app/shared/integration/__init__.py` ausente\n"
            "   FIX: criar diretório + __init__.py com docstring W2-010"
        )
    if not CANONICAL_FILE.exists():
        errors.append(
            "❌ `app/shared/integration/rails_client.py` ausente (canonical home)\n"
            "   FIX: criar canonical client. Pre-audit:\n"
            "        REPLIT_LIA_REMEDIATION_BACKLOG_2026-05-22.md W2-010"
        )
        return errors

    src = CANONICAL_FILE.read_text()
    try:
        tree = ast.parse(src)
    except SyntaxError as exc:
        return [f"❌ Syntax error em {CANONICAL_FILE.name}: {exc}"]

    # Class RailsClient + 5 métodos
    class_node = None
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == "RailsClient":
            class_node = node
            break
    if class_node is None:
        errors.append(
            "❌ Class `RailsClient` ausente em canonical home\n"
            f"   File: {CANONICAL_FILE.relative_to(REPO_ROOT)}"
        )
    else:
        methods = {m.name for m in class_node.body if isinstance(m, (ast.AsyncFunctionDef, ast.FunctionDef))}
        for required in ("get", "post", "put", "patch", "delete"):
            if required not in methods:
                errors.append(
                    f"❌ RailsClient.{required}() ausente (canonical HTTP method)\n"
                    f"   File: {CANONICAL_FILE.relative_to(REPO_ROOT)}"
                )

        # Cada método deve ter @trace_span decorator
        for method in class_node.body:
            if not isinstance(method, (ast.AsyncFunctionDef, ast.FunctionDef)):
                continue
            if method.name not in ("get", "post", "put", "patch", "delete"):
                continue
            has_trace_span = any(
                (isinstance(d, ast.Call) and (
                    (isinstance(d.func, ast.Name) and d.func.id == "trace_span")
                    or (isinstance(d.func, ast.Attribute) and d.func.attr == "trace_span")
                )) for d in method.decorator_list
            )
            if not has_trace_span:
                errors.append(
                    f"❌ RailsClient.{method.name}() SEM @trace_span (observability gap)\n"
                    f"   File: {CANONICAL_FILE.relative_to(REPO_ROOT)}:{method.lineno}\n"
                    "   Risco: zero OTel spans no Rails path (W2-010 valor perdido)\n"
                    f"   FIX: adicionar `@trace_span(\"rails.{method.name}\", attributes={{...}})`"
                )

    # 3 helpers presentes
    fn_names = {
        n.name for n in tree.body
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    for helper in ("rails_get", "rails_patch", "rails_post"):
        if helper not in fn_names:
            errors.append(
                f"❌ Helper `{helper}` ausente em canonical home\n"
                f"   File: {CANONICAL_FILE.relative_to(REPO_ROOT)}\n"
                "   FIX: helper preserva API de app/shared/rails_client.py (13 callers)"
            )

    return errors


def check_shim_redirect() -> list[str]:
    errors: list[str] = []

    if not SHIM_FILE.exists():
        errors.append(
            "❌ `app/shared/rails_client.py` ausente · esperado como shim\n"
            "   Risco: 13 callers in-tree quebram\n"
            "   FIX: shim com re-export de app.shared.integration.rails_client"
        )
        return errors

    src = SHIM_FILE.read_text()
    if "DeprecationWarning" not in src:
        errors.append(
            "❌ `app/shared/rails_client.py` NÃO emite DeprecationWarning\n"
            f"   File: {SHIM_FILE.relative_to(REPO_ROOT)}\n"
            "   FIX: adicionar warnings.warn(..., DeprecationWarning, stacklevel=2)\n"
            "        indicando canonical em app.shared.integration.rails_client"
        )
    if "from app.shared.integration.rails_client" not in src:
        errors.append(
            "❌ `app/shared/rails_client.py` NÃO re-exporta do canonical\n"
            f"   File: {SHIM_FILE.relative_to(REPO_ROOT)}\n"
            "   FIX: shim deve fazer:\n"
            "       from app.shared.integration.rails_client import (\n"
            "           rails_get, rails_patch, rails_post,\n"
            "       )"
        )

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--warn-only", action="store_true")
    args = parser.parse_args()

    errors: list[str] = []
    errors.extend(check_canonical_home())
    errors.extend(check_shim_redirect())

    if errors:
        print(
            f"W2-010 canonical Rails client · {len(errors)} violation(s):",
            file=sys.stderr,
        )
        print(file=sys.stderr)
        for err in errors:
            print(err, file=sys.stderr)
            print(file=sys.stderr)
        if args.warn_only:
            print("⚠️  WARN-ONLY mode: exit 0", file=sys.stderr)
            return 0
        return 1

    print(
        "✅ Canonical Rails client home (W2-010 Phase A) · "
        "app/shared/integration/rails_client.py + 5 methods OTel-wired + shim deprecation"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
