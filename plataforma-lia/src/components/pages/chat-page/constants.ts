import {
  Plus, Users, TrendingUp, Network, Settings, Target, Workflow, Database, BarChart3, Shield,
  DollarSign, Heart, Building, Clock, Laptop, Globe, FileText, Edit, CheckCircle, X,
  Search, Calendar, Filter, Phone, Download, ClipboardList, Copy, Brain, Zap, Lightbulb
} from "lucide-react"
import type { Message, AgentData, AgentActivity } from "./types"

const mockAgents: AgentData[] = [
  {
    id: "job-intake",
    name: "Job Intake Agent",
    icon: "📋",
    description: "Criação de vagas e JD",
    status: "active",
    actionsToday: 12,
    lastActivity: "Criou JD para Gerente de Projetos",
    lastActivityTime: "há 2 min"
  },
  {
    id: "sourcing",
    name: "Sourcing Agent",
    icon: "🔍",
    description: "Busca de candidatos",
    status: "active",
    actionsToday: 47,
    lastActivity: "Encontrou 12 candidatos para Diretor de TI",
    lastActivityTime: "há 3 min"
  },
  {
    id: "screening",
    name: "Screening Agent",
    icon: "📝",
    description: "Triagem e análise",
    status: "active",
    actionsToday: 23,
    lastActivity: "Analisou CV de Carlos Mendonça - Score 94",
    lastActivityTime: "há 5 min"
  },
  {
    id: "scheduling",
    name: "Scheduling Agent",
    icon: "📅",
    description: "Agendamento",
    status: "idle",
    actionsToday: 8,
    lastActivity: "Agendou entrevista para amanhã 14h",
    lastActivityTime: "há 15 min"
  },
  {
    id: "communication",
    name: "Communication Agent",
    icon: "📧",
    description: "Emails e mensagens",
    status: "active",
    actionsToday: 34,
    lastActivity: "Enviou convite de entrevista para 3 candidatos",
    lastActivityTime: "há 8 min"
  },
  {
    id: "analytics",
    name: "Analytics Agent",
    icon: "📊",
    description: "Métricas e KPIs",
    status: "idle",
    actionsToday: 5,
    lastActivity: "Gerou relatório semanal de pipeline",
    lastActivityTime: "há 1h"
  },
  {
    id: "assistant",
    name: "Recruiter Assistant",
    icon: "🤖",
    description: "Briefing e tarefas",
    status: "active",
    actionsToday: 15,
    lastActivity: "Preparou briefing para vaga de Dev Senior",
    lastActivityTime: "há 12 min"
  }
]

const mockActivities: AgentActivity[] = [
  {
    id: "0",
    agentId: "job-intake",
    agentIcon: "📋",
    agentName: "Job Intake",
    action: "Criou nova vaga de Gerente de Projetos com JD completo",
    timestamp: "10:35",
    status: "success"
  },
  {
    id: "1",
    agentId: "sourcing",
    agentIcon: "🔍",
    agentName: "Sourcing",
    action: "Encontrou 12 novos candidatos matching para Diretor de TI",
    timestamp: "10:32",
    status: "success"
  },
  {
    id: "2",
    agentId: "screening",
    agentIcon: "📝",
    agentName: "Screening",
    action: "Finalizou análise de 5 CVs - 3 aprovados para entrevista",
    timestamp: "10:28",
    status: "success"
  },
  {
    id: "3",
    agentId: "communication",
    agentIcon: "📧",
    agentName: "Communication",
    action: "Enviou email de follow-up para Patricia Santos",
    timestamp: "10:25",
    status: "success"
  },
  {
    id: "4",
    agentId: "scheduling",
    agentIcon: "📅",
    agentName: "Scheduling",
    action: "Confirmou entrevista com Carlos Mendonça - 23/02 às 14h",
    timestamp: "10:18",
    status: "success"
  },
  {
    id: "5",
    agentId: "assistant",
    agentIcon: "🤖",
    agentName: "Assistant",
    action: "Criou job description para Dev Senior React",
    timestamp: "10:05",
    status: "success"
  },
  {
    id: "6",
    agentId: "analytics",
    agentIcon: "📊",
    agentName: "Analytics",
    action: "Atualizou métricas do funil - Time-to-hire: 23 dias",
    timestamp: "09:45",
    status: "success"
  },
  {
    id: "7",
    agentId: "sourcing",
    agentIcon: "🔍",
    agentName: "Sourcing",
    action: "Iniciou busca ativa no LinkedIn para 3 vagas",
    timestamp: "09:30",
    status: "pending"
  },
  {
    id: "8",
    agentId: "screening",
    agentIcon: "📝",
    agentName: "Screening",
    action: "Pré-qualificou 8 candidatos da base interna",
    timestamp: "09:15",
    status: "success"
  }
]

// Nova conversa vazia para demonstrar layout estilo ChatGPT
const emptyConversation: Message[] = []

const modernConversation: Message[] = [
  {
    id: 1,
    sender: "lia",
    content: "Olá! Vejo que você deseja criar uma nova vaga. Vamos começar a jornada de abertura da posição de Diretor de TI. Para criar a vaga perfeita, preciso entender alguns detalhes. Qual é o contexto organizacional desta posição?",
    timestamp: "09:00",
    type: "action",
    actions: [
      { label: "Nova posição na estrutura", icon: Plus, variant: "secondary" },
      { label: "Substituição de colaborador", icon: Users, variant: "secondary" },
      { label: "Expansão da equipe", icon: TrendingUp, variant: "secondary" }
    ]
  },
  {
    id: 2,
    sender: "user",
    content: "É uma nova posição na estrutura. Estamos expandindo a área de TI e precisamos de um diretor para liderar a transformação digital da empresa.",
    timestamp: "09:02",
    type: "text"
  },
  {
    id: 3,
    sender: "lia",
    content: "Perfeito! Uma nova posição estratégica para transformação digital. Entendi que vocês estão expandindo e precisam de liderança. Agora preciso mapear a estrutura organizacional atual para posicionar essa nova direção corretamente. Vamos começar analisando onde essa posição se encaixa?",
    timestamp: "09:03",
    type: "action",
    actions: [
      { label: "Ver Estrutura Atual", icon: Network, variant: "secondary" },
      { label: "Mapear Organograma", icon: Users, variant: "secondary" },
      { label: "Analisar Gaps", icon: Target, variant: "secondary" }
    ],
    contextData: {
      type: "org-structure-analysis",
      title: "Análise da Estrutura Organizacional",
      data: {
        company_overview: {
          size: "Médio porte (500-1000 funcionários)",
          industry: "Tecnologia e Serviços",
          current_tech_team: 45,
          growth_stage: "Expansão"
        },
        current_structure: {
          tech_leadership: [
            { role: "CTO", name: "Existente", team_size: 45, focus: "Estratégia e Visão" },
            { role: "Tech Leads", count: 3, focus: "Desenvolvimento, Infra, Produto" }
          ],
          missing_layer: {
            role: "Diretor de TI",
            purpose: "Ponte entre estratégia (CTO) e execução (Tech Leads)",
            impact: "Transformação Digital + Gestão Operacional"
          }
        },
        growth_projection: {
          current_team: 45,
          projected_6months: 65,
          projected_12months: 85,
          new_departments: ["Segurança", "Dados & Analytics", "Automação"]
        },
        reporting_structure: {
          reports_to: "CTO",
          direct_reports: ["Gerentes de TI", "Tech Leads", "Coordenadores"],
          matrix_relationships: ["Head de Produto", "Head de Operações"]
        }
      }
    }
  },
  {
    id: 4,
    sender: "user",
    content: "Vamos mapear a estrutura atual. Preciso entender melhor como isso se encaixa na nossa organização.",
    timestamp: "09:05",
    type: "text"
  },
  {
    id: 5,
    sender: "lia",
    content: "Perfeito! Identifiquei que vocês precisam de uma nova camada de liderança entre o CTO e os Tech Leads. Agora vou definir o escopo exato desta posição. Qual será o foco principal do Diretor de TI?",
    timestamp: "09:07",
    type: "action",
    actions: [
      { label: "Transformação Digital", icon: Workflow, variant: "secondary" },
      { label: "Gestão Operacional", icon: Settings, variant: "secondary" },
      { label: "Crescimento da Equipe", icon: Users, variant: "secondary" }
    ],
    contextData: {
      type: "role-scope-definition",
      title: "Definição do Escopo da Posição",
      data: {
        role_focus: "Diretor de TI - Transformação Digital",
        key_responsibilities: [
          "Liderar iniciativas de transformação digital",
          "Gerenciar operações de TI do dia a dia",
          "Escalar a equipe de 45 para 85+ pessoas",
          "Implementar novos departamentos especializados"
        ]
      }
    }
  },
  {
    id: 6,
    sender: "user",
    content: "O foco principal deve ser transformação digital, mas também precisa cuidar da gestão operacional.",
    timestamp: "09:09",
    type: "text"
  },
  {
    id: 7,
    sender: "lia",
    content: "Entendi! Um perfil híbrido: estratégico para transformação digital + operacional para gestão do dia a dia. Agora preciso mapear as competências técnicas necessárias. Quais tecnologias são prioritárias?",
    timestamp: "09:11",
    type: "action",
    actions: [
      { label: "Cloud & Infrastructure", icon: Database, variant: "secondary" },
      { label: "Data & Analytics", icon: BarChart3, variant: "secondary" },
      { label: "Security & Compliance", icon: Shield, variant: "secondary" }
    ]
  },
  {
    id: 8,
    sender: "user",
    content: "Todas são importantes, mas cloud e infrastructure são críticos para o crescimento.",
    timestamp: "09:13",
    type: "text"
  },
  {
    id: 9,
    sender: "lia",
    content: "Perfeito! Cloud-first strategy. Agora vou mapear as competências comportamentais essenciais para liderar uma transformação dessa magnitude. Que tipo de liderança vocês buscam?",
    timestamp: "09:15",
    type: "action",
    actions: [
      { label: "Líder Transformacional", icon: Lightbulb, variant: "secondary" },
      { label: "Gestor Execution-Focused", icon: Target, variant: "secondary" },
      { label: "Coach de Times", icon: Users, variant: "secondary" }
    ]
  },
  {
    id: 10,
    sender: "user",
    content: "Precisamos de um líder transformacional que também seja focado em execução.",
    timestamp: "09:17",
    type: "text"
  },
  {
    id: 11,
    sender: "lia",
    content: "Excelente combinação! Visionário + executor. Agora preciso definir o modelo de trabalho. Como será a estrutura híbrida?",
    timestamp: "09:18",
    type: "action",
    actions: [
      { label: "3 dias presencial", icon: Building, variant: "secondary" },
      { label: "Flexibilidade total", icon: Clock, variant: "secondary" },
      { label: "Remote-first", icon: Laptop, variant: "secondary" }
    ],
    contextData: {
      type: "work-arrangement",
      title: "Modelo de Trabalho Híbrido",
      data: {
        arrangement: "Híbrido - 3 dias presencial",
        office_days: ["Terça", "Quarta", "Quinta"],
        home_office_days: ["Segunda", "Sexta"],
        flexibility: "Core hours 10h-16h",
        benefits: "Home office setup + auxílio combustível"
      }
    }
  },
  {
    id: 12,
    sender: "user",
    content: "3 dias presencial funciona bem. É importante ter presença física para liderar a transformação.",
    timestamp: "09:20",
    type: "text"
  },
  {
    id: 12.5,
    sender: "lia",
    content: "Ótimo! Agora preciso definir o tipo de visibilidade desta vaga. Qual será o nível de confidencialidade?",
    timestamp: "09:20:30",
    type: "action",
    actions: [
      { label: "Vaga Pública", icon: Globe, variant: "secondary" },
      { label: "Vaga Interna", icon: Building, variant: "secondary" },
      { label: "Vaga Confidencial", icon: Shield, variant: "secondary" }
    ],
    contextData: {
      type: "job-visibility",
      title: "Tipo de Vaga e Confidencialidade",
      data: {
        options: [
          {
            type: "public",
            label: "Vaga Pública",
            icon: "Globe",
            description: "Todos os recrutadores da empresa podem visualizar",
            features: ["Visível para toda equipe de RH", "Pode ser publicada em job boards", "Candidatos externos podem se candidatar"]
          },
          {
            type: "internal",
            label: "Vaga Interna",
            icon: "Building",
            description: "Só equipe interna, não publica em job boards",
            features: ["Visível apenas para colaboradores", "Não é publicada externamente", "Prioriza talentos internos"]
          },
          {
            type: "confidential",
            label: "Vaga Confidencial",
            icon: "Shield",
            description: "Só você e pessoas autorizadas podem ver",
            features: ["Acesso restrito por lista", "Nome da empresa pode ser ocultado", "Ideal para substituições sensíveis"]
          }
        ],
        current_selection: null,
        access_list: [],
        masked_company_name: null
      }
    }
  },
  {
    id: 12.6,
    sender: "user",
    content: "Vamos com Vaga Pública. Queremos atrair o máximo de candidatos qualificados.",
    timestamp: "09:20:45",
    type: "text"
  },
  {
    id: 13,
    sender: "lia",
    content: "Perfeito! Vaga configurada como pública - todos os recrutadores poderão visualizar e será publicada nos job boards. Agora tenho tudo mapeado: estrutura, hierarquia, escopo, competências técnicas e comportamentais. Vou consolidar em um job description completo e atrativo. Mas antes, preciso definir alguns detalhes importantes para finalizar a vaga. Posso começar com a remuneração e benefícios?",
    timestamp: "09:21",
    type: "action",
    actions: [
      { label: "Definir Remuneração", icon: DollarSign, variant: "secondary" },
      { label: "Estruturar Benefícios", icon: Heart, variant: "secondary" },
      { label: "Configurar Variável", icon: TrendingUp, variant: "secondary" }
    ],
    contextData: {
      type: "compensation-package",
      title: "Pacote de Remuneração e Benefícios",
      data: {
        position: "Diretor de TI",
        market_analysis: {
          salary_research: {
            market_median: "R$ 42.500",
            percentile_25: "R$ 35.000",
            percentile_75: "R$ 50.000",
            percentile_90: "R$ 62.000",
            regional_adjustment: "São Paulo = 100% (base)",
            industry_premium: "+8% (Tech/Fintech)",
            size_adjustment: "+5% (500-1000 employees)"
          },
          benchmarking_companies: [
            { company: "Nubank", range: "R$ 45-65k", notes: "Alto equity" },
            { company: "iFood", range: "R$ 40-55k", notes: "Forte variável" },
            { company: "Stone", range: "R$ 38-52k", notes: "Equity generoso" },
            { company: "PagSeguro", range: "R$ 42-58k", notes: "Benefícios premium" }
          ]
        },
        recommended_package: {
          base_salary: {
            min: "R$ 35.000",
            target: "R$ 42.500",
            max: "R$ 50.000",
            positioning: "Mediana de mercado",
            rationale: "Competitivo para atrair top talent"
          },
          variable_compensation: {
            annual_bonus: {
              target: "30% do salário base",
              min: "0%",
              max: "50%",
              criteria: [
                "Objetivos individuais (40%)",
                "Objetivos de equipe (30%)",
                "Resultados da empresa (30%)"
              ]
            }
          },
          benefits_package: {
            health_dental: {
              plan: "Premium nacional",
              coverage: "Titular + dependentes",
              copay: "Zero",
              estimated_value: "R$ 2.400/mês"
            },
            mobility: {
              car_allowance: "R$ 3.500/mês",
              fuel_card: "R$ 800/mês",
              uber_corporate: "R$ 500/mês backup",
              estimated_value: "R$ 4.800/mês"
            },
            development: {
              education_budget: "R$ 30.000/ano",
              conferences: "2 internacionais + nacionais",
              books_courses: "Ilimitado",
              estimated_value: "R$ 2.500/mês"
            },
            flexibility: {
              vacation: "30 dias + 5 extras",
              sabbatical: "1 mês após 3 anos",
              flexible_hours: "Core time 10-16h",
              remote_work: "3 dias home office",
              estimated_value: "R$ 1.500/mês"
            },
            technology: {
              equipment: "MacBook Pro M3 + setup",
              home_office: "R$ 8.000 one-time",
              mobile_plan: "Corporate unlimited",
              estimated_value: "R$ 800/mês"
            }
          },
          total_compensation: {
            cash_total: "R$ 55.250 (base + target bonus)",
            benefits_value: "R$ 12.000/mês",
            equity_annual: "R$ 50.000/ano",
            total_annual: "R$ 807.000",
            positioning: "Top 25% do mercado"
          }
        }
      }
    }
  },
  {
    id: 14,
    sender: "user",
    content: "Perfeito! O pacote de remuneração está bem estruturado e competitivo. Pode finalizar o job description completo agora.",
    timestamp: "09:25",
    type: "text"
  },
  {
    id: 15,
    sender: "lia",
    content: "Ótimo! Agora vou consolidar tudo em um job description completo e profissional. Criando a descrição final da vaga integrando todos os elementos que mapeamos: estrutura organizacional, competências, remuneração e contexto estratégico. O JD está pronto para revisão!",
    timestamp: "09:27",
    type: "action",
    actions: [
      { label: "Revisar Job Description", icon: FileText, variant: "secondary" },
      { label: "Editar Conteúdo", icon: Edit, variant: "secondary" },
      { label: "Aprovar e Publicar", icon: CheckCircle, variant: "secondary" }
    ],
    contextData: {
      type: "final-job-description",
      title: "Job Description Completo - Diretor de TI",
      data: {
        header: {
          title: "Diretor de Tecnologia da Informação",
          company: "Sodexo Enterprise",
          location: "São Paulo, SP (Híbrido - 3 dias presencial)",
          employment_type: "CLT - Tempo Integral",
          salary_range: "R$ 35.000 - R$ 50.000 + Benefícios Premium",
          posting_date: "22 de Fevereiro de 2024"
        },
        key_responsibilities: {
          strategic_leadership: [
            "Desenvolver e executar a estratégia de TI alinhada aos objetivos de negócio",
            "Liderar a transformação digital end-to-end da organização"
          ],
          operational_excellence: [
            "Gerenciar orçamento de TI de R$ 15M+ anuais",
            "Implementar frameworks de governança e compliance"
          ]
        },
        required_qualifications: {
          education: [
            "Graduação em Engenharia, Ciência da Computação ou áreas relacionadas",
            "MBA ou especialização em Gestão de TI (preferencial)"
          ],
          experience: [
            "8+ anos em liderança de TI em empresas de médio/grande porte",
            "5+ anos em transformação digital e modernização de infraestrutura"
          ]
        },
        compensation_highlights: {
          total_package: "R$ 807.000/ano (Total Compensation)",
          salary_range: "R$ 35.000 - R$ 50.000 (CLT)",
          variable_bonus: "Até 50% do salário base (target: 30%)",
          benefits_value: "R$ 12.000/mês em benefícios premium"
        }
      }
    }
  },
  {
    id: 16,
    sender: "user",
    content: "Excelente trabalho no job description! Está muito completo e atrativo. Agora pode publicar a vaga e iniciar o processo de sourcing ativo.",
    timestamp: "09:30",
    type: "text"
  },
  {
    id: 16.5,
    sender: "lia",
    content: "Antes de publicar a vaga, preciso solicitar aprovação do gestor para o job description e orçamento proposto. Vou enviar para Carlos Silva (Head de TI) aprovar.",
    timestamp: "09:31",
    type: "approval",
    needsApproval: true,
    approvalStatus: "pending",
    approvalRequest: {
      title: "Aprovação: Job Description + Orçamento",
      description: "Solicito aprovação para publicação da vaga de Diretor de TI conforme especificações abaixo",
      manager: "Carlos Silva - Head de TI",
      items: [
        { label: "Posição", value: "Diretor de Tecnologia da Informação" },
        { label: "Salário proposto", value: "R$ 35.000 - R$ 50.000 + benefícios" },
        { label: "Orçamento total anual", value: "R$ 807.000" },
        { label: "Orçamento de publicação", value: "R$ 5.500" },
        { label: "Prazo estimado", value: "45 dias" }
      ]
    },
    actions: [
      { label: "Aprovar", icon: CheckCircle, variant: "secondary" },
      { label: "Solicitar Alterações", icon: Edit, variant: "secondary" },
      { label: "Rejeitar", icon: X, variant: "secondary" }
    ]
  },
  {
    id: 17,
    sender: "lia",
    content: "Perfeito! Agora vou executar tudo automaticamente no seu ATS Workday. Criando a vaga no sistema... ✅ Vaga criada com sucesso! ID: WD-2024-0156 'Diretor de Tecnologia da Informação'. Configurei todos os campos, critérios de triagem automática e fluxo de aprovação. Agora posso publicar nos canais e iniciar o sourcing ativo?",
    timestamp: "09:32",
    type: "action",
    actions: [
      { label: "Publicar em Todos os Canais", icon: Globe, variant: "secondary" },
      { label: "Iniciar Sourcing Ativo", icon: Search, variant: "secondary" },
      { label: "Configurar Automações", icon: Settings, variant: "secondary" }
    ],
    contextData: {
      type: "job-publishing",
      title: "Publicação da Vaga - Execução Automática",
      data: {
        ats_integration: {
          system: "Workday",
          job_id: "WD-2024-0156",
          status: "Published"
        },
        publication_channels: [
          { platform: "LinkedIn Jobs", status: "Published", reach: "50K+ professionals", budget: "R$ 2.500" },
          { platform: "Indeed Premium", status: "Published", reach: "25K+ candidates", budget: "R$ 1.800" },
          { platform: "Glassdoor", status: "Published", reach: "15K+ tech talent", budget: "R$ 1.200" }
        ],
        success_metrics: {
          targets: {
            applications: "200+ applications em 4 semanas",
            qualified_candidates: "50+ qualified profiles",
            interview_pipeline: "15+ candidates para entrevistas",
            time_to_hire: "45 dias maximum"
          }
        }
      }
    }
  },
  {
    id: 18,
    sender: "user",
    content: "Ótimo! Pode publicar em todos os canais e iniciar o sourcing ativo. Vamos acelerar este processo.",
    timestamp: "09:35",
    type: "text"
  },
  {
    id: 19,
    sender: "lia",
    content: "🚀 Sourcing ativo iniciado! Publiquei a vaga em todos os 5 canais principais. Já identifiquei 47 candidatos potenciais através do meu algoritmo de matching avançado. Iniciando outreach personalizado... ⚡ Update em tempo real: 12 aplicações recebidas nas primeiras 3 horas! Vou começar a triagem automática?",
    timestamp: "09:38",
    type: "action",
    actions: [
      { label: "Ver Pipeline de Candidatos", icon: Users, variant: "secondary" },
      { label: "Iniciar Triagem Automática", icon: Filter, variant: "secondary" },
      { label: "Agendar Primeiras Entrevistas", icon: Calendar, variant: "secondary" }
    ],
    contextData: {
      type: "interview-scheduling",
      title: "Agendamento de Entrevistas - Candidatos Top",
      data: {
        candidates_to_schedule: [
          {
            name: "Carlos Mendonça",
            score: 94,
            interview_type: "Screening Call (30 min)",
            preferred_times: ["Manhã", "Tarde"]
          },
          {
            name: "Patricia Santos",
            score: 91,
            interview_type: "Screening Call (30 min)",
            preferred_times: ["Tarde", "Noite"]
          },
          {
            name: "Ricardo Alves",
            score: 88,
            interview_type: "Screening Call (30 min)",
            preferred_times: ["Manhã"]
          }
        ],
        available_slots: {
          "23/02/2024": [
            { time: "09:00", duration: "30 min", available: true },
            { time: "10:00", duration: "30 min", available: true },
            { time: "11:00", duration: "30 min", available: true },
            { time: "14:00", duration: "30 min", available: true },
            { time: "15:00", duration: "30 min", available: true },
            { time: "16:00", duration: "30 min", available: true }
          ],
          "24/02/2024": [
            { time: "09:00", duration: "30 min", available: true },
            { time: "10:00", duration: "30 min", available: false },
            { time: "11:00", duration: "30 min", available: true },
            { time: "14:00", duration: "30 min", available: true },
            { time: "15:00", duration: "30 min", available: true },
            { time: "16:30", duration: "30 min", available: true }
          ],
          "25/02/2024": [
            { time: "09:00", duration: "30 min", available: true },
            { time: "10:00", duration: "30 min", available: true },
            { time: "14:00", duration: "30 min", available: true },
            { time: "15:00", duration: "30 min", available: true }
          ]
        },
        interviewer: "Ana Silva - Senior Recruiter",
        auto_confirmation: true,
        calendar_integration: "Google Calendar"
      }
    }
  },
  {
    id: 20,
    sender: "user",
    content: "Excelente progresso! Por favor inicie a triagem automática e agende as primeiras entrevistas com os candidatos top.",
    timestamp: "09:42",
    type: "text"
  },
  {
    id: 21,
    sender: "lia",
    content: "✅ Triagem automática ativada! Processei os 12 candidatos aplicados - 8 avançaram automaticamente e 4 foram filtrados. Agendei 5 screening calls para amanhã e after-tomorrow. Também configurei o processo de entrevistas estruturadas. Quer revisar o cronograma de entrevistas?",
    timestamp: "09:45",
    type: "action",
    actions: [
      { label: "Ver Cronograma de Entrevistas", icon: Calendar, variant: "secondary" },
      { label: "Configurar Avaliações", icon: ClipboardList, variant: "secondary" },
      { label: "Preparar Interview Kits", icon: FileText, variant: "secondary" }
    ],
    contextData: {
      type: "interview-management",
      title: "Gestão de Entrevistas - Sistema Integrado",
      data: {
        screening_schedule: [
          {
            candidate: "Carlos Mendonça",
            date: "23/02/2024",
            time: "14:00-14:30",
            interviewer: "Ana Silva",
            type: "Screening Call",
            status: "Confirmed"
          },
          {
            candidate: "Patricia Santos",
            date: "23/02/2024",
            time: "15:00-15:30",
            interviewer: "Ana Silva",
            type: "Screening Call",
            status: "Confirmed"
          }
        ],
        interview_structure: {
          stage_1_screening: {
            duration: "30 minutes",
            interviewer: "Ana Silva (Recruiter)",
            focus: ["Cultural fit", "Communication skills", "Salary expectations"],
            success_criteria: "Score ≥ 7/10 para advance"
          },
          stage_2_technical: {
            duration: "90 minutes",
            interviewer: "CTO + Senior Tech Lead",
            focus: ["Technical leadership", "Architecture decisions", "Team management"],
            success_criteria: "Score ≥ 8/10 para advance"
          }
        }
      }
    }
  },
  {
    id: 22,
    sender: "user",
    content: "Perfeito! O processo de entrevistas está bem estruturado. Agora vamos para a próxima fase - assumindo que encontramos o candidato ideal, preciso que você prepare todo o processo de seleção final e proposta.",
    timestamp: "09:50",
    type: "text"
  },
  {
    id: 23,
    sender: "lia",
    content: "Excelente! Vou preparar todo o workflow de seleção final, negociação e proposta. Assumindo que Carlos Mendonça seja nosso candidato escolhido (score 94), já preparei a proposta completa, processo de referências, due diligence e documentação para aprovação do C-Level. Tudo pronto para execução!",
    timestamp: "09:53",
    type: "action",
    actions: [
      { label: "Ver Proposta Final", icon: FileText, variant: "secondary" },
      { label: "Iniciar Referências", icon: Phone, variant: "secondary" },
      { label: "Preparar Documentos", icon: Download, variant: "secondary" }
    ],
    contextData: {
      type: "offer-letter",
      title: "Carta Oferta - Carlos Mendonça",
      data: {
        candidate_info: {
          name: "Carlos Mendonça",
          email: "carlos.mendonca@email.com",
          phone: "+55 11 98765-4321",
          current_company: "iFood"
        },
        position_details: {
          title: "Diretor de Tecnologia da Informação",
          department: "Tecnologia e Inovação",
          reports_to: "CEO - Roberto Costa",
          start_date: "15 de Março de 2024",
          location: "São Paulo, SP - Modelo Híbrido"
        },
        compensation: {
          base_salary: "R$ 47.500,00/mês",
          variable_bonus: "Até 50% do salário base (target: 30%)",
          sign_on_bonus: "R$ 30.000,00 (pagamento único)",
          stock_options: "0.15% equity - 4 anos vesting",
          total_annual: "R$ 807.000,00"
        },
        benefits: {
          health_insurance: "Plano de saúde premium (titular + dependentes)",
          dental: "Plano odontológico completo",
          life_insurance: "Seguro de vida em grupo",
          meal_voucher: "R$ 1.200/mês (Flash)",
          transport: "Vale-transporte ou estacionamento",
          gym: "Gympass premium",
          home_office: "Auxílio home office R$ 500/mês",
          education: "Budget anual de R$ 15.000 para cursos e certificações",
          vacation: "30 dias de férias anuais",
          pto: "15 dias de PTO (Paid Time Off) adicionais"
        },
        letter_template: `São Paulo, 14 de Fevereiro de 2024

Prezado Carlos Mendonça,

É com grande satisfação que apresentamos nossa proposta formal para você integrar nossa equipe como **Diretor de Tecnologia da Informação**.

**DETALHES DA POSIÇÃO:**
Cargo: Diretor de Tecnologia da Informação
Departamento: Tecnologia e Inovação
Reporta-se a: CEO - Roberto Costa
Data de início: 15 de Março de 2024
Localização: São Paulo, SP - Modelo Híbrido (3 dias presencial)

**COMPENSAÇÃO:**
• Salário base: R$ 47.500,00 mensais (CLT)
• Bônus variável: Até 50% do salário base anual (target: 30%)
• Sign-on bonus: R$ 30.000,00 (pagamento único no primeiro mês)
• Stock Options: 0.15% equity com vesting de 4 anos
• Total anual estimado: R$ 807.000,00

**PACOTE DE BENEFÍCIOS:**
• Plano de saúde premium (titular + dependentes) - Bradesco Saúde Top
• Plano odontológico completo
• Seguro de vida em grupo
• Vale-refeição: R$ 1.200/mês (Flash)
• Vale-transporte ou estacionamento
• Gympass premium
• Auxílio home office: R$ 500/mês
• Budget educacional: R$ 15.000/ano para cursos, certificações e conferências
• 30 dias de férias anuais
• 15 dias de PTO (Paid Time Off) adicionais

**RESPONSABILIDADES PRINCIPAIS:**
Liderar a transformação digital da empresa, gerenciar equipe de 45+ profissionais de TI, modernizar infraestrutura tecnológica e implementar estratégias de inovação alinhadas aos objetivos de negócio.

Esta proposta é válida até 28 de Fevereiro de 2024. Estamos entusiasmados com a possibilidade de tê-lo em nossa equipe!

Atenciosamente,

Roberto Costa
CEO
WeDo Talent Solutions`
      }
    }
  },
  {
    id: 24,
    sender: "user",
    content: "Excelente trabalho! A proposta está bem estruturada. Assumindo que ele aceite, agora preciso que você prepare todo o processo de onboarding e integração dele à empresa.",
    timestamp: "09:58",
    type: "text"
  },
  {
    id: 25,
    sender: "lia",
    content: "🎉 Perfeito! Vou criar um plano de onboarding de classe mundial para Carlos. Preparei um programa de 90 dias estruturado, com integração técnica, cultural e estratégica. Incluí automação completa no HRIS, preparação da equipe, e acompanhamento contínuo. O onboarding está desenhado para maximizar o sucesso dele nos primeiros meses!",
    timestamp: "10:02",
    type: "action",
    actions: [
      { label: "Ver Plano de Onboarding", icon: Workflow, variant: "secondary" },
      { label: "Configurar Automações", icon: Settings, variant: "secondary" },
      { label: "Preparar Equipe", icon: Users, variant: "secondary" }
    ],
    contextData: {
      type: "onboarding-plan",
      title: "Plano de Onboarding - 90 Dias",
      data: {
        program: "Programa de 90 Dias",
        description: "Integração estratégica e cultural personalizada",
        first_30_days: [
          "Imersão na cultura e processos da empresa",
          "Reuniões 1:1 com stakeholders principais",
          "Análise do estado atual da infraestrutura TI"
        ],
        days_60_90: [
          "Apresentação do plano estratégico de transformação digital",
          "Início das primeiras iniciativas de melhoria"
        ]
      }
    }
  },
  {
    id: 26,
    sender: "user",
    content: "Fantástico! O plano de onboarding está muito bem estruturado. Agora preciso que você configure o acompanhamento de 90 dias e prepare um sistema de avaliação de performance para o primeiro ano dele.",
    timestamp: "10:08",
    type: "text"
  },
  {
    id: 27,
    sender: "lia",
    content: "Excelente! Vou criar um sistema completo de acompanhamento pós-90 dias e avaliação de performance anual. Preparei um framework de performance management integrado, com OKRs estratégicos, métricas de sucesso, 360-feedback contínuo, e planejamento de carreira. Tudo automatizado no sistema para garantir o sucesso de longo prazo!",
    timestamp: "10:12",
    type: "action",
    actions: [
      { label: "Ver Framework de Performance", icon: Target, variant: "secondary" },
      { label: "Configurar OKRs", icon: BarChart3, variant: "secondary" },
      { label: "Agendar Reviews", icon: Calendar, variant: "secondary" }
    ],
    contextData: {
      type: "performance-management",
      title: "Framework de Performance Management",
      data: {
        framework: "Framework de Avaliação Anual",
        description: "OKRs + 360-feedback + desenvolvimento contínuo",
        first_year_okrs: [
          { objective: "Transformação Digital", description: "Migrar 80% dos sistemas para cloud em 12 meses" },
          { objective: "Crescimento da Equipe", description: "Escalar equipe de 45 para 75 pessoas com 95% de retenção" },
          { objective: "Excelência Operacional", description: "Reduzir downtime em 50% e implementar monitoramento avançado" }
        ],
        review_schedule: [
          { period: "30 dias", type: "Check-in inicial" },
          { period: "90 dias", type: "Avaliação onboarding" },
          { period: "12 meses", type: "Review anual" }
        ]
      }
    }
  },
  {
    id: 28,
    sender: "user",
    content: "Perfeito! O sistema de performance management está extremamente bem estruturado. Agora temos uma jornada completa desde a abertura da vaga até o acompanhamento de performance do primeiro ano. Muito bom trabalho!",
    timestamp: "10:18",
    type: "text"
  },
  {
    id: 29,
    sender: "lia",
    content: "🎉 Obrigada! Criamos uma jornada de recrutamento verdadeiramente completa e integrada! Do mapeamento organizacional inicial até o performance management de primeiro ano - tudo conectado, automatizado e otimizado. Agora quero gerar um relatório executivo final consolidando toda esta jornada para documentação e futuras replicações. Posso criar?",
    timestamp: "10:20",
    type: "action",
    actions: [
      { label: "Gerar Relatório Executivo", icon: FileText, variant: "secondary" },
      { label: "Criar Template Replicável", icon: Copy, variant: "secondary" },
      { label: "Configurar Dashboard", icon: BarChart3, variant: "secondary" }
    ],
    contextData: {
      type: "journey-summary",
      title: "Relatório Executivo - Jornada Completa de Recrutamento",
      data: {
        executive_summary: {
          position: "Diretor de Tecnologia da Informação",
          journey_duration: "Planejamento: 2 semanas | Execução: 6 semanas | Onboarding: 12 semanas",
          total_investment: "R$ 127.500 (recrutamento) + R$ 807.000 (compensação anual)",
          roi_projection: "R$ 3.2M em valor gerado no primeiro ano",
          success_probability: "94% baseado em assessment completo e cultural fit"
        },
        journey_phases: {
          phase_1_strategic_planning: {
            duration: "1 semana",
            activities: [
              "Análise estrutura organizacional",
              "Definição hierarquia e escopo",
              "Mapeamento competências técnicas/comportamentais",
              "Estruturação pacote compensação"
            ],
            outcomes: [
              "Job description completo e atrativo",
              "Compensação top 25% do mercado",
              "Aprovação unânime do C-Level",
              "Framework de avaliação estruturado"
            ]
          },
          phase_2_sourcing_selection: {
            duration: "4 semanas",
            activities: [
              "Publicação em 5 canais premium",
              "Sourcing ativo de 150+ candidatos",
              "Processo estruturado de 4 etapas",
              "Avaliação com IA e 360-feedback"
            ],
            outcomes: [
              "200+ aplicações de qualidade",
              "59 candidatos no pipeline",
              "Seleção final com 94% de score",
              "Proposta aceita em primeira rodada"
            ]
          }
        },
        key_innovations: {
          ai_integration: [
            "Sourcing automatizado com ML matching",
            "Análise sentimento em entrevistas",
            "Predictive success modeling",
            "Automated performance tracking"
          ],
          ats_automation: [
            "Workday integration completa",
            "Workflows automatizados end-to-end",
            "Real-time dashboards e analytics",
            "Cross-system data synchronization"
          ]
        },
        measurable_results: {
          time_to_hire: "45 dias (vs 65 dias industry average)",
          cost_per_hire: "R$ 127.500 (vs R$ 180.000 executive search)",
          candidate_quality: "94/100 final score (vs 78 average)",
          hiring_manager_satisfaction: "9.8/10 NPS"
        }
      }
    }
  },
  {
    id: 30,
    sender: "lia",
    content: "💡 Com base na análise preditiva dos dados históricos, identifiquei 3 oportunidades de otimização para futuras jornadas similares. Minha IA analisou 500+ processos anteriores e sugere melhorias que podem reduzir o time-to-hire em 15% e aumentar a qualidade dos candidatos em 12%.",
    timestamp: "10:25",
    type: "action",
    actions: [
      { label: "Ver Sugestões Preditivas", icon: Brain, variant: "secondary" },
      { label: "Aplicar Otimizações", icon: Zap, variant: "secondary" },
      { label: "Configurar IA Preditiva", icon: Settings, variant: "secondary" }
    ],
    contextData: {
      type: "predictive-insights",
      title: "Inteligência Preditiva - Sugestões de Otimização",
      data: {
        analysis_base: {
          historical_processes: 500,
          success_rate_current: 87,
          avg_time_current: 45,
          data_points: 15000
        },
        predictions: [
          {
            category: "Tempo de Contratação",
            current_performance: "45 dias médios",
            predicted_improvement: "38 dias (-15%)",
            confidence: 94,
            actions: [
              "Automatizar triagem inicial com scoring IA",
              "Implementar agendamento inteligente de entrevistas",
              "Priorizar candidatos com maior probabilidade de aceite"
            ]
          },
          {
            category: "Qualidade dos Candidatos",
            current_performance: "Score médio 78/100",
            predicted_improvement: "Score médio 87/100 (+12%)",
            confidence: 89,
            actions: [
              "Refinar critérios de sourcing com ML",
              "Implementar análise preditiva de fit cultural",
              "Otimizar job descriptions com NLP"
            ]
          },
          {
            category: "Taxa de Conversão",
            current_performance: "67% de conversão",
            predicted_improvement: "79% de conversão (+18%)",
            confidence: 91,
            actions: [
              "Personalizar approach por perfil candidato",
              "Implementar follow-up inteligente",
              "Otimizar processo de negociação"
            ]
          }
        ],
        implementation_roadmap: {
          phase_1: "Implementar scoring IA (2 semanas)",
          phase_2: "Deploy agendamento inteligente (3 semanas)",
          phase_3: "Ativar análise preditiva completa (4 semanas)"
        }
      }
    }
  },
  {
    id: 30,
    sender: "user",
    content: "Perfeito! Agora quero que você analise os candidatos do último processo e me ajude a identificar padrões de sucesso para futuras contratações.",
    timestamp: "10:22",
    type: "text"
  },
  {
    id: 31,
    sender: "lia",
    content: "",
    timestamp: "10:23",
    type: "thinking",
    thinkingMessage: "Analisando dados dos candidatos e identificando padrões de performance..."
  },
  {
    id: 32,
    sender: "lia",
    content: "Vou realizar uma análise completa dos dados de candidatos para identificar padrões de sucesso. Deixe-me processar todas as informações.",
    timestamp: "10:23",
    type: "progress",
    progressSteps: [
      {
        id: "step1",
        label: "Coletando dados dos candidatos",
        status: "completed",
        details: "150 candidatos analisados",
        icon: Users
      },
      {
        id: "step2",
        label: "Analisando performance histórica",
        status: "processing",
        details: "Correlacionando dados com performance",
        icon: BarChart3
      },
      {
        id: "step3",
        label: "Identificando padrões de sucesso",
        status: "pending",
        details: "Algoritmos de ML em processamento",
        icon: Brain
      },
      {
        id: "step4",
        label: "Gerando insights preditivos",
        status: "pending",
        details: "Criando modelo de predição",
        icon: Target
      }
    ],
    currentStep: "step2"
  },
  {
    id: 33,
    sender: "lia",
    content: "Executando análise de dados avançada...",
    timestamp: "10:24",
    type: "command",
    command: {
      text: "python analyze_candidates.py --model=success_pattern --data=last_12_months",
      status: "executing",
      output: "Processando 150 candidatos...\nCorrelação encontrada: 0.89\nPadrões identificados: 12"
    }
  },
  {
    id: 34,
    sender: "lia",
    content: "Criando relatório de análise...",
    timestamp: "10:25",
    type: "file-creation",
    fileCreation: {
      fileName: "candidate_success_patterns_2024.pdf",
      fileType: "Relatório de Análise Preditiva",
      status: "creating"
    }
  },
  {
    id: 35,
    sender: "lia",
    content: "🎯 Análise concluída com sucesso! Identifiquei 5 padrões principais que correlacionam com alta performance:\n\n• **Experiência em transformação digital** (correlação: 0.92)\n• **Liderança em equipes multidisciplinares** (correlação: 0.87)\n• **Background em metodologias ágeis** (correlação: 0.84)\n• **Formação continuada em tecnologia** (correlação: 0.79)\n• **Experiência internacional** (correlação: 0.71)\n\nCom base nesses padrões, posso prever com 89% de precisão o sucesso de futuros candidatos para posições similares.",
    timestamp: "10:26",
    type: "completion",
    completion: {
      message: "Análise de padrões de sucesso concluída com precisão de 89%",
      allowRating: true,
      allowFollowUp: true
    },
    contextData: {
      type: "predictive-insights",
      title: "Padrões de Sucesso - Análise Preditiva",
      data: {
        analysis_summary: {
          candidates_analyzed: 150,
          success_correlation: 0.89,
          prediction_accuracy: "89%",
          patterns_identified: 5,
          model_confidence: "Alta"
        },
        success_patterns: [
          {
            pattern: "Experiência em Transformação Digital",
            correlation: 0.92,
            description: "Candidatos com experiência comprovada em projetos de transformação digital apresentam 92% maior probabilidade de sucesso",
            examples: ["Migração cloud", "Implementação de DevOps", "Digitalização de processos"]
          },
          {
            pattern: "Liderança Multidisciplinar",
            correlation: 0.87,
            description: "Liderança de equipes diversas indica melhor adaptação ao ambiente organizacional",
            examples: ["Gestão de times técnicos e negócio", "Coordenação de stakeholders", "Projetos cross-funcionais"]
          }
        ],
        predictive_model: {
          accuracy: "89%",
          confidence_interval: "85-93%",
          validation_method: "Cross-validation com dados de 24 meses",
          next_calibration: "Trimestral"
        },
        recommendations: [
          "Priorizar candidatos com score > 85% no modelo preditivo",
          "Incluir perguntas específicas sobre transformação digital",
          "Avaliar experiência em gestão de mudanças organizacionais",
          "Verificar histórico de projetos multidisciplinares"
        ]
      }
    }
  }
]

export { mockAgents, mockActivities, emptyConversation, modernConversation }
