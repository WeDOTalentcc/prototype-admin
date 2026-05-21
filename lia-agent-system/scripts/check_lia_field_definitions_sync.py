#!/usr/bin/env python3
"""
P2-10 schema-sync sensor (audit 2026-05-21): pin canonical field-definition
list across the Python backend and the TypeScript frontend.

Both ends declare the same 34-canonical-field list under different names:

- **Python (lia-agent-system):** ``DEFAULT_FIELD_TOGGLES`` in
  ``libs/models/lia_models/lia_field_toggles.py``.
- **TypeScript (plataforma-lia):** ``LIA_FIELD_DEFINITIONS`` in
  ``src/hooks/company/use-company-lia-instructions.ts``.

Drift here is silent and devastating: the frontend exposes toggle X, the
recruiter flips it, the backend has no row for X in ``DEFAULT_FIELD_TOGGLES``
so the persistence layer treats the toggle as a no-op. Or vice-versa: the
backend reads field Y from the canonical list, the frontend never offers
a toggle for it, and the recruiter cannot opt out.

This script computes the symmetric difference of the two key sets and
exits non-zero if anything is in one side but not the other.

## Why a script and not a unit test

The TS side has no Python parser; we extract via regex over the .ts file.
That style of validation lives more naturally in scripts/ alongside other
harness lints (e.g. ``check_pydantic_conventions.py``) than in tests/.

## How to fix when it fails

Output prints the canonical sets and the diff with paths + suggested
edits. The message is LLM-friendly: a coding agent reading the failure
should know exactly what to add where without needing a human translator.

Run manually::

    python3 scripts/check_lia_field_definitions_sync.py

CI usage: invoke the same way; non-zero exit fails the job.
"""
from __future__ import annotations

import pathlib
import re
import sys


REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
PYTHON_FILE = REPO_ROOT / "libs/models/lia_models/lia_field_toggles.py"
# The TS file is in a sibling repo within the same Replit workspace.
TS_FILE = (
    REPO_ROOT.parent
    / "plataforma-lia/src/hooks/company/use-company-lia-instructions.ts"
)


def extract_python_keys() -> set[str]:
    """Pull ``field_key`` values out of the DEFAULT_FIELD_TOGGLES list.

    We do NOT import the module (would pull DB models, ORM machinery, the
    full lia_models tree). Regex over the literal Python source is
    deterministic and fast — 34 lines, 1ms.
    """
    if not PYTHON_FILE.exists():
        print(f"❌ Python source not found: {PYTHON_FILE}", file=sys.stderr)
        sys.exit(2)
    text = PYTHON_FILE.read_text()
    # Match: {"field_key": "<name>", "is_active": ...}
    pattern = re.compile(r'"field_key"\s*:\s*"([^"]+)"')
    keys = set(pattern.findall(text))
    if not keys:
        print(f"❌ No field_key entries found in {PYTHON_FILE}", file=sys.stderr)
        sys.exit(2)
    return keys


def extract_ts_keys() -> set[str]:
    """Pull top-level identifiers from ``LIA_FIELD_DEFINITIONS = { ... }``.

    Stops at the first ``} as const`` so we never accidentally swallow
    sibling declarations. Lines that are not field declarations (comments,
    blank lines, type definitions) are skipped via the trailing ``: {``
    pattern check.
    """
    if not TS_FILE.exists():
        print(f"❌ TypeScript source not found: {TS_FILE}", file=sys.stderr)
        sys.exit(2)
    text = TS_FILE.read_text()
    # Slice from declaration to closing brace.
    start = text.find("export const LIA_FIELD_DEFINITIONS")
    if start == -1:
        print(
            f"❌ LIA_FIELD_DEFINITIONS not found in {TS_FILE}",
            file=sys.stderr,
        )
        sys.exit(2)
    end = text.find("} as const", start)
    if end == -1:
        print(
            f"❌ Could not locate end of LIA_FIELD_DEFINITIONS in {TS_FILE} "
            f"(expected backtick-bracket-as-const terminator).",
            file=sys.stderr,
        )
        sys.exit(2)
    body = text[start:end]
    # Match: <key>: { label: ...  — only those that open an object literal.
    pattern = re.compile(r"^\s*([a-z_][a-z0-9_]*)\s*:\s*\{", re.MULTILINE)
    keys = set(pattern.findall(body))
    if not keys:
        print(f"❌ No field entries parsed from {TS_FILE}", file=sys.stderr)
        sys.exit(2)
    return keys


def main() -> int:
    py_keys = extract_python_keys()
    ts_keys = extract_ts_keys()

    only_in_python = py_keys - ts_keys
    only_in_ts = ts_keys - py_keys

    if not only_in_python and not only_in_ts:
        print(
            f"✅ lia_field definitions in sync — {len(py_keys)} canonical "
            f"fields match across Python and TypeScript."
        )
        return 0

    print(
        "❌ lia_field definition drift detected between Python and TypeScript.\n"
    )
    if only_in_python:
        print(
            f"  Fields in Python ({PYTHON_FILE.name}) but missing in TypeScript:"
        )
        for k in sorted(only_in_python):
            print(f"    - {k}")
        print(
            f"\n  Fix: add entries for these keys to LIA_FIELD_DEFINITIONS in\n"
            f"    {TS_FILE.relative_to(REPO_ROOT.parent)}\n"
            f"  Use the canonical label/category/location convention from "
            f"the existing entries.\n"
        )
    if only_in_ts:
        print(
            f"  Fields in TypeScript ({TS_FILE.name}) but missing in Python:"
        )
        for k in sorted(only_in_ts):
            print(f"    - {k}")
        print(
            f'\n  Fix: add `{{"field_key": "<name>", "is_active": True}}` '
            f"entries to DEFAULT_FIELD_TOGGLES in\n"
            f"    {PYTHON_FILE.relative_to(REPO_ROOT.parent)}\n"
            f"  Plus a FIELD_FALLBACK_CONFIG entry if the field needs a "
            f"fallback strategy.\n"
        )
    print(
        "  Both sides MUST stay aligned — drift means the recruiter "
        "configures one side and the agents/backend cannot honor it."
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
