"""277 — Seed Voice Screening template no Agent Studio.

Revision ID: 277_seed_voice_agent_studio
Revises: 276_seed_wf_agent_studio
Create Date: 2026-06-13

Voice domain usa pattern diferente dos outros 3: nao e um domain de tools,
e um CANAL (StudioVoicePlugin + agent_studio_voice.py endpoints). Qualquer
custom agent pode ser voice-enabled via CustomAgent.voice_enabled=True.

Este seed cria um template pre-pronto de "Triagem por Voz" no catalogo do
marketplace, com voice_enabled configurado e tools de screening.
"""
from __future__ import annotations

import uuid

import sqlalchemy as sa
from alembic import op

revision = "277_seed_voice_agent_studio"
down_revision = "276_seed_wf_agent_studio"
branch_labels = None
depends_on = None

TEMPLATE_ID = str(uuid.uuid5(uuid.NAMESPACE_DNS, "wedotalent.voice_screening.v1"))
LISTING_ID = str(uuid.uuid4())

ALLOWED_TOOLS = [
    "analyze_interview_recording",
    "detect_interview_bias",
    "generate_candidate_feedback",
]

SYSTEM_PROMPT = (
    "Voce e um agente de triagem por voz. Conduza entrevistas de screening "
    "por telefone ou VoIP de forma profissional, empatetica e eficiente. "
    "Faca perguntas comportamentais e tecnicas relevantes para a vaga. "
    "Avalie as respostas usando o framework WSI (Bloom, Dreyfus, CBI). "
    "Detecte vieses inconscientes na propria conduta da entrevista. "
    "Ao finalizar, gere feedback construtivo para o candidato. "
    "Sempre respeite LGPD: obtenha consentimento antes de gravar, "
    "nunca use raca, religiao, genero, etnia, estado civil ou saude "
    "em decisoes de scoring. A WeDOTalent e a controladora legal dos dados. "
    "Responda sempre em portugues do Brasil."
)


def upgrade() -> None:
    conn = op.get_bind()
    meta = sa.MetaData()

    # Category "voice" (idempotent)
    categories = sa.Table("agent_categories", meta, autoload_with=conn)
    exists = conn.execute(
        sa.select(categories.c.id).where(categories.c.id == "voice")
    ).first()
    if not exists:
        conn.execute(categories.insert().values(
            id="voice",
            label_pt="Voz",
            label_en="Voice",
            icon="Phone",
            sort_order=10,
            is_active=True,
        ))

    # Template catalog entry (idempotent by slug)
    catalog = sa.Table("agent_template_catalog", meta, autoload_with=conn)
    slug = "tpl-voice-screening"
    exists_tpl = conn.execute(
        sa.select(catalog.c.id).where(catalog.c.slug == slug)
    ).first()
    if not exists_tpl:
        conn.execute(catalog.insert().values(
            id=TEMPLATE_ID,
            slug=slug,
            name="Triagem por Voz",
            description=(
                "Agente de triagem por voz: conduz entrevistas por telefone/VoIP, "
                "avalia respostas com WSI, detecta vieses e gera feedback."
            ),
            category_id="voice",
            sector_id=None,
            system_prompt=SYSTEM_PROMPT,
            allowed_tools=ALLOWED_TOOLS,
            context_level="full",
            max_steps=8,
            temperature=0.4,
            enable_memory=True,
            excluded_tools=[],
            tags=["voz", "triagem", "entrevista", "screening", "telefone", "voip"],
            icon="Phone",
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
            module_required="voice_screening",
            listing_type="template",
            publisher_company_id="wedotalent",
            title="Triagem por Voz",
            short_description="Entrevista de screening por telefone/VoIP com WSI e deteccao de vies",
            long_description=(
                "Agente de triagem por voz que conduz entrevistas de screening "
                "automatizadas por telefone (Twilio PSTN) ou VoIP (Gemini Live). "
                "Avalia respostas com o framework WSI (Bloom, Dreyfus, CBI, Big Five), "
                "detecta vieses inconscientes na conduta da entrevista e gera "
                "feedback construtivo para o candidato. Consentimento LGPD obrigatorio "
                "antes de iniciar gravacao. Voice-enabled por padrao."
            ),
            category="voice",
            tags=["voz", "triagem", "screening", "telefone", "voip"],
            icon_url=None,
            status="approved",
            credits_per_execution=5,
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
    conn.execute(catalog.delete().where(catalog.c.slug == "tpl-voice-screening"))

    categories = sa.Table("agent_categories", meta, autoload_with=conn)
    conn.execute(categories.delete().where(categories.c.id == "voice"))
