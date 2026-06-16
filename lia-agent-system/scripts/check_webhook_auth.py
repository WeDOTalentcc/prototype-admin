#!/usr/bin/env python3
"""
check_webhook_auth.py — Sensor P1-W3: detecta endpoints de webhook sem autenticação.

Criado 2026-05-24 como parte do fix P1-W3-01/02/04/06.

O que detecta:
- Funções Python decoradas com @router.post/@router.put em arquivos cujo
  nome contém "webhook" que NÃO têm nenhum dos gates de autenticação canônicos:
    1. verify_webhook_owner(...)          — canonical HMAC per-tenant (Task #1146)
    2. _verify_external_webhook_bearer(  — bearer token estático (P1-W3-02)
    3. require_company_id                 — mínimo JWT gate (Onda 4.2e-P0-9/10/11)
    4. # WEBHOOK-AUTH-EXEMPT: <reason>   — marker de isenção documentado

Falso-positivo mitigação:
- Ignora @router.get (read-only, sem side effects).
- Ignora health/status endpoints (nome contém "health" ou "status").
- Exige marker # WEBHOOK-AUTH-EXEMPT pra isentar legítimos (força documentação).

Uso:
  python scripts/check_webhook_auth.py [--blocking] [--path <dir>]

Exit code:
  0 — OK (nenhuma violação ou --blocking não passado)
  1 — Violações encontradas (com --blocking)

Output (LLM-otimizado):
  [file:line] handler_name | motivo | Fix: adicionar <gate> à função
"""
from __future__ import annotations

import argparse
import ast
import os
import sys
from pathlib import Path

# Gates canônicos — qualquer referência no corpo da função OU nos decoradores
# satisfaz o check. Strings que aparecem como chamada de função OU como argumento
# de Depends().
CANONICAL_GATES = {
    "verify_webhook_owner",            # canonical HMAC per-tenant (Task #1146)
    "_verify_external_webhook_bearer", # bearer token estático P1-W3-02
    "require_company_id",              # JWT gate mínimo (Onda 4.2e-P0)
    "verify_webhook_signature",        # legacy HMAC gate (mailgun, etc.)
    "_verify_mailgun_signature",       # mailgun-specific HMAC
    "get_current_active_user",         # user-session JWT (endpoints de gestão)
    "get_current_user",                # alias de get_current_active_user
    "require_authenticated_user",      # alternate name pra mesmo gate
}

EXEMPTION_MARKER = "WEBHOOK-AUTH-EXEMPT"

# Nomes de endpoint que são sabidamente read-only / public (não precisam de auth).
EXEMPT_FUNCTION_PATTERNS = {"health", "status", "ping"}


def _has_gate(func_node: ast.AsyncFunctionDef | ast.FunctionDef, source_lines: list[str]) -> bool:
    """Return True if function body references any canonical auth gate."""
    # Check source text for string patterns (mais robusto que AST puro pra Depends())
    func_start = func_node.lineno - 1
    func_end = func_node.end_lineno if hasattr(func_node, "end_lineno") else func_node.lineno + 50
    func_source = "\n".join(source_lines[func_start:func_end])

    for gate in CANONICAL_GATES:
        if gate in func_source:
            return True

    if EXEMPTION_MARKER in func_source:
        return True

    return False


def _is_webhook_post_handler(
    node: ast.AsyncFunctionDef | ast.FunctionDef,
) -> bool:
    """Return True if function is decorated with @router.post or @router.put."""
    for decorator in node.decorator_list:
        # Detect router.post(...), router.put(...), router.patch(...)
        if isinstance(decorator, ast.Call):
            func = decorator.func
            if isinstance(func, ast.Attribute) and func.attr in ("post", "put", "patch"):
                return True
        # Detect @router.post (without call args — rare but possible)
        elif isinstance(decorator, ast.Attribute) and decorator.attr in ("post", "put", "patch"):
            return True
    return False


def _is_exempt_by_name(name: str) -> bool:
    lower = name.lower()
    return any(p in lower for p in EXEMPT_FUNCTION_PATTERNS)


def check_file(path: Path) -> list[str]:
    """Return list of violation strings for the given file."""
    violations = []
    try:
        source = path.read_text(encoding="utf-8")
    except Exception as exc:
        return [f"[{path}:?] ERRO ao ler arquivo: {exc}"]

    source_lines = source.splitlines()
    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError as exc:
        return [f"[{path}:{exc.lineno}] SyntaxError: {exc.msg}"]

    for node in ast.walk(tree):
        if not isinstance(node, (ast.AsyncFunctionDef, ast.FunctionDef)):
            continue
        if not _is_webhook_post_handler(node):
            continue
        if _is_exempt_by_name(node.name):
            continue
        if _has_gate(node, source_lines):
            continue

        violations.append(
            f"[{path}:{node.lineno}] {node.name}() — "
            f"endpoint de webhook sem gate de autenticação detectado | "
            f"→ Fix: adicionar verify_webhook_owner(...) OU "
            f"_verify_external_webhook_bearer(...) OU require_company_id Depends() "
            f"OU marcar '# {EXEMPTION_MARKER}: <reason>' no corpo da função"
        )

    return violations


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--path",
        default="lia-agent-system/app/api/v1",
        help="Diretório raiz para buscar arquivos webhook (default: lia-agent-system/app/api/v1)",
    )
    parser.add_argument(
        "--blocking",
        action="store_true",
        help="Exit 1 se houver violações (modo CI bloqueante)",
    )
    parser.add_argument(
        "--max-violations",
        type=int,
        default=0,
        help="Número máximo de violações antes de bloquear (default: 0 = qualquer)",
    )
    args = parser.parse_args()

    root = Path(args.path)
    if not root.exists():
        print(f"❌ Diretório não encontrado: {root}")
        return 1

    # Buscar arquivos com "webhook" no nome ou no path
    webhook_files = list(root.rglob("*webhook*.py"))

    if not webhook_files:
        print(f"⚠ Nenhum arquivo *webhook*.py encontrado em {root}")
        return 0

    all_violations: list[str] = []
    for f in sorted(webhook_files):
        violations = check_file(f)
        all_violations.extend(violations)

    if not all_violations:
        print(f"✅ check_webhook_auth: 0 violations em {len(webhook_files)} arquivo(s)")
        return 0

    print(f"\n❌ check_webhook_auth: {len(all_violations)} violation(s) em {len(webhook_files)} arquivo(s) *webhook*.py:\n")
    for v in all_violations:
        print(f"  {v}")

    print(f"\nTotal: {len(all_violations)} violation(s)")
    print("Resolver adicionando gate de autenticação OU marcando WEBHOOK-AUTH-EXEMPT com justificativa.")

    if args.blocking and len(all_violations) > args.max_violations:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
