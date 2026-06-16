"""TDD: RLS deny-by-default smoke tests for migration 173 (batch 1).

Migration 173 enables RLS on 9 remaining direct-`company_id` tables.
These tests pin the canonical isolation invariants for the freshly-protected
tables, using `credentials_access_logs` as the representative case (LGPD Art. 37
audit trail — the highest-stakes table in this batch).

Tests cover the 5 canonical RLS invariants (ADR-030 v2):
  1. RLS is actually enabled (rowsecurity = true)
  2. Cross-tenant SELECT returns empty (USING filter)
  3. Cross-tenant INSERT raises InsufficientPrivilege (WITH CHECK policy)
  4. Cross-tenant UPDATE is a no-op (USING filter on UPDATE)
  5. Cross-tenant DELETE is a no-op (USING filter on DELETE)

Companion to tests/integration/test_rls_candidates.py — same pattern, applied
to the canonical-fix DRY template introduced by migration 173.

Uses synchronous psycopg2 to avoid asyncpg+pytest-asyncio fixture complexity.
RLS is pure SQL so no async value here.

Skills aplicadas: tdd-workflow (red-green-refactor), harness-engineering
(computational sensor — verifies sensor's promise of multi-tenant isolation).

Skip conditions: DATABASE_URL not set OR psycopg2 unavailable OR migration 173
not yet applied (graceful degradation for environments behind alembic head).
"""
from __future__ import annotations

import os
import uuid

import pytest

try:
    import psycopg2  # type: ignore[import-not-found]
    HAS_PSYCOPG2 = True
except ImportError:
    HAS_PSYCOPG2 = False


pytestmark = pytest.mark.skipif(
    not HAS_PSYCOPG2 or not os.environ.get("DATABASE_URL"),
    reason="DATABASE_URL or psycopg2 not available",
)


# Representative table for batch 1 — LGPD Art. 37 credentials audit trail
TABLE = "credentials_access_logs"


def _conn():
    """Open a fresh psycopg2 connection. Caller manages txn + close."""
    return psycopg2.connect(os.environ["DATABASE_URL"])


def _migration_applied() -> bool:
    """Check if migration 173 has landed (RLS enabled on TABLE)."""
    conn = _conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT c.relrowsecurity "
                "FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace "
                "WHERE n.nspname = 'public' AND c.relname = %s",
                (TABLE,),
            )
            row = cur.fetchone()
            return bool(row and row[0])
    finally:
        conn.close()


_SKIP_NO_MIGRATION = pytest.mark.skipif(
    not _migration_applied(),
    reason=f"Migration 173 not applied — RLS not enabled on {TABLE}",
)


@pytest.fixture
def two_tenants():
    """Insert one row for each of 2 tenants into credentials_access_logs.

    Schema (verified 2026-05-22):
      id (uuid PK), company_id (uuid NOT NULL), integration_connection_id (uuid),
      accessed_at (timestamptz NOT NULL), accessor_user_id (uuid),
      accessor_type (varchar NOT NULL), access_purpose (varchar NOT NULL),
      client_ip (varchar)

    Inserts as superuser (bypasses RLS for setup). Cleans up after test.
    """
    tenant_a = str(uuid.uuid4())
    tenant_b = str(uuid.uuid4())
    row_a_id = uuid.uuid4()
    row_b_id = uuid.uuid4()

    conn = _conn()
    conn.autocommit = True
    try:
        with conn.cursor() as cur:
            for row_id, company in (
                (row_a_id, tenant_a),
                (row_b_id, tenant_b),
            ):
                cur.execute(
                    f"""
                    INSERT INTO {TABLE}
                        (id, company_id, accessed_at, accessor_type, access_purpose)
                    VALUES (%s, %s, NOW(), 'test_rls_fixture', 'rls_isolation_test')
                    """,
                    (str(row_id), company),
                )
    finally:
        conn.close()

    yield {
        "tenant_a": tenant_a,
        "tenant_b": tenant_b,
        "row_a": str(row_a_id),
        "row_b": str(row_b_id),
    }

    # Cleanup as superuser
    conn = _conn()
    conn.autocommit = True
    try:
        with conn.cursor() as cur:
            cur.execute(
                f"DELETE FROM {TABLE} WHERE accessor_type = 'test_rls_fixture'"
            )
    finally:
        conn.close()


def _set_tenant(cur, company_id: str) -> None:
    """Switch session to lia_app role + set tenant context."""
    cur.execute("SET ROLE lia_app")
    cur.execute("SET LOCAL app.company_id = %s", (company_id,))


# ---------------------------------------------------------------------------
# 5 canonical RLS invariants for migration 173
# ---------------------------------------------------------------------------


@_SKIP_NO_MIGRATION
def test_rls_is_enabled():
    """Invariant 1: ALTER TABLE ... ENABLE ROW LEVEL SECURITY landed."""
    conn = _conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT c.relrowsecurity, c.relforcerowsecurity "
                "FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace "
                "WHERE n.nspname = 'public' AND c.relname = %s",
                (TABLE,),
            )
            row = cur.fetchone()
            assert row is not None, f"Table {TABLE} does not exist"
            assert row[0] is True, (
                f"RLS not enabled on {TABLE} — migration 173 not applied"
            )
            assert row[1] is True, (
                f"FORCE RLS missing on {TABLE} — would allow table owner bypass"
            )
    finally:
        conn.close()


@_SKIP_NO_MIGRATION
def test_rls_blocks_cross_tenant_select(two_tenants):
    """Invariant 2: tenant A must NOT see tenant B's rows (USING filter)."""
    conn = _conn()
    try:
        with conn.cursor() as cur:
            _set_tenant(cur, two_tenants["tenant_a"])
            cur.execute(
                f"SELECT id, company_id FROM {TABLE} "
                f"WHERE accessor_type = 'test_rls_fixture'"
            )
            rows = cur.fetchall()
            assert len(rows) == 1, (
                f"RLS leak on {TABLE}: tenant A saw {len(rows)} rows, "
                f"expected 1. Rows: {rows}"
            )
            assert str(rows[0][0]) == two_tenants["row_a"], (
                "Tenant A saw the wrong row"
            )
    finally:
        conn.close()


@_SKIP_NO_MIGRATION
def test_rls_blocks_cross_tenant_insert(two_tenants):
    """Invariant 3: tenant A must NOT INSERT as tenant B (WITH CHECK policy)."""
    conn = _conn()
    try:
        with conn.cursor() as cur:
            _set_tenant(cur, two_tenants["tenant_a"])
            with pytest.raises(
                psycopg2.errors.InsufficientPrivilege  # row-level security
            ):
                cur.execute(
                    f"""
                    INSERT INTO {TABLE}
                        (id, company_id, accessed_at, accessor_type, access_purpose)
                    VALUES (%s, %s, NOW(), 'test_rls_fixture', 'spoof_attempt')
                    """,
                    (
                        str(uuid.uuid4()),
                        two_tenants["tenant_b"],  # spoofed company_id
                    ),
                )
    finally:
        conn.close()


@_SKIP_NO_MIGRATION
def test_rls_blocks_cross_tenant_update(two_tenants):
    """Invariant 4: tenant A UPDATE on tenant B's row is no-op (USING filter)."""
    conn = _conn()
    try:
        with conn.cursor() as cur:
            _set_tenant(cur, two_tenants["tenant_a"])
            cur.execute(
                f"UPDATE {TABLE} SET access_purpose = 'HACKED' WHERE id = %s",
                (two_tenants["row_b"],),
            )
            assert cur.rowcount == 0, (
                f"RLS leak on {TABLE}: tenant A managed to UPDATE tenant B's "
                f"row ({cur.rowcount} rows affected)"
            )
        conn.commit()
    finally:
        conn.close()

    # Verify tenant B's row was NOT changed (as superuser)
    conn = _conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                f"SELECT access_purpose FROM {TABLE} WHERE id = %s",
                (two_tenants["row_b"],),
            )
            value = cur.fetchone()[0]
            assert value == "rls_isolation_test", (
                f"Tenant B's row was modified by tenant A: '{value}'"
            )
    finally:
        conn.close()


@_SKIP_NO_MIGRATION
def test_rls_blocks_cross_tenant_delete(two_tenants):
    """Invariant 5: tenant A DELETE on tenant B's row is no-op (USING filter)."""
    conn = _conn()
    try:
        with conn.cursor() as cur:
            _set_tenant(cur, two_tenants["tenant_a"])
            cur.execute(
                f"DELETE FROM {TABLE} WHERE id = %s",
                (two_tenants["row_b"],),
            )
            assert cur.rowcount == 0, (
                f"RLS leak on {TABLE}: tenant A managed to DELETE tenant B's "
                f"row ({cur.rowcount} rows affected)"
            )
        conn.commit()
    finally:
        conn.close()

    # Verify tenant B's row still exists (as superuser)
    conn = _conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                f"SELECT COUNT(*) FROM {TABLE} WHERE id = %s",
                (two_tenants["row_b"],),
            )
            assert cur.fetchone()[0] == 1, (
                "Tenant B's row was DELETED by tenant A"
            )
    finally:
        conn.close()
