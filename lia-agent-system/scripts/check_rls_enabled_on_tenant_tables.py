#!/usr/bin/env python3
"""Sensor (BLOCKING): RLS enabled on the Fase 2.5 agent-studio tenant tables.

Fase 2.5 Onda C2.4 — AUDIT 6 P0-2 regression guard.

This is a *focused, blocking* complement to the broad warn-only ratchet sensor
``check_table_has_rls_policy.py`` (which covers the whole company_id inventory
with a baseline). Here we pin a small CANONICAL list of agent-studio tenant
tables that MUST have RLS ENABLED in some migration. Baseline is 0 — any of
these losing its ``ENABLE ROW LEVEL SECURITY`` statement fails the build.

Why a separate sensor: the agent-studio data layer (custom_agents, deployments,
runs, assignments, consumption, twins, catalog) is the multi-tenancy hot path of
Fase 2.5. A regression here is a cross-tenant data-leak class bug, so it gets a
hard gate at baseline 0, not a soft ratchet.

Detection is migration-source introspection (does any alembic file contain
``ALTER TABLE <name> ENABLE ROW LEVEL SECURITY``), so it runs with no DB
connection — safe in CI without DATABASE_URL.

Exit codes:
  0 — every canonical table has an ENABLE RLS statement.
  1 — at least one canonical table is missing RLS (BLOCKING).
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ALEMBIC_DIR = ROOT / "alembic" / "versions"

# Canonical agent-studio tenant tables that MUST carry RLS. Adding a new
# tenant-scoped agent-studio table? Add it here AND ship its RLS migration.
CANONICAL_TENANT_TABLES = (
    "custom_agents",
    "digital_twins",
    "ai_consumption",
    "ai_credits_balance",
    "agent_deployments",
    "agent_execution_logs",
    "pool_agent_runs",
    "pool_agent_assignments",
    "agent_template_catalog",
)

_ENABLE_RE = re.compile(
    r"ALTER\s+TABLE\s+(?:public\.)?([a-z_0-9]+)\s+ENABLE\s+ROW\s+LEVEL\s+SECURITY",
    re.IGNORECASE,
)


def _rls_enabled_tables() -> set[str]:
    enabled: set[str] = set()
    if not ALEMBIC_DIR.exists():
        return enabled
    for f in ALEMBIC_DIR.glob("*.py"):
        try:
            src = f.read_text(encoding="utf-8")
        except OSError:
            continue
        # Direct ALTER TABLE statements.
        for m in _ENABLE_RE.finditer(src):
            enabled.add(m.group(1).lower())
        # Loop pattern: `for table in (_STANDARD + ...): op.execute(f"ALTER TABLE
        # {table} ENABLE ROW LEVEL SECURITY")`. We can't evaluate the loop var, so
        # collect any string literal that appears in a file that ALSO contains the
        # ENABLE statement (conservative: covers mig 220's _STANDARD/_GLOBAL lists).
        if "ENABLE ROW LEVEL SECURITY" in src.upper():
            for lit in re.findall(r"[\"']([a-z_0-9]+)[\"']", src):
                # Only count names that look like our tables (avoid noise like
                # policy-name fragments) — must be in the canonical set to matter.
                if lit in CANONICAL_TENANT_TABLES:
                    enabled.add(lit)
    return enabled


def main() -> int:
    enabled = _rls_enabled_tables()
    missing = [t for t in CANONICAL_TENANT_TABLES if t not in enabled]

    print(
        f"[rls-enabled sensor] {len(CANONICAL_TENANT_TABLES)} canonical "
        f"agent-studio tenant tables; {len(enabled & set(CANONICAL_TENANT_TABLES))} "
        f"with RLS; {len(missing)} missing."
    )
    if not missing:
        print("[rls-enabled sensor] OK — all canonical tenant tables have RLS.")
        return 0

    for t in missing:
        print(
            f"[rls-enabled sensor] MISSING RLS: table '{t}' has no "
            f"`ALTER TABLE {t} ENABLE ROW LEVEL SECURITY` in any alembic migration.",
            file=sys.stderr,
        )
    print(
        "\n[rls-enabled sensor] BLOCKING: add an alembic migration enabling RLS "
        "for the listed table(s).\n"
        "Follow the canonical 4-policy pattern (mig 196 tasks_rls_policy / "
        "mig 220 rls_agent_studio_runtime_tables):\n"
        "  ALTER TABLE <t> ENABLE ROW LEVEL SECURITY;\n"
        "  ALTER TABLE <t> FORCE ROW LEVEL SECURITY;\n"
        "  CREATE POLICY <t>_tenant_select ON <t> FOR SELECT\n"
        "    USING ((company_id)::text = app_current_company_id());\n"
        "  (+ insert WITH CHECK, update USING, delete USING)\n"
        "If the table is intentionally global (no tenant rows), remove it from "
        "CANONICAL_TENANT_TABLES with a justifying comment.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
