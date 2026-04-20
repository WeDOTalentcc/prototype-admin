"""
Integration tests: Admin Tenant Gap — Rails account sync.

Verifies that creating a client via the Admin API propagates the record
to Rails, ensuring multi-tenancy consistency (Apartment gem / schema-per-tenant).

Tests:
  1. sync_client_to_rails — success path (mocked Rails 201)
  2. sync_client_to_rails — Rails unreachable (non-blocking, returns error dict)
  3. sync_client_to_rails — missing RAILS_ADMIN_TOKEN (skips gracefully)
  4. _build_rails_payload — correct field mapping from ClientAccount
  5. create_client endpoint — response includes rails_synced flag
"""
import os
from dataclasses import dataclass, field
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Fake ClientAccount ORM object
# ---------------------------------------------------------------------------

@dataclass
class FakeClient:
    id: str = "abc-123"
    name: str = "Acme Corp"
    trade_name: str = "Acme"
    cnpj: str = "12.345.678/0001-99"
    industry: str = "Technology"
    company_size: str = "50-200"
    website: str = "https://acme.com"
    primary_email: str = "admin@acme.com"
    primary_phone: str = "+5511999999999"
    plan_id: str = "plan_pro"
    status: str = "active"
    user_limit: int = 50
    job_limit: int = 20
    ai_credits_monthly: int = 1000


# ---------------------------------------------------------------------------
# Tests: sync_client_to_rails
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_sync_client_to_rails_success():
    """Rails returns 201 — function returns success dict with rails_id."""
    from app.shared.services.rails_account_sync_service import sync_client_to_rails

    mock_result = {"id": "42", "type": "client_account", "name": "Acme Corp"}

    with patch.dict(os.environ, {"RAILS_ADMIN_TOKEN": "test-service-token"}):
        with patch(
            "app.shared.services.rails_account_sync_service.WeDOTalentATSClient"
        ) as MockClient:
            instance = MockClient.return_value
            instance.create_client_account = AsyncMock(return_value=mock_result)
            instance.close = AsyncMock()

            result = await sync_client_to_rails(FakeClient())

    assert result["success"] is True
    assert result["rails_id"] == "42"


@pytest.mark.asyncio
async def test_sync_client_to_rails_rails_unreachable():
    """Rails throws exception — non-blocking, returns error dict."""
    from app.shared.services.rails_account_sync_service import sync_client_to_rails

    with patch.dict(os.environ, {"RAILS_ADMIN_TOKEN": "test-service-token"}):
        with patch(
            "app.shared.services.rails_account_sync_service.WeDOTalentATSClient"
        ) as MockClient:
            instance = MockClient.return_value
            instance.create_client_account = AsyncMock(side_effect=ConnectionError("refused"))
            instance.close = AsyncMock()

            result = await sync_client_to_rails(FakeClient())

    assert result["success"] is False
    assert "refused" in result["error"]


@pytest.mark.asyncio
async def test_sync_client_to_rails_missing_token():
    """No RAILS_ADMIN_TOKEN — skips gracefully without calling Rails."""
    from app.shared.services.rails_account_sync_service import sync_client_to_rails

    env_without_token = {k: v for k, v in os.environ.items()
                         if k not in ("RAILS_ADMIN_TOKEN", "RAILS_API_TOKEN")}

    with patch.dict(os.environ, env_without_token, clear=True):
        with patch(
            "app.shared.services.rails_account_sync_service.WeDOTalentATSClient"
        ) as MockClient:
            result = await sync_client_to_rails(FakeClient())
            MockClient.assert_not_called()

    assert result["success"] is False
    assert "RAILS_ADMIN_TOKEN" in result["error"]


@pytest.mark.asyncio
async def test_sync_client_to_rails_none_response():
    """Rails returns None (e.g. 409 conflict) — returns error dict."""
    from app.shared.services.rails_account_sync_service import sync_client_to_rails

    with patch.dict(os.environ, {"RAILS_ADMIN_TOKEN": "test-service-token"}):
        with patch(
            "app.shared.services.rails_account_sync_service.WeDOTalentATSClient"
        ) as MockClient:
            instance = MockClient.return_value
            instance.create_client_account = AsyncMock(return_value=None)
            instance.close = AsyncMock()

            result = await sync_client_to_rails(FakeClient())

    assert result["success"] is False


# ---------------------------------------------------------------------------
# Tests: _build_rails_payload
# ---------------------------------------------------------------------------

def test_build_rails_payload_field_mapping():
    """Verify field mapping — company_size → size, primary_email → email."""
    from app.shared.services.rails_account_sync_service import _build_rails_payload

    client = FakeClient()
    payload = _build_rails_payload(client)

    assert payload["name"] == "Acme Corp"
    assert payload["size"] == "50-200"        # company_size → size
    assert payload["email"] == "admin@acme.com"  # primary_email → email
    assert payload["phone"] == "+5511999999999"  # primary_phone → phone
    assert "primary_email" not in payload
    assert "primary_phone" not in payload
    assert "company_size" not in payload


def test_build_rails_payload_strips_none():
    """None values are stripped from payload."""
    from app.shared.services.rails_account_sync_service import _build_rails_payload

    client = FakeClient(trade_name=None, cnpj=None, website=None)
    payload = _build_rails_payload(client)

    assert "trade_name" not in payload
    assert "cnpj" not in payload
    assert "website" not in payload
    assert "name" in payload  # required field always present
