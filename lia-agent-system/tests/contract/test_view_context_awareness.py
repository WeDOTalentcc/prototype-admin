"""Sensor canonical P0.1 (2026-06-03) — consciencia de estado da tela.

O chat global da LIA deve ABRIR ciente do conjunto de trabalho atual do
recrutador (igual Apollo: "voce tem 88.778 contatos na busca atual"). Hoje o
SSE manda so {content, conversation_id} e o agente fica cego ao que esta na tela.

Este sensor pina o helper PURO que formata view_context num bloco de prompt, e
que o agente global injeta esse bloco quando view_context esta presente.
"""
import pytest


def test_empty_view_context_returns_empty():
    from app.orchestrator.context.view_context import format_view_context
    assert format_view_context(None) == ""
    assert format_view_context({}) == ""


def test_counts_are_surfaced():
    from app.orchestrator.context.view_context import format_view_context
    out = format_view_context({
        "page_type": "vagas",
        "counts": {"total": 50, "ativas": 4, "urgentes": 11},
    })
    assert "50" in out
    assert "11" in out
    # rotulo legivel da tela, nao o slug cru
    assert "Vagas" in out
    # deve sinalizar que e o estado atual da tela pro LLM usar
    assert "tela" in out.lower()


def test_active_filters_surfaced():
    from app.orchestrator.context.view_context import format_view_context
    out = format_view_context({
        "page_type": "funil",
        "counts": {"total": 120},
        "active_filters": ["status=entrevista", "departamento=engenharia"],
    })
    assert "status=entrevista" in out
    assert "departamento=engenharia" in out


def test_unknown_page_type_does_not_crash():
    from app.orchestrator.context.view_context import format_view_context
    out = format_view_context({"page_type": "alguma_tela_nova", "counts": {"total": 3}})
    assert "3" in out  # nao quebra; usa o slug como fallback


def test_partial_payload_robust():
    from app.orchestrator.context.view_context import format_view_context
    # so page_type, sem counts
    out = format_view_context({"page_type": "kanban"})
    assert "Kanban" in out
    # so counts, sem page_type
    out2 = format_view_context({"counts": {"total": 7}})
    assert "7" in out2
