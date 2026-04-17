"""Integration regression test for Task #319.

Pins the public path of the agent chat WebSocket on the real route
registry to ``/api/v1/ws/chat/{session_id}``. A future refactor that
drops the ``prefix="/api/v1"`` from the
``app.include_router(agent_chat_ws_router, ...)`` call inside
``app/api/routes.register_all_routes`` would silently re-expose the WS
at the bare ``/ws/chat/...`` path — bypassing the auth middleware /
proxy / CORS rules that key off ``/api/v1`` and breaking the frontend
client.

Unlike the focused unit test (``tests/unit/test_agent_chat_ws_prefix.py``),
this test exercises the production ``register_all_routes`` registry, so
a regression at the *registration site* — not just in the router file —
is also caught.
"""
from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.routing import APIWebSocketRoute


@pytest.fixture(scope="module")
def registered_app() -> FastAPI:
    from app.api.routes import register_all_routes

    app = FastAPI()
    register_all_routes(app)
    return app


def _ws_paths(app: FastAPI) -> list[str]:
    return [r.path for r in app.routes if isinstance(r, APIWebSocketRoute)]


def test_chat_ws_is_mounted_under_api_v1(registered_app: FastAPI) -> None:
    paths = _ws_paths(registered_app)
    assert "/api/v1/ws/chat/{session_id}" in paths, (
        "Chat WS must be exposed at /api/v1/ws/chat/{session_id}; "
        f"current WS routes: {paths}"
    )


def test_chat_ws_is_not_exposed_at_bare_root(registered_app: FastAPI) -> None:
    paths = _ws_paths(registered_app)
    assert "/ws/chat/{session_id}" not in paths, (
        "Chat WS must NOT be exposed at the unprefixed /ws/chat/{session_id} "
        "path; this is the audit finding W17/W2 that Task #319 fixed. "
        f"current WS routes: {paths}"
    )
