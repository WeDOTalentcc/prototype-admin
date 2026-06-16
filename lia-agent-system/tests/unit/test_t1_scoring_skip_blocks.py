"""
T1 — Blocos 0/5 (admin) NÃO entram no scoring WSI.

Red→Green:
- Antes do fix: respostas em block_index 0 ou 5 contaminam technical/behavioral_scores.
- Após o fix: blocos 0 e 5 são ignorados pelo _calculate_final_score.
"""
import pytest


def _make_score(score: float, block_type: str, block_index: int) -> dict:
    return {
        "score": score,
        "block_type": block_type,
        "block_index": block_index,
        "competency": "test",
        "trait_weight": 1.0,
    }


def test_blocks_0_and_5_excluded_from_final_score():
    """Respostas em blocos 0 e 5 (admin) não entram no cálculo final."""
    from app.domains.recruitment.services.triagem_session_service.scoring import (
        _calculate_final_score,
    )
    # Bloco 0 (admin): score=1.0 técnico — sem o fix, derruba a média técnica
    # Bloco 5 (admin): score=1.0 comportamental — sem o fix, derruba a média comportamental
    # Blocos reais (1-4): score=4.0 — devem ser a única base
    scores = [
        _make_score(1.0, "technical", 0),   # admin — DEVE ser ignorado
        _make_score(4.0, "technical", 3),   # real
        _make_score(4.0, "behavioral", 4),  # real
        _make_score(1.0, "behavioral", 5),  # admin — DEVE ser ignorado
    ]
    final, recommendation = _calculate_final_score(scores, seniority="pleno")
    # Com só scores 4.0 reais: resultado deve ser alto (aprovado/aguardando)
    assert final >= 6.0, (
        f"Esperado score >= 6.0 sem blocos admin, obtido {final}. "
        "Blocos 0/5 (disponibilidade/salário/encerramento) estão contaminando o cálculo."
    )
    assert recommendation in ("aprovado", "aguardando"), (
        f"Candidato com score real 4.0 não deve ser reprovado. Recommendation: {recommendation}"
    )


def test_only_admin_blocks_fallback_to_neutral():
    """Se TODAS as respostas são de blocos admin (fallback de emergência), retorna score neutro."""
    from app.domains.recruitment.services.triagem_session_service.scoring import (
        _calculate_final_score,
    )
    scores = [
        _make_score(1.0, "technical", 0),
        _make_score(1.0, "behavioral", 5),
    ]
    final, recommendation = _calculate_final_score(scores, seniority="pleno")
    # Sem scores reais → fallback neutro (não reprovado por perguntas admin)
    assert final >= 5.5, (
        f"Fallback de emergência com só blocos admin deve retornar score neutro >= 5.5, obtido {final}"
    )


def test_real_blocks_unaffected_by_skip():
    """Blocos 1-4 continuam sendo pontuados normalmente."""
    from app.domains.recruitment.services.triagem_session_service.scoring import (
        _calculate_final_score,
    )
    scores = [
        _make_score(2.0, "technical", 1),
        _make_score(2.0, "behavioral", 2),
        _make_score(2.0, "technical", 3),
        _make_score(2.0, "behavioral", 4),
    ]
    final, _ = _calculate_final_score(scores, seniority="pleno")
    assert final < 6.0, (
        f"Score baixo (2.0) nos blocos reais deve resultar em score final baixo, obtido {final}"
    )
