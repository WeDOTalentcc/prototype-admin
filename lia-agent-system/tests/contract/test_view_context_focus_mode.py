"""TDD: view_context deve diferenciar vaga em foco ativa vs background.

Fix P1: chat full-screen com job em foco background nao deve receber
briefing automatico de vaga — o contexto deve ser diferente.
"""
import pytest
from app.orchestrator.context.view_context import format_view_context


def test_active_focus_shows_job_in_focus_label():
    """Modo active: deve mostrar Vaga em foco no prompt."""
    vc = {
        "entity_focus": {
            "type": "job",
            "id": "abc-123",
            "label": "Dev Sr",
            "mode": "active"
        }
    }
    result = format_view_context(vc)
    assert "Vaga em foco" in result,         "Modo active deve mostrar Vaga em foco"
    assert "abc-123" in result,         "ID deve estar presente no resultado"


def test_background_focus_shows_context_label_not_active():
    """Modo background: NAO deve mostrar Vaga em foco, deve indicar contexto."""
    vc = {
        "entity_focus": {
            "type": "job",
            "id": "abc-123",
            "label": "Dev Sr",
            "mode": "background"
        }
    }
    result = format_view_context(vc)
    assert "Vaga em foco" not in result,         "Modo background NAO deve dizer Vaga em foco como se fosse ativo"
    assert "abc-123" in result,         "ID deve estar presente mesmo no modo background"
    assert (
        "nao esta navegando" in result.lower()
        or "não está navegando" in result.lower()
        or "contexto" in result.lower()
        or "background" in result.lower()
    ), "Modo background deve indicar que usuario nao esta na pagina da vaga"


def test_no_mode_defaults_to_active_behavior():
    """Backward compat: sem campo mode = comportamento original (active)."""
    vc = {
        "entity_focus": {
            "type": "job",
            "id": "abc-123",
            "label": "Dev Sr"
            # sem campo "mode"
        }
    }
    result = format_view_context(vc)
    assert "Vaga em foco" in result,         "Sem mode field, deve usar comportamento legacy (active)"


def test_candidate_focus_unaffected_by_mode():
    """Candidato em foco nao e afetado pelo campo mode (so aplica a vagas)."""
    vc = {
        "entity_focus": {
            "type": "candidate",
            "id": "cand-456",
            "label": "Joao Silva"
        }
    }
    result = format_view_context(vc)
    assert "Candidato em foco" in result,         "Candidato em foco deve manter label original"
