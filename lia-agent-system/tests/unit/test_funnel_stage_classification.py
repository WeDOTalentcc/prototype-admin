"""P1-2 sensor — classify_funnel_stage (mapeamento stage -> bucket do funil).

Pina a lógica do funil real (substituiu generate_lia_metrics random). Pura,
sem DB. Cobre os stages canônicos reais observados em vacancy_candidates
(screening/Triagem/interview_*/Entrevista/offer/hired/sourcing/rejected).
"""
import pytest

from app.domains.job_management.repositories.job_vacancy_crud_repository import (
    classify_funnel_stage,
)


@pytest.mark.parametrize(
    "stage,expected",
    [
        # screening
        ("screening", "screening"),
        ("Triagem", "screening"),
        ("triagem", "screening"),
        # interview (todas as variantes reais do banco)
        ("interview_hr", "interview"),
        ("interview_manager", "interview"),
        ("interview_technical", "interview"),
        ("Entrevista", "interview"),
        ("interview", "interview"),
        # final / oferta
        ("offer", "final"),
        ("oferta", "final"),
        # hired
        ("hired", "hired"),
        ("contratado", "hired"),
        # fora do funil (contam só no total)
        ("sourcing", None),
        ("long_list", None),
        ("short_list", None),
        ("rejected", None),
        # robustez
        ("", None),
        (None, None),
        ("  SCREENING  ", "screening"),
    ],
)
def test_classify_funnel_stage(stage, expected):
    assert classify_funnel_stage(stage) == expected
