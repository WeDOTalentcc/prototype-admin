#!/usr/bin/env python3
"""B2: Sensor verifica que TODOS list methods têm ORDER BY.

Regra canônica:
  - Toda query que retorna múltiplos registros (SELECT * ou lista) DEVE ter
    ORDER BY explícito para garantir ordem determinística entre paginações.
  - Sem ORDER BY: ordem é undefined (até pode variar entre execuções).
  - Padrão: .order_by(Model.created_at.desc()) ou similar no final da query.

Sensor:
  - Busca funções async def list_* em app/api/v1/ e app/domains/*/services/
  - Verifica se a função/serviço chama query.order_by(...) ou repository.list_ordered(...)
  - Se usar pagination sem order_by, é violation
  - Honra marcador: # B2-EXEMPT: <reason>

Exit 0 = sem violations. Exit 1 = violations. --warn-only para modo audit.

Referências:
  - AUDIT_GAPS_V3: GAP-02-001 (sort determinístico em list)
  - padrão canonical: repository.list_ordered(filters) ou query.order_by(Model.created_at.desc())
"""
import ast
import sys
import re
from pathlib import Path
from typing import List, Tuple


SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent


def find_list_methods_without_order_by() -> List[Tuple[Path, int, str, str]]:
    """Acha funções list_* que não possuem ORDER BY visível.
    
    Retorna lista de (filepath, lineno, function_name, reason).
    
    Heurística:
    - Se função chama query.all() ou .scalars() sem .order_by() antes = violation
    - Se função chama repository.list(...) sem repository.list_ordered() = OK (skip)
    - Se função tem return padrão/vazio = skip (stub)
    """
    violations = []
    
    # Busca em API endpoints e services
    search_paths = [
        PROJECT_ROOT / "app" / "api" / "v1",
        PROJECT_ROOT / "app" / "domains",
    ]
    
    for base_path in search_paths:
        if not base_path.exists():
            continue
        
        for py_file in sorted(base_path.rglob("*.py")):
            if "__pycache__" in str(py_file) or "test" in str(py_file):
                continue
            
            try:
                with open(py_file) as f:
                    content = f.read()
                    tree = ast.parse(content)
            except Exception as e:
                print(f"⚠️  Falha ao parsear {py_file}: {e}", file=sys.stderr)
                continue
            
            # Procura por funções que fazem list
            for node in ast.walk(tree):
                if not isinstance(node, (ast.AsyncFunctionDef, ast.FunctionDef)):
                    continue
                
                func_name = node.name
                
                # Filtra por nome (list_*, get_all_*, *_list, etc.)
                is_list_like = any([
                    "list" in func_name.lower(),
                    "get_all" in func_name.lower(),
                    func_name.lower().endswith("s"),  # plurals como candidates, jobs
                ])
                
                if not is_list_like:
                    continue
                
                # Verifica se função tem B2-EXEMPT marker
                try:
                    line_content = content.split("\n")[node.lineno - 1] if node.lineno else ""
                except:
                    line_content = ""
                
                if "B2-EXEMPT" in line_content:
                    continue
                
                # Analisa função body para detectar ORDER BY
                func_source = ast.get_source_segment(content, node) if hasattr(ast, "get_source_segment") else ""
                if not func_source:
                    # Fallback: unparse (menos acurado)
                    func_source = ast.unparse(node) if hasattr(ast, "unparse") else ""
                
                # Red flags: tem query/select mas sem order_by
                has_query_call = any([
                    ".select(" in func_source,
                    ".all()" in func_source,
                    ".scalars()" in func_source,
                    "Query(" in func_source,
                ])
                
                has_order_by = any([
                    ".order_by(" in func_source,
                    ".sort_by(" in func_source,
                ])
                
                # Exceção: se chama repository.list_ordered (que já tem order)
                has_repo_list_ordered = ".list_ordered(" in func_source
                
                # Exceção: se é um stub (só tem pass / ...)
                is_stub = (
                    ("pass" in func_source and func_source.count("\n") < 3) or
                    ("..." in func_source and func_source.count("\n") < 3)
                )
                
                if has_query_call and not has_order_by and not has_repo_list_ordered and not is_stub:
                    violations.append((
                        py_file,
                        node.lineno,
                        func_name,
                        "query/.all()/.scalars() sem .order_by()"
                    ))
    
    return violations


def main():
    warn_only = "--warn-only" in sys.argv
    blocking = "--blocking" not in sys.argv  # Default: warn-only (inverso de blocking)
    
    violations = find_list_methods_without_order_by()
    
    if violations:
        print("❌ B2 Violations: list methods sem ORDER BY\n", file=sys.stderr)
        for fpath, lineno, fname, reason in violations:
            rel_path = fpath.relative_to(PROJECT_ROOT)
            print(f"  {rel_path}:{lineno} {fname}()", file=sys.stderr)
            print(f"    → {reason}", file=sys.stderr)
            print(f"    → Adicionar .order_by(Model.created_at.desc()) ou similar", file=sys.stderr)
            print(f"    → OU usar repository.list_ordered() que já tem ORDER BY", file=sys.stderr)
            print(f"    → OU marcar com # B2-EXEMPT: <reason>\n", file=sys.stderr)
        
        if warn_only:
            print(f"\n⚠️  {len(violations)} violation(s) detectada(s) (warn-only mode)", file=sys.stderr)
            return 0
        else:
            print(f"\n❌ {len(violations)} violation(s). Bloqueado.", file=sys.stderr)
            return 1
    else:
        print("✅ B2: All list methods have deterministic ordering (ORDER BY)")
        return 0


if __name__ == "__main__":
    sys.exit(main())
