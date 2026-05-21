"""Sprint O.2 sensor — pin created_at/updated_at population in _create_job_local INSERT.

Root cause (2026-05-21): 4 vacancies from Sprint M/N validation had created_at = NULL
because (a) DB schema lacked DEFAULT CURRENT_TIMESTAMP, (b) INSERT in api_client.py
omitted both timestamp columns. Result: ORDER BY created_at DESC broken, time-based
filters broken, audit timeline UI broken.

Fix (defense-in-depth):
1. Migration 145_job_vacancies_created_at_default added DEFAULT CURRENT_TIMESTAMP.
2. api_client._create_job_local now passes created_at/updated_at explicitly.

This sensor guards both layers:
- DB sensor: assert column has server_default = CURRENT_TIMESTAMP
- INSERT sensor: assert new row has created_at populated within last 60s
- AST sensor: assert INSERT statement source includes "created_at" + "updated_at"
"""
import datetime as dt
import os
import re
import uuid

import psycopg2
import pytest

from app.domains.job_creation.api_client import JobCreationAPIClient


@pytest.fixture
def dev_local_env(monkeypatch):
    monkeypatch.setenv("LIA_DEV_LOCAL_PUBLISH", "1")
    monkeypatch.setenv("RAILS_API_URL", "")
    monkeypatch.setenv("RAILS_BACKEND_URL", "")
    yield


@pytest.fixture
def db_cleanup():
    created_ids = []
    yield created_ids
    if created_ids:
        url = os.environ["DATABASE_URL"].replace("postgresql+asyncpg://", "postgresql://")
        with psycopg2.connect(url) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM job_vacancies WHERE id::text = ANY(%s)",
                    ([str(uid) for uid in created_ids],),
                )
            conn.commit()


def _db_url() -> str:
    return os.environ["DATABASE_URL"].replace("postgresql+asyncpg://", "postgresql://")


# ----------------------------------------------------------------------
# Layer 1 — INSERT statement source includes created_at + updated_at
# ----------------------------------------------------------------------
def test_insert_statement_includes_created_at_columns():
    """AST/source guard: INSERT statement must reference created_at + updated_at.

    Detects regression where a future refactor strips the columns from INSERT,
    causing reliance solely on DB server_default (which would still work but
    erodes the belt-and-suspenders posture).
    """
    import inspect

    src = inspect.getsource(JobCreationAPIClient._create_job_local)

    # Match the INSERT INTO ... (columns) header; must include created_at + updated_at.
    m = re.search(r"INSERT INTO job_vacancies\s*\(([^)]+)\)", src, re.DOTALL)
    assert m, "Sprint O.2 sensor: INSERT INTO job_vacancies block not found"
    columns_block = m.group(1)
    assert "created_at" in columns_block, (
        "Sprint O.2 sensor: INSERT must include created_at column "
        "(belt-and-suspenders with DB DEFAULT). Refactor stripped it."
    )
    assert "updated_at" in columns_block, (
        "Sprint O.2 sensor: INSERT must include updated_at column."
    )


# ----------------------------------------------------------------------
# Layer 2 — DB schema has server_default = CURRENT_TIMESTAMP
# ----------------------------------------------------------------------
def test_job_vacancies_created_at_has_db_default():
    """DB safety net: created_at/updated_at must have server_default.

    Pins migration 145_job_vacancies_created_at_default.py against accidental
    downgrade / future ALTER COLUMN removing the default.
    """
    sql = (
        "SELECT column_name, column_default "
        "FROM information_schema.columns "
        "WHERE table_name = %s AND column_name = ANY(%s) "
        "ORDER BY column_name"
    )
    with psycopg2.connect(_db_url()) as conn:
        with conn.cursor() as cur:
            cur.execute(sql, ("job_vacancies", ["created_at", "updated_at"]))
            rows = dict(cur.fetchall())

    assert "created_at" in rows, "created_at column missing from job_vacancies"
    assert "updated_at" in rows, "updated_at column missing from job_vacancies"

    created_default = rows["created_at"]
    assert created_default is not None, (
        "Sprint O.2 sensor: job_vacancies.created_at has NO server_default. "
        "Migration 145 was reverted or never applied."
    )
    assert "CURRENT_TIMESTAMP" in created_default.upper(), (
        f"Sprint O.2 sensor: created_at default should be CURRENT_TIMESTAMP, "
        f"got: {created_default!r}"
    )
    assert rows["updated_at"] is not None, (
        "Sprint O.2 sensor: job_vacancies.updated_at has NO server_default."
    )


# ----------------------------------------------------------------------
# Layer 3 — End-to-end: new INSERT populates created_at within 60s
# ----------------------------------------------------------------------
def test_create_job_populates_created_at(dev_local_env, db_cleanup):
    """E2E: invoke _create_job_local, assert created_at is populated + recent."""
    client = JobCreationAPIClient(context=None)
    job_data = {
        "title": "Sprint O.2 sensor row",
        "description": "Verifica que created_at chega populado.",
        "department": "QA",
        "location": "Remoto",
        "work_model": "remoto",
        "seniority": "pleno",
        "technical_requirements": [],
        "behavioral_competencies": [],
        "responsibilities": [],
        "requirements": [],
        "company_id": "00000000-0000-4000-a000-000000000001",
    }

    resp = client._create_job_local(job_data)
    assert resp.success, f"INSERT failed: {resp.data}"
    new_id = resp.data["data"]["id"]
    db_cleanup.append(new_id)

    with psycopg2.connect(_db_url()) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT created_at, updated_at FROM job_vacancies WHERE id::text = %s",
                (new_id,),
            )
            created_at, updated_at = cur.fetchone()

    assert created_at is not None, (
        "Sprint O.2 sensor: NEW vacancy still has created_at = NULL. "
        "Either INSERT regression or DB default removed."
    )
    assert updated_at is not None, (
        "Sprint O.2 sensor: NEW vacancy still has updated_at = NULL."
    )

    # Recency check: should be within last 5 minutes.
    now_naive = dt.datetime.utcnow()
    age = abs((now_naive - created_at).total_seconds())
    assert age < 300, (
        f"Sprint O.2 sensor: created_at off by {age:.0f}s — clock skew or wrong default?"
    )
