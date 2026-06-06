"""Integration test pinning the CompanyCultureProfile silent-ghost bug (FASE 0).

Context (audit 2026-06-06): the 16 narrative company fields configured in
Configurações → Minha Empresa (mission, vision, values, tech_stack,
engineering_culture, leadership_style, team_dynamics, growth_opportunities,
dei_initiatives, sustainability, social_impact, evp_bullets, core_competencies,
default_languages, locations, company_big_five) live on
``CompanyCultureProfile`` — a table with NO ORM relationship from
``CompanyProfile``. ``LiaFieldConfigRepository.get_company_profile`` only
selectinload-s departments/benefits/culture_values/compensation_policies and
NEVER loads ``CompanyCultureProfile``. So ``_get_company_value('mission', ...)``
does ``hasattr(CompanyProfile, 'mission')`` -> False -> returns None -> the
field is dropped from the context. Result: the recruiter flips the toggle ON,
but the value NEVER reaches any agent prompt (true ghost).

These tests touch the real PostgreSQL container (DATABASE_URL) and seed an
isolated CompanyProfile + CompanyCultureProfile. RED state: the culture values
do not surface in get_field_config / build_company_agent_context. GREEN: the
repository loads the culture profile and _get_company_value reads from it.

Mirrors tests/integration/test_lia_field_config_relationships.py.
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
    LiaFieldConfigService,
)
from app.shared.services.lia_agent_context_builder import build_company_agent_context

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


# Sentinel values unlikely to collide with seed data.
MISSION_TXT = "Democratizar contratacoes justas com IA SENTINEL-MISSION"
VISION_TXT = "Ser a plataforma de recrutamento mais confiavel SENTINEL-VISION"


@pytest.fixture
async def company_with_culture(db):
    """Seed an isolated CompanyProfile + CompanyCultureProfile.

    Yields the company_id (uuid str). Cleans up afterwards.
    """
    company_id = str(uuid.uuid4())
    await db.execute(
        text(
            "INSERT INTO company_profiles (id, name, is_active, is_default) "
            "VALUES (:id, :name, TRUE, FALSE)"
        ),
        {"id": company_id, "name": f"CultureTest {company_id[:8]}"},
    )
    await db.execute(
        text(
            "INSERT INTO company_culture_profiles "
            "(id, company_id, website_url, mission, vision, values, tech_stack) "
            "VALUES (:id, :cid, :url, :mission, :vision, "
            "ARRAY['Inovacao','Transparencia'], ARRAY['Python','Go']) "
        ),
        {
            "id": str(uuid.uuid4()),
            "cid": company_id,
            "url": "https://sentinel.example.com",
            "mission": MISSION_TXT,
            "vision": VISION_TXT,
        },
    )
    await db.commit()
    try:
        yield company_id
    finally:
        await db.execute(
            text("DELETE FROM company_culture_profiles WHERE company_id = :id"),
            {"id": company_id},
        )
        await db.execute(
            text("DELETE FROM company_profiles WHERE id = :id"), {"id": company_id}
        )
        await db.commit()


async def test_get_field_config_surfaces_culture_mission_and_vision(
    db, company_with_culture
):
    """RED: mission/vision live on CompanyCultureProfile which the repository
    never loads, so they are dropped. GREEN: they are classified as
    COMPANY_CONFIG (toggle ON by default) with the seeded value present.
    """
    svc = LiaFieldConfigService(db)
    result = await svc.get_field_config(company_with_culture)

    assert "mission" in result.active_fields, (
        "mission not surfaced from CompanyCultureProfile "
        f"(active_fields={sorted(result.active_fields)})"
    )
    assert "vision" in result.active_fields, "vision not surfaced from culture profile"


async def test_build_company_agent_context_includes_culture_values(
    db, company_with_culture
):
    """End-to-end: the canonical context fed to every agent must contain the
    recruiter-configured mission/vision/values text (toggle ON by default).
    RED state omits them entirely (true ghost)."""
    context = await build_company_agent_context(company_with_culture, db)
    assert context, "build_company_agent_context returned empty"
    assert "SENTINEL-MISSION" in context, "mission text did not reach the prompt"
    assert "SENTINEL-VISION" in context, "vision text did not reach the prompt"
