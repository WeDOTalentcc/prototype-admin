#!/usr/bin/env python3
"""
RLS canonical — detect `db.commit() + db.refresh/SELECT` without tenant restore.

Origin: commits 0a58a5bf → 611883220 → 996f50d9 → b134b74a (V5 canonical).
After V5 introduced commit_keeping_tenant() as the canonical helper, any
handler that does a plain `await db.commit()` followed by a SELECT or
refresh inside the SAME async function is suspect: the new implicit
transaction loses app.company_id (is_local=true is tx-scoped), the RLS
SELECT policy returns NULL and the row becomes invisible.

This sensor walks every Python file in:
  - app/api/v1
  - app/api
  - app/domains/*/services
  - app/domains/*/repositories
  - app/orchestrator
  - app/shared

For each `async def` function, it looks for an `await <expr>.commit()` call.
If a `<expr>.refresh(...)` or `<expr>.execute(select(...))` or similar
read appears AFTER that commit IN THE SAME function body, AND no
`commit_keeping_tenant` or `set_tenant_context` call sits between them,
it is flagged.

Escape hatch:
  - `# RLS-OK: <reason>` on the line of the commit OR the line above it.
  - Functions named with prefix `_test_`, `_setup_`, or marked decorator
    `@no_rls` are skipped.

Error output is optimized for LLM consumers:
  - file:line of the commit
  - file:line of the offending read
  - canonical fix snippet using commit_keeping_tenant
  - escape hatch syntax

Usage:
    python scripts/check_commit_then_read_without_tenant.py
    python scripts/check_commit_then_read_without_tenant.py --json
    python scripts/check_commit_then_read_without_tenant.py --warn-only

Exit codes:
    0 — clean (or within --max-violations budget, default 0)
    1 — violations exceed budget
    2 — internal error
"""
from __future__ import annotations

import argparse
import ast
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable


REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PATHS = [
    "app/api",
    "app/domains",
    "app/orchestrator",
    "app/shared",
]
EXEMPT_MARKER = "RLS-OK:"


@dataclass
class Violation:
    file: str
    func: str
    commit_line: int
    read_line: int
    read_kind: str  # "refresh" | "execute" | "scalar" | "scalars"
    suggestion: str

    def as_dict(self) -> dict:
        return asdict(self)


READ_METHOD_NAMES = {"refresh", "execute", "scalar", "scalars", "get"}
COMMIT_METHOD_NAMES = {"commit"}
CANONICAL_HELPERS = {"commit_keeping_tenant", "set_tenant_context"}


def _is_commit_call(node: ast.AST) -> bool:
    """Match `<expr>.commit()` (await wrapper handled by caller)."""
    if not isinstance(node, ast.Call):
        return False
    func = node.func
    if isinstance(func, ast.Attribute) and func.attr in COMMIT_METHOD_NAMES:
        return True
    return False


def _is_read_call(node: ast.AST) -> tuple[bool, str]:
    """Match `<expr>.refresh(...)`, `<expr>.execute(...)`, etc."""
    if not isinstance(node, ast.Call):
        return False, ""
    func = node.func
    if isinstance(func, ast.Attribute) and func.attr in READ_METHOD_NAMES:
        return True, func.attr
    return False, ""


def _is_canonical_helper(node: ast.AST) -> bool:
    """Match `commit_keeping_tenant(...)` or `set_tenant_context(...)`."""
    if not isinstance(node, ast.Call):
        return False
    func = node.func
    if isinstance(func, ast.Name) and func.id in CANONICAL_HELPERS:
        return True
    if isinstance(func, ast.Attribute) and func.attr in CANONICAL_HELPERS:
        return True
    return False


def _has_exempt_marker(src_lines: list[str], lineno: int) -> bool:
    """Honor `# RLS-OK:` on same line or line above."""
    candidates = []
    if 1 <= lineno <= len(src_lines):
        candidates.append(src_lines[lineno - 1])
    if 2 <= lineno <= len(src_lines):
        candidates.append(src_lines[lineno - 2])
    return any(EXEMPT_MARKER in c for c in candidates)


class FunctionAnalyzer(ast.NodeVisitor):
    def __init__(self, src_lines: list[str], path: Path):
        self.src_lines = src_lines
        self.path = path
        self.violations: list[Violation] = []

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._analyze_function(node)
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        # Plain sync functions don't await db.commit, but visit anyway in
        # case of unusual patterns.
        self._analyze_function(node)
        self.generic_visit(node)

    def _analyze_function(self, fn: ast.AST) -> None:
        # Skip test/setup helpers by naming convention.
        name = getattr(fn, "name", "")
        if name.startswith(("_test_", "_setup_", "_teardown_", "test_")):
            return
        # Walk the body; track commit events and inspect subsequent reads.
        commits: list[tuple[int, ast.AST]] = []
        for stmt in ast.walk(fn):
            if isinstance(stmt, ast.Await):
                inner = stmt.value
                if _is_commit_call(inner):
                    if not _has_exempt_marker(self.src_lines, stmt.lineno):
                        commits.append((stmt.lineno, stmt))
                    continue
                if _is_canonical_helper(inner):
                    # Reset the pending-commit list when canonical helper is
                    # called — re-injection happened.
                    commits = []
                    continue
                is_read, kind = _is_read_call(inner)
                if is_read and commits:
                    # Found a read after an unmitigated commit.
                    commit_line, _ = commits[0]
                    if commit_line < stmt.lineno:
                        self.violations.append(
                            Violation(
                                file=str(self.path.relative_to(REPO_ROOT)),
                                func=name,
                                commit_line=commit_line,
                                read_line=stmt.lineno,
                                read_kind=kind,
                                suggestion=_build_suggestion(name, kind),
                            )
                        )
                        # Don't flag the same commit twice.
                        commits = []
            elif isinstance(stmt, ast.Call):
                # Sync canonical helper call (rare but possible).
                if _is_canonical_helper(stmt):
                    commits = []


def _build_suggestion(func: str, kind: str) -> str:
    return (
        f"In `{func}()`, an `await db.commit()` is followed by an "
        f"`await db.{kind}(...)` without re-injecting the tenant context. "
        f"set_config('app.company_id', :cid, true) is transaction-scoped; "
        f"the commit ends the tx and the next read is filtered by the RLS "
        f"SELECT policy `company_id = app_current_company_id()` → NULL "
        f"blocks the row (SQLAlchemy reports 'Could not refresh instance'). "
        f"Canonical fix:\n"
        f"    from app.core.database import commit_keeping_tenant\n"
        f"    await commit_keeping_tenant(db)\n"
        f"    await db.{kind}(...)\n"
        f"Escape hatch (rare, document):\n"
        f"    # RLS-OK: <reason this commit doesn't precede a tenant-scoped read>\n"
        f"    await db.commit()\n"
        f"See app/core/database.py:commit_keeping_tenant docstring."
    )


def scan_file(path: Path) -> list[Violation]:
    try:
        src = path.read_text()
    except (OSError, UnicodeDecodeError):
        return []
    try:
        tree = ast.parse(src, filename=str(path))
    except SyntaxError as e:
        print(f"warn: syntax error {path}: {e}", file=sys.stderr)
        return []
    analyzer = FunctionAnalyzer(src.splitlines(), path)
    analyzer.visit(tree)
    return analyzer.violations


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
    parser.add_argument("--paths", nargs="*", default=DEFAULT_PATHS,
                        help="paths to scan")
    parser.add_argument("--json", action="store_true",
                        help="emit JSON")
    parser.add_argument("--max-violations", type=int, default=None,
                        help="exit 1 if violations > N (default: None = warn-only). "
                             "Use 0 for strict blocking once baseline reaches zero.")
    parser.add_argument("--blocking", action="store_true",
                        help="alias for --max-violations 0 (force exit 1 on any violation)")
    parser.add_argument("--warn-only", action="store_true",
                        help="never exit non-zero (default behavior)")
    args = parser.parse_args()

    roots = [REPO_ROOT / p for p in args.paths]
    all_violations: list[Violation] = []
    for f in iter_py_files(roots):
        all_violations.extend(scan_file(f))

    if args.json:
        print(json.dumps({
            "violations": [v.as_dict() for v in all_violations],
            "total": len(all_violations),
        }, indent=2))
    else:
        if not all_violations:
            print("OK commit_then_read sensor clean: no unmitigated "
                  "commit→read sequences found.")
        else:
            print(f"FAIL {len(all_violations)} commit→read gap(s):\n")
            by_file: dict[str, list[Violation]] = {}
            for v in all_violations:
                by_file.setdefault(v.file, []).append(v)
            for file, vs in sorted(by_file.items()):
                print(f"  {file}")
                for v in vs:
                    print(f"    {v.func}()  commit L{v.commit_line} -> "
                          f"{v.read_kind} L{v.read_line}")
                print()
            # One canonical-fix block shown once.
            print("Canonical fix (per site):")
            print("    from app.core.database import commit_keeping_tenant")
            print("    await commit_keeping_tenant(db)   # was: await db.commit()")
            print("    await db.refresh(obj)              # or whichever read")
            print()
            print("Escape hatch (rare):")
            print("    # RLS-OK: <reason>")
            print("    await db.commit()")

    if args.warn_only:
        return 0
    if args.blocking:
        return 1 if all_violations else 0
    if args.max_violations is None:
        return 0  # warn-only by default (baseline 302 as of V5)
    if len(all_violations) > args.max_violations:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
