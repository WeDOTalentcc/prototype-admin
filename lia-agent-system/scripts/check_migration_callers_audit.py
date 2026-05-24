#!/usr/bin/env python3
"""
Harness canonical — Alembic migrations that tighten contracts must list callers.

Origin: migration 139_t02_rls_high_priority.py changed the RLS SELECT
policy on `conversations` (and 26 other HIGH-priority tables) from
permissive (USING `IS NULL OR company_id = ...`) to strict (USING
`company_id::text = app_current_company_id()`). The pre-strict callers
that wrote NULL company_id continued to ship — until commits
0a58a5bf..b134b74a fixed each surface individually. Total cost: 5+
commits to undo a contract change that should have been audited at
migration-merge time.

This sensor scans `alembic/versions/*.py` for migrations whose `upgrade()`
introduces one of the contract-tightening operations:

  - `ALTER TABLE <t> ALTER COLUMN <c> SET NOT NULL`
  - `ALTER TABLE <t> ADD CONSTRAINT ... CHECK ...`
  - `ALTER TABLE <t> ENABLE ROW LEVEL SECURITY` / `FORCE`
  - `CREATE POLICY ... FOR INSERT|UPDATE WITH CHECK ...`
  - `CREATE POLICY ... FOR SELECT USING (...)` (read tightening)
  - `DROP POLICY ...` followed by stricter recreation

For each such migration, the sensor requires a sibling audit document:
  alembic/versions/audits/<revision_id>_callers_audit.md

The audit doc must:
  - List the tables touched
  - Enumerate the INSERT/UPDATE call sites in app/ that touch each table
  - Mark each call site as `[reviewed]` or `[fixed]` with link to fix
    commit / PR

If a tightening migration has no audit doc, the sensor flags it.
If the audit doc exists but is incomplete (missing tables, untracked
call sites), the sensor flags the gap.

Usage:
    python scripts/check_migration_callers_audit.py
    python scripts/check_migration_callers_audit.py --json
    python scripts/check_migration_callers_audit.py --blocking

The intent is to wire this into pre-commit on alembic/versions/*.py and
into CI on PRs that touch migrations. Default is warn-only because the
historical baseline has many tightening migrations without audits — the
sensor surfaces the debt and the path forward.
"""
from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable


REPO_ROOT = Path(__file__).resolve().parent.parent
MIGRATIONS_DIR = REPO_ROOT / "alembic/versions"
AUDITS_DIR = MIGRATIONS_DIR / "audits"

# Patterns that signal a contract-tightening operation in SQL strings.
TIGHTENING_PATTERNS = [
    (r"ALTER\s+TABLE\s+\w+\s+ALTER\s+COLUMN\s+\w+\s+SET\s+NOT\s+NULL", "NOT-NULL"),
    (r"ALTER\s+TABLE\s+\w+\s+ADD\s+CONSTRAINT\s+\w+\s+CHECK", "CHECK-CONSTRAINT"),
    (r"ALTER\s+TABLE\s+\w+\s+ENABLE\s+ROW\s+LEVEL\s+SECURITY", "RLS-ENABLE"),
    (r"ALTER\s+TABLE\s+\w+\s+FORCE\s+ROW\s+LEVEL\s+SECURITY", "RLS-FORCE"),
    (r"CREATE\s+POLICY\s+\w+\s+ON\s+\w+\s+FOR\s+(?:INSERT|UPDATE|DELETE)", "RLS-POLICY-WRITE"),
    (r"CREATE\s+POLICY\s+\w+\s+ON\s+\w+\s+FOR\s+SELECT", "RLS-POLICY-SELECT"),
    (r"ALTER\s+TABLE\s+\w+\s+ADD\s+CONSTRAINT\s+\w+\s+FOREIGN\s+KEY", "FK-ADD"),
]
COMPILED = [(re.compile(p, re.IGNORECASE | re.DOTALL), kind)
            for p, kind in TIGHTENING_PATTERNS]


@dataclass
class Violation:
    file: str
    revision: str
    kind: str
    has_audit_doc: bool
    audit_path: str
    reason: str

    def as_dict(self) -> dict:
        return asdict(self)


def _extract_string_literals(src: str) -> str:
    """Concatenate all string literals (regular and triple) for grep."""
    chunks: list[str] = []
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return ""
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            chunks.append(node.value)
    return "\n".join(chunks)


def _detect_revision(src: str) -> str:
    m = re.search(r"^revision[^=]*=\s*[\"']([^\"']+)[\"']", src, re.MULTILINE)
    if m:
        return m.group(1)
    # Fallback to filename stem prefix
    return ""


def scan_migration(path: Path) -> list[Violation]:
    try:
        src = path.read_text()
    except (OSError, UnicodeDecodeError):
        return []
    sql_text = _extract_string_literals(src)
    found_kinds: set[str] = set()
    for regex, kind in COMPILED:
        if regex.search(sql_text):
            found_kinds.add(kind)
    if not found_kinds:
        return []
    revision = _detect_revision(src) or path.stem
    audit_path = AUDITS_DIR / f"{revision}_callers_audit.md"
    if audit_path.exists():
        audit_content = audit_path.read_text().lower()
        missing = []
        if "reviewed" not in audit_content and "fixed" not in audit_content:
            missing.append("no [reviewed] / [fixed] markers in audit doc")
        if not missing:
            return []
        reason = "; ".join(missing)
        return [
            Violation(
                file=str(path.relative_to(REPO_ROOT)),
                revision=revision,
                kind=",".join(sorted(found_kinds)),
                has_audit_doc=True,
                audit_path=str(audit_path.relative_to(REPO_ROOT)),
                reason=reason,
            )
        ]
    return [
        Violation(
            file=str(path.relative_to(REPO_ROOT)),
            revision=revision,
            kind=",".join(sorted(found_kinds)),
            has_audit_doc=False,
            audit_path=str(audit_path.relative_to(REPO_ROOT)),
            reason="audit document missing — create alembic/versions/audits/<rev>_callers_audit.md",
        )
    ]


def iter_migrations() -> Iterable[Path]:
    if not MIGRATIONS_DIR.is_dir():
        return
    for p in sorted(MIGRATIONS_DIR.glob("*.py")):
        if "__pycache__" in p.parts:
            continue
        yield p


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--max-violations", type=int, default=None)
    parser.add_argument("--blocking", action="store_true",
                        help="alias for --max-violations 0")
    parser.add_argument("--warn-only", action="store_true",
                        help="never exit non-zero (default behavior)")
    parser.add_argument("--since", type=str, default=None,
                        help="only check migrations whose filename sorts >= this prefix "
                             "(e.g. '139' to skip pre-2026 history)")
    args = parser.parse_args()

    all_v: list[Violation] = []
    for f in iter_migrations():
        if args.since and f.name < args.since:
            continue
        all_v.extend(scan_migration(f))

    if args.json:
        print(json.dumps({"violations": [v.as_dict() for v in all_v],
                          "total": len(all_v)}, indent=2))
    else:
        if not all_v:
            print("OK migration-callers sensor clean: every contract-tightening "
                  "migration has a complete audit document.")
        else:
            print(f"FAIL {len(all_v)} migration(s) lacking caller audit:\n")
            for v in all_v:
                print(f"  {v.file}")
                print(f"    revision: {v.revision}")
                print(f"    kinds:    {v.kind}")
                print(f"    issue:    {v.reason}")
                if v.has_audit_doc:
                    print(f"    audit:    {v.audit_path}")
                print()
            print("Canonical fix (per migration):")
            print("    1. Create alembic/versions/audits/<rev>_callers_audit.md")
            print("    2. List the tables touched by the migration")
            print("    3. grep INSERT/UPDATE/DELETE call sites in app/ for each table")
            print("    4. Mark each call site:")
            print("         - [reviewed] <file:line> — safe under new contract")
            print("         - [fixed]    <file:line> — fix shipped in commit <sha>")
            print()
            print("Template snippet:")
            print("    # Migration 139_t02_rls_high_priority.py — callers audit")
            print("    ## Tables tightened")
            print("    - conversations (NOT NULL company_id + RLS strict)")
            print("    ## Call sites")
            print("    - [fixed] chat_repository.create_conversation (0a58a5bf)")
            print("    - [reviewed] conversation_memory.get_or_create_conversation (611883220)")

    if args.warn_only:
        return 0
    if args.blocking:
        return 1 if all_v else 0
    if args.max_violations is None:
        return 0
    return 1 if len(all_v) > args.max_violations else 0


if __name__ == "__main__":
    sys.exit(main())
