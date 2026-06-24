#!/usr/bin/env python3
"""Sensor canonical: detecta uso de validate_rails_token_from_env fora dos pontos permitidos.

FastAPI JWT e a fonte de verdade (2026-06-13).
Rails JWT so e aceito em POST /auth/exchange (endpoint de migracao).

Pontos permitidos (EXEMPT):
  - app/auth/rails_jwt.py (definicao)
  - app/auth/rails_user_sync.py (sync helper, chamado pelo exchange)
  - app/api/v1/auth.py (endpoint de exchange -- unico ponto legitimo)
  - app/middleware/auth_enforcement.py (retorna 401 upgrade_required -- comportamento correto)

Detecta usos fora desses pontos.

Uso:
    python scripts/check_rails_jwt_usage.py [--block]
"""
from __future__ import annotations
import ast, sys
from pathlib import Path

EXEMPT_FILES = {
    "app/auth/rails_jwt.py",
    "app/auth/rails_user_sync.py",
    "app/api/v1/auth.py",
    "app/middleware/auth_enforcement.py",
    # _resolve_rails_jwt_user is defined here and called only from /auth/exchange
    "app/auth/dependencies.py",
}

TARGET_NAMES = {"validate_rails_token_from_env", "_resolve_rails_jwt_user", "fetch_rails_user_info"}


def check(block=False):
    repo_root = Path(__file__).resolve().parent.parent
    violations = []

    for py_file in (repo_root / "app").rglob("*.py"):
        if "__pycache__" in str(py_file):
            continue
        rel = str(py_file.relative_to(repo_root))
        if rel in EXEMPT_FILES:
            continue
        try:
            source = py_file.read_text(encoding="utf-8")
        except Exception:
            continue
        if not any(name in source for name in TARGET_NAMES):
            continue
        try:
            tree = ast.parse(source)
        except Exception:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Name) and node.id in TARGET_NAMES:
                violations.append((rel, node.lineno, node.id))
            elif isinstance(node, ast.Attribute) and node.attr in TARGET_NAMES:
                violations.append((rel, node.lineno, node.attr))

    # Dedup by (file, name)
    seen = set()
    deduped = []
    for v in violations:
        key = (v[0], v[2])
        if key not in seen:
            seen.add(key)
            deduped.append(v)

    if deduped:
        print(f"[RAILS-JWT] {len(deduped)} usos de Rails JWT fora dos pontos permitidos:")
        for f, line, name in deduped[:15]:
            print(f"  {f}:{line} -- {name}()")
        print()
        print("CORRECAO: remover uso de Rails JWT. FastAPI JWT e a fonte de verdade.")
        print("Se o cliente tem Rails JWT, deve chamar POST /api/v1/auth/exchange primeiro.")
        mode = "BLOCKING" if block else "WARN-ONLY"
        print(f"Mode: {mode}")
        return 1 if block else 0

    print("[RAILS-JWT] OK -- 0 usos de Rails JWT fora dos pontos permitidos")
    return 0


if __name__ == "__main__":
    sys.exit(check(block="--block" in sys.argv))
