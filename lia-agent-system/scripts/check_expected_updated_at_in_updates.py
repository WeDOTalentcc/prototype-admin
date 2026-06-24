#!/usr/bin/env python3
"""B1 Sensor: expected_updated_at coverage in UPDATE endpoints.

REGRA CANÔNICA (GAP-03-003, registrada 2026-06-18):
  - Todo endpoint PUT/PATCH que modifica dados DEVE retornar
     no response schema.
  - Campo contém o valor de  PRÉ-alteração (antes da mudança).
  - Permite retry automático com optimistic locking em caso de conflito.
  - Padrão:
    1. Service checa  antes de alterar
    2. API retorna aquele valor no response (expected_updated_at)
    3. Client envia esse valor em request subsequente (via Retry-If-Match header)
    4. Service valida: se divergiu = 409 Conflict, cliente refaz

SENSOR COMPUTACIONAL (AST-based):
  - Encontra todas as funções async def *update* em app/api/v1/
  - Valida que response schema (return type ou response_model) menciona expected_updated_at
  - Honra marcador inline: # B1-EXEMPT: <reason> para exceções documentadas

EXEMPTIONS VÁLIDAS (B1-EXEMPT):
  - "admin read-only" — endpoint de administração que não persiste
  - "metadata-only update" — apenas flags, sem persistência de dados de negócio
  - "status enum" — transição de estado que não precisa optimistic locking

VIOLAÇÃO (falta expected_updated_at):
  - Endpoint PUT/PATCH retorna modelo com created_at/updated_at mas não expected_updated_at
  - Resultado: cliente não consegue implementar retry automático
  - Risco: data race silencioso se múltiplos clientes atualizam simultaneamente

EXIT CODES:
  - 0: sem violations ou warn-only
  - 1: violations encontradas (BLOCKING)

USAGE:
  python3 scripts/check_expected_updated_at_in_updates.py [--warn-only]
"""
import ast
import sys
from pathlib import Path
from typing import List, Tuple


SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
API_ROOT = PROJECT_ROOT / "app" / "api"

UPDATE_METHODS = {"put", "patch"}
UPDATE_PATTERNS = {"update", "edit", "modify", "patch"}


def find_update_endpoints() -> List[Tuple[Path, int, str]]:
    """Acha funções async def *update* em app/api/v1/ sem expected_updated_at."""
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
            
            func_name_lower = node.name.lower()
            is_update_like = any(p in func_name_lower for p in UPDATE_PATTERNS)
            if not is_update_like:
                continue
            
            has_update_decorator = False
            for deco in node.decorator_list:
                if isinstance(deco, ast.Call):
                    if isinstance(deco.func, ast.Attribute):
                        if deco.func.attr in UPDATE_METHODS:
                            has_update_decorator = True
                            break
            
            if not has_update_decorator:
                continue
            
            has_expected_updated_at = False
            
            docstring = ast.get_docstring(node)
            if docstring and "expected_updated_at" in docstring:
                has_expected_updated_at = True
            
            line_content = content.split("\n")[node.lineno - 1] if node.lineno else ""
            if "B1-EXEMPT" in line_content:
                has_expected_updated_at = True
            
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
            print(f"\n⚠️  {len(violations)} violation(s) (warn-only mode)", file=sys.stderr)
            return 0
        else:
            print(f"\n❌ {len(violations)} violation(s). Bloqueado.", file=sys.stderr)
            return 1
    else:
        print("✅ B1: All update endpoints have expected_updated_at coverage")
        return 0


if __name__ == "__main__":
    sys.exit(main())
