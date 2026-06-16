#!/usr/bin/env python3
"""AST sensor — PipelineTemplateRepository public methods MUST call _require_company_id.

Multi-tenancy canonical (CLAUDE.md REGRA #1): toda operação que recebe company_id
externo (path param, JWT, payload) DEVE validar via _require_company_id antes de
qualquer read/write. Pipeline templates são tenant-scoped; vazamento cross-tenant
quebra LGPD.

Métodos públicos QUE PRECISAM do guard (recebem company_id externo):
  list_for_company, get_by_id, clear_default, create, clone, count_active,
  get_by_name, seed_defaults, list_for_suggestion

Métodos públicos isentos (operam sobre instância já carregada — não recebem
company_id externo, multi-tenancy é responsabilidade do caller que carregou
o template via get_by_id):
  increment_usage, update, soft_delete, archive

Exit:
  0 — todos os métodos protegidos OK
  1 — pelo menos 1 método público listado não chama _require_company_id
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "app" / "domains" / "pipeline" / "repositories" / "pipeline_template_repository.py"

# Métodos públicos que DEVEM chamar _require_company_id no body.
METHODS_REQUIRING_GUARD = frozenset({
    "list_for_company",
    "get_by_id",
    "clear_default",
    "create",
    "clone",
    "count_active",
    "get_by_name",
    "seed_defaults",
    "list_for_suggestion",
})

GUARD_FUNC = "_require_company_id"


def function_calls_guard(func: ast.AsyncFunctionDef | ast.FunctionDef) -> bool:
    for node in ast.walk(func):
        if isinstance(node, ast.Call):
            target = node.func
            if isinstance(target, ast.Name) and target.id == GUARD_FUNC:
                return True
            if isinstance(target, ast.Attribute) and target.attr == GUARD_FUNC:
                return True
    return False


def main() -> int:
    if not TARGET.exists():
        print(f"❌ Sensor pipeline template multi-tenancy: arquivo não encontrado: {TARGET}")
        return 1

    source = TARGET.read_text(encoding="utf-8")
    try:
        tree = ast.parse(source)
    except SyntaxError as e:
        print(f"❌ Syntax error em {TARGET}: {e}")
        return 1

    repo_class: ast.ClassDef | None = None
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == "PipelineTemplateRepository":
            repo_class = node
            break

    if repo_class is None:
        print("❌ class PipelineTemplateRepository não encontrada em pipeline_template_repository.py")
        return 1

    offenders: list[tuple[str, int]] = []
    checked = 0
    for item in repo_class.body:
        if not isinstance(item, (ast.AsyncFunctionDef, ast.FunctionDef)):
            continue
        name = item.name
        if name.startswith("_"):
            continue
        if name not in METHODS_REQUIRING_GUARD:
            continue
        checked += 1
        if not function_calls_guard(item):
            offenders.append((name, item.lineno))

    if offenders:
        print(f"❌ PipelineTemplateRepository: {len(offenders)} método(s) público(s) sem _require_company_id no body:")
        for name, lineno in offenders:
            print(f"  PipelineTemplateRepository.{name} (linha {lineno}): falta _require_company_id no body.")
            print(f"  → Fix: adicionar _require_company_id(company_id) como primeiro statement do método {name}.")
        return 1

    print(f"✅ Pipeline template multi-tenancy OK ({checked} públicos checados)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
