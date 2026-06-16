"""
Unit tests for /api/v1/rails/health and /api/v1/rails/status (PE-10).

These tests validate the contract of the Rails health endpoints WITHOUT
requiring a live Rails service. They mock the adapter.health_check call
so CI can detect:
  - Schema breakage in the response
  - Import errors in the rails module chain
  - Circuit breaker integration regressions
"""
import pytest
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient, ASGITransport

from app.main import app


@pytest.fixture(autouse=True)
def _override_tenant_db(monkeypatch):
    """Override get_tenant_db to avoid DB connection in unit tests."""
    from unittest.mock import AsyncMock, MagicMock
    from app.core.database import get_tenant_db
    from app.domains.integrations_hub.services.rails_adapter_dependency import get_rails_adapter

    async def _fake_db():
        mock_session = MagicMock()
        mock_session.__aenter__ = AsyncMock(return_value=MagicMock())
        mock_session.__aexit__ = AsyncMock(return_value=False)
        yield mock_session

    app.dependency_overrides[get_tenant_db] = _fake_db
    yield
    app.dependency_overrides.pop(get_tenant_db, None)


@pytest.mark.asyncio
async def test_rails_health_when_disabled():
    """When RAILS_API_URL is not set, endpoint returns status=disabled."""
    fake_health = {
        "rails_enabled": False,
        "status": "disabled",
        "message": "RAILS_API_URL not configured",
        "circuit_breaker": {"state": "CLOSED", "failure_count": 0},
    }
    with patch(
        "app.domains.integrations_hub.services.rails_adapter.RailsAdapter.health_check",
        new=AsyncMock(return_value=fake_health),
    ):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.get("/api/v1/rails/health")

    assert resp.status_code == 200
    data = resp.json()
    assert "rails_enabled" in data
    assert "status" in data
    assert "circuit_breaker" in data
    assert "field_mappings" in data


@pytest.mark.asyncio
async def test_rails_health_when_healthy():
    """When Rails is reachable, endpoint returns status=ok."""
    fake_health = {
        "rails_enabled": True,
        "status": "ok",
        "latency_ms": 42,
        "circuit_breaker": {"state": "CLOSED", "failure_count": 0},
    }
    with patch(
        "app.domains.integrations_hub.services.rails_adapter.RailsAdapter.health_check",
        new=AsyncMock(return_value=fake_health),
    ):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.get("/api/v1/rails/health")

    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["rails_enabled"] is True
    assert data["circuit_breaker"]["state"] == "CLOSED"


@pytest.mark.asyncio
async def test_rails_status_requires_auth():
    """/rails/status is NOT in PUBLIC_PREFIXES — requires auth by design.

    /health is public (for infra monitoring with service token).
    /status exposes circuit breaker internals, so it requires user auth.
    """
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        # No Authorization header — expect 401 (proves auth enforcement works)
        resp = await client.get("/api/v1/rails/status")

    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_rails_health_does_not_require_auth():
    """/rails/health is intentionally public for monitoring tools."""
    fake_health = {
        "rails_enabled": False,
        "status": "disabled",
        "message": "test",
        "circuit_breaker": {"state": "CLOSED", "failure_count": 0},
    }
    with patch(
        "app.domains.integrations_hub.services.rails_adapter.RailsAdapter.health_check",
        new=AsyncMock(return_value=fake_health),
    ):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            # No Authorization header — must still return 200 (not 401)
            resp = await client.get("/api/v1/rails/health")
    assert resp.status_code == 200
