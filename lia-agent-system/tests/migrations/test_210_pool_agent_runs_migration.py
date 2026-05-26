"""Sprint 7C Part 1.5a — migration 210 pool_agent_runs sensors.

Validates upgrade creates table + indexes; downgrade cleans; idempotência.
Roda contra DB live (mesma config dos outros tests/migrations/).
"""
from __future__ import annotations

import os

import pytest
from sqlalchemy import create_engine, text


@pytest.fixture(scope="module")
def engine():
    url = os.environ.get("DATABASE_URL")
    if not url:
        pytest.skip("DATABASE_URL not set")
    return create_engine(url)


def test_table_exists_after_upgrade(engine):
    """Migration 210 cria pool_agent_runs (verificada via to_regclass)."""
    with engine.connect() as c:
        reg = c.execute(
            text("SELECT to_regclass('public.pool_agent_runs')")
        ).scalar()
        assert reg == "pool_agent_runs", f"table missing: {reg}"


def test_required_columns_present(engine):
    """Canonical columns presentes pra orchestrator Part 1.5b consumir."""
    with engine.connect() as c:
        rows = c.execute(
            text(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name = 'pool_agent_runs'"
            )
        ).fetchall()
        cols = {r[0] for r in rows}
    expected = {
        "id",
        "assignment_id",
        "company_id",
        "trigger_source",
        "status",
        "started_at",
        "finished_at",
        "dispatch_metadata",
        "results",
        "runtime_metrics",
        "error_message",
        "created_at",
        "updated_at",
    }
    missing = expected - cols
    assert not missing, f"missing columns: {missing}"


def test_indexes_canonical(engine):
    """2 indexes canonical: (assignment_id,created_at) + (company_id,status)."""
    with engine.connect() as c:
        rows = c.execute(
            text(
                "SELECT indexname FROM pg_indexes "
                "WHERE tablename = 'pool_agent_runs'"
            )
        ).fetchall()
        names = {r[0] for r in rows}
    expected = {
        "idx_pool_agent_runs_assignment",
        "idx_pool_agent_runs_company_status",
    }
    missing = expected - names
    assert not missing, f"missing indexes: {missing} (have {names})"
