"""Reusable mock HTTP transport for integration tests (GAP-08-006).

Provides a pytest fixture ``mock_http_client`` backed by httpx's built-in
async transport protocol — no third-party library required.

Usage in tests::

    async def test_something(mock_http_client):
        mock_http_client.register("GET", "https://api.example.com/data",
                                  MockResponse(200, json={"ok": True}))
        resp = await mock_http_client.get("https://api.example.com/data")
        assert resp.json() == {"ok": True}

``MockResponse`` mirrors the subset of ``httpx.Response`` that most callers
inspect: ``status_code``, ``json``, ``text``, and ``headers``.
"""
from __future__ import annotations

import json as _json_mod
from typing import Any

import httpx
import pytest


# ---------------------------------------------------------------------------
# MockResponse — lightweight description of a canned HTTP response
# ---------------------------------------------------------------------------

class MockResponse:
    """Lightweight description of a canned HTTP response.

    Args:
        status_code: HTTP status code (default 200).
        json: Python object to serialise as JSON body.  Mutually exclusive
              with *text* — if both are given, *json* wins.
        text: Plain-text body (default ``""``).
        headers: Extra response headers.
    """

    def __init__(
        self,
        status_code: int = 200,
        *,
        json: Any = None,
        text: str = "",
        headers: dict[str, str] | None = None,
    ) -> None:
        self.status_code = status_code
        self.json = json
        self.text = text if json is None else _json_mod.dumps(json)
        self.headers = headers or {}

    def __repr__(self) -> str:  # pragma: no cover
        return f"MockResponse({self.status_code})"


# ---------------------------------------------------------------------------
# MockTransport — httpx.AsyncBaseTransport implementation
# ---------------------------------------------------------------------------

class _MockTransport(httpx.AsyncBaseTransport):
    """An ``httpx.AsyncBaseTransport`` that serves canned responses.

    Registered via ``(METHOD, url_str) → MockResponse``.  Falls back to
    a 404 MockResponse for unknown routes so tests fail loudly on surprise
    requests rather than hanging on a real network call.
    """

    def __init__(self, responses: dict[tuple[str, str], MockResponse]) -> None:
        self._responses = responses

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        key = (request.method.upper(), str(request.url))
        mock = self._responses.get(key)

        if mock is None:
            # Unknown route → 404 with a descriptive body for easy debugging
            body = _json_mod.dumps({
                "error": "mock_not_registered",
                "method": request.method,
                "url": str(request.url),
                "registered_routes": [f"{m} {u}" for m, u in self._responses],
            }).encode()
            return httpx.Response(
                404,
                content=body,
                headers={"content-type": "application/json"},
            )

        content: bytes
        response_headers = dict(mock.headers)
        if mock.json is not None:
            content = _json_mod.dumps(mock.json).encode()
            response_headers.setdefault("content-type", "application/json")
        else:
            content = mock.text.encode()
            response_headers.setdefault("content-type", "text/plain")

        return httpx.Response(
            mock.status_code,
            content=content,
            headers=response_headers,
        )


# ---------------------------------------------------------------------------
# Pytest fixture
# ---------------------------------------------------------------------------

class _MockClient(httpx.AsyncClient):
    """An ``httpx.AsyncClient`` extended with a ``register`` helper."""

    def __init__(self) -> None:
        self._mock_responses: dict[tuple[str, str], MockResponse] = {}
        transport = _MockTransport(self._mock_responses)
        super().__init__(transport=transport)

    def register(
        self,
        method: str,
        url: str,
        response: MockResponse,
    ) -> None:
        """Register a canned *response* for ``method url``.

        Args:
            method: HTTP method in any case (normalised to upper).
            url: Exact URL string to match (scheme + host + path + query).
            response: :class:`MockResponse` to return.
        """
        self._mock_responses[(method.upper(), url)] = response

    def reset(self) -> None:
        """Clear all registered responses (useful within a single test)."""
        self._mock_responses.clear()


@pytest.fixture
def mock_http_client() -> _MockClient:
    """Pytest fixture: an ``httpx.AsyncClient`` backed by a mock transport.

    The returned client has an extra ``register(method, url, MockResponse)``
    method.  Unregistered routes return HTTP 404 with a JSON body listing
    all registered routes, so test failures are self-explanatory.

    Example::

        async def test_example(mock_http_client):
            mock_http_client.register(
                "GET",
                "https://api.example.com/items",
                MockResponse(200, json=[{"id": 1}]),
            )
            resp = await mock_http_client.get("https://api.example.com/items")
            assert resp.status_code == 200
            assert resp.json() == [{"id": 1}]
    """
    return _MockClient()
