#!/usr/bin/env python3
"""Sensor: SQL must not use the `:cid = '' OR company_id = :cid` escape pattern.

Multi-tenancy invariant (CLAUDE.md REGRA 1):
====================================================================
Some legacy SQL had a "tenant escape" idiom:

    WHERE (:cid = '' OR company_id = :cid)

The intent was to allow cross-tenant queries when the binding was empty.
Effect: when `company_id == ""` (which can happen if a handler bypasses
the decorator gate or a service forgets to populate context), the WHERE
clause matches ALL tenants — silent cross-tenant data leak.

After Sprint 1B (`tool_handler` ContextVar injection), `company_id` is
always populated by the auth middleware before any handler runs. The
escape clause is dead code AND a security footgun.

This sensor flags any occurrence in `app/` and asks for canonical:

    WHERE company_id = :cid          # standalone
    WHERE id = :x AND company_id = :cid   # with other conditions

Mode:
  - --block (default — Sprint 1C should leave the codebase clean)
  - warn-only when running without --block

Allowlist:
  - tests/, scripts/, alembic/, migrations/
  - Files with `# SENSOR-EXEMPT: CID-EMPTY-ESCAPE-OK <reason>` marker
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Patterns: catch the canonical anti-pattern + minor variations
PATTERNS = (
    re.compile(r":cid\s*=\s*'\s*'\s*OR\s+company_id\s*=\s*:cid", re.IGNORECASE),
    re.compile(r":company_id\s*=\s*'\s*'\s*OR\s+company_id", re.IGNORECASE),
)

ALLOWED_PREFIXES = (
    "tests/",
    "app/tests/",
    "scripts/",
    "alembic/",
    "migrations/",
    "docs/",
)

EXEMPT_MARKER = "SENSOR-EXEMPT: CID-EMPTY-ESCAPE-OK"


def is_allowlisted(path: Path) -> bool:
    rel = str(path.relative_to(ROOT))
    return any(rel.startswith(p) for p in ALLOWED_PREFIXES)


def has_exempt_marker(src: str) -> bool:
    return EXEMPT_MARKER in src


def scan_file(path: Path) -> list[tuple[int, str]]:
    findings: list[tuple[int, str]] = []
    try:
        src = path.read_text(encoding="utf-8")
    except Exception:
        return findings

    if has_exempt_marker(src):
        return findings

    for lineno, line in enumerate(src.splitlines(), start=1):
        for pat in PATTERNS:
            if pat.search(line):
                findings.append((lineno, line.strip()[:140]))
                break
    return findings


def main() -> int:
    block = "--block" in sys.argv or "--block" not in sys.argv  # default to --block
    warn = "--warn" in sys.argv

    if warn:
        block = False

    candidates: list[Path] = []
    app_dir = ROOT / "app"
    if app_dir.exists():
        for f in app_dir.rglob("*.py"):
            if not is_allowlisted(f) and "__pycache__" not in str(f):
                candidates.append(f)

    candidates = sorted(set(candidates))

    findings_by_file: dict[Path, list[tuple[int, str]]] = {}
    total = 0

    for f in candidates:
        f_findings = scan_file(f)
        if f_findings:
            findings_by_file[f] = f_findings
            total += len(f_findings)

    if total == 0:
        print(
            f"[Multi-tenancy sensor] OK — scanned {len(candidates)} python files, "
            "0 occurrences of `:cid = '' OR company_id = :cid` escape pattern."
        )
        return 0

    for f, hits in findings_by_file.items():
        rel = f.relative_to(ROOT)
        for ln, snippet in hits:
            print(f"[Multi-tenancy sensor] {rel}:{ln}: {snippet}")

    print(
        f"\n[Multi-tenancy sensor] Summary: {total} occurrences across "
        f"{len(findings_by_file)} files.\n"
        "The pattern `:cid = '' OR company_id = :cid` allows cross-tenant matches "
        "when company_id is empty — silent data leak surface (CLAUDE.md REGRA 1).\n\n"
        "Canonical fix:\n"
        "  - WHERE (:cid = '' OR company_id = :cid)  →  WHERE company_id = :cid\n"
        "  - AND (:cid = '' OR company_id = :cid)    →  AND company_id = :cid\n\n"
        "Tenant context is guaranteed populated post-Sprint 1B (tool_handler\n"
        "ContextVar injection). The escape clause is dead code AND a security footgun.\n",
        file=sys.stderr,
    )

    if block:
        return 1
    print("[Multi-tenancy sensor] WARN-ONLY mode — not blocking.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
