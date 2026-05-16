"""Real-endpoint integration tests for require_company_id_strict_match wiring.

Task #1143 acceptance criterion (d): mismatch between JWT-resolved
``request.state.company_id`` and the explicit ``company_id`` carried in
path / query / body / form must return HTTP 403.

These tests import the actual production routers (not synthetic stand-ins),
mock the downstream service to a no-op, mount them on a FastAPI app with the
same X-Test-Company-Id middleware shim used by the helper-level suite, and
exercise the 200 / 401 / 400 / 403 matrix end-to-end.
"""
from __future__ import annotations

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient


DEMO = "00000000-0000-4000-a000-000000000001"
OTHER = "00000000-0000-4000-b000-000000000002"


@pytest.fixture
def attachments_client(monkeypatch):
    """Mount app/api/v1/attachments.py with attachment_service mocked."""

    class _FakeService:
        async def list_attachments(self, **kw):
            return {
                "attachments": [],
                "total": 0,
                "limit": kw.get("limit", 50),
                "offset": kw.get("offset", 0),
            }

        async def get_candidate_attachments(self, **kw):
            return {
                "attachments": [],
                "total": 0,
                "limit": kw.get("limit", 50),
                "offset": kw.get("offset", 0),
            }

    monkeypatch.setattr(
        "app.shared.services.attachment_service.attachment_service",
        _FakeService(),
    )
    # Some modules import the symbol directly, re-bind there too.
    import app.api.v1.attachments as attachments_module
    monkeypatch.setattr(attachments_module, "attachment_service", _FakeService())

    app = FastAPI()

    @app.middleware("http")
    async def _inject(request: Request, call_next):
        request.state.company_id = request.headers.get("X-Test-Company-Id", "")
        return await call_next(request)

    app.include_router(attachments_module.router)
    app.include_router(attachments_module.candidate_attachments_router)
    return TestClient(app, raise_server_exceptions=False)


# ---------- list_attachments (query.company_id strict_match) ----------

def test_list_attachments_200_when_query_matches_jwt(attachments_client):
    r = attachments_client.get(
        "/attachments",
        params={"company_id": DEMO},
        headers={"X-Test-Company-Id": DEMO},
    )
    assert r.status_code == 200, r.text


def test_list_attachments_403_when_query_mismatches_jwt(attachments_client):
    r = attachments_client.get(
        "/attachments",
        params={"company_id": OTHER},
        headers={"X-Test-Company-Id": DEMO},
    )
    assert r.status_code == 403, r.text


def test_list_attachments_401_when_no_jwt(attachments_client):
    r = attachments_client.get(
        "/attachments",
        params={"company_id": DEMO},
        # no X-Test-Company-Id → state.company_id == "" → 401
    )
    assert r.status_code == 401, r.text


def test_list_attachments_400_when_jwt_invalid(attachments_client):
    r = attachments_client.get(
        "/attachments",
        params={"company_id": DEMO},
        headers={"X-Test-Company-Id": "default"},  # placeholder is invalid
    )
    assert r.status_code == 400, r.text


# ---------- get_candidate_attachments (query.company_id strict_match) ----------

def test_candidate_attachments_403_on_mismatch(attachments_client):
    r = attachments_client.get(
        "/candidates/cand-1/attachments",
        params={"company_id": OTHER},
        headers={"X-Test-Company-Id": DEMO},
    )
    assert r.status_code == 403, r.text


def test_candidate_attachments_200_on_match(attachments_client):
    r = attachments_client.get(
        "/candidates/cand-1/attachments",
        params={"company_id": DEMO},
        headers={"X-Test-Company-Id": DEMO},
    )
    assert r.status_code == 200, r.text


# ---------- form.company_id strict_match accessor ----------

@pytest.fixture
def form_client():
    """Mount a synthetic endpoint that uses strict_match("form.company_id")."""
    from fastapi import Depends, Form
    from app.shared.security.require_company_id import require_company_id_strict_match

    app = FastAPI()

    @app.middleware("http")
    async def _inject(request: Request, call_next):
        request.state.company_id = request.headers.get("X-Test-Company-Id", "")
        return await call_next(request)

    @app.post("/form-upload")
    async def _upload(
        company_id: str = Form(...),
        _gate: str = Depends(require_company_id_strict_match("form.company_id")),
    ):
        return {"ok": True, "company_id": company_id}

    return TestClient(app, raise_server_exceptions=False)


def test_form_strict_match_200_on_match(form_client):
    r = form_client.post(
        "/form-upload",
        data={"company_id": DEMO},
        headers={"X-Test-Company-Id": DEMO},
    )
    assert r.status_code == 200, r.text


def test_form_strict_match_403_on_mismatch(form_client):
    r = form_client.post(
        "/form-upload",
        data={"company_id": OTHER},
        headers={"X-Test-Company-Id": DEMO},
    )
    assert r.status_code == 403, r.text


def test_form_strict_match_400_on_invalid_form_value(form_client):
    r = form_client.post(
        "/form-upload",
        data={"company_id": "default"},  # placeholder rejected by CompanyId.parse
        headers={"X-Test-Company-Id": DEMO},
    )
    assert r.status_code == 400, r.text


# ---------- body.company_id strict_match accessor ----------

@pytest.fixture
def body_client():
    from app.shared.security.require_company_id import require_company_id_strict_match

    app = FastAPI()

    @app.middleware("http")
    async def _inject(request: Request, call_next):
        request.state.company_id = request.headers.get("X-Test-Company-Id", "")
        return await call_next(request)

    @app.post("/body-action")
    async def _action(request: Request):
        # Read body BEFORE the gate (helper will re-await; starlette caches).
        body = await request.json()
        gate = require_company_id_strict_match("body.company_id")
        cid = await gate(request)
        return {"ok": True, "company_id": cid, "echo": body.get("note", "")}

    return TestClient(app, raise_server_exceptions=False)


def test_body_strict_match_403_on_mismatch(body_client):
    r = body_client.post(
        "/body-action",
        json={"company_id": OTHER, "note": "x"},
        headers={"X-Test-Company-Id": DEMO},
    )
    assert r.status_code == 403, r.text


def test_body_strict_match_200_on_match(body_client):
    r = body_client.post(
        "/body-action",
        json={"company_id": DEMO, "note": "x"},
        headers={"X-Test-Company-Id": DEMO},
    )
    assert r.status_code == 200, r.text


# ---------- middleware-public regression: 3 newly-allowlisted public routes ----------

@pytest.mark.parametrize(
    "module_path,attr,path",
    [
        ("app.api.v1.rails_health", "router", "/rails/health"),
        ("app.api.v1.rails_health", "router", "/rails/status"),
        ("app.api.v1.health_langgraph", "router", "/health/langgraph"),
        ("app.api.v1.navigation_intent", "router", ""),
    ],
)
def test_public_routes_no_jwt_required(module_path, attr, path, monkeypatch):
    """Regression: routes in PUBLIC_PATHS must NOT carry require_company_id.

    Loads the router with NO X-Test-Company-Id header — if the gate was
    re-introduced by a future sweep, it would 401 here instead of attempting
    the handler.
    """
    import importlib
    mod = importlib.import_module(module_path)
    router = getattr(mod, attr)

    app = FastAPI()

    @app.middleware("http")
    async def _inject(request: Request, call_next):
        # Simulate AuthEnforcementMiddleware short-circuit on PUBLIC_PATHS:
        # state.company_id is NEVER set on public requests.
        return await call_next(request)

    app.include_router(router)
    client = TestClient(app, raise_server_exceptions=False)

    # GET for health endpoints, POST for navigation-intent.
    if path == "":
        r = client.post("", json={"text": "ir para vagas"})
    else:
        r = client.get(path)

    # The route MAY 200/422/500 depending on downstream — what it MUST NOT do
    # is 401 ("Authentication required: no tenant context.") from
    # require_company_id. That would prove a gate was re-introduced.
    assert r.status_code != 401, (
        f"REGRESSION: {module_path}{path} returned 401 — require_company_id "
        f"was re-introduced on a middleware-public route. Body: {r.text}"
    )
