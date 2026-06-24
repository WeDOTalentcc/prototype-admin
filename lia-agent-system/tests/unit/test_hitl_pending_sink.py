"""hitl_pending_sink (AUD-4 1b surfacing, 2026-06-07).

Captura needs_confirmation de um tool result na execucao (antes da
stringificacao do ToolMessage) -> drena no fim do turno -> metadata. Espelha
rrp_block_sink. Primeiro do turno vence; non-confirmation ignorado; tee
passthrough preserva o retorno.
"""
from __future__ import annotations

import asyncio

from app.shared.hitl_pending_sink import (
    reset_sink,
    append_from_result,
    drain_sink,
    tee_tool_function,
)


def test_captures_needs_confirmation():
    reset_sink()
    append_from_result({
        "success": False,
        "needs_confirmation": True,
        "message": "Confirme para prosseguir.",
        "hitl": {"tool": "close_job", "domain": "job_management"},
        "data": {"job_id": "j1"},
    })
    p = drain_sink()
    assert p is not None
    assert p["tool"] == "close_job"
    assert p["domain"] == "job_management"
    assert p["message"].startswith("Confirme")
    assert p["data"] == {"job_id": "j1"}
    # consumo unico: segundo drain volta None
    assert drain_sink() is None


def test_ignores_normal_result():
    reset_sink()
    append_from_result({"success": True, "data": {"x": 1}})
    assert drain_sink() is None


def test_first_wins():
    reset_sink()
    append_from_result({"needs_confirmation": True, "hitl": {"tool": "a"}})
    append_from_result({"needs_confirmation": True, "hitl": {"tool": "b"}})
    p = drain_sink()
    assert p["tool"] == "a"


def test_reset_clears():
    append_from_result({"needs_confirmation": True, "hitl": {"tool": "a"}})
    reset_sink()
    assert drain_sink() is None


def test_tee_passthrough_async():
    # append (dentro da tool) + drain devem rodar no MESMO contexto async, como
    # em producao (tudo na task do agente). asyncio.run(wrapped()) isolado criaria
    # contexto novo e o set() nao vazaria — artefato de teste, nao bug.
    async def _scenario():
        reset_sink()

        async def _tool(**kwargs):
            return {
                "needs_confirmation": True,
                "hitl": {"tool": "send_email"},
                "message": "m",
            }

        wrapped = tee_tool_function(_tool)
        r = await wrapped(x=1)
        return r, drain_sink()

    r, p = asyncio.run(_scenario())
    assert r["needs_confirmation"] is True  # retorno preservado
    assert p is not None and p["tool"] == "send_email"  # capturado no sink


def test_tee_never_raises_on_bad_result():
    async def _scenario():
        reset_sink()

        async def _tool(**kwargs):
            return "string-nao-dict"

        wrapped = tee_tool_function(_tool)
        r = await wrapped()
        return r, drain_sink()

    r, p = asyncio.run(_scenario())
    assert r == "string-nao-dict"
    assert p is None
