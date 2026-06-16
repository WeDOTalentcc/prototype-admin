"""Sensor RRP — bloco candidate_card (Fase 1).

GUIDE: view_candidate_profile emite candidate_card via produtor unico
build_candidate_card_block. Proveniencia honesta: score/recommendation/summary
SO com LiaOpinion real (opinion_id); senao unverified=True (sem numero fabricado).
"""
import pytest
from pydantic import TypeAdapter, ValidationError

from app.shared.rrp_blocks import CandidateCardBlock, ResponseBlock
from app.shared.rrp_ranking_builder import build_candidate_card_block

ROW_WITH_OPINION = {
    "id": "11111111-1111-4111-a111-111111111111",
    "name": "Felipe Almeida",
    "title": "CFO",
    "seniority": "Pleno",
    "location": "São Paulo/SP",
    "experience": 6,
    "skills": ["Oracle", "Power BI", "SAP FI"],
    "score": 92.0,
    "recommendation": "Altamente Recomendado",
    "summary": "Forte em financeiro.",
    "opinion_id": "22222222-2222-4222-a222-222222222222",
}


def test_card_with_opinion_has_score_and_not_unverified():
    b = TypeAdapter(ResponseBlock).validate_python(
        build_candidate_card_block(ROW_WITH_OPINION)[0]
    )
    assert b.kind == "candidate_card"
    assert b.layout == "inline"
    assert b.role == "answer"
    assert b.name == "Felipe Almeida"
    assert b.title == "CFO"
    assert b.experience_years == 6
    assert b.top_skills == ["Oracle", "Power BI", "SAP FI"]
    assert b.score == 92.0
    assert b.recommendation == "Altamente Recomendado"
    assert b.unverified is False


def test_card_without_opinion_is_unverified_no_score():
    # Proveniencia honesta: sem parecer -> sem score/recommendation, unverified.
    row = {k: v for k, v in ROW_WITH_OPINION.items()}
    row["opinion_id"] = None
    b = TypeAdapter(ResponseBlock).validate_python(
        build_candidate_card_block(row)[0]
    )
    assert b.score is None
    assert b.recommendation is None
    assert b.summary is None
    assert b.unverified is True
    # perfil ainda presente
    assert b.name == "Felipe Almeida"
    assert b.top_skills == ["Oracle", "Power BI", "SAP FI"]


def test_score_clamped_0_100():
    row = {**ROW_WITH_OPINION, "score": 150}
    b = build_candidate_card_block(row)[0]
    assert b["score"] == 100.0


def test_top_skills_capped_at_5():
    row = {**ROW_WITH_OPINION, "skills": ["a", "b", "c", "d", "e", "f", "g"]}
    b = build_candidate_card_block(row)[0]
    assert len(b["top_skills"]) == 5


def test_candidate_card_extra_forbid():
    with pytest.raises(ValidationError):
        CandidateCardBlock(
            block_id="candidate_card:x",
            candidate_id="x",
            name="n",
            top_skills=[],
            unverified=True,
            company_id="leak",  # nao pode existir
        )
