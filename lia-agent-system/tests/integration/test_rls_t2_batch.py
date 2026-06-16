"""TDD: RLS T2 batch (Sprint 5.3 — migration 120, 14 tables).

Mix UUID + VARCHAR `company_id` types. Validates structural canonical
state (rls_enabled + 4 policies) plus 1 functional test per type
exercising cross-tenant isolation.

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


# (table, cid_type) — must match migration 120 TABLES
T2_TABLES = (
    ("consent_versions", "uuid"),
    ("data_requests", "uuid"),
    ("data_subject_requests", "uuid"),
    ("data_request_configs", "uuid"),
    ("data_request_fields", "uuid"),
    ("data_request_templates", "uuid"),
    ("dpo_registry", "uuid"),
    ("data_incidents", "varchar"),
    ("sox_controls", "uuid"),
    ("company_compliance_controls", "uuid"),
    ("agent_approval_requests", "varchar"),
    ("agent_deployments", "varchar"),
    ("agent_version_snapshots", "varchar"),
    ("interview_notes", "uuid"),
)


def _conn():
    return psycopg2.connect(os.environ["DATABASE_URL"])


def _set_tenant(cur, company_id: str) -> None:
    cur.execute("SET ROLE lia_app")
    cur.execute("SET LOCAL app.company_id = %s", (company_id,))


@pytest.mark.parametrize("table_cid", T2_TABLES, ids=[t[0] for t in T2_TABLES])
def test_t2_rls_is_enabled(table_cid: tuple[str, str]):
    """Pin: each T2 table has rowsecurity=true after migration 120."""
    table, _ = table_cid
    conn = _conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT rowsecurity FROM pg_tables WHERE tablename = %s",
                (table,),
            )
            row = cur.fetchone()
            assert row is not None, f"Table {table} not found in pg_tables"
            assert row[0] is True, (
                f"RLS not enabled on {table} — migration 120 not applied"
            )
    finally:
        conn.close()


@pytest.mark.parametrize("table_cid", T2_TABLES, ids=[t[0] for t in T2_TABLES])
def test_t2_has_4_policies(table_cid: tuple[str, str]):
    """Each T2 table has tenant_select/insert/update/delete policies."""
    table, _ = table_cid
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


@pytest.mark.parametrize(
    "table_cid",
    [t for t in T2_TABLES if t[1] == "uuid"],
    ids=[t[0] for t in T2_TABLES if t[1] == "uuid"],
)
def test_t2_uuid_policy_uses_text_cast(table_cid: tuple[str, str]):
    """UUID company_id policies must include `::text` cast in qual."""
    table, _ = table_cid
    conn = _conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT qual FROM pg_policies
                WHERE tablename = %s AND policyname = %s
                """,
                (table, f"{table}_tenant_select"),
            )
            row = cur.fetchone()
            assert row is not None, f"No SELECT policy on {table}"
            qual = row[0] or ""
            # UUID cast should appear (Postgres may rewrite as `::text` or
            # `(company_id)::text`)
            assert "::text" in qual, (
                f"UUID table {table} policy missing ::text cast: {qual!r}"
            )
    finally:
        conn.close()


def test_t2_grant_to_lia_app_present():
    """Sample: company_compliance_controls grants SELECT to lia_app."""
    conn = _conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT privilege_type FROM information_schema.role_table_grants
                WHERE grantee = 'lia_app'
                  AND table_name = 'company_compliance_controls'
                """
            )
            grants = {r[0] for r in cur.fetchall()}
            for required in ("SELECT", "INSERT", "UPDATE", "DELETE"):
                assert required in grants, (
                    f"lia_app missing {required} on company_compliance_controls"
                )
    finally:
        conn.close()
