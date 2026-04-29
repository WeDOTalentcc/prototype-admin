"""
Coverage tests for app/api/v1/webhooks.py — Task #930.

Cobre os 6 endpoints do hub de Webhooks:
- GET    /webhooks/events            (catálogo público)
- POST   /webhooks                   (criar)
- GET    /webhooks                   (listar por company)
- PATCH  /webhooks/{id}              (atualizar)
- DELETE /webhooks/{id}              (deletar)
- POST   /webhooks/{id}/test         (test send)

Por endpoint, tripé happy + erro + isolamento (cross-tenant via override do
current_user — `require_role([admin])` lê company_id do user retornado, então
listar/criar/atualizar/deletar usam o tenant do sujeito autenticado, nunca
um company_id arbitrário do client).
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from app.api.v1.webhooks import router
from app.auth.dependencies import get_current_active_user, get_current_user
from app.auth.models import UserRole
from app.core.database import get_db


COMPANY_A = "11111111-1111-1111-1111-111111111111"
COMPANY_B = "22222222-2222-2222-2222-222222222222"
WEBHOOK_ID = "33333333-3333-3333-3333-333333333333"


def _user(company_id: str, role: UserRole = UserRole.admin) -> MagicMock:
    u = MagicMock()
    u.id = uuid4()
    u.email = f"user@{company_id}.test"
    u.company_id = company_id
    u.role = role
    u.is_active = True
    return u


def _override_user(app: FastAPI, company_id: str, role: UserRole = UserRole.admin) -> None:
    """Override the auth chain. require_role([admin]) → role_checker →
    get_current_active_user → get_current_user. Overriding the bottom of the
    chain (get_current_active_user) is enough — role_checker reads the user
    role from the returned object."""
    user = _user(company_id, role)
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_current_active_user] = lambda: user


@pytest.fixture
def app() -> FastAPI:
    application = FastAPI()
    application.include_router(router, prefix="/api/v1")
    db = MagicMock()
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    db.execute = AsyncMock()
    application.dependency_overrides[get_db] = lambda: db
    return application


# ----------------- GET /webhooks/events (no auth) -----------------

class TestEventsCatalog:
    def test_lists_allowed_events(self, app: FastAPI):
        client = TestClient(app, raise_server_exceptions=False)
        r = client.get("/api/v1/webhooks/events")
        assert r.status_code == 200
        body = r.json()
        assert "events" in body
        assert isinstance(body["events"], list)
        assert len(body["events"]) > 0


# ----------------- POST /webhooks (admin only) -----------------

class TestCreateWebhook:
    _PAYLOAD = {
        "name": "My Hook",
        "url": "https://example.test/hook",
        "events": ["agent.execution.completed"],
    }

    def _wh(self, company_id: str = COMPANY_A) -> MagicMock:
        wh = MagicMock()
        wh.id = WEBHOOK_ID
        wh.to_dict = MagicMock(return_value={
            "id": WEBHOOK_ID,
            "company_id": company_id,
            "name": "My Hook",
            "url": "https://example.test/hook",
            "events": ["agent.execution.completed"],
            "is_active": True,
            "secret": "whsec_xxx",
        })
        return wh

    def test_happy_creates_and_returns_secret(self, app: FastAPI):
        _override_user(app, COMPANY_A)
        with patch(
            "app.api.v1.webhooks.webhook_service.create",
            new=AsyncMock(return_value=self._wh()),
        ):
            client = TestClient(app, raise_server_exceptions=False)
            r = client.post("/api/v1/webhooks", json=self._PAYLOAD)
        assert r.status_code == 201
        body = r.json()
        assert body["id"] == WEBHOOK_ID
        # Secret retornado SOMENTE no create
        assert body.get("secret") == "whsec_xxx"

    def test_value_error_returns_400(self, app: FastAPI):
        """Service raises ValueError (e.g. invalid event) → 400 + rollback."""
        _override_user(app, COMPANY_A)
        with patch(
            "app.api.v1.webhooks.webhook_service.create",
            new=AsyncMock(side_effect=ValueError("invalid event 'foo'")),
        ):
            client = TestClient(app, raise_server_exceptions=False)
            r = client.post("/api/v1/webhooks", json=self._PAYLOAD)
        assert r.status_code == 400
        assert "invalid event" in r.json()["detail"]

    def test_isolation_company_id_from_user(self, app: FastAPI):
        captured: dict = {}

        async def _spy(*, db, company_id, created_by, data):
            captured["company_id"] = company_id
            return self._wh(company_id)

        _override_user(app, COMPANY_A)
        with patch("app.api.v1.webhooks.webhook_service.create", new=_spy):
            client = TestClient(app, raise_server_exceptions=False)
            r1 = client.post("/api/v1/webhooks", json=self._PAYLOAD)
        assert r1.status_code == 201
        assert captured["company_id"] == COMPANY_A

        captured.clear()
        _override_user(app, COMPANY_B)
        with patch("app.api.v1.webhooks.webhook_service.create", new=_spy):
            client = TestClient(app, raise_server_exceptions=False)
            r2 = client.post("/api/v1/webhooks", json=self._PAYLOAD)
        assert r2.status_code == 201
        assert captured["company_id"] == COMPANY_B


# ----------------- GET /webhooks (admin only) -----------------

class TestListWebhooks:
    def test_admin_lists_company_webhooks(self, app: FastAPI):
        _override_user(app, COMPANY_A)
        wh = MagicMock()
        wh.to_dict = MagicMock(return_value={
            "id": WEBHOOK_ID,
            "company_id": COMPANY_A,
            "name": "Test Hook",
            "url": "https://example/hook",
            "events": ["candidate.created"],
            "is_active": True,
        })
        with patch(
            "app.api.v1.webhooks.webhook_service.list_for_company",
            new=AsyncMock(return_value=[wh]),
        ):
            client = TestClient(app, raise_server_exceptions=False)
            r = client.get("/api/v1/webhooks")
        assert r.status_code == 200
        body = r.json()
        assert body["total"] == 1
        assert body["webhooks"][0]["id"] == WEBHOOK_ID

    def test_non_admin_forbidden(self, app: FastAPI):
        # require_role([admin]) raises 403 for non-admin roles. The chain reads
        # the role from get_current_active_user's return value, so overriding
        # that with a recruiter user is enough to trigger the guard naturally.
        _override_user(app, COMPANY_A, role=UserRole.recruiter)
        client = TestClient(app, raise_server_exceptions=False)
        r = client.get("/api/v1/webhooks")
        assert r.status_code == 403

    def test_isolation_company_id_from_user(self, app: FastAPI):
        """list_for_company recebe company_id do current_user (nunca de query
        param) — tenants distintos vêem só os próprios webhooks."""
        captured: list[str] = []

        async def _spy(db, company_id):
            captured.append(company_id)
            return []  # lista vazia, irrelevante para isolamento

        _override_user(app, COMPANY_A)
        with patch("app.api.v1.webhooks.webhook_service.list_for_company", new=_spy):
            client = TestClient(app, raise_server_exceptions=False)
            r1 = client.get("/api/v1/webhooks")
        assert r1.status_code == 200

        _override_user(app, COMPANY_B)
        with patch("app.api.v1.webhooks.webhook_service.list_for_company", new=_spy):
            client = TestClient(app, raise_server_exceptions=False)
            r2 = client.get("/api/v1/webhooks")
        assert r2.status_code == 200

        assert captured == [COMPANY_A, COMPANY_B]


# ----------------- PATCH /webhooks/{id} (admin only) -----------------

class TestUpdateWebhook:
    _PAYLOAD = {"is_active": False}

    def test_404_when_not_found(self, app: FastAPI):
        _override_user(app, COMPANY_A)
        with patch(
            "app.api.v1.webhooks.webhook_service.update",
            new=AsyncMock(return_value=None),
        ):
            client = TestClient(app, raise_server_exceptions=False)
            r = client.patch(f"/api/v1/webhooks/{WEBHOOK_ID}", json=self._PAYLOAD)
        assert r.status_code == 404

    def test_happy_returns_updated(self, app: FastAPI):
        _override_user(app, COMPANY_A)
        wh = MagicMock()
        wh.to_dict = MagicMock(return_value={
            "id": WEBHOOK_ID, "company_id": COMPANY_A,
            "name": "My Hook", "url": "https://example.test/hook",
            "events": ["candidate.created"], "is_active": False,
        })
        with patch(
            "app.api.v1.webhooks.webhook_service.update",
            new=AsyncMock(return_value=wh),
        ):
            client = TestClient(app, raise_server_exceptions=False)
            r = client.patch(f"/api/v1/webhooks/{WEBHOOK_ID}", json=self._PAYLOAD)
        assert r.status_code == 200
        assert r.json()["is_active"] is False

    def test_isolation_company_id_from_user(self, app: FastAPI):
        captured: list[str] = []
        wh = MagicMock()
        wh.to_dict = MagicMock(return_value={
            "id": WEBHOOK_ID, "company_id": COMPANY_A,
            "name": "x", "url": "https://x", "events": [], "is_active": True,
        })

        async def _spy(*, db, webhook_id, company_id, data):
            captured.append(company_id)
            wh.to_dict.return_value["company_id"] = company_id
            return wh

        _override_user(app, COMPANY_A)
        with patch("app.api.v1.webhooks.webhook_service.update", new=_spy):
            client = TestClient(app, raise_server_exceptions=False)
            r1 = client.patch(f"/api/v1/webhooks/{WEBHOOK_ID}", json=self._PAYLOAD)
        _override_user(app, COMPANY_B)
        with patch("app.api.v1.webhooks.webhook_service.update", new=_spy):
            client = TestClient(app, raise_server_exceptions=False)
            r2 = client.patch(f"/api/v1/webhooks/{WEBHOOK_ID}", json=self._PAYLOAD)
        assert r1.status_code == 200 and r2.status_code == 200
        assert captured == [COMPANY_A, COMPANY_B]


# ----------------- POST /webhooks/{id}/test (admin only) -----------------

class TestSendTestWebhook:
    def test_404_when_not_found(self, app: FastAPI):
        _override_user(app, COMPANY_A)
        with patch(
            "app.api.v1.webhooks.webhook_service.get",
            new=AsyncMock(return_value=None),
        ):
            client = TestClient(app, raise_server_exceptions=False)
            r = client.post(f"/api/v1/webhooks/{WEBHOOK_ID}/test")
        assert r.status_code == 404

    def test_happy_queues_test_event(self, app: FastAPI):
        _override_user(app, COMPANY_A)
        wh = MagicMock()
        wh.id = WEBHOOK_ID
        wh.url = "https://example.test/hook"
        wh.secret = "whsec_xxx"
        captured_kwargs: dict = {}

        class _FakeTask:
            def delay(self, **kw):
                captured_kwargs.update(kw)

        with patch(
            "app.api.v1.webhooks.webhook_service.get",
            new=AsyncMock(return_value=wh),
        ), patch.dict(
            "sys.modules",
            {"app.jobs.webhook_tasks": MagicMock(deliver_webhook_task=_FakeTask())},
        ):
            client = TestClient(app, raise_server_exceptions=False)
            r = client.post(f"/api/v1/webhooks/{WEBHOOK_ID}/test")
        assert r.status_code == 200
        assert r.json() == {"queued": True, "message": "Test event queued for delivery"}
        # Payload do test event tem shape canônico
        assert captured_kwargs.get("event") == "webhook.test"
        assert captured_kwargs.get("payload", {}).get("test") is True
        assert captured_kwargs.get("payload", {}).get("company_id") == COMPANY_A

    def test_isolation_company_id_passed_to_get(self, app: FastAPI):
        captured: list[str] = []

        async def _spy_get(db, webhook_id, company_id):
            captured.append(company_id)
            return None  # 404 — isolamento ainda comprovável pela captura

        _override_user(app, COMPANY_A)
        with patch("app.api.v1.webhooks.webhook_service.get", new=_spy_get):
            client = TestClient(app, raise_server_exceptions=False)
            client.post(f"/api/v1/webhooks/{WEBHOOK_ID}/test")
        _override_user(app, COMPANY_B)
        with patch("app.api.v1.webhooks.webhook_service.get", new=_spy_get):
            client = TestClient(app, raise_server_exceptions=False)
            client.post(f"/api/v1/webhooks/{WEBHOOK_ID}/test")
        assert captured == [COMPANY_A, COMPANY_B]


# ----------------- DELETE /webhooks/{id} (admin only) -----------------

class TestDeleteWebhook:
    def test_404_when_not_found(self, app: FastAPI):
        _override_user(app, COMPANY_A)
        with patch(
            "app.api.v1.webhooks.webhook_service.delete",
            new=AsyncMock(return_value=False),
        ):
            client = TestClient(app, raise_server_exceptions=False)
            r = client.delete(f"/api/v1/webhooks/{WEBHOOK_ID}")
        assert r.status_code == 404

    def test_isolation_company_id_passed_from_user(self, app: FastAPI):
        """webhook_service.delete must receive the company_id of the *user*,
        never trust a value supplied by the caller — proves isolation."""
        captured: dict = {}

        async def _spy(*, db, webhook_id, company_id):
            captured["webhook_id"] = webhook_id
            captured["company_id"] = company_id
            return True

        # tenant A
        _override_user(app, COMPANY_A)
        with patch("app.api.v1.webhooks.webhook_service.delete", new=_spy):
            client = TestClient(app, raise_server_exceptions=False)
            r = client.delete(f"/api/v1/webhooks/{WEBHOOK_ID}")
        assert r.status_code == 204
        assert captured["company_id"] == COMPANY_A
        assert captured["webhook_id"] == WEBHOOK_ID

        # switch to tenant B — same webhook_id, different company resolved
        captured.clear()
        _override_user(app, COMPANY_B)
        with patch("app.api.v1.webhooks.webhook_service.delete", new=_spy):
            client = TestClient(app, raise_server_exceptions=False)
            r = client.delete(f"/api/v1/webhooks/{WEBHOOK_ID}")
        assert r.status_code == 204
        assert captured["company_id"] == COMPANY_B
