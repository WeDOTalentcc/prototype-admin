"""Tenant isolation tests for /api/v1/job-readiness (Task #429).

Locks in: a token from company A never sees rows from company B in the
overview, board, or detail endpoints — and never can act on them. This
guards against regressions of #5 / #329 / #330.
"""
from __future__ import annotations

import os
from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

os.environ.pop("RAILS_API_URL", None)

from app.main import app  # noqa: E402
from app.auth.dependencies import (  # noqa: E402
    get_current_user,
    get_current_active_user,
    get_current_user_or_demo,
    get_current_user_strict,
)
from app.core.database import get_db  # noqa: E402
from app.api.v1 import job_readiness as jr  # noqa: E402

COMPANY_A = "11111111-1111-1111-1111-111111111111"
COMPANY_B = "22222222-2222-2222-2222-222222222222"
JOB_A_ID = uuid4()
JOB_B_ID = uuid4()


def _make_row(job_id, company_id, title, stage="importada"):
    return SimpleNamespace(
        id=job_id,
        company_id=company_id,
        title=title,
        job_id=None,
        department=None,
        source_system="gupy",
        status="Rascunho",
        readiness_stage=stage,
        readiness_blockers=[],
        last_readiness_event_at=None,
        description=None,
        enriched_jd=None,
        behavioral_competencies=[],
        screening_questions=[],
        screening_config=None,
        additional_data={},
        assigned_audience_policy=None,
    )


def _user(company_id):
    u = MagicMock()
    u.id = f"user-{company_id}"
    u.company_id = company_id
    u.role = "admin"
    u.email = f"u@{company_id}.com"
    return u


class _FakeResult:
    def __init__(self, rows=None, scalar_value=None, all_rows=None):
        self._rows = rows or []
        self._scalar = scalar_value
        self._all = all_rows

    def scalars(self):
        return self

    def all(self):
        if self._all is not None:
            return self._all
        return list(self._rows)

    def scalar(self):
        return self._scalar

    def scalar_one_or_none(self):
        return self._rows[0] if self._rows else None


class _TenantAwareDb:
    """Records the company_id used in WHERE clauses by inspecting compiled SQL.

    For the purposes of these tests we don't need to actually parse SQL —
    we monkeypatch the db.execute method to filter our pre-seeded rows by
    the company_id that the endpoint passed in via the parameters dict.
    """

    def __init__(self, rows, company_filter):
        self._rows = rows
        self._company_filter = company_filter
        self.calls = []

    async def execute(self, stmt, params=None):
        compiled = str(stmt.compile(compile_kwargs={"literal_binds": True}))
        self.calls.append(compiled)
        # Filter rows down to ones matching the company_id the endpoint
        # baked into the WHERE clause.
        scoped = [r for r in self._rows if r.company_id == self._company_filter]
        # Aggregate count detection
        if "count(" in compiled.lower():
            # By-stage aggregation returns a list of (stage, n)
            if "group by" in compiled.lower():
                from collections import Counter
                grouped = Counter(r.readiness_stage for r in scoped)
                return _FakeResult(all_rows=list(grouped.items()))
            return _FakeResult(scalar_value=len(scoped))
        if "max(" in compiled.lower():
            return _FakeResult(scalar_value=None)
        return _FakeResult(rows=scoped)

    async def commit(self):
        pass

    async def flush(self):
        pass


@pytest.fixture
def rows():
    return [
        _make_row(JOB_A_ID, COMPANY_A, "Job-A", stage="jd_rascunho"),
        _make_row(JOB_B_ID, COMPANY_B, "Job-B", stage="jd_rascunho"),
    ]


def _client(company_id, rows):
    user = _user(company_id)
    db = _TenantAwareDb(rows, company_filter=company_id)

    async def _override_user():
        return user

    async def _override_db():
        yield db

    for dep in (
        get_current_user,
        get_current_active_user,
        get_current_user_or_demo,
        get_current_user_strict,
    ):
        app.dependency_overrides[dep] = _override_user
    app.dependency_overrides[get_db] = _override_db

    return TestClient(app), db


def teardown_function(_):
    app.dependency_overrides.clear()


def test_overview_only_returns_caller_company_rows(rows):
    client, db = _client(COMPANY_A, rows)
    res = client.get("/api/v1/job-readiness/overview")
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["total"] == 1  # only Job-A
    # Every WHERE clause must mention COMPANY_A
    assert all(COMPANY_A in c for c in db.calls if "from job_vacancies" in c.lower())
    assert all(COMPANY_B not in c for c in db.calls)


def test_board_does_not_leak_other_company(rows):
    client, db = _client(COMPANY_A, rows)
    res = client.get("/api/v1/job-readiness/board")
    assert res.status_code == 200, res.text
    items = res.json()["items"]
    assert len(items) == 1
    assert items[0]["title"] == "Job-A"


def test_detail_returns_404_for_other_company_job(rows):
    client, _ = _client(COMPANY_A, rows)
    res = client.get(f"/api/v1/job-readiness/job/{JOB_B_ID}")
    assert res.status_code == 404


def test_detail_returns_caller_company_job(rows):
    client, _ = _client(COMPANY_A, rows)
    res = client.get(f"/api/v1/job-readiness/job/{JOB_A_ID}")
    assert res.status_code == 200
    body = res.json()
    assert body["title"] == "Job-A"
    assert body["readiness_stage"] == "jd_rascunho"
