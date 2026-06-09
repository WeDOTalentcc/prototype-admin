"""Seed script: insert AgentMarketplaceListing records for first-party agents
and the 15 global templates in agent_template_catalog.

Idempotent:
- First-party agents: INSERT ... ON CONFLICT (agent_id) DO NOTHING
- Templates: INSERT ... ON CONFLICT (template_id) DO NOTHING
  (agent_id is NULL for templates; need a separate unique constraint path)

Run via: python3 scripts/seed_marketplace_listings.py
"""
from __future__ import annotations

import asyncio
import uuid

from sqlalchemy import select, text
from sqlalchemy.dialects.postgresql import insert as pg_insert

from lia_config.database import AsyncSessionLocal
from lia_models.billing import AVAILABLE_MODULES, CompanyModule
from lia_models.custom_agent import (
    AgentMarketplaceListing,
    ListingType,
    MarketplaceListingStatus,
)
from lia_models.agent_template_catalog import AgentTemplateCatalog

# ── First-party agent UUIDs ─────────────────────────────────────────────────
TALENT_INTEL_AGENT_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")
INTERVIEW_ANALYSIS_AGENT_ID = uuid.UUID("00000000-0000-0000-0000-000000000002")

# WeDo platform publisher company ID (sentinel for first-party / global content)
WEDO_PUBLISHER_COMPANY_ID = "wedo-platform"

# ── Template slugs — keep in sync with migration 199 ────────────────────────
TEMPLATE_SLUGS = [
    "tpl-triagem-tech",
    "tpl-triagem-volume",
    "tpl-screening-cultural",
    "tpl-sourcing-passivo",
    "tpl-sourcing-diversidade",
    "tpl-agendamento",
    "tpl-followup",
    "tpl-analise-pipeline",
    "tpl-comparacao",
    "tpl-assistente-vaga",
    "tpl-onboarding-prep",
    "tpl-salary-benchmark",
    "tpl-feedback-collector",
    "tpl-talent-pool-curator",
    "tpl-compliance-check",
]


async def seed_marketplace_listings() -> None:
    async with AsyncSessionLocal() as db:
        # ── Step 1: First-party agent listings ──────────────────────────────
        first_party_listings = [
            {
                "agent_id": TALENT_INTEL_AGENT_ID,
                "template_id": None,
                "publisher_company_id": WEDO_PUBLISHER_COMPANY_ID,
                "title": "Talent Intelligence Pro",
                "short_description": (
                    "Skills Ontology, Gap Analysis e Market Intelligence. "
                    "Automatize a identificação de talentos e preveja necessidades de contratação."
                ),
                "long_description": (
                    "O agente Talent Intelligence Pro combina análise de habilidades, "
                    "ontologia de competências e inteligência de mercado para apoiar decisões "
                    "estratégicas de talent acquisition. Suporta 15 ferramentas especializadas "
                    "incluindo gap analysis, matching interno, nurture e previsão de contratação."
                ),
                "category": "talent_intelligence",
                "tags": ["skills", "ontology", "market_intelligence", "gap_analysis", "nurture"],
                "is_free": False,
                "credits_per_execution": 10,
                "module_required": "talent_intelligence_pro",
                "listing_type": ListingType.agent.value,
                "status": MarketplaceListingStatus.APPROVED.value,
                "published_at": text("NOW()"),
            },
            {
                "agent_id": INTERVIEW_ANALYSIS_AGENT_ID,
                "template_id": None,
                "publisher_company_id": WEDO_PUBLISHER_COMPANY_ID,
                "title": "Interview Intelligence Pro",
                "short_description": (
                    "Análise WSI de entrevistas, detecção de viés e parecer estratégico. "
                    "Eleve a qualidade das decisões de contratação."
                ),
                "long_description": (
                    "O agente Interview Intelligence Pro analisa gravações de entrevistas, "
                    "detecta vieses inconscientes, compara candidatos e gera pareceres estratégicos "
                    "baseados em evidências. Suporta 5 ferramentas especializadas de análise "
                    "e feedback estruturado."
                ),
                "category": "interview_intelligence",
                "tags": ["interview", "bias_detection", "feedback", "wsi", "analysis"],
                "is_free": False,
                "credits_per_execution": 5,
                "module_required": "interview_intelligence",
                "listing_type": ListingType.agent.value,
                "status": MarketplaceListingStatus.APPROVED.value,
                "published_at": text("NOW()"),
            },
        ]

        agents_seeded = 0
        for listing_data in first_party_listings:
            # Check if already exists by agent_id
            existing = await db.execute(
                select(AgentMarketplaceListing).where(
                    AgentMarketplaceListing.agent_id == listing_data["agent_id"]
                )
            )
            if existing.scalar_one_or_none():
                print(f"  [skip] Listing for agent {listing_data['agent_id']} already exists")
                continue

            # published_at uses text("NOW()") — needs special handling
            row = AgentMarketplaceListing(
                agent_id=listing_data["agent_id"],
                template_id=listing_data["template_id"],
                publisher_company_id=listing_data["publisher_company_id"],
                title=listing_data["title"],
                short_description=listing_data["short_description"],
                long_description=listing_data["long_description"],
                category=listing_data["category"],
                tags=listing_data["tags"],
                is_free=listing_data["is_free"],
                credits_per_execution=listing_data["credits_per_execution"],
                module_required=listing_data["module_required"],
                listing_type=listing_data["listing_type"],
                status=listing_data["status"],
            )
            db.add(row)
            agents_seeded += 1
            print(f"  [add] Listing for {listing_data['title']}")

        # ── Step 2: Template listings ────────────────────────────────────────
        # Load template IDs from DB by slug
        tpl_result = await db.execute(
            select(AgentTemplateCatalog.id, AgentTemplateCatalog.slug, AgentTemplateCatalog.name).where(
                AgentTemplateCatalog.slug.in_(TEMPLATE_SLUGS)
            )
        )
        templates_in_db = {row.slug: (row.id, row.name) for row in tpl_result}

        templates_seeded = 0
        for slug in TEMPLATE_SLUGS:
            if slug not in templates_in_db:
                print(f"  [warn] Template slug '{slug}' not found in DB — skipping")
                continue

            tpl_id, tpl_name = templates_in_db[slug]

            # Idempotency: check by template_id
            existing = await db.execute(
                select(AgentMarketplaceListing).where(
                    AgentMarketplaceListing.template_id == tpl_id
                )
            )
            if existing.scalar_one_or_none():
                print(f"  [skip] Listing for template {slug} already exists")
                continue

            row = AgentMarketplaceListing(
                agent_id=None,
                template_id=tpl_id,
                publisher_company_id=WEDO_PUBLISHER_COMPANY_ID,
                title=tpl_name,
                short_description=f"Template pré-configurado: {tpl_name}",
                category="template",
                tags=[slug.replace("tpl-", ""), "template"],
                is_free=True,
                credits_per_execution=0,
                module_required=None,
                listing_type=ListingType.template.value,
                status=MarketplaceListingStatus.APPROVED.value,
            )
            db.add(row)
            templates_seeded += 1
            print(f"  [add] Template listing for {slug} ({tpl_name})")

        await db.commit()
        print(
            f"\n[seed_marketplace_listings] Done. "
            f"Agents: {agents_seeded} added, Templates: {templates_seeded} added."
        )


if __name__ == "__main__":
    asyncio.run(seed_marketplace_listings())
