#!/usr/bin/env python3
"""Sensor canonical: detecta permissoes hardcoded em codigo de endpoint.

Regra RBAC canonical (Sprint C 2026-06-13):
  Toda permissao DEVE existir em DEFAULT_ROLE_PERMISSIONS (role_scope_filters seed).
  Guardar permissao em decorator/codigo de rota e ANTI-PATTERN.

Detecta:
  - current_user.role != UserRole.X como guard em app/api/v1/
  - Comparacoes de role inline que nao passam pelo ScopeFilterService

Modo: WARN-ONLY inicial. Promover BLOCKING quando baseline = 0.

Uso:
    python scripts/check_hardcoded_permissions.py [--block]
"""
from __future__ import annotations
import ast
import sys
from pathlib import Path


def _load_seed_permissions():
    """Carrega permissoes do DEFAULT_ROLE_PERMISSIONS como set de strings."""
    try:
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from lia_models.role_scope_filter import DEFAULT_ROLE_PERMISSIONS
        return {f"{p['role']}:{p['resource']}:{p['action']}" for p in DEFAULT_ROLE_PERMISSIONS}
    except Exception as e:
        print(f"[RBAC-SENSOR] Nao foi possivel carregar seed: {e}", file=sys.stderr)
        return set()


def check(block: bool = False) -> int:
    repo_root = Path(__file__).resolve().parent.parent
    seed_perms = _load_seed_permissions()
    violations = []

    api_dir = repo_root / "app" / "api" / "v1"
    if not api_dir.exists():
        print("[RBAC-GUIDE] OK - app/api/v1/ nao encontrado, nada a verificar")
        return 0

    for py_file in api_dir.rglob("*.py"):
        if "__pycache__" in str(py_file):
            continue
        try:
            source = py_file.read_text(encoding="utf-8")
            source_lines = source.splitlines()
            tree = ast.parse(source)
        except Exception:
            continue

        for node in ast.walk(tree):
            if isinstance(node, (ast.Compare, ast.If)):
                try:
                    src_snippet = ast.unparse(node)
                except Exception:
                    continue
                if "UserRole." in src_snippet and "role" in src_snippet:
                    if "wedotalent_admin" not in src_snippet:
                        violations.append((
                            str(py_file.relative_to(repo_root)),
                            node.lineno,
                            f"Possivel gate de role hardcoded: {src_snippet[:80]}",
                        ))

    if violations:
        print(f"[RBAC-GUIDE] {len(violations)} possiveis permissoes hardcoded detectadas:")
        for f, line, msg in violations[:20]:
            print(f"  {f}:{line} -- {msg}")
        print()
        print("CORRECAO canonical:")
        print("  1. Adicionar permissao em DEFAULT_ROLE_PERMISSIONS (lia_models/role_scope_filter.py)")
        print("  2. Substituir guard inline por: await get_scope_filter_service().is_allowed(role, resource, action, db)")
        print("  3. Executar POST /rbac/permissions/seed para propagar ao banco")
        mode = "BLOCKING" if block else "WARN-ONLY"
        print(f"Mode: {mode}")
        return 1 if block else 0

    print("[RBAC-GUIDE] OK -- 0 permissoes hardcoded detectadas")
    return 0


if __name__ == "__main__":
    block_mode = "--block" in sys.argv
    sys.exit(check(block=block_mode))
