"""
Coverage tests for app/api/v1/llm_config.py — Task #930.

Cobre os 4 endpoints de configuração de LLM por tenant:
- GET    /admin/llm-config            — config + máscara de api_key
- PUT    /admin/llm-config            — merge semantics + audit log
- POST   /admin/llm-config/test       — teste de provider (sem chamar API real)
- GET    /admin/llm-config/providers  — catálogo público

Os testes usam mocks de LlmConfigRepository / AuditLogRepository — não tocam
encryption real (ENCRYPTION_KEY não é necessário).
"""
from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from lia_config.database import get_db

from app.api.v1.llm_config import router
from app.auth.dependencies import get_current_user_or_demo
from app.auth.models import UserRole


COMPANY_A = "11111111-1111-1111-1111-111111111111"
COMPANY_B = "22222222-2222-2222-2222-222222222222"


def _user(company_id: str) -> MagicMock:
    u = MagicMock()
    u.id = uuid4()
    u.email = f"admin@{company_id}.test"
    u.company_id = company_id
    u.company_name = company_id
    u.role = UserRole.admin
    u.is_active = True
    return u


@pytest.fixture
def app() -> FastAPI:
    application = FastAPI()
    application.include_router(router, prefix="/api/v1")
    db = MagicMock()
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    application.dependency_overrides[get_db] = lambda: db
    application.dependency_overrides[get_current_user_or_demo] = lambda: _user(COMPANY_A)
    return application


# ----------------- GET /admin/llm-config -----------------

class TestGetLLMConfig:
    def test_returns_defaults_when_no_config(self, app: FastAPI):
        repo = MagicMock()
        repo.get_by_company_id = AsyncMock(return_value=None)
        with patch("app.api.v1.llm_config.LlmConfigRepository", return_value=repo):
            client = TestClient(app, raise_server_exceptions=False)
            r = client.get("/api/v1/admin/llm-config")
        assert r.status_code == 200
        body = r.json()
        assert body["company_id"] == COMPANY_A
        assert body["primary_provider"] == "gemini"
        assert body["providers"] == {}

    def test_returns_masked_api_keys(self, app: FastAPI):
        repo = MagicMock()
        repo.get_by_company_id = AsyncMock(
            return_value=SimpleNamespace(
                primary_provider="claude",
                fallback_order=["claude", "openai"],
                providers={
                    "claude": {"api_key": "sk-ant-supersecretkey-12345", "is_active": True},
                    "openai": {"api_key": "tiny", "is_active": False},  # short key path
                },
                routing={"chat": "claude"},
                is_active=True,
            )
        )
        with patch("app.api.v1.llm_config.LlmConfigRepository", return_value=repo):
            client = TestClient(app, raise_server_exceptions=False)
            r = client.get("/api/v1/admin/llm-config")
        assert r.status_code == 200
        providers = r.json()["providers"]
        assert "..." in providers["claude"]["api_key"]
        # Real secret never leaks in plaintext
        assert "supersecretkey" not in providers["claude"]["api_key"]
        # Short key path is fully masked with bullets
        assert providers["openai"]["api_key"].startswith("•")

    def test_company_id_isolation_per_user(self, app: FastAPI):
        captured: list[str] = []

        async def _spy(company_id):
            captured.append(company_id)
            return None

        repo = MagicMock()
        repo.get_by_company_id = _spy

        with patch("app.api.v1.llm_config.LlmConfigRepository", return_value=repo):
            # tenant A
            client = TestClient(app, raise_server_exceptions=False)
            r1 = client.get("/api/v1/admin/llm-config")

            # switch user → tenant B
            app.dependency_overrides[get_current_user_or_demo] = lambda: _user(COMPANY_B)
            r2 = client.get("/api/v1/admin/llm-config")

        assert r1.status_code == 200 and r2.status_code == 200
        assert captured == [COMPANY_A, COMPANY_B]
        assert r1.json()["company_id"] == COMPANY_A
        assert r2.json()["company_id"] == COMPANY_B


# ----------------- PUT /admin/llm-config -----------------

class TestUpdateLLMConfig:
    """Cobre PUT /admin/llm-config — merge semantics + audit log + isolamento.

    Task #935: corrigido o `UnboundLocalError` que vinha do re-import de
    `AuditLogRepository` dentro da função. O import canônico vive no topo
    do módulo e o endpoint agora retorna 200 no happy path.
    """

    def _payload(self, primary: str = "claude", api_key: str = "sk-ant-newsecret-XXXX"):
        return {
            "primary_provider": primary,
            "fallback_order": [primary, "openai"],
            "providers": {
                primary: {"api_key": api_key, "model": "claude-sonnet-4-6", "is_active": True},
            },
            "routing": {
                "default": primary, "screening": primary, "wsi": primary,
                "chat": primary, "interview": primary,
            },
        }

    def _patches(self, repo, audit):
        return [
            patch("app.api.v1.llm_config.LlmConfigRepository", return_value=repo),
            patch("app.api.v1.llm_config.AuditLogRepository", return_value=audit),
            patch("app.repositories.audit_log_repository.AuditLogRepository", return_value=audit),
            patch("app.api.v1.llm_config.clear_tenant_config_cache"),
        ]

    def test_happy_path_upserts_and_returns_status_updated(self, app: FastAPI):
        repo = MagicMock()
        repo.get_by_company_id = AsyncMock(return_value=None)
        repo.upsert = AsyncMock()
        audit = MagicMock(); audit.create_log = AsyncMock()
        patches = self._patches(repo, audit)
        for p in patches: p.start()
        try:
            client = TestClient(app, raise_server_exceptions=False)
            r = client.put("/api/v1/admin/llm-config", json=self._payload())
        finally:
            for p in patches: p.stop()
        assert r.status_code == 200
        assert r.json()["status"] == "updated"
        assert r.json()["company_id"] == COMPANY_A
        repo.upsert.assert_awaited_once()

    def test_masked_key_preserves_existing_secret(self, app: FastAPI):
        """Quando client envia api_key contendo '...', endpoint mantém o existente."""
        existing = SimpleNamespace(
            providers={"claude": {"api_key": "sk-ant-OLDSECRET", "is_active": True, "model": "claude-sonnet-4-6"}},
            primary_provider="claude", fallback_order=["claude"], routing={}, is_active=True,
        )
        captured: dict = {}

        async def _capture_upsert(**kwargs):
            captured.update(kwargs)

        repo = MagicMock()
        repo.get_by_company_id = AsyncMock(return_value=existing)
        repo.upsert = _capture_upsert
        audit = MagicMock(); audit.create_log = AsyncMock()
        patches = self._patches(repo, audit)
        for p in patches: p.start()
        try:
            client = TestClient(app, raise_server_exceptions=False)
            r = client.put("/api/v1/admin/llm-config", json=self._payload(api_key="sk-ant-...XXXX"))
        finally:
            for p in patches: p.stop()
        assert r.status_code == 200
        # Old secret survives because incoming key is masked
        assert captured["providers_dict"]["claude"]["api_key"] == "sk-ant-OLDSECRET"

    def test_company_id_isolation_per_user(self, app: FastAPI):
        captured_company_ids: list[str] = []

        async def _capture(**kwargs):
            captured_company_ids.append(kwargs["company_id"])

        repo = MagicMock()
        repo.get_by_company_id = AsyncMock(return_value=None)
        repo.upsert = _capture
        audit = MagicMock(); audit.create_log = AsyncMock()
        patches = self._patches(repo, audit)
        for p in patches: p.start()
        try:
            client = TestClient(app, raise_server_exceptions=False)
            r1 = client.put("/api/v1/admin/llm-config", json=self._payload())
            app.dependency_overrides[get_current_user_or_demo] = lambda: _user(COMPANY_B)
            r2 = client.put("/api/v1/admin/llm-config", json=self._payload())
        finally:
            for p in patches: p.stop()
        assert r1.status_code == 200 and r2.status_code == 200
        assert captured_company_ids == [COMPANY_A, COMPANY_B]
        assert r1.json()["company_id"] == COMPANY_A
        assert r2.json()["company_id"] == COMPANY_B


# ----------------- POST /admin/llm-config/test -----------------

class TestTestProvider:
    def test_unknown_provider_returns_400_in_message(self, app: FastAPI):
        # Endpoint uses HTTPException(400) which is *raised inside* the same
        # try/except — the except catches it and returns a TestProviderResponse
        # with success=False rather than HTTP 400. Verify the failure shape.
        client = TestClient(app, raise_server_exceptions=False)
        r = client.post(
            "/api/v1/admin/llm-config/test",
            json={"provider": "unknownx", "api_key": "x"},
        )
        # Either the HTTPException leaks as 400 (older code path) or the
        # except branch wraps it as success=False. Accept both.
        if r.status_code == 200:
            body = r.json()
            assert body["success"] is False
            assert body["provider"] == "unknownx"
        else:
            assert r.status_code == 400

    def test_redacts_api_key_in_failure_message(self, app: FastAPI):
        # Force the gemini import to raise an exception that contains a key-like
        # token; the regex in the endpoint must redact it.
        with patch(
            "google.genai.Client",
            side_effect=Exception("auth failed for AIzaSyA1234567890ABCDEFGH"),
            create=True,
        ):
            client = TestClient(app, raise_server_exceptions=False)
            r = client.post(
                "/api/v1/admin/llm-config/test",
                json={"provider": "gemini", "api_key": "AIzaSyA1234567890ABCDEFGH"},
            )
        assert r.status_code == 200
        body = r.json()
        assert body["success"] is False
        assert "AIzaSyA1234567890" not in body["message"]
        assert "***REDACTED***" in body["message"]


# ----------------- GET /admin/llm-config/providers -----------------

class TestListProviders:
    def test_lists_three_providers(self, app: FastAPI):
        client = TestClient(app, raise_server_exceptions=False)
        r = client.get("/api/v1/admin/llm-config/providers")
        assert r.status_code == 200
        body = r.json()
        ids = {p["id"] for p in body["providers"]}
        assert ids == {"gemini", "claude", "openai"}
        assert "tier1" in body["tier_definitions"]
        assert "screening" in body["routing_types"]
