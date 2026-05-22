"""seed canonical marketplace listings (Wave 3 audit 2026-05-21)

Revision ID: 163_seed_marketplace_listings
Revises: 162_workforce_entries_company_id_not_null
Create Date: 2026-05-21 22:00:00.000000

Wave 3 audit follow-up: marketplace estava 100% vazio em produção
(grep ConfirmedAgent na rota GET /agent-marketplace retorna []).
Tab Explorar mostrava empty state para qualquer cliente novo.

Este seed cria 10 custom_agents publicados pela tenant sintética
'00000000-0000-0000-0000-000000000001' (WeDOTalent system publisher)
e suas listings APPROVED com status published.

Idempotent: ON CONFLICT (id) DO NOTHING — re-runs são safe.

Audit ref: ~/Documents/wedotalent_audit_2026-05-21/DIAGNOSTICO_ESTUDIO_AGENTES_2026-05-21.md
Sec. 7 reality check (Marketplace).
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "163_seed_marketplace_listings"
down_revision = "162_workforce_entries_company_id_not_null"
branch_labels = None
depends_on = None


WEDO_PUBLISHER = "00000000-0000-0000-0000-000000000001"

SEEDS = [
    {
        "agent_id": "aaa00001-0000-4000-8000-000000000001",
        "listing_id": "bbb00001-0000-4000-8000-000000000001",
        "name": "Triagem Volume",
        "role": "Triagem em alto volume",
        "description": "Processa alto volume de candidaturas rapidamente. Ideal para vagas operacionais, varejo e atendimento.",
        "category": "screening",
        "domain": "screening",
        "icon": "users",
        "tags": [
            "triagem",
            "volume",
            "operacional"
        ],
        "allowed_tools": [
            "search_candidates",
            "get_candidate_details",
            "move_candidate"
        ],
        "title": "Triagem Volume — para alto throughput",
        "long_description": "Agente otimizado para triagem de centenas/milhares de candidaturas por dia. Identifica match score por critérios objetivos (skills, experiência, localização) e move candidatos para próxima etapa automaticamente. LGPD-compliant: não filtra por gênero/raça/idade.",
        "system_prompt": "Você é um agente de triagem em alto volume. Avalie cada candidato comparando seus skills/experiência/localização com os requisitos da vaga. Use search_candidates para listar candidatos, get_candidate_details para perfil completo, e move_candidate para avançar quem passa no filtro objetivo. NUNCA filtre por gênero, raça, idade, ou estado civil (Lei 9.029/95 + LGPD).",
        "max_steps": 10,
        "temperature": 0.3
    },
    {
        "agent_id": "aaa00002-0000-4000-8000-000000000002",
        "listing_id": "bbb00002-0000-4000-8000-000000000002",
        "name": "Agendamento Entrevista",
        "role": "Agendamento automático de entrevistas",
        "description": "Agenda entrevistas automaticamente coordenando disponibilidade do candidato e entrevistador.",
        "category": "communication",
        "domain": "communication",
        "icon": "calendar",
        "tags": [
            "agendamento",
            "entrevistas",
            "comunicação"
        ],
        "allowed_tools": [
            "get_candidate_details",
            "schedule_interview",
            "send_email"
        ],
        "title": "Agendamento Entrevista — coordenação automática",
        "long_description": "Agente que coordena agendamento de entrevistas: consulta disponibilidade do candidato, propõe horários, confirma com entrevistador, envia convite calendário e email de confirmação.",
        "system_prompt": "Você é um agente de agendamento de entrevistas. Use get_candidate_details para obter contato + preferências do candidato. Use schedule_interview para criar slot no calendário do entrevistador. Use send_email para confirmar o agendamento com o candidato. Sempre confirme dia/hora/local/link antes de agendar.",
        "max_steps": 8,
        "temperature": 0.4
    },
    {
        "agent_id": "aaa00003-0000-4000-8000-000000000003",
        "listing_id": "bbb00003-0000-4000-8000-000000000003",
        "name": "Assistente de Vaga",
        "role": "Otimização de descrição de vagas",
        "description": "Ajuda a criar e otimizar descrições de vagas. Sugere melhorias baseadas em boas práticas.",
        "category": "general",
        "domain": "job_management",
        "icon": "edit",
        "tags": [
            "vagas",
            "redação",
            "otimização"
        ],
        "allowed_tools": [
            "get_job_details",
            "list_jobs",
            "update_candidate_field"
        ],
        "title": "Assistente de Vaga — redação canonical",
        "long_description": "Agente que sugere melhorias em descrição de vagas: tom inclusivo (sem viés de gênero/idade), clareza de requisitos, alinhamento com cultura da empresa, palavras-chave para SEO de attraction.",
        "system_prompt": "Você é um assistente de redação de vagas. Use get_job_details e list_jobs para ler o contexto. Sugira melhorias na descrição focando em: (1) linguagem inclusiva e neutra de gênero, (2) requisitos claros separados em essenciais vs desejáveis, (3) destacar diferenciais da empresa, (4) evitar jargão excludente. NUNCA sugira filtros discriminatórios.",
        "max_steps": 8,
        "temperature": 0.6
    },
    {
        "agent_id": "aaa00004-0000-4000-8000-000000000004",
        "listing_id": "bbb00004-0000-4000-8000-000000000004",
        "name": "Salary Benchmark",
        "role": "Pesquisa salarial automatizada",
        "description": "Pesquisa benchmark salarial para vaga com base em dados de mercado.",
        "category": "general",
        "domain": "analytics",
        "icon": "trending",
        "tags": [
            "salário",
            "benchmark",
            "mercado"
        ],
        "allowed_tools": [
            "get_job_details",
            "list_jobs"
        ],
        "title": "Salary Benchmark — dados de mercado",
        "long_description": "Agente que pesquisa benchmark salarial para uma vaga específica considerando senioridade, localização, modelo de trabalho (remoto/hybrid/presencial), e tech stack quando aplicável.",
        "system_prompt": "Você é um especialista em benchmark salarial. Use get_job_details para obter contexto da vaga (cargo, senioridade, localização, stack). Forneça faixa salarial mínima/média/máxima com fontes ou raciocínio. Considere variação por região quando aplicável.",
        "max_steps": 6,
        "temperature": 0.4
    },
    {
        "agent_id": "aaa00005-0000-4000-8000-000000000005",
        "listing_id": "bbb00005-0000-4000-8000-000000000005",
        "name": "Sourcing Passivo",
        "role": "Busca de candidatos passivos",
        "description": "Identifica candidatos que não se candidataram ativamente. Mapeia talentos em bancos de dados internos.",
        "category": "sourcing",
        "domain": "sourcing",
        "icon": "search",
        "tags": [
            "sourcing",
            "passivo",
            "captação"
        ],
        "allowed_tools": [
            "search_candidates",
            "get_candidate_details",
            "get_job_details"
        ],
        "title": "Sourcing Passivo — talent pool interno",
        "long_description": "Agente que mapeia candidatos passivos no talent pool da empresa que tenham perfil compatível com vagas abertas. Útil para re-engajar candidatos que não foram contratados em processos anteriores mas têm fit cultural/técnico.",
        "system_prompt": "Você é um agente de sourcing passivo. Use get_job_details para obter requisitos da vaga aberta. Use search_candidates com filtros baseados em skills, experiência e localização. Para cada candidato relevante, use get_candidate_details para validar fit. NUNCA filtre por gênero, raça, ou idade (Lei 9.029/95).",
        "max_steps": 10,
        "temperature": 0.4
    },
    {
        "agent_id": "aaa00006-0000-4000-8000-000000000006",
        "listing_id": "bbb00006-0000-4000-8000-000000000006",
        "name": "Follow-up Candidato",
        "role": "Re-engajamento automático",
        "description": "Envia acompanhamento automático após entrevistas. Mantém candidato engajado no processo.",
        "category": "communication",
        "domain": "communication",
        "icon": "message",
        "tags": [
            "follow-up",
            "engajamento",
            "comunicação"
        ],
        "allowed_tools": [
            "get_candidate_details",
            "send_email"
        ],
        "title": "Follow-up Candidato — comunicação ativa",
        "long_description": "Agente que envia follow-up automático para candidatos após etapas críticas: pós-entrevista, espera por decisão, oferta enviada. Mantém o candidato engajado sem ser invasivo.",
        "system_prompt": "Você é um agente de comunicação com candidatos. Use get_candidate_details para obter contexto + última atividade. Use send_email para enviar follow-up apropriado: agradecimento pós-entrevista, atualização de status, ou check-in passivo. Tom: cordial, transparente, respeitoso do tempo do candidato.",
        "max_steps": 6,
        "temperature": 0.5
    },
    {
        "agent_id": "aaa00007-0000-4000-8000-000000000007",
        "listing_id": "bbb00007-0000-4000-8000-000000000007",
        "name": "Onboarding Prep",
        "role": "Preparação de onboarding",
        "description": "Prepara processo de onboarding após contratação. Organiza documentos e tarefas iniciais.",
        "category": "general",
        "domain": "general",
        "icon": "check",
        "tags": [
            "onboarding",
            "contratação",
            "documentos"
        ],
        "allowed_tools": [
            "get_candidate_details",
            "send_email"
        ],
        "title": "Onboarding Prep — kickstart pós-hire",
        "long_description": "Agente que orquestra a preparação de onboarding após hire confirmado: envia checklist de documentos, agenda dia 1, configura acessos, envia welcome kit. Reduz tempo de produtividade do novo colaborador.",
        "system_prompt": "Você é um agente de onboarding. Use get_candidate_details para obter dados do hire. Use send_email para enviar: (1) welcome message + boas-vindas, (2) checklist de documentos, (3) agenda do dia 1. Tom: acolhedor, claro, organizado. Confirme tudo antes do dia de início.",
        "max_steps": 8,
        "temperature": 0.5
    },
    {
        "agent_id": "aaa00008-0000-4000-8000-000000000008",
        "listing_id": "bbb00008-0000-4000-8000-000000000008",
        "name": "Compliance Check",
        "role": "Validação de compliance",
        "description": "Valida requisitos legais e de compliance do processo seletivo.",
        "category": "screening",
        "domain": "screening",
        "icon": "shield",
        "tags": [
            "compliance",
            "lgpd",
            "diversidade"
        ],
        "allowed_tools": [
            "get_job_details",
            "get_candidate_details"
        ],
        "title": "Compliance Check — LGPD + Lei 9.029/95",
        "long_description": "Agente que audita processo seletivo contra requisitos de compliance (LGPD Art. 6º+11+20, Lei 9.029/95 anti-discriminação, ISO 30414). Flagga vagas ou critérios que possam configurar bias ou violação.",
        "system_prompt": "Você é um agente de compliance de recrutamento. Use get_job_details para auditar requisitos publicados: detecte linguagem discriminatória (gênero, raça, idade, estado civil, religião). Use get_candidate_details apenas com base legal (consentimento + finalidade explícita). Reporte findings com referência ao artigo de lei. NUNCA mascare violação — sempre destaque.",
        "max_steps": 6,
        "temperature": 0.2
    },
    {
        "agent_id": "aaa00009-0000-4000-8000-000000000009",
        "listing_id": "bbb00009-0000-4000-8000-000000000009",
        "name": "Comparação Candidatos",
        "role": "Ranking objetivo de finalistas",
        "description": "Compara finalistas lado a lado com ranking objetivo baseado nos critérios da vaga.",
        "category": "screening",
        "domain": "screening",
        "icon": "compare",
        "tags": [
            "comparação",
            "ranking",
            "decisão"
        ],
        "allowed_tools": [
            "get_candidate_details",
            "get_job_details"
        ],
        "title": "Comparação Candidatos — decision support",
        "long_description": "Agente que compara N finalistas para uma vaga gerando matriz objetiva: skills match, anos de experiência, alinhamento cultural, salary expectation. Não toma decisão final — é decision-support tool para hiring manager.",
        "system_prompt": "Você é um agente de comparação de candidatos. Use get_job_details para obter critérios da vaga (REQUIRED + DESIRED). Use get_candidate_details para cada finalista. Gere matriz comparativa com critérios objetivos: skills match, experiência, fit cultural, expectativa salarial. NUNCA use gênero, raça, idade, estado civil como critério. Apresente trade-offs para o hiring manager decidir.",
        "max_steps": 10,
        "temperature": 0.3
    },
    {
        "agent_id": "aaa00010-0000-4000-8000-000000000010",
        "listing_id": "bbb00010-0000-4000-8000-000000000010",
        "name": "Análise de Pipeline",
        "role": "Diagnóstico do funil",
        "description": "Analisa métricas e gargalos do funil de recrutamento. Identifica onde candidatos estão travando.",
        "category": "general",
        "domain": "analytics",
        "icon": "chart",
        "tags": [
            "analytics",
            "funil",
            "métricas"
        ],
        "allowed_tools": [
            "list_jobs",
            "get_job_details"
        ],
        "title": "Análise de Pipeline — funnel diagnostics",
        "long_description": "Agente que diagnostica gargalos no funil de recrutamento por job_vacancy ou por departamento. Identifica conversão por etapa, tempo médio de progressão, drop-off rate por fonte. Recomenda otimizações.",
        "system_prompt": "Você é um analyst de pipeline de recrutamento. Use list_jobs para mapear vagas abertas. Use get_job_details para obter contexto + métricas. Identifique etapas com conversão abaixo do baseline (e.g., screening < 30% ou interview no-show > 20%). Reporte top 3 gargalos com recomendações específicas.",
        "max_steps": 8,
        "temperature": 0.3
    }
]


def upgrade() -> None:
    """Insert 10 canonical marketplace listings."""
    conn = op.get_bind()

    for seed in SEEDS:
        # 1. Insert CustomAgent
        conn.execute(sa.text("""
            INSERT INTO custom_agents (
                id, company_id, created_by, name, role, description,
                system_prompt, allowed_tools, domain, icon, status, version,
                config, max_steps, temperature, enable_memory, context_level, excluded_tools,
                is_marketplace_published, created_at, updated_at
            ) VALUES (
                CAST(:id AS uuid), :company_id, :created_by, :name, :role, :description,
                :system_prompt, :allowed_tools, :domain, :icon, 'active', 1,
                '{}'::jsonb, :max_steps, :temperature, true, 'full', '{}',
                true, NOW(), NOW()
            ) ON CONFLICT (id) DO NOTHING
        """), {
            "id": seed["agent_id"],
            "company_id": WEDO_PUBLISHER,
            "created_by": "wedotalent_system",
            "name": seed["name"],
            "role": seed["role"],
            "description": seed["description"],
            "system_prompt": seed["system_prompt"],
            "allowed_tools": list(seed["allowed_tools"]),
            "domain": seed["domain"],
            "icon": seed["icon"],
            "max_steps": seed["max_steps"],
            "temperature": seed["temperature"],
        })

        # 2. Insert AgentMarketplaceListing
        conn.execute(sa.text("""
            INSERT INTO agent_marketplace_listings (
                id, agent_id, publisher_company_id, title, short_description, long_description,
                category, tags, status, credits_per_execution, is_free,
                install_count, avg_rating, total_ratings, published_at,
                created_at, updated_at
            ) VALUES (
                CAST(:id AS uuid), CAST(:agent_id AS uuid), :publisher, :title, :short_desc, :long_desc,
                :category, :tags, 'approved', 1, true,
                0, 0.0, 0, NOW(),
                NOW(), NOW()
            ) ON CONFLICT (id) DO NOTHING
        """), {
            "id": seed["listing_id"],
            "agent_id": seed["agent_id"],
            "publisher": WEDO_PUBLISHER,
            "title": seed["title"],
            "short_desc": seed["description"],
            "long_desc": seed["long_description"],
            "category": seed["category"],
            "tags": list(seed["tags"]),
        })


def downgrade() -> None:
    """Remove seed listings + agents."""
    conn = op.get_bind()
    for seed in SEEDS:
        conn.execute(sa.text("DELETE FROM agent_marketplace_listings WHERE id = CAST(:id AS uuid)"),
                     {"id": seed["listing_id"]})
        conn.execute(sa.text("DELETE FROM custom_agents WHERE id = CAST(:id AS uuid)"),
                     {"id": seed["agent_id"]})
