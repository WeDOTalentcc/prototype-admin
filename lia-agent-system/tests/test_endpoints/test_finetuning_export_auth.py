"""Auth/tenant-isolation tests for the fine-tuning export endpoints.

Task #306 — these endpoints used to take ``company_id`` as a path
parameter, which let any caller export another tenant's training data
(IDOR). The path no longer carries ``company_id`` at all; it is derived
exclusively from the JWT-authenticated user.

These tests exercise the real router from
``app/api/v1/finetuning_export.py`` and verify that:
  - An unauthenticated request returns 4xx (401/403 from HTTPBearer).
  - The legacy URL with a ``{company_id}`` segment is no longer routed
    (404), so cross-tenant access via the URL is structurally
    impossible.
  - An authenticated user with no ``company_id`` is rejected with 403.
  - An authenticated user gets stats scoped to their own company,
    derived from the JWT.
"""
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.finetuning_export import router
from app.auth.dependencies import get_current_user
from app.core.database import get_db


MY_COMPANY = "00000000-0000-0000-0000-000000000001"
OTHER_COMPANY = "00000000-0000-0000-0000-000000000002"


def _make_user(company_id):
    user = MagicMock()
    user.id = uuid4()
    user.company_id = company_id
    user.is_active = True
    return user


@pytest.fixture
def app_no_auth():
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_db] = lambda: AsyncMock()
    return app


@pytest.fixture
def app_with_user():
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_db] = lambda: AsyncMock()
    return app


def test_stats_unauthenticated_rejected(app_no_auth):
    client = TestClient(app_no_auth)
    resp = client.get("/finetuning/stats")
    assert resp.status_code in (401, 403)


def test_export_unauthenticated_rejected(app_no_auth):
    client = TestClient(app_no_auth)
    resp = client.post("/finetuning/export")
    assert resp.status_code in (401, 403)


def test_legacy_company_id_path_is_gone(app_with_user):
    """The IDOR-prone ``/finetuning/stats/{company_id}`` and
    ``/finetuning/export/{company_id}`` routes must no longer exist.

    The JWT-derived endpoints take no ``company_id`` segment, so any
    request with one returns 404 (route not found), making cross-tenant
    access via the URL structurally impossible.
    """
    user = _make_user(MY_COMPANY)
    app_with_user.dependency_overrides[get_current_user] = lambda: user

    client = TestClient(app_with_user)
    assert client.get(f"/finetuning/stats/{OTHER_COMPANY}").status_code == 404
    assert client.post(f"/finetuning/export/{OTHER_COMPANY}").status_code == 404


def test_stats_user_without_company_forbidden_and_logged(app_with_user):
    user = _make_user(None)
    app_with_user.dependency_overrides[get_current_user] = lambda: user

    with patch(
        "app.api.v1.finetuning_export.audit_service.log_decision",
        new=AsyncMock(),
    ) as mock_log:
        client = TestClient(app_with_user)
        resp = client.get("/finetuning/stats")

    assert resp.status_code == 403
    assert mock_log.await_count >= 1
    assert mock_log.await_args.kwargs["decision"] == "denied_no_company"
    assert mock_log.await_args.kwargs["action"] == "get_export_stats"


def test_export_user_without_company_forbidden_and_logged(app_with_user):
    user = _make_user(None)
    app_with_user.dependency_overrides[get_current_user] = lambda: user

    with patch(
        "app.api.v1.finetuning_export.audit_service.log_decision",
        new=AsyncMock(),
    ) as mock_log:
        client = TestClient(app_with_user)
        resp = client.post("/finetuning/export")

    assert resp.status_code == 403
    assert mock_log.await_count >= 1
    assert mock_log.await_args.kwargs["decision"] == "denied_no_company"
    assert mock_log.await_args.kwargs["action"] == "trigger_export"


def test_stats_uses_jwt_company(app_with_user):
    """Stats are scoped to the JWT user's company, not anything from the
    URL or query string."""
    user = _make_user(MY_COMPANY)
    app_with_user.dependency_overrides[get_current_user] = lambda: user

    with patch(
        "app.api.v1.finetuning_export.audit_service.log_decision",
        new=AsyncMock(),
    ) as mock_log, patch(
        "app.api.v1.finetuning_export._service.get_export_stats",
        new=AsyncMock(return_value={"total": 0}),
    ) as mock_stats:
        client = TestClient(app_with_user)
        resp = client.get("/finetuning/stats")

    assert resp.status_code == 200
    assert resp.json() == {"total": 0}
    # The service was called with the JWT-derived company_id, not anything
    # from the URL.
    assert mock_stats.await_args.args[0] == MY_COMPANY
    assert any(
        call.kwargs.get("decision") == "allowed" for call in mock_log.await_args_list
    )


def test_export_uses_jwt_company(app_with_user):
    user = _make_user(MY_COMPANY)
    app_with_user.dependency_overrides[get_current_user] = lambda: user

    with patch(
        "app.api.v1.finetuning_export.audit_service.log_decision",
        new=AsyncMock(),
    ), patch(
        "app.api.v1.finetuning_export._service.export_to_file",
        new=AsyncMock(return_value=""),
    ) as mock_export:
        client = TestClient(app_with_user)
        resp = client.post("/finetuning/export")

    assert resp.status_code == 200
    assert resp.json()["company_id"] == MY_COMPANY
    assert mock_export.await_args.args[0] == MY_COMPANY
