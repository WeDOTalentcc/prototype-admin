"""
Onda 2C.1 — marcar a vaga como afirmativa auto-habilita a pergunta de autodeclaração
via o produtor de pipeline WSI, server-side (a VAGA é a fonte da verdade, não a flag do FE).

O job grava affirmative_criteria_primary em {gender, race_ethnicity, disability, lgbtqia,
age, refugee, indigenous, other}; AFFIRMATIVE_QUESTIONS usa {pcd, racial, gender, age,
lgbtqia+, refugee, indigenous}. criterion_to_affirmative_type faz a ponte (gap do audit).
"""
import pytest

from app.domains.cv_screening.services.wsi_screening_pipeline import (
    AFFIRMATIVE_QUESTIONS,
    criterion_to_affirmative_type,
)


class TestCriterionMapping:
    def test_all_job_criteria_map(self):
        assert criterion_to_affirmative_type("gender") == "gender"
        assert criterion_to_affirmative_type("race_ethnicity") == "racial"
        assert criterion_to_affirmative_type("disability") == "pcd"
        assert criterion_to_affirmative_type("lgbtqia") == "lgbtqia+"
        assert criterion_to_affirmative_type("age") == "age"
        assert criterion_to_affirmative_type("refugee") == "refugee"
        assert criterion_to_affirmative_type("indigenous") == "indigenous"

    def test_other_and_unknown_fall_back_to_none(self):
        # None -> o injection usa o texto fallback genérico (nunca pergunta ausente).
        assert criterion_to_affirmative_type("other") is None
        assert criterion_to_affirmative_type("") is None
        assert criterion_to_affirmative_type(None) is None
        assert criterion_to_affirmative_type("inexistente") is None

    def test_every_mapped_type_has_question_text(self):
        for crit in ["gender", "race_ethnicity", "disability", "lgbtqia", "age", "refugee", "indigenous"]:
            t = criterion_to_affirmative_type(crit)
            assert t in AFFIRMATIVE_QUESTIONS, f"{crit}->{t} sem texto de pergunta"


class TestNewQuestionTexts:
    def test_refugee_and_indigenous_present(self):
        assert "refugee" in AFFIRMATIVE_QUESTIONS
        assert "indigenous" in AFFIRMATIVE_QUESTIONS
        assert len(AFFIRMATIVE_QUESTIONS["refugee"]) > 20
        assert len(AFFIRMATIVE_QUESTIONS["indigenous"]) > 20

    def test_questions_are_non_eliminatory_in_tone(self):
        # Compliance: autodeclaração não-eliminatória (CLT 373-A / LGPD).
        for text in [AFFIRMATIVE_QUESTIONS["refugee"], AFFIRMATIVE_QUESTIONS["indigenous"]]:
            assert "não elimina" in text or "segue no processo" in text
