"""Contract tests: PipelineTemplateRepository.list_for_suggestion + /suggest endpoint.

Sprint Pipeline Templates Afya 2026-05-26 — Fase 4.1 (TDD canonical green).

Scoring canonical:
  - department match: 0.50
  - seniority match: 0.25
  - job_family match: 0.25
  - case-insensitive comparison

Fallback: nenhum template tem hints + existe default → default com score 0.5.

Garante:
1. Match completo (3 dims) → 1.0
2. Match parcial (dept only) → 0.50
3. Match parcial (seniority only) → 0.25
4. Match parcial (family only) → 0.25
5. Match parcial (dept + seniority) → 0.75
6. Nenhum match com hints configurados → 0.0
7. Fallback default 0.5 quando nenhum template tem hints
8. Case-insensitive match
9. Archived templates NÃO aparecem
10. Endpoint /suggest aplica threshold + top corretamente
"""
from __future__ import annotations

import uuid

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.domains.pipeline.repositories.pipeline_template_repository import (
    PipelineTemplateRepository,
)
from lia_models.pipeline_template import PipelineTemplate


COMPANY_A = "company-a-suggest"


@pytest_asyncio.fixture
async def db_session() -> AsyncSession:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(
            lambda sync_conn: PipelineTemplate.__table__.create(sync_conn, checkfirst=True)
        )
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session
    await engine.dispose()


def _stages():
    return [{"name": "S1", "order": 1, "type": "manual", "sla_days": 2}]


async def _make_template(
    repo: PipelineTemplateRepository,
    name: str,
    *,
    dept_hint=None,
    sen_hint=None,
    fam_hint=None,
    is_default: bool = False,
) -> PipelineTemplate:
    return await repo.create(
        COMPANY_A,
        {
            "name": name,
            "stages": _stages(),
            "department_hint": dept_hint,
            "seniority_hint": sen_hint,
            "job_family_hint": fam_hint,
            "is_default": is_default,
        },
        created_by="u",
    )


# ---------------------------------------------------------------------------
# Scoring exact matrix
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_scoring_full_match_1_0(db_session):
    repo = PipelineTemplateRepository(db_session)
    t = await _make_template(
        repo, "Tech",
        dept_hint=["Engineering"], sen_hint=["Sênior"], fam_hint=["Backend"],
    )
    scored = await repo.list_for_suggestion(
        COMPANY_A, department="Engineering", seniority="Sênior", job_family="Backend"
    )
    assert scored[0][0].id == t.id
    assert scored[0][1] == pytest.approx(1.0)


@pytest.mark.asyncio
async def test_scoring_department_only_0_50(db_session):
    repo = PipelineTemplateRepository(db_session)
    t = await _make_template(
        repo, "Dept", dept_hint=["Sales"], sen_hint=["Pleno"], fam_hint=["Account"]
    )
    scored = await repo.list_for_suggestion(COMPANY_A, department="Sales")
    assert scored[0][1] == pytest.approx(0.50)


@pytest.mark.asyncio
async def test_scoring_seniority_only_0_25(db_session):
    repo = PipelineTemplateRepository(db_session)
    await _make_template(repo, "Sen", sen_hint=["Sênior"])
    scored = await repo.list_for_suggestion(COMPANY_A, seniority="Sênior")
    assert scored[0][1] == pytest.approx(0.25)


@pytest.mark.asyncio
async def test_scoring_family_only_0_25(db_session):
    repo = PipelineTemplateRepository(db_session)
    await _make_template(repo, "Fam", fam_hint=["Frontend"])
    scored = await repo.list_for_suggestion(COMPANY_A, job_family="Frontend")
    assert scored[0][1] == pytest.approx(0.25)


@pytest.mark.asyncio
async def test_scoring_dept_plus_seniority_0_75(db_session):
    repo = PipelineTemplateRepository(db_session)
    await _make_template(
        repo, "DS",
        dept_hint=["Engineering"], sen_hint=["Pleno"], fam_hint=["Other"],
    )
    scored = await repo.list_for_suggestion(
        COMPANY_A, department="Engineering", seniority="Pleno"
    )
    assert scored[0][1] == pytest.approx(0.75)


@pytest.mark.asyncio
async def test_scoring_no_match_with_hints_configured_0_0(db_session):
    repo = PipelineTemplateRepository(db_session)
    await _make_template(repo, "Hinted", dept_hint=["Engineering"])
    scored = await repo.list_for_suggestion(COMPANY_A, department="Marketing")
    # Template existe com hints, mas inputs não casam — score 0.0
    assert scored[0][1] == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# Fallback default 0.5
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_fallback_default_returned_when_no_hints_configured(db_session):
    """Nenhum template tem hints + existe default → default com score 0.5."""
    repo = PipelineTemplateRepository(db_session)
    await _make_template(repo, "Other")
    default = await _make_template(repo, "Default", is_default=True)

    scored = await repo.list_for_suggestion(
        COMPANY_A, department="Anything", seniority="Anything"
    )
    # First entry MUST be the default with 0.5
    assert scored[0][0].id == default.id
    assert scored[0][1] == pytest.approx(0.5)


@pytest.mark.asyncio
async def test_fallback_default_not_triggered_when_any_template_has_hints(db_session):
    """Se algum template TEM hints, mesmo sem match, fallback NÃO dispara."""
    repo = PipelineTemplateRepository(db_session)
    await _make_template(repo, "Hinted", dept_hint=["Engineering"])
    default = await _make_template(repo, "Default", is_default=True)

    scored = await repo.list_for_suggestion(COMPANY_A, department="UnrelatedDept")
    # Não deve ter score 0.5 fallback — tem template hinted
    max_score = max(s for _, s in scored)
    assert max_score == pytest.approx(0.0), "fallback indevido com templates hinted presentes"


# ---------------------------------------------------------------------------
# Case-insensitive match
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_case_insensitive_match(db_session):
    repo = PipelineTemplateRepository(db_session)
    await _make_template(repo, "Tech", dept_hint=["Engineering"])

    scored = await repo.list_for_suggestion(COMPANY_A, department="engineering")
    assert scored[0][1] == pytest.approx(0.50)

    scored2 = await repo.list_for_suggestion(COMPANY_A, department="ENGINEERING")
    assert scored2[0][1] == pytest.approx(0.50)


@pytest.mark.asyncio
async def test_case_insensitive_whitespace_strip(db_session):
    repo = PipelineTemplateRepository(db_session)
    await _make_template(repo, "Tech", dept_hint=["Engineering"])
    scored = await repo.list_for_suggestion(COMPANY_A, department="  Engineering  ")
    assert scored[0][1] == pytest.approx(0.50)


# ---------------------------------------------------------------------------
# Archived templates excluded
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_archived_templates_not_in_suggestion(db_session):
    """Sensor canonical: archived templates NÃO aparecem em list_for_suggestion."""
    repo = PipelineTemplateRepository(db_session)
    active = await _make_template(repo, "Active", dept_hint=["Engineering"])
    archived = await _make_template(repo, "Archived", dept_hint=["Engineering"])
    await repo.archive(archived, updated_by="u")

    scored = await repo.list_for_suggestion(COMPANY_A, department="Engineering")
    ids = {t.id for t, _ in scored}
    assert active.id in ids
    assert archived.id not in ids, "archived template MUST NOT appear in suggestions"


@pytest.mark.asyncio
async def test_inactive_templates_not_in_suggestion(db_session):
    """soft_deleted (is_active=False) templates também não aparecem."""
    repo = PipelineTemplateRepository(db_session)
    active = await _make_template(repo, "Active", dept_hint=["Engineering"])
    inactive = await _make_template(repo, "Inactive", dept_hint=["Engineering"])
    await repo.soft_delete(inactive)

    scored = await repo.list_for_suggestion(COMPANY_A, department="Engineering")
    ids = {t.id for t, _ in scored}
    assert active.id in ids
    assert inactive.id not in ids


# ---------------------------------------------------------------------------
# Endpoint /suggest threshold + top default
# ---------------------------------------------------------------------------


def test_endpoint_suggest_default_threshold_and_top():
    """Pin endpoint defaults: threshold=0.4, top=3 (Query defaults)."""
    import inspect

    from app.api.v1 import pipeline_templates as pt_module

    sig = inspect.signature(pt_module.suggest_pipeline_template)
    threshold_param = sig.parameters["threshold"]
    top_param = sig.parameters["top"]

    # Query(...) default is wrapped — extract via .default attr
    assert threshold_param.default.default == 0.4
    assert top_param.default.default == 3


def test_endpoint_suggest_registered():
    """Endpoint registrado em router com path /suggest."""
    from app.api.v1.pipeline_templates import router

    paths = [r.path for r in router.routes]
    assert any(p.endswith("/suggest") for p in paths), (
        f"GET /suggest endpoint missing. Routes: {paths}"
    )
