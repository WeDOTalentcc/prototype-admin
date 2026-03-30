"use client"

"use client"

import React, { useState } from "react"
import type { ComponentType, CSSProperties } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import {
  BarChart3, TrendingUp, Brain, Target, Users, PieChart,
  Heart, Award, CheckCircle, Activity, MapPin, Building,
  Lightbulb, AlertTriangle, ChevronLeft, ChevronRight, Lock, Unlock, Phone
} from "lucide-react"
import { BigFiveDashboardPage } from "../big-five-dashboard-page"
import { ModuleUpsell } from "@/components/module-access/module-upsell"
import { hasModuleAccess } from "@/utils/license-manager"
import { textStyles, cardStyles, badgeStyles } from '@/lib/design-tokens'
import { DailyBriefingCard } from "@/components/daily-briefing-card"

// Tipos de dashboards disponíveis
type DashboardType = "estrategicos" | "previsoes-ia" | "people-analytics" | "modelos-trabalho" | "funil-performance" | "war-room" | "competencias" | "voice-screening" | "agent-activity"

interface DashboardMenuItem {
  id: DashboardType
  label: string
  icon: ComponentType<{ className?: string; style?: CSSProperties }>
  description: string
  count?: number
  color?: string
}

const dashboardMenuItems: DashboardMenuItem[] = [
  {
    id: "estrategicos",
    label: "Indicadores Estratégicos",
    icon: Target,
    description: "KPIs de negócio, performance de recrutadores e ROI",
    count: 12,
    color: "var(--wedo-purple)" // Roxo WeDo - Estratégia premium
  },
  {
    id: "previsoes-ia",
    label: "Previsões & IA",
    icon: Brain,
    description: "Machine Learning, previsões de demanda e alertas inteligentes",
    count: 8 // Ciano WeDo - Tecnologia/IA
  },
  {
    id: "people-analytics",
    label: "People Analytics",
    icon: Users,
    description: "Big Five, Diversidade & Inclusão, NPS e Satisfação",
    count: 344,
    color: "var(--status-success)" // Verde WeDo - Pessoas/qualidade
  },
  {
    id: "modelos-trabalho",
    label: "Modelos de Trabalho",
    icon: PieChart,
    description: "Remoto, Híbrido, Presencial - análises por região e departamento",
    count: 102,
    color: "var(--wedo-orange)" // Laranja WeDo - Tempo/operação
  },
  {
    id: "funil-performance",
    label: "Funil & Performance",
    icon: TrendingUp,
    description: "Conversão do pipeline, efetividade por canal e qualidade",
    count: 67 // Ciano WeDo - Performance
  },
  {
    id: "war-room",
    label: "War Room Operacional",
    icon: AlertTriangle,
    description: "Alertas críticos, ações urgentes e pipelines em risco",
    count: 8,
    color: "var(--wedo-magenta)" // Magenta WeDo - Urgência crítica
  },
  {
    id: "competencias",
    label: "Análise de Competências",
    icon: Award,
    description: "Skills gap, competências emergentes e matriz de desenvolvimento",
    count: 14,
    color: "var(--status-success)" // Verde WeDo - Desenvolvimento/qualidade
  },
  {
    id: "voice-screening",
    label: "Voice Screening",
    icon: Phone,
    description: "Análise de triagem por voz com IA - OpenMic.ai + LIA",
    count: 0 // Ciano WeDo - IA/Tecnologia
  },
  {
    id: "agent-activity",
    label: "Atividade dos Agentes",
    icon: Brain,
    description: "Monitoramento e métricas dos agentes IA especializados",
    count: 7 // Ciano WeDo - IA
  }
]

interface DashboardsPageProps {
  onNavigate?: (page: string) => void
}


export function NPSDashboard() {
  return (
    <div className="space-y-3">
      {/* KPIs de NPS */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-2.5">
        <Card className={`${cardStyles.default} dark:bg-gray-950 dark:border-gray-800`}>
          <CardContent className="p-3">
            <div className="flex items-start justify-between mb-2">
              <p className={`${textStyles.bodySmall} dark:text-lia-text-tertiary`}>NPS Geral</p>
              <Award className="w-3.5 h-3.5 text-wedo-green" />
            </div>
            <div className="text-xl font-inter font-bold text-gray-950 dark:text-gray-50">+67</div>
            <p className={`${textStyles.bodySmall} text-status-success dark:text-status-success mt-1`}>Excelente (acima de 50)</p>
          </CardContent>
        </Card>

        <Card className={`${cardStyles.default} dark:bg-gray-950 dark:border-gray-800`}>
          <CardContent className="p-3">
            <div className="flex items-start justify-between mb-2">
              <p className={`${textStyles.bodySmall} dark:text-lia-text-tertiary`}>Promotores</p>
              <CheckCircle className="w-3.5 h-3.5 text-wedo-green" />
            </div>
            <div className="text-xl font-inter font-bold text-gray-950 dark:text-gray-50">72%</div>
            <p className={`${textStyles.bodySmall} text-status-success dark:text-status-success mt-1`}>64 de 89 respostas</p>
          </CardContent>
        </Card>

        <Card className={`${cardStyles.default} dark:bg-gray-950 dark:border-gray-800`}>
          <CardContent className="p-3">
            <div className="flex items-start justify-between mb-2">
              <p className={`${textStyles.bodySmall} dark:text-lia-text-tertiary`}>Neutros</p>
              <Activity className="w-3.5 h-3.5 text-gray-800 dark:text-lia-text-primary" />
            </div>
            <div className="text-xl font-inter font-bold text-gray-950 dark:text-gray-50">23%</div>
            <p className={`${textStyles.bodySmall} dark:text-lia-text-tertiary mt-1`}>21 de 89 respostas</p>
          </CardContent>
        </Card>

        <Card className={`${cardStyles.default} dark:bg-gray-950 dark:border-gray-800`}>
          <CardContent className="p-3">
            <div className="flex items-start justify-between mb-2">
              <p className={`${textStyles.bodySmall} dark:text-lia-text-tertiary`}>Detratores</p>
              <AlertTriangle className="w-3.5 h-3.5 text-wedo-magenta" />
            </div>
            <div className="text-xl font-inter font-bold text-gray-950 dark:text-gray-50">5%</div>
            <p className={`${textStyles.bodySmall} text-status-error dark:text-status-error mt-1`}>4 de 89 respostas</p>
          </CardContent>
        </Card>
      </div>

      {/* Distribuição NPS */}
      <Card className="border-lia-border-subtle dark:border-gray-800 rounded-md bg-white dark:bg-gray-950">
        <CardHeader className="px-4 py-3">
          <CardTitle className="text-xs font-sans font-open-sans font-semibold text-gray-950 dark:text-gray-50">
            Distribuição de Respostas
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {/* Promotores */}
          <div className="space-y-1.5">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-wedo-green"></div>
                <span className="text-xs font-open-sans text-gray-800 dark:text-lia-text-primary">Promotores (9-10)</span>
              </div>
              <span className="text-sm font-inter font-bold text-gray-950 dark:text-gray-50">72%</span>
            </div>
            <div className="w-full bg-gray-200 dark:bg-lia-bg-elevated rounded-full h-3">
              <div className="h-3 rounded-full bg-wedo-green w-[72%]"></div>
            </div>
          </div>

          {/* Neutros */}
          <div className="space-y-1.5">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-gray-400"></div>
                <span className="text-xs font-open-sans text-gray-800 dark:text-lia-text-primary">Neutros (7-8)</span>
              </div>
              <span className="text-sm font-inter font-bold text-gray-950 dark:text-gray-50">23%</span>
            </div>
            <div className="w-full bg-gray-200 dark:bg-lia-bg-elevated rounded-full h-3">
              <div className="h-3 rounded-full bg-gray-400 w-[23%]"></div>
            </div>
          </div>

          {/* Detratores */}
          <div className="space-y-1.5">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-wedo-magenta"></div>
                <span className="text-xs font-open-sans text-gray-800 dark:text-lia-text-primary">Detratores (0-6)</span>
              </div>
              <span className="text-sm font-inter font-bold text-gray-950 dark:text-gray-50">5%</span>
            </div>
            <div className="w-full bg-gray-200 dark:bg-lia-bg-elevated rounded-full h-3">
              <div className="h-3 rounded-full bg-wedo-magenta w-[5%]"></div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Satisfação por Etapa */}
      <Card className="border-lia-border-subtle dark:border-gray-800 rounded-md bg-white dark:bg-gray-950">
        <CardHeader className="px-4 py-3">
          <CardTitle className="text-xs font-sans font-open-sans font-semibold text-gray-950 dark:text-gray-50">
            Satisfação por Etapa do Processo
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          <div className="flex items-center justify-between p-2 bg-gray-50 dark:bg-lia-bg-secondary/50 rounded-md">
            <span className="text-xs font-open-sans text-gray-800 dark:text-lia-text-primary">Aplicação Inicial</span>
            <div className="flex items-center gap-2">
              <Badge className="bg-status-success/15 text-status-success dark:bg-status-success/30 dark:text-status-success text-xs tracking-tight">Excelente</Badge>
              <span className="text-sm font-inter font-bold">9.2</span>
            </div>
          </div>
          <div className="flex items-center justify-between p-2 bg-gray-50 dark:bg-lia-bg-secondary/50 rounded-md">
            <span className="text-xs font-open-sans text-gray-800 dark:text-lia-text-primary">Comunicação</span>
            <div className="flex items-center gap-2">
 <Badge className="bg-gray-100 text-gray-900 dark:text-lia-text-secondary text-xs tracking-tight">Muito Bom</Badge>
              <span className="text-sm font-inter font-bold">8.8</span>
            </div>
          </div>
          <div className="flex items-center justify-between p-2 bg-gray-50 dark:bg-lia-bg-secondary/50 rounded-md">
            <span className="text-xs font-open-sans text-gray-800 dark:text-lia-text-primary">Entrevistas</span>
            <div className="flex items-center gap-2">
              <Badge className="bg-wedo-purple/15 text-wedo-purple dark:bg-wedo-purple/30 dark:text-wedo-purple text-xs tracking-tight">Muito Bom</Badge>
              <span className="text-sm font-inter font-bold">8.6</span>
            </div>
          </div>
          <div className="flex items-center justify-between p-2 bg-gray-50 dark:bg-lia-bg-secondary/50 rounded-md">
            <span className="text-xs font-open-sans text-gray-800 dark:text-lia-text-primary">Tempo de Resposta</span>
            <div className="flex items-center gap-2">
              <Badge className="bg-wedo-orange/15 text-wedo-orange dark:bg-wedo-orange/30 dark:text-wedo-orange text-xs tracking-tight">Bom</Badge>
              <span className="text-sm font-inter font-bold">7.9</span>
            </div>
          </div>
          <div className="flex items-center justify-between p-2 bg-gray-50 dark:bg-lia-bg-secondary/50 rounded-md">
            <span className="text-xs font-open-sans text-gray-800 dark:text-lia-text-primary">Feedback Pós-Entrevista</span>
            <div className="flex items-center gap-2">
              <Badge className="bg-status-warning/15 text-status-warning dark:bg-status-warning/30 dark:text-status-warning text-xs tracking-tight">Regular</Badge>
              <span className="text-sm font-inter font-bold">6.8</span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Principais Feedbacks */}
      <Card className="border-lia-border-subtle dark:border-gray-800 rounded-md bg-white dark:bg-gray-950">
        <CardHeader className="px-4 py-3">
          <CardTitle className={`${textStyles.subtitle} dark:text-lia-text-primary flex items-center gap-2`}>
            <Brain className="w-3.5 h-3.5 text-wedo-cyan" />
            Insights dos Candidatos
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex items-start gap-3">
            <CheckCircle className="w-3.5 h-3.5 mt-0.5 flex-shrink-0 text-wedo-green" />
            <p className="text-sm font-open-sans text-gray-800 dark:text-lia-text-primary">
              <strong>Pontos Positivos:</strong> Plataforma intuitiva e processo transparente elogiados por 89% dos candidatos.
            </p>
          </div>
          <div className="flex items-start gap-3">
            <AlertTriangle className="w-3.5 h-3.5 mt-0.5 flex-shrink-0 text-wedo-orange" />
            <p className="text-sm font-open-sans text-gray-800 dark:text-lia-text-primary">
              <strong>Oportunidade de Melhoria:</strong> Tempo de resposta pós-entrevista pode ser reduzido. Meta: responder em até 3 dias.
            </p>
          </div>
          <div className="flex items-start gap-3">
            <TrendingUp className="w-3.5 h-3.5 mt-0.5 flex-shrink-0 text-gray-600 dark:text-lia-text-tertiary" />
            <p className="text-sm font-open-sans text-gray-800 dark:text-lia-text-primary">
              <strong>Tendência Positiva:</strong> NPS cresceu +12 pontos nos últimos 3 meses após implementação de melhorias.
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

// ============================================================
// DASHBOARD DE ATIVIDADE DOS AGENTES IA
// ============================================================

interface AgentInfo {
  id: string
  name: string
  description: string
  status: 'active' | 'idle' | 'busy' | 'error'
  actionsToday: number
  successRate: number
  avgResponseTime: number
  color: string
}

interface RecentAction {
  id: string
  time: string
  agentId: string
  agentName: string
  type: string
  description: string
  status: 'success' | 'pending' | 'error'
}

const agentsData: AgentInfo[] = [
  {
    id: 'job-intake',
    name: 'Job Intake',
    description: 'Criação e análise de vagas',
    status: 'active',
    actionsToday: 47,
    successRate: 98,
    avgResponseTime: 1.2,
    color: 'var(--wedo-purple)'
  },
  {
    id: 'sourcing',
    name: 'Sourcing',
    description: 'Busca proativa de talentos',
    status: 'busy',
    actionsToday: 128,
    successRate: 94,
    avgResponseTime: 2.8
  },
  {
    id: 'screening',
    name: 'Screening',
    description: 'Triagem e análise de CVs',
    status: 'active',
    actionsToday: 215,
    successRate: 96,
    avgResponseTime: 0.8,
    color: 'var(--status-success)'
  },
  {
    id: 'scheduling',
    name: 'Scheduling',
    description: 'Agendamento de entrevistas',
    status: 'active',
    actionsToday: 34,
    successRate: 99,
    avgResponseTime: 1.5,
    color: 'var(--wedo-orange)'
  },
  {
    id: 'communication',
    name: 'Communication',
    description: 'E-mails e mensagens',
    status: 'idle',
    actionsToday: 89,
    successRate: 97,
    avgResponseTime: 0.5,
    color: 'var(--gray-400)'
  },
  {
    id: 'analytics',
    name: 'Analytics',
    description: 'Relatórios e insights',
    status: 'active',
    actionsToday: 23,
    successRate: 100,
    avgResponseTime: 3.2,
    color: 'var(--wedo-cyan)'
  },
  {
    id: 'recruiter-assistant',
    name: 'Recruiter Assistant',
    description: 'Assistente do recrutador',
    status: 'busy',
    actionsToday: 156,
    successRate: 95,
    avgResponseTime: 1.1,
    color: 'var(--wedo-purple)'
  }
]

const recentActionsData: RecentAction[] = [
  { id: '1', time: '14:32', agentId: 'screening', agentName: 'Screening', type: 'Análise CV', description: 'Análise completa de CV para vaga Dev Senior', status: 'success' },
  { id: '2', time: '14:28', agentId: 'sourcing', agentName: 'Sourcing', type: 'Busca', description: 'Busca de 15 candidatos React no LinkedIn', status: 'success' },
  { id: '3', time: '14:25', agentId: 'communication', agentName: 'Communication', type: 'E-mail', description: 'Envio de convite para entrevista técnica', status: 'success' },
  { id: '4', time: '14:22', agentId: 'scheduling', agentName: 'Scheduling', type: 'Agendamento', description: 'Agendamento de entrevista para 28/11 às 10:00', status: 'pending' },
  { id: '5', time: '14:18', agentId: 'recruiter-assistant', agentName: 'Recruiter Assistant', type: 'Sugestão', description: 'Sugestão de candidatos para vaga urgente', status: 'success' },
  { id: '6', time: '14:15', agentId: 'job-intake', agentName: 'Job Intake', type: 'Criação Vaga', description: 'Nova vaga criada: Product Manager Senior', status: 'success' },
  { id: '7', time: '14:12', agentId: 'analytics', agentName: 'Analytics', type: 'Relatório', description: 'Relatório semanal de métricas gerado', status: 'success' },
  { id: '8', time: '14:08', agentId: 'screening', agentName: 'Screening', type: 'Match', description: 'Match scoring para 8 candidatos', status: 'success' },
  { id: '9', time: '14:05', agentId: 'sourcing', agentName: 'Sourcing', type: 'Importação', description: 'Importação de 23 perfis do GitHub', status: 'error' },
  { id: '10', time: '14:02', agentId: 'communication', agentName: 'Communication', type: 'WhatsApp', description: 'Mensagem de follow-up enviada', status: 'success' }
]

