"""
Tests for billing endpoints — real production router with mocked BillingService/BillingRepository.

Mounts the actual router from app/api/v1/billing.py.
Patched surfaces:
  - get_billing_repo FastAPI dependency override
  - app.api.v1.billing.BillingService (patched per test via patch context)

Multi-tenant security tests exercise the REAL production code:
  - require_company_id() → 401 when X-Company-ID header is missing
  - verify_company_ownership() → 403 when user's company_id ≠ target client_id

Coverage:
  200 — GET /billing/status with X-Company-ID header
  401 — GET /billing/status without X-Company-ID header
  403 — GET /billing/subscriptions/{client_id} with wrong company (cross-tenant)
  422 — POST /billing/subscriptions with missing required fields
  404 — GET /billing/subscriptions/{client_id} where subscription does not exist
  Static — require_company_id and verify_company_ownership present in production code
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import FastAPI
from fastapi.testclient import TestClient

MY_COMPANY_UUID = "00000000-0000-0000-0000-000000000001"
OTHER_COMPANY_UUID = "00000000-0000-0000-0000-000000000002"
MY_COMPANY_HEADERS = {"X-Company-ID": MY_COMPANY_UUID}
ADMIN_HEADERS = {"X-Company-ID": MY_COMPANY_UUID, "X-User-Role": "admin"}
USER_HEADERS = {"X-Company-ID": MY_COMPANY_UUID, "X-User-Role": "user"}


@pytest.fixture(scope="module")
def billing_app():
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

    from app.api.v1.billing import router
    from app.domains.billing.dependencies import get_billing_repo

    app = FastAPI()
    app.include_router(router)

    mock_repo = MagicMock()
    mock_repo.db = MagicMock()
    mock_repo.list_subscriptions = AsyncMock(return_value=[])
    mock_repo.count_subscriptions = AsyncMock(return_value=0)
    mock_repo.get_latest_subscription_by_client = AsyncMock(return_value=None)
    mock_repo.get_invoices_paginated = AsyncMock(return_value=([], 0))
    mock_repo.get_invoice_by_id = AsyncMock(return_value=None)
    mock_repo.get_payment_methods_by_client = AsyncMock(return_value=[])
    app.dependency_overrides[get_billing_repo] = lambda: mock_repo

    return app


def _mock_billing_service(*, sub=None, providers_ok=True):
    """Produce a configured BillingService mock."""
    mock_svc = MagicMock()

    def get_provider(name):
        if not providers_ok:
            raise Exception(f"Provider {name} not configured")
        provider = MagicMock()
        provider.is_configured.return_value = True
        return provider

    mock_svc.get_provider = get_provider
    mock_svc.get_active_subscription = AsyncMock(return_value=sub)
    mock_svc.create_subscription = AsyncMock(return_value=MagicMock(
        to_dict=lambda: {"id": "sub-001", "status": "active"}
    ))
    mock_svc.cancel_subscription = AsyncMock(return_value=MagicMock(
        to_dict=lambda: {"id": "sub-001", "status": "canceled"}
    ))
    mock_svc.process_webhook = AsyncMock(return_value={"processed": True})
    return mock_svc


# ---------------------------------------------------------------------------
# GET /billing/status
# ---------------------------------------------------------------------------

class TestBillingStatus:
    def test_missing_company_header_returns_401(self, billing_app):
        client = TestClient(billing_app, raise_server_exceptions=False)
        resp = client.get('/billing/status')
        assert resp.status_code == 401

    def test_with_company_header_returns_200(self, billing_app):
        with patch('app.api.v1.billing.BillingService', return_value=_mock_billing_service()):
            client = TestClient(billing_app, raise_server_exceptions=False)
            resp = client.get('/billing/status', headers=MY_COMPANY_HEADERS)
        assert resp.status_code == 200

    def test_response_has_status_field(self, billing_app):
        with patch('app.api.v1.billing.BillingService', return_value=_mock_billing_service()):
            client = TestClient(billing_app, raise_server_exceptions=False)
            body = client.get('/billing/status', headers=MY_COMPANY_HEADERS).json()
        assert "status" in body

    def test_401_detail_mentions_company_id(self, billing_app):
        client = TestClient(billing_app, raise_server_exceptions=False)
        body = client.get('/billing/status').json()
        assert "X-Company-ID" in body.get("detail", "")


# ---------------------------------------------------------------------------
# GET /billing/subscriptions/{client_id} — multi-tenant isolation
# ---------------------------------------------------------------------------

class TestSubscriptionTenantIsolation:
    def test_same_company_admin_can_access(self, billing_app):
        with patch('app.api.v1.billing.BillingService', return_value=_mock_billing_service()):
            client = TestClient(billing_app, raise_server_exceptions=False)
            resp = client.get(
                f'/billing/subscriptions/{MY_COMPANY_UUID}',
                headers={**ADMIN_HEADERS}
            )
        assert resp.status_code in (200, 404)

    def test_cross_tenant_access_returns_403(self, billing_app):
        user_headers = {
            "X-Company-ID": MY_COMPANY_UUID,
            "X-User-Role": "user"
        }
        client = TestClient(billing_app, raise_server_exceptions=False)
        resp = client.get(
            f'/billing/subscriptions/{OTHER_COMPANY_UUID}',
            headers=user_headers
        )
        assert resp.status_code == 403

    def test_403_detail_mentions_access_denied(self, billing_app):
        user_headers = {"X-Company-ID": MY_COMPANY_UUID, "X-User-Role": "user"}
        client = TestClient(billing_app, raise_server_exceptions=False)
        body = client.get(
            f'/billing/subscriptions/{OTHER_COMPANY_UUID}',
            headers=user_headers
        ).json()
        assert "Access denied" in body.get("detail", "")

    def test_missing_company_header_returns_401(self, billing_app):
        client = TestClient(billing_app, raise_server_exceptions=False)
        resp = client.get(f'/billing/subscriptions/{MY_COMPANY_UUID}')
        assert resp.status_code == 401

    def test_subscription_not_found_returns_404(self, billing_app):
        with patch('app.api.v1.billing.BillingService', return_value=_mock_billing_service(sub=None)):
            client = TestClient(billing_app, raise_server_exceptions=False)
            resp = client.get(
                f'/billing/subscriptions/{MY_COMPANY_UUID}',
                headers=ADMIN_HEADERS
            )
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# GET /billing/subscriptions — admin list
# ---------------------------------------------------------------------------

class TestListSubscriptions:
    def test_missing_company_header_returns_401(self, billing_app):
        client = TestClient(billing_app, raise_server_exceptions=False)
        resp = client.get('/billing/subscriptions')
        assert resp.status_code == 401

    def test_admin_with_header_returns_200(self, billing_app):
        with patch('app.api.v1.billing.BillingService', return_value=_mock_billing_service()):
            client = TestClient(billing_app, raise_server_exceptions=False)
            resp = client.get('/billing/subscriptions', headers=ADMIN_HEADERS)
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# POST /billing/subscriptions — create subscription
# ---------------------------------------------------------------------------

class TestCreateSubscription:
    def test_missing_required_field_returns_422(self, billing_app):
        client = TestClient(billing_app, raise_server_exceptions=False)
        resp = client.post('/billing/subscriptions', json={}, headers=ADMIN_HEADERS)
        assert resp.status_code == 422

    def test_non_admin_returns_403(self, billing_app):
        client = TestClient(billing_app, raise_server_exceptions=False)
        resp = client.post('/billing/subscriptions', json={
            "client_id": MY_COMPANY_UUID,
            "plan_code": "professional"
        }, headers=USER_HEADERS)
        assert resp.status_code == 403

    def test_missing_plan_code_returns_422(self, billing_app):
        client = TestClient(billing_app, raise_server_exceptions=False)
        resp = client.post('/billing/subscriptions', json={
            "client_id": MY_COMPANY_UUID
        }, headers=ADMIN_HEADERS)
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Webhook endpoints (no auth needed)
# ---------------------------------------------------------------------------

class TestWebhooks:
    def test_iugu_webhook_returns_200_with_processed_true(self, billing_app):
        with patch('app.api.v1.billing.BillingService', return_value=_mock_billing_service()):
            client = TestClient(billing_app, raise_server_exceptions=False)
            resp = client.post('/billing/webhooks/iugu', json={"event": "invoice.paid"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["processed"] is True
        assert body["status"] == "ok"

    def test_vindi_webhook_returns_200_with_processed_true(self, billing_app):
        with patch('app.api.v1.billing.BillingService', return_value=_mock_billing_service()):
            client = TestClient(billing_app, raise_server_exceptions=False)
            resp = client.post('/billing/webhooks/vindi', json={"event": "charge.paid"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["processed"] is True
        assert body["status"] == "ok"


# ---------------------------------------------------------------------------
# Static code quality: multi-tenant security helpers must exist
# ---------------------------------------------------------------------------

from pathlib import Path
_PROJECT_ROOT = Path(__file__).parent.parent.parent


def _read(path: str) -> str:
    return (_PROJECT_ROOT / path).read_text()


def test_require_company_id_defined_in_billing():
    content = _read("app/api/v1/billing.py")
    assert "def require_company_id(" in content


def test_verify_company_ownership_defined_in_billing():
    content = _read("app/api/v1/billing.py")
    assert "def verify_company_ownership(" in content


def test_require_company_id_raises_401():
    content = _read("app/api/v1/billing.py")
    assert "HTTP_401_UNAUTHORIZED" in content


def test_verify_company_ownership_raises_403():
    content = _read("app/api/v1/billing.py")
    assert "HTTP_403_FORBIDDEN" in content


def test_get_user_from_headers_reads_x_company_id():
    content = _read("app/api/v1/billing.py")
    assert "X-Company-ID" in content


def test_billing_status_endpoint_calls_require_company_id():
    content = _read("app/api/v1/billing.py")
    assert "require_company_id(current_user)" in content


def test_subscription_endpoint_calls_verify_ownership():
    content = _read("app/api/v1/billing.py")
    assert "verify_company_ownership(" in content
