#!/usr/bin/env python3
"""Sensor: services/ MUST NOT use `select(Model)` directly (ADR-001).

ADR-001 — Repository Pattern (canonized 2026-05-06)
====================================================================

Services should NOT import `select` from sqlalchemy and call it on
domain Model classes. SQLAlchemy 2.x ORM queries belong in
`repositories/`. Same rationale as raw SQL — single tenancy chokepoint,
mocking, portability.

Pattern detected:
- `select(SomeModel)` where SomeModel is a CapitalizedClassName (heuristic)
- imports of `from sqlalchemy import select` in services/

Allowed in services:
- `select(*)` raw star (no model — could be subquery, column list)
- `select(some_subquery)` lowercase variable (typically a CTE/aliased)

Mode:
  - warn (default — Sprint 5.1 baseline; ~494 pre-existing hits across
    services. Caminho C policy applies)
  - --block after Sprint 5.4 backfill

Allowlist:
  - tests/, scripts/, alembic/, migrations/
  - Files marked `# ADR-001-EXEMPT: <reason>`
  - `app/domains/*/services/*.py` only
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SERVICES_DIR = ROOT / "app" / "domains"

# Pattern: `select(SomeCapitalizedClass)` — heuristic for ORM model select
# Allows: `select(*)`, `select(some_subq)`, `select(func.count())`
SELECT_MODEL_PATTERN = re.compile(r"\bselect\s*\(\s*([A-Z][A-Za-z0-9_]*)\s*[,)]")

# Excluded class names — common false positives that aren't models
EXCLUDED_NAMES = frozenset({
    "True", "False", "None", "Path", "UUID", "Decimal", "datetime",
    "func", "case", "literal", "and_", "or_", "not_",
})

EXEMPT_MARKER = "ADR-001-EXEMPT"


def is_service_file(path: Path) -> bool:
    try:
        rel = path.relative_to(ROOT)
    except ValueError:
        return False
    parts = rel.parts
    return (
        len(parts) >= 4
        and parts[0] == "app"
        and parts[1] == "domains"
        and parts[3] == "services"
        and parts[-1].endswith(".py")
    )


# === Wave 2 audit 2026-05-21: extend coverage para agent layer em app/services/ ===
# Estes arquivos historicamente escaparam dos sensores ADR-001 porque vivem fora
# de app/domains/*/services/. Audit Agent B encontrou ~40+ violations entre eles.
# Wave 3 vai refatorar via repos canonical.
AGENT_LAYER_SERVICE_FILES = frozenset({
    "agent_marketplace_service.py",
    "sourcing_agent_orchestrator.py",
    "twin_inference_service.py",
    "twin_knowledge_indexer.py",
    "agent_approval_service.py",
    "agent_version_service.py",
    "multi_strategy_search.py",
    "agent_deployment_service.py",
    "agent_quality_evaluator.py",
    "agent_quality_gate.py",
})


def is_agent_layer_service(path):
    """Detect app/services/<agent_layer>.py files (audit Wave 2 2026-05-21 extension)."""
    try:
        rel = path.relative_to(ROOT)
    except ValueError:
        return False
    parts = rel.parts
    return (
        len(parts) == 3
        and parts[0] == "app"
        and parts[1] == "services"
        and parts[2] in AGENT_LAYER_SERVICE_FILES
    )


def has_exempt_marker(src: str) -> bool:
    return EXEMPT_MARKER in src


def scan_file(path: Path) -> list[tuple[int, str, str]]:
    findings: list[tuple[int, str, str]] = []
    try:
        src = path.read_text(encoding="utf-8")
    except Exception:
        return findings

    if has_exempt_marker(src):
        return findings

    for lineno, line in enumerate(src.splitlines(), start=1):
        for m in SELECT_MODEL_PATTERN.finditer(line):
            class_name = m.group(1)
            if class_name in EXCLUDED_NAMES:
                continue
            findings.append((lineno, class_name, line.strip()[:120]))
    return findings


def main() -> int:
    # Sprint 8 batch 2 (2026-05-07): promoted to blocking by default after
    # sensor reached 0 violations via 8 parallel-agent dispatches across all
    # service domains. Use --warn-only to opt out for legacy ratchet.
    warn_only = "--warn-only" in sys.argv
    block = not warn_only

    if not SERVICES_DIR.exists():
        print(f"[ADR-001 select sensor] WARN: {SERVICES_DIR} does not exist")
        return 0

    candidates = sorted(p for p in SERVICES_DIR.rglob("*.py") if is_service_file(p))
    # Wave 2 2026-05-21 extension: agent layer em app/services/.
    # Findings em agent_layer sao warn-only ate Wave 3 refatorar via repos canonical.
    agent_layer_dir = ROOT / "app" / "services"
    agent_files = []
    if agent_layer_dir.exists():
        agent_files = sorted(
            p for p in agent_layer_dir.rglob("*.py") if is_agent_layer_service(p)
        )
    candidates = candidates + agent_files
    agent_files_set = set(agent_files)
    findings_by_file: dict[Path, list[tuple[int, str, str]]] = {}
    total = 0
    blocking_total = 0  # Wave 2 extension: agent_layer findings = warn-only
    for f in candidates:
        f_findings = scan_file(f)
        if f_findings:
            findings_by_file[f] = f_findings
            total += len(f_findings)
            if f not in agent_files_set:
                blocking_total += len(f_findings)

    if blocking_total == 0:
        if total > 0:
            # Agent layer findings present but warn-only
            agent_findings_count = total - blocking_total
            print(
                f"[ADR-001 select sensor] WARN: {agent_findings_count} findings in "
                f"app/services/ agent layer (warn-only, Wave 3 closes via repos):"
            )
            for f, hits in findings_by_file.items():
                if f in agent_files_set:
                    for ln, model, snippet in hits[:3]:
                        try:
                            rel = f.relative_to(ROOT)
                        except ValueError:
                            rel = f
                        print(f"  {rel}:{ln}: select({model}, ...)")
        else:
            print(
                f"[ADR-001 select sensor] OK — scanned {len(candidates)} service files, "
                "0 direct `select(Model)` hits."
            )
        return 0

    # Limit per-file output to top 5 findings to keep stderr manageable
    for f, hits in findings_by_file.items():
        rel = f.relative_to(ROOT)
        for ln, model, snippet in hits[:5]:
            print(f"[ADR-001 select] {rel}:{ln}: select({model}, ...)")
        if len(hits) > 5:
            print(f"[ADR-001 select] {rel}: ... (+{len(hits) - 5} more in same file)")

    print(
        f"\n[ADR-001 select sensor] Summary: {total} `select(Model)` hits across "
        f"{len(findings_by_file)} service files (of {len(candidates)} scanned).\n"
        "Per ADR-001: ORM queries go to repositories. Move `select(Model)` calls\n"
        "into the corresponding domain's repositories/ layer.\n\n"
        "Caminho C policy: legacy hits stay warn-only; new code must be clean.\n"
        "Add `# ADR-001-EXEMPT: <reason>` comment for legitimate exceptions.\n",
        file=sys.stderr,
    )

    if block:
        print("[ADR-001 select sensor] BLOCKING mode (default since Sprint 8) — failing build.")
        return 1
    print("[ADR-001 select sensor] WARN-ONLY mode (opt-out via --warn-only flag).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
