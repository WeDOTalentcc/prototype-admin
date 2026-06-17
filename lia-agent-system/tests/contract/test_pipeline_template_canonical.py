"""Contract tests: PipelineTemplateRepository canonical CRUD + multi-tenancy.

Sprint Pipeline Templates Afya 2026-05-26 — Fase 4.1 (TDD canonical green).

Garante:
1. Multi-tenancy fail-closed via _require_company_id gate (ValueError em "").
2. Multi-tenancy isolation: list/get_by_id de company A não vê templates de B.
3. CRUD ciclo completo: create → get → update → soft_delete.
4. is_default exclusivo: criar com is_default=True desativa default anterior.
5. clone preserva hint fields + reseta usage_count=0.
6. archive vs soft_delete são semanticamente distintos:
   - archive() seta is_archived=True; is_active permanece True
   - soft_delete() seta is_active=False; is_archived permanece como estava
7. list_for_company default exclui is_archived=False; passar is_archived=None
   inclui ambos.

Estratégia: usa AsyncSession em memória (sqlite + async) via fixture isolada.
"""
from __future__ import annotations

import uuid

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.domains.pipeline.repositories.pipeline_template_repository import (
    PipelineTemplateRepository,
    _require_company_id,
)
from lia_config.database import Base
from lia_models.pipeline_template import PipelineTemplate


COMPANY_A = "company-a-uuid"
COMPANY_B = "company-b-uuid"


# ---------------------------------------------------------------------------
# Async sqlite in-memory fixture (isolated per test)
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def db_session() -> AsyncSession:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        # Only create the pipeline_templates table — keep schema minimal
        await conn.run_sync(
            lambda sync_conn: PipelineTemplate.__table__.create(sync_conn, checkfirst=True)
        )
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session
    await engine.dispose()


def _stages():
    return [
        {"name": "Triagem", "order": 1, "type": "automatic", "sla_days": 2},
        {"name": "Entrevista", "order": 2, "type": "manual", "sla_days": 3},
    ]


# ---------------------------------------------------------------------------
# 1. _require_company_id fail-closed gate
# ---------------------------------------------------------------------------


def test_require_company_id_raises_on_empty_string():
    with pytest.raises(ValueError, match="company_id is required"):
        _require_company_id("")


def test_require_company_id_raises_on_none():
    with pytest.raises(ValueError, match="company_id is required"):
        _require_company_id(None)


def test_require_company_id_passes_with_valid():
    assert _require_company_id(COMPANY_A) == COMPANY_A


@pytest.mark.asyncio
async def test_repository_methods_fail_closed_on_empty_company_id(db_session):
    """Defense-in-depth: caller esquecendo company_id explode rápido."""
    repo = PipelineTemplateRepository(db_session)
    with pytest.raises(ValueError, match="company_id is required"):
        await repo.list_for_company("")
    with pytest.raises(ValueError, match="company_id is required"):
        await repo.get_by_id(uuid.uuid4(), "")
    with pytest.raises(ValueError, match="company_id is required"):
        await repo.create("", {"name": "x", "stages": []}, created_by="u")
    with pytest.raises(ValueError, match="company_id is required"):
        await repo.count_active("")
    with pytest.raises(ValueError, match="company_id is required"):
        await repo.get_by_name("", "x")
    with pytest.raises(ValueError, match="company_id is required"):
        await repo.seed_defaults("", created_by="u")
    with pytest.raises(ValueError, match="company_id is required"):
        await repo.list_for_suggestion("")


# ---------------------------------------------------------------------------
# 2. Multi-tenancy isolation
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_for_company_does_not_leak_cross_tenant(db_session):
    repo = PipelineTemplateRepository(db_session)
    await repo.create(COMPANY_A, {"name": "A-template", "stages": _stages()}, created_by="ua")
    await repo.create(COMPANY_B, {"name": "B-template", "stages": _stages()}, created_by="ub")

    items_a, total_a = await repo.list_for_company(COMPANY_A)
    items_b, total_b = await repo.list_for_company(COMPANY_B)

    assert total_a == 1 and total_b == 1
    assert {t.company_id for t in items_a} == {COMPANY_A}
    assert {t.company_id for t in items_b} == {COMPANY_B}
    assert items_a[0].name == "A-template"
    assert items_b[0].name == "B-template"


@pytest.mark.asyncio
async def test_get_by_id_returns_none_cross_tenant(db_session):
    """Canonical: cross-tenant lookup retorna None, NUNCA expõe row."""
    repo = PipelineTemplateRepository(db_session)
    tA = await repo.create(COMPANY_A, {"name": "A", "stages": _stages()}, created_by="u")

    fetched = await repo.get_by_id(tA.id, COMPANY_B)
    assert fetched is None, "cross-tenant get_by_id MUST return None"

    fetched_correct = await repo.get_by_id(tA.id, COMPANY_A)
    assert fetched_correct is not None
    assert fetched_correct.id == tA.id


# ---------------------------------------------------------------------------
# 3. CRUD ciclo completo
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_crud_cycle_create_get_update_soft_delete(db_session):
    repo = PipelineTemplateRepository(db_session)

    # create
    t = await repo.create(
        COMPANY_A,
        {"name": "Initial", "description": "desc", "stages": _stages()},
        created_by="user@x",
    )
    assert t.id is not None
    assert t.is_active is True
    assert t.is_archived is False
    assert t.usage_count == 0

    # get
    fetched = await repo.get_by_id(t.id, COMPANY_A)
    assert fetched is not None
    assert fetched.name == "Initial"

    # update
    updated = await repo.update(t, {"name": "Renamed", "description": "v2"}, updated_by="user2@x")
    assert updated.name == "Renamed"
    assert updated.description == "v2"
    assert updated.updated_by == "user2@x"

    # soft_delete (legacy)
    await repo.soft_delete(t)
    assert t.is_active is False
    # archive state independent
    assert t.is_archived is False


# ---------------------------------------------------------------------------
# 4. is_default exclusividade
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_is_default_exclusivity_clear_default_unflags_previous(db_session):
    """clear_default DEVE desativar default anterior antes de promover novo."""
    repo = PipelineTemplateRepository(db_session)
    tA = await repo.create(
        COMPANY_A, {"name": "First", "stages": _stages(), "is_default": True}, created_by="u"
    )
    assert tA.is_default is True

    # Simulating service flow: clear_default before creating new default
    await repo.clear_default(COMPANY_A)
    tB = await repo.create(
        COMPANY_A, {"name": "Second", "stages": _stages(), "is_default": True}, created_by="u"
    )
    assert tB.is_default is True

    # Reload tA — should no longer be default
    refreshed = await repo.get_by_id(tA.id, COMPANY_A)
    assert refreshed.is_default is False, "Previous default MUST be cleared"


@pytest.mark.asyncio
async def test_clear_default_does_not_touch_other_tenant(db_session):
    """Multi-tenancy: clear_default em A não afeta default de B."""
    repo = PipelineTemplateRepository(db_session)
    tA = await repo.create(
        COMPANY_A, {"name": "A", "stages": _stages(), "is_default": True}, created_by="u"
    )
    tB = await repo.create(
        COMPANY_B, {"name": "B", "stages": _stages(), "is_default": True}, created_by="u"
    )

    await repo.clear_default(COMPANY_A)

    refreshed_b = await repo.get_by_id(tB.id, COMPANY_B)
    assert refreshed_b.is_default is True, "clear_default(A) leaked into B"


# ---------------------------------------------------------------------------
# 5. clone preserva hint fields + reseta usage_count
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_clone_preserves_hints_and_resets_usage_count(db_session):
    repo = PipelineTemplateRepository(db_session)
    original = await repo.create(
        COMPANY_A,
        {
            "name": "Tech",
            "stages": _stages(),
            "department_hint": ["Engineering"],
            "seniority_hint": ["Sênior"],
            "job_family_hint": ["Backend"],
            "is_default": True,
        },
        created_by="u",
    )
    # bump usage to ensure clone resets
    await repo.increment_usage(original)
    await repo.increment_usage(original)
    assert original.usage_count == 2

    cloned = await repo.clone(original, new_name="Tech Cópia", created_by="u2")

    assert cloned.id != original.id
    assert cloned.name == "Tech Cópia"
    assert cloned.company_id == COMPANY_A
    assert cloned.department_hint == ["Engineering"]
    assert cloned.seniority_hint == ["Sênior"]
    assert cloned.job_family_hint == ["Backend"]
    assert cloned.usage_count == 0, "clone MUST reset usage_count to 0"
    assert cloned.is_default is False, "clone MUST NOT inherit is_default"
    assert cloned.is_archived is False
    assert cloned.stages == original.stages


# ---------------------------------------------------------------------------
# 6. archive vs soft_delete são distintos
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_archive_sets_is_archived_keeps_is_active(db_session):
    """archive canonical: hide-from-selector mas mantém em analytics."""
    repo = PipelineTemplateRepository(db_session)
    t = await repo.create(COMPANY_A, {"name": "X", "stages": _stages()}, created_by="u")
    assert t.is_active is True and t.is_archived is False

    await repo.archive(t, updated_by="admin@x")

    assert t.is_archived is True
    assert t.is_active is True, "archive() MUST NOT touch is_active"
    assert t.updated_by == "admin@x"


@pytest.mark.asyncio
async def test_soft_delete_sets_inactive_keeps_archived_state(db_session):
    """soft_delete legacy: is_active=False; is_archived intacto."""
    repo = PipelineTemplateRepository(db_session)
    t = await repo.create(COMPANY_A, {"name": "X", "stages": _stages()}, created_by="u")

    await repo.soft_delete(t)
    assert t.is_active is False
    assert t.is_archived is False, "soft_delete MUST NOT touch is_archived"


# ---------------------------------------------------------------------------
# 7. list_for_company is_archived filter
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_for_company_default_excludes_archived(db_session):
    repo = PipelineTemplateRepository(db_session)
    active = await repo.create(COMPANY_A, {"name": "Active", "stages": _stages()}, created_by="u")
    archived = await repo.create(COMPANY_A, {"name": "Archived", "stages": _stages()}, created_by="u")
    await repo.archive(archived, updated_by="u")

    items, total = await repo.list_for_company(COMPANY_A)
    names = {t.name for t in items}
    assert total == 1
    assert names == {"Active"}, "default list MUST exclude archived"


@pytest.mark.asyncio
async def test_list_for_company_is_archived_none_includes_both(db_session):
    repo = PipelineTemplateRepository(db_session)
    active = await repo.create(COMPANY_A, {"name": "Active", "stages": _stages()}, created_by="u")
    archived = await repo.create(COMPANY_A, {"name": "Archived", "stages": _stages()}, created_by="u")
    await repo.archive(archived, updated_by="u")

    items, total = await repo.list_for_company(COMPANY_A, is_archived=None)
    names = {t.name for t in items}
    assert total == 2
    assert names == {"Active", "Archived"}, "is_archived=None MUST include both"
