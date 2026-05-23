"""WT-2022: Contract test pra WebSocket endpoint /ws/proactive-hints.

Sensores canonical:
1. Sem token → close 4001 (Missing token).
2. Token inválido → close 4003 (Invalid token).
3. Broadcast via pool atinge cliente conectado da mesma company.
4. Broadcast NÃO atinge cliente de company diferente (multi-tenancy).
5. Pool disconnect remove cliente sem leak.
"""
from __future__ import annotations

import asyncio
from unittest.mock import MagicMock, AsyncMock

import pytest


@pytest.mark.asyncio
async def test_pool_broadcast_to_company_isolation():
    """Hint só atinge clients da mesma company_id (multi-tenancy invariant)."""
    from app.api.websockets.proactive_hints_ws import (
        ProactiveHintsConnectionPool,
    )

    pool = ProactiveHintsConnectionPool()

    ws_a = MagicMock()
    ws_a.accept = AsyncMock()
    ws_a.send_json = AsyncMock()

    ws_b = MagicMock()
    ws_b.accept = AsyncMock()
    ws_b.send_json = AsyncMock()

    await pool.connect(ws_a, "company-aaa")
    await pool.connect(ws_b, "company-bbb")

    delivered = await pool.broadcast_to_company(
        "company-aaa", {"id": "h1", "title": "x"}
    )

    assert delivered == 1
    ws_a.send_json.assert_awaited_once_with(
        {"type": "hint", "data": {"id": "h1", "title": "x"}}
    )
    ws_b.send_json.assert_not_awaited()


@pytest.mark.asyncio
async def test_pool_broadcast_removes_dead_connection():
    """Conexão que raise no send é removida do pool silenciosamente."""
    from app.api.websockets.proactive_hints_ws import (
        ProactiveHintsConnectionPool,
    )

    pool = ProactiveHintsConnectionPool()

    ws_alive = MagicMock()
    ws_alive.accept = AsyncMock()
    ws_alive.send_json = AsyncMock()

    ws_dead = MagicMock()
    ws_dead.accept = AsyncMock()
    ws_dead.send_json = AsyncMock(side_effect=RuntimeError("conn closed"))

    await pool.connect(ws_alive, "company-x")
    await pool.connect(ws_dead, "company-x")

    assert pool.connection_count("company-x") == 2

    delivered = await pool.broadcast_to_company(
        "company-x", {"id": "h2"}
    )

    # Só o vivo recebeu; o morto foi descartado.
    assert delivered == 1
    assert pool.connection_count("company-x") == 1


@pytest.mark.asyncio
async def test_pool_disconnect_cleanup():
    """Disconnect explícito remove ws e limpa bucket vazio (sem leak)."""
    from app.api.websockets.proactive_hints_ws import (
        ProactiveHintsConnectionPool,
    )

    pool = ProactiveHintsConnectionPool()
    ws = MagicMock()
    ws.accept = AsyncMock()

    await pool.connect(ws, "company-y")
    assert pool.connection_count("company-y") == 1

    pool.disconnect(ws, "company-y")
    assert pool.connection_count("company-y") == 0
    # Bucket vazio removido — não vaza memória per-tenant
    assert "company-y" not in pool._pool


@pytest.mark.asyncio
async def test_extract_company_id_rejects_missing_claim(monkeypatch):
    """Token decoded sem company_id claim → retorna None (close 4003)."""
    from app.api.websockets import proactive_hints_ws as mod

    def fake_decode(token: str) -> dict:
        return {"sub": "user-123"}  # sem company_id

    monkeypatch.setattr(
        "app.auth.security.decode_token", fake_decode
    )
    result = mod._extract_company_id_from_token("any-token")
    assert result is None


@pytest.mark.asyncio
async def test_extract_company_id_rejects_invalid_token(monkeypatch):
    """decode_token raise → retorna None (fail-closed)."""
    from app.api.websockets import proactive_hints_ws as mod

    def fake_decode(token: str) -> dict:
        raise ValueError("invalid signature")

    monkeypatch.setattr(
        "app.auth.security.decode_token", fake_decode
    )
    result = mod._extract_company_id_from_token("bad-token")
    assert result is None


@pytest.mark.asyncio
async def test_extract_company_id_accepts_alternate_claims(monkeypatch):
    """Aceita company_id / companyId / tenant_id como claims canonical."""
    from app.api.websockets import proactive_hints_ws as mod

    for claim in ("company_id", "companyId", "tenant_id"):
        def fake_decode(token: str, _c=claim) -> dict:
            return {_c: "company-zzz"}

        monkeypatch.setattr(
            "app.auth.security.decode_token", fake_decode
        )
        assert mod._extract_company_id_from_token("t") == "company-zzz"
