"""HITL gate (AUD-4, 2026-06-06) — chokepoint compartilhado @tool_handler.

Tool marcada requires_confirmation=True NAO executa o side-effect sem aprovacao
server-side (ContextVar setada pelo transporte qdo o usuario confirma). Cobre
federado E supervisor (ambos rodam o wrapper). Testado em isolamento: o gate
bloqueia sem aprovacao e libera com aprovacao.
"""
from __future__ import annotations

import asyncio

from app.shared.tool_handler import tool_handler
from app.shared.hitl.hitl_approval_context import (
    set_hitl_approved,
    reset_hitl_approved,
)


@tool_handler("test", require_company=False, requires_confirmation=True)
async def _fake_sensitive(**kwargs):
    return {"did_run": True}


@tool_handler("test", require_company=False)
async def _fake_normal(**kwargs):
    return {"did_run": True}


def test_gate_blocks_sensitive_without_approval():
    r = asyncio.run(_fake_sensitive())
    assert r.get("needs_confirmation") is True
    assert r.get("success") is False
    # mutacao NAO rodou
    assert "data" not in r or (r.get("data") or {}).get("did_run") is not True


def test_gate_passes_sensitive_with_approval():
    tok = set_hitl_approved(True)
    try:
        r = asyncio.run(_fake_sensitive())
    finally:
        reset_hitl_approved(tok)
    assert r.get("success") is True
    assert (r.get("data") or {}).get("did_run") is True
    assert not r.get("needs_confirmation")


def test_normal_tool_unaffected():
    r = asyncio.run(_fake_normal())
    assert r.get("success") is True
    assert not r.get("needs_confirmation")
