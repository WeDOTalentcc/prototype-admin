"""Fase B P0.1 (consciencia de tela): format_view_context + UniversalContext.view_context.

O supervisor (Phase 1.5) abre CIENTE do que o recrutador ve agora (page_type +
contagens + filtros). format_view_context e funcao PURA (deterministica) que vira o
snippet injetado no system prompt. UniversalContext carrega o view_context do SSE.

DRY (2026-06-22): render_view_context deletado de context_adapter.py — fonte
unica agora e format_view_context em view_context.py.
"""
from app.orchestrator.context.view_context import format_view_context
from app.orchestrator.context.context_adapter import UniversalContext


def test_render_empty_or_none_returns_blank():
    assert format_view_context(None) == ""
    assert format_view_context({}) == ""
    assert format_view_context("nao-dict") == ""


def test_render_includes_page_type_counts_filters_and_job():
    vc = {
        "page_type": "vaga_pipeline",
        "counts": {"total": 40, "triagem": 12},
        "active_filters": ["seniority: senior"],
        "job_title": "Dev Python Senior",
        "visible_ids": ["a", "b", "c"],
    }
    s = format_view_context(vc)
    assert "vaga_pipeline" in s
    assert "40" in s and "12" in s
    assert "senior" in s
    assert "Dev Python Senior" in s
    assert "3" in s


def test_render_includes_entity_focus_pagination_modal():
    vc = {
        "page_type": "kanban",
        "entity_focus": {"type": "candidate", "id": "c1", "label": "Maria"},
        "pagination_state": {"current_page": 2, "total_pages": 5, "page_size": 20, "total_items": 96},
        "active_modal": "candidate_compare",
    }
    s = format_view_context(vc)
    assert "Maria" in s
    assert "c1" in s
    assert "candidate_compare" in s


def test_universal_context_carries_view_context():
    vc = {"page_type": "vagas", "counts": {"total": 5}}
    ctx = UniversalContext(message="oi", company_id="c1", view_context=vc)
    assert ctx.view_context == vc
    ctx2 = UniversalContext(message="oi", company_id="c1")
    assert ctx2.view_context is None
