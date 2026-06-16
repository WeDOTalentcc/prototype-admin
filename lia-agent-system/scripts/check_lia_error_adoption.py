#!/usr/bin/env python3
"""
Sensor: LIAError adoption — measures how many endpoints still use
bare HTTPException(500) instead of letting exceptions propagate to
the unified LIAError handlers in main.py.

Usage:
    python scripts/check_lia_error_adoption.py          # warn-only (exit 0)
    python scripts/check_lia_error_adoption.py --json    # JSON output for CI

Goal: drive this count to 0 over time (ratchet).
"""
import ast
import os
import sys
import json


class HTTPException500Finder(ast.NodeVisitor):
    """Find `raise HTTPException(status_code=500, ...)` in Python files."""

    def __init__(self, filepath: str):
        self.filepath = filepath
        self.violations: list[dict] = []

    def visit_Raise(self, node: ast.Raise):
        if node.exc is None:
            return
        call = node.exc
        if not isinstance(call, ast.Call):
            return
        # Match HTTPException(status_code=500, ...)
        func = call.func
        func_name = None
        if isinstance(func, ast.Name):
            func_name = func.id
        elif isinstance(func, ast.Attribute):
            func_name = func.attr

        if func_name != "HTTPException":
            return

        for kw in call.keywords:
            if kw.arg == "status_code" and isinstance(kw.value, ast.Constant):
                if kw.value.value == 500:
                    self.violations.append({
                        "file": self.filepath,
                        "line": node.lineno,
                        "col": node.col_offset,
                    })
                    break
        # Also match positional: HTTPException(500, ...)
        if call.args and isinstance(call.args[0], ast.Constant) and call.args[0].value == 500:
            self.violations.append({
                "file": self.filepath,
                "line": node.lineno,
                "col": node.col_offset,
            })

        self.generic_visit(node)


def scan_directory(base: str) -> list[dict]:
    violations = []
    for root, _, files in os.walk(base):
        if "__pycache__" in root or "test" in os.path.basename(root):
            continue
        for fname in files:
            if not fname.endswith(".py") or fname.startswith("test_"):
                continue
            filepath = os.path.join(root, fname)
            try:
                with open(filepath, encoding="utf-8", errors="replace") as f:
                    tree = ast.parse(f.read(), filename=filepath)
                finder = HTTPException500Finder(filepath)
                finder.visit(tree)
                violations.extend(finder.violations)
            except SyntaxError:
                pass
    return violations


def main():
    api_dir = "app/api/v1"
    if not os.path.isdir(api_dir):
        print(f"Directory {api_dir} not found. Run from lia-agent-system root.")
        sys.exit(1)

    violations = scan_directory(api_dir)

    if "--json" in sys.argv:
        print(json.dumps({
            "total_violations": len(violations),
            "violations": violations,
        }, indent=2))
    else:
        if violations:
            print(f"⚠️  LIAError adoption: {len(violations)} endpoints still use HTTPException(500)")
            print()
            by_file: dict[str, list] = {}
            for v in violations:
                by_file.setdefault(v["file"], []).append(v)
            for f, vs in sorted(by_file.items(), key=lambda x: -len(x[1])):
                print(f"  {f}: {len(vs)} violation(s)")
                for v in vs[:3]:
                    print(f"    line {v['line']}")
                if len(vs) > 3:
                    print(f"    ... and {len(vs) - 3} more")
        else:
            print("✅ LIAError adoption: 0 HTTPException(500) remaining in API layer")

    sys.exit(0)  # always warn-only for now


if __name__ == "__main__":
    main()
