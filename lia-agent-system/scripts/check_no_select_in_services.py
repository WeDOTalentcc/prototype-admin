#!/usr/bin/env python3
"""Sensor: services/ AND agents/*_tool_registry.py MUST NOT use `select(Model)` directly (ADR-001).

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

Scan scope (W1-004-B extension 2026-05-23):
  - app/domains/*/services/*.py  (original ADR-001 scope)
  - app/domains/*/agents/*_tool_registry.py  (NEW — W1-004-B)
  - app/services/<agent_layer_files>.py  (Wave 2 2026-05-21, warn-only)

Mode:
  - blocking (default since Sprint 8 — services/ and migrated tool_registries)
  - warn-only for pre-existing tool_registry backlog (W1-004-C future wave)
  - --warn-only flag: opt-out to warn-only for all

Allowlist:
  - tests/, scripts/, alembic/, migrations/
  - Files marked `# ADR-001-EXEMPT: <reason>`
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SERVICES_DIR = ROOT / "app" / "domains"

# Pattern: `select(SomeCapitalizedClass)` — heuristic for ORM model select
SELECT_MODEL_PATTERN = re.compile(r"\bselect\s*\(\s*([A-Z][A-Za-z0-9_]*)\s*[,)]")

# Excluded class names — common false positives that aren't models
EXCLUDED_NAMES = frozenset({
    "True", "False", "None", "Path", "UUID", "Decimal", "datetime",
    "func", "case", "literal", "and_", "or_", "not_",
})

EXEMPT_MARKER = "ADR-001-EXEMPT"

# W1-004-B: 3 migrated tool_registries that are BLOCKING (must have 0 select(Model) calls).
MIGRATED_TOOL_REGISTRIES = frozenset({
    "app/domains/recruiter_assistant/agents/kanban_tool_registry.py",
    "app/domains/recruiter_assistant/agents/jobs_mgmt_tool_registry.py",
    "app/domains/recruiter_assistant/agents/talent_tool_registry.py",
})

# W1-004-C backlog: pre-existing select(Model) violations in tool_registries.
# Warn-only until migrated in future waves.
# W1-004-C Agent-B (2026-05-23): hiring_policy/policy_tool_registry + job_management/wizard_tool_registry
# removed — MIGRATE 1 (_load_vacancy_or_error → JobVacancyCrudRepository.get_by_id_strict_company)
# + no select(Model) violations remain in policy_tool_registry.
TOOL_REGISTRY_BACKLOG = frozenset({
    # company_tool_registry.py — removed 2026-05-23 W1-004-D: no select(Model) violations found; text() migrated/EXEMPT
    # cv_screening/pipeline_tool_registry.py — removed 2026-05-23 Wave C-3 Agent G: no select(Model) violations found; text() EXEMPT-marked
    # policy_tool_registry.py — removed 2026-05-23: no select(Model) violations; text() migrated/EXEMPT
    # wizard_tool_registry.py — removed 2026-05-23: MIGRATE 1 to JobVacancyCrudRepository.get_by_id_strict_company
    # pipeline_tool_registry.py — removed 2026-05-23 Wave C-2 Agent F: 8 SQL blocks migrated to repos + 4 EXEMPT markers; 0 select(Model) violations found
    # diversity_tool_registry.py — removed 2026-05-23: no select() violations; was pre-emptive
    # passive_pipeline_tool_registry.py — removed 2026-05-23 W1-004-D: no select(Model) violations found; text() 1 MIGRATE + 2 EXEMPT
    # sourcing_tool_registry.py — removed 2026-05-23: no select() violations; was pre-emptive
    # talent_pool_tool_registry.py — removed W1-004-E: 6 select(TalentPool*) MIGRATED to TalentPoolRepository + TalentPoolCandidateRepository (0 inline remaining)
    # backlog zerado em 2026-05-23 (Wave C-3 Agent G)
})

# === Wave 2 audit 2026-05-21: extend coverage para agent layer em app/services/ ===
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


def is_tool_registry_file(path: Path) -> bool:
    """`app/domains/*/agents/*_tool_registry.py` — W1-004-B scope extension."""
    try:
        rel = path.relative_to(ROOT)
    except ValueError:
        return False
    parts = rel.parts
    return (
        len(parts) >= 5
        and parts[0] == "app"
        and parts[1] == "domains"
        and parts[3] == "agents"
        and parts[-1].endswith("_tool_registry.py")
    )


def is_agent_layer_service(path: Path) -> bool:
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


def get_relative_key(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


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
    warn_only = "--warn-only" in sys.argv
    block = not warn_only

    if not SERVICES_DIR.exists():
        print(f"[ADR-001 select sensor] WARN: {SERVICES_DIR} does not exist")
        return 0

    # === Collect all files in scan scope ===
    service_files = sorted(p for p in SERVICES_DIR.rglob("*.py") if is_service_file(p))
    tool_registry_files = sorted(p for p in SERVICES_DIR.rglob("*.py") if is_tool_registry_file(p))

    agent_layer_dir = ROOT / "app" / "services"
    agent_layer_files: list[Path] = []
    if agent_layer_dir.exists():
        agent_layer_files = sorted(
            p for p in agent_layer_dir.rglob("*.py") if is_agent_layer_service(p)
        )

    all_candidates = service_files + tool_registry_files + agent_layer_files
    agent_layer_set = set(agent_layer_files)

    print(
        f"[ADR-001 select sensor] Scanning {len(service_files)} service files + "
        f"{len(tool_registry_files)} tool_registry files + "
        f"{len(agent_layer_files)} agent-layer service files"
    )

    # === Scan and categorize ===
    blocking_violations: dict[Path, list[tuple[int, str, str]]] = {}
    backlog_violations: dict[Path, list[tuple[int, str, str]]] = {}
    agent_layer_violations: dict[Path, list[tuple[int, str, str]]] = {}

    for f in all_candidates:
        f_findings = scan_file(f)
        if not f_findings:
            continue
        rel_key = get_relative_key(f)
        if f in agent_layer_set:
            agent_layer_violations[f] = f_findings
        elif rel_key in TOOL_REGISTRY_BACKLOG:
            backlog_violations[f] = f_findings
        else:
            blocking_violations[f] = f_findings

    blocking_count = sum(len(v) for v in blocking_violations.values())
    backlog_count = sum(len(v) for v in backlog_violations.values())
    agent_layer_count = sum(len(v) for v in agent_layer_violations.values())

    # === Print backlog summary (warn-only) ===
    if backlog_violations:
        print(
            f"\n[ADR-001 select sensor] WARN (backlog W1-004-C): "
            f"{backlog_count} select(Model) violations in {len(backlog_violations)} tool_registry files "
            f"(warn-only until migrated):"
        )
        for f, hits in sorted(backlog_violations.items(), key=lambda x: str(x[0])):
            rel = get_relative_key(f)
            print(f"  {rel}: {len(hits)} select(Model) calls")

    # === Print agent layer summary (warn-only) ===
    if agent_layer_violations:
        print(
            f"\n[ADR-001 select sensor] WARN (Wave 3): "
            f"{agent_layer_count} violations in app/services/ agent layer (warn-only):"
        )
        for f, hits in agent_layer_violations.items():
            rel = get_relative_key(f)
            for ln, model, snippet in hits[:3]:
                print(f"  {rel}:{ln}: select({model}, ...)")

    # === Handle blocking violations ===
    if blocking_count == 0:
        scanned_total = len(all_candidates)
        print(
            f"\n[ADR-001 select sensor] OK — 0 blocking violations across services + migrated tool_registries "
            f"({scanned_total} files scanned total)."
        )
        return 0

    # Print blocking violations
    for f, hits in sorted(blocking_violations.items(), key=lambda x: str(x[0])):
        rel = get_relative_key(f)
        for ln, model, snippet in hits[:5]:
            print(f"[ADR-001 select] {rel}:{ln}: select({model}, ...)")
        if len(hits) > 5:
            print(f"[ADR-001 select] {rel}: ... (+{len(hits) - 5} more)")

    print(
        f"\n[ADR-001 select sensor] Summary: {blocking_count} `select(Model)` hits across "
        f"{len(blocking_violations)} files.\n"
        "Per ADR-001: ORM queries go to repositories. Move `select(Model)` calls\n"
        "into the corresponding domain's repositories/ layer.\n\n"
        "For tool_registry files: either migrate (W1-004-C) or add to TOOL_REGISTRY_BACKLOG.\n"
        "Add `# ADR-001-EXEMPT: <reason>` for legitimate exceptions.\n",
        file=sys.stderr,
    )

    if block:
        print("[ADR-001 select sensor] BLOCKING mode — failing build.")
        return 1
    print("[ADR-001 select sensor] WARN-ONLY mode (--warn-only flag).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
