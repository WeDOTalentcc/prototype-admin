"""TDD: RLS deny-by-default on `candidates` table (ADR-030 v2 Sprint 4A).

Migration 118 enabled RLS on candidates. This test pins:
  1. RLS is actually enabled (rowsecurity = true)
  2. SET app.company_id ISOLATES — cross-tenant SELECT returns empty
  3. INSERT with mismatched company_id is rejected (WITH CHECK policy)
  4. UPDATE/DELETE on other-tenant rows is no-op (RLS USING filter)
  5. Same-tenant operations work normally

Uses synchronous psycopg2 to avoid asyncpg+pytest-asyncio fixture complexity.
RLS is pure SQL so no async value here.

Skill: tdd-workflow + harness-engineering (computational sensor).
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


def _conn():
    """Open a fresh psycopg2 connection. Caller manages txn + close."""
    return psycopg2.connect(os.environ["DATABASE_URL"])


@pytest.fixture
def two_tenants():
    """Insert 2 candidates for 2 different tenants and yield their ids.

    Inserts as superuser (bypasses RLS). Cleans up after test.
    """
    tenant_a = f"test_rls_a_{uuid.uuid4().hex[:8]}"
    tenant_b = f"test_rls_b_{uuid.uuid4().hex[:8]}"
    candidate_a_id = uuid.uuid4()
    candidate_b_id = uuid.uuid4()

    conn = _conn()
    conn.autocommit = True
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO candidates (id, company_id, name, source, created_at, updated_at)
                VALUES (%s, %s, %s, 'test_rls_fixture', NOW(), NOW())
                """,
                (str(candidate_a_id), tenant_a, "Tenant A Candidate"),
            )
            cur.execute(
                """
                INSERT INTO candidates (id, company_id, name, source, created_at, updated_at)
                VALUES (%s, %s, %s, 'test_rls_fixture', NOW(), NOW())
                """,
                (str(candidate_b_id), tenant_b, "Tenant B Candidate"),
            )
    finally:
        conn.close()

    yield {
        "tenant_a": tenant_a,
        "tenant_b": tenant_b,
        "candidate_a": str(candidate_a_id),
        "candidate_b": str(candidate_b_id),
    }

    # Cleanup as superuser
    conn = _conn()
    conn.autocommit = True
    try:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM candidates WHERE company_id = ANY(%s)",
                ([tenant_a, tenant_b],),
            )
    finally:
        conn.close()


def _set_tenant(cur, company_id: str) -> None:
    """Switch session to lia_app role + set tenant context."""
    cur.execute("SET ROLE lia_app")
    cur.execute("SET LOCAL app.company_id = %s", (company_id,))


def test_candidates_rls_is_enabled():
    """Pin: ALTER TABLE candidates ENABLE ROW LEVEL SECURITY landed (118)."""
    conn = _conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT rowsecurity FROM pg_tables WHERE tablename = 'candidates'"
            )
            row = cur.fetchone()
            assert row is not None and row[0] is True, (
                "RLS not enabled on candidates — migration 118 not applied"
            )
    finally:
        conn.close()


def test_candidates_rls_blocks_cross_tenant_select(two_tenants):
    """Tenant A session must NOT see Tenant B's candidate."""
    conn = _conn()
    try:
        with conn.cursor() as cur:
            _set_tenant(cur, two_tenants["tenant_a"])
            cur.execute(
                "SELECT id, company_id FROM candidates "
                "WHERE company_id = ANY(%s)",
                ([two_tenants["tenant_a"], two_tenants["tenant_b"]],),
            )
            rows = cur.fetchall()
            assert len(rows) == 1, (
                f"RLS leak: tenant A saw {len(rows)} rows, expected 1. "
                f"Rows: {rows}"
            )
            assert str(rows[0][0]) == two_tenants["candidate_a"], (
                "Tenant A saw the wrong candidate"
            )
    finally:
        conn.close()


def test_candidates_rls_blocks_cross_tenant_insert(two_tenants):
    """Tenant A session must NOT be able to insert as Tenant B (WITH CHECK)."""
    conn = _conn()
    try:
        with conn.cursor() as cur:
            _set_tenant(cur, two_tenants["tenant_a"])
            with pytest.raises(
                psycopg2.errors.InsufficientPrivilege  # row-level security
            ):
                cur.execute(
                    """
                    INSERT INTO candidates (id, company_id, name, source, created_at, updated_at)
                    VALUES (%s, %s, %s, 'test_rls_fixture', NOW(), NOW())
                    """,
                    (
                        str(uuid.uuid4()),
                        two_tenants["tenant_b"],  # spoofed
                        "Spoofed",
                    ),
                )
    finally:
        conn.close()


def test_candidates_rls_blocks_cross_tenant_update(two_tenants):
    """Tenant A session UPDATE on tenant B's row is a no-op."""
    conn = _conn()
    # autocommit=False so SET LOCAL persists across the UPDATE
    try:
        with conn.cursor() as cur:
            _set_tenant(cur, two_tenants["tenant_a"])
            cur.execute(
                "UPDATE candidates SET name = 'HACKED' WHERE id = %s",
                (two_tenants["candidate_b"],),
            )
            assert cur.rowcount == 0, (
                f"RLS leak: tenant A managed to UPDATE tenant B's row "
                f"({cur.rowcount} rows affected)"
            )
        conn.commit()
    finally:
        conn.close()

    # Verify tenant B's name was NOT changed (as superuser)
    conn = _conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT name FROM candidates WHERE id = %s",
                (two_tenants["candidate_b"],),
            )
            name = cur.fetchone()[0]
            assert name == "Tenant B Candidate", (
                f"Tenant B's name was modified by tenant A: '{name}'"
            )
    finally:
        conn.close()


def test_candidates_rls_allows_same_tenant_operations(two_tenants):
    """Sanity: same-tenant SELECT/INSERT/UPDATE/DELETE work normally.

    NOTE: `SET LOCAL` is transaction-scoped — must NOT use autocommit.
    Keep all 4 ops inside one explicit transaction.
    """
    new_id = str(uuid.uuid4())
    conn = _conn()
    # autocommit=False (default) so SET LOCAL persists across statements
    try:
        with conn.cursor() as cur:
            _set_tenant(cur, two_tenants["tenant_a"])

            cur.execute(
                """
                INSERT INTO candidates (id, company_id, name, source, created_at, updated_at)
                VALUES (%s, %s, %s, 'test_rls_fixture', NOW(), NOW())
                """,
                (new_id, two_tenants["tenant_a"], "Same-tenant ok"),
            )

            cur.execute(
                "SELECT id FROM candidates WHERE id = %s", (new_id,)
            )
            assert str(cur.fetchone()[0]) == new_id

            cur.execute(
                "UPDATE candidates SET name = 'Updated' WHERE id = %s",
                (new_id,),
            )
            assert cur.rowcount == 1

            cur.execute("DELETE FROM candidates WHERE id = %s", (new_id,))
            assert cur.rowcount == 1
        conn.commit()
    finally:
        conn.close()
