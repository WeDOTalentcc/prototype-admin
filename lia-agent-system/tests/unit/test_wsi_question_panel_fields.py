"""Consolidação WSI Fase 2 (2026-05-31): campos opcionais de painel no WSIQuestion canônico.

Direção B (decisão Paulo): a riqueza por-pergunta que vivia no fork
job_creation (block / bloom_level / dreyfus_level / ideal_answer / skill /
trait_ocean) foi portada para o WSIQuestion canônico de cv_screening como
campos OPCIONAIS, derivados via @model_validator quando não setados pelos
builders. Estes testes pinam o contrato — são puros (sem LLM).
"""
import pytest

from app.domains.cv_screening.services.wsi_service.models import WSIQuestion


def _base(**overrides):
    data = dict(
        id="q1",
        competency="Python",
        framework="CBI",
        question_type="contextual",
        question_text="Conte sobre...",
        weight=0.9,
        expected_signals=["Contexto", "Ação", "Resultado"],
        scoring_criteria={},
    )
    data.update(overrides)
    return WSIQuestion(**data)


@pytest.mark.medium
def test_skill_mirrors_competency_when_absent():
    q = _base()
    assert q.skill == "Python"


@pytest.mark.medium
def test_explicit_skill_preserved():
    q = _base(skill="SQL avançado")
    assert q.skill == "SQL avançado"


@pytest.mark.medium
def test_ideal_answer_derived_from_score_5():
    q = _base(scoring_criteria={"score_5": "Resposta-modelo ideal", "score_1": "x"})
    assert q.ideal_answer == "Resposta-modelo ideal"


@pytest.mark.medium
def test_trait_ocean_from_big_five_mapping():
    q = _base(framework="BigFive", question_type="situational", big_five_mapping="conscientiousness")
    assert q.trait_ocean == "conscientiousness"


@pytest.mark.medium
def test_trait_ocean_from_scoring_criteria_ocean_trait():
    q = _base(
        framework="BigFive", question_type="situational",
        scoring_criteria={"ocean_trait": "openness"},
    )
    assert q.trait_ocean == "openness"


@pytest.mark.medium
def test_block_defaults_technical_for_non_bigfive():
    assert _base(framework="CBI", question_type="contextual").block == "technical"
    assert _base(framework="Dreyfus", question_type="autodeclaration").block == "technical"
    assert _base(framework="Bloom", question_type="microcase").block == "technical"


@pytest.mark.medium
def test_block_defaults_behavioral_for_bigfive():
    q = _base(framework="BigFive", question_type="situational")
    assert q.block == "behavioral"


@pytest.mark.medium
def test_explicit_block_preserved():
    # CBI comportamental: builder seta block=competency.type explicitamente.
    q = _base(framework="CBI", question_type="contextual", block="behavioral")
    assert q.block == "behavioral"


@pytest.mark.medium
def test_bloom_dreyfus_optional_and_bounded():
    q = _base(framework="Bloom", question_type="microcase", bloom_level=5)
    assert q.bloom_level == 5
    assert q.dreyfus_level is None
    with pytest.raises(Exception):
        _base(bloom_level=7)  # ge=1, le=6
    with pytest.raises(Exception):
        _base(dreyfus_level=6)  # ge=1, le=5


@pytest.mark.medium
def test_backward_compat_minimal_construction():
    # Sem nenhum campo de painel → constrói e deriva sem erro (fluxo análise).
    q = _base()
    assert q.bloom_level is None and q.dreyfus_level is None
    assert q.ideal_answer is None  # score_5 ausente
    assert q.fallback_used is False
