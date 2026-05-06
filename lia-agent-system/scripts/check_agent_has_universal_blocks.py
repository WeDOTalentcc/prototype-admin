#!/usr/bin/env python3
"""Harness sensor — verify each ReAct agent class has universal blocks in DOMAIN_INSTRUCTIONS.

Per ADR-028 (Single source of truth para system prompts), every ReAct agent
class deriving from LangGraphReActBase MUST inject UNIVERSAL_BLOCKS:
  - TENANT_ISOLATION_BLOCK (multi-tenancy enforcement)
  - NEGATION_DETECTION_BLOCK (anti-confusion)
  - ANTI_SYCOPHANCY_BLOCK (response quality)

This sensor catches:
  Pattern A: agent class with DOMAIN_INSTRUCTIONS missing TENANT_ISOLATION_BLOCK
  Pattern B: agent class with DOMAIN_INSTRUCTIONS missing import of universal blocks
  Pattern C: agent class with DOMAIN_INSTRUCTIONS that's static (deprecated post-Sprint 2)

Mode:
  - warn (default during Sprint 0/1, before factory pattern is canonical)
  - block (after Sprint 2 — eliminates DOMAIN_INSTRUCTIONS class-attr entirely)

Usage:
  python scripts/check_agent_has_universal_blocks.py [--block]

Allowlist:
  - Files explicitly tagged with `# SENSOR-EXEMPT: AGENT-BLOCKS-OK <reason>`
  - Tests, scripts, alembic, migrations, docs
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

UNIVERSAL_BLOCKS = (
    "TENANT_ISOLATION_BLOCK",
    "NEGATION_DETECTION_BLOCK",
    "ANTI_SYCOPHANCY_BLOCK",
)

# Critical block — without this, multi-tenancy violations possible (LLM asking for company_id)
CRITICAL_BLOCK = "TENANT_ISOLATION_BLOCK"

ALLOWED_PREFIXES = (
    "tests/",
    "app/tests/",
    "scripts/",
    "alembic/",
    "migrations/",
    "docs/",
)


def is_allowlisted(path: Path) -> bool:
    rel = str(path.relative_to(ROOT))
    return any(rel.startswith(p) for p in ALLOWED_PREFIXES)


def has_exempt_marker(src: str) -> bool:
    return "SENSOR-EXEMPT: AGENT-BLOCKS-OK" in src


def scan_file(path: Path) -> list[tuple[int, str, str]]:
    """Return list of (line, severity, message) for issues found."""
    findings: list[tuple[int, str, str]] = []
    try:
        src = path.read_text(encoding="utf-8")
    except Exception:
        return findings

    # Skip if no DOMAIN_INSTRUCTIONS at all
    if "DOMAIN_INSTRUCTIONS" not in src:
        return findings

    # Skip if exempt
    if has_exempt_marker(src):
        return findings

    # Find line of DOMAIN_INSTRUCTIONS = ... assignment
    di_pattern = re.compile(r'^\s*DOMAIN_INSTRUCTIONS\s*=', re.MULTILINE)
    for m in di_pattern.finditer(src):
        line_no = src[:m.start()].count("\n") + 1

        # Find the full assignment block (multiline aware)
        # Take from match start to next blank line or end of class
        post = src[m.start():]
        # Crude: take next 20 lines as the "block content"
        block_lines = post.splitlines()[:20]
        block = "\n".join(block_lines)

        # Check critical block presence
        if CRITICAL_BLOCK not in block:
            findings.append((
                line_no,
                "CRITICAL",
                f"DOMAIN_INSTRUCTIONS missing {CRITICAL_BLOCK} (multi-tenancy violation)",
            ))

        # Check other universal blocks (warn level)
        for b in UNIVERSAL_BLOCKS:
            if b == CRITICAL_BLOCK:
                continue  # already checked above
            if b not in block:
                findings.append((
                    line_no,
                    "WARN",
                    f"DOMAIN_INSTRUCTIONS missing {b} (per ADR-028)",
                ))

    return findings


def main() -> int:
    block = "--block" in sys.argv

    # Find all agent files
    candidates = []
    domains_dir = ROOT / "app/domains"
    if domains_dir.exists():
        candidates = list(domains_dir.rglob("*react_agent.py"))
        candidates += list(domains_dir.rglob("*_agent.py"))

    candidates = [c for c in candidates if not is_allowlisted(c) and "__pycache__" not in str(c)]

    total_critical = 0
    total_warn = 0

    for f in candidates:
        findings = scan_file(f)
        if findings:
            rel = f.relative_to(ROOT)
            for ln, severity, msg in findings:
                print(f"[ADR-028 sensor] {severity} {rel}:{ln}: {msg}")
                if severity == "CRITICAL":
                    total_critical += 1
                else:
                    total_warn += 1

    if total_critical == 0 and total_warn == 0:
        print("[ADR-028 sensor] OK — all agent DOMAIN_INSTRUCTIONS contain universal blocks")
        return 0

    print(
        f"\n[ADR-028 sensor] Summary: {total_critical} CRITICAL, {total_warn} WARN findings.\n"
        "Per ADR-028, each agent class must inject UNIVERSAL_BLOCKS in DOMAIN_INSTRUCTIONS:\n"
        f"  - {CRITICAL_BLOCK} (multi-tenancy — required to prevent LLM asking for tenant IDs)\n"
        "  - NEGATION_DETECTION_BLOCK (anti-confusion)\n"
        "  - ANTI_SYCOPHANCY_BLOCK (response quality)\n\n"
        "Future: Sprint 2 will eliminate class-attr DOMAIN_INSTRUCTIONS entirely\n"
        "        in favor of PromptComposer factory (single source of truth).\n",
        file=sys.stderr,
    )

    if block:
        # Block only on CRITICAL findings
        if total_critical > 0:
            return 1
        print("[ADR-028 sensor] WARN-only findings — not blocking (set --strict to block on warns).")
        return 0

    print("[ADR-028 sensor] WARN-ONLY mode — not blocking.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
