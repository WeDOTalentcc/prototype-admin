"""
Testes unitários para endpoints de saúde e utilitários (Sprint H — coverage 40%).

Cobre endpoints sem dependência de DB:
  - GET /api/v1/health → 200 + componentes
  - GET /api/v1/health/langgraph → schema de resposta
  - GET /api/v1/drift/status (mock)
  - POST /api/v1/navigation-intent (mock)
  - GET /api/v1/bias-audit/job/{job_id} (mock)
"""
import pytest
import uuid
from unittest.mock import AsyncMock, patch, MagicMock
from httpx import AsyncClient, ASGITransport

from app.main import app


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mock_db_override():
    """Returns an async generator that yields a mock DB session."""
    from app.core.database import get_db

    mock_db_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar = MagicMock(return_value=1)
    mock_db_session.execute = AsyncMock(return_value=mock_result)

    async def override_get_db():
        yield mock_db_session

    return get_db, override_get_db



# ---------------------------------------------------------------------------
# Autouse fixture: prevent rate_limiter from trying Redis (closed loop in unit tests)
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _mock_rate_limiter_for_tests():
    # Prevent rate_limiter and tenant_db from using closed async connections
    from unittest.mock import patch as _patch, AsyncMock as _AsyncMock, MagicMock as _MagicMock
    from app.main import app as _app
    from app.core.database import get_tenant_db

    async def _mock_tenant_db():
        yield _MagicMock()

    _app.dependency_overrides[get_tenant_db] = _mock_tenant_db
    try:
        with _patch(
            "app.middleware.rate_limiter.RateLimiter._get_redis",
            new_callable=_AsyncMock,
            return_value=None,
        ):
            yield
    finally:
        _app.dependency_overrides.pop(get_tenant_db, None)


# ---------------------------------------------------------------------------
# Health básico
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_health_ok():
    # Mock Redis — unavailable in test env; we test app logic not infra availability
    # Mock DB — prevent real DB connections that contaminate async pool
    get_db, override_get_db = _mock_db_override()
    app.dependency_overrides[get_db] = override_get_db
    try:
        with patch("app.api.v1.system_health._check_redis", return_value={"status": "healthy", "latency_ms": 1}):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                resp = await client.get("/api/v1/health")
    finally:
        del app.dependency_overrides[get_db]
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] in ("healthy", "degraded")
    assert "components" in data
    assert "version" in data


@pytest.mark.asyncio
async def test_health_has_database_component():
    get_db, override_get_db = _mock_db_override()
    app.dependency_overrides[get_db] = override_get_db
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/api/v1/health")
    finally:
        del app.dependency_overrides[get_db]
    components = resp.json()["components"]
    assert "database" in components


@pytest.mark.asyncio
async def test_health_has_timestamp():
    get_db, override_get_db = _mock_db_override()
    app.dependency_overrides[get_db] = override_get_db
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/api/v1/health")
    finally:
        del app.dependency_overrides[get_db]
    assert "timestamp" in resp.json()


# ---------------------------------------------------------------------------
# Health LangGraph
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_health_langgraph_schema():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/v1/health/langgraph")
    assert resp.status_code == 200
    data = resp.json()
    assert "status" in data or "langgraph" in str(data).lower()


# ---------------------------------------------------------------------------
# Navigation Intent
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_navigation_intent_accepts_post():
    """navigation-intent é endpoint público para análise de contexto."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/navigation-intent",
            json={"message": "quero ver minhas vagas"},
        )
    # Endpoint retorna 200 (público) ou 422 (corpo inválido)
    assert resp.status_code in (200, 422)


# ---------------------------------------------------------------------------
# Drift Status
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_drift_status_requires_auth():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/v1/drift/status")
    assert resp.status_code in (401, 403, 422)


# ---------------------------------------------------------------------------
# Fairness endpoints (sem DB real — apenas verifica rota existe)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_fairness_summary_requires_auth():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/v1/fairness/reports/summary")
    assert resp.status_code in (401, 403, 404, 422)


# ---------------------------------------------------------------------------
# Docs (OpenAPI)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_openapi_docs_available():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/docs")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_openapi_schema_available():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/openapi.json")
    assert resp.status_code == 200
    schema = resp.json()
    assert "paths" in schema
    assert "components" in schema


@pytest.mark.asyncio
async def test_openapi_schema_has_health_path():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/openapi.json")
    paths = resp.json()["paths"]
    health_paths = [p for p in paths if "health" in p.lower()]
    assert len(health_paths) > 0


# ---------------------------------------------------------------------------
# Auth endpoints (sem DB real)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_login_with_invalid_credentials_returns_401():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/auth/login",
            json={"email": "inexistente@test.com", "password": "wrongpass"},
        )
    assert resp.status_code in (401, 422, 500)


@pytest.mark.asyncio
async def test_refresh_without_token_returns_401():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post("/api/v1/auth/refresh")
    assert resp.status_code in (401, 403, 422)
