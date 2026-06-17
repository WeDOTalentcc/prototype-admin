#!/usr/bin/env python3
"""
S7.5 — Block direct ``tool_registry.register(...)`` calls outside the canonical
authoring surface (Task #354, ADR-016).

ADR-016 declared a single canonical entry point for tool registration:

- New tools are authored with the ``@tool_handler`` decorator under
  ``app/domains/<domain>/tools/`` and exposed via ``get_<domain>_tools()`` in
  ``app/domains/<domain>/agents/<thing>_tool_registry.py``.
- The only file allowed to invoke ``tool_registry.register(...)`` is
  ``app/tools/__init__.py:initialize_tools()``, which aggregates the
  ``get_*_tools()`` results from each domain. ``app/tools/registry.py`` is
  exempt because it defines the registry itself.

Without an automated guard, a future contributor will quietly bypass tenant
checks and HITL by registering a tool directly — the exact regression that
S7.1–S7.3 already prevent for the other rules.

Allow list: a small set of files that pre-date this rule are grandfathered
in. New files are blocked from day one. Removing entries from the allow list
as they migrate to ``@tool_handler`` + ``get_<domain>_tools()`` is the path
forward.

Usage:
  python scripts/check_tool_authoring_surface.py

Exit codes:
  0 — no new violations
  1 — at least one disallowed ``tool_registry.register(`` call found outside
      the canonical entry point
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
APP_ROOT = ROOT / "app"

FORBIDDEN_RE = re.compile(r"\btool_registry\.register\s*\(")

# Files where ``tool_registry.register(`` is legitimate.
EXEMPT: set[str] = {
    "app/tools/__init__.py",   # canonical entry point (initialize_tools)
    "app/tools/registry.py",   # defines ToolRegistry.register itself
}

# Files grandfathered in. Each entry should be removed once the file migrates
# to ``@tool_handler`` + ``get_<domain>_tools()`` and ``initialize_tools()``
# starts aggregating that domain's tools instead. New entries are NOT
# accepted — onboarding new files via the allow list defeats the purpose
# of the guard.
ALLOW_LIST: set[str] = {
    "app/shared/tools/export_tools.py",
    "app/domains/talent_intelligence/tools/registry.py",
    "app/domains/analytics/tools/analytics_query_tools/registry.py",
    "app/domains/recruiter_assistant/tools/pipeline_tools.py",
    "app/domains/communication/tools/communication_tools.py",
    # `job_wizard_tools.py` removed in Task #850 (legacy WizardReActAgent path).
    "app/domains/job_management/tools/job_tools.py",
    "app/domains/job_management/tools/query_tools.py",
    "app/domains/cv_screening/tools/cv_upload_tool.py",
    "app/domains/cv_screening/tools/candidate_tools.py",
    "app/domains/sourcing/tools/query_tools.py",
}

SKIP_DIR_PARTS = {"__pycache__", ".venv", "venv", ".git", "node_modules", "tests", "test"}


def calls_register(text: str) -> bool:
    for line in text.splitlines():
        stripped = line.lstrip()
        if stripped.startswith("#"):
            continue
        if FORBIDDEN_RE.search(line):
            return True
    return False


def main() -> int:
    if not APP_ROOT.exists():
        print(f"[tool-authoring-surface] app root not found: {APP_ROOT}", file=sys.stderr)
        return 0

    violations: list[str] = []
    for py in APP_ROOT.rglob("*.py"):
        if any(part in SKIP_DIR_PARTS for part in py.parts):
            continue
        rel = str(py.relative_to(ROOT))
        if rel in EXEMPT:
            continue
        try:
            text = py.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        if not calls_register(text):
            continue
        if rel in ALLOW_LIST:
            continue
        violations.append(rel)

    if violations:
        print("[tool-authoring-surface] forbidden `tool_registry.register(` outside canonical entry point:")
        for v in violations:
            print(f"  - {v}")
        print()
        print("Author tools with `@tool_handler` under `app/domains/<domain>/tools/`")
        print("and expose them via `get_<domain>_tools()`; only")
        print("`app/tools/__init__.py:initialize_tools()` is allowed to call")
        print("`tool_registry.register(...)`. See ADR-016 for details.")
        print("(Entries already in ALLOW_LIST are exempt; do not extend the allow list.)")
        return 1

    print(
        f"[tool-authoring-surface] OK — {len(ALLOW_LIST)} grandfathered file(s) tracked, "
        f"{len(EXEMPT)} canonical file(s) exempt"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
