#!/usr/bin/env python3
"""Sensor: react_agents should assemble DOMAIN_INSTRUCTIONS via PromptComposer.

ADR-028 Sprint 2 Phase 1
====================================================================

After Sprint 2 fully migrates, every `*_react_agent.py` should compose
its DOMAIN_INSTRUCTIONS via `app.shared.prompts.prompt_composer.PromptComposer`,
NOT via hand-rolled string concatenation of `*_DOMAIN_SPECIFIC + ... +
*_REASONING_PROMPT`.

This sensor surfaces adoption rate during the rolling migration:
- agents that import `PromptComposer` → ADOPTED ✅
- agents with `DOMAIN_INSTRUCTIONS = X + Y + Z` (string concat) → LEGACY ⚠️

Mode: warn-only (Sprint 2 Phase 1 baseline; ~1/15 agents adopted).
Promote to --block after Sprint 2 Phase 2 completes (16+/16 adoption).

Allowlist:
  - tests/, scripts/, alembic/, docs/
  - Files marked `# PROMPT-COMPOSER-EXEMPT: <reason>` (rare exceptions)
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

EXEMPT_MARKER = "PROMPT-COMPOSER-EXEMPT"
COMPOSER_IMPORT_PATTERN = re.compile(
    r"from app\.shared\.prompts\.prompt_composer\s+import\s+PromptComposer"
)
DOMAIN_INSTRUCTIONS_PATTERN = re.compile(
    r"DOMAIN_INSTRUCTIONS\s*="
)


def find_react_agents() -> list[Path]:
    return sorted(
        (ROOT / "app" / "domains").rglob("*react_agent.py")
    ) if (ROOT / "app" / "domains").exists() else []


def scan_file(path: Path) -> str | None:
    """Return None if adopted, else a 1-line reason string."""
    try:
        src = path.read_text(encoding="utf-8")
    except Exception:
        return None

    if EXEMPT_MARKER in src:
        return None

    if not DOMAIN_INSTRUCTIONS_PATTERN.search(src):
        return None  # no DOMAIN_INSTRUCTIONS at all (skip)

    if COMPOSER_IMPORT_PATTERN.search(src):
        return None  # adopted

    return "DOMAIN_INSTRUCTIONS present but no PromptComposer import"


def main() -> int:
    block = "--block" in sys.argv

    candidates = find_react_agents()
    legacy: list[tuple[Path, str]] = []
    adopted: list[Path] = []
    no_domain: list[Path] = []

    for f in candidates:
        result = scan_file(f)
        if result is None:
            try:
                src = f.read_text(encoding="utf-8")
            except Exception:
                continue
            if COMPOSER_IMPORT_PATTERN.search(src):
                adopted.append(f)
            else:
                no_domain.append(f)
        else:
            legacy.append((f, result))

    print(
        f"[ADR-028 sensor] Inventory: {len(candidates)} react_agents | "
        f"{len(adopted)} ADOPTED PromptComposer | {len(legacy)} LEGACY "
        f"(string concat) | {len(no_domain)} no DOMAIN_INSTRUCTIONS"
    )

    if not legacy:
        print(
            "[ADR-028 sensor] OK — every react_agent uses PromptComposer "
            "(or has no DOMAIN_INSTRUCTIONS)."
        )
        return 0

    for path, reason in legacy:
        rel = path.relative_to(ROOT)
        print(f"[ADR-028 sensor] LEGACY {rel}: {reason}")

    print(
        f"\n[ADR-028 sensor] {len(legacy)} react_agents still use legacy "
        "DOMAIN_INSTRUCTIONS pattern.\n"
        "Migrate via PromptComposer.for_<domain>() factory or generic "
        ".compose() — see app/shared/prompts/prompt_composer.py.\n"
        "Reference migration: candidate_react_agent.py (Sprint 2 Phase 1).\n",
        file=sys.stderr,
    )

    if block:
        return 1
    print("[ADR-028 sensor] WARN-ONLY mode — not blocking.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
