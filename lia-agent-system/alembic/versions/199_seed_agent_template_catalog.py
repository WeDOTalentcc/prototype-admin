"""Seed agent_template_catalog + agent_categories + agent_sectors (Sprint 3 Caminho B).

Revision ID: 199
Revises: 198
Create Date: 2026-05-25

Plan canonical: ~/Documents/wedotalent_audit_2026-05-25/AGENT_STUDIO_IMPLEMENTATION_PLAN.md §4
Decisão Paulo: Caminho B — tabela NOVA `agent_template_catalog`, isolada de
`agent_templates` existente (per-tenant publishable).

NOTA (2026-05-25 v2): tabelas já podem existir pelo create_all auto-discovery
SQLAlchemy boot (model registrado em __init__.py). Migration idempotente:
checa via inspector se tabela existe antes de criar.

Mudanças:
1. CREATE agent_categories se não existir
2. CREATE agent_sectors se não existir
3. CREATE agent_template_catalog se não existir
4. SEED categorias (7), setores (5), templates (15)
"""
from __future__ import annotations

import uuid

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "199"
down_revision = "198"
branch_labels = None
depends_on = None


CATEGORIES = [
    ("all", "Todos", "All", "LayoutGrid", 0),
    ("screening", "Triagem", "Screening", "Filter", 1),
    ("sourcing", "Captação", "Sourcing", "Search", 2),
    ("communication", "Comunicação", "Communication", "MessageCircle", 3),
    ("analytics", "Análise", "Analytics", "BarChart3", 4),
    ("job_management", "Vagas", "Job Management", "Briefcase", 5),
    ("automation", "Automação", "Automation", "Zap", 6),
]

SECTORS = [
    ("tech", "Tecnologia", "Technology", 1),
    ("saude", "Saúde", "Healthcare", 2),
    ("educacao", "Educação", "Education", 3),
    ("varejo", "Varejo", "Retail", 4),
    ("generico", "Genérico", "Generic", 5),
]

_SECTOR_MAP = {"tech": "tech", "health": "saude", "education": "educacao", "retail": "varejo", None: None}


def _t(slug, name, description, category_id, sector_id_ts, icon, accent_color,
       system_prompt, allowed_tools, context_level, max_steps, temperature,
       enable_memory, tags, vertical_prompts=None, sort_order=0):
    return {
        "id": str(uuid.uuid4()),
        "slug": slug,
        "name": name,
        "description": description,
        "category_id": category_id,
        "sector_id": _SECTOR_MAP.get(sector_id_ts),
        "system_prompt": system_prompt,
        "allowed_tools": allowed_tools,
        "context_level": context_level,
        "max_steps": max_steps,
        "temperature": temperature,
        "enable_memory": enable_memory,
        "excluded_tools": [],
        "tags": tags,
        "vertical_prompts": vertical_prompts,
        "icon": icon,
        "accent_color": accent_color,
        "badge_variant": None,
        "sort_order": sort_order,
        "is_active": True,
        "company_id": None,
    }


TEMPLATES = [
    _t("tpl-triagem-tech", "Triagem Tech",
       "Filtra candidatos de tecnologia por stack, experiência e senioridade. Avalia fit técnico automaticamente.",
       "screening", "tech", "Code", "graphite",
       "Voce e um agente de triagem tecnica. Analise o CV do candidato focando em: stack tecnologico, anos de experiencia, projetos relevantes e senioridade. Classifique de 1-10 com justificativa.",
       ["search_candidates", "get_candidate_details", "get_evaluation_criteria", "create_note"],
       "standard", 8, 0.3, True, ["popular", "tech", "triagem"],
       vertical_prompts={"tech": "Voce e um agente de triagem tecnica especializado em tecnologia. Analise stack tecnologico (linguagens, frameworks, cloud), system design, anos de experiencia em projetos relevantes, contribuicoes open source e senioridade. Considere fit cultural com cultura DevOps/agile. Classifique de 1-10 com justificativa tecnica detalhada."},
       sort_order=10),
    _t("tpl-triagem-volume", "Triagem Volume",
       "Processa alto volume de candidaturas rapidamente. Ideal para vagas operacionais, varejo e atendimento.",
       "screening", "retail", "Users", "slate",
       "Voce e um agente de triagem rapida para vagas de alto volume. Avalie cada candidato em menos de 30 segundos focando nos requisitos minimos: disponibilidade, localizacao e experiencia basica.",
       ["search_candidates", "get_candidate_details", "move_candidate"],
       "minimal", 5, 0.2, False, ["volume", "rapido", "operacional"],
       vertical_prompts={"retail": "Voce e um agente de triagem de alto volume para vagas operacionais de varejo, FMCG e e-commerce. Avalie em segundos: disponibilidade de horarios, mobilidade (proximidade da unidade), experiencia em atendimento ao cliente, capacidade de aprendizado rapido. Foque no minimo viavel — sem viés sobre idade ou origem."},
       sort_order=20),
    _t("tpl-screening-cultural", "Screening Cultural",
       "Avalia fit cultural do candidato com base nos valores e cultura da empresa.",
       "screening", None, "Heart", "mist",
       "Voce e um agente de screening cultural. Use os valores da empresa e o perfil cultural para avaliar compatibilidade. Foque em soft skills, motivacao e alinhamento de valores. Nunca pergunte sobre idade, genero, religiao ou estado civil.",
       ["get_candidate_details", "get_evaluation_criteria", "get_company_culture", "create_note"],
       "full", 8, 0.5, True, ["cultura", "soft-skills", "valores"],
       sort_order=30),
    _t("tpl-sourcing-passivo", "Sourcing Passivo",
       "Busca candidatos que não se candidataram ativamente. Mapeia talentos em bancos de dados e pools.",
       "sourcing", None, "Search", "graphite",
       "Voce e um agente de sourcing passivo. Busque candidatos que correspondam ao perfil da vaga em bancos de talentos e listas. Priorize candidatos com experiencia relevante que nao se candidataram recentemente.",
       ["search_candidates", "get_candidate_details", "get_job_details", "search_talent_pool"],
       "standard", 10, 0.4, True, ["sourcing", "passivo", "headhunting"],
       sort_order=40),
    _t("tpl-sourcing-diversidade", "Sourcing Diversidade",
       "Busca com guardrails de diversidade e inclusão. Garante representatividade no funil.",
       "sourcing", None, "Globe", "ink",
       "Voce e um agente de sourcing com foco em diversidade. Busque candidatos garantindo representatividade no funil. NUNCA filtre por genero, raca, idade, religiao ou orientacao. Foque em competencias e potencial.",
       ["search_candidates", "get_candidate_details", "search_talent_pool", "get_analytics_summary"],
       "full", 10, 0.5, True, ["diversidade", "inclusao", "dei"],
       sort_order=50),
    _t("tpl-agendamento", "Agendamento Entrevista",
       "Agenda entrevistas automaticamente coordenando disponibilidade do candidato e entrevistador.",
       "communication", None, "Calendar", "slate",
       "Voce e um agente de agendamento. Coordene a agenda do candidato e do entrevistador para encontrar o melhor horario. Seja cordial e eficiente. Ofereca 2-3 opcoes de horario.",
       ["get_candidate_details", "schedule_interview", "send_email"],
       "minimal", 6, 0.3, False, ["agenda", "entrevista", "scheduling"],
       sort_order=60),
    _t("tpl-followup", "Follow-up Candidato",
       "Envia acompanhamento automático após entrevistas. Mantém o candidato engajado no processo.",
       "communication", None, "MessageCircle", "mist",
       "Voce e um agente de follow-up. Envie mensagens de acompanhamento personalizadas apos entrevistas. Seja profissional, empatetico e transparente sobre proximos passos.",
       ["get_candidate_details", "send_email", "get_pipeline_summary", "create_note"],
       "standard", 5, 0.6, True, ["follow-up", "engajamento", "comunicacao"],
       sort_order=70),
    _t("tpl-analise-pipeline", "Análise Pipeline",
       "Analisa métricas e gargalos do funil de recrutamento. Identifica onde candidatos estão travando.",
       "analytics", None, "BarChart3", "graphite",
       "Voce e um analista de pipeline. Identifique gargalos no funil, tempo medio por etapa, taxas de conversao e onde candidatos estao abandonando. Sugira acoes concretas para melhorar.",
       ["list_jobs", "get_pipeline_summary", "get_analytics_summary"],
       "standard", 8, 0.3, False, ["pipeline", "metricas", "gargalos"],
       sort_order=80),
    _t("tpl-comparacao", "Comparação Candidatos",
       "Compara finalistas lado a lado com ranking objetivo baseado nos critérios da vaga.",
       "analytics", None, "GitCompare", "graphite",
       "Voce e um analista de candidatos. Compare os finalistas lado a lado usando os criterios da vaga. Crie um ranking objetivo com pontuacao e justificativa para cada dimensao avaliada.",
       ["get_candidate_details", "get_job_details", "get_evaluation_criteria", "get_pipeline_summary", "create_note"],
       "full", 10, 0.3, True, ["comparacao", "ranking", "finalistas"],
       sort_order=90),
    _t("tpl-assistente-vaga", "Assistente de Vaga",
       "Ajuda a criar e otimizar descrições de vagas. Sugere melhorias baseadas em boas práticas.",
       "job_management", None, "FileEdit", "slate",
       "Voce e um especialista em job descriptions. Ajude o recrutador a criar descricoes claras, inclusivas e atrativas. Sugira skills relevantes, faixas salariais competitivas e beneficios.",
       ["get_job_details", "list_jobs", "get_analytics_summary"],
       "standard", 8, 0.7, True, ["vaga", "job-description", "otimizacao"],
       sort_order=100),
    _t("tpl-onboarding-prep", "Onboarding Prep",
       "Prepara o processo de onboarding após a contratação. Organiza documentos e tarefas iniciais.",
       "automation", "health", "Rocket", "mist",
       "Voce e um agente de onboarding. Prepare a integracao do novo colaborador: liste documentos necessarios, tarefas da primeira semana, pessoas para conhecer e recursos para acessar.",
       ["get_candidate_details", "send_email", "create_note"],
       "standard", 8, 0.5, True, ["onboarding", "integracao", "novo-colaborador"],
       vertical_prompts={"saude": "Voce e um agente de preparacao de onboarding especializado em saude e hospitalar. Verifique documentacao obrigatoria (CRM/COREN/CRP ativo, vacinas, exames admissionais, NR-32 compliance). Prepare checklist personalizado por categoria profissional (enfermagem, medicina, tecnico, administrativo). Atente a treinamentos regulatorios (LGPD em saude, codigos de etica)."},
       sort_order=110),
    _t("tpl-salary-benchmark", "Salary Benchmark",
       "Pesquisa benchmark salarial para a vaga com base em dados de mercado.",
       "analytics", None, "DollarSign", "graphite",
       "Voce e um analista de remuneracao. Pesquise e apresente benchmarks salariais para a vaga considerando senioridade, localizacao, setor e porte da empresa. Apresente faixas (P25, P50, P75).",
       ["get_job_details", "get_analytics_summary"],
       "minimal", 6, 0.3, False, ["salario", "benchmark", "remuneracao"],
       sort_order=120),
    _t("tpl-feedback-collector", "Feedback Collector",
       "Coleta e organiza feedback de entrevistadores de forma estruturada.",
       "communication", None, "ClipboardCheck", "slate",
       "Voce e um agente de coleta de feedback. Solicite feedback estruturado dos entrevistadores sobre cada candidato: pontos fortes, areas de melhoria, recomendacao (sim/nao/talvez) e justificativa.",
       ["get_candidate_details", "send_email", "create_note"],
       "standard", 6, 0.4, True, ["feedback", "entrevistadores", "avaliacao"],
       sort_order=130),
    _t("tpl-talent-pool-curator", "Talent Pool Curator",
       "Organiza e rankeia candidatos no banco de talentos. Mantém o pool atualizado e relevante.",
       "sourcing", None, "Database", "mist",
       "Voce e um curador de banco de talentos. Analise os candidatos no pool, remova perfis desatualizados, categorize por area de atuacao e ranqueie por relevancia para vagas abertas.",
       ["get_candidate_details", "get_job_details", "search_talent_pool", "create_note"],
       "standard", 10, 0.4, True, ["talent-pool", "curadoria", "organizacao"],
       sort_order=140),
    _t("tpl-compliance-check", "Compliance Check",
       "Valida requisitos legais e de compliance do processo seletivo.",
       "screening", "education", "ShieldCheck", "ink",
       "Voce e um agente de compliance. Verifique se o processo seletivo atende requisitos legais: LGPD, igualdade de oportunidades, documentacao necessaria e prazos regulatorios. Sinalize riscos.",
       ["get_job_details", "get_candidate_details", "get_evaluation_criteria", "get_pipeline_summary", "create_note"],
       "full", 8, 0.2, False, ["compliance", "lgpd", "legal"],
       vertical_prompts={"educacao": "Voce e um agente de compliance especializado em educacao (universidades, EdTech, escolas). Valide: titulacao academica (graduacao/mestrado/doutorado conforme exigencia da vaga docente), Curriculo Lattes atualizado, experiencia em pesquisa/extensao, registros profissionais especificos (Pedagogo, Psicologo Educacional). Atente LGPD para dados de alunos quando a vaga envolve contato com menores."},
       sort_order=150),
]


def _table_exists(table_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return table_name in inspector.get_table_names()


def upgrade():
    if not _table_exists("agent_categories"):
        op.create_table(
            "agent_categories",
            sa.Column("id", sa.String(64), primary_key=True),
            sa.Column("label_pt", sa.String(128), nullable=False),
            sa.Column("label_en", sa.String(128), nullable=False),
            sa.Column("icon", sa.String(64), nullable=True),
            sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        )

    if not _table_exists("agent_sectors"):
        op.create_table(
            "agent_sectors",
            sa.Column("id", sa.String(64), primary_key=True),
            sa.Column("label_pt", sa.String(128), nullable=False),
            sa.Column("label_en", sa.String(128), nullable=False),
            sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        )

    if not _table_exists("agent_template_catalog"):
        op.create_table(
            "agent_template_catalog",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("slug", sa.String(128), nullable=False, unique=True),
            sa.Column("name", sa.String(256), nullable=False),
            sa.Column("description", sa.Text(), nullable=False),
            sa.Column("category_id", sa.String(64),
                      sa.ForeignKey("agent_categories.id", ondelete="RESTRICT"), nullable=False),
            sa.Column("sector_id", sa.String(64),
                      sa.ForeignKey("agent_sectors.id", ondelete="SET NULL"), nullable=True),
            sa.Column("system_prompt", sa.Text(), nullable=False),
            sa.Column("allowed_tools", postgresql.JSONB(), nullable=False, server_default="[]"),
            sa.Column("context_level", sa.String(32), nullable=False, server_default="standard"),
            sa.Column("max_steps", sa.Integer(), nullable=False, server_default="10"),
            sa.Column("temperature", sa.Float(), nullable=False, server_default="0.7"),
            sa.Column("enable_memory", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("excluded_tools", postgresql.JSONB(), nullable=False, server_default="[]"),
            sa.Column("tags", postgresql.JSONB(), nullable=False, server_default="[]"),
            sa.Column("vertical_prompts", postgresql.JSONB(), nullable=True),
            sa.Column("icon", sa.String(64), nullable=True),
            sa.Column("accent_color", sa.String(32), nullable=True),
            sa.Column("badge_variant", sa.String(32), nullable=True),
            sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("company_id", sa.String(255), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        )
        op.create_index("ix_agent_template_catalog_slug", "agent_template_catalog", ["slug"], unique=True)
        op.create_index("ix_agent_template_catalog_company", "agent_template_catalog", ["company_id"])
        op.create_index("ix_agent_template_catalog_active", "agent_template_catalog", ["is_active"])
        op.create_index("ix_agent_template_catalog_category", "agent_template_catalog", ["category_id"])

    # SEED — somente se vazias (idempotente em reruns)
    bind = op.get_bind()
    cat_count = bind.execute(sa.text("SELECT COUNT(*) FROM agent_categories")).scalar()
    if cat_count == 0:
        op.bulk_insert(
            sa.table("agent_categories",
                sa.column("id", sa.String), sa.column("label_pt", sa.String),
                sa.column("label_en", sa.String), sa.column("icon", sa.String),
                sa.column("sort_order", sa.Integer), sa.column("is_active", sa.Boolean)),
            [{"id": cid, "label_pt": lpt, "label_en": len_, "icon": icon,
              "sort_order": so, "is_active": True}
             for (cid, lpt, len_, icon, so) in CATEGORIES],
        )

    sec_count = bind.execute(sa.text("SELECT COUNT(*) FROM agent_sectors")).scalar()
    if sec_count == 0:
        op.bulk_insert(
            sa.table("agent_sectors",
                sa.column("id", sa.String), sa.column("label_pt", sa.String),
                sa.column("label_en", sa.String), sa.column("sort_order", sa.Integer),
                sa.column("is_active", sa.Boolean)),
            [{"id": sid, "label_pt": lpt, "label_en": len_, "sort_order": so, "is_active": True}
             for (sid, lpt, len_, so) in SECTORS],
        )

    tpl_count = bind.execute(sa.text("SELECT COUNT(*) FROM agent_template_catalog")).scalar()
    if tpl_count == 0:
        op.bulk_insert(
            sa.table("agent_template_catalog",
                sa.column("id", postgresql.UUID(as_uuid=True)),
                sa.column("slug", sa.String), sa.column("name", sa.String),
                sa.column("description", sa.Text), sa.column("category_id", sa.String),
                sa.column("sector_id", sa.String), sa.column("system_prompt", sa.Text),
                sa.column("allowed_tools", postgresql.JSONB),
                sa.column("context_level", sa.String), sa.column("max_steps", sa.Integer),
                sa.column("temperature", sa.Float), sa.column("enable_memory", sa.Boolean),
                sa.column("excluded_tools", postgresql.JSONB),
                sa.column("tags", postgresql.JSONB),
                sa.column("vertical_prompts", postgresql.JSONB),
                sa.column("icon", sa.String), sa.column("accent_color", sa.String),
                sa.column("badge_variant", sa.String), sa.column("sort_order", sa.Integer),
                sa.column("is_active", sa.Boolean), sa.column("company_id", sa.String)),
            TEMPLATES,
        )


def downgrade():
    if _table_exists("agent_template_catalog"):
        op.drop_table("agent_template_catalog")
    if _table_exists("agent_sectors"):
        op.drop_table("agent_sectors")
    if _table_exists("agent_categories"):
        op.drop_table("agent_categories")
