"""
Contract tests for the FastAPI → ATS Rails (`ats-api-copia`) HTTP boundary.

These tests stub the Rails endpoints with `respx` and assert the wire-level
behaviour of `WeDOTalentATSClient`:

- Bearer-token auth header is sent.
- JSONAPI envelope (`data` / `meta`) is unwrapped into `RailsAPIResponse`.
- 4xx client errors are non-retryable and surfaced as `success=False`.
- 401 short-circuits with an `Unauthorized` error.
- 5xx triggers retry with exponential backoff (without sleeping in the test).
- Retries are bounded — the client gives up after `retry` attempts.

Together with `test_rails_sync_contracts.py` (which covers the inverse
direction — Rails calling FastAPI's /api/v1/rails-sync/*), these lock the
ATS Integration Boundary defined in §9.8 of the canonical architecture doc.
"""
from __future__ import annotations

import asyncio
import os

import httpx
import pytest
import respx

# Force a deterministic base_url before importing the client module.
os.environ.setdefault("RAILS_API_URL", "http://rails.test")
os.environ.setdefault("RAILS_API_TOKEN", "test-token")

# Recovery #9 (2026-05-23): WeDOTalentATSClient movido em W2-010-B (commit 840d952b3) pra canonical home.
from app.shared.integration.rails_client import (  # noqa: E402
    RailsAPIResponse,
    WeDOTalentATSClient,
)


@pytest.fixture(autouse=True)
def _no_sleep(monkeypatch):
    """Patch out asyncio.sleep so retry/backoff is instant in tests."""
    async def _instant(_seconds):
        return None
    monkeypatch.setattr(
        "app.shared.integration.rails_client.asyncio.sleep",
        _instant,
    )


@pytest.fixture(autouse=True)
def _reset_circuit():
    """Reset the rails circuit breaker between tests so prior failures do
    not leak across cases."""
    from app.shared.resilience.circuit_breaker import RAILS_CIRCUIT, CircuitState

    def _reset() -> None:
        RAILS_CIRCUIT._failure_count = 0
        RAILS_CIRCUIT._success_count = 0
        RAILS_CIRCUIT._state = CircuitState.CLOSED
        RAILS_CIRCUIT._last_failure_time = None

    _reset()
    yield
    _reset()


@pytest.mark.asyncio
@respx.mock
async def test_get_sends_bearer_token_and_unwraps_jsonapi():
    route = respx.get("http://rails.test/v1/users/jobs/42").mock(
        return_value=httpx.Response(
            200,
            json={"data": {"id": "42", "type": "job", "attributes": {"title": "PM"}}},
        )
    )
    client = WeDOTalentATSClient(token="bearer-xyz", base_url="http://rails.test")
    try:
        resp = await client.get("/v1/users/jobs/42")
    finally:
        await client.close()

    assert route.called
    sent = route.calls.last.request
    assert sent.headers["Authorization"] == "Bearer bearer-xyz"
    assert sent.headers["Accept"] == "application/json"

    assert isinstance(resp, RailsAPIResponse)
    assert resp.success is True
    assert resp.status_code == 200
    assert resp.data == {"id": "42", "type": "job", "attributes": {"title": "PM"}}


@pytest.mark.asyncio
@respx.mock
async def test_401_short_circuits_with_unauthorized():
    respx.get("http://rails.test/v1/me").mock(
        return_value=httpx.Response(401, json={"errors": ["bad token"]})
    )
    client = WeDOTalentATSClient(token="x", base_url="http://rails.test")
    try:
        resp = await client.get("/v1/me")
    finally:
        await client.close()

    assert resp.success is False
    assert resp.status_code == 401
    assert "Unauthorized" in resp.errors


@pytest.mark.asyncio
@respx.mock
async def test_4xx_is_non_retryable():
    route = respx.get("http://rails.test/v1/users/jobs/999").mock(
        return_value=httpx.Response(404, json={"errors": ["not found"]})
    )
    client = WeDOTalentATSClient(token="x", base_url="http://rails.test")
    try:
        resp = await client.get("/v1/users/jobs/999")
    finally:
        await client.close()

    # 4xx must NOT trigger retries — exactly one network call.
    assert route.call_count == 1
    assert resp.success is False
    assert resp.status_code == 404
    assert resp.errors == ["not found"]


@pytest.mark.asyncio
@respx.mock
async def test_5xx_retries_then_succeeds():
    """5xx triggers retry; on subsequent success the call resolves cleanly."""
    route = respx.get("http://rails.test/v1/users/jobs").mock(
        side_effect=[
            httpx.Response(500, json={"errors": ["boom"]}),
            httpx.Response(200, json={"data": [], "meta": {"total": 0}}),
        ]
    )
    client = WeDOTalentATSClient(token="x", base_url="http://rails.test")
    try:
        resp = await client.get("/v1/users/jobs")
    finally:
        await client.close()

    assert route.call_count == 2  # one failure + one retry success
    assert resp.success is True
    assert resp.data == []
    assert resp.meta == {"total": 0}


@pytest.mark.asyncio
@respx.mock
async def test_5xx_exhausts_retries_and_returns_error_response():
    """After all retries fail, the client returns a safe error response and
    does NOT raise an exception into the caller."""
    route = respx.get("http://rails.test/v1/users/jobs").mock(
        return_value=httpx.Response(503, json={"errors": ["unavailable"]})
    )
    client = WeDOTalentATSClient(token="x", base_url="http://rails.test")
    try:
        resp = await client.get("/v1/users/jobs")
    finally:
        await client.close()

    # Default retry=3 inside _request → 3 attempts before giving up.
    assert route.call_count == 3
    assert resp.success is False
    assert resp.errors  # non-empty error list
