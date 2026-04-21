"""Unit tests for the meta-question detector (Task #726)."""
from __future__ import annotations

import pytest

from app.orchestrator.meta_question_detector import (
    detect_meta_capability_question,
    get_meta_question_stats,
    reset_meta_question_stats,
)


@pytest.fixture(autouse=True)
def _reset_stats():
    reset_meta_question_stats()
    yield
    reset_meta_question_stats()


@pytest.mark.parametrize(
    "message",
    [
        "consegue buscar candidatos no banco local ou global?",
        "você sabe agendar entrevista?",
        "tem como exportar candidatos?",
        "dá pra mover candidatos em lote?",
        "é possível criar uma vaga nova?",
        "Lia, consegue listar vagas?",
        "como faço pra criar tarefa?",
    ],
)
def test_meta_questions_are_detected(message: str) -> None:
    result = detect_meta_capability_question(message)
    assert result is not None, f"expected meta-question for: {message!r}"
    assert result.reply
    # All intent-aware reply templates begin with "Sim, posso" and include
    # at least one concrete example phrase.
    assert result.reply.startswith("Sim, posso")
    assert "por exemplo" in result.reply or "ex.:" in result.reply


@pytest.mark.parametrize(
    "message",
    [
        # Real commands — no capability opener
        "busque candidatos React em São Paulo",
        "agenda entrevista com Marco amanhã às 14h",
        "exporta os candidatos da vaga V0042",
        "lista vagas ativas",
        "cria uma vaga de Tech Lead remoto",
        # Capability opener BUT specific filter present → real command
        "consegue buscar candidatos React em São Paulo?",
        "tem como buscar candidatos para a vaga V0042?",
        "você sabe procurar candidatos com Python sênior?",
        # Capability opener but no action verb → out of scope (not meta)
        "consegue me ouvir?",
        # Empty / whitespace
        "",
        "   ",
    ],
)
def test_non_meta_messages_are_passed_through(message: str) -> None:
    assert detect_meta_capability_question(message) is None


def test_telemetry_counts_intercepted_questions() -> None:
    detect_meta_capability_question("consegue buscar candidatos?")
    detect_meta_capability_question("você sabe buscar candidatos?")
    detect_meta_capability_question("tem como exportar candidatos?")
    stats = get_meta_question_stats()
    assert stats["total"] == 3
    assert "busca" in (stats["by_verb"] or {}) or "busca" in str(stats["by_verb"])
    # by_verb is a dict — exporta and busca should both be present
    by_verb = stats["by_verb"]
    assert isinstance(by_verb, dict)
    assert sum(by_verb.values()) == 3


def test_long_messages_are_not_intercepted() -> None:
    # 230+ char message — capability questions are short by nature.
    long_msg = "consegue buscar candidatos " + ("e mais texto " * 30) + "?"
    assert detect_meta_capability_question(long_msg) is None
