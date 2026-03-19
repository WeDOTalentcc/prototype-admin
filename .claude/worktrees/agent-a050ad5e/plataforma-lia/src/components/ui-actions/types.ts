import type { JobBenefit } from '@/types/benefits'

export type UIComponentType = 
  | "side_panel"
  | "chat_card"
  | "chat_action"
  | "modal"
  | "expandable_prompt"
  | "notification"
  | "inline_form"

export type SidePanelType =
  | "compensation_benefits"
  | "technical_requirements"
  | "behavioral_competencies"
  | "languages"
  | "benefits_detailed"
  | "wsi_questions"
  | "interview_scheduling"
  | "candidate_evaluation"
  | "calibration_feedback"
  | "job_requirements"
  | "candidate_profile"
  | "search_filters"
  | "ats_field_mapping"
  | "ats_sync_status"
  | "email_composer"
  | "whatsapp_composer"

export type ChatCardType =
  | "candidate_summary"
  | "job_summary"
  | "compensation_summary"
  | "interview_confirmation"
  | "wsi_score"
  | "market_analysis"
  | "calibration_sample"
  | "search_results_preview"
  | "progress_tracker"
  | "stage_transition"
  | "email_preview"
  | "whatsapp_preview"
  | "dashboard_metrics"
  | "sync_status"
  | "company_benefits"

export type ChatActionType =
  | "confirm_proceed"
  | "select_option"
  | "quick_feedback"
  | "approve_reject"
  | "schedule_options"
  | "edit_data"
  | "send_message"
  | "export_data"

export interface UIAction {
  action_id: string
  component_type: UIComponentType
  component_subtype: string
  title: string
  description?: string
  data: Record<string, unknown>
  schema?: Record<string, unknown>
  callback_action?: string
  source_agent?: string
  conversation_id?: string
  priority: number
  auto_open: boolean
  dismissible: boolean
  expires_at?: string
  created_at: string
}

export interface TechRequirement {
  id: string
  name: string
  level: "Básico" | "Intermediário" | "Avançado" | "Expert"
  required: boolean
  category: "languages" | "frameworks" | "databases" | "cloud_devops" | "tools"
}

export type { JobBenefit } from '@/types/benefits'
export type Benefit = JobBenefit

export interface Competency {
  id: string
  name: string
  description: string
  level: number
  behaviors?: string[]
  questions?: string[]
}

export interface Language {
  id: string
  name: string
  code: string
  level: "Básico" | "Intermediário" | "Avançado" | "Fluente" | "Nativo"
  required: boolean
}

export interface WSIQuestion {
  id: string
  question: string
  bloom_level: "Lembrar" | "Entender" | "Aplicar" | "Analisar" | "Avaliar" | "Criar"
  dreyfus_level: "Novato" | "Iniciante Avançado" | "Competente" | "Proficiente" | "Expert"
  competency: string
  expected_answer?: string
  time_estimate?: number
}

export interface InterviewSlot {
  id: string
  date: string
  time: string
  duration: number
  type: "presencial" | "teams" | "meet" | "telefone"
  available: boolean
}

export interface CalibrationCandidate {
  id: string
  name: string
  title: string
  location: string
  experience_years: number
  skills: string[]
  match_score: number
  avatar_url?: string
}

export interface CompensationData {
  salary_min: number
  salary_max: number
  bonus_min?: number
  bonus_max?: number
  bonus_criteria?: string
  benefits: Benefit[]
  observations?: string
}

export interface TechnicalRequirementsData {
  requirements: TechRequirement[]
}

export interface BehavioralCompetenciesData {
  competencies: Competency[]
}

export interface LanguagesData {
  languages: Language[]
}

export interface WSIQuestionsData {
  questions: WSIQuestion[]
}

export interface InterviewSchedulingData {
  candidate_id: string
  candidate_name: string
  selected_slot?: InterviewSlot
  interviewers: string[]
  notes?: string
}

export interface CalibrationFeedbackData {
  samples: CalibrationCandidate[]
  feedback: {
    approved: string[]
    rejected: string[]
    maybe: string[]
  }
  general_feedback?: string
}

export interface PanelSubmitData {
  panel_type: SidePanelType
  data: 
    | CompensationData 
    | TechnicalRequirementsData 
    | BehavioralCompetenciesData
    | LanguagesData
    | WSIQuestionsData
    | InterviewSchedulingData
    | CalibrationFeedbackData
}

export const BENEFITS_CATALOG: JobBenefit[] = [
  { id: "vale_refeicao", name: "Vale Refeição", description: '', category: 'food', value_type: 'monetary', seniority_levels: ['all'], waiting_period_days: 0, is_mandatory: false, is_active: true, is_highlighted: false, is_discount: false, enabled: false },
  { id: "vale_alimentacao", name: "Vale Alimentação", description: '', category: 'food', value_type: 'monetary', seniority_levels: ['all'], waiting_period_days: 0, is_mandatory: false, is_active: true, is_highlighted: false, is_discount: false, enabled: false },
  { id: "vale_transporte", name: "Vale Transporte", description: '', category: 'transport', value_type: 'informative', seniority_levels: ['all'], waiting_period_days: 0, is_mandatory: false, is_active: true, is_highlighted: false, is_discount: false, enabled: false },
  { id: "plano_saude", name: "Plano de Saúde", description: '', category: 'health', value_type: 'informative', seniority_levels: ['all'], waiting_period_days: 0, is_mandatory: false, is_active: true, is_highlighted: false, is_discount: false, enabled: false },
  { id: "plano_odonto", name: "Plano Odontológico", description: '', category: 'health', value_type: 'informative', seniority_levels: ['all'], waiting_period_days: 0, is_mandatory: false, is_active: true, is_highlighted: false, is_discount: false, enabled: false },
  { id: "seguro_vida", name: "Seguro de Vida", description: '', category: 'health', value_type: 'informative', seniority_levels: ['all'], waiting_period_days: 0, is_mandatory: false, is_active: true, is_highlighted: false, is_discount: false, enabled: false },
  { id: "gympass", name: "Gympass / Wellhub", description: '', category: 'health', value_type: 'informative', seniority_levels: ['all'], waiting_period_days: 0, is_mandatory: false, is_active: true, is_highlighted: false, is_discount: false, enabled: false },
  { id: "totalpass", name: "TotalPass", description: '', category: 'health', value_type: 'informative', seniority_levels: ['all'], waiting_period_days: 0, is_mandatory: false, is_active: true, is_highlighted: false, is_discount: false, enabled: false },
  { id: "stock_options", name: "Stock Options / Equity", description: '', category: 'financial', value_type: 'informative', seniority_levels: ['all'], waiting_period_days: 0, is_mandatory: false, is_active: true, is_highlighted: false, is_discount: false, enabled: false },
  { id: "ppr_plr", name: "PPR / PLR", description: '', category: 'financial', value_type: 'monetary', seniority_levels: ['all'], waiting_period_days: 0, is_mandatory: false, is_active: true, is_highlighted: false, is_discount: false, enabled: false },
  { id: "auxilio_home_office", name: "Auxílio Home Office", description: '', category: 'quality_life', value_type: 'monetary', seniority_levels: ['all'], waiting_period_days: 0, is_mandatory: false, is_active: true, is_highlighted: false, is_discount: false, enabled: false },
  { id: "auxilio_educacao", name: "Auxílio Educação", description: '', category: 'education', value_type: 'monetary', seniority_levels: ['all'], waiting_period_days: 0, is_mandatory: false, is_active: true, is_highlighted: false, is_discount: false, enabled: false },
  { id: "auxilio_creche", name: "Auxílio Creche", description: '', category: 'family', value_type: 'monetary', seniority_levels: ['all'], waiting_period_days: 0, is_mandatory: false, is_active: true, is_highlighted: false, is_discount: false, enabled: false },
  { id: "day_off_aniversario", name: "Day Off de Aniversário", description: '', category: 'quality_life', value_type: 'informative', seniority_levels: ['all'], waiting_period_days: 0, is_mandatory: false, is_active: true, is_highlighted: false, is_discount: false, enabled: false },
  { id: "licenca_parental", name: "Licença Parental Estendida", description: '', category: 'family', value_type: 'informative', seniority_levels: ['all'], waiting_period_days: 0, is_mandatory: false, is_active: true, is_highlighted: false, is_discount: false, enabled: false },
  { id: "previdencia_privada", name: "Previdência Privada", description: '', category: 'financial', value_type: 'informative', seniority_levels: ['all'], waiting_period_days: 0, is_mandatory: false, is_active: true, is_highlighted: false, is_discount: false, enabled: false },
  { id: "carro_empresa", name: "Carro da Empresa", description: '', category: 'transport', value_type: 'informative', seniority_levels: ['all'], waiting_period_days: 0, is_mandatory: false, is_active: true, is_highlighted: false, is_discount: false, enabled: false },
  { id: "estacionamento", name: "Estacionamento", description: '', category: 'transport', value_type: 'informative', seniority_levels: ['all'], waiting_period_days: 0, is_mandatory: false, is_active: true, is_highlighted: false, is_discount: false, enabled: false },
  { id: "celular_corporativo", name: "Celular Corporativo", description: '', category: 'quality_life', value_type: 'informative', seniority_levels: ['all'], waiting_period_days: 0, is_mandatory: false, is_active: true, is_highlighted: false, is_discount: false, enabled: false },
  { id: "notebook", name: "Notebook / Equipamentos", description: '', category: 'quality_life', value_type: 'informative', seniority_levels: ['all'], waiting_period_days: 0, is_mandatory: false, is_active: true, is_highlighted: false, is_discount: false, enabled: false },
  { id: "horario_flexivel", name: "Horário Flexível", description: '', category: 'quality_life', value_type: 'informative', seniority_levels: ['all'], waiting_period_days: 0, is_mandatory: false, is_active: true, is_highlighted: false, is_discount: false, enabled: false },
  { id: "sexta_curta", name: "Sexta-feira Curta", description: '', category: 'quality_life', value_type: 'informative', seniority_levels: ['all'], waiting_period_days: 0, is_mandatory: false, is_active: true, is_highlighted: false, is_discount: false, enabled: false },
  { id: "ferias_extra", name: "Férias Extras", description: '', category: 'quality_life', value_type: 'informative', seniority_levels: ['all'], waiting_period_days: 0, is_mandatory: false, is_active: true, is_highlighted: false, is_discount: false, enabled: false },
  { id: "trabalho_remoto", name: "Trabalho 100% Remoto", description: '', category: 'quality_life', value_type: 'informative', seniority_levels: ['all'], waiting_period_days: 0, is_mandatory: false, is_active: true, is_highlighted: false, is_discount: false, enabled: false },
  { id: "trabalho_hibrido", name: "Trabalho Híbrido", description: '', category: 'quality_life', value_type: 'informative', seniority_levels: ['all'], waiting_period_days: 0, is_mandatory: false, is_active: true, is_highlighted: false, is_discount: false, enabled: false },
  { id: "auxilio_idiomas", name: "Auxílio Idiomas", description: '', category: 'education', value_type: 'monetary', seniority_levels: ['all'], waiting_period_days: 0, is_mandatory: false, is_active: true, is_highlighted: false, is_discount: false, enabled: false },
  { id: "auxilio_saude_mental", name: "Auxílio Saúde Mental", description: '', category: 'health', value_type: 'informative', seniority_levels: ['all'], waiting_period_days: 0, is_mandatory: false, is_active: true, is_highlighted: false, is_discount: false, enabled: false },
  { id: "pet_friendly", name: "Pet Friendly", description: '', category: 'quality_life', value_type: 'informative', seniority_levels: ['all'], waiting_period_days: 0, is_mandatory: false, is_active: true, is_highlighted: false, is_discount: false, enabled: false },
]

export const TECHNOLOGY_CATALOG = {
  languages: [
    "JavaScript", "TypeScript", "Python", "Java", "C#", "Go", "Rust", "Ruby", "PHP", "Swift",
    "Kotlin", "Scala", "C++", "C", "R", "Julia", "Dart", "Elixir", "Clojure", "Haskell"
  ],
  frameworks: [
    "React", "Next.js", "Vue.js", "Angular", "Node.js", "Express", "FastAPI", "Django", "Flask",
    "Spring Boot", ".NET Core", "Ruby on Rails", "Laravel", "NestJS", "Svelte", "Nuxt.js",
    "Remix", "Astro", "Gatsby", "Electron"
  ],
  databases: [
    "PostgreSQL", "MySQL", "MongoDB", "Redis", "Elasticsearch", "DynamoDB", "Cassandra",
    "Oracle", "SQL Server", "SQLite", "Neo4j", "InfluxDB", "Supabase", "Firebase", "PlanetScale"
  ],
  cloud_devops: [
    "AWS", "Azure", "GCP", "Docker", "Kubernetes", "Terraform", "Jenkins", "GitHub Actions",
    "GitLab CI", "CircleCI", "Vercel", "Netlify", "Heroku", "DigitalOcean", "Cloudflare"
  ],
  tools: [
    "Git", "Jira", "Confluence", "Figma", "Postman", "VS Code", "IntelliJ", "Grafana",
    "Prometheus", "Datadog", "New Relic", "Sentry", "Segment", "Amplitude", "Mixpanel"
  ]
}

export const COMPETENCIES_CATALOG: Competency[] = [
  {
    id: "communication",
    name: "Comunicação",
    description: "Capacidade de transmitir ideias de forma clara e efetiva",
    level: 3,
    behaviors: [
      "Articula pensamentos de forma clara",
      "Adapta comunicação ao público",
      "Pratica escuta ativa"
    ],
    questions: [
      "Conte uma situação em que precisou explicar algo técnico para alguém não técnico.",
      "Como você lida com mal-entendidos na comunicação?"
    ]
  },
  {
    id: "teamwork",
    name: "Trabalho em Equipe",
    description: "Habilidade de colaborar efetivamente com outros",
    level: 3,
    behaviors: [
      "Contribui proativamente para o time",
      "Aceita e oferece feedback construtivo",
      "Celebra conquistas coletivas"
    ],
    questions: [
      "Descreva um projeto de sucesso onde trabalhou em equipe.",
      "Como você resolve conflitos dentro do time?"
    ]
  },
  {
    id: "leadership",
    name: "Liderança",
    description: "Capacidade de influenciar e guiar outros",
    level: 3,
    behaviors: [
      "Inspira e motiva pessoas",
      "Toma decisões difíceis quando necessário",
      "Desenvolve outros profissionais"
    ],
    questions: [
      "Conte sobre uma vez que liderou uma iniciativa ou projeto.",
      "Como você motiva pessoas em momentos difíceis?"
    ]
  },
  {
    id: "problem_solving",
    name: "Resolução de Problemas",
    description: "Habilidade de analisar e resolver problemas complexos",
    level: 3,
    behaviors: [
      "Identifica root cause de problemas",
      "Propõe soluções criativas",
      "Avalia trade-offs de diferentes abordagens"
    ],
    questions: [
      "Descreva um problema complexo que você resolveu recentemente.",
      "Como você aborda problemas que nunca viu antes?"
    ]
  },
  {
    id: "adaptability",
    name: "Adaptabilidade",
    description: "Flexibilidade para se ajustar a mudanças",
    level: 3,
    behaviors: [
      "Aceita mudanças positivamente",
      "Aprende rapidamente novas ferramentas",
      "Mantém produtividade sob incerteza"
    ],
    questions: [
      "Conte sobre uma mudança significativa que você enfrentou no trabalho.",
      "Como você lida com prioridades que mudam constantemente?"
    ]
  },
  {
    id: "creativity",
    name: "Criatividade",
    description: "Capacidade de pensar de forma inovadora",
    level: 3,
    behaviors: [
      "Propõe ideias originais",
      "Questiona o status quo",
      "Conecta conceitos de áreas diferentes"
    ],
    questions: [
      "Descreva uma solução criativa que você implementou.",
      "Como você estimula sua criatividade?"
    ]
  },
  {
    id: "time_management",
    name: "Gestão de Tempo",
    description: "Organização e priorização eficiente do tempo",
    level: 3,
    behaviors: [
      "Prioriza tarefas por impacto",
      "Cumpre prazos consistentemente",
      "Evita procrastinação"
    ],
    questions: [
      "Como você organiza suas tarefas diárias?",
      "Conte sobre uma vez que teve que gerenciar múltiplos prazos apertados."
    ]
  },
  {
    id: "critical_thinking",
    name: "Pensamento Crítico",
    description: "Análise objetiva e avaliação de informações",
    level: 3,
    behaviors: [
      "Questiona pressupostos",
      "Avalia evidências objetivamente",
      "Identifica vieses em argumentos"
    ],
    questions: [
      "Descreva uma decisão que você tomou baseada em análise de dados.",
      "Como você avalia a qualidade de informações que recebe?"
    ]
  },
  {
    id: "emotional_intelligence",
    name: "Inteligência Emocional",
    description: "Consciência e gestão de emoções próprias e de outros",
    level: 3,
    behaviors: [
      "Demonstra empatia genuína",
      "Controla reações sob pressão",
      "Constrói relacionamentos positivos"
    ],
    questions: [
      "Como você lida com críticas ao seu trabalho?",
      "Conte sobre uma situação em que precisou gerenciar emoções no trabalho."
    ]
  },
  {
    id: "autonomy",
    name: "Autonomia",
    description: "Capacidade de trabalhar de forma independente",
    level: 3,
    behaviors: [
      "Toma iniciativa sem esperar instruções",
      "Resolve problemas de forma independente",
      "Busca recursos e informações proativamente"
    ],
    questions: [
      "Descreva um projeto que você conduziu de forma autônoma.",
      "Como você decide quando pedir ajuda versus resolver sozinho?"
    ]
  },
  {
    id: "attention_to_detail",
    name: "Atenção aos Detalhes",
    description: "Cuidado e precisão na execução de tarefas",
    level: 3,
    behaviors: [
      "Revisa trabalho antes de entregar",
      "Identifica erros e inconsistências",
      "Mantém organização em documentações"
    ],
    questions: [
      "Como você garante qualidade no seu trabalho?",
      "Conte sobre um erro que você identificou antes de ir para produção."
    ]
  },
  {
    id: "customer_focus",
    name: "Foco no Cliente",
    description: "Orientação para satisfação e sucesso do cliente",
    level: 3,
    behaviors: [
      "Entende necessidades do cliente",
      "Busca feedback proativamente",
      "Antecipa problemas do cliente"
    ],
    questions: [
      "Descreva como você garantiu uma ótima experiência para um cliente.",
      "Como você lida com clientes insatisfeitos?"
    ]
  },
  {
    id: "strategic_thinking",
    name: "Pensamento Estratégico",
    description: "Visão de longo prazo e planejamento",
    level: 3,
    behaviors: [
      "Considera implicações de longo prazo",
      "Alinha ações com objetivos maiores",
      "Antecipa tendências e mudanças"
    ],
    questions: [
      "Como você alinha seu trabalho diário com objetivos estratégicos?",
      "Conte sobre uma decisão estratégica importante que você tomou."
    ]
  },
  {
    id: "resilience",
    name: "Resiliência",
    description: "Capacidade de se recuperar de adversidades",
    level: 3,
    behaviors: [
      "Mantém otimismo sob pressão",
      "Aprende com fracassos",
      "Persiste diante de obstáculos"
    ],
    questions: [
      "Conte sobre um grande fracasso e como você se recuperou.",
      "Como você mantém motivação em projetos longos e difíceis?"
    ]
  }
]

export const LANGUAGES_CATALOG = [
  { code: "en", name: "Inglês", flag: "🇺🇸" },
  { code: "es", name: "Espanhol", flag: "🇪🇸" },
  { code: "pt", name: "Português", flag: "🇧🇷" },
  { code: "fr", name: "Francês", flag: "🇫🇷" },
  { code: "de", name: "Alemão", flag: "🇩🇪" },
  { code: "it", name: "Italiano", flag: "🇮🇹" },
  { code: "zh", name: "Chinês (Mandarim)", flag: "🇨🇳" },
  { code: "ja", name: "Japonês", flag: "🇯🇵" },
  { code: "ko", name: "Coreano", flag: "🇰🇷" },
  { code: "ru", name: "Russo", flag: "🇷🇺" },
  { code: "ar", name: "Árabe", flag: "🇸🇦" },
  { code: "hi", name: "Hindi", flag: "🇮🇳" },
  { code: "nl", name: "Holandês", flag: "🇳🇱" },
  { code: "pl", name: "Polonês", flag: "🇵🇱" },
  { code: "tr", name: "Turco", flag: "🇹🇷" },
  { code: "sv", name: "Sueco", flag: "🇸🇪" },
  { code: "he", name: "Hebraico", flag: "🇮🇱" },
  { code: "th", name: "Tailandês", flag: "🇹🇭" },
  { code: "vi", name: "Vietnamita", flag: "🇻🇳" },
  { code: "uk", name: "Ucraniano", flag: "🇺🇦" }
]

export const WSI_TEMPLATES = {
  tech: [
    {
      question: "Descreva como você abordaria a arquitetura de um sistema de alta disponibilidade.",
      bloom_level: "Criar" as const,
      dreyfus_level: "Proficiente" as const,
      competency: "Arquitetura de Sistemas",
      time_estimate: 15
    },
    {
      question: "Explique um bug complexo que você debugou e como chegou à solução.",
      bloom_level: "Analisar" as const,
      dreyfus_level: "Competente" as const,
      competency: "Resolução de Problemas",
      time_estimate: 10
    },
    {
      question: "Como você faria o code review de um PR com 500+ linhas?",
      bloom_level: "Avaliar" as const,
      dreyfus_level: "Competente" as const,
      competency: "Qualidade de Código",
      time_estimate: 10
    }
  ],
  sales: [
    {
      question: "Simule como você conduziria uma discovery call com um prospect enterprise.",
      bloom_level: "Aplicar" as const,
      dreyfus_level: "Competente" as const,
      competency: "Discovery & Qualificação",
      time_estimate: 15
    },
    {
      question: "O cliente diz que está satisfeito com a solução atual. Como você responde?",
      bloom_level: "Analisar" as const,
      dreyfus_level: "Proficiente" as const,
      competency: "Tratamento de Objeções",
      time_estimate: 10
    }
  ],
  leadership: [
    {
      question: "Um membro sênior do seu time está desmotivado. Como você aborda a situação?",
      bloom_level: "Avaliar" as const,
      dreyfus_level: "Proficiente" as const,
      competency: "Gestão de Pessoas",
      time_estimate: 15
    },
    {
      question: "Você precisa comunicar uma mudança impopular para o time. Como faz isso?",
      bloom_level: "Criar" as const,
      dreyfus_level: "Proficiente" as const,
      competency: "Comunicação de Liderança",
      time_estimate: 10
    }
  ],
  hr: [
    {
      question: "Um funcionário reporta um conflito com seu gestor direto. Quais são seus próximos passos?",
      bloom_level: "Avaliar" as const,
      dreyfus_level: "Competente" as const,
      competency: "Resolução de Conflitos",
      time_estimate: 15
    }
  ],
  marketing: [
    {
      question: "Desenhe uma campanha de lançamento para um produto B2B SaaS.",
      bloom_level: "Criar" as const,
      dreyfus_level: "Proficiente" as const,
      competency: "Planejamento de Campanhas",
      time_estimate: 20
    }
  ],
  finance: [
    {
      question: "Analise este demonstrativo financeiro e identifique os principais pontos de atenção.",
      bloom_level: "Analisar" as const,
      dreyfus_level: "Competente" as const,
      competency: "Análise Financeira",
      time_estimate: 15
    }
  ],
  operations: [
    {
      question: "Projete um processo de onboarding de clientes para uma empresa SaaS.",
      bloom_level: "Criar" as const,
      dreyfus_level: "Competente" as const,
      competency: "Design de Processos",
      time_estimate: 20
    }
  ]
}
