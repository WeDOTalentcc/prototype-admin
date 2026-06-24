"""Sensor RRP — bloco funnel (Fase 1).

GUIDE: pipeline vira funnel via produtor unico build_pipeline_funnel_block;
get_pipeline_summary emite data.response_blocks (AD3 loop captura).
Este sensor guarda: contrato valido, union discriminada, extra=forbid,
empty stages -> [] (sem bloco vazio).
"""
import pytest
from pydantic import TypeAdapter, ValidationError

from app.shared.rrp_blocks import FunnelBlock, ResponseBlock
from app.shared.rrp_ranking_builder import build_pipeline_funnel_block


def test_builder_produces_valid_funnel_block():
    blks = build_pipeline_funnel_block(
        "Pipeline (Diretor Juridico)",
        {"Triagem": 12, "Entrevista": 5, "Oferta": 2},
        total=19,
        conversion_rate=5.3,
    )
    assert len(blks) == 1
    b = TypeAdapter(ResponseBlock).validate_python(blks[0])
    assert b.kind == "funnel"
    assert b.layout == "wide"
    assert b.role == "support"
    assert len(b.stages) == 3
    assert b.stages[0].label == "Triagem"
    assert b.stages[0].count == 12
    assert b.total == 19
    assert b.conversion_rate == 5.3


def test_empty_stages_returns_no_block():
    # Sem etapas -> nenhum bloco (nao emitir funnel vazio).
    assert build_pipeline_funnel_block("X", {}) == []


def test_funnel_block_extra_forbid():
    # Multi-tenancy/contrato: campo desconhecido rejeitado (extra=forbid).
    with pytest.raises(ValidationError):
        FunnelBlock(
            block_id="funnel:x",
            title="t",
            stages=[],
            total=0,
            conversion_rate=0.0,
            company_id="leak",  # nao pode existir
        )


def test_funnel_counts_coerced_to_int():
    blks = build_pipeline_funnel_block("X", {"A": "7"}, total="7", conversion_rate=0)
    b = blks[0]
    assert b["stages"][0]["count"] == 7
    assert isinstance(b["stages"][0]["count"], int)
    assert b["total"] == 7
