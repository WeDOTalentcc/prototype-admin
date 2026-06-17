"""Sensor — sink de response_blocks do caminho B (federado/bolha)."""
import asyncio

from app.shared.rrp_block_sink import (
    append_from_result,
    drain_sink,
    reset_sink,
    tee_tool_function,
)


def test_acumula_e_drena_uma_vez():
    reset_sink()
    append_from_result({"success": True, "data": {"response_blocks": [{"kind": "funnel"}]}})
    append_from_result({"success": True, "data": {"response_blocks": [{"kind": "prose"}]}})
    out = drain_sink()
    assert len(out) == 2
    assert out[0]["kind"] == "funnel"
    # consumo único: drenar de novo vem vazio
    assert drain_sink() == []


def test_ignora_results_sem_blocks():
    reset_sink()
    append_from_result({"data": {"x": 1}})
    append_from_result("nao e dict")
    append_from_result({"success": True})
    append_from_result(None)
    assert drain_sink() == []


def test_reset_limpa():
    reset_sink()
    append_from_result({"data": {"response_blocks": [{"kind": "funnel"}]}})
    reset_sink()
    assert drain_sink() == []


def test_tee_defensivo_nunca_levanta():
    # objeto bizarro nao pode quebrar
    class Weird:
        def get(self, *a, **k):
            raise RuntimeError("boom")

    reset_sink()
    append_from_result(Weird())  # não deve levantar
    assert drain_sink() == []


def test_tee_async_captura_e_passthrough():
    reset_sink()

    async def fake(**k):
        return {"success": True, "data": {"response_blocks": [{"kind": "funnel"}]}}

    wrapped = tee_tool_function(fake)
    out = asyncio.run(wrapped(x=1))
    assert out["data"]["response_blocks"][0]["kind"] == "funnel"  # passthrough intacto
    assert len(drain_sink()) == 1  # teed no sink


def test_tee_tool_sem_blocks_nao_polui():
    reset_sink()

    async def fake(**k):
        return {"success": True, "data": {"x": 1}}

    out = asyncio.run(tee_tool_function(fake)(y=2))
    assert out["success"] is True
    assert drain_sink() == []
