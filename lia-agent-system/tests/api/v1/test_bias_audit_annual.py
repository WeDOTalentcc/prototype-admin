"""
Coverage tests for app/api/v1/bias_audit_annual.py — Wave 1 Agent #1.

Cobre os 3 endpoints T-17 NYC LL144:
- POST  /api/v1/bias-audit/annual/generate
- GET   /api/v1/bias-audit/annual/{report_id}
- PATCH /api/v1/bias-audit/annual/{report_id}/publish
"""
from __future__ import annotations

from datetime import UTC, date, datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.bias_audit_annual import router
from app.core.database import get_db
from app.shared.security.require_company_id import require_company_id
from app.shared.tenant_guard import get_verified_company_id


COMPANY_A = "11111111-1111-1111-1111-111111111111"
REPORT_ID = "77777777-7777-7777-7777-777777777777"


def _mock_db_with_commit() -> MagicMock:
    db = MagicMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.add = MagicMock()
    return db


@pytest.fixture
def app() -> FastAPI:
    application = FastAPI()
    application.include_router(router, prefix="/api/v1")
    db_mock = _mock_db_with_commit()
    application.dependency_overrides[get_db] = lambda: db_mock
    application.dependency_overrides[require_company_id] = lambda: COMPANY_A
    application.dependency_overrides[get_verified_company_id] = lambda: COMPANY_A
    return application


def _mock_report_row(*, is_public: bool = False) -> MagicMock:
    r = MagicMock()
    r.id = UUID(REPORT_ID)
    r.company_id = UUID(COMPANY_A)
    r.audit_type = "annual_ll144"
    r.audit_date = date(2026, 1, 15)
    r.sample_size = 100
    r.bias_results = {
        "year": 2025,
        "dimensions": [
            {
                "dimension": "gender",
                "groups": {"M": {"selected": 30}, "F": {"selected": 28}},
                "adverse_impact_ratio": 0.93,
                "below_threshold": False,
                "alert_level": "ok",
            }
        ],
        "four_fifths_results": {"gender": True, "age_group": True},
        "chi_square": [
            {"dimension": "gender", "chi2": 0.85, "p_value": 0.36, "significant": False, "available": True}
        ],
        "decision_outcomes": [
            {"stage": "screening", "total": 100, "selected": 58, "rejected": 30, "pending": 12, "selection_rate": 0.58}
        ],
        "eeoc_4_fifths_pass": True,
    }
    r.overall_score = 92.5
    r.is_public = is_public
    r.report_url = "/trust-center/bias-audits/abc" if is_public else None
    r.compliance_frameworks = ["NYC_LL144", "EU_AI_ACT", "LGPD_BRAZIL"]
    r.auditor = "internal"
    r.auditor_name = None
    r.recommendations = []
    r.notes = "Annual NYC LL144 bias audit for year 2025"
    r.created_at = datetime.now(UTC)
    return r


# ───────────────────────── POST /annual/generate ────────────────────────────


class TestGenerateAnnualBiasAudit:
    def test_enqueues_report_with_canonical_audit_type(self, app: FastAPI):
        """REGRA: deve enqueue com audit_type=annual_ll144 + status=queued."""
        # When db.add is called, simulate refresh setting id
        mock_db = _mock_db_with_commit()

        async def _refresh(report):
            # Simulate ORM populating id after commit
            if not getattr(report, "id", None):
                report.id = uuid4()

        mock_db.refresh = AsyncMock(side_effect=_refresh)
        app.dependency_overrides[get_db] = lambda: mock_db

        client = TestClient(app, raise_server_exceptions=False)
        r = client.post(
            "/api/v1/bias-audit/annual/generate",
            json={"year": 2025, "scope": "company_wide", "include_subgroups": True},
        )
        assert r.status_code == 202, r.text
        body = r.json()
        assert body["status"] == "queued"
        assert body["audit_type"] == "annual_ll144"
        assert body["year"] == 2025
        assert "report_id" in body
        assert "estimated_completion" in body
        mock_db.add.assert_called_once()
        mock_db.commit.assert_awaited()

    def test_year_out_of_range_returns_422(self, app: FastAPI):
        client = TestClient(app, raise_server_exceptions=False)
        r = client.post(
            "/api/v1/bias-audit/annual/generate",
            json={"year": 1999, "scope": "company_wide"},
        )
        assert r.status_code == 422

    def test_extra_field_rejected_by_pydantic_forbid(self, app: FastAPI):
        """REGRA Pydantic R1: WeDoBaseModel forbid extra fields."""
        client = TestClient(app, raise_server_exceptions=False)
        r = client.post(
            "/api/v1/bias-audit/annual/generate",
            json={
                "year": 2025,
                "scope": "company_wide",
                "phantom_field": "should-fail",
            },
        )
        assert r.status_code == 422


# ───────────────────────── GET /annual/{report_id} ──────────────────────────


class TestGetAnnualBiasAudit:
    def test_returns_canonical_payload_with_dimensions(self, app: FastAPI):
        mock_db = MagicMock()
        get_result = MagicMock()
        get_result.scalar_one_or_none = MagicMock(return_value=_mock_report_row())
        mock_db.execute = AsyncMock(return_value=get_result)
        app.dependency_overrides[get_db] = lambda: mock_db

        client = TestClient(app, raise_server_exceptions=False)
        r = client.get(f"/api/v1/bias-audit/annual/{REPORT_ID}")
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["report_id"] == REPORT_ID
        assert body["audit_type"] == "annual_ll144"
        assert body["year"] == 2025
        assert body["company_id"] == COMPANY_A
        assert body["eeoc_4_fifths_pass"] is True
        assert len(body["dimensions"]) == 1
        assert body["dimensions"][0]["dimension"] == "gender"
        assert len(body["chi_square"]) == 1
        assert len(body["decision_outcomes"]) == 1
        assert "NYC_LL144" in body["compliance_frameworks"]

    def test_404_when_report_not_in_tenant(self, app: FastAPI):
        mock_db = MagicMock()
        get_result = MagicMock()
        get_result.scalar_one_or_none = MagicMock(return_value=None)
        mock_db.execute = AsyncMock(return_value=get_result)
        app.dependency_overrides[get_db] = lambda: mock_db

        client = TestClient(app, raise_server_exceptions=False)
        r = client.get(f"/api/v1/bias-audit/annual/{REPORT_ID}")
        assert r.status_code == 404

    def test_invalid_uuid_returns_422(self, app: FastAPI):
        client = TestClient(app, raise_server_exceptions=False)
        r = client.get("/api/v1/bias-audit/annual/not-a-uuid")
        assert r.status_code == 422


# ───────────────────────── PATCH /annual/{report_id}/publish ────────────────


class TestPublishAnnualBiasAudit:
    def test_publish_sets_public_url(self, app: FastAPI):
        """REGRA: Trust Portal toggle gera public_url canonical."""
        row = _mock_report_row(is_public=False)
        mock_db = _mock_db_with_commit()
        get_result = MagicMock()
        get_result.scalar_one_or_none = MagicMock(return_value=row)
        mock_db.execute = AsyncMock(return_value=get_result)

        # Refresh just commits values
        async def _refresh(r):
            return None

        mock_db.refresh = AsyncMock(side_effect=_refresh)
        app.dependency_overrides[get_db] = lambda: mock_db

        client = TestClient(app, raise_server_exceptions=False)
        r = client.patch(
            f"/api/v1/bias-audit/annual/{REPORT_ID}/publish",
            json={"is_public": True, "public_url_slug": "abc-2025"},
        )
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["report_id"] == REPORT_ID
        assert body["is_public"] is True
        assert body["public_url"] == "/trust-center/bias-audits/abc-2025"
        assert body["published_at"] is not None

    def test_unpublish_clears_public_url(self, app: FastAPI):
        row = _mock_report_row(is_public=True)
        mock_db = _mock_db_with_commit()
        get_result = MagicMock()
        get_result.scalar_one_or_none = MagicMock(return_value=row)
        mock_db.execute = AsyncMock(return_value=get_result)
        mock_db.refresh = AsyncMock()
        app.dependency_overrides[get_db] = lambda: mock_db

        client = TestClient(app, raise_server_exceptions=False)
        r = client.patch(
            f"/api/v1/bias-audit/annual/{REPORT_ID}/publish",
            json={"is_public": False},
        )
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["is_public"] is False
        assert body["public_url"] is None
        assert body["published_at"] is None

    def test_404_when_report_not_in_tenant(self, app: FastAPI):
        mock_db = MagicMock()
        get_result = MagicMock()
        get_result.scalar_one_or_none = MagicMock(return_value=None)
        mock_db.execute = AsyncMock(return_value=get_result)
        app.dependency_overrides[get_db] = lambda: mock_db
        client = TestClient(app, raise_server_exceptions=False)
        r = client.patch(
            f"/api/v1/bias-audit/annual/{REPORT_ID}/publish",
            json={"is_public": True},
        )
        assert r.status_code == 404

    def test_invalid_slug_rejected(self, app: FastAPI):
        """REGRA Pydantic: slug pattern ^[a-z0-9-]*$ canonical."""
        client = TestClient(app, raise_server_exceptions=False)
        r = client.patch(
            f"/api/v1/bias-audit/annual/{REPORT_ID}/publish",
            json={"is_public": True, "public_url_slug": "Invalid Slug!"},
        )
        assert r.status_code == 422
