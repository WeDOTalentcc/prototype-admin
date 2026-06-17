"""Integration test — cadeia de heranca departamento > empresa (FASE 1, slice 0-dept).

Decisao Paulo (audit 2026-06-06): o departamento vira um template com `defaults`
(JSONB). A criacao de vaga resolve cada campo descendo a cadeia
vaga > filial > DEPARTAMENTO > empresa > mercado. Aqui pinamos o elo
departamento > empresa: quando a vaga e de um departamento que tem um default
para o campo, esse default vence o valor company-wide; sem departamento (ou sem
default), cai pro valor da empresa.

Touches the real PostgreSQL container (DATABASE_URL).
"""
from __future__ import annotations

import os
import re
import uuid

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.domains.cv_screening.services.lia_field_config_service import (
    DataSource,
    LiaFieldConfigService,
)

pytestmark = pytest.mark.asyncio


def _async_db_url_and_args() -> tuple[str, dict]:
    url = os.environ.get("DATABASE_URL")
    if not url:
        pytest.skip("DATABASE_URL not set; integration test requires Postgres")
    sslmode_match = re.search(r"[?&]sslmode=([^&]+)", url)
    sslmode = sslmode_match.group(1) if sslmode_match else None
    for unsupported in ("sslmode", "channel_binding", "options"):
        url = re.sub(rf"[?&]{unsupported}=[^&]+", "", url)
    url = re.sub(r"\?&", "?", url).rstrip("?&")
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    connect_args: dict = {}
    if sslmode and sslmode.lower() in {"require", "verify-ca", "verify-full"}:
        connect_args["ssl"] = True
    return url, connect_args


@pytest.fixture
async def db() -> AsyncSession:
    url, connect_args = _async_db_url_and_args()
    engine = create_async_engine(url, future=True, connect_args=connect_args)
    Session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with Session() as session:
        yield session
    await engine.dispose()


DEPT_NAME = "Tecnologia SENTINEL"


@pytest.fixture
async def company_with_dept_defaults(db):
    company_id = str(uuid.uuid4())
    await db.execute(
        text(
            "INSERT INTO company_profiles (id, name, is_active, is_default) "
            "VALUES (:id, :name, TRUE, FALSE)"
        ),
        {"id": company_id, "name": f"DeptTest {company_id[:8]}"},
    )
    # company-level work_model vem do culture profile (FASE 0)
    await db.execute(
        text(
            "INSERT INTO company_culture_profiles "
            "(id, company_id, website_url, work_model) "
            "VALUES (:id, :cid, :url, :wm)"
        ),
        {
            "id": str(uuid.uuid4()), "cid": company_id,
            "url": "https://dept.example.com", "wm": "HYBRID-COMPANY",
        },
    )
    # department com default proprio de work_model (deve vencer o da empresa)
    await db.execute(
        text(
            "INSERT INTO departments (id, company_id, name, is_active, defaults) "
            "VALUES (:id, :cid, :name, TRUE, :defs)"
        ),
        {
            "id": str(uuid.uuid4()), "cid": company_id, "name": DEPT_NAME,
            "defs": '{"work_model": "REMOTE-ONLY-TECH"}',
        },
    )
    await db.commit()
    try:
        yield company_id
    finally:
        for tbl in ("departments", "company_culture_profiles"):
            await db.execute(
                text(f"DELETE FROM {tbl} WHERE company_id = :id"), {"id": company_id}
            )
        await db.execute(
            text("DELETE FROM company_profiles WHERE id = :id"), {"id": company_id}
        )
        await db.commit()


async def test_department_default_beats_company_value(db, company_with_dept_defaults):
    """Vaga do departamento Tecnologia: work_model resolve pro default do
    departamento (REMOTE-ONLY-TECH), com source DEPARTMENT_CONFIG."""
    svc = LiaFieldConfigService(db)
    result = await svc.get_field_config(
        company_with_dept_defaults, job_context={"department": DEPT_NAME}
    )
    ctx = result.field_contexts["work_model"]
    assert ctx.value == "REMOTE-ONLY-TECH", f"esperava default do depto, veio {ctx.value!r}"
    assert ctx.source == DataSource.DEPARTMENT_CONFIG, ctx.source


async def test_without_department_falls_back_to_company(db, company_with_dept_defaults):
    """Sem departamento no contexto, work_model cai pro valor company-wide."""
    svc = LiaFieldConfigService(db)
    result = await svc.get_field_config(company_with_dept_defaults)
    ctx = result.field_contexts["work_model"]
    assert ctx.value == "HYBRID-COMPANY", f"esperava valor da empresa, veio {ctx.value!r}"
    assert ctx.source == DataSource.COMPANY_CONFIG, ctx.source


async def test_unknown_department_falls_back_to_company(db, company_with_dept_defaults):
    """Departamento inexistente -> sem default -> valor da empresa."""
    svc = LiaFieldConfigService(db)
    result = await svc.get_field_config(
        company_with_dept_defaults, job_context={"department": "Departamento Que Nao Existe"}
    )
    ctx = result.field_contexts["work_model"]
    assert ctx.value == "HYBRID-COMPANY", ctx.value
    assert ctx.source == DataSource.COMPANY_CONFIG, ctx.source
