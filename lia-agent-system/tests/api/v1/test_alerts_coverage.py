"""
Coverage tests for app/api/v1/alerts.py — Task #930.

Cobre os endpoints expostos pelo menu Configurações:
- GET  /alerts/config         (3 testes: happy + erro 500 + isolamento por company_id)
- PUT  /alerts/config         (3 testes: cria + atualiza + isolamento)
- GET  /alerts/               (3 testes: happy + repasse de filtros + erro 500)
- GET  /alerts/preferences    (2 testes: defaults vazio + isolamento por company_id)
- POST /alerts/preferences    (1 teste: 400 quando lista vazia)
- PUT  /alerts/preferences    (3 testes: delega ao POST + isolamento + 400 vazia)

Padrão: TestClient + app.dependency_overrides (mesmo de tests/integration/test_tenant_scope_v1.py).
Sem mocks globais; sem alterar produção.

Notas:
- GET /alerts/ NÃO depende de get_verified_company_id (job_alert_service.get_active_alerts
  recebe apenas db/user_id/severity/limit), então o tripé "isolamento por company_id"
  é substituído por "isolamento por user_id/filtro" — validar que parâmetros são
  repassados ao service. O gap de tenant no GET /alerts/ está rastreado como follow-up.
"""
from __future__ import annotations

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

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


def _alert_config_payload(briefing: str = "daily") -> dict:
    """Build a valid AlertConfigRequest body."""
    return {
        "alerts": [
            {
                "id": "time_to_hire_critical",
                "name": "Time to Hire Crítico",
                "description": "TTH ultrapassa limite",
                "enabled": True,
                "channel": "email",
            }
        ],
        "briefing_frequency": briefing,
    }


def _pref_payload(user_id: str = "user-1", alert_type: str = "no_hires") -> dict:
    """Build a valid AlertPreferenceRequest body."""
    return {
        "preferences": [
            {
                "user_id": user_id,
                "alert_type": alert_type,
                "is_enabled": True,
                "threshold": 5,
                "channels": {"email": True, "bell": True, "teams": False, "whatsapp": False},
                "cooldown_hours": 24,
            }
        ]
    }


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


# ----------------- PUT /alerts/config -----------------

class TestAlertConfigPut:
    def test_creates_when_no_existing_config(self, app: FastAPI, repo_mock: MagicMock):
        """Happy path: sem config ativa → repo.create_config é chamado."""
        created = MagicMock()
        created.alerts = [{"id": "x", "name": "X", "description": "x", "enabled": True, "channel": "email"}]
        created.briefing_frequency = "daily"
        repo_mock.get_active_config_for_company = AsyncMock(return_value=None)
        repo_mock.create_config = AsyncMock(return_value=created)

        _patch_company(app, COMPANY_A)
        app.dependency_overrides[get_alert_repo] = lambda: repo_mock
        client = TestClient(app, raise_server_exceptions=False)

        r = client.put("/api/v1/alerts/config", json=_alert_config_payload())
        assert r.status_code == 200
        repo_mock.create_config.assert_awaited_once()
        repo_mock.update_config.assert_not_called()
        # company_id deve ter sido injetado no payload do create
        create_kwargs = repo_mock.create_config.await_args.args[0]
        assert create_kwargs["company_id"] == COMPANY_A

    def test_updates_existing_config(self, app: FastAPI, repo_mock: MagicMock):
        """Happy path: config ativa existente → repo.update_config é chamado."""
        existing = MagicMock()
        updated = MagicMock()
        updated.alerts = [{"id": "y"}]
        updated.briefing_frequency = "weekly"
        repo_mock.get_active_config_for_company = AsyncMock(return_value=existing)
        repo_mock.update_config = AsyncMock(return_value=updated)

        _patch_company(app, COMPANY_A)
        app.dependency_overrides[get_alert_repo] = lambda: repo_mock
        client = TestClient(app, raise_server_exceptions=False)

        r = client.put("/api/v1/alerts/config", json=_alert_config_payload(briefing="weekly"))
        assert r.status_code == 200
        assert r.json()["briefing_frequency"] == "weekly"
        repo_mock.update_config.assert_awaited_once()
        repo_mock.create_config.assert_not_called()

    def test_isolates_writes_per_company(self, app: FastAPI):
        """Cross-tenant: alterna company_id e captura o valor passado ao repo."""
        captured: list[str] = []

        async def _get_active(company_id: str):
            captured.append(company_id)
            return None

        async def _create(payload: dict):
            obj = MagicMock()
            obj.alerts = []
            obj.briefing_frequency = payload["briefing_frequency"]
            return obj

        repo = MagicMock()
        repo.get_active_config_for_company = _get_active
        repo.create_config = _create
        app.dependency_overrides[get_alert_repo] = lambda: repo

        _patch_company(app, COMPANY_A)
        client = TestClient(app, raise_server_exceptions=False)
        r1 = client.put("/api/v1/alerts/config", json=_alert_config_payload())

        _patch_company(app, COMPANY_B)
        r2 = client.put("/api/v1/alerts/config", json=_alert_config_payload())

        assert r1.status_code == 200 and r2.status_code == 200
        assert captured == [COMPANY_A, COMPANY_B]


# ----------------- GET /alerts/ (list) -----------------

class TestListAlerts:
    def test_returns_alert_list(self, app: FastAPI):
        """Happy path: service retorna alertas, endpoint serializa via to_dict."""
        alert = MagicMock()
        alert.to_dict.return_value = {
            "id": "a-1",
            "alert_type": "no_hires",
            "severity": "critical",
            "status": "active",
            "title": "Sem contratações",
            "message": "Nenhuma contratação na semana",
            "user_id": None,
            "job_id": None,
            "candidate_id": None,
            "context": None,
            "suggested_actions": None,
            "acknowledged_at": None,
            "resolved_at": None,
            "created_at": datetime.utcnow(),
        }

        with patch("app.api.v1.alerts.job_alert_service.get_active_alerts", new=AsyncMock(return_value=[alert])):
            client = TestClient(app, raise_server_exceptions=False)
            r = client.get("/api/v1/alerts/")
        assert r.status_code == 200
        body = r.json()
        assert len(body) == 1
        assert body[0]["id"] == "a-1"
        assert body[0]["severity"] == "critical"

    def test_passes_filters_to_service(self, app: FastAPI):
        """Filtros (severity/user_id/limit) devem ser repassados ao service."""
        captured: dict = {}

        async def _fake(db, user_id=None, severity=None, limit=50):
            captured["user_id"] = user_id
            captured["severity"] = severity
            captured["limit"] = limit
            return []

        with patch("app.api.v1.alerts.job_alert_service.get_active_alerts", new=_fake):
            client = TestClient(app, raise_server_exceptions=False)
            r = client.get("/api/v1/alerts/", params={"severity": "critical", "user_id": "u-1", "limit": 10})
        assert r.status_code == 200
        assert captured["user_id"] == "u-1"
        assert captured["severity"] == "critical"
        assert captured["limit"] == 10

    def test_returns_500_when_service_raises(self, app: FastAPI):
        """Erro: service falha → propaga 500 (sem handler de exceção próprio)."""
        async def _boom(*args, **kwargs):
            raise RuntimeError("upstream alert service down")

        with patch("app.api.v1.alerts.job_alert_service.get_active_alerts", new=_boom):
            client = TestClient(app, raise_server_exceptions=False)
            r = client.get("/api/v1/alerts/")
        assert r.status_code == 500


# ----------------- PUT /alerts/preferences -----------------

class TestAlertPreferencesPut:
    def test_delegates_to_post_handler(self, app: FastAPI):
        """PUT /preferences é alias do POST: chama upsert_preference_by_type."""
        captured: list[tuple[str, str, str]] = []
        pref_obj = MagicMock()
        pref_obj.to_dict.return_value = {"alert_type": "no_hires", "is_enabled": True}

        async def _upsert(*, company_id, user_id, alert_type, data):
            captured.append((company_id, user_id, alert_type))
            return pref_obj

        repo = MagicMock()
        repo.upsert_preference_by_type = _upsert
        app.dependency_overrides[get_alert_repo] = lambda: repo

        _patch_company(app, COMPANY_A)
        client = TestClient(app, raise_server_exceptions=False)
        r = client.put("/api/v1/alerts/preferences", json=_pref_payload(user_id="u-9"))
        assert r.status_code == 200
        body = r.json()
        assert body["user_id"] == "u-9"
        assert body["company_id"] == COMPANY_A
        assert captured == [(COMPANY_A, "u-9", "no_hires")]

    def test_returns_400_when_empty_list(self, app: FastAPI, repo_mock: MagicMock):
        """Erro: lista vazia → 400 (mesma validação do POST)."""
        _patch_company(app, COMPANY_A)
        app.dependency_overrides[get_alert_repo] = lambda: repo_mock
        client = TestClient(app, raise_server_exceptions=False)
        r = client.put("/api/v1/alerts/preferences", json={"preferences": []})
        assert r.status_code == 400

    def test_isolates_writes_per_company(self, app: FastAPI):
        """Cross-tenant: alterna company_id e valida que upsert recebe o valor correto."""
        seen: list[str] = []
        pref_obj = MagicMock()
        pref_obj.to_dict.return_value = {"alert_type": "no_hires"}

        async def _upsert(*, company_id, user_id, alert_type, data):
            seen.append(company_id)
            return pref_obj

        repo = MagicMock()
        repo.upsert_preference_by_type = _upsert
        app.dependency_overrides[get_alert_repo] = lambda: repo

        _patch_company(app, COMPANY_A)
        client = TestClient(app, raise_server_exceptions=False)
        r1 = client.put("/api/v1/alerts/preferences", json=_pref_payload())

        _patch_company(app, COMPANY_B)
        r2 = client.put("/api/v1/alerts/preferences", json=_pref_payload())

        assert r1.status_code == 200 and r2.status_code == 200
        assert seen == [COMPANY_A, COMPANY_B]
