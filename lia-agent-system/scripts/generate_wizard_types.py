#!/usr/bin/env python3
"""Generate ``plataforma-lia/src/types/generated/wizard-contract.ts``.

Audit finding **N-12** (Rev 4) — keeps the recruiter UI's wizard types
synced with the Python ``BaseModel``s in
``app/contracts/wizard_contract.py`` so we never ship a runtime payload
the frontend cannot parse.

Pipeline
--------
1. Walk ``WIZARD_CONTRACT_MODELS`` and ask each model for its JSON
   Schema (Pydantic v2 ``model_json_schema(mode='serialization')``).
2. Merge them into a single root schema with a shared ``$defs`` block
   so ``$ref`` cycles between models resolve correctly.
3. Pipe the merged schema into ``npx --yes json-schema-to-typescript``
   (downloads on demand the first time, then cached by npm) and write
   the result to the canonical TS path.
4. Prepend a "DO NOT EDIT" header that points contributors at this
   script + the contract module.

Two run modes
-------------
- ``--write`` (default): regenerate and overwrite the TS file.
- ``--check``: regenerate to a temp file and ``diff`` against the
  committed copy. Non-zero exit if they differ — used by CI / the
  ``check:wizard-types`` npm script to fail loud on drift.

Usage
-----
    python3 lia-agent-system/scripts/generate_wizard_types.py
    python3 lia-agent-system/scripts/generate_wizard_types.py --check
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent.parent  # /home/runner/workspace
LIA_BACKEND = REPO_ROOT / "lia-agent-system"
TS_OUT = (
    REPO_ROOT
    / "plataforma-lia"
    / "src"
    / "types"
    / "generated"
    / "wizard-contract.ts"
)

HEADER = """\
/* eslint-disable */
/**
 * THIS FILE IS AUTO-GENERATED — DO NOT EDIT BY HAND.
 *
 * Source of truth: lia-agent-system/app/contracts/wizard_contract.py
 * Generator:       lia-agent-system/scripts/generate_wizard_types.py
 *
 * To regenerate after changing the Pydantic contracts:
 *   cd plataforma-lia && npm run generate:wizard-types
 *
 * CI enforces no drift via:
 *   cd plataforma-lia && npm run check:wizard-types
 */
"""


def _ensure_backend_on_path() -> None:
    """Make ``app.contracts.wizard_contract`` importable.

    The backend uses an in-tree layout (no installed package), so we
    splice ``lia-agent-system`` onto ``sys.path`` ahead of anything else.
    """
    sys.path.insert(0, str(LIA_BACKEND))


def _build_combined_schema() -> dict[str, Any]:
    """Merge every contract model into a single JSON Schema.

    The trick: Pydantic happily renders one model's full schema with
    inlined ``$defs`` for every nested model. Asking for one big root
    schema means ``json-schema-to-typescript`` emits each ``$defs``
    entry as a top-level ``export interface`` — exactly what we want.
    """
    _ensure_backend_on_path()
    from app.contracts.wizard_contract import WIZARD_CONTRACT_MODELS

    combined_defs: dict[str, Any] = {}
    properties: dict[str, Any] = {}

    for model in WIZARD_CONTRACT_MODELS:
        schema = model.model_json_schema(mode="serialization")
        # Pydantic puts nested models under "$defs"; collect them.
        for name, sub in (schema.pop("$defs", None) or {}).items():
            combined_defs.setdefault(name, sub)
        title = schema.get("title") or model.__name__
        # Drop the inner title to avoid duplicate `export interface Title` —
        # we expose each model via the $defs below.
        schema.pop("title", None)
        combined_defs[title] = schema
        properties[title] = {"$ref": f"#/$defs/{title}"}

    return {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "WizardContract",
        "type": "object",
        "additionalProperties": False,
        "properties": properties,
        "$defs": combined_defs,
    }


def _run_json_schema_to_typescript(schema: dict[str, Any]) -> str:
    """Invoke ``npx --yes json-schema-to-typescript`` against the schema.

    We avoid declaring a permanent npm devDependency (the generator is
    a build-time tool) — ``--yes`` lets npx fetch and cache it once.
    """
    if shutil.which("npx") is None:
        sys.stderr.write(
            "ERROR: `npx` not found on PATH; install Node.js to generate types.\n"
        )
        sys.exit(2)

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False, encoding="utf-8"
    ) as tmp:
        json.dump(schema, tmp, ensure_ascii=False, indent=2)
        schema_path = tmp.name

    try:
        proc = subprocess.run(
            [
                "npx",
                "--yes",
                "json-schema-to-typescript@15",
                "--no-additionalProperties",
                "--unreachableDefinitions",
                schema_path,
            ],
            capture_output=True,
            text=True,
            check=False,
        )
    finally:
        try:
            os.unlink(schema_path)
        except OSError:
            pass

    if proc.returncode != 0:
        sys.stderr.write("npx json-schema-to-typescript failed:\n")
        sys.stderr.write(proc.stderr)
        sys.exit(proc.returncode)

    return HEADER + "\n" + proc.stdout.strip() + "\n"


def _write_ts(ts: str) -> None:
    TS_OUT.parent.mkdir(parents=True, exist_ok=True)
    TS_OUT.write_text(ts, encoding="utf-8")
    print(f"[wizard-types] wrote {TS_OUT.relative_to(REPO_ROOT)}")


def _check_ts(ts: str) -> int:
    if not TS_OUT.exists():
        sys.stderr.write(
            f"[wizard-types] {TS_OUT.relative_to(REPO_ROOT)} is missing — "
            "run `npm run generate:wizard-types` and commit the result.\n"
        )
        return 1
    current = TS_OUT.read_text(encoding="utf-8")
    if current == ts:
        print("[wizard-types] OK — generated TS matches the committed file.")
        return 0
    sys.stderr.write(
        "[wizard-types] DRIFT — generated TS differs from the committed file.\n"
        "  Run `cd plataforma-lia && npm run generate:wizard-types` and commit.\n"
    )
    # Show a short unified diff to make the failure self-explanatory.
    import difflib

    diff = "".join(
        difflib.unified_diff(
            current.splitlines(keepends=True),
            ts.splitlines(keepends=True),
            fromfile="committed",
            tofile="regenerated",
            n=3,
        )
    )
    sys.stderr.write(diff[:4000])
    return 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--check",
        action="store_true",
        help="Regenerate and diff against the committed file; non-zero on drift.",
    )
    args = parser.parse_args()

    schema = _build_combined_schema()
    ts = _run_json_schema_to_typescript(schema)

    if args.check:
        return _check_ts(ts)

    _write_ts(ts)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
