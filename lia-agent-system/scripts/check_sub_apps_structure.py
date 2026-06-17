#!/usr/bin/env python3
"""
Sensor: check_sub_apps_structure.py
Garante que toda sub-app em apps/* tem a estrutura canônica de deployable independente.

Estrutura obrigatória:
  apps/<name>/
    main.py          — entry point FastAPI
    pyproject.toml   — deps declaradas com lia-* workspace refs
    Dockerfile       — imagem standalone
    __init__.py      — pacote Python
    tests/
      __init__.py
      test_smoke.py  — ao menos 1 smoke test

Uso: python3 scripts/check_sub_apps_structure.py [--blocking]
"""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
APPS_DIR = REPO_ROOT / "apps"

REQUIRED_FILES = [
    "main.py",
    "pyproject.toml",
    "Dockerfile",
    "__init__.py",
]

REQUIRED_DIRS = [
    "tests",
]

REQUIRED_IN_PYPROJECT = ["lia-models", "lia-config"]


def check_app(app_dir: Path) -> list[str]:
    violations = []
    name = app_dir.name

    for f in REQUIRED_FILES:
        if not (app_dir / f).exists():
            violations.append(f"[{name}] arquivo obrigatório ausente: {f}")

    for d in REQUIRED_DIRS:
        if not (app_dir / d).is_dir():
            violations.append(f"[{name}] diretório obrigatório ausente: {d}/")
        else:
            # Deve ter ao menos 1 test_*.py
            tests = list((app_dir / d).glob("test_*.py"))
            if not tests:
                violations.append(
                    f"[{name}] tests/ existe mas sem test_*.py — "
                    "adicionar smoke test canônico"
                )

    pyproject = app_dir / "pyproject.toml"
    if pyproject.exists():
        content = pyproject.read_text()
        for dep in REQUIRED_IN_PYPROJECT:
            if dep not in content:
                violations.append(
                    f"[{name}] pyproject.toml não declara {dep} — "
                    "sub-app precisa de dep explícita"
                )
    return violations


def main():
    blocking = "--blocking" in sys.argv
    apps = [d for d in APPS_DIR.iterdir() if d.is_dir() and not d.name.startswith(".")]

    if not apps:
        print(f"[sub-apps sensor] Nenhuma sub-app encontrada em {APPS_DIR}")
        sys.exit(0)

    all_violations = []
    for app_dir in sorted(apps):
        all_violations.extend(check_app(app_dir))

    if all_violations:
        print(f"[sub-apps sensor] {len(all_violations)} violation(s) detectadas:")
        for v in all_violations:
            print(f"  {v}")
        print("\nFix: garantir estrutura canônica em apps/<name>/")
        if blocking:
            sys.exit(1)
    else:
        print(f"[sub-apps sensor] OK — {len(apps)} sub-app(s) com estrutura canônica ✅")


if __name__ == "__main__":
    main()
