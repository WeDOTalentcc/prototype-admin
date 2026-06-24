#!/usr/bin/env python3
"""
Sensor: detect FairnessGuard exception swallowing in sourcing domain.

Finds: except blocks near FairnessGuard calls that only call logger.debug (not .error)
       without using run_sourcing_fairness_check canonical wrapper.

Exit 0: clean. Exit 1: violations (unless --warn-only).

Usage:
  python3 scripts/check_sourcing_fairness_swallow.py
  python3 scripts/check_sourcing_fairness_swallow.py --warn-only
"""
from __future__ import annotations
import ast
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
SOURCING_DIR = REPO_ROOT / "app" / "domains" / "sourcing"
warn_only = "--warn-only" in sys.argv


class FairnessSwallowVisitor(ast.NodeVisitor):
    def __init__(self, filename: str):
        self.filename = filename
        self.violations: list[tuple[int, str]] = []

    def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:
        body_nodes = list(ast.walk(node))
        calls = [n for n in body_nodes if isinstance(n, ast.Call)]
        call_attrs = [
            c.func.attr for c in calls
            if isinstance(c.func, ast.Attribute) and hasattr(c.func, 'attr')
        ]
        has_debug_only = 'debug' in call_attrs and 'error' not in call_attrs
        has_pass = any(isinstance(s, ast.Pass) for s in node.body)

        # Check if there's a fairness-related string in the except body
        strings = [
            n.value for n in ast.walk(node)
            if isinstance(n, ast.Constant) and isinstance(n.value, str)
        ]
        fairness_mention = any(
            'fairness' in s.lower() or 'FairnessGuard' in s
            for s in strings
        )

        if (has_debug_only or has_pass) and fairness_mention:
            self.violations.append((
                node.lineno,
                f"except at line {node.lineno} swallows FairnessGuard with only "
                f"{'logger.debug' if has_debug_only else 'pass'} -- "
                "use run_sourcing_fairness_check() from fairness_guard_wrapper.py "
                "or upgrade to logger.error(exc_info=True)"
            ))
        self.generic_visit(node)


def check_file(fpath: Path) -> list[tuple[int, str]]:
    try:
        tree = ast.parse(fpath.read_text(encoding="utf-8"))
    except SyntaxError:
        return []
    visitor = FairnessSwallowVisitor(str(fpath))
    visitor.visit(tree)
    return visitor.violations


def main() -> int:
    total = 0
    for fpath in sorted(SOURCING_DIR.rglob("*.py")):
        violations = check_file(fpath)
        for lineno, msg in violations:
            rel = fpath.relative_to(REPO_ROOT)
            print(f"[{rel}:{lineno}] {msg}")
            total += 1

    if total == 0:
        print(f"check_sourcing_fairness_swallow: 0 violations in {SOURCING_DIR.relative_to(REPO_ROOT)}")
        return 0
    else:
        print(f"\n-> {total} violation(s). Fix: use run_sourcing_fairness_check() from "
              "app/domains/sourcing/fairness/fairness_guard_wrapper.py")
        return 0 if warn_only else 1


if __name__ == "__main__":
    sys.exit(main())
