"""Auth/tenant-isolation tests for the fine-tuning export endpoints.

These exercise the real router from `app/api/v1/finetuning_export.py` and
verify that:
  - An unauthenticated request returns 4xx (401/403 from HTTPBearer).
  - A cross-tenant request (authenticated user whose company_id does not
    match the path company_id) returns 403.
  - A user with no company_id returns 404.
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
    resp = client.get(f"/finetuning/stats/{MY_COMPANY}")
    assert resp.status_code in (401, 403)


def test_export_unauthenticated_rejected(app_no_auth):
    client = TestClient(app_no_auth)
    resp = client.post(f"/finetuning/export/{MY_COMPANY}")
    assert resp.status_code in (401, 403)


def test_stats_cross_tenant_forbidden(app_with_user):
    user = _make_user(MY_COMPANY)
    app_with_user.dependency_overrides[get_current_user] = lambda: user

    with patch(
        "app.api.v1.finetuning_export.audit_service.log_decision",
        new=AsyncMock(),
    ) as mock_log:
        client = TestClient(app_with_user)
        resp = client.get(f"/finetuning/stats/{OTHER_COMPANY}")

    assert resp.status_code == 403
    assert mock_log.await_count >= 1
    kwargs = mock_log.await_args.kwargs
    assert kwargs["decision"] == "denied_cross_tenant"


def test_export_cross_tenant_forbidden(app_with_user):
    user = _make_user(MY_COMPANY)
    app_with_user.dependency_overrides[get_current_user] = lambda: user

    with patch(
        "app.api.v1.finetuning_export.audit_service.log_decision",
        new=AsyncMock(),
    ) as mock_log:
        client = TestClient(app_with_user)
        resp = client.post(f"/finetuning/export/{OTHER_COMPANY}")

    assert resp.status_code == 403
    assert mock_log.await_count >= 1


def test_user_without_company_gets_404(app_with_user):
    user = _make_user(None)
    app_with_user.dependency_overrides[get_current_user] = lambda: user

    with patch(
        "app.api.v1.finetuning_export.audit_service.log_decision",
        new=AsyncMock(),
    ):
        client = TestClient(app_with_user)
        resp = client.get(f"/finetuning/stats/{MY_COMPANY}")

    assert resp.status_code == 404


def test_stats_same_tenant_allowed_and_logged(app_with_user):
    user = _make_user(MY_COMPANY)
    app_with_user.dependency_overrides[get_current_user] = lambda: user

    with patch(
        "app.api.v1.finetuning_export.audit_service.log_decision",
        new=AsyncMock(),
    ) as mock_log, patch(
        "app.api.v1.finetuning_export._service.get_export_stats",
        new=AsyncMock(return_value={"total": 0}),
    ):
        client = TestClient(app_with_user)
        resp = client.get(f"/finetuning/stats/{MY_COMPANY}")

    assert resp.status_code == 200
    assert resp.json() == {"total": 0}
    assert any(
        call.kwargs.get("decision") == "allowed" for call in mock_log.await_args_list
    )
