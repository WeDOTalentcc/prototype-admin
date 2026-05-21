"""Create integration_catalog_entries + seed master canonical (16 entradas).

Audit 2026-05-20 Sessão I Step 5 / Sprint 4 (catalogos dinamicos):
substitui catalogo hardcoded `integration-data.ts` (frontend, 370 linhas, 16
entradas Gemini/Claude/OpenAI/Gupy/Pandapé/Merge/etc) por modelo per-tenant
canonical no DB.

Schema canonical:
- is_master_template=True: items curados pela WeDOTalent (NULL company_id)
- is_master_template=False: customs por company (company_id NOT NULL)
- parent_template_id: NOT NULL quando custom é cópia de master (canonical A1)
- soft-delete via deleted_at

Multiple heads (153_eligibility_question_templates + 151_sprint_p1_deferred_tables_fix):
fixar revises em 153 (mais recente). 151 vira parent merge via alembic.

Revision ID: 156_integration_catalog_entries
Revises: 153_eligibility_question_templates
Create Date: 2026-05-21

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "156_integration_catalog_entries"
down_revision: Union[str, None] = "153_eligibility_question_templates"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Master canonical seed extraido de
# plataforma-lia/src/components/settings/integrations/integration-data.ts (2026-05-20).
# Mapeamento canonical:
#   id -> provider (slug)
#   name -> label
#   shortDescription -> description
#   fullDescription -> full_description
#   status: "connected"|"not_configured" -> "production"; "coming_soon" -> "coming_soon"
#   icon* / capabilities / configFields / connectAction / isActiveProvider -> metadata
MASTER_ITEMS = [
    {
        "provider": "gemini",
        "label": "Google Gemini",
        "category": "ai_models",
        "logo_url": None,
        "description": "Modelo de IA principal da plataforma LIA",
        "full_description": "Google Gemini é o provedor de IA padrão da plataforma LIA. Utilizado para análise de currículos, geração de perguntas de entrevista, avaliação de candidatos e interações conversacionais. Suporta modelos Gemini 2.0 Flash e Pro.",
        "status": "production",
        "industries_recommended": [],
        "metadata": {
            "icon_bg": "bg-blue-500/10",
            "icon_color": "text-blue-600 dark:text-blue-400",
            "icon_letter": "G",
            "is_active_provider": True,
            "connect_action": "config",
            "capabilities": [
                {"name": "Análise de Currículos", "description": "Extração e avaliação de competências"},
                {"name": "Geração de Perguntas", "description": "Perguntas de entrevista personalizadas"},
                {"name": "Avaliação de Candidatos", "description": "Scoring e ranking inteligente"},
                {"name": "Chat Conversacional", "description": "Interação natural com recrutadores"},
                {"name": "Resumos Automáticos", "description": "Síntese de perfis e entrevistas"},
            ],
            "config_fields": ["GOOGLE_API_KEY"],
        },
    },
    {
        "provider": "claude",
        "label": "Anthropic Claude",
        "category": "ai_models",
        "logo_url": None,
        "description": "Modelo de IA alternativo com raciocínio avançado",
        "full_description": "Anthropic Claude oferece capacidades avançadas de raciocínio e análise. Disponível como provedor alternativo ou fallback na plataforma LIA, com suporte a Claude 3.5 Sonnet e Haiku.",
        "status": "production",
        "industries_recommended": [],
        "metadata": {
            "icon_bg": "bg-orange-500/10",
            "icon_color": "text-orange-600 dark:text-orange-400",
            "icon_letter": "C",
            "is_active_provider": False,
            "connect_action": "config",
            "capabilities": [
                {"name": "Análise Profunda", "description": "Raciocínio complexo sobre candidatos"},
                {"name": "Geração de Texto", "description": "Comunicações e feedbacks elaborados"},
                {"name": "Avaliação Contextual", "description": "Análise de aderência cultural"},
                {"name": "Fallback Provider", "description": "Backup automático quando Gemini indisponível"},
            ],
            "config_fields": ["ANTHROPIC_API_KEY"],
        },
    },
    {
        "provider": "openai",
        "label": "OpenAI GPT",
        "category": "ai_models",
        "logo_url": None,
        "description": "Modelo de IA com ampla base de conhecimento",
        "full_description": "OpenAI GPT oferece modelos versáteis com ampla base de conhecimento. Disponível como provedor terciário na cadeia de fallback da plataforma LIA, suportando GPT-4o e GPT-4o-mini. Essencial para transcrição de áudio (Whisper STT) e voz da LIA (TTS) nas triagens — sem esta chave, as funcionalidades de voz ficam indisponíveis.",
        "status": "production",
        "industries_recommended": [],
        "metadata": {
            "icon_bg": "bg-emerald-500/10",
            "icon_color": "text-emerald-600 dark:text-emerald-400",
            "icon_letter": "O",
            "is_active_provider": False,
            "connect_action": "config",
            "capabilities": [
                {"name": "Processamento de Linguagem", "description": "Compreensão e geração de texto"},
                {"name": "Embeddings", "description": "Representações vetoriais para busca semântica"},
                {"name": "Function Calling", "description": "Integração com ferramentas da plataforma"},
                {"name": "Transcrição (Whisper)", "description": "STT para áudio de candidatos em triagens"},
                {"name": "Voz da LIA (TTS)", "description": "Síntese de voz para perguntas da LIA em triagens"},
                {"name": "Fallback Provider", "description": "Terceiro na cadeia de resiliência"},
            ],
            "config_fields": ["OPENAI_API_KEY"],
        },
    },
    {
        "provider": "gupy",
        "label": "Gupy",
        "category": "ats",
        "logo_url": None,
        "description": "ATS líder no mercado brasileiro",
        "full_description": "Integração com a Gupy, plataforma líder de recrutamento no Brasil. Sincronize vagas, candidatos e etapas do processo seletivo automaticamente com a plataforma LIA.",
        "status": "production",
        "industries_recommended": [],
        "metadata": {
            "icon_bg": "bg-pink-500/10",
            "icon_color": "text-pink-600 dark:text-pink-400",
            "icon_letter": "Gy",
            "connect_action": "config",
            "capabilities": [
                {"name": "Sync de Vagas", "description": "Importação automática de posições abertas"},
                {"name": "Sync de Candidatos", "description": "Sincronização bidirecional de perfis"},
                {"name": "Movimentação de Etapas", "description": "Atualização automática de status"},
                {"name": "Webhooks", "description": "Notificações em tempo real de eventos"},
            ],
            "config_fields": ["GUPY_API_TOKEN", "GUPY_COMPANY_ID"],
        },
    },
    {
        "provider": "pandape",
        "label": "Pandapé",
        "category": "ats",
        "logo_url": None,
        "description": "ATS do grupo InfoJobs para gestão de talentos",
        "full_description": "Integração com Pandapé (InfoJobs) para gestão completa do ciclo de recrutamento. Conecte vagas, candidatos e processos seletivos diretamente à plataforma LIA.",
        "status": "production",
        "industries_recommended": [],
        "metadata": {
            "icon_bg": "bg-green-500/10",
            "icon_color": "text-green-600 dark:text-green-400",
            "icon_letter": "Pp",
            "connect_action": "config",
            "capabilities": [
                {"name": "Importação de Vagas", "description": "Sincronização de posições"},
                {"name": "Gestão de Candidatos", "description": "Perfis e histórico integrados"},
                {"name": "Relatórios", "description": "Métricas unificadas de processo"},
            ],
            "config_fields": ["PANDAPE_API_KEY"],
        },
    },
    {
        "provider": "merge",
        "label": "Merge.dev",
        "category": "ats",
        "logo_url": None,
        "description": "API unificada para 40+ ATS e HRIS",
        "full_description": "Merge.dev oferece uma API unificada que conecta a plataforma LIA a mais de 40 sistemas ATS e HRIS, incluindo Greenhouse, Lever, BambooHR e outros. Uma integração, múltiplas plataformas.",
        "status": "production",
        "industries_recommended": [],
        "metadata": {
            "icon_bg": "bg-violet-500/10",
            "icon_color": "text-violet-600 dark:text-violet-400",
            "icon_letter": "M",
            "connect_action": "config",
            "capabilities": [
                {"name": "Unified API", "description": "Uma API para 40+ plataformas ATS/HRIS"},
                {"name": "Sync Bidirecional", "description": "Dados sincronizados em tempo real"},
                {"name": "Webhooks", "description": "Eventos de mudança em tempo real"},
                {"name": "Normalização de Dados", "description": "Schema unificado entre plataformas"},
            ],
            "config_fields": ["MERGE_API_KEY", "MERGE_ACCOUNT_TOKEN"],
        },
    },
    {
        "provider": "google-calendar",
        "label": "Google Calendar",
        "category": "calendar",
        "logo_url": None,
        "description": "Agendamento com Google Meet automático",
        "full_description": "Conecte sua conta Google Workspace para criar eventos com link do Google Meet automaticamente ao agendar entrevistas. A integração utiliza OAuth 2.0 para acesso seguro ao calendário.",
        "status": "production",
        "industries_recommended": [],
        "metadata": {
            "icon_bg": "bg-red-500/10",
            "icon_color": "text-red-500 dark:text-red-400",
            "icon_letter": "GC",
            "connect_action": "oauth",
            "capabilities": [
                {"name": "Criação de Eventos", "description": "Agendamento automático de entrevistas"},
                {"name": "Google Meet", "description": "Links de videoconferência automáticos"},
                {"name": "Verificação de Disponibilidade", "description": "Consulta de horários livres"},
                {"name": "Notificações", "description": "Lembretes automáticos para participantes"},
            ],
            "config_fields": [],
        },
    },
    {
        "provider": "microsoft-calendar",
        "label": "Microsoft Calendar",
        "category": "calendar",
        "logo_url": None,
        "description": "Agendamento via Microsoft Graph / Outlook",
        "full_description": "Integração com Microsoft Calendar via Microsoft Graph API. Configure as credenciais Azure para habilitar agendamento automático de entrevistas pelo Outlook.",
        "status": "production",
        "industries_recommended": [],
        "metadata": {
            "icon_bg": "bg-sky-500/10",
            "icon_color": "text-sky-600 dark:text-sky-400",
            "icon_letter": "MC",
            "connect_action": "config",
            "capabilities": [
                {"name": "Agendamento Outlook", "description": "Criação de eventos no calendário Outlook"},
                {"name": "Teams Meeting", "description": "Links de reunião Microsoft Teams"},
                {"name": "Disponibilidade", "description": "Consulta de agenda dos participantes"},
                {"name": "Salas de Reunião", "description": "Reserva automática de salas"},
            ],
            "config_fields": ["AZURE_CLIENT_ID", "AZURE_CLIENT_SECRET", "AZURE_TENANT_ID"],
        },
    },
    {
        "provider": "teams",
        "label": "Microsoft Teams",
        "category": "communication",
        "logo_url": None,
        "description": "Notificações e alertas via webhooks do Teams",
        "full_description": "Envie notificações de recrutamento diretamente para canais do Microsoft Teams. Configure webhooks para alertas de novos candidatos, mudanças de status e atualizações de processo seletivo.",
        "status": "production",
        "industries_recommended": [],
        "metadata": {
            "icon_bg": "bg-indigo-500/10",
            "icon_color": "text-indigo-600 dark:text-indigo-400",
            "icon_letter": "T",
            "connect_action": "webhook",
            "capabilities": [
                {"name": "Notificações de Candidatos", "description": "Alertas de novos candidatos"},
                {"name": "Alertas de Processo", "description": "Mudanças de status em tempo real"},
                {"name": "Adaptive Cards", "description": "Cards interativos com ações"},
                {"name": "Canais Customizados", "description": "Diferentes canais por tipo de alerta"},
            ],
            "config_fields": ["TEAMS_WEBHOOK_URL"],
        },
    },
    {
        "provider": "whatsapp",
        "label": "WhatsApp Business",
        "category": "communication",
        "logo_url": None,
        "description": "Comunicação com candidatos via WhatsApp",
        "full_description": "Integração com WhatsApp Business API para comunicação direta com candidatos. Envie convites para entrevistas, atualizações de status e mensagens automatizadas.",
        "status": "coming_soon",
        "industries_recommended": [],
        "metadata": {
            "icon_bg": "bg-green-500/10",
            "icon_color": "text-green-600 dark:text-green-400",
            "icon_letter": "W",
            "connect_action": "none",
            "capabilities": [
                {"name": "Mensagens Automatizadas", "description": "Templates de comunicação"},
                {"name": "Convites de Entrevista", "description": "Envio direto de agendamentos"},
                {"name": "Chatbot", "description": "Atendimento automatizado a candidatos"},
            ],
            "config_fields": [],
        },
    },
    {
        "provider": "email-smtp",
        "label": "Email / SMTP",
        "category": "communication",
        "logo_url": None,
        "description": "Envio de emails transacionais e notificações",
        "full_description": "Configure um servidor SMTP personalizado para envio de emails da plataforma. Personalize templates, remetente e domínio para comunicações com candidatos.",
        "status": "coming_soon",
        "industries_recommended": [],
        "metadata": {
            "icon_bg": "bg-amber-500/10",
            "icon_color": "text-amber-600 dark:text-amber-400",
            "icon_letter": "E",
            "connect_action": "none",
            "capabilities": [
                {"name": "Emails Transacionais", "description": "Confirmações e notificações"},
                {"name": "Templates Customizados", "description": "Modelos personalizáveis"},
                {"name": "Tracking", "description": "Rastreamento de abertura e cliques"},
            ],
            "config_fields": [],
        },
    },
    {
        "provider": "salesforce",
        "label": "Salesforce",
        "category": "crm_hris",
        "logo_url": None,
        "description": "CRM líder mundial para gestão de relacionamento",
        "full_description": "Integração planejada com Salesforce para sincronizar dados de candidatos, empresas clientes e processos seletivos entre a plataforma LIA e seu CRM.",
        "status": "coming_soon",
        "industries_recommended": [],
        "metadata": {
            "icon_bg": "bg-blue-500/10",
            "icon_color": "text-blue-600 dark:text-blue-400",
            "icon_letter": "SF",
            "connect_action": "none",
            "capabilities": [
                {"name": "Sync de Contatos", "description": "Candidatos e clientes sincronizados"},
                {"name": "Funil de Vendas", "description": "Oportunidades de recrutamento"},
                {"name": "Relatórios", "description": "Dashboards integrados"},
            ],
            "config_fields": [],
        },
    },
    {
        "provider": "sap-successfactors",
        "label": "SAP SuccessFactors",
        "category": "crm_hris",
        "logo_url": None,
        "description": "HRIS corporativo para gestão de talentos",
        "full_description": "Integração planejada com SAP SuccessFactors para conectar processos de recrutamento com a gestão de capital humano da sua organização.",
        "status": "coming_soon",
        "industries_recommended": [],
        "metadata": {
            "icon_bg": "bg-blue-700/10",
            "icon_color": "text-blue-700 dark:text-blue-300",
            "icon_letter": "SAP",
            "connect_action": "none",
            "capabilities": [
                {"name": "Gestão de Talentos", "description": "Integração com módulo de recrutamento"},
                {"name": "Integração", "description": "Fluxo de admissão automatizado"},
                {"name": "Perfil do Colaborador", "description": "Dados unificados de RH"},
            ],
            "config_fields": [],
        },
    },
    {
        "provider": "workday",
        "label": "Workday",
        "category": "crm_hris",
        "logo_url": None,
        "description": "Plataforma de RH e finanças empresarial",
        "full_description": "Integração planejada com Workday para conectar o recrutamento da plataforma LIA com a gestão de pessoas e processos de admissão da sua organização.",
        "status": "coming_soon",
        "industries_recommended": [],
        "metadata": {
            "icon_bg": "bg-orange-500/10",
            "icon_color": "text-orange-600 dark:text-orange-400",
            "icon_letter": "Wd",
            "connect_action": "none",
            "capabilities": [
                {"name": "Requisição de Vagas", "description": "Criação automática de posições"},
                {"name": "Admissão Digital", "description": "Processo de onboarding integrado"},
                {"name": "Dados de RH", "description": "Sincronização de informações organizacionais"},
            ],
            "config_fields": [],
        },
    },
    {
        "provider": "webhook-custom",
        "label": "Webhook Customizado",
        "category": "mcps_apis",
        "logo_url": None,
        "description": "Notifique sistemas externos via webhooks HTTP",
        "full_description": "Configure webhooks HTTP para notificar seus sistemas quando eventos de recrutamento acontecem na plataforma LIA. Suporta POST com payload JSON customizável e autenticação via headers.",
        "status": "production",
        "industries_recommended": [],
        "metadata": {
            "icon_bg": "bg-gray-500/10",
            "icon_color": "text-gray-600 dark:text-gray-400",
            "icon_letter": "WH",
            "connect_action": "webhook",
            "capabilities": [
                {"name": "Eventos de Candidatos", "description": "Novos candidatos, mudanças de status"},
                {"name": "Eventos de Vagas", "description": "Abertura, fechamento, atualização"},
                {"name": "Eventos de Entrevista", "description": "Agendamento, conclusão, avaliação"},
                {"name": "Payload Customizável", "description": "Formato JSON configurável"},
                {"name": "Retry Automático", "description": "Reenvio em caso de falha"},
            ],
            "config_fields": ["WEBHOOK_URL", "WEBHOOK_SECRET"],
        },
    },
    {
        "provider": "api-rest",
        "label": "API REST",
        "category": "mcps_apis",
        "logo_url": None,
        "description": "Acesso programático à plataforma LIA via API",
        "full_description": "A API REST da plataforma LIA permite acesso programático completo para integração com qualquer sistema. Documentação OpenAPI disponível para desenvolvedores.",
        "status": "production",
        "industries_recommended": [],
        "metadata": {
            "icon_bg": "bg-cyan-500/10",
            "icon_color": "text-cyan-600 dark:text-cyan-400",
            "icon_letter": "API",
            "connect_action": "none",
            "capabilities": [
                {"name": "CRUD de Vagas", "description": "Criação e gestão de posições"},
                {"name": "Gestão de Candidatos", "description": "Busca, criação e atualização"},
                {"name": "Agendamento", "description": "APIs de calendário e entrevistas"},
                {"name": "Webhooks", "description": "Configuração de notificações"},
                {"name": "Autenticação JWT", "description": "Tokens seguros com scopes"},
            ],
            "config_fields": [],
        },
    },
]


def upgrade() -> None:
    """Create table + seed 16 master items canonical (integration-data.ts)."""
    op.create_table(
        "integration_catalog_entries",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("company_id", sa.String(255), nullable=True, index=True),
        sa.Column("is_master_template", sa.Boolean, nullable=False, server_default=sa.text("FALSE"), index=True),
        sa.Column(
            "parent_template_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("integration_catalog_entries.id"),
            nullable=True,
            index=True,
        ),
        sa.Column("data", postgresql.JSONB, nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.text("NOW()")),
        sa.Column("created_by", sa.String(255), nullable=True),
        sa.Column("deleted_at", sa.DateTime, nullable=True, index=True),
    )

    # Composite indexes canonical
    op.create_index(
        "ix_integration_catalog_company_master",
        "integration_catalog_entries",
        ["company_id", "is_master_template"],
    )
    op.create_index(
        "ix_integration_catalog_active",
        "integration_catalog_entries",
        ["deleted_at", "is_master_template"],
    )

    # Seed master canonical (16 items from integration-data.ts canonical)
    import uuid
    import json as _json

    connection = op.get_bind()
    insert_sql = sa.text(
        """
        INSERT INTO integration_catalog_entries
        (id, company_id, is_master_template, parent_template_id, data, created_at, updated_at, created_by, deleted_at)
        VALUES (:id, NULL, TRUE, NULL, CAST(:data AS JSONB), NOW(), NOW(), 'system-seed-2026-05-21', NULL)
        """
    )
    for item in MASTER_ITEMS:
        new_uuid = str(uuid.uuid4())
        connection.execute(
            insert_sql,
            {"id": new_uuid, "data": _json.dumps(item, ensure_ascii=False)},
        )


def downgrade() -> None:
    """Drop table — DATA LOSS de customs canonical."""
    op.drop_index("ix_integration_catalog_active", table_name="integration_catalog_entries")
    op.drop_index("ix_integration_catalog_company_master", table_name="integration_catalog_entries")
    op.drop_table("integration_catalog_entries")
