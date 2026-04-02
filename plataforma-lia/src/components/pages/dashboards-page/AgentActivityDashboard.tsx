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
  // @ts-ignore TODO: fix type
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


export function AgentActivityDashboard() {
  const [selectedAgentFilter, setSelectedAgentFilter] = useState<string>('all')
  const [selectedTypeFilter, setSelectedTypeFilter] = useState<string>('all')

  const activeAgents = agentsData.filter(a => a.status === 'active' || a.status === 'busy').length
  const totalActionsToday = agentsData.reduce((sum, a) => sum + a.actionsToday, 0)
  const avgSuccessRate = Math.round(agentsData.reduce((sum, a) => sum + a.successRate, 0) / agentsData.length)
  const avgResponseTime = (agentsData.reduce((sum, a) => sum + a.avgResponseTime, 0) / agentsData.length).toFixed(1)

  const filteredActions = recentActionsData.filter(action => {
    if (selectedAgentFilter !== 'all' && action.agentId !== selectedAgentFilter) return false
    if (selectedTypeFilter !== 'all' && action.type !== selectedTypeFilter) return false
    return true
  })

  const actionTypes = [...new Set(recentActionsData.map(a => a.type))]

  const getStatusColor = (status: AgentInfo['status']) => {
    switch (status) {
      case 'active': return 'bg-gray-900 dark:bg-gray-50'
      case 'busy': return 'bg-wedo-green-bright'
      case 'idle': return 'bg-gray-400'
      case 'error': return 'bg-status-error'
    }
  }

  const getStatusLabel = (status: AgentInfo['status']) => {
    switch (status) {
      case 'active': return 'Ativo'
      case 'busy': return 'Ocupado'
      case 'idle': return 'Inativo'
      case 'error': return 'Erro'
    }
  }

  const getActionStatusColor = (status: RecentAction['status']) => {
    switch (status) {
      case 'success': return 'bg-status-success/15 text-status-success dark:bg-status-success/30 dark:text-status-success'
      case 'pending': return 'bg-status-warning/15 text-status-warning dark:bg-status-warning/30 dark:text-status-warning'
      case 'error': return 'bg-status-error/15 text-status-error dark:bg-status-error/30 dark:text-status-error'
    }
  }

  const getActionStatusLabel = (status: RecentAction['status']) => {
    switch (status) {
      case 'success': return 'Sucesso'
      case 'pending': return 'Pendente'
      case 'error': return 'Erro'
    }
  }

  return (
    <div className="space-y-3">
      {/* Header */}
      <div>
        <h1 className={`${textStyles.title} flex items-center gap-2`}>
          <Brain className="w-3.5 h-3.5 text-wedo-cyan" />
          Atividade dos Agentes
        </h1>
        <p className={`${textStyles.bodySmall} mt-1`}>
          Monitoramento e métricas dos 7 agentes IA especializados da plataforma LIA
        </p>
      </div>

      {/* A. Seção KPIs (4 cards no topo) */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-2.5">
        {/* Total de Ações Hoje */}
        <Card className={`${cardStyles.default} dark:bg-lia-bg-primary dark:border-lia-border-subtle`}>
          <CardContent className="p-3">
            <div className="flex items-start justify-between mb-2">
              <p className={`${textStyles.bodySmall}`}>Total de Ações Hoje</p>
              <Activity className="w-3.5 h-3.5 text-lia-text-secondary" />
            </div>
            <div className="text-xl font-inter font-bold text-lia-text-primary">{totalActionsToday}</div>
 <p className={`${textStyles.bodySmall} text-lia-text-primary mt-1`}>+18% vs. ontem</p>
          </CardContent>
        </Card>

        {/* Taxa de Sucesso */}
        <Card className={`${cardStyles.default} dark:bg-lia-bg-primary dark:border-lia-border-subtle`}>
          <CardContent className="p-3">
            <div className="flex items-start justify-between mb-2">
              <p className={`${textStyles.bodySmall}`}>Taxa de Sucesso</p>
              <CheckCircle className="w-3.5 h-3.5 text-wedo-green" />
            </div>
            <div className="text-xl font-inter font-bold text-lia-text-primary">{avgSuccessRate}%</div>
            <p className={`${textStyles.bodySmall} text-status-success dark:text-status-success mt-1`}>Média geral dos agentes</p>
          </CardContent>
        </Card>

        {/* Tempo Médio de Resposta */}
        <Card className={`${cardStyles.default} dark:bg-lia-bg-primary dark:border-lia-border-subtle`}>
          <CardContent className="p-3">
            <div className="flex items-start justify-between mb-2">
              <p className={`${textStyles.bodySmall}`}>Tempo Médio de Resposta</p>
              <TrendingUp className="w-3.5 h-3.5 text-wedo-orange" />
            </div>
            <div className="text-xl font-inter font-bold text-lia-text-primary">{avgResponseTime}s</div>
            <p className={`${textStyles.bodySmall} text-wedo-orange dark:text-wedo-orange mt-1`}>-0.3s vs. semana passada</p>
          </CardContent>
        </Card>

        {/* Agentes Ativos */}
        <Card className={`${cardStyles.default} dark:bg-lia-bg-primary dark:border-lia-border-subtle`}>
          <CardContent className="p-3">
            <div className="flex items-start justify-between mb-2">
              <p className={`${textStyles.bodySmall}`}>Agentes Ativos</p>
              <Brain className="w-3.5 h-3.5 text-wedo-purple" />
            </div>
            <div className="text-xl font-inter font-bold text-lia-text-primary">{activeAgents}/7</div>
            <p className={`${textStyles.bodySmall} text-wedo-purple dark:text-wedo-purple mt-1`}>Sistema operacional</p>
          </CardContent>
        </Card>
      </div>

      {/* B. Grid de Status dos Agentes */}
      <Card className={`${cardStyles.default} dark:bg-lia-bg-primary dark:border-lia-border-subtle`}>
        <CardHeader className="px-4 py-3">
          <CardTitle className={`${textStyles.subtitle} flex items-center gap-2`}>
            <Brain className="w-3.5 h-3.5 text-wedo-cyan" />
            Status dos Agentes Especializados
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 xl:grid-cols-7 gap-2.5">
            {agentsData.map((agent) => (
              <div 
                key={agent.id}
                className="p-3 bg-gray-50 dark:bg-lia-bg-primary rounded-md border border-lia-border-subtle dark:border-lia-border-subtle hover:border-gray-900 dark:hover:border-gray-50 dark:hover:border-gray-900 dark:hover:border-gray-50 transition-colors motion-reduce:transition-none"
              >
                {/* Header com status */}
                <div className="flex items-start justify-between mb-2">
                  <div className="flex items-center gap-1.5">
                    <div className={`w-2 h-2 rounded-full ${getStatusColor(agent.status)}`}></div>
                    <span className={`${textStyles.description}`}>{getStatusLabel(agent.status)}</span>
                  </div>
                </div>

                {/* Nome e descrição */}
                <div className="mb-2">
                  <p className="font-semibold font-open-sans text-sm text-lia-text-primary truncate" style={{color: agent.color}}>
                    {agent.name}
                  </p>
                  <p className="text-xs tracking-tight font-open-sans text-lia-text-primary truncate">
                    {agent.description}
                  </p>
                </div>

                {/* Métricas do dia */}
                <div className="space-y-1.5">
                  <div className="flex items-center justify-between">
                    <span className={`${textStyles.description}`}>Ações</span>
                    <span className="text-xs font-inter font-bold text-lia-text-primary">{agent.actionsToday}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className={`${textStyles.description}`}>Sucesso</span>
                    <span className="text-xs font-inter font-bold text-status-success dark:text-status-success">{agent.successRate}%</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className={`${textStyles.description}`}>Tempo</span>
                    <span className="text-xs font-inter font-bold text-lia-text-primary">{agent.avgResponseTime}s</span>
                  </div>
                </div>

                {/* Sparkline simplificado (visual bar) */}
                <div className="mt-2 flex items-end gap-0.5 h-6">
                  {[40, 65, 45, 80, 55, 70, 90, 60].map((value, idx) => (
                    <div 
                      key={idx}
                      className="flex-1 rounded-sm transition-colors motion-reduce:transition-none"
                      style={{height: `${value}%`, 
                        backgroundColor: agent.color,
                        opacity: 0.4 + (idx * 0.08)}}
                    ></div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* C. Gráfico de Atividade por Agente */}
      <Card className={`${cardStyles.default} dark:bg-lia-bg-primary dark:border-lia-border-subtle`}>
        <CardHeader className="px-4 py-3">
          <CardTitle className={`${textStyles.subtitle} flex items-center gap-2`}>
            <BarChart3 className="w-3.5 h-3.5 text-lia-text-secondary" />
            Volume de Ações por Agente (Hoje)
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {agentsData
              .sort((a, b) => b.actionsToday - a.actionsToday)
              .map((agent) => {
                const maxActions = Math.max(...agentsData.map(a => a.actionsToday))
                const percentage = (agent.actionsToday / maxActions) * 100
                
                return (
                  <div key={agent.id} className="space-y-1.5">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <div className="w-2.5 h-2.5 rounded-full" style={{backgroundColor: agent.color}}></div>
                        <span className="text-xs font-open-sans font-medium text-lia-text-primary">{agent.name}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-inter font-bold text-lia-text-primary">{agent.actionsToday}</span>
                        <Badge className={`text-xs tracking-tight ${
                          agent.successRate >= 98 ? 'bg-status-success/15 text-status-success dark:bg-status-success/30 dark:text-status-success' :
 agent.successRate >= 95 ? 'bg-gray-100 text-lia-text-primary' :
                          'bg-status-warning/15 text-status-warning dark:bg-status-warning/30 dark:text-status-warning'
                        }`}>
                          {agent.successRate}%
                        </Badge>
                      </div>
                    </div>
                    <div className="w-full bg-gray-200 dark:bg-lia-bg-elevated rounded-full h-2">
                      <div 
                        className="h-2 rounded-full transition-[width,height]"
                        style={{width: `${percentage}%`, backgroundColor: agent.color}}
                      ></div>
                    </div>
                  </div>
                )
              })}
          </div>
        </CardContent>
      </Card>

      {/* D. Tabela de Ações Recentes */}
      <Card className={`${cardStyles.default} dark:bg-lia-bg-primary dark:border-lia-border-subtle`}>
        <CardHeader className="px-4 py-3">
          <div className="flex items-center justify-between">
            <CardTitle className={`${textStyles.subtitle} flex items-center gap-2`}>
              <Activity className="w-3.5 h-3.5 text-lia-text-secondary" />
              Ações Recentes
            </CardTitle>
            
            {/* Filtros */}
            <div className="flex items-center gap-2">
              <select
                value={selectedAgentFilter}
                onChange={(e) => setSelectedAgentFilter(e.target.value)}
                className="text-xs font-open-sans px-2 py-1 rounded-full border border-lia-border-subtle dark:border-lia-border-subtle bg-white dark:bg-lia-bg-primary text-lia-text-primary"
              >
                <option value="all">Todos os Agentes</option>
                {agentsData.map(agent => (
                  <option key={agent.id} value={agent.id}>{agent.name}</option>
                ))}
              </select>
              
              <select
                value={selectedTypeFilter}
                onChange={(e) => setSelectedTypeFilter(e.target.value)}
                className="text-xs font-open-sans px-2 py-1 rounded-full border border-lia-border-subtle dark:border-lia-border-subtle bg-white dark:bg-lia-bg-primary text-lia-text-primary"
              >
                <option value="all">Todos os Tipos</option>
                {actionTypes.map(type => (
                  <option key={type} value={type}>{type}</option>
                ))}
              </select>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-lia-border-subtle dark:border-lia-border-subtle">
                  <th className="text-left py-2 px-2 text-xs tracking-tight font-open-sans font-semibold text-lia-text-primary uppercase">Hora</th>
                  <th className="text-left py-2 px-2 text-xs tracking-tight font-open-sans font-semibold text-lia-text-primary uppercase">Agente</th>
                  <th className="text-left py-2 px-2 text-xs tracking-tight font-open-sans font-semibold text-lia-text-primary uppercase">Tipo</th>
                  <th className="text-left py-2 px-2 text-xs tracking-tight font-open-sans font-semibold text-lia-text-primary uppercase">Descrição</th>
                  <th className="text-left py-2 px-2 text-xs tracking-tight font-open-sans font-semibold text-lia-text-primary uppercase">Status</th>
                </tr>
              </thead>
              <tbody>
                {filteredActions.map((action) => {
                  const agent = agentsData.find(a => a.id === action.agentId)
                  return (
                    <tr key={action.id} className="border-b border-lia-border-subtle dark:border-lia-border-subtle hover:bg-gray-50 dark:hover:bg-gray-900/50">
                      <td className="py-2 px-2">
                        <span className="text-xs font-inter font-medium text-lia-text-primary">{action.time}</span>
                      </td>
                      <td className="py-2 px-2">
                        <div className="flex items-center gap-1.5">
                          <div className="w-2 h-2 rounded-full" style={{backgroundColor: agent?.color || 'var(--gray-950)'}}></div>
                          <span className="text-xs font-open-sans font-medium text-lia-text-primary">{action.agentName}</span>
                        </div>
                      </td>
                      <td className="py-2 px-2">
                        <Badge variant="outline" className="text-xs tracking-tight font-open-sans">
                          {action.type}
                        </Badge>
                      </td>
                      <td className="py-2 px-2">
                        <span className="text-xs font-open-sans text-lia-text-secondary line-clamp-1 max-w-sidebar-content">{action.description}</span>
                      </td>
                      <td className="py-2 px-2">
                        <Badge className={`text-xs tracking-tight ${getActionStatusColor(action.status)}`}>
                          {getActionStatusLabel(action.status)}
                        </Badge>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
          
          {filteredActions.length === 0 && (
            <div className="text-center py-6">
 <Activity className="w-8 h-8 mx-auto text-lia-text-disabled mb-2" />
              <p className="text-xs font-open-sans text-lia-text-primary">Nenhuma ação encontrada com os filtros selecionados</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Insights dos Agentes */}
      <Card className={`${cardStyles.default} dark:bg-lia-bg-primary dark:border-lia-border-subtle`}>
        <CardHeader className="px-4 py-3">
          <CardTitle className={`${textStyles.title} flex items-center gap-2`}>
            <Brain className="w-3.5 h-3.5 text-wedo-cyan" />
            Insights do Sistema de Agentes
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex items-start gap-3">
            <CheckCircle className="w-3.5 h-3.5 mt-0.5 flex-shrink-0 text-wedo-green" />
            <p className="text-sm font-open-sans text-lia-text-primary">
              <strong>Performance excelente:</strong> Agente Screening lidera com 215 ações e 96% de sucesso. Análise de CVs automatizada reduzindo tempo em 78%.
            </p>
          </div>
          <div className="flex items-start gap-3">
            <TrendingUp className="w-3.5 h-3.5 mt-0.5 flex-shrink-0 text-lia-text-secondary" />
            <p className="text-sm font-open-sans text-lia-text-primary">
              <strong>Agente Sourcing ativo:</strong> 128 buscas realizadas hoje. Pipeline de talentos ampliado em 23 perfis qualificados.
            </p>
          </div>
          <div className="flex items-start gap-3">
            <AlertTriangle className="w-3.5 h-3.5 mt-0.5 flex-shrink-0 text-wedo-orange" />
            <p className="text-sm font-open-sans text-lia-text-primary">
              <strong>Atenção:</strong> Agente Communication em modo idle. Considere revisar filas de mensagens pendentes.
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
