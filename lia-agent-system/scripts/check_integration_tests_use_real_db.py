#!/usr/bin/env python3
"""
Harness canonical — `@pytest.mark.integration` must NOT use Mock/MagicMock.

Origin: the chat RLS saga (commits 0a58a5bf..e33d6aee) found that the
46 legacy `conversation_*` tests passed even though the chat write path
was broken under RLS strict policy. Reason: every test used MagicMock /
AsyncMock — they exercised SQLAlchemy logic but never touched Postgres,
so the RLS policy machinery was never invoked.

Pattern already documented in CLAUDE.md (i18n section):
  "fixture local em teste NUNCA substitui validação contra messages file
   canonical"
— now applies to DB write paths under RLS.

This sensor flags any test function decorated `@pytest.mark.integration`
whose body references MagicMock, AsyncMock, Mock, or mock.patch. An
integration test by definition exercises the real I/O surface; a mocked
"integration test" is a lie that gives false confidence.

Allowed:
  - Tests NOT marked integration (unit/contract/etc. — mocks are fine).
  - Integration tests using pytest fixtures like pg_session, real_engine,
    or any factory that creates a real AsyncSession.
  - Helper/utility mocks for things unrelated to the system under test
    (rare — annotate with `# RLS-OK: mock unrelated to DB I/O`).

Usage:
    python scripts/check_integration_tests_use_real_db.py
    python scripts/check_integration_tests_use_real_db.py --json
    python scripts/check_integration_tests_use_real_db.py --blocking
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
DEFAULT_PATHS = ["tests"]
EXEMPT_MARKER = "RLS-OK:"

MOCK_NAMES = {"MagicMock", "AsyncMock", "Mock", "NonCallableMock"}
MOCK_ATTRS = {"patch", "patch.object", "patch.dict"}


@dataclass
class Violation:
    file: str
    test_func: str
    mock_kind: str  # which mock construct was found
    mock_line: int

    def as_dict(self) -> dict:
        return asdict(self)


def _has_integration_marker(fn: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    for dec in fn.decorator_list:
        # @pytest.mark.integration
        if isinstance(dec, ast.Attribute) and dec.attr == "integration":
            inner = dec.value
            if isinstance(inner, ast.Attribute) and inner.attr == "mark":
                return True
        # bare @integration (less common but possible)
        if isinstance(dec, ast.Name) and dec.id == "integration":
            return True
    return False


def _find_mocks_in_body(fn: ast.AST) -> list[tuple[str, int]]:
    """Return [(mock_kind, lineno)] of mock usages inside this function."""
    found: list[tuple[str, int]] = []
    for node in ast.walk(fn):
        if isinstance(node, ast.Call):
            # Direct: MagicMock(...), AsyncMock(...)
            func = node.func
            if isinstance(func, ast.Name) and func.id in MOCK_NAMES:
                found.append((func.id, node.lineno))
                continue
            # Attribute: mock.patch(), unittest.mock.patch(...)
            if isinstance(func, ast.Attribute):
                attr_path = _attr_chain(func)
                if any(attr_path.endswith(suffix)
                       for suffix in ["mock.patch", ".patch", "mock.MagicMock",
                                      "mock.AsyncMock", ".MagicMock",
                                      ".AsyncMock"]):
                    found.append((attr_path.split(".")[-1], node.lineno))
    return found


def _attr_chain(attr: ast.Attribute) -> str:
    parts: list[str] = []
    cur: ast.AST = attr
    while isinstance(cur, ast.Attribute):
        parts.append(cur.attr)
        cur = cur.value
    if isinstance(cur, ast.Name):
        parts.append(cur.id)
    return ".".join(reversed(parts))


def _line_has_exempt(src_lines: list[str], lineno: int) -> bool:
    candidates = []
    if 1 <= lineno <= len(src_lines):
        candidates.append(src_lines[lineno - 1])
    if 2 <= lineno <= len(src_lines):
        candidates.append(src_lines[lineno - 2])
    return any(EXEMPT_MARKER in c for c in candidates)


class Walker(ast.NodeVisitor):
    def __init__(self, src_lines: list[str], path: Path):
        self.src_lines = src_lines
        self.path = path
        self.violations: list[Violation] = []

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._inspect(node)
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._inspect(node)
        self.generic_visit(node)

    def _inspect(self, fn: ast.AST) -> None:
        if not _has_integration_marker(fn):
            return
        for kind, ln in _find_mocks_in_body(fn):
            if _line_has_exempt(self.src_lines, ln):
                continue
            self.violations.append(
                Violation(
                    file=str(self.path.relative_to(REPO_ROOT)),
                    test_func=getattr(fn, "name", ""),
                    mock_kind=kind,
                    mock_line=ln,
                )
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
    walker = Walker(src.splitlines(), path)
    walker.visit(tree)
    return walker.violations


def iter_py_files(roots: Iterable[Path]) -> Iterable[Path]:
    for root in roots:
        if root.is_file() and root.suffix == ".py":
            yield root
            continue
        if not root.is_dir():
            continue
        for p in root.rglob("*.py"):
            if "__pycache__" in p.parts:
                continue
            yield p


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--paths", nargs="*", default=DEFAULT_PATHS)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--max-violations", type=int, default=0,
                        help="exit 1 if > N (default 0, blocking since baseline is 0)")
    parser.add_argument("--warn-only", action="store_true",
                        help="never exit non-zero (opt-out)")
    args = parser.parse_args()

    roots = [REPO_ROOT / p for p in args.paths]
    all_v: list[Violation] = []
    for f in iter_py_files(roots):
        all_v.extend(scan_file(f))

    if args.json:
        print(json.dumps({"violations": [v.as_dict() for v in all_v],
                          "total": len(all_v)}, indent=2))
    else:
        if not all_v:
            print("OK integration-real-db sensor clean: every "
                  "@pytest.mark.integration test exercises real I/O.")
        else:
            print(f"FAIL {len(all_v)} integration test(s) using Mock/MagicMock:\n")
            by_file: dict[str, list[Violation]] = {}
            for v in all_v:
                by_file.setdefault(v.file, []).append(v)
            for file, vs in sorted(by_file.items()):
                print(f"  {file}")
                for v in vs:
                    print(f"    L{v.mock_line:>4}  {v.test_func}() uses "
                          f"{v.mock_kind}")
                print()
            print("An @pytest.mark.integration test MUST exercise the real")
            print("I/O surface (Postgres, Redis, external API) — otherwise")
            print("it is a unit test lying about its scope, and bugs in the")
            print("real surface (like RLS policy enforcement) ship.")
            print()
            print("Canonical fix:")
            print("  - Use the pg_session fixture (or equivalent real-DB")
            print("    fixture). See tests/integration/")
            print("    test_rls_tenant_context_lifecycle.py for the pattern.")
            print("  - Remove @pytest.mark.integration if the test is")
            print("    genuinely a unit test.")
            print()
            print("Escape hatch (rare):")
            print("  # RLS-OK: mock unrelated to DB I/O (specify why)")

    if args.warn_only:
        return 0
    if len(all_v) > args.max_violations:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
