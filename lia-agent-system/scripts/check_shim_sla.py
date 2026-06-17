#!/usr/bin/env python3
"""
S7.1 — Shim SLA check.

A "shim" here is a backwards-compatibility proxy file that simply re-exports
symbols from a canonical location (typically `lia_models.*` or
`lia_messaging.*`). Examples are the proxy files documented in ADR-002.

Rule: if a shim has zero importers anywhere in the repo AND has been on disk
for 90 or more days, it is eligible for automated deletion. The script lists
such files and exits non-zero so CI/pre-commit fails until they are removed
(or the SLA window resets by re-importing them).

Heuristics:
- A shim is any *.py file under `app/` whose body (excluding comments and
  blank lines) is dominated by `from lia_models...` / `from lia_messaging...`
  re-exports, or that contains the text "compatibility shim".
- Importer search uses simple regex over the repo's Python sources.
- Age is determined from `git log --diff-filter=A --follow --format=%aI`,
  with the file's mtime as a fallback when git history is unavailable
  (e.g. shallow CI checkouts of a brand-new file).

Usage:
  python scripts/check_shim_sla.py
  python scripts/check_shim_sla.py --max-age-days 90  # default
  python scripts/check_shim_sla.py --json             # machine-readable

Exit codes:
  0 — no expired orphan shims
  1 — at least one shim is past SLA with 0 importers
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
APP_ROOT = ROOT / "app"
LIBS_ROOT = ROOT / "libs"

SHIM_MARKER_RE = re.compile(
    r"compatibility shim|backwards-compatibility|^\s*from\s+lia_(models|messaging)\b.*import\s+\*",
    re.IGNORECASE | re.MULTILINE,
)
REEXPORT_RE = re.compile(
    r"^\s*from\s+lia_(models|messaging)[\w.]*\s+import\s+",
    re.MULTILINE,
)
CODE_LINE_RE = re.compile(r"^\s*[^#\s]")


@dataclass
class ShimReport:
    path: str
    module: str
    age_days: int
    importer_count: int
    importers: list[str]
    eligible_for_deletion: bool


def is_shim(path: Path) -> bool:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return False
    if not SHIM_MARKER_RE.search(text) and not REEXPORT_RE.search(text):
        return False
    code_lines = [ln for ln in text.splitlines() if CODE_LINE_RE.match(ln)]
    if not code_lines:
        return False
    reexport_lines = sum(
        1 for ln in code_lines
        if re.match(r"\s*from\s+lia_(models|messaging)\b", ln)
        or re.match(r"\s*import\s+lia_(models|messaging)\b", ln)
    )
    # Dominated by re-exports (>=50%) and small file (<= 30 code lines).
    return reexport_lines >= 1 and len(code_lines) <= 30 and reexport_lines / len(code_lines) >= 0.5


def file_age_days(path: Path) -> int:
    try:
        out = subprocess.run(
            ["git", "log", "--diff-filter=A", "--follow", "--format=%aI", "--", str(path)],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
        first_line = (out.stdout or "").strip().splitlines()
        if first_line:
            created = datetime.fromisoformat(first_line[-1])
            delta = datetime.now(timezone.utc) - created.astimezone(timezone.utc)
            return max(0, delta.days)
    except (subprocess.SubprocessError, ValueError, FileNotFoundError):
        pass
    try:
        mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
        return max(0, (datetime.now(timezone.utc) - mtime).days)
    except OSError:
        return 0


def module_for(path: Path) -> str:
    rel = path.relative_to(ROOT).with_suffix("")
    parts = rel.parts
    if parts and parts[0] == "libs":
        # libs/models/lia_models/foo/bar.py -> lia_models.foo.bar
        try:
            idx = parts.index("lia_models")
        except ValueError:
            try:
                idx = parts.index("lia_messaging")
            except ValueError:
                idx = 0
        parts = parts[idx:]
    return ".".join(parts)


def find_importers(module: str, exclude: Path) -> list[str]:
    if not module:
        return []
    pattern = re.compile(
        rf"^\s*(?:from\s+{re.escape(module)}(?:\s|\.)|import\s+{re.escape(module)}(?:\s|$|\.|,))",
        re.MULTILINE,
    )
    importers: list[str] = []
    for py in ROOT.rglob("*.py"):
        if py == exclude:
            continue
        if any(part in {".venv", "venv", "__pycache__", ".git", "node_modules"} for part in py.parts):
            continue
        try:
            text = py.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        if pattern.search(text):
            importers.append(str(py.relative_to(ROOT)))
    return importers


def collect_shims() -> list[Path]:
    candidates: list[Path] = []
    for root in (APP_ROOT, LIBS_ROOT):
        if not root.exists():
            continue
        for py in root.rglob("*.py"):
            if py.name == "__init__.py":
                continue
            if any(part in {"__pycache__", "tests", "test"} for part in py.parts):
                continue
            if is_shim(py):
                candidates.append(py)
    return candidates


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--max-age-days", type=int, default=90)
    parser.add_argument("--json", action="store_true", help="emit a JSON report")
    args = parser.parse_args()

    shims = collect_shims()
    reports: list[ShimReport] = []
    for shim in shims:
        module = module_for(shim)
        importers = find_importers(module, exclude=shim)
        age = file_age_days(shim)
        eligible = (len(importers) == 0) and (age >= args.max_age_days)
        reports.append(ShimReport(
            path=str(shim.relative_to(ROOT)),
            module=module,
            age_days=age,
            importer_count=len(importers),
            importers=importers[:5],
            eligible_for_deletion=eligible,
        ))

    expired = [r for r in reports if r.eligible_for_deletion]

    if args.json:
        print(json.dumps({
            "max_age_days": args.max_age_days,
            "total_shims": len(reports),
            "expired": len(expired),
            "reports": [asdict(r) for r in reports],
        }, indent=2))
    else:
        print(f"[shim-sla] scanned {len(reports)} shim file(s); SLA = {args.max_age_days} days")
        if expired:
            print(f"[shim-sla] {len(expired)} shim(s) past SLA with 0 importers — eligible for deletion:")
            for r in expired:
                print(f"  - {r.path}  (module={r.module}, age={r.age_days}d)")
                print(f"      suggested:  git rm {r.path}")
        else:
            print("[shim-sla] no expired orphan shims")

    return 1 if expired else 0


if __name__ == "__main__":
    sys.exit(main())
