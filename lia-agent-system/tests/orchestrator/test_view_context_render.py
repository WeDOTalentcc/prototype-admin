"""Fase B P0.1 (consciencia de tela): render_view_context + UniversalContext.view_context.

O supervisor (Phase 1.5) abre CIENTE do que o recrutador ve agora (page_type +
contagens + filtros). render_view_context e funcao PURA (deterministica) que vira o
snippet injetado no system prompt. UniversalContext carrega o view_context do SSE.
"""
from app.orchestrator.context.context_adapter import render_view_context, UniversalContext


def test_render_empty_or_none_returns_blank():
    assert render_view_context(None) == ""
    assert render_view_context({}) == ""
    assert render_view_context("nao-dict") == ""


def test_render_includes_page_type_counts_filters():
    vc = {
        "page_type": "vaga_pipeline",
        "counts": {"total": 40, "triagem": 12},
        "filters": {"seniority": "senior", "empty": ""},
        "job_title": "Dev Python Senior",
        "visible_ids": ["a", "b", "c"],
    }
    s = render_view_context(vc)
    assert "vaga_pipeline" in s
    assert "40" in s and "12" in s
    assert "senior" in s
    assert "empty" not in s  # filtro vazio nao entra
    assert "Dev Python Senior" in s
    assert "3" in s  # contagem de ids visiveis


def test_universal_context_carries_view_context():
    vc = {"page_type": "vagas", "counts": {"total": 5}}
    ctx = UniversalContext(message="oi", company_id="c1", view_context=vc)
    assert ctx.view_context == vc
    # default None quando nao informado
    ctx2 = UniversalContext(message="oi", company_id="c1")
    assert ctx2.view_context is None
