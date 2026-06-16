"""Task #293 — non-regressão: middleware DEV_MODE usa UUID canônico.

Cobre:
1. Em produção (APP_ENV=production) + sem Bearer → 401.
2. Em produção + LIA_DEV_MODE apagado → 401 mesmo com X-Dev-Api-Key.
3. Em dev + DEV_MODE+DEV_KEY válidos → injeta DEMO_COMPANY_UUID canônico em
   request.state.company_id (não a string legada "demo_company").
"""

from __future__ import annotations

import os
from unittest.mock import patch

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient


def _build_app_with_middleware(dev_mode: bool, dev_api_key: str = ""):
    """Builds a minimal FastAPI app wrapping AuthEnforcementMiddleware.

    The middleware reads module-level flags set at import time, so we patch
    both the env and the module globals to simulate prod/dev regimes.
    """
    env_patches = {
        "LIA_DEV_MODE": "true" if dev_mode else "",
        "LIA_DEV_API_KEY": dev_api_key,
        # Literal production probe: quando dev_mode=False simulamos deploy real.
        "APP_ENV": "development" if dev_mode else "production",
    }
    with patch.dict(os.environ, env_patches, clear=False):
        import importlib
        import app.middleware.auth_enforcement as m
        importlib.reload(m)

        app = FastAPI()
        app.add_middleware(m.AuthEnforcementMiddleware)

        @app.get("/api/v1/candidates")
        async def list_candidates(request: Request):
            return JSONResponse({
                "company_id": getattr(request.state, "company_id", None),
                "user_id": getattr(request.state, "user_id", None),
            })

        return app, m


def test_production_without_bearer_returns_401():
    """Regressão: sem Bearer + sem DEV_MODE → 401 (comportamento produção)."""
    app, _ = _build_app_with_middleware(dev_mode=False)
    client = TestClient(app)
    resp = client.get("/api/v1/candidates")
    assert resp.status_code == 401
    assert resp.json()["detail"] == "Authentication required"


def test_production_rejects_dev_api_key_header_when_dev_mode_off():
    """Mesmo com X-Dev-Api-Key presente, sem LIA_DEV_MODE ativo → 401."""
    app, _ = _build_app_with_middleware(dev_mode=False)
    client = TestClient(app)
    resp = client.get("/api/v1/candidates", headers={"X-Dev-Api-Key": "anything"})
    assert resp.status_code == 401


def test_dev_mode_injects_canonical_demo_uuid():
    """Dev fallback deve injetar DEMO_COMPANY_UUID, não a string legada."""
    from app.core.tenant import DEMO_COMPANY_UUID

    app, _ = _build_app_with_middleware(dev_mode=True, dev_api_key="test-key")
    client = TestClient(app)
    resp = client.get(
        "/api/v1/candidates",
        headers={"X-Dev-Api-Key": "test-key"},
    )
    assert resp.status_code == 200
    payload = resp.json()
    assert payload["company_id"] == DEMO_COMPANY_UUID
    assert payload["company_id"] != "demo_company"
    assert payload["user_id"] == "dev-user"


def test_dev_mode_without_dev_key_header_rejects():
    """Dev fallback fail-closed: sem X-Dev-Api-Key → bloqueia."""
    app, _ = _build_app_with_middleware(dev_mode=True, dev_api_key="test-key")
    client = TestClient(app)
    resp = client.get("/api/v1/candidates")
    assert resp.status_code in (401, 403)
