#!/usr/bin/env python3
"""Task #1143 — Warn-only CI sensor for `_require_company_id` sweep progress.

Counts remaining occurrences of the canonical TODO marker
``Sprint follow-up: add _require_company_id explicit gate`` across
``app/api/``.

Modes:
  - default (warn-only): prints the count, always exits 0. Used in CI to
    track progress without blocking the pipeline.
  - ``--block``: exits 1 when the count is greater than zero. Used by the
    Sealing task (S10) once the sweep is complete.
  - ``--max=N``: ratchet mode. Exits 1 if count exceeds N. Used during
    incremental sweep to prevent regressions (new endpoints without gate).

This sensor pairs with ``apply_require_company_id.py`` (exploratory sweep
tool) and ``app/shared/security/require_company_id.py`` (the helper itself).
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
API_DIR = ROOT / "app" / "api"
MARKER = "Sprint follow-up: add _require_company_id"


def count_marker_lines() -> tuple[int, dict[str, int]]:
    total = 0
    per_file: dict[str, int] = {}
    if not API_DIR.is_dir():
        return 0, per_file
    for py in API_DIR.rglob("*.py"):
        try:
            src = py.read_text(encoding="utf-8")
        except Exception:
            continue
        n = src.count(MARKER)
        if n:
            per_file[str(py.relative_to(ROOT))] = n
            total += n
    return total, per_file


def parse_max(args: list[str]) -> int | None:
    for a in args:
        m = re.match(r"--max=(\d+)$", a)
        if m:
            return int(m.group(1))
    return None


def main() -> int:
    args = sys.argv[1:]
    block = "--block" in args
    max_allowed = parse_max(args)
    verbose = "-v" in args or "--verbose" in args

    total, per_file = count_marker_lines()

    print(
        f"[require_company_id sensor] {total} pending occurrences of "
        f"`{MARKER}` across {len(per_file)} file(s)."
    )
    if verbose:
        for path, n in sorted(per_file.items(), key=lambda kv: -kv[1])[:20]:
            print(f"  {n:>4}  {path}")

    if block and total > 0:
        print(
            "[require_company_id sensor] BLOCK mode: failing because "
            "TODO marker is still present. Apply the gate via "
            "`Depends(require_company_id)` (see "
            "app/shared/security/require_company_id.py).",
            file=sys.stderr,
        )
        return 1

    if max_allowed is not None and total > max_allowed:
        print(
            f"[require_company_id sensor] RATCHET broken: {total} > {max_allowed}. "
            "A new endpoint without the gate was likely added — please apply "
            "Depends(require_company_id) before merging.",
            file=sys.stderr,
        )
        return 1

    if total == 0:
        print("[require_company_id sensor] OK — sweep complete.")
    else:
        print(
            "[require_company_id sensor] WARN-ONLY mode — not blocking. "
            "Pass --block once the sweep is complete (Task #1143 Sealing)."
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
