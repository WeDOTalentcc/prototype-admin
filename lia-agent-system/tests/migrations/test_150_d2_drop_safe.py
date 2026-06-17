"""Sensor for Sprint P.3 migration 150_sprint_p3_d2_drop_safe.

Verifies each orphan column dropped by migration 150 is actually absent from
the live DB. Catches regression from a downgrade / divergent dev env / missing
alembic upgrade head on a deploy.

Each (table, column) pair listed below met THREE drop conditions:
  1. DB had the column
  2. Model lacked the attribute
  3. Column had 0 non-NULL values in DB (verified via COUNT FILTER pre-drop)

Ref: ADR-MIGRATIONS-001 in CLAUDE.md.
"""
from __future__ import annotations

import os

import pytest
from sqlalchemy import create_engine, inspect


def _db_url() -> str:
    url = os.environ.get("DATABASE_URL", "")
    if not url:
        pytest.skip("DATABASE_URL not set")
    url = url.replace("+asyncpg", "").replace("+psycopg", "")
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg2://")
    return url


# (table, column) pairs dropped by migration 150. Each must be absent from DB.
DROPPED_COLS: list[tuple[str, str]] = [
    # intelligence_insights (6)
    ("intelligence_insights", "title"),
    ("intelligence_insights", "description"),
    ("intelligence_insights", "impact_score"),
    ("intelligence_insights", "was_dismissed"),
    ("intelligence_insights", "user_feedback"),
    ("intelligence_insights", "expires_at"),
    # profile_calculation_logs (5)
    ("profile_calculation_logs", "calculation_type"),
    ("profile_calculation_logs", "old_values"),
    ("profile_calculation_logs", "new_values"),
    ("profile_calculation_logs", "trigger_event"),
    ("profile_calculation_logs", "created_at"),
    # talent_pools / talent_pool_candidates (2)
    ("talent_pools", "archetype_embedding"),
    ("talent_pool_candidates", "candidate_embedding"),
    # company_benefits (2)
    ("company_benefits", "created_by"),
    ("company_benefits", "updated_by"),
]


@pytest.mark.parametrize("table,column", DROPPED_COLS)
def test_migration_150_column_absent(table: str, column: str) -> None:
    """Each orphan column dropped by migration 150 must NOT exist in the DB."""
    engine = create_engine(_db_url())
    insp = inspect(engine)
    cols = {c["name"] for c in insp.get_columns(table)}
    assert column not in cols, (
        f"Column {table}.{column} still present in DB — "
        f"migration 150_sprint_p3_d2_drop_safe was downgraded or never applied. "
        f"Run alembic upgrade head (ADR-MIGRATIONS-001)."
    )


def test_migration_150_dropped_count_matches() -> None:
    """Sanity: total dropped column count equals 15 (canonical Sprint P.3 scope)."""
    assert len(DROPPED_COLS) == 15, (
        f"Sprint P.3 dropped 15 columns canonical; sensor expects 15, got {len(DROPPED_COLS)}."
    )
