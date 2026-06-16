#!/usr/bin/env python3
"""
Sensor: check_rails_owned_writes.py

Detects writes (update/delete) to Rails-owned tables (candidates, messages)
in LIA app code that are missing an ADR-001-EXEMPT marker on the preceding line.

Usage:
  python scripts/check_rails_owned_writes.py [--strict]

Flags:
  --strict  Exit with code 1 on violations (default: warn-only, exit 0)
"""
import ast
import sys
from pathlib import Path

RAILS_OWNED_MODELS = {"Candidate", "Message"}
EXEMPT_MARKER = "ADR-001-EXEMPT"


class RailsWriteChecker(ast.NodeVisitor):
    def __init__(self, source_lines: list[str]):
        self.source_lines = source_lines
        self.violations: list[tuple[int, str]] = []

    def visit_Call(self, node: ast.Call) -> None:
        func_name = None
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            func_name = node.func.attr

        if func_name in ("update", "delete") and node.args:
            first_arg = node.args[0]
            model_name = None
            if isinstance(first_arg, ast.Name):
                model_name = first_arg.id
            elif isinstance(first_arg, ast.Attribute):
                model_name = first_arg.attr

            if model_name in RAILS_OWNED_MODELS:
                if not self._has_exempt_marker(node.lineno):
                    self.violations.append(
                        (node.lineno, f"{func_name}({model_name})")
                    )

        self.generic_visit(node)

    def _has_exempt_marker(self, lineno: int) -> bool:
        for offset in range(1, min(6, lineno + 1)):
            line = self.source_lines[lineno - offset - 1] if lineno - offset - 1 >= 0 else ""
            if EXEMPT_MARKER in line:
                return True
        return False


def check_file(path: Path) -> list[tuple[str, int, str]]:
    try:
        source = path.read_text(encoding="utf-8")
    except Exception:
        return []
    source_lines = source.splitlines()
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []
    checker = RailsWriteChecker(source_lines)
    checker.visit(tree)
    return [(str(path), lineno, op) for lineno, op in checker.violations]


def main() -> int:
    strict = "--strict" in sys.argv
    app_root = Path(__file__).parent.parent / "app"

    all_violations: list[tuple[str, int, str]] = []
    for py_file in sorted(app_root.rglob("*.py")):
        if "test_" in py_file.name or py_file.name.startswith("test"):
            continue
        all_violations.extend(check_file(py_file))

    if not all_violations:
        print("OK check_rails_owned_writes: all Rails-boundary writes have ADR-001-EXEMPT markers")
        return 0

    print(f"WARN check_rails_owned_writes: {len(all_violations)} write(s) missing ADR-001-EXEMPT marker\n")
    for file_path, lineno, op in all_violations:
        print(f"  {file_path}:{lineno} -- {op}")
        print(f"    Add: # ADR-001-EXEMPT: Rails-owned <Table> -- <reason>")
        print()
    print("See docs/architecture/RAILS_BOUNDARY.md for the correct pattern.")

    return 1 if strict else 0


if __name__ == "__main__":
    sys.exit(main())
