"""Contract test: Alembic chain integrity at migrations 162-173.

Sister file to ``test_alembic_chain_integrity.py`` (which pins 161). After
161 fix, migration 162 + downstream blocked on a different P0 class:

1. ``162_workforce_entries_company_id_not_null`` used ``MIN(company_id)``
   on a UUID column. PostgreSQL has NO aggregate ``MIN(uuid)`` —
   query plan rejects with::

       function min(uuid) does not exist

2. ``163_seed_marketplace_listings`` used ``:param::type`` syntax which
   asyncpg cannot bind (collides with positional ``$N`` substitution),
   and forgot the NOT NULL ``config`` column on ``custom_agents``, and
   passed PG arrays as literal string ``"{a,b,c}"`` instead of Python
   lists.

3. ``171_credentials_access_log`` ran ``op.create_table`` unconditionally
   — broke recovery from a partial prior chain run because the table
   was already created by the failed first attempt.

This file pins canonical fixes so any future refactor that reintroduces
these patterns fails CI. Pure-unit (no live DB).

Reference: 2026-05-22 chain unblock session.
"""
from __future__ import annotations

import importlib.util
import re
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
MIG_DIR = ROOT / "alembic" / "versions"


def _read(name: str) -> str:
    path = MIG_DIR / name
    assert path.exists(), f"Migration {name} missing — update this test."
    return path.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Migration 162
# ---------------------------------------------------------------------------


def test_migration_162_module_loadable() -> None:
    """Sanity: 162 file is valid Python with upgrade/downgrade."""
    path = MIG_DIR / "162_workforce_entries_company_id_not_null.py"
    spec = importlib.util.spec_from_file_location("_test_mig_162", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert callable(getattr(module, "upgrade", None))
    assert callable(getattr(module, "downgrade", None))
    assert module.revision == "162_workforce_entries_company_id_not_null"
    assert module.down_revision == "161_tasks_company_id_not_null"


def test_migration_162_no_uuid_aggregate_bug() -> None:
    """Asserts 162 does NOT use ``MIN(company_id)`` (broken UUID aggregate).

    PostgreSQL has no aggregate ``MIN(uuid)`` — discovered 2026-05-22 blocking
    the entire chain. Canonical fix uses ``(array_agg(company_id))[1]``.
    """
    src = _read("162_workforce_entries_company_id_not_null.py")
    # The broken pattern must not be present in executable SQL
    bad = re.search(r"\bMIN\s*\(\s*company_id\s*\)(?!\s*::\s*text)", src)
    assert bad is None, (
        "Migration 162 contains `MIN(company_id)` on UUID column. "
        "PostgreSQL has no aggregate for UUID type. "
        f"Match: {bad.group(0) if bad else None}. "
        "Use `(array_agg(company_id))[1]` or `MIN(company_id::text)::uuid`."
    )
    # Positive: canonical fix is present
    assert "(array_agg(company_id))[1]" in src or "MIN(company_id::text)" in src, (
        "Migration 162 must use the canonical UUID-aggregate fix "
        "(array_agg or ::text cast)."
    )


# ---------------------------------------------------------------------------
# Migration 163
# ---------------------------------------------------------------------------


def test_migration_163_no_asyncpg_incompatible_cast() -> None:
    """Asserts 163 does NOT use ``:param::type`` (asyncpg-incompatible).

    asyncpg substitutes ``:id`` -> ``$1`` BEFORE PG parses, so ``$1::uuid``
    in a VALUES clause hits a syntax error because the parser sees the
    cast operator outside of the param-binding context. Canonical fix:
    ``CAST(:id AS uuid)``.
    """
    src = _read("163_seed_marketplace_listings.py")
    bad = re.findall(r":[a-zA-Z_][a-zA-Z0-9_]*::uuid", src)
    assert not bad, (
        f"Migration 163 has asyncpg-incompatible cast(s): {bad}. "
        "Use `CAST(:param AS uuid)` instead of `:param::uuid`."
    )
    # Positive: canonical fix is present
    assert "CAST(:id AS uuid)" in src, (
        "Migration 163 must use `CAST(:id AS uuid)` for UUID casts."
    )


def test_migration_163_includes_required_config_column() -> None:
    """Asserts the INSERT into custom_agents covers the NOT NULL ``config``
    column. The DB schema has ``config jsonb NOT NULL`` without a default;
    omitting it makes the INSERT fail with NotNullViolationError.
    """
    src = _read("163_seed_marketplace_listings.py")
    # The config column must appear in the column list of the INSERT
    insert_block_match = re.search(
        r"INSERT INTO custom_agents\s*\((?P<cols>.+?)\)\s*VALUES",
        src,
        re.DOTALL,
    )
    assert insert_block_match, "Cannot find INSERT INTO custom_agents block"
    cols = insert_block_match.group("cols")
    assert "config" in cols, (
        "Migration 163 INSERT INTO custom_agents must include `config` "
        "(NOT NULL jsonb column in DB schema). "
        f"Columns found: {cols.strip()}"
    )


def test_migration_163_passes_arrays_as_python_lists() -> None:
    """Asserts array params are Python lists (asyncpg requirement), not
    PG-literal strings like ``"{a,b,c}"``. asyncpg binds lists -> PG arrays
    natively; string literals fail with type error.
    """
    src = _read("163_seed_marketplace_listings.py")
    # Anti-pattern: building array as string concat
    bad = re.search(r'"\{"\s*\+\s*","\.join\(seed\[', src)
    assert bad is None, (
        "Migration 163 builds PG array as string literal — asyncpg fails. "
        f"Match: {bad.group(0) if bad else None}. "
        "Pass a Python list (e.g., `list(seed[\"allowed_tools\"])`)."
    )
    # Positive: lists are passed
    assert 'list(seed["allowed_tools"])' in src or 'list(seed["tags"])' in src, (
        "Migration 163 must pass arrays as Python lists for asyncpg."
    )


# ---------------------------------------------------------------------------
# Migration 171
# ---------------------------------------------------------------------------


def test_migration_171_create_table_idempotent() -> None:
    """Asserts 171 skips create_table if the table already exists. Recovery
    from partial prior chain runs depends on this — otherwise re-running
    upgrade head crashes with DuplicateTableError when an earlier failed
    attempt left the table in place.
    """
    src = _read("171_credentials_access_log.py")
    # Must have an existence-check before create_table
    has_guard = (
        "pg_tables" in src
        and "credentials_access_logs" in src
        and re.search(r"if\s+exists\s*:\s*\n\s+print", src) is not None
    )
    assert has_guard, (
        "Migration 171 must guard `op.create_table('credentials_access_logs')` "
        "with an idempotent pre-check (SELECT FROM pg_tables) — otherwise "
        "recovery from a partial prior run fails with DuplicateTableError."
    )


# ---------------------------------------------------------------------------
# Chain integrity (162-173)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "rev",
    [
        "162_workforce_entries_company_id_not_null",
        "163_seed_marketplace_listings",
        "164_candidate_company_id_not_null",
        "165_interview_company_id_not_null",
        "166_planned_task_company_id_not_null",
        "167_execution_plan_company_id_not_null",
        "168_encrypt_integration_credentials",
        "169_encrypt_billing_document",
        "169_twin_decisions_candidate_fk",
        "170_alert_canonical_consolidation",
        "170_approver_department_amount",
        "171_credentials_access_log",
        "172_offer_proposal_department",
        "173_rls_policy_batch_1",
    ],
)
def test_migration_module_loadable(rev: str) -> None:
    """Sanity: every migration 162-173 is valid Python with upgrade()/downgrade()."""
    path = MIG_DIR / f"{rev}.py"
    spec = importlib.util.spec_from_file_location(f"_test_mig_{rev}", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert callable(getattr(module, "upgrade", None)), (
        f"{rev}: upgrade() not defined"
    )
    assert callable(getattr(module, "downgrade", None)), (
        f"{rev}: downgrade() not defined"
    )
    assert module.revision == rev, f"{rev}: revision attr mismatch"
