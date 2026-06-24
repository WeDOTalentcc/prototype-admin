#!/usr/bin/env python3
"""B2 Sensor: ORDER BY in all list methods (deterministic ordering).

REGRA CANÔNICA (GAP-03-005, registrada 2026-06-18):
  - Todo método list_* em Repository classes DEVE incluir ORDER BY explícito.
  - Sem ORDER BY = resultado não-determinístico = flakey tests.
  - Padrão:
    1. Repository.list_* sempre retorna query.order_by(Model.created_at.desc())
    2. OU order_by(Model.id) se created_at não apropriado
    3. OU order_by(...) com campo semanticamente apropriado ao domínio
  - Default recomendado: .order_by(Model.created_at.desc()) (mais recente primeiro)

SENSOR COMPUTACIONAL (AST-based):
  - Encontra def list_* em app/domains/*/repositories/
  - Valida que source contém .order_by() após select()
  - Honra marcador inline: # B2-EXEMPT: <reason> para casos especiais

EXEMPTIONS VÁLIDAS (B2-EXEMPT):
  - "aggregation query" — COUNT/SUM que retorna escalar, não lista
  - "unordered acceptable" — cases extremamente raros onde ordem não importa (comentar porquê)
  - "client-side sort" — client pede dados unsorted pra fazer sua própria sort (raro, documentar)

VIOLAÇÃO (falta .order_by()):
  - query.select(Model).all() sem .order_by()
  - Resultado: ordem impredictível entre runs
  - Risco: testes flakeyy, debugging difícil ("às vezes passa, às vezes falha")

EXIT CODES:
  - 0: sem violations ou warn-only
  - 1: violations encontradas (BLOCKING)

USAGE:
  python3 scripts/check_list_methods_have_order_by.py [--warn-only]
"""
import ast
import sys
from pathlib import Path
from typing import List, Tuple


SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
REPOS_ROOT = PROJECT_ROOT / "app" / "domains"


def find_list_methods_missing_order_by() -> List[Tuple[Path, int, str]]:
    """Acha métodos list_* em repositories sem ORDER BY."""
    violations = []
    
    for repo_file in sorted(REPOS_ROOT.rglob("repositories/*.py")):
        if "__pycache__" in str(repo_file):
            continue
        
        try:
            with open(repo_file) as f:
                content = f.read()
                tree = ast.parse(content)
        except Exception as e:
            print(f"⚠️  Falha ao parsear {repo_file}: {e}", file=sys.stderr)
            continue
        
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            
            if not node.name.startswith("list_"):
                continue
            
            func_first_line = node.lineno
            if func_first_line and func_first_line > 0:
                lines = content.split("\n")
                func_line = lines[func_first_line - 1] if func_first_line <= len(lines) else ""
                if "B2-EXEMPT" in func_line:
                    continue
            
            has_select = False
            has_order_by = False
            
            func_source = ast.get_source_segment(content, node) or ""
            
            if "select(" in func_source:
                has_select = True
                if ".order_by(" in func_source:
                    has_order_by = True
            
            if has_select and not has_order_by:
                violations.append((repo_file, node.lineno, node.name))
    
    return violations


def main():
    warn_only = "--warn-only" in sys.argv
    violations = find_list_methods_missing_order_by()
    
    if violations:
        print("❌ B2 Violations: list methods missing ORDER BY\n", file=sys.stderr)
        for fpath, lineno, fname in violations:
            rel_path = fpath.relative_to(PROJECT_ROOT)
            print(f"  {rel_path}:{lineno} {fname}()", file=sys.stderr)
            print(f"    → Adicionar .order_by(...) ao select()", file=sys.stderr)
            print(f"    → Padrão: .order_by(Model.created_at.desc())", file=sys.stderr)
            print(f"    → OU marcar com # B2-EXEMPT: <reason>\n", file=sys.stderr)
        
        if warn_only:
            print(f"\n⚠️  {len(violations)} violation(s) (warn-only mode)", file=sys.stderr)
            return 0
        else:
            print(f"\n❌ {len(violations)} violation(s). Bloqueado.", file=sys.stderr)
            return 1
    else:
        print("✅ B2: All list methods have ORDER BY")
        return 0


if __name__ == "__main__":
    sys.exit(main())
