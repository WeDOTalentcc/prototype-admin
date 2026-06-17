"""Sensor: ui_action_sink — side-channel da diretiva ui_action (caminho B).

Espelha o contrato de rrp_block_sink: reset/append_from_result/drain + tee
defensivo. Garante que apply_table_state (e os demais acionaveis) sobrevivem o
caminho federado (LangGraph ReAct) ate o AgentOutput.metadata.
"""
from __future__ import annotations

import pytest

from app.shared.ui_action_sink import (
    append_from_result,
    drain_sink,
    reset_sink,
    tee_tool_function,
)


@pytest.fixture(autouse=True)
def _clean():
    reset_sink()
    yield
    reset_sink()


def test_drain_empty_is_none():
    assert drain_sink() is None


def test_append_actionable_directive():
    append_from_result(
        {
            "success": True,
            "data": {
                "ui_action": "apply_table_state",
                "ui_action_params": {"surface": "candidates", "patch": {"search": "x"}},
            },
        }
    )
    d = drain_sink()
    assert d == {
        "ui_action": "apply_table_state",
        "ui_action_params": {"surface": "candidates", "patch": {"search": "x"}},
    }


def test_open_modal_also_captured():
    # caminho federado tambem destrava open_ui (open_modal/navigate_to).
    append_from_result(
        {"data": {"ui_action": "open_modal", "ui_action_params": {"modal_id": "x"}}}
    )
    assert drain_sink()["ui_action"] == "open_modal"


def test_non_actionable_ignored():
    append_from_result({"data": {"ui_action": "not_a_real_action", "ui_action_params": {}}})
    assert drain_sink() is None


def test_result_without_directive_ignored():
    append_from_result({"success": True, "message": "ok"})
    assert drain_sink() is None
    append_from_result("not a dict")
    assert drain_sink() is None


def test_last_wins():
    append_from_result({"data": {"ui_action": "navigate_to", "ui_action_params": {"page": "/a"}}})
    append_from_result(
        {"data": {"ui_action": "apply_table_state", "ui_action_params": {"surface": "candidates", "patch": {}}}}
    )
    assert drain_sink()["ui_action"] == "apply_table_state"


def test_drain_consumes():
    append_from_result({"data": {"ui_action": "open_modal", "ui_action_params": {}}})
    assert drain_sink() is not None
    assert drain_sink() is None


@pytest.mark.asyncio
async def test_tee_async_passthrough_and_captures():
    async def _tool(**kwargs):
        return {"data": {"ui_action": "apply_table_state", "ui_action_params": {"surface": "candidates", "patch": {}}}}

    wrapped = tee_tool_function(_tool)
    out = await wrapped(surface="candidates")
    # passthrough: retorno intacto
    assert out["data"]["ui_action"] == "apply_table_state"
    # tee: diretiva no sink
    assert drain_sink()["ui_action"] == "apply_table_state"


def test_tee_sync_passthrough():
    def _tool(**kwargs):
        return {"data": {"ui_action": "open_modal", "ui_action_params": {"modal_id": "m"}}}

    wrapped = tee_tool_function(_tool)
    out = wrapped()
    assert out["data"]["ui_action"] == "open_modal"
    assert drain_sink()["ui_action"] == "open_modal"


def test_tee_never_raises_on_bad_tool_result():
    def _tool():
        return None  # sem diretiva — tee nao pode levantar

    assert tee_tool_function(_tool)() is None
    assert drain_sink() is None


def test_actionable_uses_canonical_allowlist():
    # fonte unica: o allowlist do agentic_loop deve conter apply_table_state.
    from app.shared.ui_action_sink import _actionable

    assert "apply_table_state" in _actionable()
