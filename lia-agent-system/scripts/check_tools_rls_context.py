#!/usr/bin/env python3
"""Sensor canonical RLS (2026-06-04, v2 — PRODUTOR).

HISTORICO: v1 (2026-06-03) escaneava ~226 CONSUMIDORES (tools que abrem
AsyncSessionLocal cru) exigindo set_tenant_context/tenant_session em cada um.
Isso era fix-no-consumidor (anti canonical-fix #3). v2 troca pelo fix no
PRODUTOR: um listener no engine `begin` (lia_config.database
:_inject_tenant_guc_on_begin) injeta app.company_id do contextvar
_current_company_id em TODA transacao, igual ao get_db do caminho HTTP. Isso
corrige todas as tools de uma vez + futuras.

Este sensor agora GUARDA O PRODUTOR: se o listener sumir, o agentic loop volta
a ficar cego (RLS FORCED em ~241 tabelas bloqueia tudo). Espelha o teste
tests/contract/test_engine_rls_autoinject.py (introspeccao em runtime); aqui e
estatico (AST) p/ rodar em pre-commit sem subir o engine.

Uso:
  python3 scripts/check_tools_rls_context.py            # warn-only (exit 0)
  python3 scripts/check_tools_rls_context.py --blocking # exit 1 se produtor ausente
  python3 scripts/check_tools_rls_context.py --audit-consumers  # lista tools c/
        sessao crua (informativo; defense-in-depth, NUNCA bloqueante)
"""
from __future__ import annotations
import ast, sys, glob, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRODUCER_FILE = os.path.join(ROOT, "libs/config/lia_config/database.py")
LISTENER = "_inject_tenant_guc_on_begin"
SET_CONFIG = "set_config('app.company_id'"

CONSUMER_PATTERNS = [
    "app/domains/**/tools/**/*.py",
    "app/domains/**/agents/*tool*registry*.py",
]
OPEN = "AsyncSessionLocal"
SAFE = ("set_tenant_context", "tenant_session", "get_tenant_db")
EXEMPT = "RLS-EXEMPT"


def check_producer() -> list[str]:
    """Retorna lista de problemas (vazia = produtor OK)."""
    problems = []
    try:
        text = open(PRODUCER_FILE, encoding="utf-8").read()
    except Exception as exc:
        return [f"nao consegui ler {PRODUCER_FILE}: {exc}"]
    if LISTENER not in text:
        problems.append(f"funcao {LISTENER}() AUSENTE em {PRODUCER_FILE}")
    if SET_CONFIG not in text:
        problems.append(f"set_config('app.company_id', ...) AUSENTE em {PRODUCER_FILE}")
    # confirma registro via decorator @event.listens_for(engine.sync_engine, "begin")
    if 'listens_for(engine.sync_engine, "begin")' not in text and \
       "listens_for(engine.sync_engine, 'begin')" not in text:
        problems.append("listener nao registrado no evento `begin` do engine")
    return problems


def audit_consumers() -> list[tuple[str, int, str]]:
    files = set()
    for pat in CONSUMER_PATTERNS:
        files.update(glob.glob(os.path.join(ROOT, pat), recursive=True))
    viol = []
    for path in sorted(files):
        try:
            text = open(path, encoding="utf-8").read()
        except Exception:
            continue
        if OPEN not in text:
            continue
        lines = text.splitlines()
        try:
            tree = ast.parse(text)
        except SyntaxError:
            continue
        rel = os.path.relpath(path, ROOT)
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            body = "\n".join(lines[node.lineno - 1: node.end_lineno])
            if OPEN not in body or any(s in body for s in SAFE) or EXEMPT in body:
                continue
            viol.append((rel, node.lineno, node.name))
    return viol


def main():
    blocking = "--blocking" in sys.argv
    problems = check_producer()
    if problems:
        print("ERRO — fix RLS no PRODUTOR ausente/quebrado:")
        for p in problems:
            print(f"  - {p}")
        print("\nO agentic loop (LIA-A04) ficara CEGO: RLS FORCED bloqueia tudo.")
        print("Fix: restaure o listener @event.listens_for(engine.sync_engine, \"begin\")")
        print("     em libs/config/lia_config/database.py que injeta app.company_id")
        print("     do contextvar _current_company_id (espelha get_db).")
        if blocking:
            return 1
        return 0
    print("OK — fix RLS no produtor presente (engine begin -> set_config app.company_id).")
    if "--audit-consumers" in sys.argv:
        viol = audit_consumers()
        print(f"\n[informativo] {len(viol)} tool(s) abrem AsyncSessionLocal cru.")
        print("Cobertas pelo produtor (auto-inject). Contexto explicito e opcional")
        print("(defense-in-depth p/ writes sensiveis). NUNCA bloqueante.")
        for rel, ln, fn in viol:
            print(f"  {rel}:{ln} {fn}()")
    return 0


if __name__ == "__main__":
    sys.exit(main())
