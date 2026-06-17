#!/usr/bin/env python3
"""
G8 canonical sensor — flag new callers of the deprecated hardcoded
capability list (WHAT_I_CAN_DO / get_out_of_scope_response).

These constructs contradict lia_persona.yaml Anti-pattern #1 ("Resposta-
lista-de-capabilities" is forbidden). The canonical sources for capability
surfacing are now:
  - lia_persona.yaml (persona behavior + improvisation rules)
  - system_prompt_builder.py G3 Navegação section
  - system_prompt_builder.py G6 Ações section

Baseline as of 2026-05-24: 2 expected hits (the defensive_prompts.py
self-reference + the __init__.py re-export). New callers fail the sensor.

Usage:
    python scripts/check_no_hardcoded_capability_list.py
    python scripts/check_no_hardcoded_capability_list.py --blocking
"""
from __future__ import annotations

import argparse
import ast
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable


REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PATHS = ["app"]

FLAGGED_NAMES = {"WHAT_I_CAN_DO", "get_out_of_scope_response"}

# Files where references are expected and pre-approved (the canonical
# definition + the re-export module). New entries here must be reviewed.
ALLOWED_FILES = {
    "app/shared/robustness/defensive_prompts.py",
    "app/shared/robustness/__init__.py",
}


@dataclass
class Violation:
    file: str
    line: int
    name: str

    def as_dict(self) -> dict:
        return asdict(self)


def scan(path: Path) -> list[Violation]:
    rel = str(path.relative_to(REPO_ROOT))
    if rel in ALLOWED_FILES:
        return []
    try:
        src = path.read_text()
    except (OSError, UnicodeDecodeError):
        return []
    try:
        tree = ast.parse(src, filename=str(path))
    except SyntaxError:
        return []
    found: list[Violation] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and node.id in FLAGGED_NAMES:
            found.append(Violation(file=rel, line=node.lineno, name=node.id))
        if isinstance(node, ast.Attribute) and node.attr in FLAGGED_NAMES:
            found.append(Violation(file=rel, line=node.lineno, name=node.attr))
        if isinstance(node, ast.ImportFrom):
            for alias in node.names:
                if alias.name in FLAGGED_NAMES:
                    found.append(Violation(file=rel, line=node.lineno, name=alias.name))
    return found


def iter_py_files(roots: Iterable[Path]) -> Iterable[Path]:
    for root in roots:
        if root.is_file() and root.suffix == ".py":
            yield root
            continue
        if not root.is_dir():
            continue
        for p in root.rglob("*.py"):
            parts = set(p.parts)
            if "__pycache__" in parts or "tests" in parts or "test" in parts:
                continue
            yield p


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--paths", nargs="*", default=DEFAULT_PATHS)
    parser.add_argument("--blocking", action="store_true",
                        help="exit 1 on any violation (default 0)")
    args = parser.parse_args()

    roots = [REPO_ROOT / p for p in args.paths]
    all_v: list[Violation] = []
    for f in iter_py_files(roots):
        all_v.extend(scan(f))

    if not all_v:
        print("OK no_hardcoded_capability_list sensor clean.")
    else:
        print(f"FAIL {len(all_v)} reference(s) to deprecated capability list:")
        for v in all_v:
            print(f"  {v.file}:{v.line}  {v.name}")
        print()
        print("These constructs contradict lia_persona.yaml Anti-pattern #1.")
        print("Use the canonical sources instead:")
        print("  - lia_persona.yaml (improvisation rules)")
        print("  - system_prompt_builder.py Capabilities — Navegação (G3)")
        print("  - system_prompt_builder.py Capabilities — Ações (G6)")

    if args.blocking and all_v:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
