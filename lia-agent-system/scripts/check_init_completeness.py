#!/usr/bin/env python3
"""
Lint check: ensure every model file in lia_models/ is imported in __init__.py.

Prevents drift where new model files are added but forgotten in the package
re-export, breaking `from lia_models import SomeModel` usage.

See ADR-002 in ARCHITECTURE.md for rationale.

Run:  python scripts/check_init_completeness.py
Exit: 0 = clean, 1 = missing imports found
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
LIA_MODELS_DIR = ROOT / "libs" / "models" / "lia_models"
INIT_FILE = LIA_MODELS_DIR / "__init__.py"

EXCLUDED_FILES = {"__init__", "conftest"}
EXCLUDED_PREFIXES = ("test_",)

IMPORT_PATTERN = re.compile(r"^from\s+lia_models\.(\w+)\s+import\b")


def get_model_modules() -> set[str]:
    modules = set()
    for py_file in LIA_MODELS_DIR.glob("*.py"):
        name = py_file.stem
        if name in EXCLUDED_FILES:
            continue
        if any(name.startswith(p) for p in EXCLUDED_PREFIXES):
            continue
        modules.add(name)
    return modules


def get_imported_modules() -> set[str]:
    imported = set()
    source = INIT_FILE.read_text(encoding="utf-8")
    for line in source.splitlines():
        m = IMPORT_PATTERN.match(line.strip())
        if m:
            imported.add(m.group(1))
    return imported


def main() -> int:
    model_modules = get_model_modules()
    imported_modules = get_imported_modules()

    missing = sorted(model_modules - imported_modules)

    if missing:
        print(
            "FAIL — model files not imported in lia_models/__init__.py (ADR-002):\n"
            + "\n".join(f"  libs/models/lia_models/{m}.py" for m in missing)
            + "\n\n"
            "Every model file must be imported in __init__.py so that\n"
            "`from lia_models import X` works and proxy shims in app/models/\n"
            "resolve correctly.\n"
            "\n"
            "Fix: add `from lia_models.{module} import ...` to __init__.py."
        )
        return 1

    extra = sorted(imported_modules - model_modules)
    if extra:
        print(
            "WARN — __init__.py imports modules that don't exist as files:\n"
            + "\n".join(f"  lia_models.{m}" for m in extra)
            + "\n\n"
            "These imports may cause ImportError at startup. Check if the\n"
            "files were renamed or deleted."
        )
        return 1

    print(f"OK — all {len(model_modules)} model files imported in __init__.py (ADR-002).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
