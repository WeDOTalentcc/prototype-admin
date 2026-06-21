"""276 — Seed Workforce Planning template no Agent Studio.

Revision ID: 276_seed_wf_agent_studio
Revises: 275_seed_ti_agent_studio
Create Date: 2026-06-13

Wiring: terceiro dominio "Agent Studio em Desenvolvimento" conectado ao factory.
1 tool (get_workforce_plan_summary).
"""
from __future__ import annotations

import uuid

import sqlalchemy as sa
from alembic import op

revision = "276_seed_wf_agent_studio"
down_revision = "275_add_tier_policies"
branch_labels = None
depends_on = None

TEMPLATE_ID = str(uuid.uuid5(uuid.NAMESPACE_DNS, "wedotalent.workforce.v1"))
LISTING_ID = str(uuid.uuid4())

ALLOWED_TOOLS = ["get_workforce_plan_summary"]

SYSTEM_PROMPT = (
    "Voce e um agente de planejamento de workforce. "
    "Consulte o plano de headcount da empresa para responder sobre: "
    "quantas vagas estao planejadas por departamento, quantas ja foram abertas, "
    "e quantas faltam abrir. Compare planejado vs realizado e identifique gaps. "
    "Quando os dados de vagas abertas nao estiverem disponiveis, informe honestamente "
    "em vez de fabricar numeros. "
    "Responda sempre em portugues do Brasil de forma profissional e direta."
)


def upgrade() -> None:
    conn = op.get_bind()
    meta = sa.MetaData()

    # Category "workforce" (idempotent)
    categories = sa.Table("agent_categories", meta, autoload_with=conn)
    exists = conn.execute(
        sa.select(categories.c.id).where(categories.c.id == "workforce")
    ).first()
    if not exists:
        conn.execute(categories.insert().values(
            id="workforce",
            label_pt="Workforce Planning",
            label_en="Workforce Planning",
            icon="Users",
            sort_order=9,
            is_active=True,
        ))

    # Template catalog entry (idempotent by slug)
    catalog = sa.Table("agent_template_catalog", meta, autoload_with=conn)
    slug = "tpl-workforce-planning"
    exists_tpl = conn.execute(
        sa.select(catalog.c.id).where(catalog.c.slug == slug)
    ).first()
    if not exists_tpl:
        conn.execute(catalog.insert().values(
            id=TEMPLATE_ID,
            slug=slug,
            name="Planejador de Workforce",
            description=(
                "Consulta plano de headcount por departamento, compara planejado "
                "vs vagas abertas e identifica gaps de contratacao."
            ),
            category_id="workforce",
            sector_id=None,
            system_prompt=SYSTEM_PROMPT,
            allowed_tools=ALLOWED_TOOLS,
            context_level="standard",
            max_steps=6,
            temperature=0.3,
            enable_memory=True,
            excluded_tools=[],
            tags=["workforce", "headcount", "planejamento", "gap"],
            icon="Users",
            accent_color="slate",
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
            module_required="workforce",
            listing_type="template",
            publisher_company_id="wedotalent",
            title="Planejador de Workforce",
            short_description="Headcount planejado vs realizado por departamento",
            long_description=(
                "Agente de planejamento de workforce. Consulta o plano de headcount "
                "cadastrado pela empresa, cruza com vagas abertas no momento e "
                "identifica gaps por departamento. Responde perguntas como "
                "'quantas vagas faltam abrir em Engenharia?' com dados reais."
            ),
            category="workforce",
            tags=["workforce", "headcount", "planejamento"],
            icon_url=None,
            status="approved",
            credits_per_execution=1,
            is_free=True,
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
    conn.execute(catalog.delete().where(catalog.c.slug == "tpl-workforce-planning"))

    categories = sa.Table("agent_categories", meta, autoload_with=conn)
    conn.execute(categories.delete().where(categories.c.id == "workforce"))
