"""TDD: RLS T5 — Learning/ML/Knowledge (14 tables) (migration 123).

Pattern from 121: parametrized rls_enabled + 4-policy presence checks.
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

# Must match migration 123 TABLES list
TABLES = (
    ('big_five_role_profiles', 'uuid', True),
    ('few_shot_candidates', 'varchar', True),
    ('goal_templates', 'uuid', True),
    ('goals', 'uuid', True),
    ('ideal_profiles', 'uuid', False),
    ('imported_job_descriptions', 'uuid', False),
    ('jd_similar_history', 'varchar', False),
    ('job_embeddings', 'uuid', False),
    ('job_patterns', 'uuid', False),
    ('knowledge_base', 'uuid', False),
    ('learning_patterns', 'uuid', False),
    ('ml_model_registry', 'varchar', True),
    ('model_evaluations', 'uuid', True),
    ('query_embeddings', 'varchar', True),
)


def _conn():
    return psycopg2.connect(os.environ["DATABASE_URL"])


@pytest.mark.parametrize("entry", TABLES, ids=[t[0] for t in TABLES])
def test_rls_enabled(entry):
    table, _, _ = entry
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
                f"RLS not enabled on {table} — migration 123 not applied"
            )
    finally:
        conn.close()


@pytest.mark.parametrize("entry", TABLES, ids=[t[0] for t in TABLES])
def test_has_4_policies(entry):
    table, _, _ = entry
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
    "entry",
    [t for t in TABLES if t[2]],  # nullable=True only
    ids=[t[0] for t in TABLES if t[2]],
)
def test_nullable_predicate_includes_is_null(entry):
    """NULLABLE tables MUST have `IS NULL` clause to preserve fail-open reads."""
    table, _, _ = entry
    conn = _conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT qual FROM pg_policies WHERE tablename = %s AND cmd = 'SELECT'",
                (table,),
            )
            row = cur.fetchone()
            assert row is not None, f"No SELECT policy on {table}"
            qual = row[0] or ""
            assert "IS NULL" in qual.upper(), (
                f"Nullable {table} policy must include IS NULL clause; got: {qual}"
            )
    finally:
        conn.close()
