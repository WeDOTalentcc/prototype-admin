"""Regression test for Task #319 / audit findings W17 + W2.

Pins the public path of the agent chat WebSocket to the canonical
``/api/v1/ws/chat/{session_id}`` surface. A future refactor that drops
the ``prefix="/api/v1"`` from ``app.include_router(agent_chat_ws_router, ...)``
would silently re-expose the WS at ``/ws/chat/...`` — bypassing the auth
middleware/proxy/CORS/rate-limit rules that key off ``/api/v1``.
"""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.routing import APIRoute, APIWebSocketRoute

from app.api.v1.agent_chat_ws import router as agent_chat_ws_router


def _ws_paths(app: FastAPI) -> list[str]:
    return [r.path for r in app.routes if isinstance(r, APIWebSocketRoute)]


def _http_paths(app: FastAPI) -> list[str]:
    return [r.path for r in app.routes if isinstance(r, APIRoute)]


def test_router_declares_relative_chat_path() -> None:
    """The router itself should still declare the relative ``/ws/chat`` path —
    the ``/api/v1`` prefix is applied at ``include_router`` time."""
    paths = [r.path for r in agent_chat_ws_router.routes if isinstance(r, APIWebSocketRoute)]
    assert "/ws/chat/{session_id}" in paths


def test_chat_ws_is_mounted_under_api_v1() -> None:
    app = FastAPI()
    app.include_router(agent_chat_ws_router, prefix="/api/v1")

    paths = _ws_paths(app)
    assert "/api/v1/ws/chat/{session_id}" in paths, paths
    assert "/ws/chat/{session_id}" not in paths, (
        "Chat WS must NOT be exposed at the unprefixed root path; this is "
        "the audit finding W17/W2 that Task #319 fixed."
    )


def test_sibling_http_routes_also_move_under_api_v1() -> None:
    """The same router also defines ``GET /sessions/active`` and
    ``POST /chat/message`` — they must move with the WS so HTTP clients
    (e.g. plataforma-lia/src/app/api/backend-proxy/agent-chat/sessions/active)
    can hit the prefixed paths consistently."""
    app = FastAPI()
    app.include_router(agent_chat_ws_router, prefix="/api/v1")

    paths = _http_paths(app)
    assert "/api/v1/sessions/active" in paths, paths
    assert "/api/v1/chat/message" in paths, paths
    assert "/sessions/active" not in paths
    assert "/chat/message" not in paths


def test_chat_ws_unprefixed_mount_would_be_a_regression() -> None:
    """Negative control: confirms the tests above genuinely exercise the
    prefix logic (without a prefix, the routes show up at the bare path)."""
    app = FastAPI()
    app.include_router(agent_chat_ws_router)  # no prefix == regression

    paths = _ws_paths(app)
    assert "/ws/chat/{session_id}" in paths
    assert "/api/v1/ws/chat/{session_id}" not in paths
