"""
Unit tests for billing API endpoints — targeting app/api/v1/billing.py.
Covers: helper functions, endpoint request/response shapes, security checks.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4, UUID
from datetime import datetime

from app.api.v1.billing import (
    get_user_from_headers,
    require_company_id,
    require_admin,
    log_cross_tenant_attempt,
    verify_company_ownership,
    parse_uuid,

)


# ---------------------------------------------------------------------------
# Pure helper tests (no I/O)
# ---------------------------------------------------------------------------

class TestGetUserFromHeaders:
    def test_extracts_all_headers(self):
        result = get_user_from_headers(
            x_company_id="comp-1",
            x_user_id="user-1",
            x_user_role="admin",
        )
        assert result["company_id"] == "comp-1"
        assert result["user_id"] == "user-1"
        assert result["role"] == "admin"
        assert result["is_admin"] is True

    def test_defaults_when_headers_missing(self):
        result = get_user_from_headers(x_company_id=None, x_user_id=None, x_user_role=None)
        assert result["company_id"] is None
        assert result["user_id"] == "system"
        assert result["role"] == "user"
        assert result["is_admin"] is False

    def test_non_admin_role(self):
        result = get_user_from_headers(x_company_id="c1", x_user_id="u1", x_user_role="user")
        assert result["is_admin"] is False


class TestRequireCompanyId:
    def test_returns_company_id_when_present(self):
        assert require_company_id({"company_id": "abc"}) == "abc"

    def test_raises_401_when_missing(self):
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc:
            require_company_id({"company_id": None})
        assert exc.value.status_code == 401

    def test_raises_401_when_empty_string(self):
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc:
            require_company_id({"company_id": ""})
        assert exc.value.status_code == 401


class TestRequireAdmin:
    def test_passes_for_admin(self):
        # Should not raise
        require_admin({"is_admin": True, "role": "admin"})

    def test_raises_403_for_non_admin(self):
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc:
            require_admin({"is_admin": False, "role": "user"})
        assert exc.value.status_code == 403


class TestParseUuid:
    def test_valid_uuid(self):
        uid = str(uuid4())
        result = parse_uuid(uid)
        assert isinstance(result, UUID)
        assert str(result) == uid

    def test_invalid_uuid_raises_400(self):
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc:
            parse_uuid("not-a-uuid")
        assert exc.value.status_code == 400

    def test_custom_field_name_in_error(self):
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc:
            parse_uuid("bad", field_name="client_id")
        assert "client_id" in str(exc.value.detail)


class TestVerifyCompanyOwnership:
    def test_admin_always_passes(self):
        verify_company_ownership(
            current_user={"is_admin": True, "company_id": "comp-1"},
            target_client_id=str(uuid4()),
            resource_type="subscription",
            resource_id="sub-1",
        )

    def test_matching_company_passes(self):
        cid = str(uuid4())
        verify_company_ownership(
            current_user={"is_admin": False, "company_id": cid},
            target_client_id=cid,
            resource_type="subscription",
            resource_id="sub-1",
        )

    def test_mismatched_company_raises_403(self):
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc:
            verify_company_ownership(
                current_user={"is_admin": False, "company_id": str(uuid4())},
                target_client_id=str(uuid4()),
                resource_type="subscription",
                resource_id="sub-1",
            )
        assert exc.value.status_code == 403


class TestLogCrossTenantAttempt:
    def test_does_not_raise(self):
        """Just ensure it logs without error."""
        log_cross_tenant_attempt(
            action="access",
            user_company_id="comp-a",
            target_company_id="comp-b",
            user_id="u1",
            resource_type="subscription",
            resource_id="sub-1",
        )


# ---------------------------------------------------------------------------
# Billing API endpoint tests using httpx + ASGITransport
# ---------------------------------------------------------------------------
from fastapi import FastAPI
from fastapi.testclient import TestClient

# Import the router
from app.api.v1.billing import router as billing_router


def _make_app():
    app = FastAPI()
    app.include_router(billing_router, prefix="/api/v1")
    return app


class TestBillingStatusEndpoint:
    @pytest.mark.asyncio
    async def test_missing_company_id_returns_401(self):
        from httpx import AsyncClient, ASGITransport
        app = _make_app()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.get("/api/v1/billing/status")
            assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_status_returns_200_with_mocked_service(self):
        from httpx import AsyncClient, ASGITransport
        from app.core.database import get_tenant_db

        mock_provider = MagicMock()
        mock_provider.is_configured.return_value = True

        mock_billing_service = MagicMock()
        mock_billing_service.get_provider.return_value = mock_provider

        app = _make_app()

        # Override get_tenant_db so no real DB connection is created
        mock_db_session = AsyncMock()
        mock_db_session.execute = AsyncMock(
            return_value=MagicMock(
                scalar_one_or_none=lambda: None,
                scalar=lambda: None,
            )
        )

        async def override_get_tenant_db():
            yield mock_db_session

        app.dependency_overrides[get_tenant_db] = override_get_tenant_db

        with patch("app.api.v1.billing.BillingService", return_value=mock_billing_service):
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as ac:
                resp = await ac.get(
                    "/api/v1/billing/status",
                    headers={"X-Company-ID": str(uuid4())},
                )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"


class TestListSubscriptionsEndpoint:
    @pytest.mark.asyncio
    async def test_missing_company_returns_401(self):
        from httpx import AsyncClient, ASGITransport
        app = _make_app()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.get("/api/v1/billing/subscriptions")
            assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_list_subscriptions_returns_data(self):
        from httpx import AsyncClient, ASGITransport

        mock_sub = MagicMock()
        mock_sub.to_dict.return_value = {"id": str(uuid4()), "status": "active"}

        mock_repo = AsyncMock()
        mock_repo.list_subscriptions = AsyncMock(return_value=[mock_sub])
        mock_repo.count_subscriptions = AsyncMock(return_value=1)
        mock_repo.db = MagicMock()

        app = _make_app()

        from app.domains.billing.dependencies import get_billing_repo
        app.dependency_overrides[get_billing_repo] = lambda: mock_repo

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            resp = await ac.get(
                "/api/v1/billing/subscriptions",
                headers={"X-Company-ID": str(uuid4())},
            )
            assert resp.status_code == 200
            body = resp.json()
            assert body["success"] is True
            assert len(body["data"]["subscriptions"]) == 1


class TestCreateSubscriptionEndpoint:
    @pytest.mark.asyncio
    async def test_non_admin_returns_403(self):
        from httpx import AsyncClient, ASGITransport

        app = _make_app()
        mock_repo = AsyncMock()
        mock_repo.db = MagicMock()

        from app.domains.billing.dependencies import get_billing_repo
        app.dependency_overrides[get_billing_repo] = lambda: mock_repo

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            resp = await ac.post(
                "/api/v1/billing/subscriptions",
                headers={
                    "X-Company-ID": str(uuid4()),
                    "X-User-Role": "user",
                },
                json={
                    "client_id": str(uuid4()),
                    "plan_code": "pro",
                    "plan_name": "Pro Plan",
                    "price_cents": 9900,
                    "provider": "iugu",
                },
            )
            assert resp.status_code == 403


class TestBillingPydanticModels:
    """Test the Pydantic response models defined in billing.py."""

    def test_webhook_processed_response(self):
        from app.api.v1.billing import WebhookProcessedResponse
        r = WebhookProcessedResponse(status="ok", processed=True, message="OK")
        assert r.processed is True

    def test_billing_operation_response(self):
        from app.api.v1.billing import BillingOperationResponse
        r = BillingOperationResponse(success=True, operation="create", message="done")
        assert r.operation == "create"

    def test_usage_data(self):
        from app.api.v1.billing import UsageData
        u = UsageData(
            ai_credits_used=100,
            ai_credits_limit=1000,
            active_jobs=5,
            jobs_limit=50,
            period_start="2024-01-01",
            period_end="2024-01-31",
        )
        assert u.ai_credits_used == 100

    def test_client_billing_data(self):
        from app.api.v1.billing import ClientBillingData
        d = ClientBillingData(
            client_id=str(uuid4()),
            client_name="Test Corp",
        )
        assert d.client_name == "Test Corp"

    def test_subscription_settings_wrapper(self):
        from app.api.v1.billing import SubscriptionSettingsWrapper
        w = SubscriptionSettingsWrapper(success=True, data={"plan": "basic"})
        assert w.success is True
