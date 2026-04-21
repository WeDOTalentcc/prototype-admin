"""Task #729 — Schema regression tests for recruitment_campaigns.

The endpoint at ``GET /api/v1/recruitment_campaigns`` started returning
500 in dev because the live table was missing every column the
``RecruitmentCampaign`` model declares (``created_by``, ``stages``,
``current_stage_index``, ``stage_history`` and the per-stage counters).
Migration ``097_reconcile_recruitment_campaigns_columns`` reconciles the
schema. These tests pin the contract so the drift cannot silently come
back.
"""
from __future__ import annotations

import pytest
from sqlalchemy import inspect, select

from app.core.database import engine
from lia_models.recruitment_campaign import RecruitmentCampaign


# (column_name, expected_python_type_name_substring, must_be_not_null)
_REQUIRED_COLUMNS: list[tuple[str, str, bool]] = [
    ("id", "UUID", True),
    ("company_id", "VARCHAR", True),
    ("created_by", "VARCHAR", True),
    ("name", "VARCHAR", True),
    ("description", "TEXT", False),
    ("job_id", "VARCHAR", False),
    ("talent_pool_id", "", False),  # type intentionally left flexible (uuid in dev, varchar elsewhere)
    ("status", "VARCHAR", True),
    ("stages", "JSON", True),
    ("current_stage_index", "INTEGER", True),
    ("automation_level", "VARCHAR", True),
    ("total_candidates", "INTEGER", False),
    ("candidates_screened", "INTEGER", False),
    ("candidates_contacted", "INTEGER", False),
    ("candidates_interviewed", "INTEGER", False),
    ("candidates_offered", "INTEGER", False),
    ("candidates_hired", "INTEGER", False),
    ("stage_history", "JSON", True),
    ("created_at", "", False),
    ("updated_at", "", False),
]

_REQUIRED_INDEXES = {"idx_campaign_company", "idx_campaign_status", "idx_campaign_job"}


@pytest.mark.asyncio
async def test_recruitment_campaigns_columns_match_model_contract():
    """DB has every column the model maps, with the right nullability."""

    def _inspect(sync_conn):
        insp = inspect(sync_conn)
        cols = {c["name"]: c for c in insp.get_columns("recruitment_campaigns")}
        idx = {ix["name"] for ix in insp.get_indexes("recruitment_campaigns")}
        return cols, idx

    async with engine.connect() as conn:
        live_cols, live_idx = await conn.run_sync(_inspect)

    failures: list[str] = []
    for name, type_hint, must_be_not_null in _REQUIRED_COLUMNS:
        if name not in live_cols:
            failures.append(f"missing column: {name}")
            continue
        if must_be_not_null and live_cols[name].get("nullable", True):
            failures.append(f"column {name} must be NOT NULL")
        if type_hint and type_hint not in str(live_cols[name]["type"]).upper():
            failures.append(
                f"column {name} expected type containing {type_hint!r}, got {live_cols[name]['type']!r}"
            )

    missing_idx = _REQUIRED_INDEXES - live_idx
    if missing_idx:
        failures.append(f"missing indexes: {sorted(missing_idx)}")

    assert not failures, "Schema drift detected:\n  - " + "\n  - ".join(failures)


def test_recruitment_campaigns_select_via_model_executes():
    """The exact SELECT issued by ``list_campaigns`` must run cleanly.

    Reproduces the original 500 (``UndefinedColumnError: created_by``) and
    pins the fix at the ORM compile + DB execution level. Uses a fresh
    sync engine so the asyncpg lifecycle of the module-level async engine
    isn't tied to the test runner's event loop.
    """
    import os

    from sqlalchemy import create_engine

    sync_url = os.environ.get("SYNC_DATABASE_URL") or (
        os.environ["DATABASE_URL"]
        .replace("postgresql+asyncpg://", "postgresql+psycopg2://")
        .replace("postgres+asyncpg://", "postgresql+psycopg2://")
    )
    sync_engine = create_engine(sync_url, future=True)
    try:
        with sync_engine.connect() as conn:
            conn.execute(select(RecruitmentCampaign).limit(1)).fetchall()
    finally:
        sync_engine.dispose()


def test_recruitment_campaign_model_declares_required_columns():
    """Belt-and-braces: model itself must keep declaring these columns."""
    declared = {c.name for c in RecruitmentCampaign.__table__.columns}
    missing = {n for n, _, _ in _REQUIRED_COLUMNS} - declared
    assert not missing, f"RecruitmentCampaign model is missing columns: {sorted(missing)}"
