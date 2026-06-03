#!/usr/bin/env python3
"""Sensor canonical (2026-06-03): tools/loops que abrem AsyncSessionLocal DEVEM
setar o contexto RLS (tenant_session / set_tenant_context) na mesma funcao.

ROOT CAUSE (chat cego): RLS habilitado+FORCED em ~241 tabelas. Tool que abre
sessao sem o GUC app.company_id -> RLS bloqueia tudo -> retorna 0 no agentic
loop (fora do middleware HTTP). Ver app/core/database.py:tenant_session.

Escopo: app/domains/**/tools/*.py e **/agents/*tool*.py (camada de tools).
Exit 0 (warn-only) por padrao; --blocking exit 1 se > --max (default 0).
Marker de opt-out: `# RLS-EXEMPT: <motivo>` na funcao.
Output otimizado p/ LLM: instrucao de fix embutida.
"""
from __future__ import annotations
import ast, sys, glob, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATTERNS = [
    "app/domains/**/tools/**/*.py",
    "app/domains/**/agents/*tool*registry*.py",
]
SAFE = ("set_tenant_context", "tenant_session", "get_tenant_db")
OPEN = "AsyncSessionLocal"
EXEMPT = "RLS-EXEMPT"


def _src(node, lines):
    seg = lines[node.lineno - 1: node.end_lineno]
    return "\n".join(seg)


def scan_file(path):
    rel = os.path.relpath(path, ROOT)
    try:
        text = open(path, encoding="utf-8").read()
    except Exception:
        return []
    if OPEN not in text:
        return []
    lines = text.splitlines()
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return []
    viol = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        body = _src(node, lines)
        if OPEN not in body:
            continue
        if any(s in body for s in SAFE):
            continue
        if EXEMPT in body:
            continue
        viol.append((rel, node.lineno, node.name))
    return viol


def main():
    blocking = "--blocking" in sys.argv
    files = set()
    for pat in PATTERNS:
        files.update(glob.glob(os.path.join(ROOT, pat), recursive=True))
    all_viol = []
    for f in sorted(files):
        all_viol.extend(scan_file(f))
    for rel, ln, fn in all_viol:
        print(f"[RLS] {rel}:{ln} {fn}() abre AsyncSessionLocal sem contexto RLS")
    if all_viol:
        print(f"\n{len(all_viol)} tool(s) sem contexto RLS.")
        print("Fix: troque `async with AsyncSessionLocal() as db:` por")
        print("     `async with tenant_session(company_id) as db:` (app/core/database.py)")
        print("     OU chame `await set_tenant_context(db, company_id)` apos abrir.")
        print("Sem isso a tool retorna 0 no agentic loop (RLS FORCED em ~241 tabelas).")
        print("Opt-out justificado: comente `# RLS-EXEMPT: <motivo>` na funcao.")
    else:
        print("OK — nenhuma tool sem contexto RLS.")
    if blocking and len(all_viol) > 0:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
