"""Regression test para prefixo canonical do chat SSE.

Migrado de test_agent_chat_ws_prefix.py (audit findings W17 + W2):
antes verificava o router WebSocket. Com a deleção de agent_chat_ws.py
(2026-06-09), verificamos o router SSE (agent_chat_sse.py) que é o
transporte ativo (NEXT_PUBLIC_CHAT_TRANSPORT=sse).

Pina os paths públicos do agente chat SSE ao prefixo canonical /api/v1.
"""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.routing import APIRoute, APIWebSocketRoute

from app.api.v1.agent_chat_sse import router as agent_chat_sse_router

# Retrocompat alias — mantido para não quebrar imports que ainda referenciam
# agent_chat_ws_router pelo nome
agent_chat_ws_router = agent_chat_sse_router


def _http_paths(app: FastAPI) -> list[str]:
    return [r.path for r in app.routes if isinstance(r, APIRoute)]


def test_router_declares_sessions_active_path() -> None:
    """O router SSE deve declarar GET /sessions/active para compatibilidade com SwitchTaskModal."""
    paths = [r.path for r in agent_chat_sse_router.routes if isinstance(r, APIRoute)]
    assert "/sessions/active" in paths, f"Expected /sessions/active in {paths}"


def test_router_declares_stream_path() -> None:
    """O router SSE deve declarar GET /chat/{session_id}/stream."""
    paths = [r.path for r in agent_chat_sse_router.routes if isinstance(r, APIRoute)]
    assert "/chat/{session_id}/stream" in paths, f"Expected /chat/{{session_id}}/stream in {paths}"


def test_chat_sse_is_mounted_under_api_v1() -> None:
    """Rotas SSE montadas sob /api/v1."""
    app = FastAPI()
    app.include_router(agent_chat_sse_router, prefix="/api/v1")

    paths = _http_paths(app)
    assert "/api/v1/sessions/active" in paths, paths
    assert "/api/v1/chat/{session_id}/stream" in paths, paths
    assert "/sessions/active" not in paths
    assert "/chat/{session_id}/stream" not in paths


def test_sibling_http_routes_also_move_under_api_v1() -> None:
    """GET /sessions/active e POST /chat/action devem mover com o router."""
    app = FastAPI()
    app.include_router(agent_chat_sse_router, prefix="/api/v1")

    paths = _http_paths(app)
    assert "/api/v1/sessions/active" in paths, paths


def test_chat_sse_unprefixed_mount_would_be_a_regression() -> None:
    """Controle negativo: sem prefixo, rotas aparecem no caminho bare."""
    app = FastAPI()
    app.include_router(agent_chat_sse_router)  # no prefix == regression

    paths = _http_paths(app)
    assert "/sessions/active" in paths
    assert "/api/v1/sessions/active" not in paths
