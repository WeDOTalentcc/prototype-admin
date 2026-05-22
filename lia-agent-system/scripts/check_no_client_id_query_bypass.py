#!/usr/bin/env python3
"""SENSOR (harness-engineering: B.2 client_id "platform" sentinel bypass).

Registrado 2026-05-21 — HARDENING_PLAN.md Bloco B.2 (P1.1 specific).

AST + regex checker que detecta o padrao residual de bypass cross-tenant
via sentinela magica `client_id == "platform"` (ou similar) em arquivos
de `app/api/**/*.py`. Falha CI se a sentinela aparecer dentro de uma
expressao condicional que NAO esta acompanhada de um role-check
correspondente (super_admin / wedotalent_admin).

Por que:
  Audit 2026-05-21 (P1.1) descobriu que `app/api/v1/audit_logs.py`
  permitia bypass via `client_id=platform` sem verificar role do user
  autenticado. Qualquer user passava `?client_id=platform` e
  escapava o tenant filter (ver SOXAuditLog). Fix removeu sentinela;
  este sensor previne reintroducao.

Pattern detectado:
  - Comparacao literal `== "platform"` ou `!= "platform"` em filter logic
  - String "platform" em filter conditions sem role check no mesmo escopo
  - Substituicoes equivalentes (filter_client_id, filter_company_id, etc.)

Modo: BLOCKING por default (baseline esperada = 0 apos fix P1.1).

Use --warn-only para opt-out (so deveria ser usado pra investigar
falsos positivos antes de adicionar a SKIP).

Output: PATH:LINE  message  com FIX inline.

Uso:
    python3 scripts/check_no_client_id_query_bypass.py [--warn-only]
                                                       [--json]
"""
from __future__ import annotations

import argparse
import ast
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
API_DIR = ROOT / "app" / "api"

# Sentinela magica P1.1
SENTINEL_VALUES = frozenset({"platform"})

# Field names que comumente atuam como tenant identifier no payload/query
TENANT_FIELD_NAMES = frozenset({
    "client_id",
    "company_id",
    "filter_client_id",
    "filter_company_id",
    "tenant_id",
    "owner_id",
})

# Role check tokens — se aparecerem na mesma function/scope que o
# sentinel, consideramos OK (super admin bypass legitimo).
ROLE_CHECK_TOKENS = frozenset({
    "wedotalent_admin",
    "super_admin",
    "is_superuser",
    "is_super_admin",
    "is_admin",
    "platform_admin",
    "UserRole.wedotalent_admin",
    "UserRole.super_admin",
    "Role.wedotalent_admin",
    "user.role",
})

# Skip patterns — arquivos que legitimamente referenciam "platform"
# por motivos nao-tenant (ex: external_webhooks que parsea platform name)
SKIP_PATTERNS = (
    "external_webhooks.py",  # platform = github/gitlab/etc, nao tenant sentinel
)

# Marker pra opt-out explicito
EXEMPT_MARKER = "CLIENT-ID-BYPASS-EXEMPT"


@dataclass
class Hit:
    path: Path
    line: int
    snippet: str
    reason: str
    fix: str


def is_skip_file(path: Path) -> bool:
    return any(skip in path.name for skip in SKIP_PATTERNS)


def has_exempt_in_window(src_lines: list[str], lineno: int, window: int = 5) -> bool:
    start = max(0, lineno - 1 - window)
    end = min(len(src_lines), lineno + 1)
    chunk = "\n".join(src_lines[start:end])
    return EXEMPT_MARKER in chunk


def function_scope_has_role_check(func_node: ast.AST) -> bool:
    """Retorna True se a function contem qualquer token de role check."""
    src_snippet = ast.unparse(func_node) if hasattr(ast, "unparse") else ""
    if not src_snippet:
        return False
    for token in ROLE_CHECK_TOKENS:
        if token in src_snippet:
            return True
    return False


def find_enclosing_function(tree: ast.AST, target_node: ast.AST) -> ast.AST | None:
    """Encontra o FunctionDef/AsyncFunctionDef que contem target_node."""
    target_id = id(target_node)
    for n in ast.walk(tree):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for descendant in ast.walk(n):
                if id(descendant) == target_id:
                    return n
    return None


def is_string_literal(node: ast.AST, value: str) -> bool:
    """True se node eh ast.Constant(value=value) string."""
    return (
        isinstance(node, ast.Constant)
        and isinstance(node.value, str)
        and node.value == value
    )


def is_tenant_field_ref(node: ast.AST) -> bool:
    """True se node referencia um tenant-field-like name."""
    if isinstance(node, ast.Name) and node.id in TENANT_FIELD_NAMES:
        return True
    if isinstance(node, ast.Attribute) and node.attr in TENANT_FIELD_NAMES:
        return True
    return False


def detect_sentinel_compares(tree: ast.AST, src_lines: list[str]) -> list[tuple[int, str, str]]:
    """Detecta comparacoes literais com sentinela 'platform'.

    Pattern:
      - client_id == "platform"
      - client_id != "platform"
      - "platform" == client_id (raro mas valido)
      - str(client_id) == "platform"

    Retorna [(lineno, snippet, reason)].
    """
    findings: list[tuple[int, str, str]] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Compare):
            # left + comparators
            operands = [node.left] + list(node.comparators)
            has_sentinel = False
            has_tenant_field = False
            for op in operands:
                # str(client_id) wrapper
                target = op
                if isinstance(op, ast.Call) and isinstance(op.func, ast.Name) and op.func.id == "str":
                    if op.args:
                        target = op.args[0]
                for sentinel in SENTINEL_VALUES:
                    if is_string_literal(target, sentinel):
                        has_sentinel = True
                if is_tenant_field_ref(target):
                    has_tenant_field = True

            if has_sentinel and has_tenant_field:
                lineno = node.lineno
                snippet = src_lines[lineno - 1].strip()[:140] if lineno <= len(src_lines) else ""
                findings.append((
                    lineno,
                    snippet,
                    "sentinel 'platform' compared with tenant-field",
                ))

    return findings


def detect_in_membership(tree: ast.AST, src_lines: list[str]) -> list[tuple[int, str, str]]:
    """Detecta `client_id in (..., "platform", ...)` ou
    `"platform" in client_ids_list`."""
    findings: list[tuple[int, str, str]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Compare):
            continue
        for op, right in zip(node.ops, node.comparators):
            if not isinstance(op, (ast.In, ast.NotIn)):
                continue
            # esquerda eh tenant field?
            left_is_tenant = is_tenant_field_ref(node.left)
            # checar se "platform" esta na coleção direita
            sentinel_in_collection = False
            if isinstance(right, (ast.Tuple, ast.List, ast.Set)):
                for elt in right.elts:
                    for sentinel in SENTINEL_VALUES:
                        if is_string_literal(elt, sentinel):
                            sentinel_in_collection = True
            if left_is_tenant and sentinel_in_collection:
                lineno = node.lineno
                snippet = src_lines[lineno - 1].strip()[:140] if lineno <= len(src_lines) else ""
                findings.append((
                    lineno,
                    snippet,
                    "tenant-field membership test contains 'platform' sentinel",
                ))
    return findings


def scan_file(path: Path) -> list[Hit]:
    if is_skip_file(path):
        return []

    try:
        src = path.read_text(encoding="utf-8")
        tree = ast.parse(src, filename=str(path))
    except (OSError, SyntaxError, UnicodeDecodeError):
        return []

    src_lines = src.splitlines()
    hits: list[Hit] = []

    candidates: list[tuple[int, str, str, ast.AST | None]] = []

    for lineno, snippet, reason in detect_sentinel_compares(tree, src_lines):
        # achar enclosing function pra checar role gate
        node_at_line = None
        for n in ast.walk(tree):
            if getattr(n, "lineno", None) == lineno and isinstance(n, ast.Compare):
                node_at_line = n
                break
        candidates.append((lineno, snippet, reason, node_at_line))

    for lineno, snippet, reason in detect_in_membership(tree, src_lines):
        node_at_line = None
        for n in ast.walk(tree):
            if getattr(n, "lineno", None) == lineno and isinstance(n, ast.Compare):
                node_at_line = n
                break
        candidates.append((lineno, snippet, reason, node_at_line))

    for lineno, snippet, reason, target_node in candidates:
        if has_exempt_in_window(src_lines, lineno):
            continue

        # Se a enclosing function tem role check, considerar OK (super admin
        # legitimo). Caso contrario, hit.
        ok_via_role_check = False
        if target_node is not None:
            enclosing = find_enclosing_function(tree, target_node)
            if enclosing is not None and function_scope_has_role_check(enclosing):
                ok_via_role_check = True

        if ok_via_role_check:
            continue

        fix = (
            "Sentinela 'platform' bypassa filtro multi-tenancy. Remover OR\n"
            "  adicionar role check explicito ANTES da comparacao:\n"
            "    if user.role != UserRole.wedotalent_admin:\n"
            "        raise HTTPException(403, 'super admin only')\n"
            "    # so chega aqui se for super admin\n"
            "Alternativa: marker CLIENT-ID-BYPASS-EXEMPT inline se ja ha role\n"
            "  check em layer superior (dependency injection)."
        )
        hits.append(Hit(
            path=path,
            line=lineno,
            snippet=snippet,
            reason=reason,
            fix=fix,
        ))

    return hits


def find_api_files() -> list[Path]:
    if not API_DIR.exists():
        return []
    return sorted(p for p in API_DIR.rglob("*.py") if p.is_file())


def format_hit(hit: Hit) -> str:
    try:
        rel = hit.path.relative_to(ROOT)
    except ValueError:
        rel = hit.path
    return f"{rel}:{hit.line}  {hit.reason}\n    SNIPPET: {hit.snippet}\n    FIX:\n      {hit.fix.replace(chr(10), chr(10) + '      ')}"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="AST checker: client_id 'platform' sentinel bypass (P1.1)"
    )
    parser.add_argument("--warn-only", action="store_true", help="Exit 0 mesmo se houver violations")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    args = parser.parse_args(argv)

    files = find_api_files()
    all_hits: list[Hit] = []
    for f in files:
        all_hits.extend(scan_file(f))

    count = len(all_hits)

    if args.json:
        import json
        payload = {
            "count": count,
            "scanned_files": len(files),
            "hits": [
                {
                    "path": str(h.path.relative_to(ROOT)) if h.path.is_absolute() else str(h.path),
                    "line": h.line,
                    "reason": h.reason,
                    "snippet": h.snippet,
                    "fix": h.fix,
                }
                for h in all_hits
            ],
        }
        print(json.dumps(payload, indent=2))
    else:
        if count == 0:
            print(
                f"[B.2 client-id-bypass sensor] OK — scanned {len(files)} api files in "
                f"app/api/, 0 'platform' sentinel bypasses detected. Baseline 0 mantido."
            )
            return 0

        for h in all_hits:
            print(format_hit(h))
            print()
        print(
            f"\n[B.2 client-id-bypass sensor] FAIL: {count} sentinel bypass(es) "
            "encontrado(s). Baseline canonical = 0 (apos fix P1.1).",
            file=sys.stderr,
        )

    if args.warn_only:
        return 0

    return 1 if count > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
