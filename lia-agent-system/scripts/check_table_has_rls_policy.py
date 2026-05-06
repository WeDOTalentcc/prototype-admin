#!/usr/bin/env python3
"""Sensor: every table model with `company_id` column should have RLS coverage.

ADR-030 v2 — Postgres RLS Coverage
====================================================================

Multi-tenancy defense in depth (CLAUDE.md REGRA 1): tables with a
`company_id` column SHOULD have an RLS migration enabling
`tenant_<table>_select/insert/update/delete` policies via
`app_current_company_id()`.

This sensor cross-references:
  - libs/models/lia_models/*.py (SQLAlchemy table definitions)
  - alembic/versions/*.py (RLS migration source — searches for
    "ALTER TABLE <name> ENABLE ROW LEVEL SECURITY")

Reports tables with `company_id` that lack a corresponding ENABLE RLS
statement in any migration file.

Mode:
  - warn (default — for ratchet during Sprint 4 rollout)
  - --block after Sprint 5 closes the gap

Allowlist:
  - Tables marked with `# RLS-EXEMPT: <reason>` comment in the model file
  - Tables that don't have direct `company_id` (transitive isolation
    via FK chain) are documented separately in ADR-030 v2.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Models live inside the lia-agent-system package: libs/models/lia_models/
# (not at the workspace level — common confusion since some monorepo
# layouts put libs/ as a sibling of app/)
MODELS_DIR = ROOT / "libs" / "models" / "lia_models"
ALEMBIC_DIR = ROOT / "alembic" / "versions"

# Tables we know are isolated transitively (FK chain) — documented in ADR-030 v2
TRANSITIVE_ISOLATION = frozenset({
    "wsi_sessions",        # → job_vacancies, candidates
    "wsi_results",         # → wsi_sessions, candidates, job_vacancies
    "screening_question_sets",  # → job_vacancies
    "messages",            # → conversations
})

EXEMPT_PATTERN = re.compile(r"#\s*RLS-EXEMPT:\s*(.+)$", re.MULTILINE)
TABLENAME_PATTERN = re.compile(r"__tablename__\s*=\s*['\"]([a-z_0-9]+)['\"]")
COMPANY_ID_PATTERN = re.compile(r"\bcompany_id\b")
RLS_ENABLE_PATTERN = re.compile(
    r"ALTER\s+TABLE\s+(?:public\.)?([a-z_0-9]+)\s+ENABLE\s+ROW\s+LEVEL\s+SECURITY",
    re.IGNORECASE,
)


def collect_tables_with_company_id() -> dict[str, Path]:
    """Map tablename -> model file path for tables with company_id column."""
    tables: dict[str, Path] = {}
    if not MODELS_DIR.exists():
        return tables

    for f in MODELS_DIR.glob("*.py"):
        try:
            src = f.read_text(encoding="utf-8")
        except Exception:
            continue
        if not COMPANY_ID_PATTERN.search(src):
            continue
        # Find all __tablename__ assignments — a file can define multiple tables
        for m in TABLENAME_PATTERN.finditer(src):
            tables[m.group(1)] = f
    return tables


def collect_rls_enabled_tables() -> set[str]:
    """Tables found in any migration with ENABLE ROW LEVEL SECURITY."""
    enabled: set[str] = set()
    if not ALEMBIC_DIR.exists():
        return enabled
    for f in ALEMBIC_DIR.glob("*.py"):
        try:
            src = f.read_text(encoding="utf-8")
        except Exception:
            continue
        for m in RLS_ENABLE_PATTERN.finditer(src):
            enabled.add(m.group(1).lower())
        # Also pick up table names from RLS_TABLES_NOT_NULL list (068 pattern)
        # — a `for table in ALL_RLS_TABLES: ... ENABLE ROW LEVEL SECURITY` loop
        if "ENABLE ROW LEVEL SECURITY" in src:
            for line in src.splitlines():
                stripped = line.strip()
                # Quoted string literals inside lists
                if stripped.startswith('"') and stripped.endswith('",'):
                    enabled.add(stripped.strip('",').strip())
                elif stripped.startswith("'") and stripped.endswith("',"):
                    enabled.add(stripped.strip("',").strip())
    return enabled


def get_exempt_tables() -> dict[str, str]:
    """Tables marked `# RLS-EXEMPT: <reason>` in their model file."""
    exempt: dict[str, str] = {}
    for tablename, model_path in collect_tables_with_company_id().items():
        try:
            src = model_path.read_text(encoding="utf-8")
        except Exception:
            continue
        m = EXEMPT_PATTERN.search(src)
        if m and tablename in src:
            exempt[tablename] = m.group(1).strip()
    return exempt


def main() -> int:
    block = "--block" in sys.argv

    tables = collect_tables_with_company_id()
    rls_enabled = collect_rls_enabled_tables()
    exempt = get_exempt_tables()

    gaps: list[tuple[str, Path]] = []
    transitive: list[str] = []

    for tablename, model_path in sorted(tables.items()):
        if tablename in rls_enabled:
            continue
        if tablename in exempt:
            continue
        if tablename in TRANSITIVE_ISOLATION:
            transitive.append(tablename)
            continue
        gaps.append((tablename, model_path))

    print(
        f"[ADR-030 sensor] Inventory: {len(tables)} tables with company_id, "
        f"{len(rls_enabled)} with RLS enabled, {len(exempt)} explicitly exempt, "
        f"{len(transitive)} transitively isolated, {len(gaps)} GAPS."
    )

    if transitive:
        print(
            f"[ADR-030 sensor] Transitively isolated (documented in ADR-030 v2): "
            f"{sorted(transitive)}"
        )

    if not gaps:
        print(
            "[ADR-030 sensor] OK — every table with company_id has RLS coverage."
        )
        return 0

    for tablename, model_path in gaps:
        rel = model_path.relative_to(ROOT.parent)
        print(
            f"[ADR-030 sensor] GAP {rel}:{tablename}: no `ALTER TABLE {tablename} "
            f"ENABLE ROW LEVEL SECURITY` found in any migration."
        )

    print(
        f"\n[ADR-030 sensor] Summary: {len(gaps)} table(s) with company_id "
        "but no RLS migration.\n"
        "Per ADR-030 v2: every multi-tenant table SHOULD have RLS deny-by-default.\n"
        "Add an alembic migration following pattern from 068_rls_deny_by_default.py\n"
        "or 118_rls_candidates.py.\n"
        "If isolation is via FK chain (transitive), add table name to TRANSITIVE_ISOLATION.\n"
        "If genuinely exempt, add `# RLS-EXEMPT: <reason>` to the model file.\n",
        file=sys.stderr,
    )

    if block:
        return 1
    print("[ADR-030 sensor] WARN-ONLY mode — not blocking. Pass --block after Sprint 5.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
