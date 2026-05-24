/**
 * @deprecated Sprint 4 (catalogos dinamicos 2026-05-21).
 *
 * Este catalogo hardcoded foi substituido pelo catalogo dinamico per-tenant
 * canonical em  (src/hooks/integrations/use-integration-catalog.ts).
 *
 * MIGRACAO EM CURSO:
 *   - Hook canonical: useIntegrationCatalog() → fetch dinamico do DB
 *   - Shape compat: FlatIntegration (em use-integration-catalog.ts) imita
 *     o shape  deste arquivo para migracao incremental
 *   - Schema canonical: status "connected"/"not_configured" → "production";
 *     "coming_soon" segue igual
 *
 * QUEM AINDA USA (a refatorar):
 *   - IntegrationsHub.tsx (refatorado Sprint 4 F4 para hook + fallback)
 *   - IntegrationCard.tsx (mantem shape Integration via FlatIntegration)
 *   - IntegrationDetailDrawer.tsx (mantem shape Integration via FlatIntegration)
 *
 * REMOVER quando F6 (Sprint 4 final consolidate) confirmar 0 consumers.
 */

export type IntegrationStatus = "connected" | "not_configured" | "coming_soon"

export type IntegrationCategory =
  | "ai_models"
  | "ats"
  | "calendar"
  | "communication"
  | "crm_hris"
  | "mcps_apis"

export interface IntegrationCapability {
  name: string
  description: string
}

export interface Integration {
  id: string
  name: string
  shortDescription: string
  fullDescription: string
  category: IntegrationCategory
  status: IntegrationStatus
  iconBg: string
  iconColor: string
  iconLetter: string
  capabilities: IntegrationCapability[]
  configFields?: string[]
  isActiveProvider?: boolean
  /**
   * AI provider only. True when the platform is using a global system env var
   * for this provider because the tenant has no entry in `tenant_llm_configs`.
   * Surfaced as a "Cota compartilhada" badge (P2.3-INT: renamed from Chave do sistema) so users know they share quota and
   * can configure their own key for isolation.
   */
  usingSystemKey?: boolean
  connectAction?: "oauth" | "config" | "webhook" | "none"
}

export interface CategoryInfo {
  id: IntegrationCategory
  label: string
  icon: string
}

export const categories: CategoryInfo[] = [
  { id: "ai_models", label: "Modelos de IA", icon: "brain" },
  { id: "ats", label: "ATS / Applicant Tracking", icon: "briefcase" },
  { id: "calendar", label: "Calendário & Agendamento", icon: "calendar" },
  { id: "communication", label: "Comunicação", icon: "message-circle" },
  { id: "crm_hris", label: "CRM & HRIS", icon: "building" },
  { id: "mcps_apis", label: "MCPs & APIs", icon: "code" },
]

export const integrations: Integration[] = [
  {
    id: "gemini",
    name: "Google Gemini",
    shortDescription: "Modelo de IA principal da plataforma LIA",
    fullDescription:
      "Google Gemini é o provedor de IA padrão da plataforma LIA. Utilizado para análise de currículos, geração de perguntas de entrevista, avaliação de candidatos e interações conversacionais. Suporta modelos Gemini 2.0 Flash e Pro.",
    category: "ai_models",
    status: "connected",
    iconBg: "bg-blue-500/10",
    iconColor: "text-blue-600 dark:text-blue-400",
    iconLetter: "G",
    isActiveProvider: true,
    connectAction: "config",
    capabilities: [
      { name: "Análise de Currículos", description: "Extração e avaliação de competências" },
      { name: "Geração de Perguntas", description: "Perguntas de entrevista personalizadas" },
      { name: "Avaliação de Candidatos", description: "Scoring e ranking inteligente" },
      { name: "Chat Conversacional", description: "Interação natural com recrutadores" },
      { name: "Resumos Automáticos", description: "Síntese de perfis e entrevistas" },
    ],
    configFields: ["GOOGLE_API_KEY"],
  },
  {
    id: "claude",
    name: "Anthropic Claude",
    shortDescription: "Modelo de IA alternativo com raciocínio avançado",
    fullDescription:
      "Anthropic Claude oferece capacidades avançadas de raciocínio e análise. Disponível como provedor alternativo ou fallback na plataforma LIA, com suporte a Claude 3.5 Sonnet e Haiku.",
    category: "ai_models",
    status: "connected",
    iconBg: "bg-orange-500/10",
    iconColor: "text-orange-600 dark:text-orange-400",
    iconLetter: "C",
    isActiveProvider: false,
    connectAction: "config",
    capabilities: [
      { name: "Análise Profunda", description: "Raciocínio complexo sobre candidatos" },
      { name: "Geração de Texto", description: "Comunicações e feedbacks elaborados" },
      { name: "Avaliação Contextual", description: "Análise de aderência cultural" },
      { name: "Fallback Provider", description: "Backup automático quando Gemini indisponível" },
    ],
    configFields: ["ANTHROPIC_API_KEY"],
  },
  {
    id: "openai",
    name: "OpenAI GPT",
    shortDescription: "Modelo de IA com ampla base de conhecimento",
    fullDescription:
      "OpenAI GPT oferece modelos versáteis com ampla base de conhecimento. Disponível como provedor terciário na cadeia de fallback da plataforma LIA, suportando GPT-4o e GPT-4o-mini. Essencial para transcrição de áudio (Whisper STT) e voz da LIA (TTS) nas triagens — sem esta chave, as funcionalidades de voz ficam indisponíveis.",
    category: "ai_models",
    status: "connected",
    iconBg: "bg-emerald-500/10",
    iconColor: "text-emerald-600 dark:text-emerald-400",
    iconLetter: "O",
    isActiveProvider: false,
    connectAction: "config",
    capabilities: [
      { name: "Processamento de Linguagem", description: "Compreensão e geração de texto" },
      { name: "Embeddings", description: "Representações vetoriais para busca semântica" },
      { name: "Function Calling", description: "Integração com ferramentas da plataforma" },
      { name: "Transcrição (Whisper)", description: "STT para áudio de candidatos em triagens" },
      { name: "Voz da LIA (TTS)", description: "Síntese de voz para perguntas da LIA em triagens" },
      { name: "Fallback Provider", description: "Terceiro na cadeia de resiliência" },
    ],
    configFields: ["OPENAI_API_KEY"],
  },
  {
    id: "gupy",
    name: "Gupy",
    shortDescription: "ATS líder no mercado brasileiro",
    fullDescription:
      "Integração com a Gupy, plataforma líder de recrutamento no Brasil. Sincronize vagas, candidatos e etapas do processo seletivo automaticamente com a plataforma LIA.",
    category: "ats",
    status: "not_configured",
    iconBg: "bg-pink-500/10",
    iconColor: "text-pink-600 dark:text-pink-400",
    iconLetter: "Gy",
    connectAction: "config",
    capabilities: [
      { name: "Sync de Vagas", description: "Importação automática de posições abertas" },
      { name: "Sync de Candidatos", description: "Sincronização bidirecional de perfis" },
      { name: "Movimentação de Etapas", description: "Atualização automática de status" },
      { name: "Webhooks", description: "Notificações em tempo real de eventos" },
    ],
    configFields: ["GUPY_API_TOKEN", "GUPY_COMPANY_ID"],
  },
  {
    id: "pandape",
    name: "Pandapé",
    shortDescription: "ATS do grupo InfoJobs para gestão de talentos",
    fullDescription:
      "Integração com Pandapé (InfoJobs) para gestão completa do ciclo de recrutamento. Conecte vagas, candidatos e processos seletivos diretamente à plataforma LIA.",
    category: "ats",
    status: "not_configured",
    iconBg: "bg-green-500/10",
    iconColor: "text-green-600 dark:text-green-400",
    iconLetter: "Pp",
    connectAction: "config",
    capabilities: [
      { name: "Importação de Vagas", description: "Sincronização de posições" },
      { name: "Gestão de Candidatos", description: "Perfis e histórico integrados" },
      { name: "Relatórios", description: "Métricas unificadas de processo" },
    ],
    configFields: ["PANDAPE_API_KEY"],
  },
  {
    id: "merge",
    name: "Merge.dev",
    shortDescription: "API unificada para 40+ ATS e HRIS",
    fullDescription:
      "Merge.dev oferece uma API unificada que conecta a plataforma LIA a mais de 40 sistemas ATS e HRIS, incluindo Greenhouse, Lever, BambooHR e outros. Uma integração, múltiplas plataformas.",
    category: "ats",
    status: "not_configured",
    iconBg: "bg-violet-500/10",
    iconColor: "text-violet-600 dark:text-violet-400",
    iconLetter: "M",
    connectAction: "config",
    capabilities: [
      { name: "Unified API", description: "Uma API para 40+ plataformas ATS/HRIS" },
      { name: "Sync Bidirecional", description: "Dados sincronizados em tempo real" },
      { name: "Webhooks", description: "Eventos de mudança em tempo real" },
      { name: "Normalização de Dados", description: "Schema unificado entre plataformas" },
    ],
    configFields: ["MERGE_API_KEY", "MERGE_ACCOUNT_TOKEN"],
  },
  {
    id: "google-calendar",
    name: "Google Calendar",
    shortDescription: "Agendamento com Google Meet automático",
    fullDescription:
      "Conecte sua conta Google Workspace para criar eventos com link do Google Meet automaticamente ao agendar entrevistas. A integração utiliza OAuth 2.0 para acesso seguro ao calendário.",
    category: "calendar",
    status: "not_configured",
    iconBg: "bg-red-500/10",
    iconColor: "text-red-500 dark:text-red-400",
    iconLetter: "GC",
    connectAction: "oauth",
    capabilities: [
      { name: "Criação de Eventos", description: "Agendamento automático de entrevistas" },
      { name: "Google Meet", description: "Links de videoconferência automáticos" },
      { name: "Verificação de Disponibilidade", description: "Consulta de horários livres" },
      { name: "Notificações", description: "Lembretes automáticos para participantes" },
    ],
  },
  {
    id: "microsoft-calendar",
    name: "Microsoft Calendar",
    shortDescription: "Agendamento via Microsoft Graph / Outlook",
    fullDescription:
      "Integração com Microsoft Calendar via Microsoft Graph API. Configure as credenciais Azure para habilitar agendamento automático de entrevistas pelo Outlook.",
    category: "calendar",
    status: "not_configured",
    iconBg: "bg-sky-500/10",
    iconColor: "text-sky-600 dark:text-sky-400",
    iconLetter: "MC",
    connectAction: "config",
    capabilities: [
      { name: "Agendamento Outlook", description: "Criação de eventos no calendário Outlook" },
      { name: "Teams Meeting", description: "Links de reunião Microsoft Teams" },
      { name: "Disponibilidade", description: "Consulta de agenda dos participantes" },
      { name: "Salas de Reunião", description: "Reserva automática de salas" },
    ],
    configFields: ["AZURE_CLIENT_ID", "AZURE_CLIENT_SECRET", "AZURE_TENANT_ID"],
  },
  {
    id: "teams",
    name: "Microsoft Teams",
    shortDescription: "Notificações e alertas via webhooks do Teams",
    fullDescription:
      "Envie notificações de recrutamento diretamente para canais do Microsoft Teams. Configure webhooks para alertas de novos candidatos, mudanças de status e atualizações de processo seletivo.",
    category: "communication",
    status: "not_configured",
    iconBg: "bg-indigo-500/10",
    iconColor: "text-indigo-600 dark:text-indigo-400",
    iconLetter: "T",
    connectAction: "webhook",
    capabilities: [
      { name: "Notificações de Candidatos", description: "Alertas de novos candidatos" },
      { name: "Alertas de Processo", description: "Mudanças de status em tempo real" },
      { name: "Adaptive Cards", description: "Cards interativos com ações" },
      { name: "Canais Customizados", description: "Diferentes canais por tipo de alerta" },
    ],
    configFields: ["TEAMS_WEBHOOK_URL"],
  },
  {
    id: "whatsapp",
    name: "WhatsApp Business",
    shortDescription: "Comunicação com candidatos via WhatsApp",
    fullDescription:
      "Integração com WhatsApp Business API para comunicação direta com candidatos. Envie convites para entrevistas, atualizações de status e mensagens automatizadas.",
    category: "communication",
    status: "coming_soon",
    iconBg: "bg-green-500/10",
    iconColor: "text-green-600 dark:text-green-400",
    iconLetter: "W",
    connectAction: "none",
    capabilities: [
      { name: "Mensagens Automatizadas", description: "Templates de comunicação" },
      { name: "Convites de Entrevista", description: "Envio direto de agendamentos" },
      { name: "Chatbot", description: "Atendimento automatizado a candidatos" },
    ],
  },
  {
    id: "email-smtp",
    name: "Email / SMTP",
    shortDescription: "Envio de emails transacionais e notificações",
    fullDescription:
      "Configure um servidor SMTP personalizado para envio de emails da plataforma. Personalize templates, remetente e domínio para comunicações com candidatos.",
    category: "communication",
    status: "coming_soon",
    iconBg: "bg-amber-500/10",
    iconColor: "text-amber-600 dark:text-amber-400",
    iconLetter: "E",
    connectAction: "none",
    capabilities: [
      { name: "Emails Transacionais", description: "Confirmações e notificações" },
      { name: "Templates Customizados", description: "Modelos personalizáveis" },
      { name: "Tracking", description: "Rastreamento de abertura e cliques" },
    ],
  },
  {
    id: "salesforce",
    name: "Salesforce",
    shortDescription: "CRM líder mundial para gestão de relacionamento",
    fullDescription:
      "Integração planejada com Salesforce para sincronizar dados de candidatos, empresas clientes e processos seletivos entre a plataforma LIA e seu CRM.",
    category: "crm_hris",
    status: "coming_soon",
    iconBg: "bg-blue-500/10",
    iconColor: "text-blue-600 dark:text-blue-400",
    iconLetter: "SF",
    connectAction: "none",
    capabilities: [
      { name: "Sync de Contatos", description: "Candidatos e clientes sincronizados" },
      { name: "Funil de Vendas", description: "Oportunidades de recrutamento" },
      { name: "Relatórios", description: "Dashboards integrados" },
    ],
  },
  {
    id: "sap-successfactors",
    name: "SAP SuccessFactors",
    shortDescription: "HRIS corporativo para gestão de talentos",
    fullDescription:
      "Integração planejada com SAP SuccessFactors para conectar processos de recrutamento com a gestão de capital humano da sua organização.",
    category: "crm_hris",
    status: "coming_soon",
    iconBg: "bg-blue-700/10",
    iconColor: "text-blue-700 dark:text-blue-300",
    iconLetter: "SAP",
    connectAction: "none",
    capabilities: [
      { name: "Gestão de Talentos", description: "Integração com módulo de recrutamento" },
      { name: "Integração", description: "Fluxo de admissão automatizado" },
      { name: "Perfil do Colaborador", description: "Dados unificados de RH" },
    ],
  },
  {
    id: "workday",
    name: "Workday",
    shortDescription: "Plataforma de RH e finanças empresarial",
    fullDescription:
      "Integração planejada com Workday para conectar o recrutamento da plataforma LIA com a gestão de pessoas e processos de admissão da sua organização.",
    category: "crm_hris",
    status: "coming_soon",
    iconBg: "bg-orange-500/10",
    iconColor: "text-orange-600 dark:text-orange-400",
    iconLetter: "Wd",
    connectAction: "none",
    capabilities: [
      { name: "Requisição de Vagas", description: "Criação automática de posições" },
      { name: "Admissão Digital", description: "Processo de onboarding integrado" },
      { name: "Dados de RH", description: "Sincronização de informações organizacionais" },
    ],
  },
  {
    id: "webhook-custom",
    name: "Webhook Customizado",
    shortDescription: "Notifique sistemas externos via webhooks HTTP",
    fullDescription:
      "Configure webhooks HTTP para notificar seus sistemas quando eventos de recrutamento acontecem na plataforma LIA. Suporta POST com payload JSON customizável e autenticação via headers.",
    category: "mcps_apis",
    status: "not_configured",
    iconBg: "bg-gray-500/10",
    iconColor: "text-gray-600 dark:text-gray-400",
    iconLetter: "WH",
    connectAction: "webhook",
    capabilities: [
      { name: "Eventos de Candidatos", description: "Novos candidatos, mudanças de status" },
      { name: "Eventos de Vagas", description: "Abertura, fechamento, atualização" },
      { name: "Eventos de Entrevista", description: "Agendamento, conclusão, avaliação" },
      { name: "Payload Customizável", description: "Formato JSON configurável" },
      { name: "Retry Automático", description: "Reenvio em caso de falha" },
    ],
    configFields: ["WEBHOOK_URL", "WEBHOOK_SECRET"],
  },
  {
    id: "api-rest",
    name: "API REST",
    shortDescription: "Acesso programático à plataforma LIA via API",
    fullDescription:
      "A API REST da plataforma LIA permite acesso programático completo para integração com qualquer sistema. Documentação OpenAPI disponível para desenvolvedores.",
    category: "mcps_apis",
    status: "connected",
    iconBg: "bg-cyan-500/10",
    iconColor: "text-cyan-600 dark:text-cyan-400",
    iconLetter: "API",
    connectAction: "none",
    capabilities: [
      { name: "CRUD de Vagas", description: "Criação e gestão de posições" },
      { name: "Gestão de Candidatos", description: "Busca, criação e atualização" },
      { name: "Agendamento", description: "APIs de calendário e entrevistas" },
      { name: "Webhooks", description: "Configuração de notificações" },
      { name: "Autenticação JWT", description: "Tokens seguros com scopes" },
    ],
  },
]
