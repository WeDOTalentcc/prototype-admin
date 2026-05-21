"""Sensor for Sprint P.1 fix migration 151_sprint_p1_deferred_tables_fix.

Verifies each canonical column added by migration 151 actually exists in
the live DB. Catches regression from rollback / missing alembic upgrade
head on deploy / divergent dev environment.

Background:
- Migration 148 shipped as a slot-claim no-op (race with P.2/P.3).
- Migration 151 carries the real DDL deferred from Sprint G migration 143
  for the 3 P.1 tables: whatsapp_conversations, profile_calculation_logs,
  ai_consumption.

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


# (table, column) pairs added by migration 151.
EXPECTED_COLS: list[tuple[str, str]] = [
    # whatsapp_conversations (13)
    ("whatsapp_conversations", "pre_qualification_score"),
    ("whatsapp_conversations", "pre_qualification_result"),
    ("whatsapp_conversations", "pre_qualification_matched"),
    ("whatsapp_conversations", "pre_qualification_missing"),
    ("whatsapp_conversations", "pre_qualification_decision"),
    ("whatsapp_conversations", "pre_qualification_at"),
    ("whatsapp_conversations", "eligibility_answers"),
    ("whatsapp_conversations", "eligibility_question_index"),
    ("whatsapp_conversations", "reconsideration_count"),
    ("whatsapp_conversations", "reconsideration_context"),
    ("whatsapp_conversations", "had_reconsiderations"),
    ("whatsapp_conversations", "is_existing_candidate"),
    ("whatsapp_conversations", "existing_candidate_since"),
    # profile_calculation_logs (9)
    ("profile_calculation_logs", "trigger"),
    ("profile_calculation_logs", "jobs_analyzed"),
    ("profile_calculation_logs", "corrections_analyzed"),
    ("profile_calculation_logs", "outcomes_analyzed"),
    ("profile_calculation_logs", "changes_detected"),
    ("profile_calculation_logs", "previous_profile_snapshot"),
    ("profile_calculation_logs", "new_profile_snapshot"),
    ("profile_calculation_logs", "calculated_at"),
    ("profile_calculation_logs", "calculation_time_ms"),
    # ai_consumption (2)
    ("ai_consumption", "agent_category"),
    ("ai_consumption", "studio_agent_id"),
]


@pytest.mark.parametrize("table,column", EXPECTED_COLS)
def test_migration_151_column_exists(table: str, column: str) -> None:
    """Each canonical column added by migration 151 must exist in the DB."""
    engine = create_engine(_db_url())
    insp = inspect(engine)
    cols = {c["name"] for c in insp.get_columns(table)}
    assert column in cols, (
        f"Column {table}.{column} missing — "
        f"migration 151_sprint_p1_deferred_tables_fix not applied? "
        f"Run alembic upgrade head (ADR-MIGRATIONS-001)."
    )


def test_migration_151_trigger_is_not_null() -> None:
    """profile_calculation_logs.trigger is NOT NULL (model canonical)."""
    engine = create_engine(_db_url())
    insp = inspect(engine)
    cols = {c["name"]: c for c in insp.get_columns("profile_calculation_logs")}
    assert "trigger" in cols, "profile_calculation_logs.trigger missing"
    assert cols["trigger"]["nullable"] is False, (
        "profile_calculation_logs.trigger must be NOT NULL — model declares nullable=False."
    )


def test_migration_151_agent_category_is_not_null() -> None:
    """ai_consumption.agent_category is NOT NULL with server_default core."""
    engine = create_engine(_db_url())
    insp = inspect(engine)
    cols = {c["name"]: c for c in insp.get_columns("ai_consumption")}
    assert "agent_category" in cols, "ai_consumption.agent_category missing"
    assert cols["agent_category"]["nullable"] is False, (
        "ai_consumption.agent_category must be NOT NULL — model declares nullable=False default=core."
    )


def test_migration_151_ai_consumption_indexes() -> None:
    """ai_consumption new cols are indexed (model declares index=True)."""
    engine = create_engine(_db_url())
    insp = inspect(engine)
    idx_names = {ix["name"] for ix in insp.get_indexes("ai_consumption")}
    assert "ix_ai_consumption_agent_category" in idx_names, (
        "ix_ai_consumption_agent_category missing — model declares index=True on agent_category."
    )
    assert "ix_ai_consumption_studio_agent_id" in idx_names, (
        "ix_ai_consumption_studio_agent_id missing — model declares index=True on studio_agent_id."
    )
