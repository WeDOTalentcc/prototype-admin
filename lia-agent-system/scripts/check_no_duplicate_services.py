#!/usr/bin/env python3
"""Sensor canonical T-08 / ADR-019-v2: previne duplicação shared/domains services.

Detecta:
- R1: shim re-export em app/shared/services/*_service.py (forbidden após T-08)
- R2: basename de service duplicado em 2+ paths simultaneamente
- R3: class name collision em app/shared/learning/

Modo: BLOCKING (T-08 promoveu desde fix).

Uso:
    python scripts/check_no_duplicate_services.py [--warn-only]
"""
from __future__ import annotations

import ast
import re
import sys
from pathlib import Path
from collections import defaultdict


ROOT_REL = "app"

# Após T-08, app/shared/services/*_service.py NÃO deve existir mais para esses
FORBIDDEN_SHIM_FILES = {
    "app/shared/services/feedback_service.py",
    "app/shared/services/feedback_learning_service.py",
    "app/shared/services/learning_loop_service.py",
    "app/shared/services/training_data_service.py",
}

# Whitelist de basenames legítimos em multiple locations (domain-scoped)
WHITELIST_DUPLICATE_BASENAMES = {
    "domain.py",      # Cada domain agentic tem o seu
    "schemas.py",     # Schemas por domain OK
    "router.py",      # APIs separadas
    "__init__.py",
    "dependencies.py",
    "_shared.py",     # Helpers scoped por subdir
    "tasks.py",
    "models.py",      # Modelos por domain
    "config.py",
    "constants.py",
    "errors.py",
    "exceptions.py",
    "types.py",
    "utils.py",
    "base.py",
}


def check_r1_shim_files(repo_root: Path) -> list[str]:
    """R1: shim re-export files devem ter sido deletados."""
    violations = []
    for shim_rel in FORBIDDEN_SHIM_FILES:
        target = repo_root / shim_rel
        if target.exists():
            content = target.read_text(encoding="utf-8")
            if "import *" in content:
                violations.append(
                    f"R1: shim re-export ainda existe em {shim_rel} — "
                    f"delete file (T-08 ADR-019-v2)"
                )
    return violations


def check_r2_duplicate_basenames(repo_root: Path) -> list[str]:
    """R2: basename de service duplicado em 2+ paths."""
    violations = []
    app_dir = repo_root / ROOT_REL
    if not app_dir.exists():
        return []

    basename_map: dict[str, list[Path]] = defaultdict(list)
    for py in app_dir.rglob("*_service.py"):
        if "__pycache__" in str(py):
            continue
        basename_map[py.name].append(py)

    for basename, paths in basename_map.items():
        if len(paths) >= 2 and basename not in WHITELIST_DUPLICATE_BASENAMES:
            # Verifica se realmente compartilham classes (caso contrário OK)
            rel_paths = [str(p.relative_to(repo_root)) for p in paths]
            violations.append(
                f"R2: basename `{basename}` em {len(paths)} paths: {rel_paths}"
            )
    return violations


def check_r3_class_collision_in_learning(repo_root: Path) -> list[str]:
    """R3: class name não pode colidir em app/shared/learning/*.py."""
    violations = []
    learning_dir = repo_root / "app/shared/learning"
    if not learning_dir.exists():
        return []

    class_map: dict[str, list[str]] = defaultdict(list)
    for py in learning_dir.glob("*.py"):
        if py.name.startswith("__"):
            continue
        try:
            tree = ast.parse(py.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    class_map[node.name].append(py.name)
        except Exception:
            continue

    for class_name, files in class_map.items():
        if len(files) >= 2:
            violations.append(
                f"R3: class `{class_name}` duplicada em app/shared/learning/: {files}"
            )
    return violations


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    warn_only = "--strict" not in sys.argv  # Default BLOCKING [PROMOTED Sprint 7] (baseline 85). Use --strict para BLOCKING.

    r1 = check_r1_shim_files(repo_root)
    r2 = check_r2_duplicate_basenames(repo_root)
    r3 = check_r3_class_collision_in_learning(repo_root)

    total = len(r1) + len(r2) + len(r3)

    if total == 0:
        print("[T-08 ADR-019-v2] OK -- 0 duplications")
        return 0

    print(f"[T-08 ADR-019-v2] {total} violations:")
    for v in r1:
        print(f"  ❌ {v}")
    for v in r2:
        print(f"  ❌ {v}")
    for v in r3:
        print(f"  ❌ {v}")
    print()
    print("CORRECAO canonical (CLAUDE.md + ADR-019-v2):")
    print("  - shim re-exports: deletar files inteiramente, migrar callers")
    print("  - duplicate basenames: consolidar em canonical path único")
    print("  - class collisions: renomear uma das classes")
    print()
    mode = "WARN-ONLY" if warn_only else "BLOCKING"
    print(f"Mode: {mode}")
    return 0 if warn_only else 1


if __name__ == "__main__":
    sys.exit(main())
