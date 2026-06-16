#!/usr/bin/env python3
"""
Harness canonical — suppressors must carry ticket + TTL (v2: tokenize).

v1 used line-based regex which matched the suppressor marker inside string
literals and docstrings (e.g., a sensor script that documents the marker
as part of its own help text). v2 uses tokenize to distinguish real
COMMENT tokens from STRING/NAME tokens, eliminating that false-positive
class.

For full doc, see v1 (this file replaces it). Behavior is identical
otherwise:

    # <SUPPRESSOR-KIND>: <reason>  WT-<N>  exp:<YYYY-MM-DD>

Usage:
    python scripts/check_suppressor_canonical.py
    python scripts/check_suppressor_canonical.py --json
    python scripts/check_suppressor_canonical.py --blocking
"""
from __future__ import annotations

import argparse
import io
import json
import re
import sys
import tokenize
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path
from typing import Iterable


REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PATHS = ["app", "libs", "scripts"]

SUPPRESSOR_PATTERNS = [
    (r"#\s*noqa(?::\s*[\w,]+)?\b", "noqa"),
    (r"#\s*type:\s*ignore(?:\[[\w,]+\])?", "type-ignore"),
    (r"#\s*pyright:\s*ignore", "pyright-ignore"),
    (r"#\s*pragma:\s*no\s*cover", "pragma-no-cover"),
    (r"#\s*RLS-EXEMPT:", "RLS-EXEMPT"),
    (r"#\s*RLS-OK:", "RLS-OK"),
    (r"#\s*TENANT-EXEMPT:", "TENANT-EXEMPT"),
    (r"#\s*ADR-001-EXEMPT", "ADR-001-EXEMPT"),
    (r"#\s*SENSOR-SUPPRESS\s+[\w-]+:", "SENSOR-SUPPRESS"),
    (r"#\s*(?:sensor\s+)?false\s+positive\b", "false-positive-claim"),
    (r"#\s*(?:re-?enable|reenable)\s+later", "reenable-later"),
]
COMPILED = [(re.compile(p, re.IGNORECASE), kind) for p, kind in SUPPRESSOR_PATTERNS]

TICKET_RE = re.compile(r"\bWT-(?:\d+|LEGACY(?:-[\w-]+)?)\b", re.IGNORECASE)
TTL_RE = re.compile(r"\bexp:(\d{4})-(\d{2})-(\d{2})\b", re.IGNORECASE)


@dataclass
class Violation:
    file: str
    line: int
    kind: str
    raw: str
    reason: str

    def as_dict(self) -> dict:
        return asdict(self)


def _validate(comment: str) -> tuple[bool, str]:
    has_ticket = bool(TICKET_RE.search(comment))
    ttl_match = TTL_RE.search(comment)
    if not has_ticket and not ttl_match:
        return False, "missing both ticket (WT-N) and exp:YYYY-MM-DD"
    if not has_ticket:
        return False, "missing ticket reference (WT-N or WT-LEGACY)"
    if not ttl_match:
        return False, "missing TTL (exp:YYYY-MM-DD)"
    try:
        y, m, d = int(ttl_match.group(1)), int(ttl_match.group(2)), int(ttl_match.group(3))
        ttl_date = date(y, m, d)
    except (ValueError, TypeError):
        return False, "TTL date malformed (use exp:YYYY-MM-DD)"
    if ttl_date < date.today():
        return False, f"TTL expired ({ttl_match.group(0)})"
    return True, ""


def scan_file(path: Path) -> list[Violation]:
    try:
        src = path.read_bytes()
    except OSError:
        return []
    out: list[Violation] = []
    try:
        tokens = list(tokenize.tokenize(io.BytesIO(src).readline))
    except tokenize.TokenizeError:
        return out
    for tok in tokens:
        if tok.type != tokenize.COMMENT:
            continue
        comment = tok.string
        for regex, kind in COMPILED:
            if not regex.search(comment):
                continue
            is_valid, reason = _validate(comment)
            if not is_valid:
                out.append(
                    Violation(
                        file=str(path.relative_to(REPO_ROOT)),
                        line=tok.start[0],
                        kind=kind,
                        raw=comment.strip()[:200],
                        reason=reason,
                    )
                )
            break
    return out


def iter_py_files(roots: Iterable[Path]) -> Iterable[Path]:
    for root in roots:
        if root.is_file() and root.suffix == ".py":
            yield root
            continue
        if not root.is_dir():
            continue
        for p in root.rglob("*.py"):
            parts = set(p.parts)
            if "__pycache__" in parts or ".venv" in parts:
                continue
            yield p


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--paths", nargs="*", default=DEFAULT_PATHS)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--max-violations", type=int, default=None)
    parser.add_argument("--blocking", action="store_true",
                        help="alias for --max-violations 0")
    parser.add_argument("--warn-only", action="store_true",
                        help="never exit non-zero (default behavior)")
    parser.add_argument("--kinds", nargs="*", default=None)
    args = parser.parse_args()

    roots = [REPO_ROOT / p for p in args.paths]
    all_v: list[Violation] = []
    for f in iter_py_files(roots):
        all_v.extend(scan_file(f))
    if args.kinds:
        all_v = [v for v in all_v if v.kind in set(args.kinds)]

    if args.json:
        print(json.dumps({"violations": [v.as_dict() for v in all_v],
                          "total": len(all_v)}, indent=2))
    else:
        if not all_v:
            print("OK suppressor sensor clean: every suppressor carries "
                  "WT-<N> + exp:YYYY-MM-DD.")
        else:
            print(f"FAIL {len(all_v)} suppressor(s) missing ticket or TTL:\n")
            by_kind: dict[str, int] = {}
            for v in all_v:
                by_kind[v.kind] = by_kind.get(v.kind, 0) + 1
            print("By kind:")
            for k, n in sorted(by_kind.items(), key=lambda x: -x[1]):
                print(f"  {n:5d}  {k}")
            print()
            print("Sample (first 10):")
            for v in all_v[:10]:
                print(f"  {v.file}:{v.line}  [{v.kind}]  {v.reason}")
                print(f"    raw: {v.raw[:100]}")
            print()
            print("Canonical format:")
            print("    # <KIND>: <reason>  WT-<N> exp:<YYYY-MM-DD>")
            print()
            print("Bulk legacy migration:")
            print("    Append `  WT-LEGACY exp:2026-09-01` to each existing")
            print("    suppressor, then triage WT-LEGACY individually.")

    if args.warn_only:
        return 0
    if args.blocking:
        return 1 if all_v else 0
    if args.max_violations is None:
        return 0
    return 1 if len(all_v) > args.max_violations else 0


if __name__ == "__main__":
    sys.exit(main())
