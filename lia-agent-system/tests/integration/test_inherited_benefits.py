"""Integration test — resolve_inherited_benefits (FASE 1).

Vaga SEM beneficios herda os beneficios da empresa casados por
nivel+departamento+contrato + os obrigatorios (is_mandatory). Recebe `db` como
param (estavel, sem AsyncSessionLocal/loop flake). Touches real Postgres.
"""
from __future__ import annotations

import os
import re
import uuid
from types import SimpleNamespace

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.api.v1.job_vacancies._shared import resolve_inherited_benefits

pytestmark = pytest.mark.asyncio


def _url():
    url = os.environ.get("DATABASE_URL")
    if not url:
        pytest.skip("DATABASE_URL not set")
    for u in ("sslmode", "channel_binding", "options"):
        url = re.sub(rf"[?&]{u}=[^&]+", "", url)
    url = re.sub(r"\?&", "?", url).rstrip("?&")
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url


@pytest.fixture
async def db() -> AsyncSession:
    engine = create_async_engine(_url(), future=True)
    Session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with Session() as s:
        yield s
    await engine.dispose()


@pytest.fixture
async def company_with_benefits(db):
    cid = str(uuid.uuid4())

    def _ins(name, sen, con, mand):
        return (
            "INSERT INTO company_benefits "
            "(id, company_id, name, category, seniority_levels, contract_types, "
            " is_mandatory, is_active) "
            f"VALUES (:id, :cid, :name, 'food', {sen}, {con}, {mand}, TRUE)"
        )

    await db.execute(text(_ins("a", "ARRAY['senior']", "ARRAY['clt']", "FALSE")),
                     {"id": str(uuid.uuid4()), "cid": cid, "name": "SENTA matching"})
    await db.execute(text(_ins("b", "ARRAY[]::varchar[]", "ARRAY[]::varchar[]", "TRUE")),
                     {"id": str(uuid.uuid4()), "cid": cid, "name": "SENTB mandatory"})
    await db.execute(text(_ins("c", "ARRAY['junior']", "ARRAY[]::varchar[]", "FALSE")),
                     {"id": str(uuid.uuid4()), "cid": cid, "name": "SENTC junior"})
    await db.commit()
    try:
        yield cid
    finally:
        await db.execute(text("DELETE FROM company_benefits WHERE company_id=:c"), {"c": cid})
        await db.commit()


async def test_vaga_inherits_matching_and_mandatory(db, company_with_benefits):
    vaga = SimpleNamespace(
        benefits=[], seniority_level="senior", department="Tech", employment_type="clt"
    )
    await resolve_inherited_benefits(db, company_with_benefits, [vaga])
    names = {b["name"] for b in vaga.benefits}
    assert "SENTA matching" in names, f"benefit casado (senior/clt) deveria herdar: {names}"
    assert "SENTB mandatory" in names, f"benefit obrigatorio deveria herdar: {names}"
    assert "SENTC junior" not in names, f"benefit nao-casado (junior) NAO deveria herdar: {names}"
    assert all(b.get("inherited") for b in vaga.benefits)


async def test_vaga_with_explicit_benefits_is_untouched(db, company_with_benefits):
    vaga = SimpleNamespace(
        benefits=[{"name": "Escolhido pelo recrutador"}],
        seniority_level="senior", department="Tech", employment_type="clt",
    )
    await resolve_inherited_benefits(db, company_with_benefits, [vaga])
    assert vaga.benefits == [{"name": "Escolhido pelo recrutador"}]


async def test_fail_open_unknown_company(db):
    vaga = SimpleNamespace(benefits=[], seniority_level="senior", department=None, employment_type="clt")
    await resolve_inherited_benefits(db, "unknown", [vaga])
    assert vaga.benefits == []
