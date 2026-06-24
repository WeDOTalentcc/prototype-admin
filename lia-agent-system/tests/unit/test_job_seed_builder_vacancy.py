"""Unit tests for JobSeedBuilderService.build_seed_from_vacancy (PR-B1).

Mirrors test_job_seed_builder.py (template) — mocks the vacancy repo so the
mapping/guard logic is tested without a DB (lia-testing layer 2 unit).
Decisao Paulo 2026-06-05: clone a partir de vaga existente, conservador
(salario needs_review; ALWAYS_FRESH nunca; rico vem no PR-B2).
"""
import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.domains.job_creation.schemas import ALWAYS_FRESH_FIELDS, JobCreationSeed
from app.domains.job_creation.services.job_seed_builder_service import (
    JobSeedBuilderService,
)


def _vac(company_id="co-1", **over):
    base = dict(
        id=uuid.uuid4(),
        company_id=company_id,
        title="Engenheiro de Dados Senior",
        seniority_level="senior",
        work_model="remoto",
        department="Tecnologia",
        location="Sao Paulo, SP",
        employment_type="CLT",
        salary_range={"min": 14000, "max": 20000, "currency": "BRL"},
        description="Constroi pipelines de dados.",
        requirements=["Python", "5 anos de experiencia"],
        responsibilities=["Desenhar ETLs", "Garantir qualidade de dados"],
        technical_requirements=[
            {"technology": "Python", "level": "Avancado", "required": True},
            {"technology": "Airflow", "level": "Intermediario"},
        ],
        manager="Fulano Gestor",
        manager_email="gestor@empresa.com",
    )
    base.update(over)
    return SimpleNamespace(**base)


def _svc_with(vac):
    svc = JobSeedBuilderService(db=None)  # db unused; vacancy fetch is mocked
    svc._vacancies.get_by_id_strict_company = AsyncMock(return_value=vac)
    return svc


@pytest.mark.asyncio
async def test_maps_vacancy_fields_and_provenance():
    svc = _svc_with(_vac())
    seed = await svc.build_seed_from_vacancy(str(uuid.uuid4()), company_id="co-1")
    assert isinstance(seed, JobCreationSeed)
    assert seed.title == "Engenheiro de Dados Senior"
    assert seed.seniority == "senior"
    assert seed.work_model == "remoto"
    assert seed.department == "Tecnologia"
    assert seed.location == "Sao Paulo, SP"
    assert seed.employment_type == "CLT"
    assert seed.responsibilities == ["Desenhar ETLs", "Garantir qualidade de dados"]
    assert "Python" in seed.skills and "Airflow" in seed.skills
    assert seed.source.type == "vacancy"
    assert seed.provenance["title"].source_type == "vacancy"


@pytest.mark.asyncio
async def test_vacancy_salary_marked_needs_review():
    svc = _svc_with(_vac())
    seed = await svc.build_seed_from_vacancy(uuid.uuid4(), company_id="co-1")
    assert seed.salary_min == 14000
    assert seed.salary_max == 20000
    assert seed.provenance["salary_min"].needs_review is True
    assert seed.provenance["salary_max"].needs_review is True


@pytest.mark.asyncio
async def test_vacancy_never_carries_always_fresh_fields():
    svc = _svc_with(_vac())
    seed = await svc.build_seed_from_vacancy(uuid.uuid4(), company_id="co-1")
    dumped = seed.model_dump()
    for f in ALWAYS_FRESH_FIELDS:
        assert f not in dumped
    # gestor/email da vaga NUNCA viram seed (sao ALWAYS_FRESH)
    assert "Fulano Gestor" not in str(dumped)


@pytest.mark.asyncio
async def test_vacancy_not_found_or_cross_tenant_raises():
    # get_by_id_strict_company devolve None p/ inexistente E cross-tenant (opaco).
    svc = JobSeedBuilderService(db=None)
    svc._vacancies.get_by_id_strict_company = AsyncMock(return_value=None)
    with pytest.raises(ValueError):
        await svc.build_seed_from_vacancy(uuid.uuid4(), company_id="co-1")


@pytest.mark.asyncio
async def test_vacancy_requirements_array_becomes_text():
    svc = _svc_with(_vac())
    seed = await svc.build_seed_from_vacancy(uuid.uuid4(), company_id="co-1")
    # requirements (ARRAY no model) vira str no seed (campo Optional[str])
    assert isinstance(seed.requirements, str)
    assert "Python" in seed.requirements


@pytest.mark.asyncio
async def test_maps_competencies_and_eligibility():
    svc = _svc_with(_vac(
        behavioral_competencies=[{"competency": "Lideranca", "weight": "Essencial"}],
        eligibility_questions=[
            {"id": "1", "question": "Tem CNH?", "is_eliminatory": True}
        ],
    ))
    seed = await svc.build_seed_from_vacancy(uuid.uuid4(), company_id="co-1")
    # technical_competencies derivadas de technical_requirements (technology)
    assert any(c["skill"] == "Python" for c in seed.technical_competencies)
    assert seed.behavioral_competencies[0]["competencia"] == "Lideranca"
    assert seed.eligibility_questions[0]["question"] == "Tem CNH?"


@pytest.mark.asyncio
async def test_maps_wsi_questions_to_seed_field():
    svc = _svc_with(_vac(
        screening_questions=[{"id": "1", "question": "Conte sobre X", "weight": 5}]
    ))
    seed = await svc.build_seed_from_vacancy(uuid.uuid4(), company_id="co-1")
    assert seed.wsi_questions[0]["question"] == "Conte sobre X"


@pytest.mark.asyncio
async def test_maps_enriched_jd_exact():
    svc = _svc_with(_vac(
        enriched_jd={"titulo_padronizado": "Eng de Dados Sr", "about_role": "..."}
    ))
    seed = await svc.build_seed_from_vacancy(uuid.uuid4(), company_id="co-1")
    assert seed.jd_enriched["titulo_padronizado"] == "Eng de Dados Sr"
    assert seed.provenance["jd_enriched"].needs_review is True
