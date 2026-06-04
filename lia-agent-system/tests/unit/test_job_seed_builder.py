"""Unit tests for JobSeedBuilderService.build_seed_from_template (Task A2).

Mocks JobTemplateService.get_template_by_id so the mapping/guard logic is
tested without a DB (lia-testing pyramid: layer 2 unit). Contract/integration
with a real template row comes later.
"""
import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.domains.job_creation.schemas import ALWAYS_FRESH_FIELDS, JobCreationSeed
from app.domains.job_creation.services.job_seed_builder_service import (
    JobSeedBuilderService,
)


def _tpl(company_id=None, **over):
    base = dict(
        id=uuid.uuid4(),
        company_id=company_id,
        title="Dev Backend Senior",
        seniority="senior",
        work_model="hybrid",
        default_description="Constroi APIs.",
        default_requirements="Python, 5 anos.",
        default_nice_to_have="Kafka.",
        default_responsibilities=["Desenhar APIs", "Mentorar"],
        default_skills=["Python", "FastAPI"],
        salary_range_min=12000,
        salary_range_max=16000,
    )
    base.update(over)
    return SimpleNamespace(**base)


def _svc_with(tpl):
    svc = JobSeedBuilderService(db=None)  # db unused; template fetch is mocked
    svc._templates.get_template_by_id = AsyncMock(return_value=tpl)
    return svc


@pytest.mark.asyncio
async def test_maps_fields_and_provenance():
    svc = _svc_with(_tpl())
    seed = await svc.build_seed_from_template(str(uuid.uuid4()), company_id="co-1")
    assert isinstance(seed, JobCreationSeed)
    assert seed.title == "Dev Backend Senior"
    assert seed.skills == ["Python", "FastAPI"]
    assert seed.responsibilities == ["Desenhar APIs", "Mentorar"]
    assert seed.source.type == "template"
    assert seed.provenance["title"].source_type == "template"
    assert seed.coverage_total == 12
    assert seed.coverage_filled >= 8


@pytest.mark.asyncio
async def test_salary_marked_needs_review():
    svc = _svc_with(_tpl())
    seed = await svc.build_seed_from_template(uuid.uuid4(), company_id="co-1")
    assert seed.salary_min == 12000
    assert seed.provenance["salary_min"].needs_review is True
    assert seed.provenance["salary_max"].needs_review is True


@pytest.mark.asyncio
async def test_never_carries_always_fresh_fields():
    svc = _svc_with(_tpl())
    seed = await svc.build_seed_from_template(uuid.uuid4(), company_id="co-1")
    dumped = seed.model_dump()
    for f in ALWAYS_FRESH_FIELDS:
        assert f not in dumped


@pytest.mark.asyncio
async def test_system_template_readable_by_any_company():
    svc = _svc_with(_tpl(company_id=None))  # is_system
    seed = await svc.build_seed_from_template(uuid.uuid4(), company_id="qualquer-co")
    assert seed.title is not None


@pytest.mark.asyncio
async def test_company_template_cross_company_rejected():
    svc = _svc_with(_tpl(company_id="co-A"))
    with pytest.raises(PermissionError):
        await svc.build_seed_from_template(uuid.uuid4(), company_id="co-B")


@pytest.mark.asyncio
async def test_template_not_found_raises():
    svc = _svc_with(None)
    with pytest.raises(ValueError):
        await svc.build_seed_from_template(uuid.uuid4(), company_id="co-1")


@pytest.mark.asyncio
async def test_skills_normalized_from_dicts():
    svc = _svc_with(_tpl(default_skills=[{"skill": "Python"}, "FastAPI", {"name": "Go"}]))
    seed = await svc.build_seed_from_template(uuid.uuid4(), company_id="co-1")
    assert seed.skills == ["Python", "FastAPI", "Go"]


@pytest.mark.asyncio
async def test_sparse_template_low_coverage():
    sparse = _tpl(
        default_description=None,
        default_requirements=None,
        default_nice_to_have=None,
        default_responsibilities=[],
        default_skills=[],
        salary_range_min=None,
        salary_range_max=None,
    )
    svc = _svc_with(sparse)
    seed = await svc.build_seed_from_template(uuid.uuid4(), company_id="co-1")
    assert seed.coverage_filled <= 3
