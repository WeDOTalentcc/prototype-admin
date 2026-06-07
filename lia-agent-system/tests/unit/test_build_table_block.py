"""build_table_block (2026-06-07): card RRP generico p/ list tools.

Unifica tabelas (card comparison_table) em vez de markdown da LLM. FE ja
renderiza comparison_table com colunas/cells arbitrarias + entity_type job.
"""
from __future__ import annotations

from app.shared.rrp_ranking_builder import build_table_block, RRP_TABLE_HINT


def test_jobs_table():
    blocks = build_table_block(
        title="Vagas",
        entity_type="job",
        source_tool="list_jobs",
        total_count=6,
        columns=[("title", "Vaga", "text"), ("candidate_count", "Candidatos", "number")],
        rows=[{"entity_id": "j1", "cells": {"title": "Android", "candidate_count": 18}}],
    )
    assert len(blocks) == 1
    b = blocks[0]
    assert b["kind"] == "comparison_table"
    assert b["entity_type"] == "job"
    assert b["title"] == "Vagas"
    assert b["total_count"] == 6
    assert [c["key"] for c in b["columns"]] == ["title", "candidate_count"]
    assert b["rows"][0]["cells"]["title"] == "Android"


def test_empty_rows():
    assert build_table_block(
        title="x", entity_type="candidate", columns=[], rows=[], source_tool="t"
    ) == []


def test_score_column_type_preserved():
    blocks = build_table_block(
        title="C",
        entity_type="candidate",
        source_tool="list_candidates",
        total_count=1,
        columns=[("name", "Nome", "text"), ("lia_score", "Score LIA", "score")],
        rows=[{"entity_id": "c1", "cells": {"name": "Yasmin", "lia_score": 95.8}}],
    )
    cols = {c["key"]: c["type"] for c in blocks[0]["columns"]}
    assert cols["lia_score"] == "score"
    assert cols["name"] == "text"


def test_hint_is_string():
    assert isinstance(RRP_TABLE_HINT, str) and "markdown" in RRP_TABLE_HINT
