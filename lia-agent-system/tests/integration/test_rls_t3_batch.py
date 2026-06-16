"""TDD: RLS T3 batch (Sprint 5.7 — migration 121, 20 tables).

Continues 119/120 pattern: structural validation (rls_enabled + 4 policies)
parametrized over all 20 tables. UUID + VARCHAR mix.

Skill: tdd-workflow + harness-engineering.
"""
from __future__ import annotations

import os

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


# Must match migration 121 TABLES list
T3_TABLES = (
    ("ai_consumption", "uuid"),
    ("ai_credits_balance", "uuid"),
    ("external_api_consumption", "varchar"),
    ("feedback_events", "varchar"),
    ("approval_requests", "uuid"),
    ("approvers", "uuid"),
    ("client_users", "uuid"),
    ("client_skill_catalogs", "uuid"),
    ("background_jobs", "uuid"),
    ("business_processes", "uuid"),
    ("culture_analysis_jobs", "uuid"),
    ("departments", "uuid"),
    ("department_members", "uuid"),
    ("benefits", "uuid"),
    ("company_calendar_credentials", "uuid"),
    ("company_culture_profiles", "uuid"),
    ("culture_values", "uuid"),
    ("conversation_memories", "uuid"),
    ("bigfive_department_profiles", "varchar"),
    ("domain_events", "varchar"),
)


def _conn():
    return psycopg2.connect(os.environ["DATABASE_URL"])


@pytest.mark.parametrize("table_cid", T3_TABLES, ids=[t[0] for t in T3_TABLES])
def test_t3_rls_is_enabled(table_cid: tuple[str, str]):
    """Pin: each T3 table has rowsecurity=true after migration 121."""
    table, _ = table_cid
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
                f"RLS not enabled on {table} — migration 121 not applied"
            )
    finally:
        conn.close()


@pytest.mark.parametrize("table_cid", T3_TABLES, ids=[t[0] for t in T3_TABLES])
def test_t3_has_4_policies(table_cid: tuple[str, str]):
    """Each T3 table has tenant_select/insert/update/delete policies."""
    table, _ = table_cid
    conn = _conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT COUNT(*) FROM pg_policies WHERE tablename = %s",
                (table,),
            )
            count = cur.fetchone()[0]
            assert count == 4, f"Expected 4 policies on {table}, got {count}"
    finally:
        conn.close()


@pytest.mark.parametrize(
    "table_cid",
    [t for t in T3_TABLES if t[1] == "uuid"],
    ids=[t[0] for t in T3_TABLES if t[1] == "uuid"],
)
def test_t3_uuid_policy_uses_text_cast(table_cid: tuple[str, str]):
    """UUID company_id policies must include `::text` cast in qual."""
    table, _ = table_cid
    conn = _conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT qual FROM pg_policies WHERE tablename = %s AND policyname = %s",
                (table, f"{table}_tenant_select"),
            )
            row = cur.fetchone()
            assert row is not None, f"No SELECT policy on {table}"
            qual = row[0] or ""
            assert "::text" in qual, (
                f"UUID table {table} policy missing ::text cast: {qual!r}"
            )
    finally:
        conn.close()


def test_t3_external_api_consumption_existing_data_intact():
    """The biggest table (540 rows) must keep its data after RLS apply."""
    conn = _conn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM external_api_consumption")
            count = cur.fetchone()[0]
            assert count >= 500, (
                f"Data loss in external_api_consumption: {count} rows "
                "(expected >= 500 from pre-migration count of 540)"
            )
    finally:
        conn.close()
