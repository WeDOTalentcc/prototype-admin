"""R-006 — gate dev-fallback-token em /api/v1/teams/tab/auth.

Pin behaviors:
  1. Azure NÃO configurado + _DEV_MODE=False (prod) → HTTPException(503).
  2. Azure NÃO configurado + _DEV_MODE=True (dev) → 200 + dev token.
  3. Azure configurado → branch fallback NÃO dispara (segue OBO real).

Testa o handler `teams_tab_auth` direto (chamada de função), sem subir o
app FastAPI completo — mantém hermético e rápido. Multi-tenancy não se
aplica porque o endpoint é PÚBLICO por desenho (gate principal é Azure
SSO; em dev cai no fallback).
"""
from __future__ import annotations

import os
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException

from app.api.v1.teams import TabAuthRequest, teams_tab_auth


@pytest.mark.asyncio
async def test_azure_not_configured_in_prod_raises_503(monkeypatch):
    """Em prod (não-DEV), endpoint recusa fallback e retorna 503."""
    # Limpa envs Azure (path do gate)
    monkeypatch.delenv("AZURE_CLIENT_ID", raising=False)
    monkeypatch.delenv("AZURE_CLIENT_SECRET", raising=False)
    monkeypatch.delenv("AZURE_TENANT_ID", raising=False)
    # Mock _DEV_MODE=False (prod-like)
    with patch("app.middleware.auth_enforcement._DEV_MODE", False):
        payload = TabAuthRequest(sso_token="fake-jwt")
        fake_db = AsyncMock()
        with pytest.raises(HTTPException) as exc:
            await teams_tab_auth(payload, db=fake_db)
        assert exc.value.status_code == 503
        assert "unavailable" in exc.value.detail.lower()


@pytest.mark.asyncio
async def test_azure_not_configured_in_dev_returns_dev_token(monkeypatch):
    """Em DEV, sem Azure, endpoint devolve dev fallback token (200)."""
    monkeypatch.delenv("AZURE_CLIENT_ID", raising=False)
    monkeypatch.delenv("AZURE_CLIENT_SECRET", raising=False)
    monkeypatch.delenv("AZURE_TENANT_ID", raising=False)
    monkeypatch.delenv("TEAMS_DEV_FALLBACK_TOKEN", raising=False)
    with patch("app.middleware.auth_enforcement._DEV_MODE", True):
        payload = TabAuthRequest(sso_token="fake-jwt")
        fake_db = AsyncMock()
        resp = await teams_tab_auth(payload, db=fake_db)
        assert resp.access_token == "dev-fallback-token"
        assert resp.user_id == "dev-user"
        assert resp.email == "dev@wedotalent.com"


@pytest.mark.asyncio
async def test_azure_not_configured_in_dev_honors_env_override(monkeypatch):
    """Dev fallback respeita TEAMS_DEV_FALLBACK_TOKEN env override."""
    monkeypatch.delenv("AZURE_CLIENT_ID", raising=False)
    monkeypatch.delenv("AZURE_CLIENT_SECRET", raising=False)
    monkeypatch.delenv("AZURE_TENANT_ID", raising=False)
    monkeypatch.setenv("TEAMS_DEV_FALLBACK_TOKEN", "custom-dev-secret-xyz")
    with patch("app.middleware.auth_enforcement._DEV_MODE", True):
        payload = TabAuthRequest(sso_token="fake-jwt")
        fake_db = AsyncMock()
        resp = await teams_tab_auth(payload, db=fake_db)
        assert resp.access_token == "custom-dev-secret-xyz"


@pytest.mark.asyncio
async def test_azure_configured_does_not_hit_fallback(monkeypatch):
    """Com Azure configurado, branch fallback NÃO dispara — caminho OBO
    real é tentado (e falhará por SSO inválido, mas isso é OK; pin é
    só que o fallback NÃO retorna)."""
    monkeypatch.setenv("AZURE_CLIENT_ID", "fake-client")
    monkeypatch.setenv("AZURE_CLIENT_SECRET", "fake-secret")
    monkeypatch.setenv("AZURE_TENANT_ID", "fake-tenant")
    payload = TabAuthRequest(sso_token="fake-jwt")
    fake_db = AsyncMock()

    # Mock httpx para evitar request real ao Azure — basta retornar 401.
    class FakeResp:
        status_code = 401

        def json(self):
            return {"error": "invalid_grant"}

    class FakeClient:
        def __init__(self, *a, **kw):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        async def post(self, *a, **kw):
            return FakeResp()

        async def get(self, *a, **kw):
            return FakeResp()

    with patch("httpx.AsyncClient", FakeClient):
        # Espera HTTPException 401 do path OBO — NÃO o dev token.
        with pytest.raises(HTTPException) as exc:
            await teams_tab_auth(payload, db=fake_db)
        # Pin: status NÃO é 503 (fallback prod) e não voltou TabAuthResponse
        # com dev token. Path OBO disparou.
        assert exc.value.status_code != 503
