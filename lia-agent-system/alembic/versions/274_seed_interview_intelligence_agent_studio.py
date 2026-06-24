"""274 — Seed Interview Intelligence template no Agent Studio.

Revision ID: 274_seed_ii_agent_studio
Revises: 273_create_role_scope_filters
Create Date: 2026-06-13

Wiring pilot: primeiro domínio "Agent Studio em Desenvolvimento" conectado
ao factory CustomAgentRuntime. Adiciona:
1. Categoria "interview_intelligence" em agent_categories (se não existir)
2. Template no agent_template_catalog com 5 allowed_tools
3. Marketplace listing para o template
"""
from __future__ import annotations

import uuid

import sqlalchemy as sa
from alembic import op

revision = "274_seed_ii_agent_studio"
down_revision = "273_create_role_scope_filters"
branch_labels = None
depends_on = None

CATEGORY_ID = "interview_intelligence"
TEMPLATE_ID = str(uuid.uuid5(uuid.NAMESPACE_DNS, "wedotalent.interview_intelligence.v1"))
LISTING_ID = str(uuid.uuid4())

ALLOWED_TOOLS = [
    "analyze_interview_recording",
    "detect_interview_bias",
    "compare_interview_performance",
    "generate_interview_opinion",
    "generate_candidate_feedback",
]

SYSTEM_PROMPT = (
    "Voce e um agente especialista em inteligencia de entrevistas. "
    "Analise transcricoes de entrevistas usando o framework WSI (Bloom, Dreyfus, CBI, Big Five). "
    "Detecte vieses (idade, genero, aparencia, afinidade, confirmacao, perguntas ilegais) e "
    "gere pareceres estrategicos de contratacao com evidencias. "
    "Compare performance entre candidatos da mesma vaga usando cohorts (peers, hired top, triaged high). "
    "Gere feedback construtivo e estruturado para devolver ao candidato. "
    "Sempre respeite LGPD: nunca use raca, religiao, genero, etnia, estado civil ou saude "
    "em decisoes de scoring/ranking. "
    "Responda sempre em portugues do Brasil de forma profissional e direta."
)


def upgrade() -> None:
    conn = op.get_bind()
    meta = sa.MetaData()

    # 1. Category (idempotent)
    categories = sa.Table("agent_categories", meta, autoload_with=conn)
    exists = conn.execute(
        sa.select(categories.c.id).where(categories.c.id == CATEGORY_ID)
    ).first()
    if not exists:
        conn.execute(categories.insert().values(
            id=CATEGORY_ID,
            label_pt="Inteligência de Entrevistas",
            label_en="Interview Intelligence",
            icon="Mic",
            sort_order=7,
            is_active=True,
        ))

    # 2. Template catalog entry (idempotent by slug)
    catalog = sa.Table("agent_template_catalog", meta, autoload_with=conn)
    slug = "tpl-interview-intelligence"
    exists_tpl = conn.execute(
        sa.select(catalog.c.id).where(catalog.c.slug == slug)
    ).first()
    if not exists_tpl:
        conn.execute(catalog.insert().values(
            id=TEMPLATE_ID,
            slug=slug,
            name="Analista de Entrevistas",
            description=(
                "Analisa transcricoes de entrevistas com WSI, detecta vieses, "
                "compara candidatos e gera pareceres estrategicos de contratacao."
            ),
            category_id=CATEGORY_ID,
            sector_id=None,
            system_prompt=SYSTEM_PROMPT,
            allowed_tools=ALLOWED_TOOLS,
            context_level="full",
            max_steps=10,
            temperature=0.4,
            enable_memory=True,
            excluded_tools=[],
            tags=["entrevista", "wsi", "bias", "parecer", "feedback", "interview_intelligence"],
            icon="Mic",
            accent_color="graphite",
            sort_order=0,
            is_active=True,
            company_id=None,
        ))

    # 3. Marketplace listing (idempotent by template_id)
    listings = sa.Table("agent_marketplace_listings", meta, autoload_with=conn)
    exists_listing = conn.execute(
        sa.select(listings.c.id).where(listings.c.template_id == TEMPLATE_ID)
    ).first()
    if not exists_listing:
        conn.execute(listings.insert().values(
            id=LISTING_ID,
            agent_id=None,
            template_id=TEMPLATE_ID,
            module_required="interview_intelligence",
            listing_type="template",
            publisher_company_id="wedotalent",
            title="Analista de Entrevistas",
            short_description="WSI + bias + comparativo + parecer + feedback para entrevistas",
            long_description=(
                "Agente especializado em analisar transcricoes de entrevistas de emprego. "
                "Usa o framework WSI (Bloom, Dreyfus, CBI, Big Five) para scoring profundo, "
                "detecta vieses inconscientes, compara performance entre candidatos da mesma vaga, "
                "gera parecer estrategico (CONTRATAR/NAO CONTRATAR/AVALIAR MAIS) com evidencias, "
                "e cria feedback construtivo para devolver ao candidato."
            ),
            category="interview_intelligence",
            tags=["entrevista", "wsi", "bias", "parecer", "feedback"],
            icon_url=None,
            status="approved",
            credits_per_execution=2,
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
    conn.execute(catalog.delete().where(catalog.c.slug == "tpl-interview-intelligence"))

    categories = sa.Table("agent_categories", meta, autoload_with=conn)
    conn.execute(categories.delete().where(categories.c.id == CATEGORY_ID))
