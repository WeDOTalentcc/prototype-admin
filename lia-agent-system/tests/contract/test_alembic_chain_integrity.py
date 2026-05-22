"""Contract test: Alembic chain integrity at migration 161 (P0 unblock).

Migration ``161_tasks_company_id_not_null`` introduced cross-tenant lockdown
on ``tasks.company_id`` (WT-2022). The first version of the migration had a
canonical-fix violation: it joined ``tasks.related_job_id`` (VARCHAR) against
``job_vacancies.id`` (UUID) without an explicit CAST. PostgreSQL has no
implicit cast between those types and rejects the query with::

    operator does not exist: character varying = uuid

That blocked ``alembic upgrade head`` for revisions 161-173 in production.

This file pins the canonical fix so any future refactor that reintroduces
the bad pattern fails CI.

The tests are pure-unit (no live DB):
1. ``test_migration_161_module_loadable`` — sanity that the file is valid
   Python and exposes ``upgrade``/``downgrade``.
2. ``test_migration_161_uses_canonical_uuid_cast`` — asserts the backfill
   SQL casts ``jv.id::text`` (canonical-fix pattern).
3. ``test_migration_161_validates_related_job_id_format`` — asserts the
   defensive regex format check is present (rejects malformed varchar).
4. ``test_migration_161_creates_preflight_backup`` — asserts the
   ``_tasks_pre_161_backup`` idempotent ``CREATE TABLE IF NOT EXISTS`` is
   present (rollback safety).
5. ``test_migration_161_logs_orphans_before_delete`` — asserts the migration
   logs sample orphan IDs before issuing ``DELETE`` (REGRA 4 no-silent).

The tests parse the migration source file as text. Heavyweight integration
tests that spin up a real DB belong in ``tests/integration/`` (out of scope
here — sandbox DB already validated the chain manually 2026-05-22).
"""
from __future__ import annotations

import importlib.util
import re
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
MIGRATION_PATH = (
    ROOT / "alembic" / "versions" / "161_tasks_company_id_not_null.py"
)


@pytest.fixture(scope="module")
def migration_source() -> str:
    assert MIGRATION_PATH.exists(), (
        f"Migration file missing at {MIGRATION_PATH}. Canonical-fix harness "
        "depends on its presence — if it was renamed/removed update this test."
    )
    return MIGRATION_PATH.read_text(encoding="utf-8")


def test_migration_161_module_loadable(migration_source: str) -> None:
    """Sanity: the migration file is valid Python with upgrade/downgrade."""
    spec = importlib.util.spec_from_file_location(
        "_test_migration_161", MIGRATION_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert callable(getattr(module, "upgrade", None)), (
        "Migration must expose upgrade()"
    )
    assert callable(getattr(module, "downgrade", None)), (
        "Migration must expose downgrade()"
    )
    assert module.revision == "161_tasks_company_id_not_null"
    assert module.down_revision == "160_encrypt_interview_offer_emails"


def test_migration_161_uses_canonical_uuid_cast(migration_source: str) -> None:
    """Asserts the backfill SQL uses ``jv.id::text`` (canonical-fix pattern).

    Without the cast, PostgreSQL rejects the JOIN with
    ``operator does not exist: character varying = uuid``. Regression bug
    that blocked alembic upgrade head 2026-05-22.
    """
    assert "jv.id::text" in migration_source, (
        "Migration 161 MUST cast jv.id to text in the backfill JOIN "
        "(canonical-fix). Anti-pattern that previously blocked deploy: "
        "`tasks.related_job_id = jv.id`. Canonical: "
        "`tasks.related_job_id = jv.id::text`."
    )
    # Bonus: anti-pattern must NOT reappear
    bad_pattern = re.search(
        r"tasks\.related_job_id\s*=\s*jv\.id\b(?!::)", migration_source
    )
    assert bad_pattern is None, (
        "Anti-pattern `tasks.related_job_id = jv.id` detected without cast. "
        f"Match: {bad_pattern.group(0) if bad_pattern else None}"
    )


def test_migration_161_validates_related_job_id_format(
    migration_source: str,
) -> None:
    """Asserts the defensive regex format check is present.

    Without format validation, rows with malformed varchar in
    related_job_id (e.g., external numeric IDs from legacy imports) would
    crash the cast. The migration filters via regex
    ``~ '^[0-9a-fA-F-]{36}$'`` to skip non-UUID values safely.
    """
    assert "'^[0-9a-fA-F-]{36}$'" in migration_source, (
        "Migration 161 MUST format-validate related_job_id before joining "
        "(defense in depth against malformed legacy data)."
    )


def test_migration_161_creates_preflight_backup(
    migration_source: str,
) -> None:
    """Asserts the pre-flight backup table is created idempotently.

    Backup enables rollback if DELETE removed too many rows. Idempotent
    via IF NOT EXISTS so rerun is safe.
    """
    assert "CREATE TABLE IF NOT EXISTS _tasks_pre_161_backup" in migration_source, (
        "Migration 161 MUST create idempotent backup table "
        "`_tasks_pre_161_backup` before destructive DELETE."
    )


def test_migration_161_logs_orphans_before_delete(
    migration_source: str,
) -> None:
    """Asserts orphan rows are sampled and logged before DELETE.

    Production REGRA 4 (canonical-standards): never silently delete. Audit
    trail must surface (sample) IDs before destructive action so operators
    can verify post-hoc.
    """
    # Must SELECT samples
    assert re.search(
        r"SELECT\s+id.*FROM\s+tasks\s+WHERE\s+company_id\s+IS\s+NULL",
        migration_source,
        re.IGNORECASE | re.DOTALL,
    ), "Migration 161 MUST SELECT sample orphan IDs before DELETE for audit."

    # Must print sample IDs
    assert "Sample orfas" in migration_source or "Sample orphans" in migration_source, (
        "Migration 161 MUST log sample orphan IDs to stdout (audit trail "
        "visible in deploy logs)."
    )

    # DELETE must come AFTER the SELECT/print (textual order check)
    select_idx = migration_source.find("SELECT id")
    delete_idx = migration_source.find("DELETE FROM tasks WHERE company_id IS NULL")
    assert select_idx > 0 and delete_idx > 0, (
        "Both SELECT (sample) and DELETE statements must be present."
    )
    assert select_idx < delete_idx, (
        "SELECT/log of orphans MUST precede DELETE (no silent deletion)."
    )
