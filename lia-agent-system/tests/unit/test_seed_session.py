"""Unit tests for seed_initial_state (Task A5b) — async seam over producer+mapper.

The canonical producer (JobSeedBuilderService.build_seed_from_template) is mocked
with an AsyncMock returning a real JobCreationSeed, so the test exercises the
seam wiring (build -> apply -> state) without touching the DB.
"""
from unittest.mock import AsyncMock, patch

import pytest

from app.domains.job_creation.helpers.seed_session import seed_initial_state
from app.domains.job_creation.schemas import (
    FieldProvenance,
    JobCreationSeed,
    SourceDescriptor,
)

_PRODUCER = (
    "app.domains.job_creation.helpers.seed_session."
    "JobSeedBuilderService.build_seed_from_template"
)

_VACANCY_PRODUCER = (
    "app.domains.job_creation.helpers.seed_session."
    "JobSeedBuilderService.build_seed_from_vacancy"
)


def _seed() -> JobCreationSeed:
    return JobCreationSeed(
        title="Dev Backend Senior",
        seniority="senior",
        work_model="hybrid",
        department="Engenharia",
        salary_min=12000,
        salary_max=16000,
        description="Constroi APIs.",
        provenance={
            "title": FieldProvenance(
                source_type="template", source_id="t1", source_name="Tpl X"
            ),
        },
        source=SourceDescriptor(type="template", id="t1", name="Tpl X"),
    )


async def test_template_source_populates_state():
    state: dict = {}
    with patch(_PRODUCER, new=AsyncMock(return_value=_seed())) as mock_build:
        out = await seed_initial_state(
            state, {"type": "template", "id": "t1"}, "company-1", db=object()
        )
    mock_build.assert_awaited_once()
    assert out is state  # merged in place
    assert state["parsed_title"] == "Dev Backend Senior"
    assert state["parsed_seniority"] == "senior"
    assert state["parsed_model"] == "hybrid"
    assert state["parsed_department"] == "Engenharia"
    assert state["salary_min"] == 12000
    # seed_source + provenance recorded for the review surface.
    # NOTE: apply_seed_to_state keys provenance by the *state* field name.
    assert state["seed_source"] == {"type": "template", "id": "t1", "name": "Tpl X"}
    assert "parsed_title" in state["seed_provenance"]


async def test_none_source_leaves_state_unchanged():
    state = {"foo": "bar"}
    with patch(_PRODUCER, new=AsyncMock()) as mock_build:
        out = await seed_initial_state(state, None, "company-1", db=object())
    mock_build.assert_not_awaited()
    assert out == {"foo": "bar"}


async def test_vacancy_source_populates_state():
    """PR-B1: vacancy source agora despacha para build_seed_from_vacancy e
    semeia o state (antes era no-op \'chega em breve\')."""
    vac_seed = JobCreationSeed(
        title="Eng de Dados Senior",
        seniority="senior",
        work_model="remoto",
        department="Tecnologia",
        location="Sao Paulo, SP",
        employment_type="CLT",
        salary_min=14000,
        salary_max=20000,
        provenance={
            "salary_min": FieldProvenance(
                source_type="vacancy",
                source_id="v1",
                source_name="Vaga X",
                needs_review=True,
            ),
        },
        source=SourceDescriptor(type="vacancy", id="v1", name="Vaga X"),
    )
    state: dict = {}
    with patch(_VACANCY_PRODUCER, new=AsyncMock(return_value=vac_seed)) as mock_build:
        out = await seed_initial_state(
            state, {"type": "vacancy", "id": "v1"}, "company-1", db=object()
        )
    mock_build.assert_awaited_once()  # vacancy producer IS called now
    assert out is state
    assert state["parsed_title"] == "Eng de Dados Senior"
    assert state["parsed_location"] == "Sao Paulo, SP"
    assert state["parsed_employment_type"] == "CLT"
    assert state["seed_source"] == {"type": "vacancy", "id": "v1", "name": "Vaga X"}


async def test_producer_permission_error_fails_soft():
    state = {"foo": "bar"}
    with patch(
        _PRODUCER, new=AsyncMock(side_effect=PermissionError("cross-tenant"))
    ) as mock_build:
        out = await seed_initial_state(
            state, {"type": "template", "id": "tX"}, "company-1", db=object()
        )
    mock_build.assert_awaited_once()
    assert out == {"foo": "bar"}  # unchanged, no crash


async def test_producer_value_error_fails_soft():
    state: dict = {}
    with patch(
        _PRODUCER, new=AsyncMock(side_effect=ValueError("not found"))
    ):
        out = await seed_initial_state(
            state, {"type": "template", "id": "missing"}, "company-1", db=object()
        )
    assert out == {}  # unchanged, no crash


async def test_missing_id_skips_producer():
    state = {"foo": "bar"}
    with patch(_PRODUCER, new=AsyncMock()) as mock_build:
        out = await seed_initial_state(
            state, {"type": "template"}, "company-1", db=object()
        )
    mock_build.assert_not_awaited()
    assert out == {"foo": "bar"}
