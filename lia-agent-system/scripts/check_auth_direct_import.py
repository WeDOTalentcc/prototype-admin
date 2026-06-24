#!/usr/bin/env python3
"""Sensor canonical: detecta imports diretos de app/auth/ fora da camada de auth.

Regra Auth canonical (Sprint Auth-light 2026-06-13):
  Sub-apps e dominios devem importar de app.shared.auth.auth_provider,
  nao de app.auth.* diretamente.
  Excecoes legítimas: app/auth/ si mesmo, app/shared/auth/, app/middleware/.

Detecta:
  from app.auth.dependencies import ... em apps/ (sub-apps Sprint F)
  from app.auth.security import ... em apps/ (sub-apps Sprint F)

Modo: WARN-ONLY (baseline muito alto — 3700 endpoints, mudanca gradual).
      Scopo restrito a sub-apps (apps/) para nao criar ruído no monolito existente.

Uso:
    python scripts/check_auth_direct_import.py
    python scripts/check_auth_direct_import.py --block
"""
from __future__ import annotations
import ast
import sys
from pathlib import Path

EXEMPT_PATHS = {
    "app/auth",
    "app/shared/auth",
    "app/middleware",
    "tests",
    "scripts",
}

FLAGGED_IMPORTS = {
    "app.auth.dependencies",
    "app.auth.security",
}

# Escopo restrito: só sub-apps (apps/) para não gerar ruído no monolito existente.
# Quando Sprint F criar api-onboarding em apps/, esse sensor vai detectar imports diretos.
SCAN_DIRS = ["apps"]


def check(block: bool = False) -> int:
    repo_root = Path(__file__).resolve().parent.parent
    violations = []

    for scan_dir in SCAN_DIRS:
        target = repo_root / scan_dir
        if not target.exists():
            continue
        for py_file in target.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue
            rel = str(py_file.relative_to(repo_root))
            if any(rel.startswith(ex) for ex in EXEMPT_PATHS):
                continue
            try:
                source = py_file.read_text(encoding="utf-8")
                tree = ast.parse(source)
            except Exception:
                continue

            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and node.module:
                    module = node.module
                    if any(module.startswith(f) for f in FLAGGED_IMPORTS):
                        violations.append(
                            (rel, node.lineno, f"from {module} import ...")
                        )

    if violations:
        print(
            f"[AUTH-PROVIDER] {len(violations)} imports diretos de app.auth.* em sub-apps:"
        )
        for f, line, code in violations[:15]:
            print(f"  {f}:{line} -- {code}")
        print()
        print("CORRECAO: substituir por:")
        print(
            "  from app.shared.auth.auth_provider import get_auth_context_dependency, AuthContext"
        )
        mode = "BLOCKING" if block else "WARN-ONLY"
        print(f"Mode: {mode}")
        return 1 if block else 0

    print("[AUTH-PROVIDER] OK -- 0 imports diretos de app.auth.* em sub-apps")
    return 0


if __name__ == "__main__":
    sys.exit(check(block="--block" in sys.argv))
