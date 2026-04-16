"""Tests for dev-auto-login tenant normalization and http_chat_message empty response.

Covers task #282:
- `_extract_auth` in WS/SSE accepts both the new UUID token and the legacy
  `demo_company` string (mapped to DEMO_COMPANY_UUID in dev).
- `http_chat_message` turns an empty agent response into a friendly message
  with `error="agent_empty_response"`.
"""
from __future__ import annotations

import os
from unittest.mock import patch, AsyncMock, MagicMock

import jwt as pyjwt
import pytest

from app.core.config import settings
from app.core.tenant import (
    DEMO_COMPANY_UUID,
    normalize_demo_company_id,
)


# ─────────────────────────────────────────────────────────────────────────
# normalize_demo_company_id / _extract_auth
# ─────────────────────────────────────────────────────────────────────────


def _encode(payload: dict) -> str:
    return pyjwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


@patch.dict(os.environ, {"ENVIRONMENT": "development"}, clear=False)
def test_normalize_maps_legacy_demo_company_in_dev():
    assert normalize_demo_company_id("demo_company") == DEMO_COMPANY_UUID


@patch.dict(os.environ, {"ENVIRONMENT": "development"}, clear=False)
def test_normalize_preserves_valid_uuid():
    uid = "7d2f5f63-0a23-40a4-9f61-3a0b2b2f1c11"
    assert normalize_demo_company_id(uid) == uid


@patch.dict(os.environ, {"ENVIRONMENT": "production"}, clear=False)
def test_normalize_does_not_rewrite_in_production():
    # In production the legacy string is left untouched so we don't
    # silently paper over a misconfigured token.
    assert normalize_demo_company_id("demo_company") == "demo_company"


@patch.dict(os.environ, {"ENVIRONMENT": "development"}, clear=False)
def test_ws_extract_auth_accepts_new_uuid_token():
    from app.api.v1.agent_chat_ws import _extract_auth

    token = _encode({
        "sub": "13cf82fb-f1f6-4205-9377-758e59040148",
        "company_id": DEMO_COMPANY_UUID,
        "role": "admin",
        "type": "access",
    })
    auth = _extract_auth(token)
    assert auth["user_id"] == "13cf82fb-f1f6-4205-9377-758e59040148"
    assert auth["company_id"] == DEMO_COMPANY_UUID


@patch.dict(os.environ, {"ENVIRONMENT": "development"}, clear=False)
def test_ws_extract_auth_normalizes_legacy_demo_company_token():
    from app.api.v1.agent_chat_ws import _extract_auth

    token = _encode({
        "sub": "13cf82fb-f1f6-4205-9377-758e59040148",
        "company_id": "demo_company",
        "role": "admin",
        "type": "access",
    })
    auth = _extract_auth(token)
    assert auth["company_id"] == DEMO_COMPANY_UUID
    assert auth["user_id"] == "13cf82fb-f1f6-4205-9377-758e59040148"


@patch.dict(os.environ, {"ENVIRONMENT": "development"}, clear=False)
def test_sse_extract_auth_normalizes_legacy_demo_company_token():
    from app.api.v1.agent_chat_sse import _extract_auth

    token = _encode({
        "sub": "abc",
        "company_id": "demo_company",
        "type": "access",
    })
    auth = _extract_auth(token)
    assert auth["company_id"] == DEMO_COMPANY_UUID


# ─────────────────────────────────────────────────────────────────────────
# http_chat_message empty response → error="agent_empty_response"
# ─────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
@patch.dict(os.environ, {"ENVIRONMENT": "development"}, clear=False)
async def test_http_chat_message_empty_agent_response_returns_error():
    from app.api.v1 import agent_chat_ws as mod

    token = _encode({
        "sub": "13cf82fb-f1f6-4205-9377-758e59040148",
        "company_id": DEMO_COMPANY_UUID,
        "type": "access",
    })

    fake_output = MagicMock()
    fake_output.message = ""
    fake_output.confidence = 0.0
    fake_output.actions = []
    fake_output.metadata = {}

    fake_agent = MagicMock()
    fake_agent.process = AsyncMock(return_value=fake_output)

    fake_request = MagicMock()
    fake_request.headers = {"authorization": f"Bearer {token}"}

    req = mod.HTTPChatRequest(
        message="oi",
        domain="recruiter_assistant",
        session_id="s-test-empty",
        context={},
    )

    with patch.object(mod, "_get_agent", return_value=fake_agent), \
         patch.object(mod, "check_budget", AsyncMock(return_value=(True, 0, 100000))), \
         patch.object(mod, "get_plan_for_company", AsyncMock(return_value="free")), \
         patch.object(mod, "increment_usage", AsyncMock(return_value=None)):
        resp = await mod.http_chat_message(req, fake_request)

    assert resp.error == "agent_empty_response"
    assert resp.content
    assert resp.content.strip() != ""


@patch.dict(os.environ, {"ENVIRONMENT": "development"}, clear=False)
def test_get_user_company_id_normalizes_legacy_demo_company():
    from app.auth.dependencies import get_user_company_id

    class _U:
        company_id = "demo_company"

    u = _U()
    assert get_user_company_id(u) == DEMO_COMPANY_UUID
    # Side-effect: in-memory user object is normalized as well, so downstream
    # code that reads `user.company_id` sees the canonical UUID.
    assert u.company_id == DEMO_COMPANY_UUID


@patch.dict(os.environ, {"ENVIRONMENT": "development"}, clear=False)
def test_get_user_company_id_preserves_valid_uuid():
    from app.auth.dependencies import get_user_company_id

    class _U:
        company_id = "7d2f5f63-0a23-40a4-9f61-3a0b2b2f1c11"

    u = _U()
    assert get_user_company_id(u) == "7d2f5f63-0a23-40a4-9f61-3a0b2b2f1c11"


@pytest.mark.asyncio
@patch.dict(os.environ, {"ENVIRONMENT": "development"}, clear=False)
async def test_http_chat_message_non_empty_agent_response_unaffected():
    from app.api.v1 import agent_chat_ws as mod

    token = _encode({
        "sub": "13cf82fb-f1f6-4205-9377-758e59040148",
        "company_id": DEMO_COMPANY_UUID,
        "type": "access",
    })

    fake_output = MagicMock()
    fake_output.message = "Olá! Como posso ajudar?"
    fake_output.confidence = 0.9
    fake_output.actions = []
    fake_output.metadata = {}

    fake_agent = MagicMock()
    fake_agent.process = AsyncMock(return_value=fake_output)

    fake_request = MagicMock()
    fake_request.headers = {"authorization": f"Bearer {token}"}

    req = mod.HTTPChatRequest(
        message="oi",
        domain="recruiter_assistant",
        session_id="s-test-ok",
        context={},
    )

    with patch.object(mod, "_get_agent", return_value=fake_agent), \
         patch.object(mod, "check_budget", AsyncMock(return_value=(True, 0, 100000))), \
         patch.object(mod, "get_plan_for_company", AsyncMock(return_value="free")), \
         patch.object(mod, "increment_usage", AsyncMock(return_value=None)):
        resp = await mod.http_chat_message(req, fake_request)

    assert resp.error is None
    assert "Olá" in resp.content
