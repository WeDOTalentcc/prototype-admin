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

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Models live inside the lia-agent-system package: libs/models/lia_models/
# (not at the workspace level — common confusion since some monorepo
# layouts put libs/ as a sibling of app/)
MODELS_DIR = ROOT / "libs" / "models" / "lia_models"
ALEMBIC_DIR = ROOT / "alembic" / "versions"
ALLOWLIST_FILE = ROOT / "scripts" / ".rls_allowlist.txt"


def load_allowlist() -> dict[str, str]:
    """Load tablename → reason from scripts/.rls_allowlist.txt.

    Format: ``tablename: reason`` (reason optional). Lines starting with
    ``#`` and blank lines are ignored.
    """
    out: dict[str, str] = {}
    if not ALLOWLIST_FILE.exists():
        return out
    for raw in ALLOWLIST_FILE.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if ":" in line:
            name, reason = line.split(":", 1)
            out[name.strip()] = reason.strip()
        else:
            out[line] = "(see scripts/.rls_allowlist.txt)"
    return out

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
    # Pattern: tuple of (table_name, type_str) inside a list — e.g.
    # `("consent_versions", "uuid"),` as used by 120/139/173 migrations.
    tuple_pattern = re.compile(
        r"""\(\s*["']([a-z_0-9]+)["']\s*,\s*["'][a-z_]+["']\s*\)\s*,?""",
        re.IGNORECASE,
    )
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
                else:
                    # Tuple pattern: `("table", "uuid"),` used by 120/139/173.
                    # Parser previously missed these — drove 100 false-positive
                    # GAP reports in 2026-05-22 audit. Cover them here.
                    for m in tuple_pattern.finditer(line):
                        enabled.add(m.group(1).lower())
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


def load_baseline(baseline_file: Path) -> int:
    """Load ratchet baseline count from file. Returns 0 if missing/unparseable."""
    if not baseline_file.exists():
        return 0
    try:
        return int(baseline_file.read_text(encoding="utf-8").strip())
    except (ValueError, OSError):
        return 0


def save_baseline(baseline_file: Path, count: int) -> None:
    """Persist ratchet baseline count for future runs."""
    baseline_file.parent.mkdir(parents=True, exist_ok=True)
    baseline_file.write_text(f"{count}\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="ADR-030 sensor: RLS coverage on tables with company_id"
    )
    parser.add_argument(
        "--block", "--blocking", dest="block", action="store_true",
        help="Forca BLOCKING mode (fail se count > baseline)"
    )
    parser.add_argument(
        "--warn-only", action="store_true",
        help="Forca WARN-ONLY mode (sempre exit 0)"
    )
    parser.add_argument(
        "--baseline-file", type=Path,
        default=ROOT / "scripts" / "baselines" / "rls_policy.txt",
        help="Ratchet baseline file (default: scripts/baselines/rls_policy.txt)",
    )
    parser.add_argument(
        "--update-baseline", action="store_true",
        help="Atualiza baseline com count atual e sai 0 (use apos closing gaps)",
    )
    args = parser.parse_args(argv)

    tables = collect_tables_with_company_id()
    rls_enabled = collect_rls_enabled_tables()
    exempt = get_exempt_tables()
    allowlist = load_allowlist()

    gaps: list[tuple[str, Path]] = []
    transitive: list[str] = []
    allowlisted: list[tuple[str, str]] = []

    for tablename, model_path in sorted(tables.items()):
        if tablename in rls_enabled:
            continue
        if tablename in exempt:
            continue
        if tablename in TRANSITIVE_ISOLATION:
            transitive.append(tablename)
            continue
        if tablename in allowlist:
            allowlisted.append((tablename, allowlist[tablename]))
            continue
        gaps.append((tablename, model_path))

    count = len(gaps)
    baseline = load_baseline(args.baseline_file)

    if args.update_baseline:
        save_baseline(args.baseline_file, count)
        print(
            f"[ADR-030 sensor] Baseline atualizado em {args.baseline_file}: "
            f"{count} GAPS"
        )
        return 0

    print(
        f"[ADR-030 sensor] Inventory: {len(tables)} tables with company_id, "
        f"{len(rls_enabled)} with RLS enabled, {len(exempt)} explicitly exempt, "
        f"{len(transitive)} transitively isolated, "
        f"{len(allowlisted)} allowlisted, {count} GAPS "
        f"(baseline ratchet: {baseline})."
    )
    if allowlisted:
        print(
            "[ADR-030 sensor] Allowlisted via scripts/.rls_allowlist.txt: "
            f"{[t for t, _ in allowlisted]}"
        )

    if transitive:
        print(
            f"[ADR-030 sensor] Transitively isolated (documented in ADR-030 v2): "
            f"{sorted(transitive)}"
        )

    if count == 0:
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
        f"\n[ADR-030 sensor] Summary: {count} table(s) with company_id "
        "but no RLS migration.\n"
        "Per ADR-030 v2: every multi-tenant table SHOULD have RLS deny-by-default.\n"
        "Add an alembic migration following pattern from 068_rls_deny_by_default.py,\n"
        "118_rls_candidates.py, 139_t02_rls_high_priority.py, or\n"
        "173_rls_policy_batch_1.py.\n"
        "If isolation is via FK chain (transitive), add table name to TRANSITIVE_ISOLATION.\n"
        "If genuinely exempt, add `# RLS-EXEMPT: <reason>` to the model file.\n"
        "If sensor false-positive (parser bug), add tablename to scripts/.rls_allowlist.txt\n"
        "with reason 'RLS applied via <migration_filename>'.\n",
        file=sys.stderr,
    )

    blocking_mode = args.block and not args.warn_only

    if blocking_mode and count > baseline:
        print(
            f"\n[ADR-030 sensor] BLOCKING: {count} > baseline {baseline}. "
            "Corrigir GAP ou ajustar baseline via --update-baseline.",
            file=sys.stderr,
        )
        return 1

    if not blocking_mode:
        print(
            "[ADR-030 sensor] WARN-ONLY mode — not blocking. "
            "Pass --block para promover a BLOCKING (ou via baseline ratchet).",
            file=sys.stderr,
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
