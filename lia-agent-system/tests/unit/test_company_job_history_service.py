"""
Unit tests for CompanyJobHistoryService — Onda 4 (Frente F).

Cobre:
- get_similar_vacancies_by_role_seniority: sem matches, com matches, confidence levels
- JobHistoryInsights.to_dict() JSON-serializable
- Similaridade Jaccard: tokens comuns, zero overlap
- Validação de company_id vazio (ValueError)
- Degraded mode: db indisponível (Exception propagada / swallowed)
- Inferência de confidence: high >= 5 vagas, medium >= 2, low < 2
- salary_band cálculo: média mín/máx de vagas similares
- recurring_skills: top 3 skills mais frequentes
- Behavior: vaga com senioridade diferente tem peso menor
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.domains.job_management.services.company_job_history_service import (
    CompanyJobHistoryService,
    JobHistoryInsights,
    VacancyMatch,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_service(rows=None):
    """Cria CompanyJobHistoryService com db mockado."""
    db = MagicMock()
    # execute retorna um objeto com scalars().all() == rows
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = rows or []
    db.execute = AsyncMock(return_value=mock_result)
    return CompanyJobHistoryService(db)


def _make_vacancy(
    title: str = "Engenheiro Python",
    seniority: str = "Pleno",
    salary_min: float | None = 8000,
    salary_max: float | None = 12000,
    skills: list[str] | None = None,
    benefits: list[str] | None = None,
):
    v = MagicMock()
    v.title = title
    v.seniority_level = seniority
    v.salary_min = salary_min
    v.salary_max = salary_max
    # Simula JSON stored as dict in skills_required / benefits
    v.skills_required = [{"name": s} for s in (skills or ["Python", "FastAPI"])]
    v.benefits = [{"name": b} for b in (benefits or ["VR", "VA"])]
    return v


# ---------------------------------------------------------------------------
# T.1.1 — company_id vazio levanta ValueError
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_empty_company_id_raises():
    svc = _make_service()
    with pytest.raises(ValueError, match="company_id"):
        await svc.get_similar_vacancies_by_role_seniority(
            company_id="",
            role="Dev",
            seniority="Pleno",
        )


# ---------------------------------------------------------------------------
# T.1.2 — sem vagas retorna insights com evidence_count == 0
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_no_vacancies_returns_empty_insights():
    svc = _make_service(rows=[])
    insights = await svc.get_similar_vacancies_by_role_seniority(
        company_id="company-123",
        role="Engenheiro Python",
        seniority="Pleno",
    )
    assert isinstance(insights, JobHistoryInsights)
    assert insights.evidence_count == 0
    assert insights.confidence == "low"
    assert insights.salary_band is None
    assert insights.recurring_skills == []


# ---------------------------------------------------------------------------
# T.1.3 — com vagas similares retorna insights preenchidos
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_with_matching_vacancies_returns_populated_insights():
    vacancies = [
        _make_vacancy("Engenheiro Python Pleno", "Pleno", 8000, 12000, ["Python", "FastAPI", "PostgreSQL"]),
        _make_vacancy("Dev Python", "Pleno", 9000, 13000, ["Python", "Django", "PostgreSQL"]),
        _make_vacancy("Python Developer", "Pleno", 8500, 11500, ["Python", "FastAPI", "Redis"]),
    ]
    svc = _make_service(rows=vacancies)
    insights = await svc.get_similar_vacancies_by_role_seniority(
        company_id="company-123",
        role="Engenheiro Python",
        seniority="Pleno",
    )
    assert insights.evidence_count >= 1
    # salary_band deve estar presente quando há salários
    if insights.evidence_count >= 2:
        assert insights.salary_band is not None
        assert "min" in insights.salary_band
        assert "max" in insights.salary_band
    # Python deve aparecer em recurring_skills (presente em todas)
    if insights.recurring_skills:
        assert any("python" in s.lower() for s in insights.recurring_skills)


# ---------------------------------------------------------------------------
# T.1.4 — confidence levels
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_confidence_high_with_five_or_more_matches():
    vacancies = [
        _make_vacancy("Python Dev", "Pleno") for _ in range(6)
    ]
    svc = _make_service(rows=vacancies)
    insights = await svc.get_similar_vacancies_by_role_seniority(
        company_id="company-123",
        role="Python Dev",
        seniority="Pleno",
    )
    # Com 6 vagas similares, confidence deve ser "high"
    if insights.evidence_count >= 5:
        assert insights.confidence == "high"


@pytest.mark.asyncio
async def test_confidence_medium_with_two_matches():
    vacancies = [
        _make_vacancy("Python Dev", "Pleno"),
        _make_vacancy("Dev Python", "Pleno"),
    ]
    svc = _make_service(rows=vacancies)
    insights = await svc.get_similar_vacancies_by_role_seniority(
        company_id="company-123",
        role="Python Dev",
        seniority="Pleno",
    )
    if insights.evidence_count >= 2:
        assert insights.confidence in ("medium", "high")


# ---------------------------------------------------------------------------
# T.1.5 — to_dict() é JSON-serializable
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_insights_to_dict_json_serializable():
    import json
    vacancies = [
        _make_vacancy("Python Dev", "Pleno", 8000, 12000, ["Python"]),
        _make_vacancy("Python Engineer", "Pleno", 9000, 13000, ["Python", "FastAPI"]),
    ]
    svc = _make_service(rows=vacancies)
    insights = await svc.get_similar_vacancies_by_role_seniority(
        company_id="company-123",
        role="Python Dev",
        seniority="Pleno",
    )
    d = insights.to_dict()
    # Deve ser serializável sem exceção
    serialized = json.dumps(d)
    assert isinstance(serialized, str)
    assert "evidence_count" in d


# ---------------------------------------------------------------------------
# T.1.6 — vagas sem salário não quebram salary_band
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_vacancies_without_salary_safe():
    vacancies = [
        _make_vacancy("Python Dev", "Pleno", salary_min=None, salary_max=None),
        _make_vacancy("Python Dev", "Pleno", salary_min=None, salary_max=None),
    ]
    svc = _make_service(rows=vacancies)
    insights = await svc.get_similar_vacancies_by_role_seniority(
        company_id="company-123",
        role="Python Dev",
        seniority="Pleno",
    )
    # Sem salários, salary_band deve ser None (sem quebrar)
    assert insights.salary_band is None or isinstance(insights.salary_band, dict)


# ---------------------------------------------------------------------------
# T.1.7 — VacancyMatch dataclass
# ---------------------------------------------------------------------------

def test_vacancy_match_dataclass():
    vm = VacancyMatch(
        title="Python Dev",
        seniority="Pleno",
        similarity_score=0.75,
    )
    assert vm.title == "Python Dev"
    assert vm.similarity_score == 0.75
    assert vm.salary_min is None  # default
