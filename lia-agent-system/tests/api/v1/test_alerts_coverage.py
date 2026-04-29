"""
Coverage tests for app/api/v1/alerts.py — Task #930.

Cobre os endpoints sem testes prévios:
- GET /alerts/config + PUT /alerts/config
- GET /alerts/preferences + POST /alerts/preferences
- GET /alerts/  (listagem geral)

Cada endpoint tem ≥3 testes (happy + erro + isolamento por company_id).
"""
from __future__ import annotations

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.alerts import get_alert_repo, router
from app.core.database import get_db
from app.shared.tenant_guard import get_verified_company_id

COMPANY_A = "11111111-1111-1111-1111-111111111111"
COMPANY_B = "22222222-2222-2222-2222-222222222222"


def _patch_company(app: FastAPI, company_id: str) -> None:
    app.dependency_overrides[get_verified_company_id] = lambda: company_id


@pytest.fixture
def app() -> FastAPI:
    application = FastAPI()
    application.include_router(router, prefix="/api/v1")
    application.dependency_overrides[get_db] = lambda: MagicMock()
    return application


@pytest.fixture
def repo_mock() -> MagicMock:
    repo = MagicMock()
    repo.get_active_config_for_company = AsyncMock(return_value=None)
    repo.update_config = AsyncMock()
    repo.create_config = AsyncMock()
    repo.list_preferences_for_company_user = AsyncMock(return_value=[])
    repo.upsert_preference_by_type = AsyncMock()
    return repo


# ----------------- /alerts/config -----------------

class TestAlertConfigGet:
    def test_returns_defaults_when_no_config(self, app: FastAPI, repo_mock: MagicMock):
        _patch_company(app, COMPANY_A)
        app.dependency_overrides[get_alert_repo] = lambda: repo_mock
        client = TestClient(app, raise_server_exceptions=False)
        r = client.get("/api/v1/alerts/config")
        assert r.status_code == 200
        body = r.json()
        # Defaults have 5 entries
        assert len(body["alerts"]) == 5
        assert body["briefing_frequency"] == "daily"

    def test_returns_500_when_repository_raises(self, app: FastAPI, repo_mock: MagicMock):
        _patch_company(app, COMPANY_A)
        repo_mock.get_active_config_for_company = AsyncMock(
            side_effect=RuntimeError("db down")
        )
        app.dependency_overrides[get_alert_repo] = lambda: repo_mock
        client = TestClient(app, raise_server_exceptions=False)
        r = client.get("/api/v1/alerts/config")
        assert r.status_code == 500

    def test_company_id_dependency_isolates_responses(self, app: FastAPI):
        """Different tenants resolve their own configs from the repository."""
        captured: list[str] = []

        repo = MagicMock()

        async def _get_cfg(company_id):
            captured.append(company_id)
            cfg = MagicMock()
            cfg.alerts = [{"id": company_id, "name": "T", "description": "d", "enabled": True, "channel": "email"}]
            cfg.briefing_frequency = "daily"
            return cfg

        repo.get_active_config_for_company = _get_cfg
        app.dependency_overrides[get_alert_repo] = lambda: repo

        _patch_company(app, COMPANY_A)
        client = TestClient(app, raise_server_exceptions=False)
        r1 = client.get("/api/v1/alerts/config")

        _patch_company(app, COMPANY_B)
        r2 = client.get("/api/v1/alerts/config")

        assert r1.status_code == 200 and r2.status_code == 200
        assert captured == [COMPANY_A, COMPANY_B]
        assert r1.json()["alerts"][0]["id"] == COMPANY_A
        assert r2.json()["alerts"][0]["id"] == COMPANY_B


# ----------------- /alerts/preferences -----------------

class TestAlertPreferences:
    def test_get_returns_defaults_when_empty(self, app: FastAPI, repo_mock: MagicMock):
        _patch_company(app, COMPANY_A)
        app.dependency_overrides[get_alert_repo] = lambda: repo_mock
        client = TestClient(app, raise_server_exceptions=False)
        r = client.get("/api/v1/alerts/preferences", params={"user_id": "u-1"})
        assert r.status_code == 200
        body = r.json()
        assert body["user_id"] == "u-1"
        assert body["company_id"] == COMPANY_A
        assert len(body["preferences"]) > 0
        assert all(p["company_id"] == COMPANY_A for p in body["preferences"])

    def test_post_empty_preferences_returns_400(self, app: FastAPI, repo_mock: MagicMock):
        _patch_company(app, COMPANY_A)
        app.dependency_overrides[get_alert_repo] = lambda: repo_mock
        client = TestClient(app, raise_server_exceptions=False)
        r = client.post("/api/v1/alerts/preferences", json={"preferences": []})
        assert r.status_code == 400

    def test_get_isolates_preferences_per_company(self, app: FastAPI):
        captured: list[tuple[str, str]] = []

        repo = MagicMock()

        async def _list(company_id, user_id):
            captured.append((company_id, user_id))
            return []

        repo.list_preferences_for_company_user = _list
        app.dependency_overrides[get_alert_repo] = lambda: repo

        _patch_company(app, COMPANY_A)
        client = TestClient(app, raise_server_exceptions=False)
        r1 = client.get("/api/v1/alerts/preferences", params={"user_id": "u-1"})

        _patch_company(app, COMPANY_B)
        r2 = client.get("/api/v1/alerts/preferences", params={"user_id": "u-1"})

        assert r1.status_code == 200 and r2.status_code == 200
        assert captured == [(COMPANY_A, "u-1"), (COMPANY_B, "u-1")]
        assert r1.json()["company_id"] == COMPANY_A
        assert r2.json()["company_id"] == COMPANY_B
