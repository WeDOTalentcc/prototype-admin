"""P0 regression sentinel: alembic upgrade head must produce valid SQL.

Historical bug (2026-05-22):
- Migration 174 (`174_briefing_frequency_canonical`) attempted to call
  `COALESCE(hp.communication_rules, '{}'::jsonb)` on a `json`-typed column
  (`company_hiring_policies.communication_rules` is `JSON`, not `JSONB`).
  Postgres refused with `CannotCoerceError: COALESCE could not convert
  type jsonb to json`, blocking the entire alembic chain.
- Sprint 3.7 (W4-1, voice_enabled) had to bypass via psycopg2 sync to
  deploy migration 177. This sensor prevents recidivism.

Fix applied:
- 174 SQL now casts the JSON column explicitly to jsonb for jsonb_set /
  ? / -> operations, and casts back with `::json` on the SET clause.
- 177 made idempotent (`ADD COLUMN IF NOT EXISTS`) so a partial-state
  database (column already present from psycopg2 bypass) can be
  reconciled by alembic without manual surgery.

This file enforces three invariants:
  1. alembic DAG has a SINGLE head (no unresolved merge).
  2. `alembic upgrade head --sql` produces valid SQL (no crash).
  3. Recent migrations (170+) don't reintroduce the same json/jsonb
     coercion anti-pattern without an explicit cast or EXEMPT marker.
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
VERSIONS_DIR = REPO_ROOT / "alembic" / "versions"


def test_alembic_heads_single() -> None:
    """alembic DAG must have a single head — multiple heads signal an
    unresolved merge that will eventually block `upgrade head`.
    """
    result = subprocess.run(
        [
            "python",
            "-c",
            (
                "from alembic.script import ScriptDirectory; "
                "from alembic.config import Config; "
                "cfg = Config('alembic.ini'); "
                "sd = ScriptDirectory.from_config(cfg); "
                "heads = sd.get_heads(); "
                "assert len(heads) == 1, f'multiple heads: {heads}'; "
                "print(heads[0])"
            ),
        ],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, (
        "alembic heads check failed:\n"
        f"stdout: {result.stdout}\n"
        f"stderr: {result.stderr}"
    )


def test_alembic_upgrade_head_against_live_db() -> None:
    """`alembic upgrade head` must NOT crash on the live database.

    This is the P0 sentinel: the original 174 bug surfaced as
    `CannotCoerceError: COALESCE could not convert type jsonb to json`
    blocking the whole chain. Re-running this in CI ensures any new
    migration that fails Postgres DDL validation is caught.

    Idempotent: if the DB is already at head, alembic short-circuits
    with no SQL emitted and exit 0. So this also runs cheaply on
    repeated CI invocations.

    Skipped automatically when DATABASE_URL is unset (e.g., local dev
    without a Postgres instance running).
    """
    import os

    if not os.environ.get("DATABASE_URL"):
        pytest.skip("DATABASE_URL not set; skipping live-DB upgrade check")

    result = subprocess.run(
        ["alembic", "upgrade", "head"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        timeout=300,
    )
    assert result.returncode == 0, (
        "alembic upgrade head crashed:\n"
        f"stdout (last 800 chars): {result.stdout[-800:]}\n"
        f"stderr (last 800 chars): {result.stderr[-800:]}"
    )


def test_no_jsonb_coercion_on_json_columns_without_cast() -> None:
    """Migrations 170+ must not COALESCE/jsonb_set a json-typed column
    without an explicit ::jsonb cast or an # ALEMBIC-COERCION-EXEMPT marker.

    Heuristic: any migration that uses `jsonb_set(` or `'{}'::jsonb` on a
    column reference (heuristically: `<word>.<word>` immediately before
    the jsonb expression) without `::jsonb` cast on that reference. We
    skip files that include the EXEMPT marker so an intentional case
    documents itself.
    """
    if not VERSIONS_DIR.exists():
        pytest.skip("alembic/versions not present")

    risky_patterns = [
        # jsonb_set(col_ref, ...) where col_ref has no ::jsonb cast
        re.compile(
            r"jsonb_set\(\s*COALESCE\(\s*([a-zA-Z_][\w]*\.[a-zA-Z_][\w]*)\s*,\s*'\{\}'::jsonb",
            re.IGNORECASE,
        ),
        # col_ref ? 'key' or col_ref - 'key' without ::jsonb cast (jsonb-only ops)
        re.compile(
            r"\b([a-zA-Z_][\w]*\.[a-zA-Z_][\w]*)\s*\?\s*'[^']+'",
            re.IGNORECASE,
        ),
    ]

    failures: list[str] = []
    for mig in sorted(VERSIONS_DIR.glob("17[0-9]_*.py")) + sorted(
        VERSIONS_DIR.glob("18[0-9]_*.py")
    ):
        content = mig.read_text()
        if "ALEMBIC-COERCION-EXEMPT" in content:
            continue
        for pat in risky_patterns:
            for match in pat.finditer(content):
                col_ref = match.group(1)
                # Need explicit cast somewhere in the same statement
                # (rough proxy: same file mentions `<col_ref>::jsonb`).
                if f"{col_ref}::jsonb" not in content:
                    failures.append(
                        f"{mig.name}: `{col_ref}` used in jsonb context "
                        f"without explicit `::jsonb` cast. "
                        f"Add `{col_ref}::jsonb` or `# ALEMBIC-COERCION-EXEMPT: <reason>`."
                    )

    assert not failures, (
        "Risky json/jsonb coercion(s) found in recent migrations:\n"
        + "\n".join(failures)
    )
