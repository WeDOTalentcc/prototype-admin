#!/usr/bin/env python3
"""
Lint check: block forbidden import paths that cause duplicate SQLAlchemy
class registrations.

Forbidden paths:
  - from libs.models.lia_models.*
  - from libs.messaging.lia_messaging.*
  - import libs.models.lia_models.*
  - import libs.messaging.lia_messaging.*
  - from app.models(.*)? / import app.models(.*)?  (removed shim layer — task #242)

Correct alternatives:
  - from lia_models.* …
  - from lia_messaging.* …

See ADR-012 in ARCHITECTURE.md for rationale.

Run:  python scripts/check_forbidden_imports.py
Exit: 0 = clean, 1 = violations found
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
WORKSPACE_ROOT = ROOT.parent

FORBIDDEN_PATTERNS = [
    re.compile(r"\bfrom\s+libs\.models\.lia_models\b"),
    re.compile(r"\bimport\s+libs\.models\.lia_models\b"),
    re.compile(r"\bfrom\s+libs\.messaging\.lia_messaging\b"),
    re.compile(r"\bimport\s+libs\.messaging\.lia_messaging\b"),
    # task #242: app/models/ shim layer was deleted. The canonical path is
    # `lia_models.*`. A second import path created duplicate SQLAlchemy class
    # registrations (e.g. SourcingAgentSignal) and 500s.
    re.compile(r"\bfrom\s+app\.models\b"),
    re.compile(r"\bimport\s+app\.models\b"),
]

SCAN_DIRS = ["app", "scripts", "tests"]

SELF = Path(__file__).resolve()


def _check_file(py_file: Path, base: Path, violations: list[str]) -> None:
    if py_file.resolve() == SELF:
        return
    try:
        source = py_file.read_text(encoding="utf-8")
    except Exception:
        return
    for lineno, line in enumerate(source.splitlines(), 1):
        stripped = line.lstrip()
        if stripped.startswith("#"):
            continue
        for pattern in FORBIDDEN_PATTERNS:
            if pattern.search(line):
                rel = py_file.relative_to(base)
                violations.append(f"  {rel}:{lineno}: {line.rstrip()}")
                break


def main() -> int:
    violations: list[str] = []

    for scan_dir in SCAN_DIRS:
        target = ROOT / scan_dir
        if not target.exists():
            continue
        for py_file in target.rglob("*.py"):
            _check_file(py_file, ROOT, violations)

    for py_file in ROOT.glob("*.py"):
        _check_file(py_file, ROOT, violations)

    for py_file in WORKSPACE_ROOT.glob("*.py"):
        _check_file(py_file, WORKSPACE_ROOT, violations)

    if violations:
        print(
            "FAIL — forbidden import paths found (ADR-012):\n"
            + "\n".join(violations)
            + "\n\n"
            "These paths cause duplicate SQLAlchemy class registrations.\n"
            "Use the short-form imports instead:\n"
            "  from libs.models.lia_models.X  →  from lia_models.X\n"
            "  from libs.messaging.lia_messaging.X  →  from lia_messaging.X\n"
            "\n"
            "See ADR-012 in ARCHITECTURE.md for details."
        )
        return 1

    print("OK — no forbidden import paths (ADR-012).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
