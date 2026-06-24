"""Tests for the mock HTTP transport fixture (GAP-08-006).

Tests the fixture itself + provides an example integration test pattern
that downstream tests can follow.
"""
from __future__ import annotations

import pytest
import httpx

from tests.fixtures.mock_http import MockResponse, _MockClient, _MockTransport


# ---------------------------------------------------------------------------
# Tests for MockResponse
# ---------------------------------------------------------------------------

class TestMockResponse:
    def test_default_status_200(self):
        r = MockResponse()
        assert r.status_code == 200

    def test_json_serialised_to_text(self):
        r = MockResponse(json={"key": "value"})
        assert '"key"' in r.text
        assert '"value"' in r.text

    def test_text_passthrough(self):
        r = MockResponse(text="hello")
        assert r.text == "hello"

    def test_json_wins_over_text(self):
        r = MockResponse(json={"a": 1}, text="should be ignored")
        assert '"a"' in r.text

    def test_custom_headers(self):
        r = MockResponse(headers={"x-custom": "yes"})
        assert r.headers["x-custom"] == "yes"

    def test_status_code_passthrough(self):
        r = MockResponse(404)
        assert r.status_code == 404


# ---------------------------------------------------------------------------
# Tests for the fixture itself
# ---------------------------------------------------------------------------

class TestMockHttpClient:
    def test_returns_async_client(self, mock_http_client):
        assert isinstance(mock_http_client, httpx.AsyncClient)

    def test_has_register_method(self, mock_http_client):
        assert callable(mock_http_client.register)

    def test_has_reset_method(self, mock_http_client):
        assert callable(mock_http_client.reset)

    @pytest.mark.asyncio
    async def test_registered_get_returns_200(self, mock_http_client):
        mock_http_client.register(
            "GET",
            "https://api.example.com/data",
            MockResponse(200, json={"ok": True}),
        )
        resp = await mock_http_client.get("https://api.example.com/data")
        assert resp.status_code == 200
        assert resp.json() == {"ok": True}

    @pytest.mark.asyncio
    async def test_registered_post_returns_201(self, mock_http_client):
        mock_http_client.register(
            "POST",
            "https://api.example.com/items",
            MockResponse(201, json={"id": 42}),
        )
        resp = await mock_http_client.post("https://api.example.com/items", json={})
        assert resp.status_code == 201
        assert resp.json()["id"] == 42

    @pytest.mark.asyncio
    async def test_unregistered_route_returns_404(self, mock_http_client):
        """Unregistered routes should return 404 with a helpful error body."""
        resp = await mock_http_client.get("https://api.example.com/unknown")
        assert resp.status_code == 404
        body = resp.json()
        assert body["error"] == "mock_not_registered"
        assert "GET" in body["method"]

    @pytest.mark.asyncio
    async def test_method_normalised_to_upper(self, mock_http_client):
        """register() should accept lowercase method names."""
        mock_http_client.register(
            "get",  # lowercase
            "https://api.example.com/x",
            MockResponse(200, json={"x": 1}),
        )
        resp = await mock_http_client.get("https://api.example.com/x")
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_reset_clears_registered_routes(self, mock_http_client):
        mock_http_client.register(
            "GET",
            "https://api.example.com/y",
            MockResponse(200, json={"y": 1}),
        )
        mock_http_client.reset()
        resp = await mock_http_client.get("https://api.example.com/y")
        assert resp.status_code == 404  # cleared → unregistered

    @pytest.mark.asyncio
    async def test_error_response_passthrough(self, mock_http_client):
        """500 responses should be returned as-is (not raised)."""
        mock_http_client.register(
            "GET",
            "https://api.example.com/err",
            MockResponse(500, json={"error": "server_error"}),
        )
        resp = await mock_http_client.get("https://api.example.com/err")
        assert resp.status_code == 500

    @pytest.mark.asyncio
    async def test_text_body_response(self, mock_http_client):
        mock_http_client.register(
            "GET",
            "https://api.example.com/text",
            MockResponse(200, text="plain text"),
        )
        resp = await mock_http_client.get("https://api.example.com/text")
        assert resp.status_code == 200
        assert resp.text == "plain text"

    @pytest.mark.asyncio
    async def test_custom_response_headers(self, mock_http_client):
        mock_http_client.register(
            "GET",
            "https://api.example.com/h",
            MockResponse(200, json={}, headers={"x-trace": "abc123"}),
        )
        resp = await mock_http_client.get("https://api.example.com/h")
        assert resp.headers["x-trace"] == "abc123"

    @pytest.mark.asyncio
    async def test_unregistered_route_lists_registered(self, mock_http_client):
        """404 body should include registered routes for debugging."""
        mock_http_client.register("GET", "https://api.example.com/a", MockResponse(200))
        resp = await mock_http_client.get("https://api.example.com/b")
        body = resp.json()
        assert any("api.example.com/a" in r for r in body.get("registered_routes", []))


# ---------------------------------------------------------------------------
# Example integration-style test (documents the pattern)
# ---------------------------------------------------------------------------

class TestExampleHttpMockPattern:
    """Documents how to use mock_http_client in integration tests.

    This is the canonical pattern for any test that would otherwise
    call a real external API.
    """

    @pytest.mark.asyncio
    async def test_external_api_mock(self, mock_http_client):
        """Canonical example: GET request returns expected JSON."""
        mock_http_client.register(
            "GET",
            "https://api.example.com/data",
            MockResponse(200, json={"ok": True}),
        )
        response = await mock_http_client.get("https://api.example.com/data")
        assert response.json() == {"ok": True}

    @pytest.mark.asyncio
    async def test_service_handles_external_api_error(self, mock_http_client):
        """Canonical example: service should handle 503 gracefully."""
        mock_http_client.register(
            "POST",
            "https://api.vendor.com/send",
            MockResponse(503, json={"error": "Service Unavailable"}),
        )
        resp = await mock_http_client.post("https://api.vendor.com/send", json={})
        assert resp.status_code == 503
        # Callers should not raise — just return status; test that service
        # propagates error signals rather than silently swallowing them.
        assert resp.json()["error"] == "Service Unavailable"
