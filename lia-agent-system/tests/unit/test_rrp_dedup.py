"""RRP dedup / 2-table (2026-06-07): card RRP = fonte visual unica.

O tee do rrp_block_sink remove response_blocks da view-LLM (apos teear pro sink)
-> a LLM nao re-tabula. As tools RRP expoem narrativa compacta em vez da lista.
"""
from __future__ import annotations

import asyncio

from app.shared.rrp_block_sink import (
    reset_sink,
    drain_sink,
    tee_tool_function,
    _strip_blocks_for_llm,
)


def test_strip_removes_blocks_not_original():
    orig = {"success": True, "data": {"response_blocks": [{"kind": "x"}], "narrative": "n"}}
    out = _strip_blocks_for_llm(orig)
    assert out["data"]["response_blocks"] is None
    assert out["data"]["narrative"] == "n"
    assert orig["data"]["response_blocks"] == [{"kind": "x"}]  # original intacto


def test_strip_noop_when_no_blocks():
    orig = {"success": True, "data": {"x": 1}}
    out = _strip_blocks_for_llm(orig)
    assert out["data"]["x"] == 1


def test_tee_captures_then_strips_for_llm():
    async def _scenario():
        reset_sink()

        async def _tool(**kw):
            return {
                "success": True,
                "data": {
                    "response_blocks": [{"kind": "score_explainer"}],
                    "narrative": "n",
                },
            }

        wrapped = tee_tool_function(_tool)
        r = await wrapped()
        return r, drain_sink()

    r, blocks = asyncio.run(_scenario())
    assert r["data"]["response_blocks"] is None  # LLM nao ve os blocks
    assert blocks == [{"kind": "score_explainer"}]  # sink capturou (card)


def test_rank_narrative_is_prose_not_table():
    from app.domains.recruiter_assistant.agents.talent_tool_registry import (
        _rrp_rank_narrative,
    )
    s = _rrp_rank_narrative([
        {"name": "Nicolas", "lia_score": 99, "stage": "sourcing"},
        {"name": "Igor", "lia_score": 99, "stage": "sourcing"},
        {"name": "Sofia", "lia_score": 98, "stage": "sourcing"},
        {"name": "X", "lia_score": 50, "stage": "sourcing"},
    ])
    assert "Nicolas" in s and "99" in s
    assert "Total 4" in s
    assert "|" not in s  # nao e tabela markdown


def test_compare_narrative_is_prose():
    from app.domains.recruiter_assistant.agents.talent_tool_registry import (
        _rrp_compare_narrative,
    )
    s = _rrp_compare_narrative(
        [{"name": "A"}, {"name": "B"}], ["id1", "id2"]
    )
    assert "2 candidatos" in s
    assert "|" not in s
