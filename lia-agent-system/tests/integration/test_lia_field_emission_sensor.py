"""Emission sensor (harness, audit 2026-06-06) — anti-ghost for the LIA field
config layer.

The existing sensor (tests/contract/test_lia_field_toggles_sync.py) only checks
that a field_key exists in BOTH the Python + TS universes and that *some* caller
references the canonical pathway. It does NOT prove the configured VALUE actually
reaches the prompt — which is exactly how the CompanyCultureProfile ghost (16
narrative fields silently dropped) survived for months: toggle ON, caller
present, value None.

This sensor closes that gap: it seeds an isolated company with a sentinel value
in EVERY company-side source (CompanyProfile columns + CompanyCultureProfile
narrative fields + departments/benefits) and asserts each WIRED field's value is
actually emitted by LiaFieldConfigService.get_field_config into the context that
build_company_agent_context feeds to every agent.

Fields with NO company-side source (resolved only via fallback / market /
job-history, or genuinely source-less) are intentionally excluded and listed in
NO_DIRECT_SOURCE so the omission is explicit, not silent.

Touches the real PostgreSQL container (DATABASE_URL). Mirrors
tests/integration/test_lia_field_config_relationships.py.
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


# field_key -> sentinel substring that MUST appear in the emitted context_prompt.
# Covers CompanyProfile columns + CompanyCultureProfile narrative fields +
# relationships. Every entry here is a WIRED field with a real company source.
EXPECTED_EMISSION = {
    # CompanyProfile direct column (trade_name maps to trading_name — bug fix)
    "trade_name": "SENTINELTRADE",
    # CompanyCultureProfile — Text fields
    "mission": "SENTINELMISSION",
    "vision": "SENTINELVISION",
    "work_model": "SENTINELWORKMODEL",
    "growth_opportunities": "SENTINELGROWTH",
    "team_dynamics": "SENTINELTEAM",
    "leadership_style": "SENTINELLEAD",
    "dei_initiatives": "SENTINELDEI",
    "sustainability": "SENTINELSUST",
    "social_impact": "SENTINELSOCIAL",
    "engineering_culture": "SENTINELENGCULT",
    # CompanyCultureProfile — ARRAY fields
    "values": "SENTINELVALUE",
    "evp_bullets": "SENTINELEVP",
    "core_competencies": "SENTINELCORECOMP",
    "behavioral_competencies": "SENTINELCORECOMP",  # shares core_competencies col
    "locations": "SENTINELLOC",
    "tech_stack": "SENTINELTECH",
    "default_languages": "SENTINELLANG",
    # relationships
    "departments": "SENTINELDEPT",
    "benefits": "SENTINELBENEFIT",
    # big_five (only emits when culture is_approved=True)
    "company_big_five": "77",
}

# Documented exclusions: fields with no direct company source. Resolved via
# fallback (job_history/market) or genuinely source-less today. Listing them
# here keeps the omission explicit (harness: no silent caps).
NO_DIRECT_SOURCE = {
    "seniority_levels", "employment_types", "salary_ranges",  # fallback/bands
    "pipeline", "eligibility_questions", "headcount_planning",  # no source yet
    "hybrid_days_onsite",  # no source column yet (FASE 1, with work_model)
    "industry", "website", "linkedin_url", "company_size",  # CompanyProfile cols
    "employee_count", "founded_year",  # (not seeded here; covered by other tests)
}


@pytest.fixture
async def fully_seeded_company(db):
    company_id = str(uuid.uuid4())
    await db.execute(
        text(
            "INSERT INTO company_profiles (id, name, is_active, is_default, trading_name) "
            "VALUES (:id, :name, TRUE, FALSE, :tn)"
        ),
        {"id": company_id, "name": f"EmitTest {company_id[:8]}", "tn": "SENTINELTRADE Ltda"},
    )
    await db.execute(
        text(
            "INSERT INTO company_culture_profiles "
            "(id, company_id, website_url, is_approved, "
            " mission, vision, work_model, growth_opportunities, team_dynamics, "
            " leadership_style, dei_initiatives, sustainability, social_impact, "
            " engineering_culture, values, evp_bullets, core_competencies, "
            " locations, tech_stack, default_languages, "
            " openness_score, conscientiousness_score, extraversion_score, "
            " agreeableness_score, stability_score) "
            "VALUES (:id, :cid, :url, TRUE, "
            " :mission, :vision, :wm, :growth, :team, "
            " :lead, :dei, :sust, :social, "
            " :eng, ARRAY['SENTINELVALUE'], ARRAY['SENTINELEVP'], ARRAY['SENTINELCORECOMP'], "
            " ARRAY['SENTINELLOC'], ARRAY['SENTINELTECH'], ARRAY['SENTINELLANG'], "
            " 77, 60, 55, 50, 65)"
        ),
        {
            "id": str(uuid.uuid4()), "cid": company_id,
            "url": "https://emit.example.com",
            "mission": "SENTINELMISSION", "vision": "SENTINELVISION",
            "wm": "SENTINELWORKMODEL", "growth": "SENTINELGROWTH",
            "team": "SENTINELTEAM", "lead": "SENTINELLEAD", "dei": "SENTINELDEI",
            "sust": "SENTINELSUST", "social": "SENTINELSOCIAL", "eng": "SENTINELENGCULT",
        },
    )
    await db.execute(
        text(
            "INSERT INTO departments (id, company_id, name, is_active) "
            "VALUES (:id, :cid, :name, TRUE)"
        ),
        {"id": str(uuid.uuid4()), "cid": company_id, "name": "SENTINELDEPT"},
    )
    await db.execute(
        text(
            "INSERT INTO benefits (id, company_id, name, category, is_active) "
            "VALUES (:id, :cid, :name, :cat, TRUE)"
        ),
        {"id": str(uuid.uuid4()), "cid": company_id, "name": "SENTINELBENEFIT", "cat": "outros"},
    )
    await db.commit()
    try:
        yield company_id
    finally:
        for tbl in ("benefits", "departments", "company_culture_profiles"):
            await db.execute(
                text(f"DELETE FROM {tbl} WHERE company_id = :id"), {"id": company_id}
            )
        await db.execute(
            text("DELETE FROM company_profiles WHERE id = :id"), {"id": company_id}
        )
        await db.commit()


async def test_every_wired_field_emits_its_value(db, fully_seeded_company):
    """For each WIRED field, the seeded sentinel value must reach the emitted
    context. A regression that drops a field (the ghost class) fails here."""
    context = await build_company_agent_context(fully_seeded_company, db)
    assert context, "context empty — silent degradation"

    missing = [
        f"{fk} (expected '{sentinel}')"
        for fk, sentinel in EXPECTED_EMISSION.items()
        if sentinel not in context
    ]
    assert not missing, (
        "WIRED fields not emitted into the agent context (ghost regression):\n  "
        + "\n  ".join(missing)
        + f"\n--- context ---\n{context}"
    )


async def test_field_contexts_carry_resolved_values(db, fully_seeded_company):
    """Belt-and-suspenders: the structured field_contexts must carry a non-None
    value for each WIRED field (not just the rendered string)."""
    svc = LiaFieldConfigService(db)
    result = await svc.get_field_config(fully_seeded_company)
    none_valued = [
        fk for fk in EXPECTED_EMISSION
        if result.field_contexts.get(fk) is None
        or result.field_contexts[fk].value is None
    ]
    assert not none_valued, f"WIRED fields with None value: {sorted(none_valued)}"
