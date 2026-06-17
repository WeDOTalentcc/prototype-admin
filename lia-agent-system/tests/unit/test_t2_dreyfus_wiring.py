"""
T2 — Dreyfus wiring: question_framework propagado até scorer + fórmula correta.

RED tests:
1. calculate_wsi_deterministic Dreyfus branch usa fórmula 0.60×auto + 0.40×ctx
2. Dreyfus não aplica penalidade de resposta curta (respostas de autodeclaração são naturalmente breves)
3. Dreyfus não tem STAR components (star_score=0)
4. WSI_BLOCKS_FALLBACK tem question_frameworks em cada bloco
5. _build_wsi_blocks_from_question_set propaga framework=Dreyfus para question_frameworks
"""
import pytest


def test_dreyfus_formula_correct_weights():
    """Dreyfus branch: 0.60×autodeclaracao + 0.40×context_score."""
    from app.domains.cv_screening.services.wsi_deterministic_scorer import (
        calculate_wsi_deterministic,
    )
    # Resposta típica Dreyfus: autodeclaração "4 de 5" + justificativa curta
    result = calculate_wsi_deterministic(
        response_text="Diria que tenho nível 4 de domínio em Python. Uso há 5 anos em projetos profissionais.",
        competency_name="Python",
        question_framework="Dreyfus",
        autodeclaracao_override=4.0,
        contexto_override=3.5,
    )
    # fórmula = 0.60*4.0 + 0.40*3.5 = 2.40 + 1.40 = 3.80
    expected_base = 0.60 * 4.0 + 0.40 * 3.5
    assert abs(result.final_score - expected_base) < 0.3, (
        f"Dreyfus formula deve ser ~{expected_base:.2f}, got {result.final_score}. "
        f"formula_applied={result.formula_applied}"
    )
    assert "dreyfus" in (result.formula_applied or "").lower(), (
        f"formula_applied deve conter 'dreyfus': {result.formula_applied}"
    )


def test_dreyfus_no_star_components():
    """Dreyfus não usa STAR — star_score deve ser 0."""
    from app.domains.cv_screening.services.wsi_deterministic_scorer import (
        calculate_wsi_deterministic,
    )
    result = calculate_wsi_deterministic(
        response_text="Nível 3 de 5 em React.",
        competency_name="React",
        question_framework="Dreyfus",
        autodeclaracao_override=3.0,
        contexto_override=2.5,
    )
    assert result.star_score == 0.0, (
        f"Dreyfus não deve calcular STAR: star_score={result.star_score}"
    )
    assert result.star_components == {}, (
        f"Dreyfus deve ter star_components vazio: {result.star_components}"
    )


def test_dreyfus_formula_version_tag():
    """Dreyfus result deve ter formula_version 'v2-dreyfus'."""
    from app.domains.cv_screening.services.wsi_deterministic_scorer import (
        calculate_wsi_deterministic,
    )
    result = calculate_wsi_deterministic(
        response_text="Tenho nível 2 de SQL.",
        competency_name="SQL",
        question_framework="Dreyfus",
        autodeclaracao_override=2.0,
        contexto_override=2.0,
    )
    assert result.formula_version == "v2-dreyfus", (
        f"formula_version deve ser 'v2-dreyfus': {result.formula_version}"
    )


def test_wsi_blocks_fallback_has_question_frameworks():
    """Cada bloco em WSI_BLOCKS_FALLBACK deve ter question_frameworks como lista não-vazia."""
    from app.domains.recruitment.services.triagem_session_service._shared import (
        WSI_BLOCKS_FALLBACK,
    )
    for block in WSI_BLOCKS_FALLBACK:
        assert "question_frameworks" in block, (
            f"Bloco {block['index']} ({block['name']}) não tem question_frameworks"
        )
        frameworks = block["question_frameworks"]
        assert isinstance(frameworks, list) and len(frameworks) > 0, (
            f"Bloco {block['index']}: question_frameworks deve ser lista não-vazia, got {frameworks}"
        )
        assert len(frameworks) == len(block["questions"]), (
            f"Bloco {block['index']}: len(question_frameworks)={len(frameworks)} != "
            f"len(questions)={len(block['questions'])}"
        )
        for fw in frameworks:
            assert fw in ("CBI", "Bloom", "Dreyfus", "BigFive"), (
                f"Bloco {block['index']}: framework inválido '{fw}'"
            )


def test_build_wsi_blocks_propagates_dreyfus_framework():
    """_build_wsi_blocks_from_question_set propaga framework=Dreyfus para question_frameworks."""
    from app.domains.recruitment.services.triagem_session_service.wsi_blocks import (
        _build_wsi_blocks_from_question_set,
    )
    snapshot = [
        {
            "text": "De 1 a 5, quanto você domina Python?",
            "category": "technical",
            "framework": "Dreyfus",
            "block_id": 3,
            "weight": 1.0,
        },
        {
            "text": "Descreva um projeto técnico desafiador.",
            "category": "technical",
            "framework": "CBI",
            "block_id": 3,
            "weight": 1.0,
        },
    ]
    blocks = _build_wsi_blocks_from_question_set(snapshot)
    block3 = next((b for b in blocks if b["index"] == 3), None)
    assert block3 is not None, "Bloco 3 deve existir"
    assert "question_frameworks" in block3, (
        f"Bloco 3 deve ter question_frameworks: {block3.keys()}"
    )
    assert block3["question_frameworks"] == ["Dreyfus", "CBI"], (
        f"question_frameworks deve ser ['Dreyfus', 'CBI']: {block3['question_frameworks']}"
    )
