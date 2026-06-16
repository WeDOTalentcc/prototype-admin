"""275 — Seed Talent Intelligence template no Agent Studio.

Revision ID: 275_seed_ti_agent_studio
Revises: 274_seed_ii_agent_studio
Create Date: 2026-06-13

Wiring: segundo dominio "Agent Studio em Desenvolvimento" conectado ao factory.
15 tools (skills ontology, interview intelligence, nurture, workforce, market).
"""
from __future__ import annotations

import uuid

import sqlalchemy as sa
from alembic import op

revision = "275_seed_ti_agent_studio"
down_revision = "274_seed_ii_agent_studio"
branch_labels = None
depends_on = None

TEMPLATE_ID = str(uuid.uuid5(uuid.NAMESPACE_DNS, "wedotalent.talent_intelligence.v1"))
LISTING_ID = str(uuid.uuid4())

ALLOWED_TOOLS = [
    "infer_related_skills",
    "get_skill_adjacencies",
    "analyze_skill_gaps",
    "map_candidate_skills_to_ontology",
    "match_internal_candidates",
    "forecast_hiring_needs",
    "analyze_interview_recording",
    "detect_interview_bias",
    "generate_interview_opinion",
    "generate_candidate_feedback",
    "compare_interview_performance",
    "create_nurture_sequence",
    "get_engagement_metrics",
    "suggest_reengagement",
    "get_market_intelligence",
]

SYSTEM_PROMPT = (
    "Voce e um agente de inteligencia de talentos. Suas capacidades incluem: "
    "1) Ontologia de skills — inferir skills relacionadas, analisar gaps entre candidato e vaga, "
    "mapear skills brutas para nos canonicos. "
    "2) Mobilidade interna — encontrar candidatos internos para novas posicoes. "
    "3) Inteligencia de entrevistas — analise WSI completa, deteccao de vies, "
    "comparativo entre candidatos, parecer estrategico e feedback. "
    "4) Nurture — criar sequencias de engajamento para candidatos passivos, "
    "metricas de engajamento e sugestoes de reengajamento. "
    "5) Inteligencia de mercado — benchmarks salariais, tendencias e skills em alta. "
    "6) Workforce planning — previsao de necessidades de contratacao. "
    "Sempre respeite LGPD: nunca use raca, religiao, genero, etnia, estado civil ou saude "
    "em decisoes de scoring/ranking. "
    "Responda sempre em portugues do Brasil de forma profissional e direta."
)


def upgrade() -> None:
    conn = op.get_bind()
    meta = sa.MetaData()

    # Category "talent_intelligence" (idempotent)
    categories = sa.Table("agent_categories", meta, autoload_with=conn)
    exists = conn.execute(
        sa.select(categories.c.id).where(categories.c.id == "talent_intelligence")
    ).first()
    if not exists:
        conn.execute(categories.insert().values(
            id="talent_intelligence",
            label_pt="Inteligencia de Talentos",
            label_en="Talent Intelligence",
            icon="Brain",
            sort_order=8,
            is_active=True,
        ))

    # Template catalog entry (idempotent by slug)
    catalog = sa.Table("agent_template_catalog", meta, autoload_with=conn)
    slug = "tpl-talent-intelligence"
    exists_tpl = conn.execute(
        sa.select(catalog.c.id).where(catalog.c.slug == slug)
    ).first()
    if not exists_tpl:
        conn.execute(catalog.insert().values(
            id=TEMPLATE_ID,
            slug=slug,
            name="Especialista em Talentos",
            description=(
                "Agente completo de inteligencia de talentos: ontologia de skills, "
                "mobilidade interna, analise de entrevistas, nurture de candidatos, "
                "inteligencia de mercado e workforce planning."
            ),
            category_id="talent_intelligence",
            sector_id=None,
            system_prompt=SYSTEM_PROMPT,
            allowed_tools=ALLOWED_TOOLS,
            context_level="full",
            max_steps=12,
            temperature=0.4,
            enable_memory=True,
            excluded_tools=[],
            tags=[
                "skills", "ontologia", "mobilidade", "entrevista", "nurture",
                "mercado", "workforce", "talent_intelligence",
            ],
            icon="Brain",
            accent_color="graphite",
            sort_order=0,
            is_active=True,
            company_id=None,
        ))

    # Marketplace listing (idempotent by template_id)
    listings = sa.Table("agent_marketplace_listings", meta, autoload_with=conn)
    exists_listing = conn.execute(
        sa.select(listings.c.id).where(listings.c.template_id == TEMPLATE_ID)
    ).first()
    if not exists_listing:
        conn.execute(listings.insert().values(
            id=LISTING_ID,
            agent_id=None,
            template_id=TEMPLATE_ID,
            module_required="talent_intelligence",
            listing_type="template",
            publisher_company_id="wedotalent",
            title="Especialista em Talentos",
            short_description=(
                "Ontologia de skills + mobilidade interna + analise de entrevistas "
                "+ nurture + inteligencia de mercado + workforce planning"
            ),
            long_description=(
                "Agente premium de inteligencia de talentos com 15 ferramentas. "
                "Mapeia skills para ontologia canonica, encontra candidatos internos "
                "para mobilidade, analisa entrevistas com WSI (Bloom, Dreyfus, CBI, Big Five), "
                "detecta vieses inconscientes, cria sequencias de nurture para candidatos passivos, "
                "monitora metricas de engajamento, preve necessidades de contratacao "
                "e fornece inteligencia de mercado em tempo real."
            ),
            category="talent_intelligence",
            tags=["skills", "ontologia", "mobilidade", "entrevista", "nurture", "mercado"],
            icon_url=None,
            status="approved",
            credits_per_execution=3,
            is_free=False,
            install_count=0,
            avg_rating=0.0,
            total_ratings=0,
        ))


def downgrade() -> None:
    conn = op.get_bind()
    meta = sa.MetaData()

    listings = sa.Table("agent_marketplace_listings", meta, autoload_with=conn)
    conn.execute(listings.delete().where(listings.c.template_id == TEMPLATE_ID))

    catalog = sa.Table("agent_template_catalog", meta, autoload_with=conn)
    conn.execute(catalog.delete().where(catalog.c.slug == "tpl-talent-intelligence"))

    categories = sa.Table("agent_categories", meta, autoload_with=conn)
    conn.execute(categories.delete().where(categories.c.id == "talent_intelligence"))
