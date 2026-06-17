"""Sensor for Sprint P.2 migration 149_sprint_p2_deferred_nullables.

Verifies each canonical nullable column added by migration 149 actually
exists in the live DB. Catches regression from a rollback / missing
`alembic upgrade head` on a deploy / divergent dev environment.

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


# (table, column) pairs added by migration 149.
EXPECTED_COLS: list[tuple[str, str]] = [
    # webhook_logs (4)
    ("webhook_logs", "request_body"),
    ("webhook_logs", "error"),
    ("webhook_logs", "attempt"),
    ("webhook_logs", "created_at"),
    # pattern_cache (1)
    ("pattern_cache", "updated_at"),
    # recruiter_field_preferences (14)
    ("recruiter_field_preferences", "recruiter_id"),
    ("recruiter_field_preferences", "total_encounters"),
    ("recruiter_field_preferences", "typical_corrections"),
    ("recruiter_field_preferences", "preferred_values"),
    ("recruiter_field_preferences", "value_range"),
    ("recruiter_field_preferences", "custom_threshold"),
    ("recruiter_field_preferences", "always_ask"),
    ("recruiter_field_preferences", "remind_me_empty_field"),
    ("recruiter_field_preferences", "last_reminded_at"),
    ("recruiter_field_preferences", "snooze_until"),
    ("recruiter_field_preferences", "times_reminded"),
    ("recruiter_field_preferences", "times_filled_with_lia"),
    ("recruiter_field_preferences", "last_reminder_action"),
    ("recruiter_field_preferences", "last_correction_at"),
]


@pytest.mark.parametrize("table,column", EXPECTED_COLS)
def test_migration_149_column_exists(table: str, column: str) -> None:
    """Each canonical column added by migration 149 must exist in the DB."""
    engine = create_engine(_db_url())
    insp = inspect(engine)
    cols = {c["name"] for c in insp.get_columns(table)}
    assert column in cols, (
        f"Column {table}.{column} missing — "
        f"migration 149_sprint_p2_deferred_nullables not applied? "
        f"Run `alembic upgrade head` (ADR-MIGRATIONS-001)."
    )


def test_migration_149_attempt_is_not_null() -> None:
    """webhook_logs.attempt is NOT NULL with default 1 (model canonical)."""
    engine = create_engine(_db_url())
    insp = inspect(engine)
    cols = {c["name"]: c for c in insp.get_columns("webhook_logs")}
    assert "attempt" in cols, "webhook_logs.attempt missing"
    # nullable should be False per model declaration
    assert cols["attempt"]["nullable"] is False, (
        "webhook_logs.attempt must be NOT NULL — model declares nullable=False default=1."
    )
