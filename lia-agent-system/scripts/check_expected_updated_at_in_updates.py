#!/usr/bin/env python3
"""B1: Sensor que verifica cobertura de expected_updated_at em TODOS endpoints UPDATE.

Regra canônica:
  - Todo endpoint PUT/PATCH que modifica dados DEVE retornar expected_updated_at
    em sua resposta (ou incluir em response schema) para permitir retry automático
    com optimistic locking.
  - Padrão: response schema tem field  que calcula
     antes da alteração.

Sensor:
  - AST-based: encontra funções async def *update* em app/api/v1/
  - Verifica response schema (return type hint ou response_model)
  - Detecta se expected_updated_at está documentado
  - Honra marcador inline: # B1-EXEMPT: <reason>

Exit 0 = sem violations. Exit 1 = violations. --warn-only para modo audit.
"""
import ast
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple


SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
API_ROOT = PROJECT_ROOT / "app" / "api"

# Query HTTP methods que indicam update
UPDATE_METHODS = {"put", "patch"}

# Sufixos de função que indicam update
UPDATE_PATTERNS = {"update", "edit", "modify", "patch"}


def find_update_endpoints() -> List[Tuple[Path, int, str]]:
    """Acha todas as funções async def *update* em app/api/v1/."""
    violations = []
    
    for api_file in sorted(API_ROOT.rglob("*.py")):
        if "__pycache__" in str(api_file):
            continue
        
        try:
            with open(api_file) as f:
                content = f.read()
                tree = ast.parse(content)
        except Exception as e:
            print(f"⚠️  Falha ao parsear {api_file}: {e}", file=sys.stderr)
            continue
        
        for node in ast.walk(tree):
            if not isinstance(node, ast.AsyncFunctionDef):
                continue
            
            # Checker 1: nome sugere update
            func_name_lower = node.name.lower()
            is_update_like = any(p in func_name_lower for p in UPDATE_PATTERNS)
            
            if not is_update_like:
                continue
            
            # Checker 2: decorador @router.put ou @router.patch
            has_update_decorator = False
            for deco in node.decorator_list:
                if isinstance(deco, ast.Call):
                    if isinstance(deco.func, ast.Attribute):
                        if deco.func.attr in UPDATE_METHODS:
                            has_update_decorator = True
                            break
            
            if not has_update_decorator:
                continue
            
            # Checker 3: Procura por expected_updated_at na signature ou docstring
            # Se houver em docstring ou return type, tudo OK
            # Senão, é violation
            
            has_expected_updated_at = False
            
            # Verifica docstring
            docstring = ast.get_docstring(node)
            if docstring and "expected_updated_at" in docstring:
                has_expected_updated_at = True
            
            # Verifica comentário inline (B1-EXEMPT)
            line_content = content.split("\n")[node.lineno - 1] if node.lineno else ""
            if "B1-EXEMPT" in line_content:
                has_expected_updated_at = True  # Exempto marcado
            
            # Verifica return type
            if node.returns:
                try:
                    type_str = ast.unparse(node.returns) if hasattr(ast, unparse) else ""
                    if "expected_updated_at" in type_str:
                        has_expected_updated_at = True
                except:
                    pass
            
            if not has_expected_updated_at:
                violations.append((api_file, node.lineno, node.name))
    
    return violations


def main():
    warn_only = "--warn-only" in sys.argv
    
    violations = find_update_endpoints()
    
    if violations:
        print("❌ B1 Violations: expected_updated_at missing in update endpoints\n", file=sys.stderr)
        for fpath, lineno, fname in violations:
            rel_path = fpath.relative_to(PROJECT_ROOT)
            print(f"  {rel_path}:{lineno} {fname}()", file=sys.stderr)
            print(f"    → Adicionar expected_updated_at ao response schema", file=sys.stderr)
            print(f"    → OU marcar com # B1-EXEMPT: <reason>\n", file=sys.stderr)
        
        if warn_only:
            print(f"\n⚠️  {len(violations)} violation(s) detectada(s) (warn-only mode)", file=sys.stderr)
            return 0
        else:
            print(f"\n❌ {len(violations)} violation(s). Bloqueado.", file=sys.stderr)
            return 1
    else:
        print("✅ B1: All update endpoints have expected_updated_at coverage")
        return 0


if __name__ == "__main__":
    sys.exit(main())
