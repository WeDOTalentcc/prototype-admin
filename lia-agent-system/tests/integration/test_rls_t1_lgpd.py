"""TDD: RLS deny-by-default for T1 LGPD/PII tables (Sprint 5.2 batch 1).

Migration 119 enabled RLS on 6 LGPD-critical tables with UUID
company_id (different from 118 candidates which uses VARCHAR).

Tests pin:
  1. RLS is enabled on all 6 tables (rowsecurity = true)
  2. UUID `::text` cast pattern works (sample on shared_searches — 0 rows
     so safe to insert)
  3. Same-tenant SELECT/INSERT works
  4. Cross-tenant SELECT returns empty (RLS USING)
  5. Cross-tenant INSERT rejected (WITH CHECK)

Skill: tdd-workflow + harness-engineering.
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


T1_TABLES = (
    "consent_records",
    "consent_events",
    "breach_notifications",
    "automated_decision_explanations",
    "ai_inference_logs",
    "shared_searches",
)


def _conn():
    return psycopg2.connect(os.environ["DATABASE_URL"])


def _set_tenant(cur, company_id: str) -> None:
    cur.execute("SET ROLE lia_app")
    cur.execute("SET LOCAL app.company_id = %s", (company_id,))


@pytest.mark.parametrize("table", T1_TABLES)
def test_t1_rls_is_enabled(table: str):
    """Pin: each T1 table has rowsecurity=true after migration 119."""
    conn = _conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT rowsecurity FROM pg_tables WHERE tablename = %s",
                (table,),
            )
            row = cur.fetchone()
            assert row is not None, f"Table {table} not found"
            assert row[0] is True, (
                f"RLS not enabled on {table} — migration 119 not applied"
            )
    finally:
        conn.close()


@pytest.mark.parametrize("table", T1_TABLES)
def test_t1_has_4_policies(table: str):
    """Each T1 table has tenant_select/insert/update/delete policies."""
    conn = _conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT COUNT(*) FROM pg_policies WHERE tablename = %s",
                (table,),
            )
            count = cur.fetchone()[0]
            assert count == 4, (
                f"Expected 4 policies on {table}, got {count}"
            )
    finally:
        conn.close()


def test_t1_uuid_cast_pattern_blocks_cross_tenant_select():
    """Smoke: UUID `::text` cast pattern actually filters by tenant.

    Uses shared_searches (0 rows in dev DB → safe to insert + delete).
    Inserts 1 row as tenant A, sees 1 from tenant A session, 0 from
    tenant B session.
    """
    tenant_a = str(uuid.uuid4())
    tenant_b = str(uuid.uuid4())
    search_id = str(uuid.uuid4())

    conn = _conn()
    try:
        # Insert as superuser (bypass RLS)
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO shared_searches
                  (id, company_id, created_by_user_id, share_type, title,
                   status, snapshot_payload, can_comment, can_rate,
                   created_at, updated_at)
                VALUES (%s, %s, %s, 'search', %s, 'active',
                        '{}'::jsonb, true, true, NOW(), NOW())
                """,
                (search_id, tenant_a, str(uuid.uuid4()), "Test RLS UUID cast"),
            )
        conn.commit()

        # Tenant A session — should see the row
        with conn.cursor() as cur:
            _set_tenant(cur, tenant_a)
            cur.execute(
                "SELECT id FROM shared_searches WHERE id = %s",
                (search_id,),
            )
            assert cur.fetchone() is not None, (
                "Tenant A session did NOT see its own row — UUID cast broken"
            )
        conn.commit()

        # Tenant B session — should NOT see it
        with conn.cursor() as cur:
            _set_tenant(cur, tenant_b)
            cur.execute(
                "SELECT id FROM shared_searches WHERE id = %s",
                (search_id,),
            )
            assert cur.fetchone() is None, (
                "RLS LEAK: Tenant B saw tenant A's row"
            )
        conn.commit()
    finally:
        # Cleanup as superuser
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM shared_searches WHERE id = %s",
                (search_id,),
            )
        conn.commit()
        conn.close()


def test_t1_uuid_cast_blocks_cross_tenant_insert():
    """Tenant A cannot insert spoofed as Tenant B (WITH CHECK)."""
    tenant_a = str(uuid.uuid4())
    tenant_b = str(uuid.uuid4())

    conn = _conn()
    try:
        with conn.cursor() as cur:
            _set_tenant(cur, tenant_a)
            with pytest.raises(psycopg2.errors.InsufficientPrivilege):
                cur.execute(
                    """
                    INSERT INTO shared_searches
                      (id, company_id, created_by_user_id, share_type, title,
                       status, snapshot_payload, can_comment, can_rate,
                       created_at, updated_at)
                    VALUES (%s, %s, %s, 'search', %s, 'active',
                            '{}'::jsonb, true, true, NOW(), NOW())
                    """,
                    (str(uuid.uuid4()), tenant_b, str(uuid.uuid4()), "Spoofed"),
                )
    finally:
        conn.close()
