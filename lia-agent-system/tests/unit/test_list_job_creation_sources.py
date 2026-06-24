"""Unit tests for the `list_job_creation_sources` wizard tool.

Create-from-source agentic flow: the recruiter asks to create a vacancy
"a partir de um modelo/vaga existente"; the LIA calls this tool to list the
candidate sources (existing vacancies + archetypes/templates) and disambiguate.

Paulo's firm requirement under test: EVERY vacancy source item MUST carry the
vacancy `id` AND the `recruiter` so the recruiter can disambiguate.

Pure unit test — all repos + JobTemplateService mocked (AsyncMock); no DB.
Multi-tenancy `company_id` is injected by `@tool_handler` from the
`_current_company_id` ContextVar (set here in a fixture), never from payload.
"""
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.domains.job_management.agents.wizard_tool_registry import (
    TOOL_DEFINITIONS,
    _wrap_list_job_creation_sources,
)
from app.middleware.auth_enforcement import _current_company_id

COMPANY_ID = "11111111-1111-1111-1111-111111111111"


@pytest.fixture()
def _tenant_ctx():
    """Populate + reset the tenant ContextVar the tool_handler reads."""
    token = _current_company_id.set(COMPANY_ID)
    try:
        yield
    finally:
        _current_company_id.reset(token)


def _vacancy(**kw):
    base = dict(
        id="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
        job_id="WDT-2025-001",
        title="Engenheiro de Software Pleno",
        recruiter="Paula Recrutadora",
        manager="Carlos Gestor",
        department="Engenharia",
        status="Ativa",
    )
    base.update(kw)
    return SimpleNamespace(**base)


def _template(**kw):
    base = dict(
        id="bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
        title="Desenvolvedor Backend",
        seniority="pleno",
        category="engineering",
        subcategory="backend",
        is_system=True,
        usage_count=42,
    )
    base.update(kw)
    return SimpleNamespace(**base)


def _patch_db_and_services(monkeypatch, *, vacancies, templates,
                           list_vacancies=None):
    """Patch AsyncSessionLocal + repo + JobTemplateService used by the tool.

    Returns the repo MagicMock so tests can assert which search path ran.
    """
    import app.domains.job_management.agents.wizard_tool_registry as mod

    # ── AsyncSessionLocal() async context manager ────────────────────────
    fake_db = MagicMock(name="db")
    cm = MagicMock(name="session_cm")
    cm.__aenter__ = AsyncMock(return_value=fake_db)
    cm.__aexit__ = AsyncMock(return_value=False)
    monkeypatch.setattr(mod, "AsyncSessionLocal", lambda: cm, raising=False)
    # Also patch the canonical import location (tool imports locally).
    monkeypatch.setattr(
        "app.core.database.AsyncSessionLocal", lambda: cm, raising=False
    )

    # ── JobVacancyCRUDRepository ─────────────────────────────────────────
    repo = MagicMock(name="vac_repo")
    repo.search_for_summary_by_criteria = AsyncMock(return_value=list(vacancies))
    repo.list_vacancies = AsyncMock(
        return_value=list(list_vacancies if list_vacancies is not None else vacancies)
    )
    monkeypatch.setattr(
        "app.domains.job_management.repositories.job_vacancy_crud_repository."
        "JobVacancyCRUDRepository",
        lambda db: repo,
        raising=False,
    )

    # ── JobTemplateService ───────────────────────────────────────────────
    svc = MagicMock(name="tpl_svc")
    svc.get_templates = AsyncMock(return_value=list(templates))
    monkeypatch.setattr(
        "app.domains.job_management.services.job_template_service."
        "JobTemplateService",
        lambda db: svc,
        raising=False,
    )
    return repo, svc


@pytest.mark.asyncio
async def test_vacancy_items_carry_id_and_recruiter(monkeypatch, _tenant_ctx):
    """Paulo's requirement: every vacancy item has non-empty id AND recruiter."""
    _patch_db_and_services(
        monkeypatch,
        vacancies=[_vacancy()],
        templates=[_template()],
    )

    result = await _wrap_list_job_creation_sources()

    assert result["success"] is True
    vacancy_items = [s for s in result["data"]["sources"] if s["type"] == "vacancy"]
    assert vacancy_items, "expected at least one vacancy source"
    for item in vacancy_items:
        assert item["id"], "vacancy source missing id"
        assert item["recruiter"], "vacancy source missing recruiter"
        # Gestor is also part of the disambiguation contract.
        assert "manager" in item
        assert "job_id" in item


@pytest.mark.asyncio
async def test_query_matching_manager_returns_vacancy(monkeypatch, _tenant_ctx):
    """A query that matches a manager name exercises the search-by-gestor path."""
    matched = _vacancy(manager="Mariana Líder", title="Designer Sênior")
    repo, _svc = _patch_db_and_services(
        monkeypatch,
        vacancies=[matched],
        templates=[],
    )

    result = await _wrap_list_job_creation_sources(query="Mariana Líder")

    # The criteria-based search (gestor path) must have been used, not list_vacancies.
    assert repo.search_for_summary_by_criteria.await_count >= 1
    assert repo.list_vacancies.await_count == 0
    # The gestor criteria must have been passed through.
    call_kwargs = repo.search_for_summary_by_criteria.await_args.kwargs
    assert call_kwargs["criteria"].get("gestor") == "Mariana Líder"

    vacancy_items = [s for s in result["data"]["sources"] if s["type"] == "vacancy"]
    assert any(s["manager"] == "Mariana Líder" for s in vacancy_items)


@pytest.mark.asyncio
async def test_templates_appear_with_type_template(monkeypatch, _tenant_ctx):
    """Archetypes are returned as type='template' with id + title."""
    _patch_db_and_services(
        monkeypatch,
        vacancies=[],
        templates=[_template(title="Analista de Dados")],
    )

    result = await _wrap_list_job_creation_sources()

    template_items = [s for s in result["data"]["sources"] if s["type"] == "template"]
    assert template_items, "expected at least one template source"
    for item in template_items:
        assert item["id"]
        assert item["title"]
        assert item["type"] == "template"


def test_tooldefinition_has_no_company_id_param():
    """Multi-tenancy: company_id must NEVER be a tool parameter (comes from JWT)."""
    tool = next(
        (t for t in TOOL_DEFINITIONS if t.name == "list_job_creation_sources"),
        None,
    )
    assert tool is not None, "list_job_creation_sources not registered"
    props = tool.parameters.get("properties", {})
    assert "company_id" not in props
    # The only exposed parameter is the optional free-text query.
    assert set(props.keys()) <= {"query"}
