#!/usr/bin/env python3
"""
Sync sensor: GLOBAL_UI_ACTION_TYPES_CORE (Python canonical) must match
the GlobalUIAction discriminated union in plataforma-lia/src/types/ui-action.ts.

Exits 0 if in sync, 1 if diverged. Prints actionable fix instructions.

Usage:
  python3 scripts/check_ui_action_ts_sync.py
  python3 scripts/check_ui_action_ts_sync.py --warn-only   (always exits 0)
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
TS_FILE = REPO_ROOT.parent / "plataforma-lia" / "src" / "types" / "ui-action.ts"

warn_only = "--warn-only" in sys.argv


def extract_py_types() -> frozenset[str]:
    """Load GLOBAL_UI_ACTION_TYPES_CORE from the canonical Python module."""
    import importlib.util
    sys.path.insert(0, str(REPO_ROOT))
    spec = importlib.util.spec_from_file_location(
        "ui_action_canonical",
        REPO_ROOT / "app" / "shared" / "ui_action_canonical.py",
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.GLOBAL_UI_ACTION_TYPES_CORE


def extract_ts_types(ts_path: Path) -> frozenset[str]:
    """Extract string literals from the GlobalUIAction discriminated union.
    The TS union uses:  type: "string_name";  inside the GlobalUIAction type alias.
    Strategy: slice from 'export type GlobalUIAction' to the next 'export ' keyword
    (the union spans many lines and contains internal semicolons).
    """
    content = ts_path.read_text(encoding="utf-8")
    idx_start = content.find("export type GlobalUIAction")
    if idx_start == -1:
        raise ValueError(f"Could not find 'export type GlobalUIAction' in {ts_path}")
    # Find next top-level export after the GlobalUIAction block
    idx_end = content.find("\nexport ", idx_start + 1)
    block = content[idx_start:idx_end if idx_end != -1 else len(content)]
    # Find all  type: "..."  string literals in the union block (discriminant field)
    return frozenset(re.findall(r'type:\s*"([^"]+)"', block))


def main() -> int:
    if not TS_FILE.exists():
        print(f"ERROR: TS file not found: {TS_FILE}")
        return 1 if not warn_only else 0

    py_types = extract_py_types()
    ts_types = extract_ts_types(TS_FILE)

    in_py_not_ts = py_types - ts_types
    in_ts_not_py = ts_types - py_types

    if not in_py_not_ts and not in_ts_not_py:
        print(f"OK UI action sync: {len(py_types)} types in sync (py canonical == ts GlobalUIAction)")
        return 0

    print("FAIL UI action sync divergence detected:\n")
    if in_py_not_ts:
        print("  In Python canonical (GLOBAL_UI_ACTION_TYPES_CORE) but NOT in TypeScript:")
        for t in sorted(in_py_not_ts):
            print(f'    -> Add to GlobalUIAction union in ui-action.ts:  type: "{t}"')
    if in_ts_not_py:
        print("\n  In TypeScript GlobalUIAction but NOT in Python canonical:")
        for t in sorted(in_ts_not_py):
            print(f"    -> Add to GLOBAL_UI_ACTION_TYPES_CORE in app/shared/ui_action_canonical.py")
    print("\n-> Fix: keep both in sync. Python canonical is the source of truth.")
    return 0 if warn_only else 1


if __name__ == "__main__":
    sys.exit(main())
