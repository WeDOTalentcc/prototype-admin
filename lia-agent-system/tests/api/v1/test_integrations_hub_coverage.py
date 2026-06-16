"""
Coverage tests for app/api/v1/integrations_hub.py — Task #930.

Cobre os principais endpoints do hub de integrações:
- GET  /integrations/providers (lista) e /providers/{category} (filtro inválido)
- GET  /integrations/connections
- PUT  /integrations/connections/{id} (verify_connection_ownership cross-tenant)
- DELETE /integrations/connections/{id}
- POST /integrations/connections/{id}/test
"""
from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.integrations_hub import router
from app.auth.dependencies import get_current_user_or_demo
from app.auth.models import User
from app.domains.integrations_hub.dependencies import get_integrations_hub_repo


COMPANY_A = "11111111-1111-1111-1111-111111111111"
COMPANY_B = "22222222-2222-2222-2222-222222222222"


def _user_in(company_id: str) -> MagicMock:
    """Mock user whose JWT-derived company matches `company_id` (Onda 36 guards)."""
    u = MagicMock(spec=User)
    u.id = f"user-{company_id}"
    u.email = f"user@{company_id}.test"
    u.company_id = company_id
    u.role = "user"
    u.is_active = True
    u.can_access_company = lambda cid: cid == company_id
    return u
CONN_ID = "33333333-3333-3333-3333-333333333333"
PROVIDER_ID = "44444444-4444-4444-4444-444444444444"


def _provider() -> SimpleNamespace:
    return SimpleNamespace(
        id=PROVIDER_ID,
        name="HRIS",
        category="hris",
        slug="hris",
        description=None,
        logo_url=None,
        supports_oauth=True,
        supports_api_key=False,
        supports_webhook=False,
        features=[],
        is_active=True,
        is_premium=False,
    )


def _connection(company_id: str = COMPANY_A) -> SimpleNamespace:
    return SimpleNamespace(
        id=CONN_ID,
        company_id=company_id,
        provider_id=PROVIDER_ID,
        status="connected",
        auth_type="oauth",
        sync_enabled=True,
        sync_direction="bidirectional",
        sync_frequency="realtime",
        last_sync_at=None,
        last_sync_status=None,
        health_score=1.0,
        error_count=0,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


@pytest.fixture
def repo() -> MagicMock:
    r = MagicMock()
    r.list_providers = AsyncMock(return_value=[_provider()])
    r.seed_default_providers = AsyncMock(return_value=[_provider()])
    r.list_connections = AsyncMock(return_value=[(_connection(), _provider())])
    r.get_connection_by_id = AsyncMock(return_value=_connection())
    r.get_connection_with_provider = AsyncMock(return_value=(_connection(), _provider()))
    r.update_connection = AsyncMock(return_value=_connection())
    r.delete_connection = AsyncMock()
    r.mark_connection_tested = AsyncMock()
    r.rollback = AsyncMock()
    return r


@pytest.fixture
def app(repo: MagicMock) -> FastAPI:
    application = FastAPI()
    application.include_router(router, prefix="/api/v1")
    application.dependency_overrides[get_integrations_hub_repo] = lambda: repo
    # Onda 36: tenant guards exigem current_user; default = COMPANY_A para os happy paths.
    # Testes cross-tenant podem sobrepor explicitamente para COMPANY_B.
    application.dependency_overrides[get_current_user_or_demo] = lambda: _user_in(COMPANY_A)
    return application


# ----------------- /providers -----------------

class TestProviders:
    def test_list_providers_happy(self, app: FastAPI):
        client = TestClient(app, raise_server_exceptions=False)
        r = client.get("/api/v1/integrations/providers")
        assert r.status_code == 200
        body = r.json()
        assert isinstance(body, list)
        assert body[0]["slug"] == "hris"

    def test_invalid_category_returns_400(self, app: FastAPI):
        client = TestClient(app, raise_server_exceptions=False)
        r = client.get("/api/v1/integrations/providers/__not_a_category__")
        assert r.status_code == 400


# ----------------- /connections list (cross-tenant via query) -----------------

class TestListConnections:
    def test_company_id_query_passed_to_repo(self, app: FastAPI, repo: MagicMock):
        """Onda 36: query company_id is passed to repo — but only when authz allows.

        Cross-tenant case (COMPANY_B with COMPANY_A user) returns 403 (correct
        behavior post-Onda 36). Same-tenant case captures company_id at repo level.
        """
        captured: list[str] = []

        async def _spy(*, company_id, status=None, category=None):
            captured.append(company_id)
            return [(_connection(company_id), _provider())]

        repo.list_connections = _spy
        client = TestClient(app, raise_server_exceptions=False)

        # Same-tenant: 200 + repo receives COMPANY_A
        r1 = client.get("/api/v1/integrations/connections", params={"company_id": COMPANY_A})
        assert r1.status_code == 200, r1.text
        assert captured == [COMPANY_A]

        # Cross-tenant: 403 (Onda 36 guard) — repo NOT called
        r2 = client.get("/api/v1/integrations/connections", params={"company_id": COMPANY_B})
        assert r2.status_code == 403, r2.text
        assert captured == [COMPANY_A]  # unchanged

    def test_missing_company_id_returns_422(self, app: FastAPI):
        client = TestClient(app, raise_server_exceptions=False)
        r = client.get("/api/v1/integrations/connections")
        assert r.status_code == 422


# ----------------- /connections/{id} update / delete (cross-tenant guard) -----------------

class TestConnectionUpdate:
    def test_update_happy(self, app: FastAPI):
        client = TestClient(app, raise_server_exceptions=False)
        r = client.put(
            f"/api/v1/integrations/connections/{CONN_ID}",
            params={"company_id": COMPANY_A},
            json={"sync_enabled": False},
        )
        assert r.status_code == 200
        assert r.json()["id"] == CONN_ID

    def test_update_other_tenant_returns_403(self, app: FastAPI, repo: MagicMock):
        # Connection belongs to A — request says B.
        repo.get_connection_with_provider = AsyncMock(
            return_value=(_connection(COMPANY_A), _provider())
        )
        client = TestClient(app, raise_server_exceptions=False)
        r = client.put(
            f"/api/v1/integrations/connections/{CONN_ID}",
            params={"company_id": COMPANY_B},
            json={"sync_enabled": False},
        )
        assert r.status_code == 403

    def test_update_not_found_returns_404(self, app: FastAPI, repo: MagicMock):
        repo.get_connection_with_provider = AsyncMock(return_value=None)
        client = TestClient(app, raise_server_exceptions=False)
        r = client.put(
            f"/api/v1/integrations/connections/{CONN_ID}",
            params={"company_id": COMPANY_A},
            json={"sync_enabled": False},
        )
        assert r.status_code == 404


class TestConnectionDelete:
    def test_delete_happy(self, app: FastAPI):
        client = TestClient(app, raise_server_exceptions=False)
        r = client.delete(
            f"/api/v1/integrations/connections/{CONN_ID}",
            params={"company_id": COMPANY_A},
        )
        assert r.status_code == 200

    def test_delete_other_tenant_returns_403(self, app: FastAPI, repo: MagicMock):
        repo.get_connection_by_id = AsyncMock(return_value=_connection(COMPANY_A))
        client = TestClient(app, raise_server_exceptions=False)
        r = client.delete(
            f"/api/v1/integrations/connections/{CONN_ID}",
            params={"company_id": COMPANY_B},
        )
        assert r.status_code == 403


class TestConnectionTest:
    def test_test_happy(self, app: FastAPI):
        client = TestClient(app, raise_server_exceptions=False)
        r = client.post(
            f"/api/v1/integrations/connections/{CONN_ID}/test",
            params={"company_id": COMPANY_A},
        )
        assert r.status_code == 200
        assert r.json()["status"] == "connected"

    def test_test_other_tenant_returns_403(self, app: FastAPI, repo: MagicMock):
        repo.get_connection_with_provider = AsyncMock(
            return_value=(_connection(COMPANY_A), _provider())
        )
        client = TestClient(app, raise_server_exceptions=False)
        r = client.post(
            f"/api/v1/integrations/connections/{CONN_ID}/test",
            params={"company_id": COMPANY_B},
        )
        assert r.status_code == 403
