#!/usr/bin/env python3
"""Sprint 3 canonical sensor — every registered tool MUST have a canonical category.

Bug class prevented: new tool added to the registry without an entry in
app/tools/categories.TOOL_TO_CATEGORY → lands in "OTHER" → invisible to the
LLM capability section grouped view. The LLM treats it as if it didn't exist.

Canonical contract:
  1. Every tool registered via tool_registry.register() must have category
     populated from TOOL_TO_CATEGORY (auto-applied by registry).
  2. category == "OTHER" means the dev forgot to add the mapping.
  3. Sensor exits non-zero in --blocking mode if ANY tool is in OTHER.

Bypass: add the tool to TOOL_TO_CATEGORY in app/tools/categories.py.
There is NO escape hatch — every action tool has a category by design.

Usage:
    python scripts/check_tools_have_category.py
    python scripts/check_tools_have_category.py --blocking
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--blocking", action="store_true",
                        help="exit 1 if any tool is in OTHER (default: warn)")
    parser.add_argument("--json", action="store_true",
                        help="emit JSON report for CI tooling")
    args = parser.parse_args()

    # Add repo root to sys.path so we can import app.*
    sys.path.insert(0, str(REPO_ROOT))
    # Set required env var defaults to allow boot
    os.environ.setdefault("DATABASE_URL", "postgresql://stub/stub")

    try:
        from app.tools import initialize_tools  # noqa: WPS433 import-in-func
        from app.tools.registry import tool_registry
    except Exception as exc:  # pragma: no cover — boot failure
        print(f"FAIL: cannot import tool registry: {exc}", file=sys.stderr)
        return 2

    try:
        initialize_tools()
    except Exception as exc:
        print(f"FAIL: tool init raised: {exc}", file=sys.stderr)
        return 2

    other_tools = sorted(
        t.name for t in tool_registry._tools.values() if t.category == "OTHER"
    )
    total = len(tool_registry._tools)
    in_other = len(other_tools)

    if args.json:
        print(json.dumps({
            "total_tools": total,
            "uncategorized": in_other,
            "tool_names": other_tools,
        }, indent=2))
    else:
        if in_other == 0:
            print(f"OK tools_have_category sensor clean: {total}/{total} tools have canonical category.")
        else:
            print(f"FAIL {in_other}/{total} tools landed in OTHER category:")
            print()
            for name in other_tools:
                print(f"  - {name}")
            print()
            print("Fix: add each name to TOOL_TO_CATEGORY in app/tools/categories.py")
            print("with the appropriate ToolCategory.* value. There is no escape hatch")
            print("for this sensor — every action tool MUST have a category.")

    if args.blocking and in_other > 0:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
