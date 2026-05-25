#!/usr/bin/env python3
"""
RLS-bearing tables — INSERT canonical contract sensor.

Audit 2026-05-23: chat_repository.create_conversation built a
Conversation(user_id=..., ...) WITHOUT company_id. The conversations
table has an RLS policy that rejects NULL company_id, so every new
chat session failed with asyncpg.InsufficientPrivilegeError. The
frontend hung on "Pensando..." indefinitely.

Pattern: any ORM model constructor that includes user_id= but NOT
company_id= inside repository / API code is a strong signal of a
multi-tenancy gap. user_id is tenant-scoped (a user belongs to a
company), so the row will fail RLS the moment a company_id-scoped
policy is enforced.

This sensor uses AST to walk every Python file in:
  - app/domains/*/repositories/*.py
  - app/api/v1/*.py
  - app/orchestrator
  - app/shared
and flags every `<Capitalized>(... user_id=..., ...)` call where the
kwargs do NOT include company_id.

Escape hatch: comment `# RLS-EXEMPT: <reason>` on the same line OR
the line immediately above the constructor call. Legacy markers
`# TENANT-EXEMPT:` and `# ADR-001-EXEMPT` are also honored.

Error message is optimized for LLM consumers: includes file:line,
exact constructor name, the missing kwarg, and the canonical fix.

Usage:
    python scripts/check_rls_table_inserts_have_company_id.py
    python scripts/check_rls_table_inserts_have_company_id.py --paths app/domains/chat
    python scripts/check_rls_table_inserts_have_company_id.py --json   # CI output
    python scripts/check_rls_table_inserts_have_company_id.py --max-violations 0  # blocking

Exit codes:
    0 — clean (no violations OR within --max-violations budget)
    1 — violations exceed budget (blocking mode)
    2 — internal error
"""
from __future__ import annotations

import argparse
import ast
import json
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
import re
from typing import Iterable


REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PATHS = [
    "app/domains",
    "app/api/v1",
    "app/orchestrator",
    "app/shared",
]
EXEMPT_MARKER = "RLS-EXEMPT:"
LEGACY_EXEMPT_MARKERS = ("TENANT-EXEMPT:", "ADR-001-EXEMPT")

# Models that ALWAYS require company_id= regardless of other kwargs.
# Extend this list when a new table gains RLS. Covers models whose
# tenant-signal kwarg differs from the canonical "user_id=" pattern
# (e.g. Task uses assigned_to_user_id, not user_id).
REQUIRED_COMPANY_ID_MODELS: frozenset[str] = frozenset({
    "Task",  # tasks table — RLS added migration 196 (2026-05-25)
})


@dataclass
class Violation:
    file: str
    line: int
    col: int
    model: str
    has_user_id: bool
    has_company_id: bool
    suggestion: str

    def as_dict(self) -> dict:
        return asdict(self)


def _line_has_exempt(src_lines: list[str], lineno: int) -> bool:
    candidates = []
    if 1 <= lineno <= len(src_lines):
        candidates.append(src_lines[lineno - 1])
    if 2 <= lineno <= len(src_lines):
        candidates.append(src_lines[lineno - 2])
    for line in candidates:
        if EXEMPT_MARKER in line:
            return True
        for legacy in LEGACY_EXEMPT_MARKERS:
            if legacy in line:
                return True
    return False


def _extract_call_kwargs(node: ast.Call) -> set[str]:
    return {kw.arg for kw in node.keywords if kw.arg is not None}


BAD_SUFFIXES = (
    "Error", "Exception", "Response", "Request", "Schema", "Config",
    "Settings", "Result", "Event", "Mode", "Type", "Enum", "Filter",
    "Builder", "Factory", "Adapter", "Helper", "Manager", "Service",
    "Repository", "Handler", "Middleware", "Provider", "Strategy",
    "Validator", "Guard", "Processor", "Hook", "Mixin", "Base",
    "Client", "Session", "Engine", "Logger", "Tracker", "Reporter",
    "Context", "State", "Info", "Data", "Payload", "Input", "Output",
)


def _model_name_of(node: ast.Call) -> str | None:
    func = node.func
    name: str | None = None
    if isinstance(func, ast.Name):
        name = func.id
    elif isinstance(func, ast.Attribute):
        name = func.attr
    if not name:
        return None
    if not name[0].isupper():
        return None
    if any(name.endswith(s) for s in BAD_SUFFIXES):
        return None
    return name




# Sprint 4.1 (H) — raw-SQL INSERT INTO detection.
# Pattern: text("INSERT INTO <table> (col1, col2, ...) VALUES (...)")
# Flag if the SQL string has INSERT INTO but lacks ANY reference to
# company_id (column name OR :company_id bind OR app.company_id GUC).

_INSERT_INTO_RE = re.compile(r"\bINSERT\s+INTO\s+(\w+)", re.IGNORECASE)


def _sql_string_from_text_call(node: ast.Call) -> str | None:
    """If node is text("...") or sa.text("..."), return the SQL string;
    None otherwise.
    """
    func = node.func
    if isinstance(func, ast.Name):
        if func.id != "text":
            return None
    elif isinstance(func, ast.Attribute):
        if func.attr != "text":
            return None
    else:
        return None
    if not node.args:
        return None
    first = node.args[0]
    if isinstance(first, ast.Constant) and isinstance(first.value, str):
        return first.value
    # Multi-line strings sometimes appear as JoinedStr or concatenation.
    # For our heuristic we ignore those (would require constant-folding).
    return None


def _sql_has_company_id(sql: str) -> bool:
    """Return True if the raw SQL references company_id in any canonical form:
    - column name `company_id`
    - bind param `:company_id`
    - GUC reference `app.company_id`
    """
    s = sql.lower()
    return "company_id" in s


def _scan_raw_sql_inserts(tree: ast.AST, src_lines: list[str], path: Path) -> list[Violation]:
    out: list[Violation] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        sql = _sql_string_from_text_call(node)
        if not sql:
            continue
        m = _INSERT_INTO_RE.search(sql)
        if not m:
            continue
        table = m.group(1)
        if _sql_has_company_id(sql):
            continue
        if _line_has_exempt(src_lines, node.lineno):
            continue
        out.append(
            Violation(
                file=str(path.relative_to(REPO_ROOT)),
                line=node.lineno,
                col=node.col_offset,
                model=f"text('INSERT INTO {table} ...')",
                has_user_id=False,
                has_company_id=False,
                suggestion=(
                    f"Raw SQL INSERT INTO `{table}` does not reference "
                    f"`company_id` anywhere. If this table has an RLS "
                    f"policy, the INSERT will be rejected at runtime "
                    f"(asyncpg.InsufficientPrivilegeError). Canonical "
                    f"fix: add `company_id` to both the column list "
                    f"AND the VALUES clause, sourced from the repo "
                    f"method's required company_id parameter. If the "
                    f"table is genuinely tenant-less, add `# RLS-EXEMPT: "
                    f"<reason>` on the line above."
                ),
            )
        )
    return out


class Walker(ast.NodeVisitor):
    def __init__(self, src_lines: list[str], path: Path):
        self.src_lines = src_lines
        self.path = path
        self.violations: list[Violation] = []

    def visit_Call(self, node: ast.Call) -> None:
        model = _model_name_of(node)
        if model:
            kwargs = _extract_call_kwargs(node)
            has_uid = "user_id" in kwargs
            has_cid = "company_id" in kwargs
            always_required = model in REQUIRED_COMPANY_ID_MODELS
            if (has_uid or always_required) and not has_cid:
                if not _line_has_exempt(self.src_lines, node.lineno):
                    self.violations.append(
                        Violation(
                            file=str(self.path.relative_to(REPO_ROOT)),
                            line=node.lineno,
                            col=node.col_offset,
                            model=model,
                            has_user_id=has_uid,
                            has_company_id=False,
                            suggestion=(
                                f"Add company_id= kwarg to the {model}(...) "
                                f"constructor. Tables with RLS policy reject "
                                f"INSERT with NULL company_id at runtime "
                                f"(asyncpg.InsufficientPrivilegeError). "
                                f"Canonical fix: thread company_id from the "
                                f"handler (Depends(require_company_id)) "
                                f"through the repo method as a REQUIRED "
                                f"parameter, and raise ValueError if empty "
                                f"(fail-closed per ADR-001). If this row is "
                                f"genuinely tenant-less (system table, global "
                                f"registry), add `# RLS-EXEMPT: <reason>` on "
                                f"the line above."
                            ),
                        )
                    )
        self.generic_visit(node)


def scan_file(path: Path) -> list[Violation]:
    try:
        src = path.read_text()
    except (OSError, UnicodeDecodeError):
        return []
    try:
        tree = ast.parse(src, filename=str(path))
    except SyntaxError as e:
        print(f"warn: syntax error parsing {path}: {e}", file=sys.stderr)
        return []
    src_lines = src.splitlines()
    walker = Walker(src_lines, path)
    walker.visit(tree)
    # Sprint 4.1 (H) — append raw-SQL INSERT INTO violations
    raw_sql_violations = _scan_raw_sql_inserts(tree, src_lines, path)
    return walker.violations + raw_sql_violations


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
                        help="paths to scan (relative to repo root)")
    parser.add_argument("--json", action="store_true",
                        help="emit machine-readable JSON")
    parser.add_argument("--max-violations", type=int, default=0,
                        help="exit 1 if violations > N (default: 0, blocking)")
    parser.add_argument("--warn-only", action="store_true",
                        help="never exit non-zero (opt-out of blocking mode)")
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
            print("OK RLS sensor clean: no <Model>(user_id=..., ...) "
                  "constructors missing company_id.")
        else:
            print(f"FAIL {len(all_violations)} RLS company_id gap(s):\n")
            by_file: dict[str, list[Violation]] = {}
            for v in all_violations:
                by_file.setdefault(v.file, []).append(v)
            for file, vs in sorted(by_file.items()):
                print(f"  {file}")
                for v in vs:
                    print(f"    L{v.line:>4} col {v.col:>3}  "
                          f"{v.model}(user_id=..., ...)  <-- missing company_id=")
                print()
            unique_models = sorted({v.model for v in all_violations})
            print("Canonical fix:")
            for m in unique_models[:5]:
                print(f"    {m}(user_id=..., company_id=company_id, ...)")
            if len(unique_models) > 5:
                print(f"    ...({len(unique_models) - 5} more model(s))")
            print()
            print("Repo method canonical:")
            print("    async def create_X(self, user_id: str, company_id: str):")
            print("        if not company_id:")
            print("            raise ValueError('company_id required "
                  "(multi-tenancy fail-closed)')")
            print("        obj = Model(user_id=user_id, "
                  "company_id=company_id, ...)")
            print()
            print("Escape hatch (rare, document the reason):")
            print("    # RLS-EXEMPT: <table is genuinely tenant-less>")
            print("    obj = Model(user_id=..., ...)")

    if args.warn_only:
        return 0
    if len(all_violations) > args.max_violations:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
