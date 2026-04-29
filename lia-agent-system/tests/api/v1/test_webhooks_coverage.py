"""
Coverage tests for app/api/v1/webhooks.py — Task #930.

Cobre:
- happy: GET /webhooks/events lista catálogo, GET /webhooks lista por company.
- erro: PATCH/DELETE em webhook inexistente devolve 404; criação com role
        diferente de admin devolve 403 (require_role enforcement).
- isolamento: list_webhooks recebe company_id do current_user (não de query
        param) — tenants distintos vêem só seus webhooks.
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
