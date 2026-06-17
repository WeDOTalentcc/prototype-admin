#!/usr/bin/env python3
"""
S7.3 — Block the legacy `@tool` decorator inside domain tool modules.

Anti-revival of the migration `@tool` (langchain_core) → `@tool_handler`.
Domain tools (`app/domains/*/tools/*.py`) MUST use the in-house
`@tool_handler` decorator so cross-cutting concerns (audit, scope,
permission, fail-closed semantics) are applied uniformly.

Allow list: a small set of files that pre-date this rule are grandfathered
in. New files are blocked from day one. Removing entries from the allow list
as they migrate is the path forward.

Usage:
  python scripts/check_no_legacy_tool_decorator.py

Exit codes:
  0 — no new violations
  1 — at least one disallowed import found in `app/domains/*/tools/`
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOMAINS_ROOT = ROOT / "app" / "domains"

FORBIDDEN_RE = re.compile(
    r"^\s*from\s+langchain_core\.tools\s+import\s+([^\n]+)$",
    re.MULTILINE,
)

# Files grandfathered in. Each entry should be removed once the file migrates
# to `@tool_handler`. New entries are NOT accepted — onboarding new files via
# the allow list defeats the purpose of the guard.
ALLOW_LIST: set[str] = set()


def imports_legacy_tool(text: str) -> bool:
    for match in FORBIDDEN_RE.finditer(text):
        names = [n.strip() for n in match.group(1).replace("(", "").replace(")", "").split(",")]
        if any(n == "tool" or n.startswith("tool ") or n.startswith("tool as ") for n in names):
            return True
    return False


def main() -> int:
    if not DOMAINS_ROOT.exists():
        print(f"[no-legacy-tool] domains root not found: {DOMAINS_ROOT}", file=sys.stderr)
        return 0

    violations: list[str] = []
    for py in DOMAINS_ROOT.rglob("tools/*.py"):
        rel = str(py.relative_to(ROOT))
        try:
            text = py.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        if not imports_legacy_tool(text):
            continue
        if rel in ALLOW_LIST:
            continue
        violations.append(rel)

    if violations:
        print("[no-legacy-tool] forbidden `from langchain_core.tools import tool` found:")
        for v in violations:
            print(f"  - {v}")
        print("Use `from app.shared.tools.decorator import tool_handler` instead.")
        print("(Entries already in ALLOW_LIST are exempt; do not extend the allow list.)")
        return 1

    print(f"[no-legacy-tool] OK — {len(ALLOW_LIST)} grandfathered file(s) tracked")
    return 0


if __name__ == "__main__":
    sys.exit(main())
