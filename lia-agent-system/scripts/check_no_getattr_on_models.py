"""
G6 — No getattr fallback on SQLAlchemy model rows.

Purpose
-------
Detect `getattr(<row_var>, "<attr>", <default>)` patterns when <row_var> looks
like a SQLAlchemy model instance (named row, conv, user, candidate, vacancy,
job, audit, etc.) AND the attribute name corresponds to a known model column.

This pattern silently masks schema bugs: if the column doesn't exist on the
model, getattr returns the default (typically None) without any error,
producing wrong behavior downstream. The cost was concrete: P0-1 in
AUDITORIA_TEAMS_2026-04-26.md — _resolve_company_id returned None for every
Teams message because TeamsConversation didn't have company_id (the column
was added later in Migration 097, but until then getattr masked the bug).

Rule
----
Direct attribute access (row.column) is correct. If the model is missing the
column, AttributeError is raised — fail-fast, easy to debug.

Use getattr ONLY for runtime objects whose schema is genuinely dynamic
(e.g. settings dataclasses with optional flags). NEVER for SQLAlchemy rows.

Exit codes
----------
0  -> no violations (or only justified ones with `# G6 ok: <reason>`)
1  -> violations found

Output is optimized for LLM consumption: each violation includes a suggested
fix in natural language so an agent reading the lint output can self-correct.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_APP = _ROOT / "app"
_LIBS = _ROOT / "libs"

# Pattern: getattr(<varname>, "<attr>", <default>)
# Captures the variable name, the attribute name, and the default expr.
_GETATTR = re.compile(
    r'getattr\(\s*([a-zA-Z_][\w]*)\s*,\s*["\']([\w_]+)["\']\s*,\s*([^)]+)\)'
)

# Variable names that strongly suggest a SQLAlchemy model row.
# (Matched as a whole word against the var captured above.)
_ROW_VAR_HINTS = frozenset({
    "row", "rows", "obj", "instance", "record",
    "conv", "conversation", "msg", "message", "messages",
    "user", "users", "candidate", "candidates",
    "vacancy", "vacancies", "job", "jobs",
    "audit", "audit_log", "auditlog",
    "feedback", "ticket", "submission",
    "evaluation", "screening",
    "subscription", "notification",
    "session", "stage",
})

# Attribute names that almost always belong to model columns
# (multi-tenant + audit fields most commonly affected).
_MODEL_COLUMN_HINTS = frozenset({
    "company_id", "tenant_id", "account_id", "workspace_id",
    "candidate_id", "vacancy_id", "job_id", "user_id",
    "created_at", "updated_at", "deleted_at",
    "is_active", "is_deleted", "status",
    "actor_id", "actor_name",
    "azure_ad_object_id", "aad_object_id", "user_aad_object_id",
})

# Inline opt-out: `# G6 ok: <reason>` on the same line or the line above.
_OK_MARKER = re.compile(r"#\s*G6\s*ok\s*:", re.IGNORECASE)


def _is_violation(var: str, attr: str) -> bool:
    """True when the (var, attr) pair looks like model-row + model-column."""
    return var.lower() in _ROW_VAR_HINTS and attr.lower() in _MODEL_COLUMN_HINTS


def _scan() -> list[tuple[Path, int, str, str, str]]:
    violations: list[tuple[Path, int, str, str, str]] = []
    for base in (_APP, _LIBS):
        if not base.exists():
            continue
        for py in base.rglob("*.py"):
            try:
                lines = py.read_text(errors="ignore").splitlines()
            except Exception:
                continue
            for idx, line in enumerate(lines):
                m = _GETATTR.search(line)
                if not m:
                    continue
                var, attr, default = m.group(1), m.group(2), m.group(3).strip()
                if not _is_violation(var, attr):
                    continue
                # Skip if line itself or previous line carries the opt-out
                if _OK_MARKER.search(line):
                    continue
                if idx - 1 >= 0 and _OK_MARKER.search(lines[idx - 1]):
                    continue
                violations.append((py, idx + 1, var, attr, default))
    return violations


def main() -> int:
    violations = _scan()
    if not violations:
        return 0

    print("=" * 78)
    print("G6 — getattr fallback on model row detected (schema bug masking)")
    print("=" * 78)
    print()
    print("This pattern hides missing-column schema bugs silently. See P0-1 in")
    print("AUDITORIA_TEAMS_2026-04-26.md for the cost: every Teams message lost")
    print("its company_id because the column didn't exist and getattr returned None.")
    print()
    print("Fix (canonical):")
    print("  1. Use direct attribute access:  row.column   (not getattr(...))")
    print("  2. If the column may legitimately be absent, check explicitly:")
    print('       if hasattr(row, "column") and row.column:')
    print('           ...')
    print("  3. If you intentionally need a runtime fallback, add:")
    print('       # G6 ok: <reason — why this is dynamic, not a schema bug>')
    print("     on the same line OR the line above.")
    print()
    print(f"Violations ({len(violations)}):")
    print("-" * 78)
    for path, line_no, var, attr, default in violations:
        rel = path.relative_to(_ROOT)
        print(f"  {rel}:{line_no}")
        print(f"    found: getattr({var}, \"{attr}\", {default})")
        print(f"    fix:   {var}.{attr}  (or add `# G6 ok: <reason>`)")
        print()
    return 1


if __name__ == "__main__":
    sys.exit(main())
