"""Sentinela canônica do helper `Depends(require_company_id)` — Task #1143.

Cobre os 4 outcomes do gate (acceptance criteria do task):

  (a) JWT válido + tenant resolvível → 200 + corpo `{"company_id": cid}`.
  (b) JWT válido + body com `company_id` mismatched → 403 (modo strict_match).
  (c) Sem JWT / state ausente → 401.
  (d) `company_id` inválido (``""``, ``"default"``) → 400.

Não depende do TestClient da app real — monta um router FastAPI minimal
in-process e injeta ``request.state.company_id`` manualmente para isolar
o helper do middleware de auth.
"""
from __future__ import annotations

import pytest
from fastapi import Depends, FastAPI, Request
from fastapi.testclient import TestClient

from app.shared.security.require_company_id import (
    require_company_id,
    require_company_id_strict_match,
)

DEMO_UUID = "00000000-0000-4000-a000-000000000001"
OTHER_UUID = "00000000-0000-4000-b000-000000000002"


def _build_app() -> FastAPI:
    app = FastAPI()

    @app.middleware("http")
    async def _inject_state(request: Request, call_next):
        # Mimic AuthEnforcementMiddleware: read `X-Test-Company-Id` and set state.
        # Empty value → simulate unauthenticated request.
        request.state.company_id = request.headers.get("X-Test-Company-Id", "")
        return await call_next(request)

    @app.get("/gated")
    def gated(cid: str = Depends(require_company_id)):
        return {"company_id": cid}

    @app.post("/strict-body")
    async def strict_body(request: Request):
        body = await request.json()

        def _resolve(_request: Request):
            return body.get("company_id")

        gate = require_company_id_strict_match(_resolve)
        cid = await gate(request)
        return {"company_id": cid}

    @app.get("/strict-path/{tenant_id}")
    def strict_path(
        tenant_id: str,
        cid: str = Depends(require_company_id_strict_match("path.tenant_id")),
    ):
        return {"company_id": cid, "path": tenant_id}

    @app.get("/strict-query")
    def strict_query(
        cid: str = Depends(require_company_id_strict_match("query.company_id")),
    ):
        return {"company_id": cid}

    return app


@pytest.fixture(scope="module")
def client() -> TestClient:
    return TestClient(_build_app())


# ---------- (a) happy path ----------

def test_happy_path_uuid(client: TestClient):
    r = client.get("/gated", headers={"X-Test-Company-Id": DEMO_UUID})
    assert r.status_code == 200
    assert r.json() == {"company_id": DEMO_UUID}


def test_happy_path_slug(client: TestClient):
    r = client.get("/gated", headers={"X-Test-Company-Id": "demo_company"})
    assert r.status_code == 200
    assert r.json() == {"company_id": "demo_company"}


# ---------- (c) missing JWT → 401 ----------

def test_missing_jwt_returns_401(client: TestClient):
    r = client.get("/gated")
    assert r.status_code == 401
    assert "Authentication required" in r.json()["detail"]


def test_empty_string_company_id_treated_as_missing(client: TestClient):
    r = client.get("/gated", headers={"X-Test-Company-Id": ""})
    assert r.status_code == 401


# ---------- (d) invalid company_id → 400 ----------

@pytest.mark.parametrize("invalid", ["default", "none", "null", "system", "anonymous", "Default"])
def test_invalid_forbidden_literals_return_400(client: TestClient, invalid: str):
    r = client.get("/gated", headers={"X-Test-Company-Id": invalid})
    assert r.status_code == 400
    assert "Invalid tenant" in r.json()["detail"]


def test_malformed_uuid_returns_400(client: TestClient):
    r = client.get("/gated", headers={"X-Test-Company-Id": "not-a-uuid-nor-slug-!!!"})
    assert r.status_code == 400


# ---------- (b) strict-match mismatch → 403 ----------

def test_strict_path_match_ok(client: TestClient):
    r = client.get(
        f"/strict-path/{DEMO_UUID}",
        headers={"X-Test-Company-Id": DEMO_UUID},
    )
    assert r.status_code == 200


def test_strict_path_mismatch_returns_403(client: TestClient):
    r = client.get(
        f"/strict-path/{OTHER_UUID}",
        headers={"X-Test-Company-Id": DEMO_UUID},
    )
    assert r.status_code == 403
    assert "Tenant mismatch" in r.json()["detail"]


def test_strict_query_match_ok(client: TestClient):
    r = client.get(
        f"/strict-query?company_id={DEMO_UUID}",
        headers={"X-Test-Company-Id": DEMO_UUID},
    )
    assert r.status_code == 200


def test_strict_query_mismatch_returns_403(client: TestClient):
    r = client.get(
        f"/strict-query?company_id={OTHER_UUID}",
        headers={"X-Test-Company-Id": DEMO_UUID},
    )
    assert r.status_code == 403


def test_strict_body_mismatch_returns_403(client: TestClient):
    r = client.post(
        "/strict-body",
        json={"company_id": OTHER_UUID},
        headers={"X-Test-Company-Id": DEMO_UUID},
    )
    assert r.status_code == 403


def test_strict_body_match_ok(client: TestClient):
    r = client.post(
        "/strict-body",
        json={"company_id": DEMO_UUID},
        headers={"X-Test-Company-Id": DEMO_UUID},
    )
    assert r.status_code == 200


def test_strict_body_missing_payload_falls_back_to_jwt(client: TestClient):
    # Payload sem `company_id` ⇒ helper aceita (sem cross-check) e usa JWT.
    r = client.post(
        "/strict-body",
        json={"other": "field"},
        headers={"X-Test-Company-Id": DEMO_UUID},
    )
    assert r.status_code == 200
    assert r.json() == {"company_id": DEMO_UUID}


# ---------- prometheus metric ----------

def test_prometheus_counter_emits_outcomes(client: TestClient):
    """Smoke test: counter is wired and labels are accepted."""
    from app.shared.security import require_company_id as mod

    if mod._REQUIRE_COUNTER is None:
        pytest.skip("prometheus_client not installed in this test env")

    # Exercise both outcomes — should not raise.
    client.get("/gated", headers={"X-Test-Company-Id": DEMO_UUID})
    client.get("/gated")  # missing_jwt
    client.get("/gated", headers={"X-Test-Company-Id": "default"})  # invalid

    # Verify counter has at least one sample
    metric = mod._REQUIRE_COUNTER
    samples = list(metric.collect())
    assert samples, "counter must emit at least one metric family"
