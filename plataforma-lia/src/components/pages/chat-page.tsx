"use client"

import React, { useState, useEffect, useCallback, useRef, useMemo } from "react"
import { useRouter, useSearchParams } from "next/navigation"
import { AnimatePresence, motion } from "framer-motion"
import { useChatLayout } from "@/hooks/useChatLayout"
import { useEmptyFieldNotifications, type EmptyFieldNotification, type FieldValueSuggestion } from "@/hooks/use-empty-field-notifications"
import { EmptyFieldNotificationMessage } from "@/components/chat/empty-field-notification-message"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { LIAIcon } from "@/components/ui/lia-icon"
import { liaApi } from "@/services/lia-api"
import {
  Send, Zap, Loader2, FileText, Users, Plus, MessageSquare, Mic, Paperclip, Image, Calendar, BarChart3, Target,
  ChevronLeft, ChevronRight, ChevronDown, Search, Clock, Star, Layout, Layers3, MapPin, GraduationCap, Briefcase, DollarSign, HelpCircle, X,
  Phone, Video, ExternalLink, Database, Info, CheckCircle, AlertTriangle, XCircle, Download, Settings, Eye,
  Filter, Mail, Building, Globe, Edit, Copy, Share2, BookOpen, UserCheck, MessageCircle, TrendingUp, PieChart,
  CalendarDays, Timer, ArrowUpDown, Percent, Users2, Award, Link, Linkedin, Upload, Network, Workflow, Brain, Lightbulb, Heart,
  Play, Bell, Laptop, ClipboardList, Shield, RefreshCcw
} from "lucide-react"
import {
  ThinkingIndicator,
  ProgressSteps,
  CommandExecution,
  FileCreationIndicator,
  CompletionMessage,
  ProgressiveDisclosure
} from "@/components/ui/chat-status-indicators"
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs"
import { Activity, Bot, Cpu } from "lucide-react"
import { CandidateCard } from "@/components/ui/candidate-card"
import { InterviewSchedulingModal } from "@/components/ui/interview-scheduling-modal"
import { PromptSuggestionsDock } from "@/components/ui/prompt-suggestions-dock"
import { ContextPill } from "@/components/ui/context-pill"
import { QuickActionChips, QuickAction, defaultCandidateActions } from "@/components/ui/quick-action-chips"
import { CommandPalette, CommandItem, defaultCommands } from "@/components/ui/command-palette"
import { PipelineReport } from "@/components/ui/pipeline-report"
import { FileUploadButton, FileAnalysisResult } from "@/components/ui/file-upload-button"
import { AudioRecordButton } from "@/components/ui/audio-record-button"
import { useToast } from "@/hooks/use-toast"
import { PipelineReportResponse } from "@/services/lia-api"
import { AgentControlCenter } from "@/components/agent-control-center"
import { SearchResultsCard, CandidateResult } from "@/components/search/search-results-card"
import { CandidateDetailSidebar } from "@/components/search/candidate-detail-sidebar"
import { CreditConfirmationDialog } from "@/components/search/credit-confirmation-dialog"
import { SmartSearchInput, ParsedEntities, SearchMode, SearchMetadata } from "@/components/search/smart-search-input"
import { SearchPreviewCard, SearchPreviewData } from "@/components/search/search-preview-card"
import { AdvancedFiltersModal, SearchFilters } from "@/components/search/advanced-filters-modal"
import { promoteCandidateToBase } from "@/lib/api/candidate-search"
import { useSearchFlow, SearchFlowState } from "@/hooks/useSearchFlow"
import { useUIActions } from "@/hooks/useUIActions"
import { useAgentStreaming } from "@/hooks/use-agent-streaming"
import { useGlobalSearchSettings } from "@/hooks/useGlobalSearchSettings"
import { 
  SidePanelContainer, 
  CandidateSummaryCard, 
  JobSummaryCard, 
  WSIScoreCard, 
  CompensationSummaryCard,
  InterviewConfirmationCard,
  ProgressTrackerCard,
  CompanyBenefitsSummaryCard
} from "@/components/ui-actions"
import { SidePanelType, PanelSubmitData, ChatCardType } from "@/components/ui-actions/types"
import { ActionResultCard } from "@/components/chat/action-result-card"
import { TypingIndicator } from "@/components/chat/typing-indicator"
import { AgentMemoryIndicator } from "@/components/chat/agent-memory-indicator"

interface Message {
  id: number
  sender: "lia" | "user"
  content: string
  timestamp: string
  type?: "text" | "action" | "structured" | "file" | "system" | "approval" | "thinking" | "progress" | "command" | "file-creation" | "completion"
  actions?: Array<{ label: string; icon?: any; variant?: "default" | "outline" | "secondary" }>
  data?: any
  step?: string
  contextData?: any // Dados para o painel lateral
  needsApproval?: boolean
  approvalStatus?: "pending" | "approved" | "rejected"
  approvalRequest?: {
    title: string
    description: string
    manager: string
    items: Array<{ label: string; value: string }>
  }
  chatCardType?: ChatCardType
  chatCardData?: Record<string, unknown>
  // Novos campos para status indicators
  thinkingMessage?: string
  progressSteps?: Array<{
    id: string
    label: string
    status: "pending" | "processing" | "completed" | "error"
    details?: string
    icon?: any
  }>
  currentStep?: string
  command?: {
    text: string
    status: "executing" | "completed" | "error"
    output?: string
  }
  fileCreation?: {
    fileName: string
    fileType: string
    status: "creating" | "created"
  }
  completion?: {
    message: string
    allowRating?: boolean
    allowFollowUp?: boolean
  }
}

interface ContextPanelData {
  type: "candidate" | "candidates" | "job" | "schedule" | "shortlist" | "report" | "comparison" | "analytics" | "job-details" | "position" | "recruitment-strategy" | "recruitment-process" | "job-final" | "job-description" | "compensation-package" | "search-strategy" | "candidate-suggestions" | "job-launch" | "evaluation-format" | "journey-progress" | "search-analytics" | "executive-report" | "proposal-template" | "final-report" | "shortlist-approval" | "screening-guide" | "org-structure-analysis" | "hierarchy-definition" | "technical-competencies" | "behavioral-competencies" | "complete-job-description" | "role-scope-definition" | "work-arrangement" | "sourcing-strategy" | "final-job-description" | "job-publishing" | "sourcing-progress" | "interview-management" | "final-selection" | "onboarding-plan" | "performance-management" | "journey-summary" | "predictive-insights" | "offer-letter" | "interview-scheduling" | "technical-matrix" | "timeline" | "interview-flow" | "org-chart" | "job-creation-progress" | "pipeline-report"
  title: string
  data: any
}

interface AgentData {
  id: string
  name: string
  icon: string
  description: string
  status: "active" | "idle" | "error"
  actionsToday: number
  lastActivity: string
  lastActivityTime: string
}

interface AgentActivity {
  id: string
  agentId: string
  agentIcon: string
  agentName: string
  action: string
  timestamp: string
  status: "success" | "pending" | "error"
}

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

export function ChatPage() {
  const searchParams = useSearchParams()
  
  // Permite alternar entre conversas via URL (/?conversation=director para histórico)
  // Por padrão, inicia com conversa vazia
  const conversationType = searchParams?.get('conversation') || 'empty'
  const initialConversation = conversationType === 'empty' ? emptyConversation : modernConversation
  
  const [messages, setMessages] = useState<Message[]>(initialConversation)
  const [input, setInput] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [contextData, setContextData] = useState<ContextPanelData | null>(null)
  const [isPanelOpen, setIsPanelOpen] = useState(false)
  const [searchTerm, setSearchTerm] = useState("")
  const [showSearch, setShowSearch] = useState(false)
  const [newMessageIndicator, setNewMessageIndicator] = useState(false)
  const [currentMessageIndex, setCurrentMessageIndex] = useState(0)
  const [availableCredits, setAvailableCredits] = useState<number>(50)
  
  // Interview Scheduling Modal state
  const [isSchedulingModalOpen, setIsSchedulingModalOpen] = useState(false)
  const [isCommandPaletteOpen, setIsCommandPaletteOpen] = useState(false)
  const [selectedCandidateForScheduling, setSelectedCandidateForScheduling] = useState<{
    name: string
    email: string
    id?: string
    job_title: string
    job_vacancy_id?: string
  } | null>(null)
  
  // Candidate Search states (Pearch Integration)
  const [isCandidateDetailOpen, setIsCandidateDetailOpen] = useState(false)
  const [selectedCandidateForDetail, setSelectedCandidateForDetail] = useState<CandidateResult | null>(null)
  const [isCreditDialogOpen, setIsCreditDialogOpen] = useState(false)
  const [pendingPearchSearch, setPendingPearchSearch] = useState<{
    query: string
    threadId?: string
  } | null>(null)
  
  // Smart Search Mode - expands input with dynamic tags
  const [isSmartSearchMode, setIsSmartSearchMode] = useState(false)
  const [smartSearchQuery, setSmartSearchQuery] = useState("")
  
  // Search Flow State Machine - controls the candidate search experience
  const searchFlow = useSearchFlow()
  const [searchPreviewData, setSearchPreviewData] = useState<SearchPreviewData | null>(null)
  const [hasSearchResults, setHasSearchResults] = useState(false)
  
  // Global Search Settings - provides default values for search filters
  const { settings: globalSearchSettings, loading: globalSettingsLoading } = useGlobalSearchSettings()
  
  // UI Actions System - Side panels and Chat Cards from agents
  const handlePanelSubmit = useCallback(async (data: PanelSubmitData) => {
    console.log("Panel submitted:", data)
    // Here you can send the data back to the backend or process it
  }, [])

  const handlePanelClose = useCallback((panelType: SidePanelType) => {
    console.log("Panel closed:", panelType)
  }, [])

  const handleChatCardAction = useCallback((cardType: ChatCardType, action: string, data: unknown) => {
    console.log("Chat card action:", { cardType, action, data })
    // Process chat card actions - e.g., schedule interview, view candidate details
    if (cardType === "candidate_summary" && action === "schedule") {
      const candidateData = data as { id: string; name: string; email?: string; title?: string }
      setSelectedCandidateForScheduling({
        name: candidateData.name,
        email: candidateData.email || "",
        id: candidateData.id,
        job_title: candidateData.title || "Candidato"
      })
      setIsSchedulingModalOpen(true)
    }
  }, [])

  const uiActions = useUIActions({
    onPanelSubmit: handlePanelSubmit,
    onPanelClose: handlePanelClose,
    onChatCardAction: handleChatCardAction,
    enableWebSocket: false // UI-actions WS (panels/cards) — kept disabled; token streaming uses useAgentStreaming below
  })

  // Advanced Filters Modal
  const [isFiltersModalOpen, setIsFiltersModalOpen] = useState(false)
  const [activeSearchFilters, setActiveSearchFilters] = useState<SearchFilters>({})
  
  // Empty Field Notifications - for job creation wizard
  const emptyFieldNotifications = useEmptyFieldNotifications()
  const [currentSuggestion, setCurrentSuggestion] = useState<FieldValueSuggestion | null>(null)
  const [isLoadingSuggestion, setIsLoadingSuggestion] = useState(false)
  const DEFAULT_COMPANY_ID = 'a1b2c3d4-e5f6-7890-abcd-ef1234567890'
  
  // Initialize search filters with global settings when loaded
  useEffect(() => {
    if (!globalSettingsLoading && globalSearchSettings) {
      setActiveSearchFilters(prev => ({
        ...prev,
        ppiOptions: {
          ...prev.ppiOptions,
          searchType: globalSearchSettings.searchType,
          highFreshness: globalSearchSettings.highFreshness,
          showEmails: globalSearchSettings.showEmails,
          showPhoneNumbers: globalSearchSettings.showPhoneNumbers
        }
      }))
    }
  }, [globalSettingsLoading, globalSearchSettings])
  
  // File Attachment states
  const [attachedFiles, setAttachedFiles] = useState<File[]>([])
  const [fileValidationError, setFileValidationError] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
  
  // File validation constants
  const MAX_FILE_SIZE_MB = 10
  const MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
  const ALLOWED_FILE_TYPES = {
    'application/pdf': 'PDF',
    'application/msword': 'DOC',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'DOCX',
    'text/plain': 'TXT',
    'text/csv': 'CSV',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': 'XLSX',
    'application/vnd.ms-excel': 'XLS',
    'image/png': 'PNG',
    'image/jpeg': 'JPG',
    'image/jpg': 'JPG'
  } as const
  
  // Voice Recording states
  const [isRecording, setIsRecording] = useState(false)
  const [recordingTime, setRecordingTime] = useState(0)
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null)
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const audioChunksRef = useRef<Blob[]>([])
  const recordingTimerRef = useRef<NodeJS.Timeout | null>(null)
  
  // Toast notifications
  const { toast } = useToast()
  
  // File analysis context - stores analyzed file data to include in messages
  const [fileAnalysisContext, setFileAnalysisContext] = useState<FileAnalysisResult | null>(null)
  
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const messagesContainerRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)
  
  // Detecta se a conversa está vazia para ajustar layout
  const isEmptyChat = messages.length === 0
  
  // Chat layout hook - gerencia estados de layout (empty, chat-only, chat-with-panel)
  const { mode: layoutMode, chatContainerClass, inputContainerClass, messagesContainerClass } = useChatLayout({
    isEmptyChat,
    isPanelOpen
  })
  
  // Ciclo fechado: detectar ação pendente na última mensagem da LIA
  const activePendingAction = useMemo(() => {
    const lastLia = [...messages].reverse().find(m => m.sender === "lia")
    const pending = lastLia?.data?.pending_action
    if (!pending || pending.awaiting_confirmation) return null
    if (!pending.missing_params?.length) return null
    return { intent: pending.intent as string, missing_params: pending.missing_params as string[] }
  }, [messages])

  // Sistema de Títulos Automáticos para Histórico
  // Use fixed initial value to avoid hydration mismatch
  const [chatId, setChatId] = useState("#0000")

  // Generate ID on client-side only
  useEffect(() => {
    const timestamp = Date.now()
    const id = String(timestamp).slice(-4)
    setChatId(`#${id}`)
  }, [])

  // ── Agent Streaming via WebSocket ────────────────────────────────────────
  // Receives LangGraph tokens in real-time from StreamingCallback → ws_manager.
  // Connects to /ws/chat/{wsSessionId}; tokens update the last LIA message live.
  // Falls back to SSE path when WS is not connected.
  const wsSessionId = chatId.replace('#', '')
  const {
    tokens: wsTokens,
    isStreaming: wsIsStreaming,
    isConnected: wsIsConnected,
    connect: wsConnect,
    disconnect: wsDisconnect,
    clearTokens: wsClearTokens,
    sendMessage: wsSendMessage,
  } = useAgentStreaming(wsSessionId)

  // Ref updated synchronously so finally{} can check it without async state lag
  const wsStreamingModeRef = useRef(false)

  // Connect once chatId settles to a real value (not the SSR placeholder '#0000')
  useEffect(() => {
    if (wsSessionId && wsSessionId !== '0000') {
      wsConnect()
    }
    return () => { wsDisconnect() }
  }, [wsSessionId, wsConnect, wsDisconnect])

  // Update last LIA message as WS tokens accumulate
  useEffect(() => {
    if (!wsStreamingModeRef.current || !wsTokens) return
    setMessages(prev => {
      const updated = [...prev]
      const last = updated[updated.length - 1]
      if (last?.sender === 'lia') {
        updated[updated.length - 1] = { ...last, content: wsTokens }
      }
      return updated
    })
  }, [wsTokens])

  // Reset isLoading when WS streaming ends (token_done received)
  useEffect(() => {
    if (wsStreamingModeRef.current && !wsIsStreaming && wsTokens) {
      wsStreamingModeRef.current = false
      setIsLoading(false)
    }
  }, [wsIsStreaming, wsTokens])
  // ─────────────────────────────────────────────────────────────────────────

  const [chatTitle, setChatTitle] = useState(() => {
    if (conversationType === 'empty') {
      return 'Nova Conversa'
    }
    
    // Detecta o tipo de conversa baseado nas primeiras mensagens
    const firstMessages = initialConversation.slice(0, 5).map(m => m.content.toLowerCase()).join(' ')
    
    if (firstMessages.includes('vaga') || firstMessages.includes('posição') || firstMessages.includes('diretor')) {
      // Tenta extrair o cargo específico
      const directorMatch = firstMessages.match(/diretor\s+de\s+(\w+)/i)
      if (directorMatch) {
        return `Vaga ${directorMatch[0].split(' ').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ')}`
      }
      return 'Nova Vaga'
    }
    
    if (firstMessages.includes('candidato') || firstMessages.includes('triagem')) {
      return 'Análise de Candidatos'
    }
    
    if (firstMessages.includes('relatório') || firstMessages.includes('dashboard')) {
      return 'Relatório & Analytics'
    }
    
    if (firstMessages.includes('onboarding')) {
      return 'Plano de Onboarding'
    }
    
    return 'Conversa Geral'
  })

  const [activeTab, setActiveTab] = useState<"conversa" | "controle">("conversa")
  
  // Função helper para atualizar título manualmente (útil para quando criar nova conversa)
  const updateChatTitle = useCallback((newTitle: string) => {
    setChatTitle(newTitle)
  }, [])

  // Process contextData from initial/seeded conversation messages
  useEffect(() => {
    // Only run once on mount to check if any initial message has contextData
    if (initialConversation.length > 0) {
      // Find the last message with contextData (most recent)
      const messageWithContext = initialConversation
        .slice()
        .reverse()
        .find(msg => msg.contextData)
      
      if (messageWithContext && messageWithContext.contextData) {
        setContextData(messageWithContext.contextData)
        setIsPanelOpen(true)
      }
    }
  }, []) // Empty dependency array - run only on mount

  // Fetch credit balance on mount
  useEffect(() => {
    const fetchCredits = async () => {
      try {
        const balance = await liaApi.getCreditBalance("demo-user")
        setAvailableCredits(balance.available_credits)
      } catch (error) {
        console.error("Error fetching credit balance:", error)
        // Keep default value (50) on error
      }
    }
    
    fetchCredits()
  }, []) // Empty dependency array - run only on mount

  // Escuta evento de "Novo Chat" do botão do sidebar
  useEffect(() => {
    const handleNewChat = () => {
      setMessages([])
      setInput("")
      setContextData(null)
      setIsPanelOpen(false)
      setChatTitle('Nova Conversa')
    }

    window.addEventListener('lia:new-chat', handleNewChat)
    return () => window.removeEventListener('lia:new-chat', handleNewChat)
  }, [])

  // Escuta evento de "Ver Pipeline" do Daily Briefing Card
  useEffect(() => {
    const handleOpenPipeline = async (event: CustomEvent) => {
      setChatTitle('Gerenciamento de Pipeline')
      setIsLoading(true)
      
      try {
        const report = await liaApi.getStaleCandidates(3, 50)
        
        if (report && report.groups) {
          setContextData({
            type: "pipeline-report",
            title: "Pipeline - Candidatos Parados",
            data: report
          })
          setIsPanelOpen(true)
          
          const totalStale = report.total_stale || report.groups.reduce(
            (acc: number, job: any) => acc + (job.stale_candidates?.length || 0), 0
          )
          
          const newMessage: Message = {
            id: Date.now(),
            sender: "lia",
            content: totalStale > 0 
              ? `Encontrei **${totalStale} candidatos** que estão parados há mais de 3 dias em **${report.groups.length} vagas**. No painel ao lado você pode ver o detalhamento e tomar ações rápidas para cada candidato.\n\nQuer que eu priorize alguma vaga específica ou sugira as próximas ações?`
              : `Ótimo! Todos os candidatos estão fluindo bem pelo pipeline. Nenhum candidato está parado há mais de 3 dias.\n\nPosso ajudar com outra coisa?`,
            timestamp: new Date().toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" }),
            type: "text"
          }
          setMessages(prev => [...prev, newMessage])
        }
      } catch (error) {
        console.error('Error fetching pipeline report:', error)
        const errorMessage: Message = {
          id: Date.now(),
          sender: "lia",
          content: "Desculpe, não consegui carregar os dados do pipeline. Tente novamente em alguns instantes.",
          timestamp: new Date().toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" }),
          type: "text"
        }
        setMessages(prev => [...prev, errorMessage])
      } finally {
        setIsLoading(false)
      }
    }

    window.addEventListener('lia-open-pipeline', handleOpenPipeline as EventListener)
    return () => window.removeEventListener('lia-open-pipeline', handleOpenPipeline as EventListener)
  }, [])

  // Escuta evento de "Nova Tarefa" do botão do Painel de Controle
  useEffect(() => {
    const handleNewTask = () => {
      setChatTitle('Nova Tarefa')
      
      const taskSuggestions = [
        { icon: '🔍', title: 'Buscar candidatos', description: 'Encontrar perfis que atendam aos requisitos de uma vaga' },
        { icon: '📋', title: 'Criar nova vaga', description: 'Definir uma nova posição com requisitos e benefícios' },
        { icon: '📞', title: 'Agendar entrevistas', description: 'Organizar entrevistas com candidatos selecionados' },
        { icon: '✉️', title: 'Enviar comunicações', description: 'Enviar emails ou mensagens para candidatos' },
        { icon: '📊', title: 'Gerar relatório', description: 'Criar análises e relatórios de recrutamento' },
        { icon: '🎯', title: 'Fazer triagem', description: 'Avaliar e qualificar candidatos de uma vaga' },
      ]
      
      const suggestionsText = taskSuggestions.map(s => `${s.icon} **${s.title}** - ${s.description}`).join('\n')
      
      const newMessage: Message = {
        id: Date.now(),
        sender: "lia",
        content: `Olá! Estou pronta para ajudar você a criar uma nova tarefa. O que você gostaria de fazer?\n\n${suggestionsText}\n\nDigite o que você precisa ou escolha uma das opções acima!`,
        timestamp: new Date().toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" }),
        type: "text"
      }
      setMessages(prev => [...prev, newMessage])
    }

    window.addEventListener('lia-new-task', handleNewTask)
    return () => window.removeEventListener('lia-new-task', handleNewTask)
  }, [])

  // Handler para ações de notificação de campos vazios
  const handleEmptyFieldAction = useCallback(async (action: string) => {
    const notification = emptyFieldNotifications.currentNotification
    if (!notification) return
    
    if (action === 'fill_now') {
      setIsLoadingSuggestion(true)
      const suggestion = await emptyFieldNotifications.getSuggestion(DEFAULT_COMPANY_ID, notification.field_key)
      setCurrentSuggestion(suggestion)
      setIsLoadingSuggestion(false)
      await emptyFieldNotifications.handleAction(DEFAULT_COMPANY_ID, notification.field_key, action)
    } else {
      await emptyFieldNotifications.handleAction(DEFAULT_COMPANY_ID, notification.field_key, action)
      setCurrentSuggestion(null)
      
      // Adiciona mensagem de confirmação no chat
      const confirmMessage: Message = {
        id: Date.now(),
        sender: "lia",
        content: action === 'remind_later' 
          ? `Certo! Vou lembrar você sobre o campo **${notification.field_label}** em 7 dias. Por enquanto, usarei dados alternativos para as sugestões.`
          : `Entendido! Não vou mais lembrar sobre o campo **${notification.field_label}**. Usarei dados alternativos quando necessário.`,
        timestamp: new Date().toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" }),
        type: "text"
      }
      setMessages(prev => [...prev, confirmMessage])
    }
  }, [emptyFieldNotifications])

  // Handler para quando o recrutador aceita uma sugestão
  const handleSuggestionAccepted = useCallback((fieldKey: string, value: any) => {
    const formattedValue = typeof value === 'object' ? JSON.stringify(value) : String(value)
    
    const confirmMessage: Message = {
      id: Date.now(),
      sender: "lia",
      content: `Ótimo! O campo **${fieldKey}** foi atualizado com: ${formattedValue}\n\nAgora posso usar esse valor nas minhas sugestões para esta e futuras vagas.`,
      timestamp: new Date().toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" }),
      type: "text"
    }
    setMessages(prev => [...prev, confirmMessage])
    setCurrentSuggestion(null)
  }, [])
  
  // Handler para quando o recrutador rejeita a sugestão
  const handleSuggestionRejected = useCallback(() => {
    setCurrentSuggestion(null)
    
    const confirmMessage: Message = {
      id: Date.now(),
      sender: "lia",
      content: `Sem problemas! Usarei dados alternativos para as sugestões. Você pode configurar esse campo a qualquer momento nas configurações da empresa.`,
      timestamp: new Date().toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" }),
      type: "text"
    }
    setMessages(prev => [...prev, confirmMessage])
  }, [])

  // Escuta evento de "Nova Vaga" do botão da página de Vagas
  useEffect(() => {
    const handleNewJob = async () => {
      setChatTitle('Nova Vaga')
      
      // Primeiro, verifica se há campos vazios com toggles ativos
      await emptyFieldNotifications.fetchNotifications(DEFAULT_COMPANY_ID)
      
      const newMessage: Message = {
        id: Date.now(),
        sender: "lia",
        content: `Olá! Sou a **LIA**, sua assistente de recrutamento. Vou ajudar você a criar uma nova vaga de forma conversacional.

Para começar, me conte sobre a posição que você precisa preencher:

**O que preciso saber:**
- Qual é o **cargo/título** da vaga?
- Para qual **departamento** ou **área** é essa posição?
- É uma vaga **presencial**, **híbrida** ou **remota**?

Você pode me contar livremente ou colar uma descrição de vaga existente que eu extraio as informações automaticamente!`,
        timestamp: new Date().toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" }),
        type: "text"
      }
      setMessages(prev => [...prev, newMessage])
    }

    window.addEventListener('lia-new-job', handleNewJob)
    return () => window.removeEventListener('lia-new-job', handleNewJob)
  }, [emptyFieldNotifications])

  // Escuta eventos da Biblioteca LIA
  useEffect(() => {
    const handleExecuteCommand = (event: CustomEvent) => {
      const { command, title } = event.detail
      setChatTitle(title || 'Comando da Biblioteca')
      
      const userMessage: Message = {
        id: Date.now(),
        sender: "user",
        content: command,
        timestamp: new Date().toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" }),
        type: "text"
      }
      setMessages(prev => [...prev, userMessage])
      
      setTimeout(() => {
        const liaResponse: Message = {
          id: Date.now() + 1,
          sender: "lia",
          content: `Entendido! Estou processando seu comando: **"${title}"**\n\nAguarde enquanto analiso as informações...`,
          timestamp: new Date().toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" }),
          type: "text"
        }
        setMessages(prev => [...prev, liaResponse])
      }, 500)
    }

    const handleLibraryPrompt = (event: CustomEvent) => {
      const { prompt } = event.detail
      setChatTitle('Conversa com LIA')
      
      const userMessage: Message = {
        id: Date.now(),
        sender: "user",
        content: prompt,
        timestamp: new Date().toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" }),
        type: "text"
      }
      setMessages(prev => [...prev, userMessage])
    }

    const handleLibraryCategory = (event: CustomEvent) => {
      const { category } = event.detail
      setChatTitle(`Explorar ${category}`)
      
      const newMessage: Message = {
        id: Date.now(),
        sender: "lia",
        content: `Vamos explorar comandos de **${category}**! O que você gostaria de fazer?\n\nPosso ajudar com tarefas como buscar informações, gerar relatórios, automatizar processos ou criar conteúdo relacionado a ${category.toLowerCase()}.\n\nMe conte sua necessidade!`,
        timestamp: new Date().toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" }),
        type: "text"
      }
      setMessages(prev => [...prev, newMessage])
    }

    window.addEventListener('lia-execute-command', handleExecuteCommand as EventListener)
    window.addEventListener('lia-library-prompt', handleLibraryPrompt as EventListener)
    window.addEventListener('lia-library-category', handleLibraryCategory as EventListener)
    
    return () => {
      window.removeEventListener('lia-execute-command', handleExecuteCommand as EventListener)
      window.removeEventListener('lia-library-prompt', handleLibraryPrompt as EventListener)
      window.removeEventListener('lia-library-category', handleLibraryCategory as EventListener)
    }
  }, [])

  // Função para converter timestamp para relativo
  const getRelativeTime = useCallback((timestamp: string) => {
    const now = new Date()
    const messageTime = new Date(`2024-02-22T${timestamp}:00`)
    const diffInMinutes = Math.floor((now.getTime() - messageTime.getTime()) / (1000 * 60))

    if (diffInMinutes < 1) return "agora"
    if (diffInMinutes < 60) return `há ${diffInMinutes} min`
    if (diffInMinutes < 1440) return `há ${Math.floor(diffInMinutes / 60)}h`
    return "ontem"
  }, [])

  // Sugestões de resposta rápida baseadas no contexto
  const getQuickSuggestions = useCallback(() => {
    const lastLiaMessage = messages.filter(m => m.sender === "lia").pop()
    if (!lastLiaMessage) return []

    const content = lastLiaMessage.content.toLowerCase()

    if (content.includes("competências") || content.includes("liderança")) {
      return ["Concordo", "Preciso de mais detalhes", "Vamos prosseguir"]
    }
    if (content.includes("remuneração") || content.includes("salário")) {
      return ["Está dentro do orçamento", "Precisamos ajustar", "Perfeito"]
    }
    if (content.includes("candidato") || content.includes("perfil")) {
      return ["Interessante", "Vamos agendar", "Preciso avaliar"]
    }
    return ["Entendi", "Continue", "Preciso de mais informações"]
  }, [messages])

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  // Calculate active filters count
  const getActiveFiltersCount = useCallback(() => {
    let count = 0
    Object.values(activeSearchFilters).forEach(category => {
      if (category) {
        Object.values(category).forEach(value => {
          if (value !== undefined && value !== null && value !== "" && 
              !(Array.isArray(value) && value.length === 0)) {
            count++
          }
        })
      }
    })
    return count
  }, [activeSearchFilters])

  // Handle filters apply
  const handleApplyFilters = useCallback((filters: SearchFilters) => {
    setActiveSearchFilters(filters)
    setIsFiltersModalOpen(false)
  }, [])

  // Smart Search Handlers
  const handleSmartSearchSubmit = useCallback(async (query: string, entities: ParsedEntities, mode?: SearchMode, metadata?: SearchMetadata) => {
    setIsSmartSearchMode(false)
    setSmartSearchQuery("")
    
    // Construct search metadata with mode and filters
    const finalMode = mode || "natural"
    const finalMetadata: SearchMetadata = metadata || { mode: finalMode }
    
    // Submit search with all context (mode, metadata, filters)
    searchFlow.submitSearch({
      query,
      entities,
      mode: finalMode,
      metadata: finalMetadata,
      filters: activeSearchFilters
    })
    
    // Add user message showing what they searched for (use unique timestamp-based IDs)
    const timestamp = Date.now()
    const userMessage: Message = {
      id: timestamp,
      sender: "user",
      content: query,
      timestamp: new Date().toLocaleTimeString("pt-BR", {
        hour: "2-digit",
        minute: "2-digit"
      }),
      type: "text"
    }
    setMessages(prev => [...prev, userMessage])
    
    // Set preview data with loading state
    setSearchPreviewData({
      query,
      localCount: 0,
      pearchEstimate: 0,
      pearchCredits: 0,
      isSearchingLocal: true,
      isEstimatingPearch: true
    })
    
    // Create enriched search query with detected entities
    let enrichedQuery = query
    if (entities.job_title || entities.skills?.length || entities.location) {
      const parts = []
      if (entities.job_title) parts.push(`cargo: ${entities.job_title}`)
      if (entities.location) parts.push(`local: ${entities.location}`)
      if (entities.skills?.length) parts.push(`skills: ${entities.skills.join(", ")}`)
      if (entities.years_experience) parts.push(`experiência: ${entities.years_experience}`)
      if (entities.seniority) parts.push(`senioridade: ${entities.seniority}`)
      enrichedQuery = `Buscar candidatos: ${query} [${parts.join(" | ")}]`
    }
    
    setIsLoading(true)
    
    try {
      // Execute real search via backend
      const response = await liaApi.sendMessage({
        content: enrichedQuery,
        user_id: "demo-user"
      })
      
      const workflowData = response.conversation?.workflow_data || response.message.message_metadata?.workflow_data
      const searchResults = workflowData?.search_results
      
      const localCount = searchResults?.local_count || searchResults?.local_candidates?.length || 0
      const globalCandidates = searchResults?.global_candidates || []
      
      // Update preview with real counts
      setSearchPreviewData({
        query,
        localCount,
        pearchEstimate: globalCandidates.length > 0 ? globalCandidates.length : Math.floor(Math.random() * 50) + 10,
        pearchCredits: Math.max(5, Math.ceil(localCount / 2) + 5),
        isSearchingLocal: false,
        isEstimatingPearch: false
      })
      
      // Store the response for later use (use unique ID to avoid duplicates)
      const liaResponse: Message = {
        id: timestamp + 1,
        sender: "lia",
        content: localCount > 0 
          ? `Encontrei **${localCount} candidato(s)** no banco proprietário que correspondem ao perfil.\n\nVocê pode ver os resultados abaixo ou expandir a busca para o banco global com 800M+ perfis.`
          : `Não encontrei candidatos correspondentes no banco proprietário, mas posso buscar no banco global com 800M+ perfis.`,
        timestamp: new Date().toLocaleTimeString("pt-BR", {
          hour: "2-digit",
          minute: "2-digit"
        }),
        type: "text",
        data: {
          workflow_data: workflowData
        }
      }
      
      setMessages(prev => [...prev.filter(m => m.type !== "thinking"), liaResponse])
      
      if (searchResults) {
        setHasSearchResults(true)
        searchFlow.showResults()
        
        const totalCount = localCount + globalCandidates.length
        if (totalCount > 0) {
          setContextData({
            type: "candidate-suggestions",
            title: `Candidatos Encontrados (${totalCount})`,
            data: {
              query: searchResults.query,
              source: searchResults.source,
              localCount,
              totalCount,
              candidates: [...(searchResults.local_candidates || []), ...globalCandidates]
            }
          })
          setIsPanelOpen(true)
        }
      }
      
    } catch (error) {
      console.error("Search error:", error)
      setSearchPreviewData(null)
      
      const errorMessage: Message = {
        id: timestamp + 2,
        sender: "lia",
        content: "Desculpe, ocorreu um erro ao buscar candidatos. Por favor, tente novamente.",
        timestamp: new Date().toLocaleTimeString("pt-BR", {
          hour: "2-digit",
          minute: "2-digit"
        }),
        type: "text"
      }
      setMessages(prev => [...prev.filter(m => m.type !== "thinking"), errorMessage])
    } finally {
      setIsLoading(false)
    }
  }, [searchFlow, activeSearchFilters])

  const handleSmartSearchCancel = useCallback(() => {
    setIsSmartSearchMode(false)
    setSmartSearchQuery("")
    searchFlow.reset()
    setSearchPreviewData(null)
  }, [searchFlow])

  // ============================================
  // FILE ATTACHMENT HANDLERS
  // ============================================
  const handleFileButtonClick = useCallback(() => {
    fileInputRef.current?.click()
  }, [])

  const handleFileChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (files && files.length > 0) {
      const newFiles = Array.from(files)
      const validFiles: File[] = []
      const errors: string[] = []
      
      newFiles.forEach(file => {
        if (file.size > MAX_FILE_SIZE_BYTES) {
          const sizeMB = (file.size / (1024 * 1024)).toFixed(1)
          errors.push(`"${file.name}" excede ${MAX_FILE_SIZE_MB}MB (${sizeMB}MB)`)
          return
        }
        
        if (!(file.type in ALLOWED_FILE_TYPES)) {
          const ext = file.name.split('.').pop()?.toUpperCase() || 'desconhecido'
          errors.push(`"${file.name}" tem tipo não suportado (.${ext})`)
          return
        }
        
        validFiles.push(file)
      })
      
      if (errors.length > 0) {
        const errorMessage = errors.length === 1 
          ? errors[0] 
          : `${errors.length} arquivos rejeitados:\n• ${errors.join('\n• ')}`
        setFileValidationError(errorMessage)
        
        setTimeout(() => setFileValidationError(null), 5000)
      }
      
      if (validFiles.length > 0) {
        setAttachedFiles(prev => [...prev, ...validFiles])
        
        const fileNames = validFiles.map(f => f.name).join(", ")
        const message = validFiles.length === 1
          ? `Arquivo "${fileNames}" anexado. O que gostaria que eu fizesse com ele?`
          : `${validFiles.length} arquivos anexados (${fileNames}). O que gostaria que eu fizesse com eles?`
        
        const liaResponse: Message = {
          id: Date.now(),
          sender: "lia",
          content: message,
          timestamp: new Date().toLocaleTimeString("pt-BR", {
            hour: "2-digit",
            minute: "2-digit"
          }),
          type: "text",
          actions: [
            { label: "Analisar CV", icon: FileText, variant: "default" },
            { label: "Extrair dados", icon: Database, variant: "outline" },
            { label: "Comparar perfis", icon: Users, variant: "outline" }
          ]
        }
        setMessages(prev => [...prev, liaResponse])
      }
    }
    if (e.target) {
      e.target.value = ""
    }
  }, [MAX_FILE_SIZE_BYTES, ALLOWED_FILE_TYPES])

  const handleRemoveFile = useCallback((index: number) => {
    setAttachedFiles(prev => prev.filter((_, i) => i !== index))
  }, [])

  // File Upload Button handlers
  const handleFilesSelected = useCallback((files: File[]) => {
    setAttachedFiles(prev => [...prev, ...files])
  }, [])

  const handleFileAnalyzed = useCallback((file: File, analysis: FileAnalysisResult) => {
    if (analysis.success) {
      setFileAnalysisContext(analysis)
      toast({
        title: "Arquivo analisado",
        description: `${file.name} foi processado. A análise será enviada junto com sua próxima mensagem.`,
      })
    } else {
      toast({
        title: "Erro na análise",
        description: analysis.error || `Não foi possível analisar ${file.name}`,
        variant: "destructive",
      })
    }
  }, [toast])

  // Audio Record Button handlers
  const handleAudioTranscription = useCallback((text: string) => {
    setInput(prev => prev ? `${prev} ${text}` : text)
    toast({
      title: "Áudio transcrito",
      description: "O texto foi adicionado ao campo de mensagem.",
    })
    inputRef.current?.focus()
  }, [toast])

  const handleAudioRecordingStart = useCallback(() => {
    toast({
      title: "Gravando...",
      description: "Fale sua mensagem. Clique novamente para parar.",
    })
  }, [toast])

  const handleAudioRecordingEnd = useCallback(() => {
    toast({
      title: "Processando áudio",
      description: "Aguarde enquanto transcrevemos sua mensagem.",
    })
  }, [toast])

  // ============================================
  // VOICE RECORDING HANDLERS
  // ============================================
  const startRecording = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const mediaRecorder = new MediaRecorder(stream)
      mediaRecorderRef.current = mediaRecorder
      audioChunksRef.current = []
      
      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data)
        }
      }
      
      mediaRecorder.onstop = () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: "audio/webm" })
        setAudioBlob(audioBlob)
        
        stream.getTracks().forEach(track => track.stop())
      }
      
      mediaRecorder.start()
      setIsRecording(true)
      setRecordingTime(0)
      
      recordingTimerRef.current = setInterval(() => {
        setRecordingTime(prev => prev + 1)
      }, 1000)
      
    } catch (error) {
      console.error("Error accessing microphone:", error)
      const errorMessage: Message = {
        id: Date.now(),
        sender: "lia",
        content: "Não consegui acessar o microfone. Por favor, verifique as permissões do navegador e tente novamente.",
        timestamp: new Date().toLocaleTimeString("pt-BR", {
          hour: "2-digit",
          minute: "2-digit"
        }),
        type: "text"
      }
      setMessages(prev => [...prev, errorMessage])
    }
  }, [recordingTime])

  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop()
      setIsRecording(false)
      
      if (recordingTimerRef.current) {
        clearInterval(recordingTimerRef.current)
        recordingTimerRef.current = null
      }
    }
  }, [isRecording])

  const handleRecordingToggle = useCallback(() => {
    if (isRecording) {
      stopRecording()
    } else {
      startRecording()
    }
  }, [isRecording, startRecording, stopRecording])

  // Cleanup recording timer on unmount
  useEffect(() => {
    return () => {
      if (recordingTimerRef.current) {
        clearInterval(recordingTimerRef.current)
      }
    }
  }, [])

  // Activate Smart Search Mode when LIA suggests insufficient data
  const activateSmartSearch = useCallback(() => {
    setIsSmartSearchMode(true)
    setSmartSearchQuery(input)
    setInput("")
    if (searchFlow.flowState === "idle") {
      searchFlow.startProfileCollection()
    }
  }, [input, searchFlow])

  // Detectar se há novas mensagens fora da área visível
  const checkNewMessageIndicator = useCallback(() => {
    if (!messagesContainerRef.current) return

    const container = messagesContainerRef.current
    const isAtBottom = container.scrollHeight - container.scrollTop <= container.clientHeight + 100

    setNewMessageIndicator(!isAtBottom && messages.length > 0)
  }, [messages.length])

  // Navegação por teclado
  useEffect(() => {
    const handleKeyboard = (e: KeyboardEvent) => {
      // Busca com Ctrl+F
      if (e.ctrlKey && e.key === 'f') {
        e.preventDefault()
        setShowSearch(true)
      }

      // Navegação com Ctrl+↑/↓
      if (e.ctrlKey && (e.key === 'ArrowUp' || e.key === 'ArrowDown')) {
        e.preventDefault()
        const direction = e.key === 'ArrowUp' ? -1 : 1
        const newIndex = Math.max(0, Math.min(messages.length - 1, currentMessageIndex + direction))
        setCurrentMessageIndex(newIndex)

        // Scroll para a mensagem
        const messageElements = document.querySelectorAll('[data-message-id]')
        if (messageElements[newIndex]) {
          messageElements[newIndex].scrollIntoView({ behavior: 'smooth', block: 'center' })
        }
      }

      // Fechar busca com Escape
      if (e.key === 'Escape') {
        setShowSearch(false)
        setSearchTerm("")
      }

      // Focar input com Ctrl+/
      if (e.ctrlKey && e.key === '/') {
        e.preventDefault()
        inputRef.current?.focus()
      }

      // Abrir Command Palette com Cmd+K ou Ctrl+K
      // Only if no input/textarea is focused (respect active element)
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        const activeElement = document.activeElement
        const isInputFocused = activeElement?.tagName === 'INPUT' || activeElement?.tagName === 'TEXTAREA'
        
        // Only open palette if not in input/textarea or if in our chat input
        if (!isInputFocused || activeElement === inputRef.current) {
          e.preventDefault()
          setIsCommandPaletteOpen(true)
        }
      }
    }

    window.addEventListener('keydown', handleKeyboard)
    return () => window.removeEventListener('keydown', handleKeyboard)
  }, [currentMessageIndex, messages.length])

  useEffect(() => {
    scrollToBottom()
    checkNewMessageIndicator()
  }, [messages, checkNewMessageIndicator])

  // Highlight de texto na busca
  const formatMessageContent = useCallback((text: string) => {
    // 1. Converter **texto** para <strong>texto</strong>
    let formatted = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    
    // 2. Converter quebras de linha duplas para parágrafos
    formatted = formatted.replace(/\n\n/g, '<br/><br/>')
    
    // 3. Converter quebras de linha simples para <br/>
    formatted = formatted.replace(/\n/g, '<br/>')
    
    // 4. Adicionar espaçamento extra após bullet points
    formatted = formatted.replace(/•\s/g, '• ')
    
    return formatted
  }, [])

  const highlightSearchTerm = useCallback((text: string, term: string) => {
    // Primeiro formata o conteúdo
    let formatted = formatMessageContent(text)
    
    // Depois aplica o highlight se houver termo de busca
    if (!term) return formatted
    const regex = new RegExp(`(${term})`, 'gi')
    return formatted.replace(regex, '<mark class="bg-yellow-200 dark:bg-yellow-800">$1</mark>')
  }, [formatMessageContent])

  const renderChatCard = useCallback((message: Message) => {
    if (!message.chatCardType || !message.chatCardData) return null
    
    const { chatCardType, chatCardData } = message
    
    const handleCardAction = (action: string) => {
      handleChatCardAction(chatCardType, action, chatCardData)
    }

    switch (chatCardType) {
      case "candidate_summary":
        return (
          <CandidateSummaryCard
            data={chatCardData as {
              id: string
              name: string
              title: string
              location: string
              experience_years: number
              skills: string[]
              match_score: number
              email?: string
              phone?: string
              linkedin_url?: string
              salary_expectation?: string
            }}
            onScheduleInterview={() => handleCardAction("schedule")}
            onViewDetails={() => handleCardAction("view_details")}
            onAddToShortlist={() => handleCardAction("add_shortlist")}
          />
        )
      case "wsi_score":
        return (
          <WSIScoreCard
            data={chatCardData as {
              candidate_name: string
              overall_score: number
              work_style: { score: number; details: string }
              independence: { score: number; details: string }
              consistency: { score: number; details: string }
            }}
            onViewDetails={() => handleCardAction("view_details")}
          />
        )
      case "compensation_summary":
        return (
          <CompensationSummaryCard
            data={chatCardData as {
              salary_range: { min: number; max: number; target: number }
              currency: string
              benefits: string[]
              equity?: string
              bonus?: string
            }}
            onEdit={() => handleCardAction("edit")}
            onApprove={() => handleCardAction("approve")}
          />
        )
      case "interview_confirmation":
        return (
          <InterviewConfirmationCard
            data={chatCardData as {
              candidate_name: string
              interview_date: string
              interview_time: string
              interview_type: "presencial" | "remoto" | "hibrido"
              interviewers: string[]
              location?: string
              meeting_link?: string
            }}
            onReschedule={() => handleCardAction("reschedule")}
            onCancel={() => handleCardAction("cancel")}
            onConfirm={() => handleCardAction("confirm")}
          />
        )
      case "progress_tracker":
        return (
          <ProgressTrackerCard
            data={chatCardData as {
              process_name: string
              current_stage: string
              stages: Array<{
                name: string
                status: "completed" | "current" | "pending"
                date?: string
              }>
              candidates_count?: number
            }}
            onViewDetails={() => handleCardAction("view_details")}
          />
        )
      case "job_summary":
        return (
          <JobSummaryCard
            data={chatCardData as {
              title: string
              department: string
              location: string
              salary_range: { min: number; max: number }
              requirements: string[]
              status: "draft" | "active" | "paused" | "closed"
            }}
            onEdit={() => handleCardAction("edit")}
            onPublish={() => handleCardAction("publish")}
            onViewCandidates={() => handleCardAction("view_candidates")}
          />
        )
      case "company_benefits":
        return (
          <CompanyBenefitsSummaryCard
            data={chatCardData as {
              benefits: Array<{
                id?: string
                name: string
                description?: string
                category: string
                value_type?: "monetary" | "percentage" | "informative"
                value?: number
                percentage_value?: number
                is_highlighted?: boolean
              }>
              total_count?: number
              highlighted_count?: number
            }}
            onViewAll={() => handleCardAction("view_all")}
            onAction={handleCardAction}
          />
        )
      default:
        return null
    }
  }, [handleChatCardAction])

  const handleSendMessage = useCallback(async (customContent?: string) => {
    const userMessageContent = customContent || input
    if (!userMessageContent.trim() || isLoading) return
    
    const normalizedContent = userMessageContent.toLowerCase().trim()
    
    // Intercept "Buscar candidatos" to activate profile collection flow
    const isSearchCandidatesRequest = 
      normalizedContent.includes('buscar candidatos') ||
      normalizedContent.includes('buscar candidato') ||
      normalizedContent.includes('encontrar candidatos') ||
      normalizedContent.includes('procurar candidatos') ||
      normalizedContent === 'buscar candidatos'
    
    if (isSearchCandidatesRequest && searchFlow.flowState === "idle") {
      const newMessage: Message = {
        id: messages.length + 1,
        sender: "user",
        content: userMessageContent,
        timestamp: new Date().toLocaleTimeString("pt-BR", {
          hour: "2-digit",
          minute: "2-digit"
        }),
        type: "text"
      }
      setMessages(prev => [...prev, newMessage])
      setInput("")
      
      // LIA asks for profile details instead of searching immediately
      const liaResponse: Message = {
        id: messages.length + 2,
        sender: "lia",
        content: `Vou te ajudar a encontrar os melhores candidatos! Para uma busca mais precisa, me conte sobre o perfil que você procura.

**O que você pode descrever:**
- **Cargo**: Ex: "Desenvolvedor Python Sênior", "Analista de Marketing"
- **Skills principais**: Ex: "Python, AWS, Docker" ou "SEO, Google Ads"
- **Localização**: Ex: "São Paulo", "remoto", "híbrido RJ"
- **Senioridade**: Ex: "júnior", "pleno", "sênior"

Digite abaixo o perfil ideal e vou buscar simultaneamente no nosso banco proprietário e no banco global com 800M+ perfis.`,
        timestamp: new Date().toLocaleTimeString("pt-BR", {
          hour: "2-digit",
          minute: "2-digit"
        }),
        type: "text"
      }
      setMessages(prev => [...prev, liaResponse])
      
      // Activate Smart Search mode for profile collection
      searchFlow.startProfileCollection()
      setIsSmartSearchMode(true)
      setSmartSearchQuery("")
      setChatTitle('Busca de Candidatos')
      return
    }
    
    const newMessage: Message = {
      id: messages.length + 1,
      sender: "user",
      content: userMessageContent,
      timestamp: new Date().toLocaleTimeString("pt-BR", {
        hour: "2-digit",
        minute: "2-digit"
      }),
      type: "text"
    }

    setMessages(prev => [...prev, newMessage])
    setInput("")
    setIsLoading(true)
    
    const currentAttachments = [...attachedFiles]
    const currentAudio = audioBlob
    const currentFileAnalysis = fileAnalysisContext
    
    setAttachedFiles([])
    setAudioBlob(null)
    setFileAnalysisContext(null)

    const thinkingMessage: Message = {
      id: messages.length + 2,
      sender: "lia",
      content: "",
      timestamp: new Date().toLocaleTimeString("pt-BR", {
        hour: "2-digit",
        minute: "2-digit"
      }),
      type: "thinking",
      thinkingMessage: currentAttachments.length > 0 
        ? "Processando arquivos e sua solicitação..." 
        : currentAudio 
          ? "Transcrevendo áudio e processando..." 
          : "Processando sua solicitação com IA..."
    }

    setMessages(prev => [...prev, thinkingMessage])

    try {
      const messageContent = currentFileAnalysis
        ? `${userMessageContent}\n\n[Contexto do arquivo analisado: ${currentFileAnalysis.filename}]\n${currentFileAnalysis.summary || ''}\n${currentFileAnalysis.extractedText ? `Texto extraído: ${currentFileAnalysis.extractedText.substring(0, 500)}...` : ''}`
        : userMessageContent

      // Use streaming for text-only messages (no attachments / audio)
      const useStreaming = currentAttachments.length === 0 && !currentAudio

      if (useStreaming && wsIsConnected) {
        // WS path — tokens arrive via LangGraph StreamingCallback (USE_LANGGRAPH_NATIVE=True)
        const streamingMessage: Message = {
          id: messages.length + 3,
          sender: "lia",
          content: "",
          timestamp: new Date().toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" }),
          type: "text",
        }
        setMessages(prev => {
          const newMsgs = [...prev]
          newMsgs[newMsgs.length - 1] = streamingMessage
          return newMsgs
        })
        wsClearTokens()
        wsStreamingModeRef.current = true
        wsSendMessage(messageContent)
        // isLoading reset by useEffect watching wsIsStreaming; finally block checks wsStreamingModeRef

      } else if (useStreaming) {
        // SSE path — fallback when WS is not connected (direct Anthropic streaming)
        const streamingMessage: Message = {
          id: messages.length + 3,
          sender: "lia",
          content: "",
          timestamp: new Date().toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" }),
          type: "text",
        }
        setMessages(prev => {
          const newMsgs = [...prev]
          newMsgs[newMsgs.length - 1] = streamingMessage
          return newMsgs
        })

        const streamResp = await fetch('/api/lia/chat/stream', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ content: messageContent }),
        })

        if (!streamResp.ok || !streamResp.body) {
          throw new Error(`Stream request failed: ${streamResp.status}`)
        }

        const reader = streamResp.body.getReader()
        const decoder = new TextDecoder()
        let accumulated = ""

        outer: while (true) {
          const { done, value } = await reader.read()
          if (done) break

          const rawChunk = decoder.decode(value, { stream: true })
          for (const line of rawChunk.split('\n')) {
            if (!line.startsWith('data: ')) continue
            const payload = line.slice(6).trim()
            if (payload === '[DONE]') break outer

            try {
              const parsed = JSON.parse(payload)
              if (parsed.token) {
                accumulated += parsed.token
                const snapshot = accumulated
                setMessages(prev => {
                  const updated = [...prev]
                  const last = updated[updated.length - 1]
                  if (last?.sender === "lia") {
                    updated[updated.length - 1] = { ...last, content: snapshot }
                  }
                  return updated
                })
              } else if (parsed.error) {
                throw new Error(parsed.error)
              }
            } catch (_) {
              // ignore partial JSON chunks
            }
          }
        }

      } else {
        // Fallback: regular (blocking) request for attachments / audio
        const response = await liaApi.sendMessage({
          content: messageContent,
          user_id: "demo-user",
          attachments: currentAttachments.length > 0 ? currentAttachments : undefined,
          audio: currentAudio || undefined
        })

        const liaResponse: Message = {
          id: messages.length + 3,
          sender: "lia",
          content: response.message.content,
          timestamp: new Date().toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" }),
          type: "text",
          data: {
            ...response.message.message_metadata,
            workflow_data: response.conversation?.workflow_data || response.message.message_metadata?.workflow_data
          }
        }

        const workflowData = response.conversation?.workflow_data || response.message.message_metadata?.workflow_data

        if (workflowData?.search_results) {
          const searchResults = workflowData.search_results
          const totalCount = (searchResults.local_candidates?.length || 0) + (searchResults.global_candidates?.length || 0)
          const panelData = {
            type: "candidate-suggestions" as const,
            title: `Candidatos Encontrados (${totalCount})`,
            data: {
              query: searchResults.query,
              source: searchResults.source,
              localCount: searchResults.local_count,
              totalCount,
              candidates: [...(searchResults.local_candidates || []), ...(searchResults.global_candidates || [])]
            }
          }
          liaResponse.contextData = panelData
          setContextData(panelData)
          setIsPanelOpen(true)
        } else if (response.conversation?.workflow_type === 'job_creation' && workflowData) {
          if (workflowData.completion_percentage !== undefined) {
            const jobState = workflowData
            const collectedFields = Object.keys(jobState.field_status || {}).filter(k => jobState.field_status[k] === 'collected')
            const pendingFields = Object.keys(jobState.field_status || {}).filter(k => jobState.field_status[k] === 'pending')
            const panelData = {
              type: "job-creation-progress" as const,
              title: "Progresso: Criação de Vaga",
              data: {
                completion_percentage: Math.round(jobState.completion_percentage || 0),
                collected_fields: collectedFields,
                pending_fields: pendingFields,
                next_panel: jobState.current_panel || 'Aguardando próxima etapa'
              }
            }
            liaResponse.contextData = panelData
            setContextData(panelData)
            setIsPanelOpen(true)
          } else if (workflowData.frames) {
            const frames = workflowData.frames
            let panelData: ContextPanelData | null = null
            if (frames.org_chart) panelData = { type: "org-chart", title: "Organograma da Posição", data: frames.org_chart }
            else if (frames.interview_flow) panelData = { type: "interview-flow", title: "Fluxo de Entrevistas", data: frames.interview_flow }
            else if (frames.timeline) panelData = { type: "timeline", title: "Cronograma de Recrutamento", data: frames.timeline }
            else if (frames.technical_matrix) panelData = { type: "technical-matrix", title: "Matriz Técnica - Requisitos da Vaga", data: frames.technical_matrix }
            if (panelData) {
              liaResponse.contextData = panelData
              setContextData(panelData)
              setIsPanelOpen(true)
            }
          }
        }

        setMessages(prev => {
          const newMessages = [...prev]
          newMessages[newMessages.length - 1] = liaResponse
          return newMessages
        })

        // Ciclo fechado: notificar outros componentes (ex: kanban) quando uma ação foi executada
        const actionResult = response.message.message_metadata?.action_result
        if (actionResult?.success) {
          window.dispatchEvent(
            new CustomEvent("lia:action-executed", {
              detail: { action_id: actionResult.action_id, data: actionResult.data }
            })
          )
        }
      }

    } catch (error) {
      console.error("Error sending message to LIA:", error)

      const errorMessage: Message = {
        id: messages.length + 3,
        sender: "lia",
        content: "Desculpe, ocorreu um erro ao processar sua mensagem. Por favor, tente novamente.",
        timestamp: new Date().toLocaleTimeString("pt-BR", {
          hour: "2-digit",
          minute: "2-digit"
        }),
        type: "text"
      }

      setMessages(prev => {
        const newMessages = [...prev]
        newMessages[newMessages.length - 1] = errorMessage
        return newMessages
      })
    } finally {
      // Skip resetting isLoading when WS streaming mode is active —
      // the useEffect watching wsIsStreaming will reset it when streaming ends.
      if (!wsStreamingModeRef.current) {
        setIsLoading(false)
      }
    }
  }, [input, isLoading, messages.length, wsIsConnected, wsSendMessage, wsClearTokens])

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  const handleActionClick = (message: Message, action: any) => {
    if (message.contextData) {
      setContextData({
        type: message.contextData.type,
        title: message.contextData.title,
        data: message.contextData.data
      })
      setIsPanelOpen(true)
    }
  }

  // AI-First Action Handlers
  const handleScheduleInterview = useCallback(() => {
    // Safe validation before dereferencing candidate data
    if (
      contextData?.type === 'candidate-suggestions' &&
      contextData.data?.candidates &&
      Array.isArray(contextData.data.candidates) &&
      contextData.data.candidates.length > 0
    ) {
      const candidate = contextData.data.candidates[0]
      
      // Ensure candidate has required fields
      if (candidate?.name) {
        setSelectedCandidateForScheduling({
          name: candidate.name,
          email: candidate.contact?.email || candidate.email || '',
          id: candidate.id || candidate.candidateId,
          job_title: candidate.current_title || 'Candidato',
          job_vacancy_id: candidate.job_vacancy_id // Preserve job vacancy ID from context
        })
        setIsSchedulingModalOpen(true)
        return
      }
    }
    
    // Fallback: send prompt to LIA if no valid candidate data
    handleSendMessage("agendar entrevista")
  }, [contextData, handleSendMessage])

  const handleEvaluateFit = useCallback(() => {
    handleSendMessage("avaliar fit técnico do candidato")
  }, [handleSendMessage])

  const handleGenerateEmail = useCallback(() => {
    handleSendMessage("gerar email de follow-up")
  }, [handleSendMessage])

  const handleSendWhatsApp = useCallback(() => {
    handleSendMessage("enviar mensagem whatsapp")
  }, [handleSendMessage])

  const handleCompareProfiles = useCallback(() => {
    handleSendMessage("comparar perfis de candidatos")
  }, [handleSendMessage])

  const handleViewAnalytics = useCallback(() => {
    // router.push('/indicadores')
    window.location.href = '/indicadores'
  }, [])

  const handlePipelineAction = useCallback(async (candidateId: string, actionId: string, candidateName: string) => {
    try {
      const result = await liaApi.executePipelineAction(candidateId, actionId)
      
      if (result.success) {
        const liaMessage: Message = {
          id: messages.length + 1,
          sender: "lia",
          content: result.message,
          timestamp: new Date().toLocaleTimeString("pt-BR", {
            hour: "2-digit",
            minute: "2-digit"
          }),
          type: "text"
        }
        setMessages(prev => [...prev, liaMessage])
        
        if (result.open_modal === "interview_scheduling") {
          setSelectedCandidateForScheduling({
            name: candidateName,
            id: candidateId,
            email: "",
            job_title: ""
          })
          setIsSchedulingModalOpen(true)
        }
        
        if (result.navigate) {
          window.location.href = result.navigate
        }
        
        if (contextData?.type === "pipeline-report") {
          const updatedData = await liaApi.getStaleCandidates()
          setContextData({
            type: "pipeline-report",
            title: "Pipeline de Candidatos",
            data: updatedData
          })
        }
      }
    } catch (error) {
      console.error("Error executing pipeline action:", error)
      const errorMessage: Message = {
        id: messages.length + 1,
        sender: "lia",
        content: "Desculpe, ocorreu um erro ao executar a ação. Tente novamente.",
        timestamp: new Date().toLocaleTimeString("pt-BR", {
          hour: "2-digit",
          minute: "2-digit"
        }),
        type: "text"
      }
      setMessages(prev => [...prev, errorMessage])
    }
  }, [messages.length, contextData])

  // Candidate Search Handlers (Pearch Integration)
  const handleSelectCandidate = useCallback((candidate: CandidateResult) => {
    setSelectedCandidateForDetail(candidate)
    setIsCandidateDetailOpen(true)
  }, [])

  const handleAddCandidatesToJob = useCallback((candidateIds: string[]) => {
    const count = candidateIds.length
    handleSendMessage(`Adicionar ${count} candidato(s) selecionado(s) à vaga atual`)
  }, [handleSendMessage])

  const handleCompareCandidates = useCallback((candidateIds: string[]) => {
    if (candidateIds.length >= 2) {
      handleSendMessage(`Comparar os ${candidateIds.length} candidatos selecionados`)
    }
  }, [handleSendMessage])

  const handleLoadMoreCandidates = useCallback((query: string, threadId?: string) => {
    setPendingPearchSearch({ query, threadId })
    setIsCreditDialogOpen(true)
  }, [])

  const handleConfirmPearchSearch = useCallback(() => {
    if (pendingPearchSearch) {
      handleSendMessage(`Buscar mais candidatos para "${pendingPearchSearch.query}" no banco global Pearch`)
      setIsCreditDialogOpen(false)
      setPendingPearchSearch(null)
    }
  }, [pendingPearchSearch, handleSendMessage])

  const handleAddCandidateToJob = useCallback((candidateId: string) => {
    handleSendMessage(`Adicionar candidato ${candidateId} à vaga atual`)
    setIsCandidateDetailOpen(false)
  }, [handleSendMessage])

  const handleSaveToBase = useCallback(async (candidateId: string) => {
    try {
      const result = await promoteCandidateToBase(candidateId)
      if (result.success) {
        if (selectedCandidateForDetail) {
          setSelectedCandidateForDetail({
            ...selectedCandidateForDetail,
            is_discovered: false,
            source: "local"
          })
        }
        if (contextData?.type === 'candidate-suggestions' && contextData.data?.candidates) {
          setContextData(prev => prev ? {
            ...prev,
            data: {
              ...prev.data,
              candidates: prev.data.candidates.map((c: any) => 
                c.id === candidateId 
                  ? { ...c, is_discovered: false, source: "local" }
                  : c
              )
            }
          } : null)
        }
        const liaMessage: Message = {
          id: Date.now(),
          sender: "lia",
          content: result.was_merged 
            ? `Candidato **${selectedCandidateForDetail?.name || 'selecionado'}** foi mesclado com perfil existente na sua base.`
            : `Candidato **${selectedCandidateForDetail?.name || 'selecionado'}** foi salvo na sua base local com sucesso!`,
          timestamp: new Date().toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" }),
          type: "text"
        }
        setMessages(prev => [...prev, liaMessage])
      }
    } catch (error) {
      console.error("Error promoting candidate:", error)
      const errorMessage: Message = {
        id: Date.now(),
        sender: "lia",
        content: "Desculpe, ocorreu um erro ao salvar o candidato na base. Por favor, tente novamente.",
        timestamp: new Date().toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" }),
        type: "text"
      }
      setMessages(prev => [...prev, errorMessage])
    }
  }, [selectedCandidateForDetail, contextData])

  // Command Palette Items
  const commandItems: CommandItem[] = [
    ...defaultCommands({
      onSchedule: handleScheduleInterview,
      onEvaluate: handleEvaluateFit,
      onEmail: handleGenerateEmail,
      onWhatsApp: handleSendWhatsApp,
      onCompare: handleCompareProfiles,
      onAnalytics: handleViewAnalytics
    }),
    // Prompt Suggestions integradas no Cmd+K
    {
      id: 'create-job',
      label: 'Criar Nova Vaga',
      description: 'Configure requisitos do sistema com descrição detalhada',
      category: 'Tarefas LIA',
      icon: Plus,
      shortcut: [],
      onExecute: () => handleSendMessage("Criar uma nova vaga")
    },
    {
      id: 'approve-job',
      label: 'Solicitar Aprovação de Vaga',
      description: 'Encaminhe documentação para aprovação gerencial',
      category: 'Tarefas LIA',
      icon: FileText,
      shortcut: [],
      onExecute: () => handleSendMessage("Solicite aprovação de nova vaga")
    },
    {
      id: 'share-candidates',
      label: 'Compartilhar Candidatos com Gestor',
      description: 'Crie relatório com perfis aprovados e recomendações',
      category: 'Tarefas LIA',
      icon: UserCheck,
      shortcut: [],
      onExecute: () => handleSendMessage("Compartilhe candidatos com gestor")
    },
    {
      id: 'feedback-interview',
      label: 'Solicitar Feedback de Entrevista',
      description: 'Colete avaliação detalhada pós-entrevista do gestor',
      category: 'Tarefas LIA',
      icon: MessageSquare,
      shortcut: [],
      onExecute: () => handleSendMessage("Solicite feedback de entrevista")
    },
    {
      id: 'candidate-info',
      label: 'Consultar Informações de Candidato',
      description: 'Obtenha histórico específico e histórico completo',
      category: 'Tarefas LIA',
      icon: Search,
      shortcut: [],
      onExecute: () => handleSendMessage("Consulte informações sobre candidato")
    },
    {
      id: 'add-candidate',
      label: 'Adicionar Novo Candidato',
      description: 'Cadastre perfil com talentos',
      category: 'Tarefas LIA',
      icon: UserCheck,
      shortcut: [],
      onExecute: () => handleSendMessage("Adicione novo candidato")
    },
    {
      id: 'reschedule-interview',
      label: 'Reagendar Entrevista',
      description: 'Cancele horário e notifique automaticamente participantes',
      category: 'Tarefas LIA',
      icon: Calendar,
      shortcut: [],
      onExecute: () => handleSendMessage("Reagende uma entrevista")
    },
    {
      id: 'update-status',
      label: 'Atualizar Status do Candidato',
      description: 'Modifique situação no processo e envie notificações',
      category: 'Tarefas LIA',
      icon: RefreshCcw,
      shortcut: [],
      onExecute: () => handleSendMessage("Atualize status do candidato")
    }
  ]

  // Quick Actions (contextual based on current context)
  const getQuickActions = (): QuickAction[] => {
    const baseActions: QuickAction[] = defaultCandidateActions.map(action => ({
      ...action,
      onClick: () => {
        switch (action.id) {
          case 'schedule':
            handleScheduleInterview()
            break
          case 'evaluate':
            handleEvaluateFit()
            break
          case 'email':
            handleGenerateEmail()
            break
          case 'whatsapp':
            handleSendWhatsApp()
            break
          case 'compare':
            handleCompareProfiles()
            break
          case 'analytics':
            handleViewAnalytics()
            break
        }
      }
    }))

    // Show only first 4 most relevant actions based on context
    if (contextData?.type === 'candidate-suggestions') {
      return baseActions.filter(a => ['schedule', 'evaluate', 'email', 'whatsapp'].includes(a.id))
    }
    
    return baseActions.slice(0, 4)
  }

  // Dynamic placeholder based on context
  const getPlaceholderText = (): string => {
    if (contextData?.type === 'candidate-suggestions') {
      return 'Ex: "agendar amanhã às 14h comigo" ou "avaliar fit técnico"'
    }
    if (contextData && contextData.data?.candidates?.length > 0) {
      const candidate = contextData.data.candidates[0]
      return `Pergunte sobre ${candidate.name}... Ex: "agendar entrevista com ${candidate.name.split(' ')[0]}"`
    }
    return 'Peça a LIA...'
  }

  const renderContextPanel = () => {
    if (!contextData || !isPanelOpen) return null

    return (
      <div className="w-2/5 p-4 flex transition-all duration-300 overflow-hidden" style={{ backgroundColor: 'var(--eleven-bg-main)' }}>
        {/* Card Container com bordas suaves e arredondadas */}
        <Card className="w-full border-0 rounded-3xl overflow-hidden flex flex-col" style={{ backgroundColor: 'var(--eleven-bg-card)' }}>
          {/* Header sem linha divisória */}
          <CardHeader className="p-6 border-0" style={{ backgroundColor: 'var(--eleven-bg-card)' }}>
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold" style={{ color: 'var(--eleven-text-primary)' }}>
                  {contextData.title}
                </h3>
                <p className="text-sm" style={{ color: 'var(--eleven-text-secondary)' }}>
                  Powered by LIA Intelligence
                </p>
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setIsPanelOpen(false)}
                className="rounded-full"
              >
                <X className="w-4 h-4" />
              </Button>
            </div>
          </CardHeader>

          {/* Content Area com scroll suave e altura flexível */}
          <CardContent
            className="flex-1 overflow-y-auto overflow-x-hidden p-6 space-y-6 scrollbar-thin scrollbar-thumb-gray-300 dark:scrollbar-thumb-gray-600 scrollbar-track-transparent hover:scrollbar-thumb-gray-400 dark:hover:scrollbar-thumb-gray-500"
            style={{
              scrollBehavior: 'smooth',
              minHeight: 0
            }}
          >
          {contextData.type === "compensation-package" && (
            <div className="space-y-6 font-open-sans">
              <Card className="border-0" style={{ backgroundColor: 'var(--eleven-bg-card)' }}>
                <CardHeader style={{ backgroundColor: 'var(--eleven-bg-message)' }}>
                  <CardTitle className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <DollarSign className="w-5 h-5 text-gray-600" />
                      <span className="text-gray-950 dark:text-gray-50">Pacote de Compensação</span>
                    </div>
                    <Badge variant="outline" style={{ borderColor: 'var(--eleven-border-subtle)', color: 'var(--eleven-text-secondary)' }}>
                      Inteligência de Mercado
                    </Badge>
                  </CardTitle>
                </CardHeader>
                <CardContent className="p-6">
                  <div className="space-y-6">
                    {/* Highlight Card */}
                    <div className="p-5 rounded-md" style={{ backgroundColor: 'var(--eleven-sepia-light)' }}>
                      <div className="flex items-center justify-between mb-4">
                        <div>
                          <p className="text-sm" style={{ color: 'var(--eleven-text-secondary)' }}>Recomendação LIA - Target</p>
                          <p className="text-xl font-bold" style={{ color: 'var(--eleven-text-primary)' }}>
                            {contextData.data.recommended_package.base_salary.target}
                          </p>
                        </div>
                        <Badge style={{ backgroundColor: 'var(--eleven-sepia-gold)', color: 'var(--eleven-text-primary)' }}>
                          Percentil 90
                        </Badge>
                      </div>
                      <p className="text-sm" style={{ color: 'var(--eleven-text-secondary)' }}>
                        {contextData.data.recommended_package.total_compensation.positioning}
                      </p>
                    </div>

                    {/* Benchmarking Grid */}
                    <div className="grid grid-cols-2 gap-4">
                      <div className="p-4 rounded-md border" style={{ backgroundColor: 'var(--eleven-bg-message)', borderColor: 'var(--eleven-border-subtle)' }}>
                        <h4 className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-3">Mediana de Mercado</h4>
                        <p className="text-lg font-semibold" style={{ color: 'var(--eleven-text-primary)' }}>
                          {contextData.data.market_analysis.salary_research.market_median}
                        </p>
                      </div>
                      <div className="p-4 rounded-md border" style={{ backgroundColor: 'var(--eleven-bg-message)', borderColor: 'var(--eleven-border-subtle)' }}>
                        <h4 className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-3">Faixa Recomendada</h4>
                        <p className="text-base font-semibold" style={{ color: 'var(--eleven-text-primary)' }}>
                          {contextData.data.recommended_package.base_salary.min} - {contextData.data.recommended_package.base_salary.max}
                        </p>
                      </div>
                    </div>

                    {/* Benefits */}
                    <div>
                      <h4 className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-3">Pacote de Benefícios</h4>
                      <div className="grid grid-cols-2 gap-2">
                        {Object.entries(contextData.data.recommended_package.benefits_package).map(([key, benefit]: [string, any], index) => (
                          <div key={index} className="flex items-center justify-between p-3 rounded-md" style={{ backgroundColor: 'var(--eleven-bg-message)' }}>
                            <span className="text-sm font-medium capitalize">{key.replace('_', ' ')}</span>
                            <span className="text-sm font-semibold" style={{ color: 'var(--eleven-text-primary)' }}>{benefit.estimated_value}</span>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Benchmarking Companies */}
                    <div>
                      <h4 className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-3">Benchmarking Competitivo</h4>
                      <div className="space-y-2">
                        {contextData.data.market_analysis.benchmarking_companies.map((company: any, index: number) => (
                          <div key={index} className="flex items-center justify-between p-3 rounded-md" style={{ backgroundColor: 'var(--eleven-bg-message)' }}>
                            <div>
                              <h5 className="font-medium" style={{ color: 'var(--eleven-text-primary)' }}>{company.company}</h5>
                              <p className="text-sm" style={{ color: 'var(--eleven-text-secondary)' }}>{company.notes}</p>
                            </div>
                            <Badge variant="outline" style={{ borderColor: 'var(--eleven-border-subtle)' }}>{company.range}</Badge>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Total Compensation */}
                    <div className="p-4 rounded-md border-2" style={{ backgroundColor: 'var(--eleven-bg-message)', borderColor: 'var(--eleven-border-subtle)' }}>
                      <div className="flex items-center justify-between">
                        <span className="text-base font-semibold" style={{ color: 'var(--eleven-text-primary)' }}>Compensação Total Anual</span>
                        <span className="text-xl font-bold" style={{ color: 'var(--eleven-text-primary)' }}>
                          {contextData.data.recommended_package.total_compensation.total_annual}
                        </span>
                      </div>
                    </div>

                    {/* Action Buttons */}
                    <div className="flex gap-3 pt-2">
                      <Button className="flex-1 border border-gray-200" style={{ backgroundColor: 'var(--eleven-bg-card)', color: 'var(--eleven-text-primary)' }}>
                        <Edit className="w-4 h-4 mr-2" />
                        Ajustar Valores
                      </Button>
                      <Button className="flex-1" style={{ backgroundColor: 'var(--eleven-sepia-gold)', color: 'var(--eleven-text-primary)' }}>
                        <CheckCircle className="w-4 h-4 mr-2" />
                        Aprovar Pacote
                      </Button>
                      <Button className="flex-1 border border-gray-200" style={{ backgroundColor: 'var(--eleven-bg-card)', color: 'var(--eleven-text-primary)' }}>
                        <Download className="w-4 h-4 mr-2" />
                        Exportar
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}

          {contextData.type === "org-structure-analysis" && (
            <div className="space-y-6 font-open-sans">
              <Card className="border-0" style={{ backgroundColor: 'var(--eleven-bg-card)' }}>
                <CardHeader style={{ backgroundColor: 'var(--eleven-bg-message)' }}>
                  <CardTitle className="flex items-center space-x-3">
                    <Network className="w-5 h-5 text-gray-600" />
                    <span className="text-gray-950 dark:text-gray-50">Análise da Estrutura Organizacional</span>
                  </CardTitle>
                </CardHeader>
                <CardContent className="p-6">
                  <div className="space-y-6">
                    {/* Highlight Card - Missing Layer */}
                    <div className="p-5 rounded-md" style={{ backgroundColor: 'var(--eleven-sepia-blue)' }}>
                      <h5 className="text-lg font-bold mb-2" style={{ color: 'var(--eleven-text-primary)' }}>
                        {contextData.data.current_structure.missing_layer.role}
                      </h5>
                      <p className="text-sm mb-3" style={{ color: 'var(--eleven-text-secondary)' }}>
                        {contextData.data.current_structure.missing_layer.purpose}
                      </p>
                      <div className="p-3 rounded-md" style={{ backgroundColor: 'var(--eleven-bg-message)' }}>
                        <p className="text-sm font-medium" style={{ color: 'var(--eleven-text-primary)' }}>
                          {contextData.data.current_structure.missing_layer.impact}
                        </p>
                      </div>
                    </div>

                    {/* Company Overview Grid */}
                    <div className="grid grid-cols-2 gap-4">
                      <div className="p-4 rounded-md border" style={{ backgroundColor: 'var(--eleven-bg-message)', borderColor: 'var(--eleven-border-subtle)' }}>
                        <h4 className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-3">Visão Geral da Empresa</h4>
                        <div className="space-y-2">
                          <div className="flex justify-between">
                            <span className="text-sm" style={{ color: 'var(--eleven-text-secondary)' }}>Porte:</span>
                            <span className="font-semibold" style={{ color: 'var(--eleven-text-primary)' }}>
                              {contextData.data.company_overview.size}
                            </span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-sm" style={{ color: 'var(--eleven-text-secondary)' }}>Setor:</span>
                            <span className="font-semibold" style={{ color: 'var(--eleven-text-primary)' }}>
                              {contextData.data.company_overview.industry}
                            </span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-sm" style={{ color: 'var(--eleven-text-secondary)' }}>Time Tech Atual:</span>
                            <span className="font-semibold" style={{ color: 'var(--eleven-text-primary)' }}>
                              {contextData.data.company_overview.current_tech_team} pessoas
                            </span>
                          </div>
                        </div>
                      </div>
                      
                      <div className="p-4 rounded-md border" style={{ backgroundColor: 'var(--eleven-bg-message)', borderColor: 'var(--eleven-border-subtle)' }}>
                        <h4 className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-3">Projeção de Crescimento</h4>
                        <div className="space-y-2">
                          <div className="flex justify-between">
                            <span className="text-sm" style={{ color: 'var(--eleven-text-secondary)' }}>6 meses:</span>
                            <span className="font-semibold" style={{ color: 'var(--eleven-text-primary)' }}>
                              {contextData.data.growth_projection.projected_6months} pessoas
                            </span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-sm" style={{ color: 'var(--eleven-text-secondary)' }}>12 meses:</span>
                            <span className="font-semibold" style={{ color: 'var(--eleven-text-primary)' }}>
                              {contextData.data.growth_projection.projected_12months} pessoas
                            </span>
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Action Buttons */}
                    <div className="flex gap-3 pt-2">
                      <Button className="flex-1 border border-gray-200" style={{ backgroundColor: 'var(--eleven-bg-card)', color: 'var(--eleven-text-primary)' }}>
                        <Edit className="w-4 h-4 mr-2" />
                        Editar Estrutura
                      </Button>
                      <Button className="flex-1" style={{ backgroundColor: 'var(--eleven-sepia-blue)', color: 'var(--eleven-text-primary)' }}>
                        <CheckCircle className="w-4 h-4 mr-2" />
                        Confirmar Análise
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}

          {contextData.type === "role-scope-definition" && (
            <div className="space-y-6 font-open-sans">
              <Card className="border-0" style={{ backgroundColor: 'var(--eleven-bg-card)' }}>
                <CardHeader style={{ backgroundColor: 'var(--eleven-bg-message)' }}>
                  <CardTitle className="flex items-center space-x-3">
                    <Target className="w-5 h-5 text-gray-600" />
                    <span className="text-gray-950 dark:text-gray-50">Definição do Escopo da Posição</span>
                  </CardTitle>
                </CardHeader>
                <CardContent className="p-6">
                  <div className="space-y-6">
                    {/* Highlight - Main Focus */}
                    <div className="p-5 rounded-md" style={{ backgroundColor: 'var(--eleven-sepia-gold)' }}>
                      <h4 className="text-sm font-medium mb-2" style={{ color: 'var(--eleven-text-secondary)' }}>Foco Principal</h4>
                      <p className="text-base font-bold" style={{ color: 'var(--eleven-text-primary)' }}>
                        {contextData.data.role_focus}
                      </p>
                    </div>

                    {/* Key Responsibilities */}
                    <div>
                      <h4 className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-3">Responsabilidades Principais</h4>
                      <div className="space-y-2">
                        {contextData.data.key_responsibilities.map((responsibility: string, index: number) => (
                          <div key={index} className="flex items-start space-x-3 p-3 rounded-md" style={{ backgroundColor: 'var(--eleven-sepia-mint)' }}>
                            <div className="w-1.5 h-1.5 rounded-full mt-2 flex-shrink-0" style={{ backgroundColor: 'var(--eleven-text-secondary)' }}></div>
                            <span className="text-sm" style={{ color: 'var(--eleven-text-primary)' }}>{responsibility}</span>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Action Buttons */}
                    <div className="flex gap-3 pt-2">
                      <Button className="flex-1 border border-gray-200" style={{ backgroundColor: 'var(--eleven-bg-card)', color: 'var(--eleven-text-primary)' }}>
                        <Edit className="w-4 h-4 mr-2" />
                        Editar Escopo
                      </Button>
                      <Button className="flex-1" style={{ backgroundColor: 'var(--eleven-sepia-gold)', color: 'var(--eleven-text-primary)' }}>
                        <CheckCircle className="w-4 h-4 mr-2" />
                        Aprovar Definição
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}

          {contextData.type === "work-arrangement" && (
            <div className="space-y-6 font-open-sans">
              <Card className="border-0" style={{ backgroundColor: 'var(--eleven-bg-card)' }}>
                <CardHeader style={{ backgroundColor: 'var(--eleven-bg-message)' }}>
                  <CardTitle className="flex items-center space-x-3 font-open-sans">
                    <Clock className="w-5 h-5 text-gray-600" />
                    <span className="text-gray-950 dark:text-gray-50">Modelo de Trabalho Híbrido</span>
                  </CardTitle>
                </CardHeader>
                <CardContent className="p-6">
                  <div className="space-y-4 font-open-sans">
                    <div className="grid grid-cols-2 gap-6">
                      <div>
                        <h4 className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-2">Modalidade</h4>
                        <p className="font-semibold">{contextData.data.arrangement}</p>
                      </div>
                      <div>
                        <h4 className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-2">Flexibilidade</h4>
                        <p className="font-semibold">{contextData.data.flexibility}</p>
                      </div>
                    </div>

                    <div className="grid grid-cols-2 gap-6">
                      <div>
                        <h4 className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-2">Dias Presenciais</h4>
                        <div className="flex flex-wrap gap-1">
                          {contextData.data.office_days.map((day: string, index: number) => (
                            <Badge key={index} variant="outline" className="text-xs">{day}</Badge>
                          ))}
                        </div>
                      </div>
                      <div>
                        <h4 className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-2">Home Office</h4>
                        <div className="flex flex-wrap gap-1">
                          {contextData.data.home_office_days.map((day: string, index: number) => (
                            <Badge key={index} variant="outline" className="text-xs">{day}</Badge>
                          ))}
                        </div>
                      </div>
                    </div>

                    <div>
                      <h4 className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-2">Benefícios Inclusos</h4>
                      <p className="text-sm text-gray-600 dark:text-gray-400">{contextData.data.benefits}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}

          {contextData.type === "final-job-description" && (
            <div className="space-y-6 font-open-sans">
              <Card className="border-0" style={{ backgroundColor: 'var(--eleven-bg-card)' }}>
                <CardHeader style={{ backgroundColor: 'var(--eleven-bg-message)' }}>
                  <CardTitle className="flex items-center space-x-3 font-open-sans">
                    <FileText className="w-5 h-5 text-gray-600" />
                    <span className="text-gray-950 dark:text-gray-50">Job Description Completo</span>
                  </CardTitle>
                </CardHeader>
                <CardContent className="p-6">
                  <div className="space-y-6 font-open-sans">
                    <div className="p-4 rounded-md" style={{ backgroundColor: 'var(--eleven-sepia-salmon)' }}>
                      <h3 className="text-base font-semibold" style={{ color: 'var(--eleven-text-primary)' }}>{contextData.data.header.title}</h3>
                      <p style={{ color: 'var(--eleven-text-secondary)' }}>{contextData.data.header.company} • {contextData.data.header.location}</p>
                      <p className="text-sm mt-2" style={{ color: 'var(--eleven-text-secondary)' }}>{contextData.data.header.salary_range}</p>
                    </div>

                    <div className="grid grid-cols-2 gap-6">
                      <div>
                        <h4 className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-3">Responsabilidades Principais</h4>
                        <div className="space-y-2">
                          {Object.entries(contextData.data.key_responsibilities).map(([key, items]: [string, any], index) => (
                            <div key={index}>
                              <h5 className="text-xs font-medium text-gray-600 uppercase tracking-wide mb-1">{key.replace('_', ' ')}</h5>
                              {items.slice(0, 2).map((item: string, i: number) => (
                                <div key={i} className="flex items-start space-x-2 text-sm mb-1">
                                  <div className="w-1 h-1 bg-gray-400 rounded-full mt-2 flex-shrink-0"></div>
                                  <span>{item}</span>
                                </div>
                              ))}
                            </div>
                          ))}
                        </div>
                      </div>

                      <div>
                        <h4 className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-3">Qualificações Essenciais</h4>
                        <div className="space-y-2">
                          {Object.entries(contextData.data.required_qualifications).map(([key, items]: [string, any], index) => (
                            <div key={index}>
                              <h5 className="text-xs font-medium text-gray-600 uppercase tracking-wide mb-1">{key.replace('_', ' ')}</h5>
                              {items.slice(0, 2).map((item: string, i: number) => (
                                <div key={i} className="flex items-start space-x-2 text-sm mb-1">
                                  <CheckCircle className="w-3 h-3 text-gray-600 mt-0.5 flex-shrink-0" />
                                  <span>{item}</span>
                                </div>
                              ))}
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>

                    <div className="border-t-0 pt-4">
                      <h4 className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-3">Pacote de Compensação</h4>
                      <div className="grid grid-cols-3 gap-4 text-center">
                        <div>
                          <p className="text-sm font-semibold" style={{ color: 'var(--eleven-text-primary)' }}>
                            {contextData.data.compensation_highlights.total_package.split(' ')[1]}
                          </p>
                          <p className="text-xs text-gray-600">Total Anual</p>
                        </div>
                        <div>
                          <p className="text-sm font-medium">{contextData.data.compensation_highlights.variable_bonus}</p>
                          <p className="text-xs text-gray-600">Bônus Variável</p>
                        </div>
                        <div>
                          <p className="text-sm font-medium">{contextData.data.compensation_highlights.benefits_value}</p>
                          <p className="text-xs text-gray-600">Benefícios</p>
                        </div>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}

          {contextData.type === "job-publishing" && (
            <div className="space-y-6 font-open-sans">
              <Card className="border-0" style={{ backgroundColor: 'var(--eleven-bg-card)' }}>
                <CardHeader style={{ backgroundColor: 'var(--eleven-bg-message)' }}>
                  <CardTitle className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <Globe className="w-5 h-5 text-gray-600" />
                      <span className="text-gray-950 dark:text-gray-50">Publicação Multi-Canal</span>
                    </div>
                    <Badge style={{ backgroundColor: 'var(--eleven-sepia-mint)', color: 'var(--eleven-text-primary)' }}>
                      {contextData.data.ats_integration.status}
                    </Badge>
                  </CardTitle>
                </CardHeader>
                <CardContent className="p-6">
                  <div className="space-y-6">
                    {/* ATS Integration Highlight */}
                    <div className="p-5 rounded-md" style={{ backgroundColor: 'var(--eleven-sepia-blue)' }}>
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-sm font-medium" style={{ color: 'var(--eleven-text-secondary)' }}>Sistema ATS Integrado</p>
                          <h4 className="text-base font-bold mt-1" style={{ color: 'var(--eleven-text-primary)' }}>
                            {contextData.data.ats_integration.system}
                          </h4>
                        </div>
                        <div className="text-right">
                          <p className="text-xs" style={{ color: 'var(--eleven-text-secondary)' }}>Job ID</p>
                          <p className="text-sm font-mono font-semibold" style={{ color: 'var(--eleven-text-primary)' }}>
                            {contextData.data.ats_integration.job_id}
                          </p>
                        </div>
                      </div>
                    </div>

                    {/* Publication Channels */}
                    <div>
                      <h4 className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-3">Canais de Publicação</h4>
                      <div className="space-y-2">
                        {contextData.data.publication_channels.map((channel: any, index: number) => (
                          <div key={index} className="flex items-center justify-between p-4 rounded-md" style={{ backgroundColor: 'var(--eleven-bg-message)' }}>
                            <div className="flex-1">
                              <h5 className="font-medium" style={{ color: 'var(--eleven-text-primary)' }}>{channel.platform}</h5>
                              <p className="text-sm mt-1" style={{ color: 'var(--eleven-text-secondary)' }}>
                                {channel.reach} • {channel.budget}
                              </p>
                            </div>
                            <Badge variant="outline" style={{ borderColor: 'var(--eleven-border-subtle)', color: 'var(--eleven-text-primary)' }}>
                              {channel.status}
                            </Badge>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Success Metrics */}
                    <div>
                      <h4 className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-3">Metas de Sucesso</h4>
                      <div className="grid grid-cols-2 gap-3">
                        {Object.entries(contextData.data.success_metrics.targets).map(([key, value]: [string, any], index) => (
                          <div key={index} className="text-center p-4 rounded-md border" style={{ backgroundColor: 'var(--eleven-bg-message)', borderColor: 'var(--eleven-border-subtle)' }}>
                            <p className="text-lg font-bold" style={{ color: 'var(--eleven-text-primary)' }}>{String(value)}</p>
                            <p className="text-xs mt-1 capitalize" style={{ color: 'var(--eleven-text-secondary)' }}>
                              {key.replace('_', ' ')}
                            </p>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Action Buttons */}
                    <div className="flex gap-3 pt-2">
                      <Button className="flex-1 border border-gray-200" style={{ backgroundColor: 'var(--eleven-bg-card)', color: 'var(--eleven-text-primary)' }}>
                        <Edit className="w-4 h-4 mr-2" />
                        Editar Canais
                      </Button>
                      <Button className="flex-1" style={{ backgroundColor: 'var(--eleven-sepia-mint)', color: 'var(--eleven-text-primary)' }}>
                        <Send className="w-4 h-4 mr-2" />
                        Publicar Vaga
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}

          {contextData.type === "sourcing-progress" && (
            <div className="space-y-6 font-open-sans">
              <Card className="border-0" style={{ backgroundColor: 'var(--eleven-bg-card)' }}>
                <CardHeader style={{ backgroundColor: 'var(--eleven-bg-message)' }}>
                  <CardTitle className="flex items-center space-x-3">
                    <TrendingUp className="w-5 h-5 text-gray-600" />
                    <span className="text-gray-950 dark:text-gray-50">Progress do Sourcing - Tempo Real</span>
                  </CardTitle>
                </CardHeader>
                <CardContent className="p-6">
                  <div className="space-y-6">
                    {/* Metrics Grid */}
                    <div className="grid grid-cols-4 gap-3">
                      <div className="text-center p-4 rounded-md" style={{ backgroundColor: 'var(--eleven-sepia-light)' }}>
                        <p className="text-lg font-bold" style={{ color: 'var(--eleven-text-primary)' }}>
                          {contextData.data.realtime_metrics.applications_received}
                        </p>
                        <p className="text-xs mt-1" style={{ color: 'var(--eleven-text-secondary)' }}>Aplicações</p>
                      </div>
                      <div className="text-center p-4 rounded-md" style={{ backgroundColor: 'var(--eleven-sepia-mint)' }}>
                        <p className="text-lg font-bold" style={{ color: 'var(--eleven-text-primary)' }}>
                          {contextData.data.realtime_metrics.active_sourcing_reached}
                        </p>
                        <p className="text-xs mt-1" style={{ color: 'var(--eleven-text-secondary)' }}>Sourcing Ativo</p>
                      </div>
                      <div className="text-center p-4 rounded-md" style={{ backgroundColor: 'var(--eleven-sepia-coral)' }}>
                        <p className="text-lg font-bold" style={{ color: 'var(--eleven-text-primary)' }}>
                          {contextData.data.realtime_metrics.response_rate}
                        </p>
                        <p className="text-xs mt-1" style={{ color: 'var(--eleven-text-secondary)' }}>Taxa Resposta</p>
                      </div>
                      <div className="text-center p-4 rounded-md" style={{ backgroundColor: 'var(--eleven-sepia-blue)' }}>
                        <p className="text-lg font-bold" style={{ color: 'var(--eleven-text-primary)' }}>
                          {contextData.data.realtime_metrics.avg_candidate_score}
                        </p>
                        <p className="text-xs mt-1" style={{ color: 'var(--eleven-text-secondary)' }}>Score Médio</p>
                      </div>
                    </div>

                    {/* Top Candidates */}
                    <div>
                      <h4 className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-3">Candidatos Top Performance</h4>
                      <div className="space-y-2">
                        {contextData.data.top_candidates.map((candidate: any, index: number) => (
                          <div key={index} className="p-4 rounded-md" style={{ backgroundColor: 'var(--eleven-bg-message)' }}>
                            <div className="flex items-center justify-between mb-3">
                              <div>
                                <h5 className="font-medium" style={{ color: 'var(--eleven-text-primary)' }}>{candidate.name}</h5>
                                <p className="text-sm" style={{ color: 'var(--eleven-text-secondary)' }}>{candidate.current_role}</p>
                              </div>
                              <Badge style={{ backgroundColor: 'var(--eleven-sepia-gold)', color: 'var(--eleven-text-primary)' }}>
                                Score: {candidate.score}
                              </Badge>
                            </div>
                            <div className="flex flex-wrap gap-2 mb-2">
                              {candidate.highlights.map((highlight: string, i: number) => (
                                <Badge key={i} variant="outline" className="text-xs" style={{ borderColor: 'var(--eleven-border-subtle)' }}>
                                  {highlight}
                                </Badge>
                              ))}
                            </div>
                            <p className="text-xs" style={{ color: 'var(--eleven-text-tertiary)' }}>
                              Status: {candidate.status}
                            </p>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Action Buttons */}
                    <div className="flex gap-3 pt-2">
                      <Button className="flex-1 border border-gray-200" style={{ backgroundColor: 'var(--eleven-bg-card)', color: 'var(--eleven-text-primary)' }}>
                        <Eye className="w-4 h-4 mr-2" />
                        Ver Pipeline Completo
                      </Button>
                      <Button className="flex-1" style={{ backgroundColor: 'var(--eleven-sepia-blue)', color: 'var(--eleven-text-primary)' }}>
                        <Send className="w-4 h-4 mr-2" />
                        Convidar Candidatos
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}

          {contextData.type === "interview-management" && (
            <div className="space-y-6 font-open-sans">
              <Card className="border-0" style={{ backgroundColor: 'var(--eleven-bg-card)' }}>
                <CardHeader style={{ backgroundColor: 'var(--eleven-bg-message)' }}>
                  <CardTitle className="flex items-center space-x-3 font-open-sans">
                    <Calendar className="w-5 h-5 text-gray-600" />
                    <span className="text-gray-950 dark:text-gray-50">Gestão de Entrevistas</span>
                  </CardTitle>
                </CardHeader>
                <CardContent className="p-6">
                  <div className="space-y-6 font-open-sans">
                    <div>
                      <h4 className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-3">Cronograma de Screening</h4>
                      <div className="space-y-3 font-open-sans">
                        {contextData.data.screening_schedule.map((interview: any, index: number) => (
                          <div key={index} className="flex items-center justify-between p-3 rounded-md">
                            <div>
                              <h5 className="font-medium text-gray-950 dark:text-gray-50">{interview.candidate}</h5>
                              <p className="text-sm text-gray-600">{interview.date} • {interview.time}</p>
                              <p className="text-xs text-gray-600">{interview.interviewer}</p>
                            </div>
                            <Badge 
                              variant="outline" 
                              style={{ 
                                backgroundColor: interview.status === 'Confirmed' ? 'var(--eleven-sepia-mint)' : 'var(--eleven-sepia-gold)',
                                borderColor: 'var(--eleven-border-subtle)',
                                color: 'var(--eleven-text-primary)'
                              }}
                            >
                              {interview.status}
                            </Badge>
                          </div>
                        ))}
                      </div>
                    </div>

                    <div>
                      <h4 className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-3">Estrutura do Processo</h4>
                      <div className="grid grid-cols-2 gap-4">
                        {Object.entries(contextData.data.interview_structure).map(([key, stage]: [string, any], index) => (
                          <div key={index} className="p-3 bg-gray-50 dark:bg-gray-700 rounded-md">
                            <h5 className="font-medium capitalize mb-2">{key.replace('stage_', 'Etapa ').replace('_', ' ')}</h5>
                            <div className="text-sm space-y-1">
                              <p><span className="text-gray-600">Duração:</span> {stage.duration}</p>
                              <p><span className="text-gray-600">Entrevistador:</span> {stage.interviewer}</p>
                              <p><span className="text-gray-600">Critério:</span> {stage.success_criteria}</p>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}

          {contextData.type === "final-selection" && (
            <div className="space-y-6 font-open-sans">
              <Card className="border-0" style={{ backgroundColor: 'var(--eleven-bg-card)' }}>
                <CardHeader style={{ backgroundColor: 'var(--eleven-bg-message)' }}>
                  <CardTitle className="flex items-center space-x-3 font-open-sans">
                    <UserCheck className="w-5 h-5 text-gray-600" />
                    <span className="text-gray-950 dark:text-gray-50">Seleção Final</span>
                  </CardTitle>
                </CardHeader>
                <CardContent className="p-6">
                  <div className="space-y-6 font-open-sans">
                    <div className="p-4 rounded-md" style={{ backgroundColor: 'var(--eleven-sepia-mint)' }}>
                      <h4 className="font-medium" style={{ color: 'var(--eleven-text-primary)' }}>Candidato Selecionado: Carlos Mendonça</h4>
                      <p className="text-sm" style={{ color: 'var(--eleven-text-secondary)' }}>Score Final: 94/100 • Cultural Fit: Excelente</p>
                    </div>

                    <div>
                      <h4 className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-3">Processo de Finalização</h4>
                      <div className="space-y-3 font-open-sans">
                        <div className="flex items-center justify-between p-3 rounded-md" style={{ backgroundColor: 'var(--eleven-bg-message)' }}>
                          <span className="text-sm font-medium">Referências Profissionais</span>
                          <Badge style={{ backgroundColor: 'var(--eleven-sepia-mint)', color: 'var(--eleven-text-primary)' }}>Concluído</Badge>
                        </div>
                        <div className="flex items-center justify-between p-3 rounded-md" style={{ backgroundColor: 'var(--eleven-bg-message)' }}>
                          <span className="text-sm font-medium">Background Check</span>
                          <Badge style={{ backgroundColor: 'var(--eleven-sepia-mint)', color: 'var(--eleven-text-primary)' }}>Aprovado</Badge>
                        </div>
                        <div className="flex items-center justify-between p-3 rounded-md" style={{ backgroundColor: 'var(--eleven-bg-message)' }}>
                          <span className="text-sm font-medium">Proposta Salarial</span>
                          <Badge style={{ backgroundColor: 'var(--eleven-sepia-blue)', color: 'var(--eleven-text-primary)' }}>Aceita</Badge>
                        </div>
                      </div>
                    </div>

                    <div>
                      <h4 className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-3">Detalhes da Contratação</h4>
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <p className="text-xs text-gray-600 mb-1">Data de Início:</p>
                          <p className="font-medium">15 de Março, 2024</p>
                        </div>
                        <div>
                          <p className="text-xs text-gray-600 mb-1">Salário Negociado:</p>
                          <p className="font-semibold" style={{ color: 'var(--eleven-text-primary)' }}>R$ 47.500</p>
                        </div>
                      </div>
                    </div>

                    {/* Botões de Ação */}
                    <div className="flex gap-3 pt-4">
                      <Button className="flex-1 border border-gray-200" style={{ backgroundColor: 'var(--eleven-bg-card)', color: 'var(--eleven-text-primary)' }}>
                        <Edit className="w-4 h-4 mr-2" />
                        Revisar Proposta
                      </Button>
                      <Button className="flex-1" style={{ backgroundColor: 'var(--eleven-sepia-mint)', color: 'var(--eleven-text-primary)' }}>
                        <CheckCircle className="w-4 h-4 mr-2" />
                        Confirmar Seleção
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}

          {contextData.type === "onboarding-plan" && (
            <div className="space-y-6 font-open-sans">
              <Card className="border-0" style={{ backgroundColor: 'var(--eleven-bg-card)' }}>
                <CardHeader style={{ backgroundColor: 'var(--eleven-bg-message)' }}>
                  <CardTitle className="flex items-center space-x-3 font-open-sans">
                    <Workflow className="w-5 h-5 text-gray-600" />
                    <span className="text-gray-950 dark:text-gray-50">Plano de Onboarding</span>
                  </CardTitle>
                </CardHeader>
                <CardContent className="p-6">
                  <div className="space-y-6 font-open-sans">
                    <div className="p-5 rounded-md" style={{ backgroundColor: 'var(--eleven-sepia-blue)' }}>
                      <h4 className="text-base font-bold mb-2" style={{ color: 'var(--eleven-text-primary)' }}>Programa de 90 Dias</h4>
                      <p className="text-sm" style={{ color: 'var(--eleven-text-secondary)' }}>Integração estratégica e cultural personalizada</p>
                    </div>

                    <div>
                      <h4 className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-3">Primeiros 30 Dias</h4>
                      <div className="space-y-2">
                        <div className="flex items-start space-x-3 p-3 rounded-md" style={{ backgroundColor: 'var(--eleven-bg-message)' }}>
                          <div className="w-1.5 h-1.5 rounded-full mt-2 flex-shrink-0" style={{ backgroundColor: 'var(--eleven-text-secondary)' }}></div>
                          <span className="text-sm">Imersão na cultura e processos da empresa</span>
                        </div>
                        <div className="flex items-start space-x-3 p-3 rounded-md" style={{ backgroundColor: 'var(--eleven-bg-message)' }}>
                          <div className="w-1.5 h-1.5 rounded-full mt-2 flex-shrink-0" style={{ backgroundColor: 'var(--eleven-text-secondary)' }}></div>
                          <span className="text-sm">Reuniões 1:1 com stakeholders principais</span>
                        </div>
                        <div className="flex items-start space-x-3 p-3 rounded-md" style={{ backgroundColor: 'var(--eleven-bg-message)' }}>
                          <div className="w-1.5 h-1.5 rounded-full mt-2 flex-shrink-0" style={{ backgroundColor: 'var(--eleven-text-secondary)' }}></div>
                          <span className="text-sm">Análise do estado atual da infraestrutura TI</span>
                        </div>
                      </div>
                    </div>

                    <div>
                      <h4 className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-3">60-90 Dias</h4>
                      <div className="space-y-2">
                        <div className="flex items-start space-x-3 p-3 rounded-md" style={{ backgroundColor: 'var(--eleven-bg-message)' }}>
                          <div className="w-1.5 h-1.5 rounded-full mt-2 flex-shrink-0" style={{ backgroundColor: 'var(--eleven-text-secondary)' }}></div>
                          <span className="text-sm">Apresentação do plano estratégico de transformação digital</span>
                        </div>
                        <div className="flex items-start space-x-3 p-3 rounded-md" style={{ backgroundColor: 'var(--eleven-bg-message)' }}>
                          <div className="w-1.5 h-1.5 rounded-full mt-2 flex-shrink-0" style={{ backgroundColor: 'var(--eleven-text-secondary)' }}></div>
                          <span className="text-sm">Início das primeiras iniciativas de melhoria</span>
                        </div>
                      </div>
                    </div>

                    {/* Botões de Ação */}
                    <div className="flex gap-3 pt-4">
                      <Button className="flex-1 border border-gray-200" style={{ backgroundColor: 'var(--eleven-bg-card)', color: 'var(--eleven-text-primary)' }}>
                        <Edit className="w-4 h-4 mr-2" />
                        Editar Cronograma
                      </Button>
                      <Button className="flex-1" style={{ backgroundColor: 'var(--eleven-sepia-blue)', color: 'var(--eleven-text-primary)' }}>
                        <CheckCircle className="w-4 h-4 mr-2" />
                        Aprovar Plano
                      </Button>
                      <Button className="flex-1 border border-gray-200" style={{ backgroundColor: 'var(--eleven-bg-card)', color: 'var(--eleven-text-primary)' }}>
                        <Download className="w-4 h-4 mr-2" />
                        Exportar PDF
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}

          {contextData.type === "performance-management" && (
            <div className="space-y-6 font-open-sans">
              <Card className="border-0" style={{ backgroundColor: 'var(--eleven-bg-card)' }}>
                <CardHeader style={{ backgroundColor: 'var(--eleven-bg-message)' }}>
                  <CardTitle className="flex items-center space-x-3 font-open-sans">
                    <Target className="w-5 h-5 text-gray-600" />
                    <span className="text-gray-950 dark:text-gray-50">Gestão de Performance</span>
                  </CardTitle>
                </CardHeader>
                <CardContent className="p-6">
                  <div className="space-y-6 font-open-sans">
                    <div className="p-4 rounded-md" style={{ backgroundColor: 'var(--eleven-sepia-gold)' }}>
                      <h4 className="font-medium" style={{ color: 'var(--eleven-text-primary)' }}>Framework de Avaliação Anual</h4>
                      <p className="text-sm" style={{ color: 'var(--eleven-text-secondary)' }}>OKRs + 360-feedback + desenvolvimento contínuo</p>
                    </div>

                    <div>
                      <h4 className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-3">OKRs do Primeiro Ano</h4>
                      <div className="space-y-3 font-open-sans">
                        <div className="p-3 rounded-md">
                          <h5 className="font-medium text-gray-950 dark:text-gray-50">Objetivo 1: Transformação Digital</h5>
                          <p className="text-sm text-gray-600">Migrar 80% dos sistemas para cloud em 12 meses</p>
                        </div>
                        <div className="p-3 rounded-md">
                          <h5 className="font-medium text-gray-950 dark:text-gray-50">Objetivo 2: Crescimento da Equipe</h5>
                          <p className="text-sm text-gray-600">Escalar equipe de 45 para 75 pessoas com 95% de retenção</p>
                        </div>
                        <div className="p-3 rounded-md">
                          <h5 className="font-medium text-gray-950 dark:text-gray-50">Objetivo 3: Excelência Operacional</h5>
                          <p className="text-sm text-gray-600">Reduzir downtime em 50% e implementar monitoramento avançado</p>
                        </div>
                      </div>
                    </div>

                    <div>
                      <h4 className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-3">Cronograma de Reviews</h4>
                      <div className="grid grid-cols-3 gap-4 text-center">
                        <div className="p-3 bg-gray-50 dark:bg-gray-700 rounded-md">
                          <p className="text-sm font-semibold">30 dias</p>
                          <p className="text-xs text-gray-600">Check-in inicial</p>
                        </div>
                        <div className="p-3 bg-gray-50 dark:bg-gray-700 rounded-md">
                          <p className="text-sm font-semibold">90 dias</p>
                          <p className="text-xs text-gray-600">Avaliação onboarding</p>
                        </div>
                        <div className="p-3 bg-gray-50 dark:bg-gray-700 rounded-md">
                          <p className="text-sm font-semibold">12 meses</p>
                          <p className="text-xs text-gray-600">Review anual</p>
                        </div>
                      </div>
                    </div>

                    {/* Botões de Ação */}
                    <div className="flex gap-3 pt-4">
                      <Button className="flex-1 border border-gray-200" style={{ backgroundColor: 'var(--eleven-bg-card)', color: 'var(--eleven-text-primary)' }}>
                        <Edit className="w-4 h-4 mr-2" />
                        Ajustar OKRs
                      </Button>
                      <Button className="flex-1" style={{ backgroundColor: 'var(--eleven-sepia-gold)', color: 'var(--eleven-text-primary)' }}>
                        <CheckCircle className="w-4 h-4 mr-2" />
                        Aprovar Framework
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}

          {contextData.type === "journey-summary" && (
            <div className="space-y-6 font-open-sans">
              <Card className="border-0" style={{ backgroundColor: 'var(--eleven-bg-card)' }}>
                <CardHeader style={{ backgroundColor: 'var(--eleven-bg-message)' }}>
                  <CardTitle className="flex items-center space-x-3 font-open-sans">
                    <Award className="w-5 h-5 text-gray-600" />
                    <span className="text-gray-950 dark:text-gray-50">Relatório Executivo Final</span>
                  </CardTitle>
                </CardHeader>
                <CardContent className="p-6">
                  <div className="space-y-6 font-open-sans">
                    <div className="p-4 rounded-md" style={{ backgroundColor: 'var(--eleven-sepia-blue)' }}>
                      <h3 className="text-base font-semibold mb-3" style={{ color: 'var(--eleven-text-primary)' }}>Sumário Executivo</h3>
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <p className="text-xs text-gray-600 mb-1">Posição:</p>
                          <p className="font-medium">{contextData.data.executive_summary.position}</p>
                        </div>
                        <div>
                          <p className="text-xs text-gray-600 mb-1">ROI Projetado:</p>
                          <p className="font-semibold" style={{ color: 'var(--eleven-text-primary)' }}>
                            {contextData.data.executive_summary.roi_projection}
                          </p>
                        </div>
                        <div>
                          <p className="text-xs text-gray-600 mb-1">Investimento Total:</p>
                          <p className="font-medium">{contextData.data.executive_summary.total_investment}</p>
                        </div>
                        <div>
                          <p className="text-xs text-gray-600 mb-1">Probabilidade Sucesso:</p>
                          <p className="font-semibold" style={{ color: 'var(--eleven-text-primary)' }}>
                            {contextData.data.executive_summary.success_probability}
                          </p>
                        </div>
                      </div>
                    </div>

                    <div>
                      <h4 className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-3">Fases da Jornada</h4>
                      <div className="grid grid-cols-2 gap-4">
                        {Object.entries(contextData.data.journey_phases).map(([key, phase]: [string, any], index) => (
                          <div key={index} className="p-3 rounded-md">
                            <h5 className="font-medium capitalize mb-2">{key.replace('phase_', 'Fase ').replace('_', ' ')}</h5>
                            <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">Duração: {phase.duration}</p>
                            <div className="space-y-1">
                              {phase.activities.slice(0, 2).map((activity: string, i: number) => (
                                <div key={i} className="flex items-start space-x-2 text-xs">
                                  <div className="w-1 h-1 bg-gray-400 rounded-full mt-1.5 flex-shrink-0"></div>
                                  <span>{activity}</span>
                                </div>
                              ))}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>

                    <div className="grid grid-cols-2 gap-6">
                      <div>
                        <h4 className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-3">Resultados Mensuráveis</h4>
                        <div className="space-y-2">
                          {Object.entries(contextData.data.measurable_results).slice(0, 4).map(([key, value]: [string, any], index) => (
                            <div key={index} className="flex justify-between">
                              <span className="text-sm text-gray-600 dark:text-gray-400 capitalize">{key.replace('_', ' ')}:</span>
                              <span className="text-sm font-medium">{String(value)}</span>
                            </div>
                          ))}
                        </div>
                      </div>

                      <div>
                        <h4 className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-3">Inovações Principais</h4>
                        <div className="space-y-2">
                          {Object.entries(contextData.data.key_innovations).map(([key, innovations]: [string, any], index) => (
                            <div key={index}>
                              <h5 className="text-xs font-medium text-gray-600 uppercase tracking-wide mb-1">{key.replace('_', ' ')}</h5>
                              {innovations.slice(0, 2).map((innovation: string, i: number) => (
                                <div key={i} className="flex items-start space-x-2 text-xs mb-1">
                                  <CheckCircle className="w-3 h-3 text-gray-600 dark:text-gray-400 mt-0.5 flex-shrink-0" />
                                  <span>{innovation}</span>
                                </div>
                              ))}
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}

          {contextData.type === "predictive-insights" && (
            <div className="space-y-6 font-open-sans">
              <Card className="border-0" style={{ backgroundColor: 'var(--eleven-bg-card)' }}>
                <CardHeader style={{ backgroundColor: 'var(--eleven-bg-message)' }}>
                  <CardTitle className="flex items-center space-x-3 font-open-sans">
                    <Brain className="w-5 h-5 text-wedo-cyan" />
                    <span className="text-gray-950 dark:text-gray-50">Inteligência Preditiva</span>
                  </CardTitle>
                </CardHeader>
                <CardContent className="p-6">
                  <div className="space-y-6 font-open-sans">
                    <div className="p-4 rounded-md" style={{ backgroundColor: 'var(--eleven-sepia-coral)' }}>
                      <h4 className="font-medium mb-2" style={{ color: 'var(--eleven-text-primary)' }}>Base de Análise</h4>
                      <div className="grid grid-cols-2 gap-4 text-sm">
                        <div>
 <span className="text-wedo-cyan-dark dark:text-gray-300">Processos Históricos:</span>
                          <p className="font-semibold">{contextData.data.analysis_base.historical_processes}</p>
                        </div>
                        <div>
 <span className="text-wedo-cyan-dark dark:text-gray-300">Pontos de Dados:</span>
                          <p className="font-semibold">{contextData.data.analysis_base.data_points.toLocaleString()}</p>
                        </div>
                      </div>
                    </div>

                    <div>
                      <h4 className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-3">Predições de Melhoria</h4>
                      <div className="space-y-4 font-open-sans">
                        {contextData.data.predictions.map((prediction: any, index: number) => (
                          <div key={index} className="p-4 rounded-md">
                            <div className="flex items-center justify-between mb-3">
                              <h5 className="font-medium text-gray-950 dark:text-gray-50">{prediction.category}</h5>
                              <Badge variant="outline" className="text-xs">
                                {prediction.confidence}% confiança
                              </Badge>
                            </div>
                            <div className="grid grid-cols-2 gap-4 mb-3 text-sm">
                              <div>
                                <span className="text-gray-600">Atual:</span>
                                <p className="font-medium">{prediction.current_performance}</p>
                              </div>
                              <div>
                                <span className="text-gray-600">Predição:</span>
                                <p className="font-semibold" style={{ color: 'var(--eleven-text-primary)' }}>{prediction.predicted_improvement}</p>
                              </div>
                            </div>
                            <div>
                              <span className="text-xs text-gray-600">Ações Recomendadas:</span>
                              <ul className="mt-1 space-y-1">
                                {prediction.actions.slice(0, 2).map((action: string, i: number) => (
                                  <li key={i} className="flex items-start space-x-2 text-xs">
                                    <div className="w-1 h-1 rounded-full mt-1.5 flex-shrink-0" style={{ backgroundColor: 'var(--eleven-text-secondary)' }}></div>
                                    <span>{action}</span>
                                  </li>
                                ))}
                              </ul>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>

                    <div>
                      <h4 className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-3">Roadmap de Implementação</h4>
                      <div className="space-y-2">
                        {Object.entries(contextData.data.implementation_roadmap).map(([phase, description]: [string, any], index) => (
                          <div key={index} className="flex items-center space-x-3 p-3 rounded-md" style={{ backgroundColor: 'var(--eleven-bg-message)' }}>
                            <div className="w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold" style={{ backgroundColor: 'var(--eleven-sepia-blue)', color: 'var(--eleven-text-primary)' }}>
                              {index + 1}
                            </div>
                            <span className="text-sm">{description}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}

          {/* Painel de Carta Oferta */}
          {contextData.type === "offer-letter" && (
            <div className="space-y-6 font-open-sans">
              <Card className="border-0" style={{ backgroundColor: 'var(--eleven-bg-card)' }}>
                <CardHeader style={{ backgroundColor: 'var(--eleven-bg-message)' }}>
                  <CardTitle className="flex items-center justify-between font-open-sans">
                    <div className="flex items-center space-x-3">
                      <FileText className="w-5 h-5 text-gray-600" />
                      <span className="text-gray-950 dark:text-gray-50">{contextData.title}</span>
                    </div>
                  </CardTitle>
                </CardHeader>
                <CardContent className="p-6">
                  <div className="space-y-6 font-open-sans">
                    {/* Informações do Candidato */}
                    <div className="p-4 rounded-md" style={{ backgroundColor: 'var(--eleven-sepia-light)' }}>
                      <h4 className="font-medium mb-3" style={{ color: 'var(--eleven-text-primary)' }}>Candidato</h4>
                      <div className="grid grid-cols-2 gap-3 text-sm">
                        <div>
                          <span style={{ color: 'var(--eleven-text-secondary)' }}>Nome:</span>
                          <p className="font-medium" style={{ color: 'var(--eleven-text-primary)' }}>{contextData.data.candidate_info.name}</p>
                        </div>
                        <div>
                          <span style={{ color: 'var(--eleven-text-secondary)' }}>Email:</span>
                          <p className="font-medium" style={{ color: 'var(--eleven-text-primary)' }}>{contextData.data.candidate_info.email}</p>
                        </div>
                        <div>
                          <span style={{ color: 'var(--eleven-text-secondary)' }}>Telefone:</span>
                          <p className="font-medium" style={{ color: 'var(--eleven-text-primary)' }}>{contextData.data.candidate_info.phone}</p>
                        </div>
                        <div>
                          <span style={{ color: 'var(--eleven-text-secondary)' }}>Empresa Atual:</span>
                          <p className="font-medium" style={{ color: 'var(--eleven-text-primary)' }}>{contextData.data.candidate_info.current_company}</p>
                        </div>
                      </div>
                    </div>

                    {/* Template da Carta Oferta */}
                    <div className="p-6 rounded-md border" style={{ backgroundColor: 'var(--eleven-bg-card)', borderColor: 'var(--eleven-border-subtle)' }}>
                      <div className="prose prose-sm max-w-none">
                        <pre className="whitespace-pre-wrap font-open-sans text-sm" style={{ color: 'var(--eleven-text-primary)', fontFamily: 'var(--font-open-sans)' }}>
                          {contextData.data.letter_template}
                        </pre>
                      </div>
                    </div>

                    {/* Botões de Ação */}
                    <div className="flex gap-3 pt-4">
                      <Button className="flex-1 border border-gray-200" style={{ backgroundColor: 'var(--eleven-bg-card)', color: 'var(--eleven-text-primary)' }}>
                        <Edit className="w-4 h-4 mr-2" />
                        Revisar e Editar
                      </Button>
                      <Button className="flex-1" style={{ backgroundColor: 'var(--eleven-sepia-mint)', color: 'var(--eleven-text-primary)' }}>
                        <Send className="w-4 h-4 mr-2" />
                        Enviar para Candidato
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}

          {/* Painel de Agendamento de Entrevistas */}
          {contextData.type === "interview-scheduling" && (
            <div className="space-y-6 font-open-sans">
              <Card className="border-0" style={{ backgroundColor: 'var(--eleven-bg-card)' }}>
                <CardHeader style={{ backgroundColor: 'var(--eleven-bg-message)' }}>
                  <CardTitle className="flex items-center space-x-3 font-open-sans">
                    <Calendar className="w-5 h-5 text-gray-600" />
                    <span className="text-gray-950 dark:text-gray-50">{contextData.title}</span>
                  </CardTitle>
                </CardHeader>
                <CardContent className="p-6">
                  <div className="space-y-6 font-open-sans">
                    {/* Candidatos para Agendar */}
                    <div>
                      <h4 className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-3">Candidatos Selecionados</h4>
                      <div className="space-y-3">
                        {contextData.data.candidates_to_schedule.map((candidate: any, index: number) => (
                          <div key={index} className="p-4 rounded-md border" style={{ backgroundColor: 'var(--eleven-bg-message)', borderColor: 'var(--eleven-border-subtle)' }}>
                            <div className="flex justify-between items-start mb-2">
                              <div>
                                <h5 className="font-medium" style={{ color: 'var(--eleven-text-primary)' }}>{candidate.name}</h5>
                                <p className="text-sm" style={{ color: 'var(--eleven-text-secondary)' }}>Score: {candidate.score}/100</p>
                              </div>
                              <Badge style={{ backgroundColor: 'var(--eleven-sepia-blue)', color: 'var(--eleven-text-primary)' }}>
                                {candidate.interview_type}
                              </Badge>
                            </div>
                            <div className="flex gap-2 text-xs" style={{ color: 'var(--eleven-text-secondary)' }}>
                              <span>Preferências:</span>
                              {candidate.preferred_times.map((time: string, i: number) => (
                                <span key={i} className="px-2 py-1 rounded" style={{ backgroundColor: 'var(--eleven-bg-card)' }}>{time}</span>
                              ))}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Horários Disponíveis */}
                    <div>
                      <h4 className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-3">Horários Disponíveis</h4>
                      <div className="space-y-4">
                        {Object.entries(contextData.data.available_slots).map(([date, slots]: [string, any], index) => (
                          <div key={index}>
                            <h5 className="text-sm font-medium mb-2" style={{ color: 'var(--eleven-text-primary)' }}>{date}</h5>
                            <div className="grid grid-cols-3 gap-2">
                              {slots.map((slot: any, i: number) => (
                                <button
                                  key={i}
                                  disabled={!slot.available}
                                  className={`p-2 rounded text-xs transition-all ${slot.available ? 'hover:scale-105' : 'opacity-50 cursor-not-allowed'}`}
                                  style={{
                                    backgroundColor: slot.available ? 'var(--eleven-sepia-mint)' : 'var(--eleven-bg-message)',
                                    color: 'var(--eleven-text-primary)',
                                    border: `1px solid ${slot.available ? 'var(--eleven-border-subtle)' : 'var(--eleven-border-light)'}`
                                  }}
                                >
                                  {slot.time}
                                  <div className="text-xs" style={{ color: 'var(--eleven-text-tertiary)' }}>{slot.duration}</div>
                                </button>
                              ))}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Informações Adicionais */}
                    <div className="p-4 rounded-md" style={{ backgroundColor: 'var(--eleven-sepia-light)' }}>
                      <div className="grid grid-cols-2 gap-3 text-sm">
                        <div>
                          <span style={{ color: 'var(--eleven-text-secondary)' }}>Entrevistador:</span>
                          <p className="font-medium" style={{ color: 'var(--eleven-text-primary)' }}>{contextData.data.interviewer}</p>
                        </div>
                        <div>
                          <span style={{ color: 'var(--eleven-text-secondary)' }}>Integração:</span>
                          <p className="font-medium" style={{ color: 'var(--eleven-text-primary)' }}>{contextData.data.calendar_integration}</p>
                        </div>
                      </div>
                    </div>

                    {/* Botões de Ação */}
                    <div className="flex gap-3 pt-4">
                      <Button className="flex-1 border border-gray-200" style={{ backgroundColor: 'var(--eleven-bg-card)', color: 'var(--eleven-text-primary)' }}>
                        <Edit className="w-4 h-4 mr-2" />
                        Ajustar Horários
                      </Button>
                      <Button className="flex-1" style={{ backgroundColor: 'var(--eleven-sepia-blue)', color: 'var(--eleven-text-primary)' }}>
                        <CheckCircle className="w-4 h-4 mr-2" />
                        Confirmar Agendamentos
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}

          {/* Add other context types as needed */}

          {/* Job Creation Frames - Technical Matrix */}
          {contextData.type === "technical-matrix" && contextData.data && (
            <div className="space-y-6 font-open-sans">
              <Card className="border-0" style={{ backgroundColor: 'var(--eleven-bg-card)' }}>
                <CardHeader style={{ backgroundColor: 'var(--eleven-bg-message)' }}>
                  <CardTitle className="flex items-center space-x-3 font-open-sans">
                    <Target className="w-5 h-5 text-gray-600 dark:text-gray-400" />
                    <span className="text-gray-950 dark:text-gray-50">{contextData.title}</span>
                  </CardTitle>
                </CardHeader>
                <CardContent className="p-6">
                  <div className="space-y-4">
                    <div className="prose prose-sm max-w-none">
                      <pre className="whitespace-pre-wrap font-mono text-sm p-4 rounded-md" style={{ backgroundColor: 'var(--eleven-bg-message)', color: 'var(--eleven-text-primary)' }}>
                        {contextData.data}
                      </pre>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}

          {/* Job Creation Frames - Timeline */}
          {contextData.type === "timeline" && contextData.data && (
            <div className="space-y-6 font-open-sans">
              <Card className="border-0" style={{ backgroundColor: 'var(--eleven-bg-card)' }}>
                <CardHeader style={{ backgroundColor: 'var(--eleven-bg-message)' }}>
                  <CardTitle className="flex items-center space-x-3 font-open-sans">
                    <CalendarDays className="w-5 h-5 text-gray-600 dark:text-gray-400" />
                    <span className="text-gray-950 dark:text-gray-50">{contextData.title}</span>
                  </CardTitle>
                </CardHeader>
                <CardContent className="p-6">
                  <div className="space-y-4">
                    <div className="prose prose-sm max-w-none">
                      <pre className="whitespace-pre-wrap font-mono text-sm p-4 rounded-md" style={{ backgroundColor: 'var(--eleven-bg-message)', color: 'var(--eleven-text-primary)' }}>
                        {contextData.data}
                      </pre>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}

          {/* Job Creation Frames - Interview Flow */}
          {contextData.type === "interview-flow" && contextData.data && (
            <div className="space-y-6 font-open-sans">
              <Card className="border-0" style={{ backgroundColor: 'var(--eleven-bg-card)' }}>
                <CardHeader style={{ backgroundColor: 'var(--eleven-bg-message)' }}>
                  <CardTitle className="flex items-center space-x-3 font-open-sans">
                    <Workflow className="w-5 h-5 text-gray-600 dark:text-gray-400" />
                    <span className="text-gray-950 dark:text-gray-50">{contextData.title}</span>
                  </CardTitle>
                </CardHeader>
                <CardContent className="p-6">
                  <div className="space-y-4">
                    <div className="prose prose-sm max-w-none">
                      <pre className="whitespace-pre-wrap font-mono text-sm p-4 rounded-md" style={{ backgroundColor: 'var(--eleven-bg-message)', color: 'var(--eleven-text-primary)' }}>
                        {contextData.data}
                      </pre>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}

          {/* Job Creation Frames - Org Chart */}
          {contextData.type === "org-chart" && contextData.data && (
            <div className="space-y-6 font-open-sans">
              <Card className="border-0" style={{ backgroundColor: 'var(--eleven-bg-card)' }}>
                <CardHeader style={{ backgroundColor: 'var(--eleven-bg-message)' }}>
                  <CardTitle className="flex items-center space-x-3 font-open-sans">
                    <Network className="w-5 h-5 text-gray-600 dark:text-gray-400" />
                    <span className="text-gray-950 dark:text-gray-50">{contextData.title}</span>
                  </CardTitle>
                </CardHeader>
                <CardContent className="p-6">
                  <div className="space-y-4">
                    <div className="prose prose-sm max-w-none">
                      <pre className="whitespace-pre-wrap font-mono text-sm p-4 rounded-md" style={{ backgroundColor: 'var(--eleven-bg-message)', color: 'var(--eleven-text-primary)' }}>
                        {contextData.data}
                      </pre>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}

          {/* Job Creation Progress */}
          {contextData.type === "job-creation-progress" && contextData.data && (
            <div className="space-y-6 font-open-sans">
              <Card className="border-0" style={{ backgroundColor: 'var(--eleven-bg-card)' }}>
                <CardHeader style={{ backgroundColor: 'var(--eleven-bg-message)' }}>
                  <CardTitle className="flex items-center space-x-3 font-open-sans">
                    <Briefcase className="w-5 h-5 text-gray-600" />
                    <span className="text-gray-950 dark:text-gray-50">{contextData.title}</span>
                  </CardTitle>
                </CardHeader>
                <CardContent className="p-6">
                  <div className="space-y-6">
                    {/* Progress Overview */}
                    <div className="p-4 rounded-md" style={{ backgroundColor: 'var(--eleven-sepia-light)' }}>
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-sm font-medium" style={{ color: 'var(--eleven-text-primary)' }}>
                          Progresso da Criação
                        </span>
                        <span className="text-sm font-bold" style={{ color: 'var(--eleven-text-primary)' }}>
                          {contextData.data.completion_percentage}%
                        </span>
                      </div>
                      <div className="w-full h-2 rounded-full" style={{ backgroundColor: 'var(--eleven-bg-message)' }}>
                        <div 
                          className="h-full rounded-full transition-all duration-500 bg-gray-700" style={{ width: `${contextData.data.completion_percentage}%` }}
                        />
                      </div>
                    </div>

                    {/* Field Status */}
                    <div>
                      <h4 className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-3">Status dos Campos</h4>
                      <div className="grid grid-cols-2 gap-3">
                        {contextData.data.collected_fields?.map((field: string, idx: number) => (
                          <div key={idx} className="flex items-center gap-2 p-2 rounded" style={{ backgroundColor: 'var(--eleven-sepia-mint)' }}>
                            <CheckCircle className="w-4 h-4 text-green-600" />
                            <span className="text-sm">{field}</span>
                          </div>
                        ))}
                        {contextData.data.pending_fields?.map((field: string, idx: number) => (
                          <div key={idx} className="flex items-center gap-2 p-2 rounded" style={{ backgroundColor: 'var(--eleven-bg-message)' }}>
                            <Clock className="w-4 h-4 text-gray-600" />
                            <span className="text-sm text-gray-600">{field}</span>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Next Steps */}
                    {contextData.data.next_panel && (
                      <div className="p-4 rounded-md border-2 border-gray-400" style={{ backgroundColor: 'var(--eleven-bg-card)' }}>
                        <div className="flex items-start gap-3">
                          <ArrowUpDown className="w-5 h-5 text-gray-600 dark:text-gray-400 mt-0.5" />
                          <div>
                            <h4 className="text-sm font-semibold mb-1" style={{ color: 'var(--eleven-text-primary)' }}>
                              Próximo Passo
                            </h4>
                            <p className="text-sm" style={{ color: 'var(--eleven-text-secondary)' }}>
                              {contextData.data.next_panel}
                            </p>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            </div>
          )}

          {/* Pipeline Report - Stale Candidates */}
          {contextData.type === "pipeline-report" && contextData.data && (
            <PipelineReport
              data={contextData.data}
              onAction={handlePipelineAction}
              onClose={() => setIsPanelOpen(false)}
            />
          )}

          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="flex overflow-hidden flex-1" style={{ backgroundColor: 'var(--eleven-bg-main)' }}>
      {/* Main Chat Area */}
      <div className={`flex flex-col transition-all duration-300 overflow-hidden ${isPanelOpen ? 'w-3/5' : 'w-full'}`}>
        {/* Header */}
        <div className="py-3 px-6 flex-shrink-0" style={{ backgroundColor: 'var(--eleven-bg-main)', borderBottom: '1px solid var(--eleven-border-subtle)' }}>
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <LIAIcon size="lg" />
              <div>
                <h1 className="text-base font-semibold " style={{ color: 'var(--eleven-text-primary)' }}>
                  Chat {chatId} - {chatTitle}
                </h1>
                <p className="text-xs font-open-sans text-gray-500">
                  Lia - Assistente de Recrutamento
                </p>
              </div>
            </div>

            <div className="flex items-center space-x-2">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setShowSearch(!showSearch)}
                className="transition-all duration-200 hover:scale-105"
                title="Buscar na conversa (Ctrl+F)"
              >
                <Search className="w-4 h-4" />
              </Button>
            </div>
          </div>

          {/* Barra de Busca */}
          {showSearch && (
            <div className="mt-4 flex items-center space-x-2">
              <div className="flex-1 relative">
                <input
                  type="text"
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  placeholder="Buscar na conversa..."
                  className="w-full px-3 py-2 rounded-md text-sm focus:outline-none"
                  style={{ 
                    border: '1px solid var(--eleven-border-subtle)',
                    backgroundColor: 'var(--eleven-bg-card)',
                    color: 'var(--eleven-text-primary)'
                  }}
                  autoFocus
                />
                <Search className="absolute right-3 top-2.5 w-4 h-4 text-gray-600" />
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setShowSearch(false)}
                className="hover:bg-gray-100 dark:hover:bg-gray-700"
              >
                <X className="w-4 h-4" />
              </Button>
            </div>
          )}

          {/* Tabs de Navegação */}
          <div className="mt-2">
            <Tabs value={activeTab} onValueChange={(value) => setActiveTab(value as "conversa" | "controle")}>
              <TabsList className="bg-transparent p-0 h-auto gap-4" style={{ borderBottom: '1px solid var(--eleven-border-subtle)' }}>
                <TabsTrigger 
                  value="conversa" 
                  className="bg-transparent data-[state=active]:bg-transparent data-[state=active]:shadow-none px-0 pb-2 rounded-none border-b-2 border-transparent data-[state=active]:border-gray-900 dark:border-gray-50 transition-all"
                  style={{ color: activeTab === 'conversa' ? 'var(--gray-950)' : 'var(--eleven-text-secondary)' }}
                >
                  <MessageSquare className="w-4 h-4 mr-2" />
                  Conversa
                </TabsTrigger>
                <TabsTrigger 
                  value="controle" 
                  className="bg-transparent data-[state=active]:bg-transparent data-[state=active]:shadow-none px-0 pb-2 rounded-none border-b-2 border-transparent data-[state=active]:border-gray-900 dark:border-gray-50 transition-all"
                  style={{ color: activeTab === 'controle' ? 'var(--gray-950)' : 'var(--eleven-text-secondary)' }}
                >
                  <Cpu className="w-4 h-4 mr-2" />
                  Centro de Controle
                </TabsTrigger>
              </TabsList>
            </Tabs>
          </div>

          <AgentMemoryIndicator 
            sessionId={chatId.replace('#', '')} 
            domain="wizard" 
          />
        </div>

        {/* Tab Content: Conversa */}
        {activeTab === "conversa" && (
        <>
        {/* Messages com altura flexível e scroll */}
        <div
          ref={messagesContainerRef}
          className={`flex-1 overflow-y-auto overflow-x-hidden scrollbar-thin scrollbar-thumb-gray-300 dark:scrollbar-thumb-gray-600 scrollbar-track-transparent hover:scrollbar-thumb-gray-400 dark:hover:scrollbar-thumb-gray-500 relative transition-all duration-300 ${chatContainerClass} ${
            !isEmptyChat ? 'p-4' : ''
          }`}
          style={{
            scrollBehavior: 'smooth',
            minHeight: 0
          }}
          onScroll={checkNewMessageIndicator}
        >
          {/* Empty state with PromptSuggestionsDock */}
          {isEmptyChat && (
            <div className={`text-left pt-8 ${messagesContainerClass}`}>
              <div className="mb-8">
                <LIAIcon size="xl" className="mb-4" />
                <h2 className="text-3xl font-semibold mb-3" style={{ color: 'var(--eleven-text-primary)' }}>
                  Oi, eu sou a <span className="text-gray-700">LIA</span>.
                </h2>
                <p className="text-base mb-8" style={{ color: 'var(--eleven-text-secondary)' }}>
                  Sua assistente de recrutamento inteligente. Qual das tarefas abaixo quer que eu execute para você?
                </p>
                
                {/* Prompt Suggestions Grid (replaces old 4-button grid) */}
                <PromptSuggestionsDock
                  onSelect={(command) => setInput(command)}
                  isEmpty={true}
                />
              </div>
            </div>
          )}
          
          {/* Container de mensagens - ajusta largura baseado no painel */}
          {!isEmptyChat && (
            <div className={`${messagesContainerClass} space-y-4`}>
              {/* Notificação de campos vazios - aparece no início do wizard */}
              {emptyFieldNotifications.hasPendingNotifications && emptyFieldNotifications.currentNotification && (
                <div className="flex justify-start">
                  <div className="flex items-start gap-1 max-w-4xl">
                    <div className="flex-shrink-0 pt-4">
                      <LIAIcon size="md" />
                    </div>
                    <div className="rounded-md p-5 flex-1" style={{ backgroundColor: 'var(--eleven-bg-message)' }}>
                      <div className="flex items-center space-x-2 mb-2">
                        <span className="text-sm font-medium lia-name -ml-1" style={{ color: 'var(--eleven-text-primary)' }}>
                          Lia
                        </span>
                        <Badge variant="secondary" className="text-xs border-0">
                          Pendência
                        </Badge>
                      </div>
                      <EmptyFieldNotificationMessage
                        notification={emptyFieldNotifications.currentNotification}
                        onAction={handleEmptyFieldAction}
                        onSuggestionAccepted={handleSuggestionAccepted}
                        onSuggestionRejected={handleSuggestionRejected}
                        suggestion={currentSuggestion}
                        isLoadingSuggestion={isLoadingSuggestion}
                      />
                    </div>
                  </div>
                </div>
              )}
              
              {messages.map((message, index) => {
            const isHighlighted = searchTerm && message.content.toLowerCase().includes(searchTerm.toLowerCase())
            const isCurrentMessage = index === currentMessageIndex

            return (
              <div
                key={message.id}
                data-message-id={message.id}
                className={`flex justify-start ${isCurrentMessage ? 'ring-2 ring-gray-900/20 rounded-md' : ''} ${isHighlighted ? 'bg-yellow-50 dark:bg-yellow-900/20 rounded-md p-2' : ''}`}
              >
                <div className={`flex ${
                  message.sender === "lia" ? "items-start gap-1 max-w-4xl" : "items-start space-x-3 max-w-3xl ml-16"
                }`}>
                  {/* Avatar - sempre do lado esquerdo */}
                  {message.sender === "lia" ? (
                    <div className="flex-shrink-0 pt-4">
                      <LIAIcon size="md" />
                    </div>
                  ) : (
                    <Avatar className="w-10 h-10 mt-1 flex-shrink-0">
                      <AvatarImage
                        src="https://randomuser.me/api/portraits/women/44.jpg"
                        alt="Ana Silva"
                      />
                      <AvatarFallback className="bg-gray-900 dark:bg-gray-50 text-white dark:text-gray-900 text-sm font-medium">
                        AS
                      </AvatarFallback>
                    </Avatar>
                  )}

                  {/* Conteúdo da mensagem */}
                  <div
                    className="rounded-md p-5 flex-1"
                    style={{
                      backgroundColor: message.sender === "user" ? 'var(--eleven-bg-card)' : 'var(--eleven-bg-message)',
                      color: 'var(--eleven-text-primary)'
                    }}
                  >
                    <div className="flex items-center space-x-2 mb-2">
                      <span className={`text-sm font-medium ${
                        message.sender === "lia"
                          ? "lia-name -ml-1"
                          : ""
                      }`} style={{ color: 'var(--eleven-text-primary)' }}>
                        {message.sender === "lia" ? "Lia" : "Ana Silva"}
                      </span>
                      <span className="text-xs" style={{ color: 'var(--eleven-text-tertiary)' }}>
                        {getRelativeTime(message.timestamp)}
                      </span>
                      {isCurrentMessage && (
                        <Badge variant="secondary" className="text-xs border-0">
                          Selecionada
                        </Badge>
                      )}
                    </div>

                    {message.type !== "thinking" && message.type !== "progress" && message.type !== "command" && message.type !== "file-creation" && (
                      <div
                        className={`text-sm leading-relaxed ${
                          message.sender === "user"
                            ? "font-open-sans"
                            : "font-['Open_Sans',sans-serif] lia-markdown-content"
                        }`}
                        style={{ color: 'var(--eleven-text-primary)' }}
                        dangerouslySetInnerHTML={{
                          __html: highlightSearchTerm(message.content, searchTerm)
                        }}
                      />
                    )}

                    {message.sender === "lia" && message.data?.action_result && (
                      <div className="mt-3">
                        <ActionResultCard
                          actionType={message.data.action_result.action_type || message.data.action_type || "unknown"}
                          result={message.data.action_result}
                        />
                      </div>
                    )}

                    {/* Global Search Expansion Card - Always show when there are search results */}
                    {message.sender === "lia" && message.data?.workflow_data?.search_results && (
 <Card className="border border-gray-900 dark:border-gray-200 bg-gray-50 dark:bg-gray-900 mt-4">
                        <CardContent className="p-4">
                          <div className="flex items-start gap-3">
                            <Globe className="w-5 h-5 text-gray-600 dark:text-gray-400 mt-0.5 shrink-0" />
                            <div className="flex-1">
                              <h4 className="font-semibold text-sm mb-1 text-blue-900 dark:text-blue-100">
                                Expandir para Banco de Dados Global
                              </h4>
 <p className="text-xs text-wedo-cyan-dark dark:text-gray-300 mb-3">
                                {message.data.workflow_data.search_results.local_count > 0 
                                  ? `Encontramos ${message.data.workflow_data.search_results.local_count} candidato(s) localmente.` 
                                  : `Encontramos apenas ${message.data.workflow_data.search_results.local_count} candidato(s) localmente.`
                                } Posso buscar em nosso banco global com acesso a 800M+ perfis profissionais para encontrar mais candidatos qualificados.
                              </p>
                              
                              {/* Credit information - Complete breakdown */}
                              <div className="bg-white/60 dark:bg-gray-800/40 rounded-md p-3 mb-3 space-y-1.5">
                                <div className="flex items-center justify-between text-xs">
                                  <span className="text-gray-600 dark:text-gray-400">Créditos disponíveis:</span>
                                  <span className="font-semibold text-gray-950 dark:text-gray-50">{availableCredits} créditos</span>
                                </div>
                                <div className="flex items-center justify-between text-xs">
                                  <span className="text-gray-600 dark:text-gray-400">Esta busca consumirá:</span>
                                  <span className="font-semibold text-gray-900 dark:text-gray-50">~{message.data.workflow_data.search_results.global_credits_estimate || 5} créditos</span>
                                </div>
                                <div className="border-t border-gray-200 dark:border-gray-700 pt-1.5 flex items-center justify-between text-xs">
                                  <span className="text-gray-600 dark:text-gray-400">Saldo após busca:</span>
                                  <span className="font-semibold text-green-600 dark:text-green-400">
                                    {Math.max(0, availableCredits - (message.data.workflow_data.search_results.global_credits_estimate || 5))} créditos
                                  </span>
                                </div>
                              </div>
                              
                              <div className="flex gap-2">
                                <Button
                                  size="sm"
                                  className="bg-gray-900 hover:bg-gray-800 text-white dark:bg-gray-50 dark:text-gray-900 dark:hover:bg-gray-200"
                                  onClick={() => handleLoadMoreCandidates(
                                    message.data.workflow_data.search_results.query || "",
                                    message.data.workflow_data.search_results.thread_id
                                  )}
                                  disabled={availableCredits < (message.data.workflow_data.search_results.global_credits_estimate || 5)}
                                >
                                  <CheckCircle className="w-3.5 h-3.5 mr-1" />
                                  Sim, buscar
                                </Button>
                                <Button
                                  size="sm"
                                  variant="outline"
                                  className="border-gray-300 text-gray-800 dark:text-gray-200"
                                  onClick={() => handleSendMessage("Não obrigado, vou trabalhar com os resultados locais")}
                                >
                                  <XCircle className="w-3.5 h-3.5 mr-1" />
                                  Não obrigado
                                </Button>
                              </div>
                              
                              {availableCredits < (message.data.workflow_data.search_results.global_credits_estimate || 5) && (
                                <p className="text-xs text-red-600 dark:text-red-400 mt-2">
                                  Créditos insuficientes para esta busca.
                                </p>
                              )}
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                    )}

                    {message.type === "thinking" && (
                      <TypingIndicator />
                    )}

                    {message.type === "progress" && message.progressSteps && (
                      <ProgressSteps
                        steps={message.progressSteps}
                        currentStep={message.currentStep}
                      />
                    )}

                    {message.type === "command" && message.command && (
                      <CommandExecution
                        command={message.command.text}
                        status={message.command.status}
                        output={message.command.output}
                      />
                    )}

                    {message.type === "file-creation" && message.fileCreation && (
                      <FileCreationIndicator
                        fileName={message.fileCreation.fileName}
                        fileType={message.fileCreation.fileType}
                        status={message.fileCreation.status}
                      />
                    )}

                    {/* Chat Cards inline rendering */}
                    {message.chatCardType && message.chatCardData && (
                      <div className="mt-4">
                        {renderChatCard(message)}
                      </div>
                    )}

                    {/* Completion Message com rating e follow-up */}
                    {message.type === "completion" && message.completion && (
                      <>
                        <div
                          className="text-sm text-gray-950 dark:text-gray-50 mb-4"
                          dangerouslySetInnerHTML={{
                            __html: highlightSearchTerm(message.content, searchTerm)
                          }}
                        />
                        <CompletionMessage
                          message={message.completion.message}
                          onRating={(rating) => {
                            console.log('Rating:', rating)
                            // Implementar lógica de rating
                          }}
                          onFollowUp={(action) => {
                            console.log('Follow-up action:', action)
                            // Implementar lógica de follow-up
                          }}
                        />
                      </>
                    )}

                    {message.needsApproval && message.approvalRequest && (
                      <div className="mt-4 p-5 rounded-md" style={{ backgroundColor: 'var(--eleven-sepia-light)' }}>
                        <div className="flex items-center justify-between mb-4">
                          <div className="flex items-center space-x-2">
                            <Clock className="w-4 h-4" style={{ color: 'var(--eleven-text-secondary)' }} />
                            <h4 className="font-medium text-base" style={{ color: 'var(--eleven-text-primary)' }}>{message.approvalRequest.title}</h4>
                          </div>
                          <Badge variant="secondary" className="text-xs border-0" style={{ backgroundColor: 'var(--eleven-bg-card)', color: 'var(--eleven-text-secondary)' }}>
                            {message.approvalStatus === "pending" ? "Aguardando" : message.approvalStatus}
                          </Badge>
                        </div>
                        <p className="text-sm mb-3" style={{ color: 'var(--eleven-text-secondary)' }}>{message.approvalRequest.description}</p>
                        <p className="text-xs mb-4" style={{ color: 'var(--eleven-text-tertiary)' }}>👤 {message.approvalRequest.manager}</p>

                        <div className="space-y-2.5 mb-4">
                          {message.approvalRequest.items.map((item, index) => (
                            <div key={index} className="flex justify-between text-sm py-1.5">
                              <span style={{ color: 'var(--eleven-text-secondary)' }}>{item.label}:</span>
                              <span className="font-medium" style={{ color: 'var(--eleven-text-primary)' }}>{item.value}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {message.actions && (
                      <div className="flex flex-wrap gap-2 mt-3">
                        {message.actions.map((action, index) => {
                          const isApproveAction = action.label.toLowerCase().includes('aprovar') || action.label.toLowerCase().includes('confirm')
                          const isScheduleAction = action.label.toLowerCase().includes('agenda') || action.label.toLowerCase().includes('calendar')
                          const isCandidateAction = action.label.toLowerCase().includes('candidato') || action.label.toLowerCase().includes('pipeline')
                          const isRejectAction = action.label.toLowerCase().includes('rejeitar') || action.label.toLowerCase().includes('não')
                          
                          let buttonStyle = {
                            backgroundColor: 'var(--gray-50)',
                            color: 'var(--gray-800)',
                            borderColor: 'var(--gray-300)'
                          }
                          let iconColor = 'var(--gray-400)'
                          
                          if (isApproveAction) {
                            buttonStyle = { backgroundColor: 'var(--gray-50)', color: 'var(--wedo-green)', borderColor: 'var(--wedo-green)' }
                            iconColor = 'var(--wedo-green)'
                          } else if (isScheduleAction) {
                            buttonStyle = { backgroundColor: 'var(--gray-50)', color: 'var(--wedo-orange)', borderColor: 'var(--wedo-orange)' }
                            iconColor = 'var(--wedo-orange)'
                          } else if (isCandidateAction) {
                            buttonStyle = { backgroundColor: 'var(--gray-50)' }
                            iconColor = 'var(--gray-600)'
                          } else if (isRejectAction) {
                            buttonStyle = { backgroundColor: 'var(--gray-50)', color: 'var(--status-error)', borderColor: 'var(--status-error)' }
                            iconColor = 'var(--status-error)'
                          }
                          
                          return (
                            <Button
                              key={index}
                              variant="ghost"
                              size="sm"
                              onClick={() => handleActionClick(message, action)}
                              className="text-xs transition-all duration-200 hover:scale-105 font-medium"
                              style={{ 
                                backgroundColor: buttonStyle.backgroundColor,
                                color: buttonStyle.color,
                                border: `1px solid ${buttonStyle.borderColor}`
                              }}
                            >
                              {action.icon && <action.icon className="w-3 h-3 mr-1" style={{ color: iconColor }} />}
                              {action.label}
                            </Button>
                          )
                        })}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )
          })}

          {isLoading && (
            <div className="flex justify-start">
              <div className="flex items-start gap-1 max-w-4xl">
                <div className="flex-shrink-0 pt-4">
                  <LIAIcon size="md" />
                </div>
                <div className="rounded-md p-5 flex-1" style={{ backgroundColor: 'var(--eleven-bg-message)' }}>
                  <div className="flex items-center space-x-2">
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span className="text-sm" style={{ color: 'var(--eleven-text-secondary)' }}>
                      LIA está digitando...
                    </span>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Referência para scroll automático */}
          <div ref={messagesEndRef} />

          {/* Indicador de Nova Mensagem */}
          {newMessageIndicator && (
            <div className="absolute bottom-4 right-4">
              <Button
                onClick={scrollToBottom}
                className="rounded-full"
                size="sm"
                style={{ 
                  backgroundColor: 'var(--eleven-text-primary)',
                  color: 'var(--eleven-bg-card)'
                }}
              >
                <ChevronDown className="w-4 h-4 mr-1" />
                Nova mensagem
              </Button>
            </div>
          )}
            </div>
          )}
        </div>

        {/* Input Card - Estilo Manus - ajusta largura baseado no painel */}
        <div className="p-6 flex-shrink-0" style={{ backgroundColor: 'var(--eleven-bg-main)' }}>
          <div className={inputContainerClass}>
            {/* Context Pills - Versão simplificada */}
            {contextData && contextData.data?.totalCount > 0 && (
              <div className="mb-4">
                <ContextPill
                  icon={<MapPin className="w-3.5 h-3.5" />}
                  primaryText={contextData.title}
                  secondaryText={
                    contextData.type === 'candidate-suggestions'
                      ? `${contextData.data.totalCount} candidatos`
                      : contextData.type
                  }
                  onDismiss={() => {
                    setContextData(null)
                    setIsPanelOpen(false)
                  }}
                />
              </div>
            )}

            {/* Smart Search Input - Expands when search mode is active */}
            {isSmartSearchMode ? (
              <SmartSearchInput
                value={smartSearchQuery}
                onChange={setSmartSearchQuery}
                onSubmit={handleSmartSearchSubmit}
                onCancel={handleSmartSearchCancel}
                onOpenFilters={() => setIsFiltersModalOpen(true)}
                isLoading={isLoading}
                placeholder="Desenvolvedores Python com 5+ anos em São Paulo..."
                activeFiltersCount={getActiveFiltersCount()}
              />
            ) : (
              <div className="rounded-md p-5 space-y-4" style={{ backgroundColor: 'var(--eleven-bg-card)' }}>
                
                {/* Sugestões Rápidas - Combinadas (Quick Actions + Respostas Rápidas) */}
                {/* Quick Action Chips só aparecem quando há resultados de busca com candidatos */}
                {(getQuickSuggestions().length > 0 || (hasSearchResults && contextData && getQuickActions().length > 0)) && !isLoading && searchFlow.flowState !== "collecting_profile" && (
                  <div className="space-y-3">
                    {/* Respostas Rápidas (texto) - não mostrar durante coleta de perfil */}
                    {getQuickSuggestions().length > 0 && searchFlow.flowState !== "collecting_profile" && (
                      <div className="flex flex-wrap gap-2">
                        {getQuickSuggestions().map((suggestion, index) => (
                          <Button
                            key={index}
                            size="sm"
                            onClick={() => setInput(suggestion)}
                            className="text-xs h-7 px-3 transition-all duration-200 hover:scale-105 text-gray-950 dark:text-gray-50 border border-gray-200" style={{ backgroundColor: 'var(--gray-50)' }}
                          >
                            {suggestion}
                          </Button>
                        ))}
                      </div>
                    )}
                    
                    {/* Quick Action Chips (ações rápidas com ícones) - SÓ quando há candidatos encontrados */}
                    {hasSearchResults && contextData && contextData.data?.totalCount > 0 && getQuickActions().length > 0 && (
                      <QuickActionChips actions={getQuickActions()} />
                    )}
                  </div>
                )}

                {/* File Validation Error Toast */}
                {fileValidationError && (
                  <div className="flex items-start gap-2 p-3 rounded-md mb-2 animate-in fade-in slide-in-from-top-2 duration-300"
                    style={{ 
                      backgroundColor: 'rgba(239, 68, 68, 0.1)', 
                      border: '1px solid rgba(239, 68, 68, 0.3)' 
                    }}
                  >
                    <AlertTriangle className="w-4 h-4 text-red-500 mt-0.5 flex-shrink-0" />
                    <div className="flex-1">
                      <p className="text-sm font-medium text-red-600">Arquivo inválido</p>
                      <p className="text-xs text-red-500 whitespace-pre-line mt-0.5">{fileValidationError}</p>
                      <p className="text-xs text-gray-600 mt-1">
                        Formatos aceitos: PDF, DOC, DOCX, TXT, CSV, XLSX, PNG, JPG (máx. {MAX_FILE_SIZE_MB}MB)
                      </p>
                    </div>
                    <button
                      onClick={() => setFileValidationError(null)}
                      className="p-1 rounded-full hover:bg-red-100 transition-colors"
                    >
                      <X className="w-3.5 h-3.5 text-red-500" />
                    </button>
                  </div>
                )}

                {/* Attached Files Preview */}
                {attachedFiles.length > 0 && (
                  <div className="flex flex-wrap gap-2 p-2 rounded-md mb-2" style={{ backgroundColor: 'var(--eleven-bg-tertiary)' }}>
                    {attachedFiles.map((file, index) => {
                      const fileSizeKB = (file.size / 1024).toFixed(0)
                      const fileSizeMB = (file.size / (1024 * 1024)).toFixed(1)
                      const sizeDisplay = file.size > 1024 * 1024 ? `${fileSizeMB}MB` : `${fileSizeKB}KB`
                      
                      return (
                        <div 
                          key={index}
                          className="flex items-center gap-2 px-3 py-1.5 rounded-full text-xs"
                          style={{ 
                            backgroundColor: 'var(--eleven-bg-card)',
                            border: '1px solid var(--eleven-border)'
                          }}
                        >
                          <FileText className="w-3.5 h-3.5 text-gray-600 dark:text-gray-400" />
                          <span className="max-w-[150px] truncate" style={{ color: 'var(--eleven-text-primary)' }}>
                            {file.name}
                          </span>
                          <span className="text-xs" style={{ color: 'var(--eleven-text-tertiary)' }}>
                            ({sizeDisplay})
                          </span>
                          <button
                            onClick={() => handleRemoveFile(index)}
                            className="p-0.5 rounded-full hover:bg-gray-200 transition-colors"
                          >
                            <X className="w-3 h-3" style={{ color: 'var(--eleven-text-secondary)' }} />
                          </button>
                        </div>
                      )
                    })}
                  </div>
                )}

                {/* Recording Indicator - Active Recording */}
                {isRecording && (
                  <div className="flex items-center gap-3 p-3 rounded-md mb-2 animate-pulse" 
                    style={{ backgroundColor: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.3)' }}
                  >
                    <div className="w-3 h-3 bg-red-500 rounded-full animate-ping" />
                    <span className="text-sm font-medium text-red-600">
                      Gravando... {recordingTime}s
                    </span>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={stopRecording}
                      className="ml-auto text-xs h-7"
                      style={{ borderColor: 'rgba(239, 68, 68, 0.5)', color: 'var(--status-error)' }}
                    >
                      <X className="w-3 h-3 mr-1" />
                      Cancelar
                    </Button>
                  </div>
                )}

                {/* Audio Ready Indicator - Recorded Audio Ready to Send */}
                {audioBlob && !isRecording && (
                  <div className="flex items-center gap-3 p-3 rounded-md mb-2 animate-in fade-in slide-in-from-bottom-2 duration-300" 
                    style={{ backgroundColor: 'rgba(229, 231, 235, 0.3)', border: '1px solid rgba(96, 190, 209, 0.3)' }}
                  >
                    <div className="flex items-center gap-2">
                      <Mic className="w-4 h-4 text-gray-600 dark:text-gray-400" />
                      <div className="flex flex-col">
                        <span className="text-sm font-medium text-gray-700">
                          Áudio gravado ({recordingTime}s)
                        </span>
                        <span className="text-xs" style={{ color: 'var(--eleven-text-secondary)' }}>
                          Pronto para enviar junto com sua mensagem
                        </span>
                      </div>
                    </div>
                    <div className="ml-auto flex items-center gap-2">
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => {
                          const url = URL.createObjectURL(audioBlob)
                          const audio = new Audio(url)
                          audio.play()
                        }}
                        className="text-xs h-7"
                        style={{ borderColor: 'rgba(96, 190, 209, 0.5)' }}
                      >
                        <Play className="w-3 h-3 mr-1" />
                        Ouvir
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => setAudioBlob(null)}
                        className="text-xs h-7"
                        style={{ borderColor: 'rgba(239, 68, 68, 0.5)', color: 'var(--status-error)' }}
                      >
                        <X className="w-3 h-3 mr-1" />
                        Remover
                      </Button>
                    </div>
                  </div>
                )}

                {/* File Analysis Context Indicator */}
                {fileAnalysisContext && (
                  <div className="flex items-center gap-3 p-3 rounded-md mb-2 animate-in fade-in slide-in-from-bottom-2 duration-300" 
                    style={{ backgroundColor: 'rgba(34, 197, 94, 0.1)', border: '1px solid rgba(34, 197, 94, 0.3)' }}
                  >
                    <div className="flex items-center gap-2">
                      <FileText className="w-4 h-4 text-green-600" />
                      <div className="flex flex-col">
                        <span className="text-sm font-medium text-green-600">
                          Arquivo analisado: {fileAnalysisContext.filename}
                        </span>
                        <span className="text-xs" style={{ color: 'var(--eleven-text-secondary)' }}>
                          A análise será enviada junto com sua próxima mensagem
                        </span>
                      </div>
                    </div>
                    <div className="ml-auto">
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => setFileAnalysisContext(null)}
                        className="text-xs h-7"
                        style={{ borderColor: 'rgba(239, 68, 68, 0.5)', color: 'var(--status-error)' }}
                      >
                        <X className="w-3 h-3 mr-1" />
                        Remover
                      </Button>
                    </div>
                  </div>
                )}

                {/* Indicador de ação pendente (ciclo fechado multi-turno) */}
                {activePendingAction && (
                  <div className="flex items-center gap-2 px-3 py-1.5 mb-2 rounded-md border text-xs"
                    style={{ backgroundColor: 'rgba(96, 190, 209, 0.08)', borderColor: 'rgba(96, 190, 209, 0.35)', color: 'var(--eleven-text-secondary)' }}
                  >
                    <span className="w-2 h-2 rounded-full bg-wedo-cyan animate-pulse shrink-0" />
                    <span>
                      Ação em andamento: <strong style={{ color: 'var(--eleven-text-primary)' }}>{activePendingAction.intent.replace(/_/g, " ")}</strong>
                    </span>
                    <button
                      className="ml-auto text-xs hover:opacity-80 transition-opacity"
                      style={{ color: 'var(--eleven-text-tertiary)' }}
                      onClick={() => handleSendMessage("cancelar")}
                      type="button"
                    >
                      × cancelar
                    </button>
                  </div>
                )}

                {/* Input com botões */}
                <div className="flex items-center space-x-2">
                  <div className="flex-1 relative">
                    <textarea
                      ref={inputRef}
                      value={input}
                      onChange={(e) => setInput(e.target.value)}
                      onKeyDown={handleKeyPress}
                      placeholder={getPlaceholderText()}
                      className="w-full resize-none rounded-md px-4 py-3 text-sm focus:outline-none focus:ring-1 focus:ring-gray-900/20 dark:focus:ring-gray-50/20 border border-gray-200" style={{ backgroundColor: 'var(--gray-50)', color: 'var(--eleven-text-primary)' }}
                      rows={1}
                    />
                  </div>

                  <div className="flex items-center space-x-1">
                    {/* Smart Search Toggle Button */}
                    <Button 
                      variant="ghost" 
                      size="sm" 
                      onClick={activateSmartSearch}
                      className="transition-all duration-200 hover:scale-105"
                      style={{ color: 'var(--eleven-text-secondary)' }}
                      title="Busca avançada de candidatos"
                    >
                      <Search className="w-4 h-4" />
                    </Button>
                    
                    {/* File Upload Button Component */}
                    <FileUploadButton
                      onFilesSelected={handleFilesSelected}
                      onFileAnalyzed={handleFileAnalyzed}
                      disabled={isLoading}
                      maxFiles={3}
                      showPreview={false}
                      autoAnalyze={true}
                    />
                    
                    {/* Audio Record Button Component */}
                    <AudioRecordButton
                      onTranscription={handleAudioTranscription}
                      onRecordingStart={handleAudioRecordingStart}
                      onRecordingEnd={handleAudioRecordingEnd}
                      disabled={isLoading}
                      maxDuration={60}
                    />
                    
                    {/* Send Button */}
                    <Button
                      onClick={() => handleSendMessage()}
                      disabled={!input.trim() || isLoading || emptyFieldNotifications.hasPendingNotifications}
                      size="sm"
                      className="transition-all duration-200 hover:scale-105 disabled:hover:scale-100 disabled:opacity-50"
                      style={{ 
                        backgroundColor: 'var(--eleven-text-primary)',
                        color: 'var(--eleven-bg-card)'
                      }}
                      title={emptyFieldNotifications.hasPendingNotifications ? "Resolva as pendências acima para continuar" : undefined}
                    >
                      <Send className="w-4 h-4" />
                    </Button>
                  </div>
                </div>

              </div>
            )}
          </div>
        </div>
        </>
        )}

        {/* Tab Content: Centro de Controle */}
        {activeTab === "controle" && (
          <AgentControlCenter />
        )}
      </div>

      {/* Context Panel */}
      {renderContextPanel()}

      {/* Command Palette - Global AI-First Command Surface */}
      <CommandPalette
        isOpen={isCommandPaletteOpen}
        onClose={() => setIsCommandPaletteOpen(false)}
        commands={commandItems}
        placeholder="Buscar ação ou digitar comando..."
      />

      {/* Interview Scheduling Modal */}
      {selectedCandidateForScheduling && (
        <InterviewSchedulingModal
          open={isSchedulingModalOpen}
          onOpenChange={setIsSchedulingModalOpen}
          candidateName={selectedCandidateForScheduling.name}
          candidateEmail={selectedCandidateForScheduling.email}
          candidateId={selectedCandidateForScheduling.id}
          jobTitle={selectedCandidateForScheduling.job_title}
          jobVacancyId={selectedCandidateForScheduling.job_vacancy_id}
          userName="Ana Silva"
          userEmail="ana.silva@wedotalent.com"
        />
      )}

      {/* Candidate Detail Sidebar (Pearch Integration) */}
      <CandidateDetailSidebar
        candidate={selectedCandidateForDetail}
        open={isCandidateDetailOpen}
        onClose={() => {
          setIsCandidateDetailOpen(false)
          setSelectedCandidateForDetail(null)
        }}
        onAddToJob={handleAddCandidateToJob}
        onScheduleInterview={(candidateId) => {
          if (selectedCandidateForDetail) {
            setSelectedCandidateForScheduling({
              name: selectedCandidateForDetail.name,
              email: selectedCandidateForDetail.email || "",
              id: candidateId,
              job_title: selectedCandidateForDetail.current_title || "Candidato"
            })
            setIsCandidateDetailOpen(false)
            setIsSchedulingModalOpen(true)
          }
        }}
        onFavorite={(candidateId) => {
          handleSendMessage(`Adicionar candidato ${selectedCandidateForDetail?.name || candidateId} aos favoritos`)
        }}
        onSaveToBase={handleSaveToBase}
      />

      {/* Credit Confirmation Dialog (Pearch Integration) */}
      <CreditConfirmationDialog
        open={isCreditDialogOpen}
        onClose={() => {
          setIsCreditDialogOpen(false)
          setPendingPearchSearch(null)
        }}
        onConfirm={handleConfirmPearchSearch}
        query={pendingPearchSearch?.query || ""}
        pearchType="pro"
        limit={10}
        costPerCandidate={5}
        totalEstimated={50}
        breakdown={{
          base: 5,
          insights: 0,
          emails: 2,
          phones: 14,
          freshness: 0
        }}
        creditsRemaining={availableCredits}
      />

      {/* Advanced Filters Modal */}
      <AdvancedFiltersModal
        isOpen={isFiltersModalOpen}
        onClose={() => setIsFiltersModalOpen(false)}
        onApply={handleApplyFilters}
        initialFilters={activeSearchFilters}
        estimatedMatches={1000000}
      />

      {/* Floating Prompt Suggestions Dock (persists after conversation starts) */}
      {!isEmptyChat && (
        <PromptSuggestionsDock
          onSelect={(command) => setInput(command)}
          isEmpty={false}
        />
      )}

      {/* UI Actions Side Panel Container */}
      <SidePanelContainer
        isOpen={uiActions.isPanelOpen}
        panelType={uiActions.activePanelType}
        title={uiActions.activePanelTitle}
        initialData={uiActions.activePanelData}
        isLoading={uiActions.isLoading}
        onClose={uiActions.closePanel}
        onSubmit={uiActions.submitPanel}
      />

      {/* Debug Buttons for Testing UI Actions Panels
          To enable: Set NEXT_PUBLIC_ENABLE_UI_ACTIONS_DEBUG=true in your .env.local file
          This panel is hidden by default even in development mode for security in staging/preview environments */}
      {process.env.NODE_ENV === 'development' && process.env.NEXT_PUBLIC_ENABLE_UI_ACTIONS_DEBUG === 'true' && (
        <div className="fixed bottom-24 right-4 z-50 flex flex-col gap-2">
          <div className="bg-gray-900/90 backdrop-blur-sm rounded-md p-2 border border-gray-700">
            <div className="text-xs text-gray-600 mb-2 px-2">Debug: UI Actions</div>
            <div className="flex flex-col gap-1">
              <button
                onClick={() => uiActions.openPanel("compensation_benefits", {
                  salary_min: 15000,
                  salary_max: 25000,
                  benefits: []
                }, "Remuneração e Benefícios")}
                className="px-3 py-1.5 text-xs bg-gray-900 hover:bg-gray-800 text-white dark:bg-gray-50 dark:text-gray-900 dark:hover:bg-gray-200 rounded transition-colors"
              >
                💰 Compensation
              </button>
              <button
                onClick={() => uiActions.openPanel("technical_requirements", {
                  requirements: []
                }, "Requisitos Técnicos")}
                className="px-3 py-1.5 text-xs bg-gray-900 hover:bg-gray-800 text-white dark:bg-gray-50 dark:text-gray-900 dark:hover:bg-gray-200 rounded transition-colors"
              >
                💻 Tech Requirements
              </button>
              <button
                onClick={() => uiActions.openPanel("behavioral_competencies", {
                  competencies: []
                }, "Competências Comportamentais")}
                className="px-3 py-1.5 text-xs bg-gray-900 hover:bg-gray-800 text-white dark:bg-gray-50 dark:text-gray-900 dark:hover:bg-gray-200 rounded transition-colors"
              >
                🧠 Competencies
              </button>
              <button
                onClick={() => uiActions.openPanel("interview_scheduling", {
                  candidate_id: "demo-1",
                  candidate_name: "João Silva",
                  interviewers: []
                }, "Agendar Entrevista")}
                className="px-3 py-1.5 text-xs bg-orange-600 hover:bg-orange-700 text-white rounded transition-colors"
              >
                📅 Interview
              </button>
              <button
                onClick={() => uiActions.openPanel("calibration_feedback", {
                  samples: [
                    {
                      id: "1",
                      name: "Maria Santos",
                      title: "Senior Developer",
                      location: "São Paulo",
                      experience_years: 8,
                      skills: ["React", "Node.js", "TypeScript"],
                      match_score: 92
                    },
                    {
                      id: "2", 
                      name: "Pedro Costa",
                      title: "Tech Lead",
                      location: "Remote",
                      experience_years: 10,
                      skills: ["Python", "AWS", "Docker"],
                      match_score: 87
                    }
                  ],
                  feedback: { approved: [], rejected: [], maybe: [] }
                }, "Calibração de Busca")}
                className="px-3 py-1.5 text-xs bg-pink-600 hover:bg-pink-700 text-white rounded transition-colors"
              >
                🎯 Calibration
              </button>
              <button
                onClick={() => uiActions.openPanel("wsi_questions", {
                  questions: []
                }, "Perguntas WSI")}
                className="px-3 py-1.5 text-xs bg-gray-900 hover:bg-gray-800 text-white dark:bg-gray-50 dark:text-gray-900 dark:hover:bg-gray-200 rounded transition-colors"
              >
                📝 WSI Questions
              </button>
              <div className="border-t border-gray-600 my-2 pt-2">
                <div className="text-xs text-gray-600 mb-1 px-2">Chat Cards</div>
              </div>
              <button
                onClick={() => {
                  const testMessage: Message = {
                    id: Date.now(),
                    sender: "lia",
                    content: "Aqui está o resumo do candidato:",
                    timestamp: new Date().toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" }),
                    type: "text",
                    chatCardType: "candidate_summary",
                    chatCardData: {
                      id: "demo-123",
                      name: "Maria Santos",
                      title: "Senior Developer",
                      location: "São Paulo, SP",
                      experience_years: 8,
                      skills: ["React", "TypeScript", "Node.js", "AWS"],
                      match_score: 92,
                      email: "maria.santos@email.com",
                      linkedin_url: "https://linkedin.com/in/mariasantos"
                    }
                  }
                  setMessages(prev => [...prev, testMessage])
                }}
                className="px-3 py-1.5 text-xs bg-gray-900 hover:bg-gray-800 text-white dark:bg-gray-50 dark:text-gray-900 dark:hover:bg-gray-200 rounded transition-colors"
              >
                👤 Candidate Card
              </button>
              <button
                onClick={() => {
                  const testMessage: Message = {
                    id: Date.now(),
                    sender: "lia",
                    content: "Aqui está a pontuação WSI do candidato:",
                    timestamp: new Date().toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" }),
                    type: "text",
                    chatCardType: "wsi_score",
                    chatCardData: {
                      candidate_name: "João Silva",
                      overall_score: 85,
                      work_style: { score: 88, details: "Altamente colaborativo e orientado a resultados" },
                      independence: { score: 82, details: "Boa autonomia em tarefas complexas" },
                      consistency: { score: 85, details: "Consistente na entrega de projetos" }
                    }
                  }
                  setMessages(prev => [...prev, testMessage])
                }}
                className="px-3 py-1.5 text-xs bg-violet-600 hover:bg-violet-700 text-white rounded transition-colors"
              >
                📊 WSI Score Card
              </button>
              <button
                onClick={() => {
                  const testMessage: Message = {
                    id: Date.now(),
                    sender: "lia",
                    content: "Entrevista agendada com sucesso:",
                    timestamp: new Date().toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" }),
                    type: "text",
                    chatCardType: "interview_confirmation",
                    chatCardData: {
                      candidate_name: "Pedro Costa",
                      interview_date: "2024-03-15",
                      interview_time: "14:00",
                      interview_type: "remoto",
                      interviewers: ["Ana Silva", "Carlos Mendes"],
                      meeting_link: "https://meet.google.com/abc-defg-hij"
                    }
                  }
                  setMessages(prev => [...prev, testMessage])
                }}
                className="px-3 py-1.5 text-xs bg-amber-600 hover:bg-amber-700 text-white rounded transition-colors"
              >
                📅 Interview Card
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
