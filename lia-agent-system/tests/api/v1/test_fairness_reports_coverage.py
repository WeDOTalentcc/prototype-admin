"""
Coverage tests for app/api/v1/fairness_reports.py — Task #930.

Cobre os 3 endpoints de relatórios FairnessGuard:
- GET /fairness/reports/summary
- GET /fairness/reports/trend
- GET /fairness/audit/logs

Cada um com happy + erro (validação de Query) + isolamento (company_id passado
para o repositório).
"""
from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.fairness_reports import router
from app.auth.dependencies import get_current_user
from app.core.database import get_db


COMPANY_A = "11111111-1111-1111-1111-111111111111"
COMPANY_B = "22222222-2222-2222-2222-222222222222"


def _user(company_id: str) -> MagicMock:
    u = MagicMock()
    u.id = uuid4()
    u.company_id = company_id
    u.is_active = True
    return u


@pytest.fixture
def app() -> FastAPI:
    application = FastAPI()
    application.include_router(router, prefix="/api/v1")
    application.dependency_overrides[get_db] = lambda: MagicMock()
    application.dependency_overrides[get_current_user] = lambda: _user(COMPANY_A)
    return application


# ----------------- /fairness/reports/summary -----------------

class TestFairnessSummary:
    def test_happy_aggregates_categories(self, app: FastAPI):
        rows = [
            SimpleNamespace(category="age", blocks=3, warnings=1, last_occurrence=datetime.now(UTC)),
            SimpleNamespace(category="gender", blocks=1, warnings=2, last_occurrence=datetime.now(UTC)),
        ]
        repo_mock = MagicMock()
        repo_mock.get_summary_by_category = AsyncMock(return_value=rows)
        with patch(
            "app.api.v1.fairness_reports.FairnessReportRepository",
            return_value=repo_mock,
        ):
            client = TestClient(app, raise_server_exceptions=False)
            r = client.get("/api/v1/fairness/reports/summary", params={"days": 30})
        assert r.status_code == 200
        body = r.json()
        assert body["total_blocks"] == 4
        assert body["total_events"] == 7  # 3+1+1+2
        # Sorted desc by total_blocks
        assert body["by_category"][0]["category"] == "age"

    def test_invalid_days_returns_422(self, app: FastAPI):
        client = TestClient(app, raise_server_exceptions=False)
        r = client.get("/api/v1/fairness/reports/summary", params={"days": 0})
        assert r.status_code == 422

    def test_company_id_passed_through_to_repository(self, app: FastAPI):
        captured: list[str | None] = []

        async def _spy(since, company_id):
            captured.append(company_id)
            return []

        repo_mock = MagicMock()
        repo_mock.get_summary_by_category = _spy
        with patch(
            "app.api.v1.fairness_reports.FairnessReportRepository",
            return_value=repo_mock,
        ):
            client = TestClient(app, raise_server_exceptions=False)
            client.get("/api/v1/fairness/reports/summary", params={"company_id": COMPANY_A})
            client.get("/api/v1/fairness/reports/summary", params={"company_id": COMPANY_B})
        assert captured == [COMPANY_A, COMPANY_B]


# ----------------- /fairness/reports/trend -----------------

class TestFairnessTrend:
    def test_happy_returns_time_series(self, app: FastAPI):
        rows = [
            SimpleNamespace(day="2026-04-01", blocks=2, warnings=1),
            SimpleNamespace(day="2026-04-02", blocks=0, warnings=3),
        ]
        repo_mock = MagicMock()
        repo_mock.get_daily_trend = AsyncMock(return_value=rows)
        with patch(
            "app.api.v1.fairness_reports.FairnessReportRepository",
            return_value=repo_mock,
        ):
            client = TestClient(app, raise_server_exceptions=False)
            r = client.get("/api/v1/fairness/reports/trend", params={"days": 30})
        assert r.status_code == 200
        body = r.json()
        assert body["period_days"] == 30
        assert len(body["trend"]) == 2

    def test_below_min_days_returns_422(self, app: FastAPI):
        client = TestClient(app, raise_server_exceptions=False)
        # min=7 per Query constraint
        r = client.get("/api/v1/fairness/reports/trend", params={"days": 1})
        assert r.status_code == 422

    def test_company_id_isolated_per_request(self, app: FastAPI):
        captured: list[str | None] = []

        async def _spy(since, company_id):
            captured.append(company_id)
            return []

        repo_mock = MagicMock()
        repo_mock.get_daily_trend = _spy
        with patch(
            "app.api.v1.fairness_reports.FairnessReportRepository",
            return_value=repo_mock,
        ):
            client = TestClient(app, raise_server_exceptions=False)
            client.get("/api/v1/fairness/reports/trend", params={"company_id": COMPANY_A})
            client.get("/api/v1/fairness/reports/trend", params={"company_id": COMPANY_B})
        assert captured == [COMPANY_A, COMPANY_B]


# ----------------- /fairness/audit/logs -----------------

class TestFairnessAuditLogs:
    def test_happy_returns_paginated(self, app: FastAPI):
        row = SimpleNamespace(
            id=uuid4(),
            category="age",
            is_blocked=True,
            blocked_terms=["jovem"],
            soft_warnings=None,
            context="search_query",
            recruiter_id=uuid4(),
            job_id=uuid4(),
            created_at=datetime.now(UTC),
        )
        repo_mock = MagicMock()
        repo_mock.get_audit_logs_paginated = AsyncMock(return_value=(1, [row]))
        with patch(
            "app.api.v1.fairness_reports.FairnessReportRepository",
            return_value=repo_mock,
        ):
            client = TestClient(app, raise_server_exceptions=False)
            r = client.get("/api/v1/fairness/audit/logs")
        assert r.status_code == 200
        body = r.json()
        assert body["total"] == 1
        assert body["items"][0]["category"] == "age"
        assert body["items"][0]["is_blocked"] is True

    def test_limit_above_max_returns_422(self, app: FastAPI):
        client = TestClient(app, raise_server_exceptions=False)
        r = client.get("/api/v1/fairness/audit/logs", params={"limit": 999})
        assert r.status_code == 422

    def test_company_filter_passed_to_repo(self, app: FastAPI):
        captured: dict = {}

        async def _spy(*, since, company_id, category, blocked_only, limit, offset):
            captured["company_id"] = company_id
            captured["category"] = category
            captured["blocked_only"] = blocked_only
            return (0, [])

        repo_mock = MagicMock()
        repo_mock.get_audit_logs_paginated = _spy
        with patch(
            "app.api.v1.fairness_reports.FairnessReportRepository",
            return_value=repo_mock,
        ):
            client = TestClient(app, raise_server_exceptions=False)
            r = client.get(
                "/api/v1/fairness/audit/logs",
                params={
                    "company_id": COMPANY_B,
                    "category": "gender",
                    "blocked_only": "true",
                },
            )
        assert r.status_code == 200
        assert captured["company_id"] == COMPANY_B
        assert captured["category"] == "gender"
        assert captured["blocked_only"] is True
