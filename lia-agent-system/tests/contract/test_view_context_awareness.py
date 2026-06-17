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


# --- P0.1 MVP: sintetizar view_context a partir do context que o FE JA envia ---
# O FE (getPageContext em useChatMessages.ts) ja manda page_type + job_vacancy_id
# + candidate_id em todo request. O agente deve derivar o view_context disso
# mesmo sem o FE enviar um bloco "view_context" explicito.

def test_from_context_prefers_explicit_view_context():
    from app.orchestrator.context.view_context import view_context_from_context
    explicit = {"page_type": "vagas", "counts": {"total": 50}}
    assert view_context_from_context({"view_context": explicit}) == explicit


def test_from_context_synthesizes_from_page_type():
    from app.orchestrator.context.view_context import view_context_from_context
    out = view_context_from_context({"page_type": "vagas"})
    assert out == {"page_type": "vagas"}


def test_from_context_includes_visible_entity_ids():
    from app.orchestrator.context.view_context import view_context_from_context
    out = view_context_from_context({"page_type": "funil", "job_vacancy_id": "abc-123"})
    assert out["page_type"] == "funil"
    assert "abc-123" in out.get("visible_ids", [])


def test_from_context_empty_returns_none():
    from app.orchestrator.context.view_context import view_context_from_context
    assert view_context_from_context({}) is None
    assert view_context_from_context(None) is None


def test_from_context_end_to_end_block():
    # context cru do FE -> view_context sintetizado -> bloco de prompt
    from app.orchestrator.context.view_context import (
        view_context_from_context,
        format_view_context,
    )
    block = format_view_context(view_context_from_context({"page_type": "vagas"}))
    assert "Vagas" in block
    assert "tela" in block.lower()

# ---------------------------------------------------------------------------
# Fase 5 (2026-06-10): entity context from metadata.entity_ids
# ---------------------------------------------------------------------------

def test_entity_candidate_synthesized_from_metadata():
    """entity_focus é sintetizado quando metadata.entity_ids tem candidate_id."""
    from app.orchestrator.context.view_context import view_context_from_context
    ctx = {
        "metadata": {
            "entity_ids": {
                "candidate_id": "cand-123",
                "entity_id": "cand-123",
                "entity_type": "candidate",
                "entity_label": "João Silva",
            }
        }
    }
    vc = view_context_from_context(ctx)
    assert vc is not None
    assert vc["entity_focus"]["id"] == "cand-123"
    assert vc["entity_focus"]["type"] == "candidate"
    assert vc["entity_focus"]["label"] == "João Silva"


def test_entity_job_synthesized_from_metadata():
    """entity_focus é sintetizado quando metadata.entity_ids tem job_id."""
    from app.orchestrator.context.view_context import view_context_from_context
    ctx = {
        "metadata": {
            "entity_ids": {
                "job_id": "job-456",
                "entity_id": "job-456",
                "entity_type": "job",
                "entity_label": "Desenvolvedor Sênior",
            }
        }
    }
    vc = view_context_from_context(ctx)
    assert vc is not None
    assert vc["entity_focus"]["id"] == "job-456"
    assert vc["entity_focus"]["type"] == "job"


def test_format_view_context_renders_candidate_focus():
    """format_view_context gera linha 'Candidato em foco' no bloco."""
    from app.orchestrator.context.view_context import format_view_context
    vc = {
        "page_type": "kanban",
        "entity_focus": {
            "type": "candidate",
            "id": "cand-123",
            "label": "João Silva",
        },
    }
    result = format_view_context(vc)
    assert "Candidato em foco" in result
    assert "João Silva" in result
    assert "cand-123" in result


def test_format_view_context_renders_job_focus():
    """format_view_context gera linha 'Vaga em foco' para tipo job."""
    from app.orchestrator.context.view_context import format_view_context
    vc = {
        "entity_focus": {
            "type": "job",
            "id": "job-456",
            "label": "Dev Sênior",
        },
    }
    result = format_view_context(vc)
    assert "Vaga em foco" in result
    assert "Dev Sênior" in result


def test_entity_focus_without_label_uses_id():
    """Sem entity_label, o ID é usado como fallback no bloco."""
    from app.orchestrator.context.view_context import (
        view_context_from_context,
        format_view_context,
    )
    ctx = {
        "metadata": {
            "entity_ids": {
                "candidate_id": "cand-999",
                "entity_type": "candidate",
            }
        }
    }
    vc = view_context_from_context(ctx)
    assert vc is not None
    result = format_view_context(vc)
    assert "cand-999" in result


def test_no_entity_ids_in_metadata_no_entity_focus():
    """Sem entity_ids no metadata, entity_focus não é criado."""
    from app.orchestrator.context.view_context import view_context_from_context
    ctx = {"page_type": "kanban", "metadata": {"source": "rail_a"}}
    vc = view_context_from_context(ctx)
    if vc:
        assert "entity_focus" not in vc


def test_entity_metadata_does_not_override_explicit_view_context():
    """view_context explícito do FE tem precedência sobre síntese de metadata."""
    from app.orchestrator.context.view_context import view_context_from_context
    ctx = {
        "view_context": {"page_type": "kanban"},
        "metadata": {
            "entity_ids": {"candidate_id": "cand-123", "entity_type": "candidate"}
        },
    }
    vc = view_context_from_context(ctx)
    assert vc == {"page_type": "kanban"}

