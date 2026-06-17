#!/usr/bin/env python3
"""Sensor: services/ AND agents/*_tool_registry.py MUST NOT contain raw SQL inline (ADR-001).

ADR-001 — Repository Pattern (canonized 2026-05-06)
====================================================================

Services MUST NOT call `db.execute(text(...))`, `session.execute(text(...))`,
`sa_text(...)`, or `sqlalchemy.text(...)` for SQL queries. All SQL belongs in
`repositories/` (a layer below services).

Scan scope (W1-004-C extension 2026-05-23):
  - app/domains/*/services/*.py  (original ADR-001 scope)
  - app/domains/*/agents/*_tool_registry.py  (NEW — W1-004-B)
  - app/services/<agent_layer_files>.py  (Wave 2 2026-05-21, warn-only)

Mode:
  - blocking (default since Sprint 7)
  - SERVICES_SQL_BACKLOG: pre-existing services/ violations — now empty (all resolved in W1-004-C).
  - TOOL_REGISTRY_BACKLOG: pre-existing tool_registry violations (W1-004-C future wave)
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

# Patterns that indicate raw SQL in a service file
PATTERNS = (
    re.compile(r"\bdb\.execute\s*\(\s*(?:sa\.)?text\s*\("),        # db.execute(text("..."))
    re.compile(r"\bsa_text\s*\("),                                  # sa_text("...")
    re.compile(r"\bsqlalchemy\.text\s*\("),                         # sqlalchemy.text("...")
    re.compile(r"\bdb\.execute\s*\(\s*\"\"\""),                     # db.execute("""...""")
    re.compile(r"\bdb\.execute\s*\(\s*'''"),                        # db.execute('''...''')
    re.compile(r"\bsession\.execute\s*\(\s*(?:sa\.)?text\s*\("),    # session.execute(text(...))
)

EXEMPT_MARKER = "ADR-001-EXEMPT"

# W1-004-B: 3 migrated tool_registries — BLOCKING (must stay at 0 violations).
MIGRATED_TOOL_REGISTRIES = frozenset({
    "app/domains/recruiter_assistant/agents/kanban_tool_registry.py",
    "app/domains/recruiter_assistant/agents/jobs_mgmt_tool_registry.py",
    "app/domains/recruiter_assistant/agents/talent_tool_registry.py",
})

# W1-004-C backlog: pre-existing SQL inline in tool_registries.
# Warn-only until migrated in future waves.
# W1-004-A (2026-05-23): diversity_tool_registry + sourcing_tool_registry removed from backlog
# after full EXEMPT marker coverage (ADR-001-EXEMPT on all SQL inline blocks).
# W1-004-C Agent-B (2026-05-23): hiring_policy/policy_tool_registry + job_management/wizard_tool_registry
# removed — MIGRATE 1+2 to repos + EXEMPT markers on remaining analytics SQL.
TOOL_REGISTRY_BACKLOG = frozenset({
    # company_tool_registry.py — removed 2026-05-23 W1-004-D: 3 MIGRATE to CompanyProfileRepository + 1 EXEMPT marker
    # cv_screening/pipeline_tool_registry.py — removed 2026-05-23 Wave C-3 Agent G: 1 EXEMPT marker (generate_report analytics aggregation from applications table)
    # policy_tool_registry.py — removed 2026-05-23: MIGRATE 1+2 to HiringPolicyRepository + EXEMPT markers
    # wizard_tool_registry.py — removed 2026-05-23: MIGRATE 1 to JobVacancyCrudRepository + EXEMPT markers
    # pipeline_tool_registry.py — removed 2026-05-23 Wave C-2 Agent F: 8 MIGRATE to 4 repos (CandidatePipelineRepository, LiaOpinionRepository, StageRepository, RecruiterPreferencesRepository) + 4 EXEMPT markers
    # passive_pipeline_tool_registry.py — removed 2026-05-23 W1-004-D: 1 MIGRATE to PassiveCandidateRepository + 2 EXEMPT markers
    # talent_pool_tool_registry.py — removed W1-004-E: 6 MIGRATE to TalentPoolRepository + TalentPoolCandidateRepository + 1 EXEMPT marker (move_candidates_to_vacancy)
    # backlog zerado em 2026-05-23 (Wave C-3 Agent G)
})

# Services/ violations resolved in W1-004-C (2026-05-23):
# All 6 files either migrated to repos or EXEMPT-marked. Backlog is now empty.
# Files with EXEMPT markers: search_service.py, wsi_voice_orchestrator.py,
# autonomous_agent_service.py, outcome_learning_service.py,
# stakeholder_notification_service.py, monitoring_loop.py.
# Files with real migrations: autonomous_actions_engine.py (2 hits), +partial in others.
SERVICES_SQL_BACKLOG = frozenset()  # W1-004-C: all cleared via EXEMPT or repo migration

# Wave 2 audit 2026-05-21: agent layer in app/services/ (warn-only)
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
    """`app/domains/*/services/*.py` only."""
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
    """Detect app/services/<agent_layer>.py files (audit Wave 2 2026-05-21)."""
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
                findings.append((lineno, line.strip()[:120]))
                break
    return findings


def main() -> int:
    warn_only = "--warn-only" in sys.argv
    block = not warn_only

    if not SERVICES_DIR.exists():
        print(f"[ADR-001 SQL sensor] WARN: {SERVICES_DIR} does not exist")
        return 0

    # Collect all files in scan scope
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
        f"[ADR-001 SQL sensor] Scanning {len(service_files)} service files + "
        f"{len(tool_registry_files)} tool_registry files + "
        f"{len(agent_layer_files)} agent-layer service files"
    )

    # Scan and categorize violations
    blocking_violations: dict[Path, list[tuple[int, str]]] = {}
    backlog_tool_violations: dict[Path, list[tuple[int, str]]] = {}
    backlog_service_violations: dict[Path, list[tuple[int, str]]] = {}
    agent_layer_violations: dict[Path, list[tuple[int, str]]] = {}

    for f in all_candidates:
        f_findings = scan_file(f)
        if not f_findings:
            continue
        rel_key = get_relative_key(f)
        if f in agent_layer_set:
            agent_layer_violations[f] = f_findings
        elif rel_key in TOOL_REGISTRY_BACKLOG:
            backlog_tool_violations[f] = f_findings
        elif rel_key in SERVICES_SQL_BACKLOG:
            backlog_service_violations[f] = f_findings
        else:
            blocking_violations[f] = f_findings

    blocking_count = sum(len(v) for v in blocking_violations.values())
    backlog_tool_count = sum(len(v) for v in backlog_tool_violations.values())
    backlog_svc_count = sum(len(v) for v in backlog_service_violations.values())
    agent_layer_count = sum(len(v) for v in agent_layer_violations.values())

    # Print backlog summaries (warn-only)
    if backlog_tool_violations:
        print(
            f"\n[ADR-001 SQL sensor] WARN (backlog W1-004-C): "
            f"{backlog_tool_count} violations in {len(backlog_tool_violations)} tool_registry files "
            f"(warn-only until migrated):"
        )
        for f, hits in sorted(backlog_tool_violations.items(), key=lambda x: str(x[0])):
            rel = get_relative_key(f)
            print(f"  {rel}: {len(hits)} SQL inline blocks")

    if backlog_service_violations:
        total_svc = sum(len(v) for v in backlog_service_violations.values())
        print(
            f"\n[ADR-001 SQL sensor] WARN (services backlog, session.execute pattern): "
            f"{total_svc} violations in {len(backlog_service_violations)} service files "
            f"(pre-existing, warn-only):"
        )
        for f, hits in sorted(backlog_service_violations.items(), key=lambda x: str(x[0])):
            rel = get_relative_key(f)
            print(f"  {rel}: {len(hits)} SQL inline blocks")

    if agent_layer_violations:
        print(
            f"\n[ADR-001 SQL sensor] WARN (Wave 3 app/services/): "
            f"{agent_layer_count} violations (warn-only):"
        )
        for f, hits in agent_layer_violations.items():
            rel = get_relative_key(f)
            for ln, txt in hits[:2]:
                print(f"  {rel}:{ln}: {txt}")

    # Handle blocking violations
    if blocking_count == 0:
        scanned_total = len(all_candidates)
        print(
            f"\n[ADR-001 SQL sensor] OK — 0 blocking violations across services + tool_registries "
            f"({scanned_total} files scanned total)."
        )
        return 0

    print(f"\n[ADR-001 SQL sensor] BLOCKING VIOLATIONS ({blocking_count} hits):", file=sys.stderr)
    for f, hits in sorted(blocking_violations.items(), key=lambda x: str(x[0])):
        rel = get_relative_key(f)
        for ln, snippet in hits:
            print(f"[ADR-001 SQL] {rel}:{ln}: {snippet}", file=sys.stderr)

    print(
        f"\n[ADR-001 SQL sensor] Summary: {blocking_count} blocking raw SQL hits across "
        f"{len(blocking_violations)} files.\n"
        "Per ADR-001: services MUST NOT call db.execute(text(...)) — move SQL\n"
        "to a repository in the same domain (`app/domains/<domain>/repositories/`).\n\n"
        "For tool_registry files: either migrate (W1-004-C) or add to TOOL_REGISTRY_BACKLOG.\n"
        "For services: add to SERVICES_SQL_BACKLOG or add `# ADR-001-EXEMPT: <reason>`.\n",
        file=sys.stderr,
    )

    if block:
        print("[ADR-001 SQL sensor] BLOCKING mode — failing build.")
        return 1
    print("[ADR-001 SQL sensor] WARN-ONLY mode (--warn-only flag).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
