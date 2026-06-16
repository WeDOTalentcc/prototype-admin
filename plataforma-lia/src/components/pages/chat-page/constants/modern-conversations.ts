import { CURRENCY_SYMBOL } from "@/lib/pricing"
import {
  Plus, Users, TrendingUp, Network, Settings, Target, Workflow, Database, BarChart3, Shield,
  DollarSign, Heart, Building, Clock, Laptop, Globe, FileText, Edit, CheckCircle, X,
  Search, Calendar, Filter, Phone, Download, ClipboardList, Copy, Brain, Zap, Lightbulb
} from "lucide-react"
import type { Message } from "../types"
import { modernConversationPart2 } from "./modern-conversations-part2"

const modernConversationPart1: Message[] = [
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
            market_median: `${CURRENCY_SYMBOL} 42.500`,
            percentile_25: `${CURRENCY_SYMBOL} 35.000`,
            percentile_75: `${CURRENCY_SYMBOL} 50.000`,
            percentile_90: `${CURRENCY_SYMBOL} 62.000`,
            regional_adjustment: "São Paulo = 100% (base)",
            industry_premium: "+8% (Tech/Fintech)",
            size_adjustment: "+5% (500-1000 employees)"
          },
          benchmarking_companies: [
            { company: "Nubank", range: `${CURRENCY_SYMBOL} 45-65k`, notes: "Alto equity" },
            { company: "iFood", range: `${CURRENCY_SYMBOL} 40-55k`, notes: "Forte variável" },
            { company: "Stone", range: `${CURRENCY_SYMBOL} 38-52k`, notes: "Equity generoso" },
            { company: "PagSeguro", range: `${CURRENCY_SYMBOL} 42-58k`, notes: "Benefícios premium" }
          ]
        },
        recommended_package: {
          base_salary: {
            min: `${CURRENCY_SYMBOL} 35.000`,
            target: `${CURRENCY_SYMBOL} 42.500`,
            max: `${CURRENCY_SYMBOL} 50.000`,
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
              estimated_value: `${CURRENCY_SYMBOL} 2.400/mês`
            },
            mobility: {
              car_allowance: `${CURRENCY_SYMBOL} 3.500/mês`,
              fuel_card: `${CURRENCY_SYMBOL} 800/mês`,
              uber_corporate: `${CURRENCY_SYMBOL} 500/mês backup`,
              estimated_value: `${CURRENCY_SYMBOL} 4.800/mês`
            },
            development: {
              education_budget: `${CURRENCY_SYMBOL} 30.000/ano`,
              conferences: "2 internacionais + nacionais",
              books_courses: "Ilimitado",
              estimated_value: `${CURRENCY_SYMBOL} 2.500/mês`
            },
            flexibility: {
              vacation: "30 dias + 5 extras",
              sabbatical: "1 mês após 3 anos",
              flexible_hours: "Core time 10-16h",
              remote_work: "3 dias home office",
              estimated_value: `${CURRENCY_SYMBOL} 1.500/mês`
            },
            technology: {
              equipment: "MacBook Pro M3 + setup",
              home_office: `${CURRENCY_SYMBOL} 8.000 one-time`,
              mobile_plan: "Corporate unlimited",
              estimated_value: `${CURRENCY_SYMBOL} 800/mês`
            }
          },
          total_compensation: {
            cash_total: `${CURRENCY_SYMBOL} 55.250 (base + target bonus)`,
            benefits_value: `${CURRENCY_SYMBOL} 12.000/mês`,
            equity_annual: `${CURRENCY_SYMBOL} 50.000/ano`,
            total_annual: `${CURRENCY_SYMBOL} 807.000`,
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
          salary_range: `${CURRENCY_SYMBOL} 35.000 - ${CURRENCY_SYMBOL} 50.000 + Benefícios Premium`,
          posting_date: "22 de Fevereiro de 2024"
        },
        key_responsibilities: {
          strategic_leadership: [
            "Desenvolver e executar a estratégia de TI alinhada aos objetivos de negócio",
            "Liderar a transformação digital end-to-end da organização"
          ],
          operational_excellence: [
            `Gerenciar orçamento de TI de ${CURRENCY_SYMBOL} 15M+ anuais`,
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
          total_package: `${CURRENCY_SYMBOL} 807.000/ano (Total Compensation)`,
          salary_range: `${CURRENCY_SYMBOL} 35.000 - ${CURRENCY_SYMBOL} 50.000 (CLT)`,
          variable_bonus: "Até 50% do salário base (target: 30%)",
          benefits_value: `${CURRENCY_SYMBOL} 12.000/mês em benefícios premium`
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
        { label: "Salário proposto", value: `${CURRENCY_SYMBOL} 35.000 - ${CURRENCY_SYMBOL} 50.000 + benefícios` },
        { label: "Orçamento total anual", value: `${CURRENCY_SYMBOL} 807.000` },
        { label: "Orçamento de publicação", value: `${CURRENCY_SYMBOL} 5.500` },
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
          { platform: "LinkedIn Jobs", status: "Published", reach: "50K+ professionals", budget: `${CURRENCY_SYMBOL} 2.500` },
          { platform: "Indeed Premium", status: "Published", reach: "25K+ candidates", budget: `${CURRENCY_SYMBOL} 1.800` },
          { platform: "Glassdoor", status: "Published", reach: "15K+ tech talent", budget: `${CURRENCY_SYMBOL} 1.200` }
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

]

const modernConversation: Message[] = [...modernConversationPart1, ...modernConversationPart2]

export { modernConversation }
