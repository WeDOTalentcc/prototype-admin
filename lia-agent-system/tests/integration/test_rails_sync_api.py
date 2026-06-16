"""
Integration tests for Rails Sync API endpoints.
Uses TestClient + dependency_overrides — no real database needed.
Targets:
  - app/api/v1/rails_sync.py (all 4 endpoints)
  - app/api/v1/rails_health.py (2 endpoints)

Tests cover:
  - Auth rejection without valid token
  - Auth acceptance with valid token
  - Response format validation for each endpoint
  - Rate limiting behavior (including 429 on limit breach)
  - Bulk sync validation (size limits, invalid input)
"""
import os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.core.database import get_db

UUID1 = "123e4567-e89b-12d3-a456-426614174000"
UUID2 = "223e4567-e89b-12d3-a456-426614174001"
TEST_TOKEN = "test-rails-token-12345"


def make_mock_db():
    session = AsyncMock(spec=AsyncSession)
    mock_result = MagicMock()
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = []
    mock_scalars.first.return_value = None
    mock_result.scalars.return_value = mock_scalars
    mock_result.scalar_one_or_none.return_value = None
    mock_result.scalar.return_value = 0
    mock_result.first.return_value = None
    session.execute = AsyncMock(return_value=mock_result)
    session.get = AsyncMock(return_value=None)
    session.add = MagicMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.delete = AsyncMock()
    session.rollback = AsyncMock()
    session.flush = AsyncMock()
    return session


_mock_db_factory = None


def get_mock_db():
    if _mock_db_factory:
        yield _mock_db_factory()
    else:
        yield make_mock_db()


@pytest.fixture(scope="module")
def client():
    app.dependency_overrides[get_db] = get_mock_db
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def reset_rate_limits():
    from app.api.v1 import rails_sync
    rails_sync._rate_limit_counts.clear()
    yield
    rails_sync._rate_limit_counts.clear()


@pytest.fixture(autouse=True)
def set_token():
    from app.api.v1 import rails_sync
    original_fn = rails_sync._get_rails_api_token
    rails_sync._get_rails_api_token = lambda: TEST_TOKEN
    yield
    rails_sync._get_rails_api_token = original_fn


def _auth_header(token=TEST_TOKEN):
    return {"Authorization": f"Bearer {token}"}


class TestRailsSyncAuth:

    def test_rejects_no_token_on_enrichment(self, client):
        resp = client.get(f"/api/v1/rails-sync/candidates/{UUID1}/enrichment")
        assert resp.status_code in (401, 403)

    def test_rejects_wrong_token_on_enrichment(self, client):
        resp = client.get(
            f"/api/v1/rails-sync/candidates/{UUID1}/enrichment",
            headers=_auth_header("wrong-token"),
        )
        assert resp.status_code == 401

    def test_accepts_valid_token_on_enrichment(self, client):
        resp = client.get(
            f"/api/v1/rails-sync/candidates/{UUID1}/enrichment",
            headers=_auth_header(),
        )
        assert resp.status_code in (200, 404)

    def test_rejects_no_token_on_intelligence(self, client):
        resp = client.get(f"/api/v1/rails-sync/jobs/{UUID1}/intelligence")
        assert resp.status_code in (401, 403)

    def test_rejects_no_token_on_compliance(self, client):
        resp = client.get("/api/v1/rails-sync/compliance/status")
        assert resp.status_code in (401, 403)

    def test_rejects_no_token_on_bulk_sync(self, client):
        resp = client.post(
            "/api/v1/rails-sync/bulk-sync/candidates",
            json={"candidate_ids": [UUID1]},
        )
        assert resp.status_code in (401, 403)

    def test_sync_disabled_when_no_token_configured(self, client):
        from app.api.v1 import rails_sync
        rails_sync._get_rails_api_token = lambda: ""
        resp = client.get(
            f"/api/v1/rails-sync/candidates/{UUID1}/enrichment",
            headers=_auth_header("some-token"),
        )
        assert resp.status_code == 503
        body = resp.json()
        assert "not configured" in body.get("message", "").lower()
        rails_sync._get_rails_api_token = lambda: TEST_TOKEN


class TestCandidateEnrichment:

    def test_candidate_not_found_returns_404(self, client):
        resp = client.get(
            f"/api/v1/rails-sync/candidates/{UUID1}/enrichment",
            headers=_auth_header(),
        )
        assert resp.status_code == 404

    def test_candidate_found_returns_enrichment(self, client):
        global _mock_db_factory
        mock_candidate = MagicMock()
        mock_candidate.name = "Maria Silva"
        mock_candidate.email = "maria@test.com"
        mock_candidate.status = "active"
        mock_candidate.wsi_score = 4.2
        mock_candidate.wsi_report = {"summary": "Good"}
        mock_candidate.screening_result = {"passed": True}
        mock_candidate.ai_summary = "Strong candidate"
        mock_candidate.skills_extracted = ["Python", "React"]
        mock_candidate.embedding_vector = [0.1, 0.2]

        def db_factory():
            mock_db = make_mock_db()
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_candidate
            mock_db.execute = AsyncMock(return_value=mock_result)
            return mock_db

        _mock_db_factory = db_factory
        try:
            resp = client.get(
                f"/api/v1/rails-sync/candidates/{UUID1}/enrichment",
                headers=_auth_header(),
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["candidate_id"] == UUID1
            assert data["name"] == "Maria Silva"
            assert data["source"] == "fastapi"
            assert "synced_at" in data
            assert data["wsi"]["wsi_score"] == 4.2
            assert data["ai_insights"]["ai_summary"] == "Strong candidate"
            assert data["ai_insights"]["has_embedding"] is True
        finally:
            _mock_db_factory = None


class TestJobIntelligence:

    def test_job_not_found_returns_404(self, client):
        resp = client.get(
            f"/api/v1/rails-sync/jobs/{UUID1}/intelligence",
            headers=_auth_header(),
        )
        assert resp.status_code == 404

    def test_job_found_returns_intelligence(self, client):
        global _mock_db_factory
        mock_job = MagicMock()
        mock_job.title = "Senior Developer"
        mock_job.status = "active"
        mock_job.company_id = "company-1"
        mock_job.sourcing_channels = ["linkedin", "github"]
        mock_job.market_candidates = 500
        mock_job.saturation_score = 0.75

        def db_factory():
            mock_db = make_mock_db()
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_job
            mock_db.execute = AsyncMock(return_value=mock_result)
            return mock_db

        _mock_db_factory = db_factory
        try:
            resp = client.get(
                f"/api/v1/rails-sync/jobs/{UUID1}/intelligence",
                headers=_auth_header(),
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["job_id"] == UUID1
            assert data["title"] == "Senior Developer"
            assert data["source"] == "fastapi"
            assert data["sourcing_data"]["channels"] == ["linkedin", "github"]
            assert data["saturation"]["saturation_score"] == 0.75
        finally:
            _mock_db_factory = None


class TestComplianceStatus:

    def test_compliance_returns_status(self, client):
        resp = client.get(
            "/api/v1/rails-sync/compliance/status",
            headers=_auth_header(),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["lgpd"]["status"] == "compliant"
        assert data["lgpd"]["pii_masking_enabled"] is True
        assert data["audit"]["fairness_guard_active"] is True
        assert "platform_stats" in data
        assert data["source"] == "fastapi"


class TestBulkSync:

    def test_bulk_sync_empty_ids_returns_400(self, client):
        resp = client.post(
            "/api/v1/rails-sync/bulk-sync/candidates",
            json={"candidate_ids": []},
            headers=_auth_header(),
        )
        assert resp.status_code == 400

    def test_bulk_sync_exceeds_max_returns_400(self, client):
        ids = [f"id-{i}" for i in range(51)]
        resp = client.post(
            "/api/v1/rails-sync/bulk-sync/candidates",
            json={"candidate_ids": ids},
            headers=_auth_header(),
        )
        assert resp.status_code == 400
        body = resp.json()
        assert "50" in body.get("message", "")

    def test_bulk_sync_non_list_returns_400(self, client):
        resp = client.post(
            "/api/v1/rails-sync/bulk-sync/candidates",
            json={"candidate_ids": "not-a-list"},
            headers=_auth_header(),
        )
        assert resp.status_code == 400

    def test_bulk_sync_valid_returns_enrichments(self, client):
        resp = client.post(
            "/api/v1/rails-sync/bulk-sync/candidates",
            json={"candidate_ids": [UUID1, UUID2]},
            headers=_auth_header(),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_requested"] == 2
        assert data["source"] == "fastapi"
        assert "enrichments" in data
        assert "missing_ids" in data


class TestRailsHealth:

    def test_health_endpoint_accessible(self, client):
        resp = client.get("/api/v1/rails/health")
        assert resp.status_code in (200, 500)

    def test_status_endpoint_returns_circuit_info(self, client):
        resp = client.get("/api/v1/rails/status")
        assert resp.status_code == 200
        data = resp.json()
        assert "circuit" in data
        assert "rails_url" in data
        assert "service_token_configured" in data


class TestRateLimiting:

    def test_rate_limit_allows_normal_traffic(self, client):
        for _ in range(5):
            resp = client.get(
                "/api/v1/rails-sync/compliance/status",
                headers=_auth_header(),
            )
            assert resp.status_code == 200

    def test_rate_limit_returns_429_on_breach(self, client):
        from app.api.v1 import rails_sync
        import time
        now = time.time()
        rails_sync._rate_limit_counts["rails"] = [now] * 120
        resp = client.get(
            "/api/v1/rails-sync/compliance/status",
            headers=_auth_header(),
        )
        assert resp.status_code == 429
        body = resp.json()
        assert "rate limit" in body.get("message", "").lower()
