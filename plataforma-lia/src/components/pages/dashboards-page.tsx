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
import { BigFiveDashboardPage } from "./big-five-dashboard-page"
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
    color: "#9860D1" // Roxo WeDo - Estratégia premium
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
    color: "#60D186" // Verde WeDo - Pessoas/qualidade
  },
  {
    id: "modelos-trabalho",
    label: "Modelos de Trabalho",
    icon: PieChart,
    description: "Remoto, Híbrido, Presencial - análises por região e departamento",
    count: 102,
    color: "#D19960" // Laranja WeDo - Tempo/operação
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
    color: "#D160AB" // Magenta WeDo - Urgência crítica
  },
  {
    id: "competencias",
    label: "Análise de Competências",
    icon: Award,
    description: "Skills gap, competências emergentes e matriz de desenvolvimento",
    count: 14,
    color: "#60D186" // Verde WeDo - Desenvolvimento/qualidade
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

export function DashboardsPage({ onNavigate }: DashboardsPageProps = {}) {
  const [activeDashboard, setActiveDashboard] = useState<DashboardType>("people-analytics")
  const [isMenuCollapsed, setIsMenuCollapsed] = useState(true)
  const [isMenuLocked, setIsMenuLocked] = useState(false)
  const [isHovering, setIsHovering] = useState(false)
  const [showBriefing, setShowBriefing] = useState(true)

  // Renderizar o dashboard selecionado
  const renderDashboardContent = () => {
    switch (activeDashboard) {
      case "estrategicos":
        return <IndicadoresEstrategicosPlaceholder />
      
      case "previsoes-ia":
        return <PrevisoesIAPlaceholder />
      
      case "people-analytics":
        return <PeopleAnalyticsPlaceholder />
      
      case "modelos-trabalho":
        return <ModelosTrabalhoPlaceholder />
      
      case "funil-performance":
        return <FunilPerformancePlaceholder />
      
      case "war-room":
        return <WarRoomOperacionalPlaceholder />
      
      case "competencias":
        return <AnaliseCompetenciasPlaceholder />
      
      case "voice-screening":
        return <VoiceScreeningDashboard />
      
      case "agent-activity":
        return <AgentActivityDashboard />
      
      default:
        // Retorna mensagem neutra para slugs não reconhecidos (evita expor módulos via fallback)
        return (
          <div className="flex items-center justify-center h-full">
            <Card className="max-w-md mx-auto">
              <CardHeader>
                <CardTitle className="text-center font-sans">Dashboard Não Encontrado</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-center text-gray-600 dark:text-gray-400">
                  O dashboard solicitado não está disponível. 
                  Por favor, selecione uma das opções disponíveis no menu lateral.
                </p>
              </CardContent>
            </Card>
          </div>
        )
    }
  }

  // Sistema de auto-expand com lock
  const shouldExpand = isMenuLocked ? !isMenuCollapsed : isHovering || !isMenuCollapsed

  const handleMouseEnter = () => {
    if (!isMenuLocked) {
      setIsHovering(true)
    }
  }

  const handleMouseLeave = () => {
    if (!isMenuLocked) {
      setIsHovering(false)
    }
  }

  const toggleLock = () => {
    const newLockState = !isMenuLocked
    setIsMenuLocked(newLockState)
    
    if (newLockState) {
      // Travando: expande o menu
      setIsMenuCollapsed(false)
    } else {
      // Destravando: colapsa o menu
      setIsMenuCollapsed(true)
      setIsHovering(false)
    }
  }

  return (
    <div className="flex gap-3 h-full px-3 pt-3 pb-6 bg-gray-50 dark:bg-gray-900 overflow-hidden">
      {/* Menu Lateral de Dashboards - Retrátil com Auto-Expand */}
      <div 
        className={`bg-gray-50 dark:bg-gray-850 border border-gray-200 dark:border-gray-800 rounded-md p-4 space-y-4 shrink-0 transition-all duration-300 ${
          shouldExpand ? 'w-64' : 'w-16'
        }`}
        onMouseEnter={handleMouseEnter}
        onMouseLeave={handleMouseLeave}
      >
          <div>
            {/* Cabeçalho com Toggle de Lock */}
            <div className="flex items-center justify-between mb-4">
              {shouldExpand && (
                <div className="flex-1">
                  <h2 className={`${textStyles.label} uppercase tracking-[0.08em] flex items-center gap-2 mb-1`}>
                    <Activity className="w-3.5 h-3.5 text-gray-600 dark:text-gray-400" />
                    Dashboards
                  </h2>
                  <p className={`${textStyles.description} dark:text-gray-400`}>
                    Selecione um dashboard
                  </p>
                </div>
              )}
              <button
                onClick={toggleLock}
                className="p-1.5 rounded-md hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
                title={isMenuLocked ? "Destravar menu (auto-expand habilitado)" : "Travar menu expandido"}
              >
                {isMenuLocked ? (
                  <Lock className="w-3.5 h-3.5 text-gray-600 dark:text-gray-400" />
                ) : (
                  <Unlock className="w-3.5 h-3.5 text-gray-800 dark:text-gray-200" />
                )}
              </button>
            </div>

            <div className="space-y-2">
              {dashboardMenuItems.map((item) => {
                const Icon = item.icon
                const isActive = activeDashboard === item.id

                return (
                  <button
                    key={item.id}
                    onClick={() => setActiveDashboard(item.id)}
                    title={!shouldExpand ? item.label : undefined}
                    className={`w-full ${!shouldExpand ? 'flex justify-center' : 'text-left'} p-2 rounded-md transition-all ${
                      isActive
                        ? 'bg-gray-100 dark:bg-gray-800 border border-gray-300 dark:border-gray-600'
                        : 'hover:bg-gray-50 dark:hover:bg-gray-800/50 border border-transparent'
                    }`}
                  >
                    {!shouldExpand ? (
                      // Modo colapsado: apenas ícone
                      <div className={`p-1.5 rounded-md ${
                        isActive
                          ? 'bg-white dark:bg-gray-900'
                          : 'bg-gray-100 dark:bg-gray-800'
                      }`}>
                        <Icon 
                          className="w-3.5 h-3.5" 
                          style={{ color: item.color }}
                        />
                      </div>
                    ) : (
                      // Modo expandido: layout completo
                      <div className="flex items-start justify-between gap-2">
                        <div className="flex items-start gap-2 flex-1 min-w-0">
                          <div className={`p-1.5 rounded-md ${
                            isActive
                              ? 'bg-white dark:bg-gray-900'
                              : 'bg-gray-100 dark:bg-gray-800'
                          }`}>
                            <Icon 
                              className="w-3.5 h-3.5" 
                              style={{ color: item.color }}
                            />
                          </div>
                          <div className="flex-1 min-w-0">
                            <h3 className={`${textStyles.label} mb-0.5 ${
                              isActive
                                ? 'text-gray-950 dark:text-gray-50'
                                : ''
                            }`}>
                              {item.label}
                            </h3>
                            <p className={`${textStyles.description} dark:text-gray-400 line-clamp-2`}>
                              {item.description}
                            </p>
                          </div>
                        </div>
                        {item.count !== undefined && (
                          <Badge
                            variant="outline"
                            className="ml-auto text-xs tracking-tight font-semibold uppercase font-open-sans"
                          >
                            {item.count}
                          </Badge>
                        )}
                      </div>
                    )}
                  </button>
                )
              })}
            </div>
          </div>
        </div>

        {/* Conteúdo do Dashboard Selecionado */}
        <div className="flex-1 min-h-0 overflow-y-auto flex flex-col gap-3">
          {showBriefing && (
            <DailyBriefingCard
              onNavigate={onNavigate}
              onActionClick={(action) => {
                if (action === 'view_jobs' || action === 'view_job') onNavigate?.('Vagas')
                if (action === 'provide_feedback' || action === 'view_candidate') onNavigate?.('Funil de Talentos')
              }}
            />
          )}
          {renderDashboardContent()}
        </div>
      </div>
    )
  }

// ============================================================
// NOVOS DASHBOARDS REORGANIZADOS
// ============================================================

// 1. Indicadores Estratégicos
function IndicadoresEstrategicosPlaceholder() {
  return (
    <div className="space-y-3">
      {/* Header */}
      <div>
        <h1 className={`${textStyles.title} dark:text-gray-100 flex items-center gap-2`}>
          <Target className="w-3.5 h-3.5 text-wedo-purple" />
          Indicadores Estratégicos
        </h1>
        <p className={`${textStyles.bodySmall} dark:text-gray-400 mt-1`}>
          KPIs de negócio, performance de recrutadores e retorno sobre investimento
        </p>
      </div>

      {/* KPIs Principais */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-2.5">
        {/* Taxa de Crescimento */}
        <Card className={`${cardStyles.default} dark:bg-gray-950 dark:border-gray-800`}>
          <CardContent className="p-3">
            <div className="flex items-start justify-between mb-2">
              <p className={`${textStyles.bodySmall} dark:text-gray-400`}>Taxa de Crescimento</p>
              <TrendingUp className="w-3.5 h-3.5 text-wedo-purple" />
            </div>
            <div className="text-xl font-inter font-bold text-gray-950 dark:text-gray-50">+28%</div>
            <p className={`${textStyles.bodySmall} text-purple-600 dark:text-purple-400 mt-1`}>vs. trimestre anterior</p>
          </CardContent>
        </Card>

        {/* Eficiência Operacional */}
        <Card className={`${cardStyles.default} dark:bg-gray-950 dark:border-gray-800`}>
          <CardContent className="p-3">
            <div className="flex items-start justify-between mb-2">
              <p className={`${textStyles.bodySmall} dark:text-gray-400`}>Eficiência Operacional</p>
              <Activity className="w-3.5 h-3.5 text-gray-600 dark:text-gray-400" />
            </div>
            <div className="text-xl font-inter font-bold text-gray-950 dark:text-gray-50">87%</div>
 <p className={`${textStyles.bodySmall} text-gray-900 dark:text-gray-300 mt-1`}>+5% este mês</p>
          </CardContent>
        </Card>

        {/* ROI do Processo */}
        <Card className={`${cardStyles.default} dark:bg-gray-950 dark:border-gray-800`}>
          <CardContent className="p-3">
            <div className="flex items-start justify-between mb-2">
              <p className={`${textStyles.bodySmall} dark:text-gray-400`}>ROI do Processo</p>
              <Target className="w-3.5 h-3.5 text-wedo-green" />
            </div>
            <div className="text-xl font-inter font-bold text-gray-950 dark:text-gray-50">340%</div>
            <p className={`${textStyles.bodySmall} text-green-600 dark:text-green-400 mt-1`}>Meta: 250%</p>
          </CardContent>
        </Card>

        {/* Budget Utilizado */}
        <Card className={`${cardStyles.default} dark:bg-gray-950 dark:border-gray-800`}>
          <CardContent className="p-3">
            <div className="flex items-start justify-between mb-2">
              <p className={`${textStyles.bodySmall} dark:text-gray-400`}>Budget Utilizado</p>
              <BarChart3 className="w-3.5 h-3.5 text-wedo-orange" />
            </div>
            <div className="text-xl font-inter font-bold text-gray-950 dark:text-gray-50">67%</div>
            <p className={`${textStyles.bodySmall} text-orange-600 dark:text-orange-400 mt-1`}>R$ 842k / R$ 1.25M</p>
          </CardContent>
        </Card>
      </div>

      {/* Performance de Recrutadores & Time to Fill */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-2.5">
        {/* Performance de Recrutadores */}
        <Card className={`${cardStyles.default} dark:bg-gray-950 dark:border-gray-700`}>
          <CardHeader className="pb-3">
            <CardTitle className={`${textStyles.subtitle} dark:text-gray-100 flex items-center gap-2`}>
              <Users className="w-3.5 h-3.5 text-wedo-green" />
              Performance de Recrutadores
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex items-center justify-between p-3 bg-green-50 dark:bg-green-900/20 rounded-md border border-green-200 dark:border-green-800">
              <div className="flex-1">
                <p className={`${textStyles.subtitle} text-gray-950 dark:text-gray-50`}>Mariana Silva</p>
                <p className={`${textStyles.description} dark:text-gray-400`}>23 contratações • 94% taxa de aprovação</p>
              </div>
              <Badge className={`${badgeStyles.success} dark:bg-green-900/30 dark:text-green-400`}>
                🥇 Top 1
              </Badge>
            </div>

 <div className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 rounded-md border border-gray-300 dark:border-gray-200">
              <div className="flex-1">
                <p className={`${textStyles.subtitle} text-gray-950 dark:text-gray-50`}>Roberto Costa</p>
                <p className={`${textStyles.description} dark:text-gray-400`}>19 contratações • 89% taxa de aprovação</p>
              </div>
 <Badge className={`${badgeStyles.info} dark:bg-gray-800 dark:text-gray-300`}>
                🥈 Top 2
              </Badge>
            </div>

            <div className="flex items-center justify-between p-3 bg-purple-50 dark:bg-purple-900/20 rounded-md border border-purple-200 dark:border-purple-800">
              <div className="flex-1">
                <p className={`${textStyles.subtitle} text-gray-950 dark:text-gray-50`}>Juliana Mendes</p>
                <p className={`${textStyles.description} dark:text-gray-400`}>17 contratações • 91% taxa de aprovação</p>
              </div>
              <Badge className="bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400 text-micro font-medium">
                🥉 Top 3
              </Badge>
            </div>

            <div className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800/50 rounded-md border border-gray-200 dark:border-gray-700">
              <div className="flex-1">
                <p className={`${textStyles.subtitle} text-gray-950 dark:text-gray-50`}>Carlos Almeida</p>
                <p className={`${textStyles.description} dark:text-gray-400`}>15 contratações • 86% taxa de aprovação</p>
              </div>
              <Badge className={badgeStyles.default}>
                Top 4
              </Badge>
            </div>
          </CardContent>
        </Card>

        {/* Time to Fill por Senioridade */}
        <Card className={`${cardStyles.default} dark:bg-gray-950 dark:border-gray-700`}>
          <CardHeader className="pb-3">
            <CardTitle className={`${textStyles.subtitle} dark:text-gray-100 flex items-center gap-2`}>
              <Activity className="w-3.5 h-3.5 text-wedo-orange" />
              Time to Fill por Senioridade
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className={`${textStyles.subtitle} dark:text-gray-300`}>Júnior</span>
                <div className="flex items-center gap-2">
                  <span className="text-sm font-inter font-bold text-gray-950 dark:text-gray-50">12 dias</span>
                  <Badge className={`${badgeStyles.success} dark:bg-green-900/30 dark:text-green-400`}>
                    -2d
                  </Badge>
                </div>
              </div>
              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                <div className="h-2 rounded-full bg-wedo-green-bright" style={{ width: '40%' }}></div>
              </div>
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className={`${textStyles.subtitle} dark:text-gray-300`}>Pleno</span>
                <div className="flex items-center gap-2">
                  <span className="text-sm font-inter font-bold text-gray-950 dark:text-gray-50">18 dias</span>
 <Badge className={`${badgeStyles.info} dark:bg-gray-800 dark:text-gray-300`}>
                    -3d
                  </Badge>
                </div>
              </div>
              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                <div className="h-2 rounded-full bg-gray-900" style={{ width: '60%' }}></div>
              </div>
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className={`${textStyles.subtitle} dark:text-gray-300`}>Sênior</span>
                <div className="flex items-center gap-2">
                  <span className="text-sm font-inter font-bold text-gray-950 dark:text-gray-50">27 dias</span>
                  <Badge className={`${badgeStyles.warning} dark:bg-orange-900/30 dark:text-orange-400`}>
                    -1d
                  </Badge>
                </div>
              </div>
              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                <div className="h-2 rounded-full bg-wedo-orange" style={{ width: '90%' }}></div>
              </div>
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className={`${textStyles.subtitle} dark:text-gray-300`}>Especialista/C-Level</span>
                <div className="flex items-center gap-2">
                  <span className="text-sm font-inter font-bold text-gray-950 dark:text-gray-50">45 dias</span>
                  <Badge className="bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400 text-micro font-medium">
                    +2d
                  </Badge>
                </div>
              </div>
              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                <div className="h-2 rounded-full bg-wedo-purple" style={{ width: '100%' }}></div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Skills Gap Analysis */}
      <Card className={`${cardStyles.default} dark:bg-gray-950 dark:border-gray-700`}>
        <CardHeader className="pb-3">
          <CardTitle className={`${textStyles.subtitle} dark:text-gray-100 flex items-center gap-2`}>
            <AlertTriangle className="w-3.5 h-3.5 text-wedo-magenta" />
            Skills Gap Analysis - Competências Mais Difíceis de Preencher
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <div className="p-4 bg-red-50 dark:bg-red-900/20 rounded-md border-l-4 border-red-500">
              <div className="flex items-start justify-between mb-2">
                <p className={`${textStyles.subtitle} text-gray-950 dark:text-gray-50`}>Machine Learning Engineer</p>
                <Badge className={`${badgeStyles.error} dark:bg-red-900/30 dark:text-red-400`}>
                  Crítico
                </Badge>
              </div>
              <div className="space-y-1">
                <div className={`flex items-center justify-between ${textStyles.bodySmall}`}>
                  <span className="font-open-sans text-gray-600 dark:text-gray-400">Vagas abertas</span>
                  <span className="font-inter font-bold text-gray-950 dark:text-gray-50">14</span>
                </div>
                <div className={`flex items-center justify-between ${textStyles.bodySmall}`}>
                  <span className="font-open-sans text-gray-600 dark:text-gray-400">Tempo médio</span>
                  <span className="font-inter font-bold text-red-600 dark:text-red-400">62 dias</span>
                </div>
                <div className={`flex items-center justify-between ${textStyles.bodySmall}`}>
                  <span className="font-open-sans text-gray-600 dark:text-gray-400">Taxa sucesso</span>
                  <span className="font-inter font-bold text-gray-950 dark:text-gray-50">28%</span>
                </div>
              </div>
            </div>

            <div className="p-4 bg-orange-50 dark:bg-orange-900/20 rounded-md border-l-4 border-orange-500">
              <div className="flex items-start justify-between mb-2">
                <p className="text-sm font-open-sans font-semibold text-gray-950 dark:text-gray-50">DevOps Architect</p>
                <Badge className="bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400 text-xs font-inter">
                  Alto
                </Badge>
              </div>
              <div className="space-y-1">
                <div className={`flex items-center justify-between ${textStyles.bodySmall}`}>
                  <span className="font-open-sans text-gray-600 dark:text-gray-400">Vagas abertas</span>
                  <span className="font-inter font-bold text-gray-950 dark:text-gray-50">9</span>
                </div>
                <div className={`flex items-center justify-between ${textStyles.bodySmall}`}>
                  <span className="font-open-sans text-gray-600 dark:text-gray-400">Tempo médio</span>
                  <span className="font-inter font-bold text-orange-600 dark:text-orange-400">48 dias</span>
                </div>
                <div className={`flex items-center justify-between ${textStyles.bodySmall}`}>
                  <span className="font-open-sans text-gray-600 dark:text-gray-400">Taxa sucesso</span>
                  <span className="font-inter font-bold text-gray-950 dark:text-gray-50">42%</span>
                </div>
              </div>
            </div>

            <div className="p-4 bg-yellow-50 dark:bg-yellow-900/20 rounded-md border-l-4 border-yellow-500">
              <div className="flex items-start justify-between mb-2">
                <p className="text-sm font-open-sans font-semibold text-gray-950 dark:text-gray-50">Security Specialist</p>
                <Badge className="bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400 text-xs font-inter">
                  Médio
                </Badge>
              </div>
              <div className="space-y-1">
                <div className={`flex items-center justify-between ${textStyles.bodySmall}`}>
                  <span className="font-open-sans text-gray-600 dark:text-gray-400">Vagas abertas</span>
                  <span className="font-inter font-bold text-gray-950 dark:text-gray-50">7</span>
                </div>
                <div className={`flex items-center justify-between ${textStyles.bodySmall}`}>
                  <span className="font-open-sans text-gray-600 dark:text-gray-400">Tempo médio</span>
                  <span className="font-inter font-bold text-yellow-600 dark:text-yellow-400">35 dias</span>
                </div>
                <div className={`flex items-center justify-between ${textStyles.bodySmall}`}>
                  <span className="font-open-sans text-gray-600 dark:text-gray-400">Taxa sucesso</span>
                  <span className="font-inter font-bold text-gray-950 dark:text-gray-50">58%</span>
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Budget vs Performance */}
      <Card className={`${cardStyles.default} dark:bg-gray-950 dark:border-gray-700`}>
        <CardHeader className="pb-3">
          <CardTitle className={`${textStyles.subtitle} dark:text-gray-100 flex items-center gap-2`}>
            <BarChart3 className="w-3.5 h-3.5 text-wedo-purple" />
            Budget vs Performance por Departamento
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <div>
                  <span className="text-sm font-open-sans font-medium text-gray-800 dark:text-gray-200">Tecnologia</span>
                  <p className={`${textStyles.description} dark:text-gray-400`}>R$ 420k investidos • 47 contratações</p>
                </div>
                <Badge className={`${badgeStyles.success} dark:bg-green-900/30 dark:text-green-400`}>
                  112% ROI
                </Badge>
              </div>
              <div className="flex w-full h-2 rounded-full overflow-hidden bg-gray-200 dark:bg-gray-700">
                <div className="bg-wedo-green-bright" style={{ width: '85%' }} title="Performance"></div>
                <div className="bg-wedo-orange" style={{ width: '15%' }} title="Orçamento não utilizado"></div>
              </div>
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <div>
                  <span className="text-sm font-open-sans font-medium text-gray-800 dark:text-gray-200">Vendas</span>
                  <p className={`${textStyles.description} dark:text-gray-400`}>R$ 186k investidos • 28 contratações</p>
                </div>
 <Badge className={`${badgeStyles.info} dark:bg-gray-800 dark:text-gray-300`}>
                  94% ROI
                </Badge>
              </div>
              <div className="flex w-full h-2 rounded-full overflow-hidden bg-gray-200 dark:bg-gray-700">
                <div className="bg-gray-900" style={{ width: '72%' }} title="Performance"></div>
                <div className="bg-wedo-orange" style={{ width: '28%' }} title="Orçamento não utilizado"></div>
              </div>
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <div>
                  <span className="text-sm font-open-sans font-medium text-gray-800 dark:text-gray-200">Marketing</span>
                  <p className={`${textStyles.description} dark:text-gray-400`}>R$ 124k investidos • 19 contratações</p>
                </div>
                <Badge className="bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400 text-micro font-medium">
                  87% ROI
                </Badge>
              </div>
              <div className="flex w-full h-2 rounded-full overflow-hidden bg-gray-200 dark:bg-gray-700">
                <div className="bg-wedo-purple" style={{ width: '68%' }} title="Performance"></div>
                <div className="bg-wedo-orange" style={{ width: '32%' }} title="Orçamento não utilizado"></div>
              </div>
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <div>
                  <span className="text-sm font-open-sans font-medium text-gray-800 dark:text-gray-200">Operações</span>
                  <p className={`${textStyles.description} dark:text-gray-400`}>R$ 112k investidos • 15 contratações</p>
                </div>
                <Badge className={`${badgeStyles.warning} dark:bg-orange-900/30 dark:text-orange-400`}>
                  76% ROI
                </Badge>
              </div>
              <div className="flex w-full h-2 rounded-full overflow-hidden bg-gray-200 dark:bg-gray-700">
                <div className="bg-wedo-orange" style={{ width: '58%' }} title="Performance"></div>
                <div className="bg-wedo-purple" style={{ width: '42%' }} title="Orçamento não utilizado"></div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Insights Estratégicos */}
      <Card className={`${cardStyles.default} dark:bg-gray-900 dark:border-gray-800`}>
        <CardHeader className="px-4 py-3">
          <CardTitle className={`${textStyles.title} dark:text-gray-100 flex items-center gap-2`}>
            <Target className="w-3.5 h-3.5 text-wedo-purple" />
            Recomendações Estratégicas
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex items-start gap-3">
            <CheckCircle className="w-3.5 h-3.5 mt-0.5 flex-shrink-0 text-wedo-green-bright" />
            <p className="text-sm font-open-sans text-gray-800 dark:text-gray-200">
              <strong>Tech lidera ROI:</strong> Departamento de Tecnologia com 112% ROI - modelo de referência para outros setores.
            </p>
          </div>
          <div className="flex items-start gap-3">
            <AlertTriangle className="w-3.5 h-3.5 mt-0.5 flex-shrink-0 text-wedo-magenta" />
            <p className="text-sm font-open-sans text-gray-800 dark:text-gray-200">
              <strong>Skills gap crítico:</strong> ML Engineer leva 62 dias em média. Considere parcerias estratégicas com universidades.
            </p>
          </div>
          <div className="flex items-start gap-3">
            <TrendingUp className="w-3.5 h-3.5 mt-0.5 flex-shrink-0 text-wedo-purple" />
            <p className="text-sm font-open-sans text-gray-800 dark:text-gray-200">
              <strong>Crescimento acelerado:</strong> +28% vs. trimestre anterior. Pipeline atual suporta expansão planejada.
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

// 2. Previsões & IA
function PrevisoesIAPlaceholder() {
  return (
    <div className="space-y-3">
      {/* Header */}
      <div>
        <h1 className="text-sm leading-tight font-semibold font-['Open_Sans',sans-serif] text-gray-950 dark:text-gray-50 flex items-center gap-2">
          <Brain className="w-3.5 h-3.5 text-wedo-cyan" />
          Previsões & Inteligência Artificial
        </h1>
        <p className="text-gray-600 dark:text-gray-400 mt-1 font-open-sans text-xs">
          Machine Learning, previsões de demanda, alertas inteligentes e scoring preditivo
        </p>
      </div>

      {/* ML Predictions - Próximos 30 dias */}
      <Card className={`${cardStyles.default} dark:bg-gray-950 dark:border-gray-700`}>
        <CardHeader className="px-4 py-3">
          <CardTitle className={`${textStyles.title} dark:text-gray-100 flex items-center gap-2`}>
            <Brain className="w-3.5 h-3.5 text-wedo-cyan" />
            Previsões ML - Próximos 30 Dias
          </CardTitle>
        </CardHeader>
        <CardContent className="pt-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
            {/* Applications Prediction */}
 <div className="p-4 bg-white dark:bg-gray-800 rounded-md border border-gray-300 dark:border-gray-200">
              <p className={`${textStyles.description} dark:text-gray-400 mb-1`}>Candidaturas Esperadas</p>
              <div className="flex items-baseline gap-2">
                <span className="text-2xl font-inter font-bold text-gray-950 dark:text-gray-50">2.847</span>
                <Badge className={`${badgeStyles.success} dark:bg-green-900/30 dark:text-green-400`}>
                  +12%
                </Badge>
              </div>
              <p className={`${textStyles.description} mt-1`}>vs. média anterior</p>
            </div>

            {/* Hires Prediction */}
            <div className="p-4 bg-white dark:bg-gray-800 rounded-md border border-purple-200 dark:border-purple-800">
              <p className={`${textStyles.description} dark:text-gray-400 mb-1`}>Contratações Previstas</p>
              <div className="flex items-baseline gap-2">
                <span className="text-2xl font-inter font-bold text-gray-950 dark:text-gray-50">127</span>
 <Badge className="bg-gray-100 text-gray-900 dark:text-gray-300 text-xs font-inter">
                  +8%
                </Badge>
              </div>
              <p className={`${textStyles.description} mt-1`}>vs. média anterior</p>
            </div>

            {/* Time to Fill Prediction */}
            <div className="p-4 bg-white dark:bg-gray-800 rounded-md border border-orange-200 dark:border-orange-800">
              <p className={`${textStyles.description} dark:text-gray-400 mb-1`}>Time-to-Fill Médio</p>
              <div className="flex items-baseline gap-2">
                <span className="text-2xl font-inter font-bold text-gray-950 dark:text-gray-50">18</span>
                <span className="text-sm font-open-sans text-gray-800 dark:text-gray-200">dias</span>
              </div>
              <p className={`${textStyles.bodySmall} text-green-600 dark:text-green-400 mt-1`}>-3 dias vs. anterior</p>
            </div>

            {/* Cost Prediction */}
            <div className="p-4 bg-white dark:bg-gray-800 rounded-md border border-green-200 dark:border-green-800">
              <p className={`${textStyles.description} dark:text-gray-400 mb-1`}>Custo por Contratação</p>
              <div className="flex items-baseline gap-2">
                <span className="text-2xl font-inter font-bold text-gray-950 dark:text-gray-50">R$ 3.2k</span>
              </div>
              <p className={`${textStyles.bodySmall} text-green-600 dark:text-green-400 mt-1`}>-R$ 420 vs. anterior</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Scoring Inteligente & Alertas */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-2.5">
        {/* Scoring Inteligente - Top Performers */}
        <Card className={`${cardStyles.default} dark:bg-gray-950 dark:border-gray-700`}>
          <CardHeader className="pb-3">
            <CardTitle className={`${textStyles.subtitle} dark:text-gray-100 flex items-center gap-2`}>
              <Award className="w-3.5 h-3.5 text-wedo-purple" />
              Top Candidatos - Score LIA
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex items-center justify-between p-3 bg-purple-50 dark:bg-purple-900/20 rounded-md border border-purple-200 dark:border-purple-800">
              <div>
                <p className="font-open-sans font-semibold text-gray-950 dark:text-gray-50 text-sm">Ana Silva</p>
                <p className={`${textStyles.description} dark:text-gray-400`}>Senior Developer • React/Node</p>
              </div>
              <Badge className="bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400 font-inter font-bold">
                98/100
              </Badge>
            </div>

            <div className="flex items-center justify-between p-3 bg-purple-50 dark:bg-purple-900/20 rounded-md border border-purple-200 dark:border-purple-800">
              <div>
                <p className="font-open-sans font-semibold text-gray-950 dark:text-gray-50 text-sm">Carlos Mendes</p>
                <p className={`${textStyles.description} dark:text-gray-400`}>Product Manager • SaaS</p>
              </div>
              <Badge className="bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400 font-inter font-bold">
                96/100
              </Badge>
            </div>

 <div className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 rounded-md border border-gray-300 dark:border-gray-200">
              <div>
                <p className="font-open-sans font-semibold text-gray-950 dark:text-gray-50 text-sm">Beatriz Costa</p>
                <p className={`${textStyles.description} dark:text-gray-400`}>UX Designer • Figma Expert</p>
              </div>
 <Badge className="bg-gray-100 text-gray-900 dark:text-gray-300 font-inter font-bold">
                94/100
              </Badge>
            </div>

 <div className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 rounded-md border border-gray-300 dark:border-gray-200">
              <div>
                <p className="font-open-sans font-semibold text-gray-950 dark:text-gray-50 text-sm">Rafael Santos</p>
                <p className={`${textStyles.description} dark:text-gray-400`}>Data Scientist • Python/ML</p>
              </div>
 <Badge className="bg-gray-100 text-gray-900 dark:text-gray-300 font-inter font-bold">
                93/100
              </Badge>
            </div>
          </CardContent>
        </Card>

        {/* Alertas em Tempo Real */}
        <Card className={`${cardStyles.default} dark:bg-gray-950 dark:border-gray-700`}>
          <CardHeader className="pb-3">
            <CardTitle className={`${textStyles.subtitle} dark:text-gray-100 flex items-center gap-2`}>
              <AlertTriangle className="w-3.5 h-3.5 text-wedo-magenta" />
              Alertas Inteligentes
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex items-start gap-3 p-3 bg-red-50 dark:bg-red-900/20 rounded-md border-l-4 border-red-500">
              <AlertTriangle className="w-3.5 h-3.5 mt-0.5 flex-shrink-0 text-red-600" />
              <div>
                <p className="text-sm font-open-sans font-semibold text-gray-950 dark:text-gray-50">Vaga #2847 em risco</p>
                <p className={`${textStyles.bodySmall} dark:text-gray-400 mt-1`}>
                  45 dias sem candidatos qualificados. LIA sugere ajustar requisitos.
                </p>
              </div>
            </div>

            <div className="flex items-start gap-3 p-3 bg-orange-50 dark:bg-orange-900/20 rounded-md border-l-4 border-orange-500">
              <AlertTriangle className="w-3.5 h-3.5 mt-0.5 flex-shrink-0 text-orange-600" />
              <div>
                <p className="text-sm font-open-sans font-semibold text-gray-950 dark:text-gray-50">Pipeline lento - Tech Lead</p>
                <p className={`${textStyles.bodySmall} dark:text-gray-400 mt-1`}>
                  Tempo médio de resposta: 8 dias. Meta: 3 dias.
                </p>
              </div>
            </div>

            <div className="flex items-start gap-3 p-3 bg-green-50 dark:bg-green-900/20 rounded-md border-l-4 border-green-500">
              <CheckCircle className="w-3.5 h-3.5 mt-0.5 flex-shrink-0 text-green-600" />
              <div>
                <p className="text-sm font-open-sans font-semibold text-gray-950 dark:text-gray-50">Candidato ideal identificado</p>
                <p className={`${textStyles.bodySmall} dark:text-gray-400 mt-1`}>
                  Ana Silva (98/100) corresponde perfeitamente à vaga #2941.
                </p>
              </div>
            </div>

 <div className="flex items-start gap-3 p-3 bg-gray-50 dark:bg-gray-800 rounded-md border-l-4 border-gray-900 dark:border-gray-50">
              <Brain className="w-3.5 h-3.5 mt-0.5 flex-shrink-0 text-wedo-cyan" />
              <div>
                <p className="text-sm font-open-sans font-semibold text-gray-950 dark:text-gray-50">Recomendação automática</p>
                <p className={`${textStyles.bodySmall} dark:text-gray-400 mt-1`}>
                  LIA agendou 3 triagens para amanhã baseado em disponibilidade.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Skills em Alta & Demanda Prevista */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-2.5">
        {/* Skills em Alta */}
        <Card className={`${cardStyles.default} dark:bg-gray-950 dark:border-gray-700`}>
          <CardHeader className="pb-3">
            <CardTitle className={`${textStyles.subtitle} dark:text-gray-100 flex items-center gap-2`}>
              <TrendingUp className="w-3.5 h-3.5 text-gray-600 dark:text-gray-400" />
              Skills Mais Demandadas
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm font-open-sans font-medium text-gray-800 dark:text-gray-200">React.js</span>
                <div className="flex items-center gap-2">
                  <span className="text-xs tracking-tight font-inter text-gray-800 dark:text-gray-200">287 vagas</span>
                  <Badge className={`${badgeStyles.success} dark:bg-green-900/30 dark:text-green-400`}>
                    +18%
                  </Badge>
                </div>
              </div>
              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                <div className="h-2 rounded-full bg-gray-900" style={{ width: '92%' }}></div>
              </div>
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm font-open-sans font-medium text-gray-800 dark:text-gray-200">Python</span>
                <div className="flex items-center gap-2">
                  <span className="text-xs tracking-tight font-inter text-gray-800 dark:text-gray-200">243 vagas</span>
                  <Badge className={`${badgeStyles.success} dark:bg-green-900/30 dark:text-green-400`}>
                    +22%
                  </Badge>
                </div>
              </div>
              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                <div className="h-2 rounded-full bg-wedo-green-bright" style={{ width: '85%' }}></div>
              </div>
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm font-open-sans font-medium text-gray-800 dark:text-gray-200">Node.js</span>
                <div className="flex items-center gap-2">
                  <span className="text-xs tracking-tight font-inter text-gray-800 dark:text-gray-200">218 vagas</span>
 <Badge className="bg-gray-100 text-gray-900 dark:text-gray-300 text-xs font-inter">
                    +15%
                  </Badge>
                </div>
              </div>
              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                <div className="h-2 rounded-full bg-gray-900" style={{ width: '78%' }}></div>
              </div>
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm font-open-sans font-medium text-gray-800 dark:text-gray-200">AWS</span>
                <div className="flex items-center gap-2">
                  <span className="text-xs tracking-tight font-inter text-gray-800 dark:text-gray-200">194 vagas</span>
                  <Badge className="bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400 text-xs font-inter">
                    +28%
                  </Badge>
                </div>
              </div>
              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                <div className="h-2 rounded-full bg-wedo-purple" style={{ width: '71%' }}></div>
              </div>
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm font-open-sans font-medium text-gray-800 dark:text-gray-200">Machine Learning</span>
                <div className="flex items-center gap-2">
                  <span className="text-xs tracking-tight font-inter text-gray-800 dark:text-gray-200">156 vagas</span>
                  <Badge className="bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400 text-xs font-inter">
                    +34%
                  </Badge>
                </div>
              </div>
              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                <div className="h-2 rounded-full bg-wedo-purple" style={{ width: '62%' }}></div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Demanda por Área - Previsão */}
        <Card className={`${cardStyles.default} dark:bg-gray-950 dark:border-gray-700`}>
          <CardHeader className="pb-3">
            <CardTitle className={`${textStyles.subtitle} dark:text-gray-100 flex items-center gap-2`}>
              <BarChart3 className="w-3.5 h-3.5 text-wedo-purple" />
              Previsão de Demanda por Área
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="p-3 bg-gray-50 dark:bg-gray-800 rounded-md">
              <div className="flex items-center justify-between mb-2">
                <p className="text-sm font-open-sans font-semibold text-gray-950 dark:text-gray-50">Tecnologia</p>
                <Badge className="bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400 text-micro font-medium">
                  +42 vagas
                </Badge>
              </div>
              <p className={`${textStyles.bodySmall} dark:text-gray-400`}>
                Expansão prevista no Q1 2025. LIA recomenda pipeline proativo.
              </p>
            </div>

            <div className="p-3 bg-gray-50 dark:bg-gray-800 rounded-md">
              <div className="flex items-center justify-between mb-2">
                <p className="text-sm font-open-sans font-semibold text-gray-950 dark:text-gray-50">Vendas</p>
 <Badge className={`${badgeStyles.info} dark:bg-gray-800 dark:text-gray-300`}>
                  +28 vagas
                </Badge>
              </div>
              <p className={`${textStyles.bodySmall} dark:text-gray-400`}>
                Crescimento sustentado. Pipeline atual é suficiente.
              </p>
            </div>

            <div className="p-3 bg-gray-50 dark:bg-gray-800 rounded-md">
              <div className="flex items-center justify-between mb-2">
                <p className="text-sm font-open-sans font-semibold text-gray-950 dark:text-gray-50">Marketing</p>
                <Badge className={`${badgeStyles.success} dark:bg-green-900/30 dark:text-green-400`}>
                  +15 vagas
                </Badge>
              </div>
              <p className={`${textStyles.bodySmall} dark:text-gray-400`}>
                Demanda estável. Foco em perfis sênior.
              </p>
            </div>

            <div className="p-3 bg-gray-50 dark:bg-gray-800 rounded-md">
              <div className="flex items-center justify-between mb-2">
                <p className="text-sm font-open-sans font-semibold text-gray-950 dark:text-gray-50">Operações</p>
                <Badge className={`${badgeStyles.warning} dark:bg-orange-900/30 dark:text-orange-400`}>
                  +8 vagas
                </Badge>
              </div>
              <p className={`${textStyles.bodySmall} dark:text-gray-400`}>
                Crescimento moderado. Priorizar retenção.
              </p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Insights da LIA */}
      <Card className={`${cardStyles.default} dark:bg-gray-900 dark:border-gray-800`}>
        <CardHeader className="px-4 py-3">
          <CardTitle className={`${textStyles.title} dark:text-gray-100 flex items-center gap-2`}>
            <Brain className="w-3.5 h-3.5 text-wedo-cyan" />
            Recomendações Estratégicas da LIA
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex items-start gap-3">
            <CheckCircle className="w-3.5 h-3.5 mt-0.5 flex-shrink-0 text-wedo-green-bright" />
            <p className="text-sm font-open-sans text-gray-800 dark:text-gray-200">
              <strong>Antecipação de demanda:</strong> Tecnologia terá pico em 30 dias. Inicie sourcing proativo para React e AWS.
            </p>
          </div>
          <div className="flex items-start gap-3">
            <TrendingUp className="w-3.5 h-3.5 mt-0.5 flex-shrink-0 text-wedo-purple" />
            <p className="text-sm font-open-sans text-gray-800 dark:text-gray-200">
              <strong>Machine Learning em alta:</strong> Demanda cresceu 34% este mês. Considere parcerias com bootcamps especializados.
            </p>
          </div>
          <div className="flex items-start gap-3">
            <Activity className="w-3.5 h-3.5 mt-0.5 flex-shrink-0 text-gray-700" />
            <p className="text-sm font-open-sans text-gray-800 dark:text-gray-200">
              <strong>Otimização de custos:</strong> Pipeline automatizado reduziu custo por contratação em 12% este mês.
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

// 3. People Analytics (Big Five + D&I + NPS)
function PeopleAnalyticsPlaceholder() {
  const [activeSubDashboard, setActiveSubDashboard] = useState<'bigfive' | 'diversidade' | 'nps'>('bigfive')

  return (
    <div className="space-y-3">
      {/* Header com Navegação Interna */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className={`${textStyles.title} dark:text-gray-100 flex items-center gap-2`}>
            <Users className="w-3.5 h-3.5 text-wedo-green" />
            People Analytics
          </h1>
          <p className={`${textStyles.bodySmall} dark:text-gray-400 mt-1`}>
            Big Five, Diversidade & Inclusão, NPS e Satisfação de candidatos
          </p>
        </div>

        {/* Tabs de Navegação */}
        <div className="flex gap-2">
          <Button
            variant={activeSubDashboard === 'bigfive' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setActiveSubDashboard('bigfive')}
            className="text-xs h-7 px-3 font-open-sans"
          >
            <Brain className="w-3 h-3 mr-1.5 text-wedo-cyan" />
            Big Five
          </Button>
          <Button
            variant={activeSubDashboard === 'diversidade' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setActiveSubDashboard('diversidade')}
            className="text-xs h-7 px-3 font-open-sans"
          >
            <Heart className="w-3 h-3 mr-1.5" />
            Diversidade
          </Button>
          <Button
            variant={activeSubDashboard === 'nps' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setActiveSubDashboard('nps')}
            className="text-xs h-7 px-3 font-open-sans"
          >
            <Award className="w-3 h-3 mr-1.5" />
            NPS
          </Button>
        </div>
      </div>

      {/* Conteúdo do Sub-Dashboard */}
      <div className="mt-3">
        {activeSubDashboard === 'bigfive' && <BigFiveAnalyticsDashboard />}
        {activeSubDashboard === 'diversidade' && <DiversidadeInclusaoDashboard />}
        {activeSubDashboard === 'nps' && <NPSDashboard />}
      </div>
    </div>
  )
}

// 4. Modelos de Trabalho
function ModelosTrabalhoPlaceholder() {
  return (
    <div className="space-y-3">
      {/* Header */}
      <div>
        <h1 className={`${textStyles.title} dark:text-gray-100 flex items-center gap-2`}>
          <PieChart className="w-3.5 h-3.5 text-wedo-orange" />
          Modelos de Trabalho
        </h1>
        <p className={`${textStyles.bodySmall} dark:text-gray-400 mt-1`}>
          Distribuição entre Remoto, Híbrido e Presencial - análises regionais e por departamento
        </p>
      </div>

      {/* Distribuição Geral + Satisfação */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-3">
        {/* Distribuição Geral */}
        <Card className="border-gray-200 dark:border-gray-700 lg:col-span-2">
          <CardHeader className="pb-3">
            <CardTitle className="text-base font-sans font-open-sans font-semibold text-gray-950 dark:text-gray-50">
              Distribuição Geral de Modelos de Trabalho
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Remoto */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-gray-900"></div>
                  <span className="text-sm font-open-sans text-gray-800 dark:text-gray-200">Remoto</span>
                </div>
                <span className="text-sm font-inter font-bold text-gray-950 dark:text-gray-50">42%</span>
              </div>
              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3">
                <div className="h-3 rounded-full bg-gray-900" style={{ width: '42%' }}></div>
              </div>
            </div>

            {/* Híbrido */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-wedo-green-bright"></div>
                  <span className="text-sm font-open-sans text-gray-800 dark:text-gray-200">Híbrido</span>
                </div>
                <span className="text-sm font-inter font-bold text-gray-950 dark:text-gray-50">35%</span>
              </div>
              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3">
                <div className="h-3 rounded-full bg-wedo-green-bright" style={{ width: '35%' }}></div>
              </div>
            </div>

            {/* Presencial */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-wedo-orange"></div>
                  <span className="text-sm font-open-sans text-gray-800 dark:text-gray-200">Presencial</span>
                </div>
                <span className="text-sm font-inter font-bold text-gray-950 dark:text-gray-50">23%</span>
              </div>
              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3">
                <div className="h-3 rounded-full bg-wedo-orange" style={{ width: '23%' }}></div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Satisfação Geral */}
        <Card className={`${cardStyles.default} dark:bg-gray-950 dark:border-gray-700`}>
          <CardHeader className="pb-3">
            <CardTitle className="text-base font-sans font-open-sans font-semibold text-gray-950 dark:text-gray-50">
              Satisfação Geral
            </CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col items-center justify-center py-6">
            <div className="text-2xl font-inter font-bold text-gray-950 dark:text-gray-50 mb-2">
              8.4<span className="text-sm text-gray-800 dark:text-gray-200">/10</span>
            </div>
            <p className="text-sm font-open-sans text-gray-600 dark:text-gray-400 text-center mb-4">
              Média de satisfação com modelo de trabalho
            </p>
            <Badge className="bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400 font-open-sans">
              <CheckCircle className="w-3 h-3 mr-1" />
              Acima da meta (8.0)
            </Badge>
          </CardContent>
        </Card>
      </div>

      {/* Análise Regional */}
      <Card className={`${cardStyles.default} dark:bg-gray-950 dark:border-gray-700`}>
        <CardHeader className="pb-3">
          <CardTitle className={`${textStyles.subtitle} dark:text-gray-100 flex items-center gap-2`}>
            <MapPin className="w-3.5 h-3.5 text-gray-800 dark:text-gray-200" />
            Distribuição por Região
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            {/* São Paulo */}
            <div className="space-y-3 p-4 bg-gray-50 dark:bg-gray-800/50 rounded-md">
              <div className="flex items-center justify-between">
                <h4 className="font-open-sans font-semibold text-gray-950 dark:text-gray-50">São Paulo</h4>
                <Badge variant="outline" className="text-xs tracking-tight font-inter">523 vagas</Badge>
              </div>
              <div className="space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <span className="font-open-sans text-gray-600 dark:text-gray-400">Remoto</span>
                  <span className="font-inter font-bold text-gray-950 dark:text-gray-50">48%</span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="font-open-sans text-gray-600 dark:text-gray-400">Híbrido</span>
                  <span className="font-inter font-bold text-gray-950 dark:text-gray-50">35%</span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="font-open-sans text-gray-600 dark:text-gray-400">Presencial</span>
                  <span className="font-inter font-bold text-gray-950 dark:text-gray-50">17%</span>
                </div>
              </div>
            </div>

            {/* Rio de Janeiro */}
            <div className="space-y-3 p-4 bg-gray-50 dark:bg-gray-800/50 rounded-md">
              <div className="flex items-center justify-between">
                <h4 className="font-open-sans font-semibold text-gray-950 dark:text-gray-50">Rio de Janeiro</h4>
                <Badge variant="outline" className="text-xs tracking-tight font-inter">287 vagas</Badge>
              </div>
              <div className="space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <span className="font-open-sans text-gray-600 dark:text-gray-400">Remoto</span>
                  <span className="font-inter font-bold text-gray-950 dark:text-gray-50">38%</span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="font-open-sans text-gray-600 dark:text-gray-400">Híbrido</span>
                  <span className="font-inter font-bold text-gray-950 dark:text-gray-50">42%</span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="font-open-sans text-gray-600 dark:text-gray-400">Presencial</span>
                  <span className="font-inter font-bold text-gray-950 dark:text-gray-50">20%</span>
                </div>
              </div>
            </div>

            {/* Minas Gerais */}
            <div className="space-y-3 p-4 bg-gray-50 dark:bg-gray-800/50 rounded-md">
              <div className="flex items-center justify-between">
                <h4 className="font-open-sans font-semibold text-gray-950 dark:text-gray-50">Minas Gerais</h4>
                <Badge variant="outline" className="text-xs tracking-tight font-inter">194 vagas</Badge>
              </div>
              <div className="space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <span className="font-open-sans text-gray-600 dark:text-gray-400">Remoto</span>
                  <span className="font-inter font-bold text-gray-950 dark:text-gray-50">35%</span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="font-open-sans text-gray-600 dark:text-gray-400">Híbrido</span>
                  <span className="font-inter font-bold text-gray-950 dark:text-gray-50">28%</span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="font-open-sans text-gray-600 dark:text-gray-400">Presencial</span>
                  <span className="font-inter font-bold text-gray-950 dark:text-gray-50">37%</span>
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Análise por Departamento */}
      <Card className={`${cardStyles.default} dark:bg-gray-950 dark:border-gray-700`}>
        <CardHeader className="pb-3">
          <CardTitle className={`${textStyles.subtitle} dark:text-gray-100 flex items-center gap-2`}>
            <Building className="w-3.5 h-3.5 text-gray-800 dark:text-gray-200" />
            Distribuição por Departamento
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {/* Tecnologia */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm font-open-sans font-medium text-gray-800 dark:text-gray-200">Tecnologia</span>
                <span className="text-xs tracking-tight font-inter text-gray-800 dark:text-gray-200">78% Remoto • 18% Híbrido • 4% Presencial</span>
              </div>
              <div className="flex w-full h-2 rounded-full overflow-hidden bg-gray-200 dark:bg-gray-700">
                <div className="bg-gray-900" style={{ width: '78%' }}></div>
                <div className="bg-wedo-green-bright" style={{ width: '18%' }}></div>
                <div className="bg-wedo-orange" style={{ width: '4%' }}></div>
              </div>
            </div>

            {/* Vendas */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm font-open-sans font-medium text-gray-800 dark:text-gray-200">Vendas</span>
                <span className="text-xs tracking-tight font-inter text-gray-800 dark:text-gray-200">15% Remoto • 62% Híbrido • 23% Presencial</span>
              </div>
              <div className="flex w-full h-2 rounded-full overflow-hidden bg-gray-200 dark:bg-gray-700">
                <div className="bg-gray-900" style={{ width: '15%' }}></div>
                <div className="bg-wedo-green-bright" style={{ width: '62%' }}></div>
                <div className="bg-wedo-orange" style={{ width: '23%' }}></div>
              </div>
            </div>

            {/* Financeiro */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm font-open-sans font-medium text-gray-800 dark:text-gray-200">Financeiro</span>
                <span className="text-xs tracking-tight font-inter text-gray-800 dark:text-gray-200">32% Remoto • 51% Híbrido • 17% Presencial</span>
              </div>
              <div className="flex w-full h-2 rounded-full overflow-hidden bg-gray-200 dark:bg-gray-700">
                <div className="bg-gray-900" style={{ width: '32%' }}></div>
                <div className="bg-wedo-green-bright" style={{ width: '51%' }}></div>
                <div className="bg-wedo-orange" style={{ width: '17%' }}></div>
              </div>
            </div>

            {/* Operações */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm font-open-sans font-medium text-gray-800 dark:text-gray-200">Operações</span>
                <span className="text-xs tracking-tight font-inter text-gray-800 dark:text-gray-200">8% Remoto • 25% Híbrido • 67% Presencial</span>
              </div>
              <div className="flex w-full h-2 rounded-full overflow-hidden bg-gray-200 dark:bg-gray-700">
                <div className="bg-gray-900" style={{ width: '8%' }}></div>
                <div className="bg-wedo-green-bright" style={{ width: '25%' }}></div>
                <div className="bg-wedo-orange" style={{ width: '67%' }}></div>
              </div>
            </div>

            {/* Marketing */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm font-open-sans font-medium text-gray-800 dark:text-gray-200">Marketing</span>
                <span className="text-xs tracking-tight font-inter text-gray-800 dark:text-gray-200">55% Remoto • 38% Híbrido • 7% Presencial</span>
              </div>
              <div className="flex w-full h-2 rounded-full overflow-hidden bg-gray-200 dark:bg-gray-700">
                <div className="bg-gray-900" style={{ width: '55%' }}></div>
                <div className="bg-wedo-green-bright" style={{ width: '38%' }}></div>
                <div className="bg-wedo-orange" style={{ width: '7%' }}></div>
              </div>
            </div>

            {/* RH */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm font-open-sans font-medium text-gray-800 dark:text-gray-200">Recursos Humanos</span>
                <span className="text-xs tracking-tight font-inter text-gray-800 dark:text-gray-200">42% Remoto • 45% Híbrido • 13% Presencial</span>
              </div>
              <div className="flex w-full h-2 rounded-full overflow-hidden bg-gray-200 dark:bg-gray-700">
                <div className="bg-gray-900" style={{ width: '42%' }}></div>
                <div className="bg-wedo-green-bright" style={{ width: '45%' }}></div>
                <div className="bg-wedo-orange" style={{ width: '13%' }}></div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Insights e Recomendações */}
      <Card className={`${cardStyles.default} dark:bg-gray-900 dark:border-gray-800`}>
        <CardHeader className="px-4 py-3">
          <CardTitle className={`${textStyles.title} dark:text-gray-100 flex items-center gap-2`}>
            <Lightbulb className="w-3.5 h-3.5 text-wedo-purple" />
            Insights da LIA
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex items-start gap-3">
            <CheckCircle className="w-3.5 h-3.5 mt-0.5 flex-shrink-0 text-wedo-green-bright" />
            <p className="text-sm font-open-sans text-gray-800 dark:text-gray-200">
              <strong>Tecnologia lidera em trabalho remoto:</strong> 78% das vagas tech são remotas, refletindo tendência do mercado
            </p>
          </div>
          <div className="flex items-start gap-3">
            <AlertTriangle className="w-3.5 h-3.5 mt-0.5 flex-shrink-0 text-wedo-orange" />
            <p className="text-sm font-open-sans text-gray-800 dark:text-gray-200">
              <strong>Operações predominantemente presencial:</strong> 67% exigem presença física - considere otimizar processos
            </p>
          </div>
          <div className="flex items-start gap-3">
            <TrendingUp className="w-3.5 h-3.5 mt-0.5 flex-shrink-0 text-gray-700" />
            <p className="text-sm font-open-sans text-gray-800 dark:text-gray-200">
              <strong>Modelo híbrido em alta:</strong> Vendas (62%) e Financeiro (51%) preferem equilíbrio entre remoto e presencial
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

// 5. Funil & Performance
function FunilPerformancePlaceholder() {
  return (
    <div className="space-y-3">
      {/* Header */}
      <div>
        <h1 className={`${textStyles.title} dark:text-gray-100 flex items-center gap-2`}>
          <TrendingUp className="w-3.5 h-3.5 text-gray-600 dark:text-gray-400" />
          Funil & Performance
        </h1>
        <p className={`${textStyles.bodySmall} dark:text-gray-400 mt-1`}>
          Análise de conversão do pipeline, efetividade por canal e qualidade do processo
        </p>
      </div>

      {/* Funil de Conversão Visual */}
      <Card className={`${cardStyles.default} dark:bg-gray-950 dark:border-gray-700`}>
        <CardHeader className="px-4 py-3">
          <CardTitle className={`${textStyles.title} dark:text-gray-100 flex items-center gap-2`}>
            <BarChart3 className="w-3.5 h-3.5 text-gray-600 dark:text-gray-400" />
            Funil de Conversão do Pipeline
          </CardTitle>
        </CardHeader>
        <CardContent className="pt-6">
          <div className="space-y-4">
            {/* Candidaturas Recebidas */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-open-sans font-semibold text-gray-950 dark:text-gray-50">Candidaturas Recebidas</p>
                  <p className={`${textStyles.description} dark:text-gray-400`}>100% do funil</p>
                </div>
                <span className="text-lg font-inter font-bold text-gray-950 dark:text-gray-50">3.247</span>
              </div>
              <div className="w-full h-4 rounded-full" style={{ background: 'linear-gradient(to right, #374151, #4B5563)' }}></div>
            </div>

            {/* Triagem LIA */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-open-sans font-semibold text-gray-950 dark:text-gray-50">Triagem LIA Aprovada</p>
                  <p className={`${textStyles.description} dark:text-gray-400`}>62% conversão</p>
                </div>
                <span className="text-lg font-inter font-bold text-gray-950 dark:text-gray-50">2.013</span>
              </div>
              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-4">
                <div className="h-4 rounded-full bg-gray-900" style={{ width: '62%' }}></div>
              </div>
            </div>

            {/* Entrevistas Agendadas */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-open-sans font-semibold text-gray-950 dark:text-gray-50">Entrevistas Agendadas</p>
                  <p className={`${textStyles.description} dark:text-gray-400`}>38% conversão (total)</p>
                </div>
                <span className="text-lg font-inter font-bold text-gray-950 dark:text-gray-50">1.234</span>
              </div>
              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-4">
                <div className="h-4 rounded-full bg-wedo-purple" style={{ width: '38%' }}></div>
              </div>
            </div>

            {/* Ofertas Enviadas */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-open-sans font-semibold text-gray-950 dark:text-gray-50">Ofertas Enviadas</p>
                  <p className={`${textStyles.description} dark:text-gray-400`}>18% conversão (total)</p>
                </div>
                <span className="text-lg font-inter font-bold text-gray-950 dark:text-gray-50">585</span>
              </div>
              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-4">
                <div className="h-4 rounded-full bg-wedo-orange" style={{ width: '18%' }}></div>
              </div>
            </div>

            {/* Contratações Finalizadas */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-open-sans font-semibold text-gray-950 dark:text-gray-50">Contratações Finalizadas</p>
                  <p className={`${textStyles.description} dark:text-gray-400`}>12% conversão (total)</p>
                </div>
                <span className="text-lg font-inter font-bold text-green-600 dark:text-green-400">389</span>
              </div>
              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-4">
                <div className="h-4 rounded-full bg-wedo-green-bright" style={{ width: '12%' }}></div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Performance por Canal & Taxas de Conversão */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-2.5">
        {/* Performance por Canal de Divulgação */}
        <Card className={`${cardStyles.default} dark:bg-gray-950 dark:border-gray-700`}>
          <CardHeader className="pb-3">
            <CardTitle className={`${textStyles.subtitle} dark:text-gray-100 flex items-center gap-2`}>
              <Target className="w-3.5 h-3.5 text-wedo-green" />
              Performance por Canal de Divulgação
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {/* LinkedIn */}
            <div className="p-3 bg-gray-50 dark:bg-gray-800 rounded-md border border-gray-200 dark:border-gray-800">
              <div className="flex items-center justify-between mb-2">
                <div>
                  <p className="font-open-sans font-semibold text-gray-950 dark:text-gray-50 text-sm">LinkedIn Jobs</p>
                  <p className={`${textStyles.description} dark:text-gray-400`}>1.247 candidaturas • 178 contratações</p>
                </div>
 <Badge className="bg-gray-100 text-gray-900 dark:text-gray-300 font-inter font-bold">
                  14.3%
                </Badge>
              </div>
              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                <div className="h-2 rounded-full bg-gray-900" style={{ width: '14.3%' }}></div>
              </div>
            </div>

            {/* Indicações */}
            <div className="p-3 bg-gray-50 dark:bg-gray-800 rounded-md border border-gray-200 dark:border-gray-800">
              <div className="flex items-center justify-between mb-2">
                <div>
                  <p className="font-open-sans font-semibold text-gray-950 dark:text-gray-50 text-sm">Indicações Internas</p>
                  <p className={`${textStyles.description} dark:text-gray-400`}>412 candidaturas • 94 contratações</p>
                </div>
                <Badge className="bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400 font-inter font-bold">
                  22.8%
                </Badge>
              </div>
              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                <div className="h-2 rounded-full bg-wedo-green-bright" style={{ width: '22.8%' }}></div>
              </div>
            </div>

            {/* Site Corporativo */}
            <div className="p-3 bg-gray-50 dark:bg-gray-800 rounded-md border border-gray-200 dark:border-gray-800">
              <div className="flex items-center justify-between mb-2">
                <div>
                  <p className="font-open-sans font-semibold text-gray-950 dark:text-gray-50 text-sm">Site Corporativo</p>
                  <p className={`${textStyles.description} dark:text-gray-400`}>894 candidaturas • 87 contratações</p>
                </div>
                <Badge className="bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400 font-inter font-bold">
                  9.7%
                </Badge>
              </div>
              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                <div className="h-2 rounded-full bg-wedo-orange" style={{ width: '9.7%' }}></div>
              </div>
            </div>

            {/* Job Boards */}
            <div className="p-3 bg-gray-50 dark:bg-gray-800 rounded-md border border-gray-200 dark:border-gray-800">
              <div className="flex items-center justify-between mb-2">
                <div>
                  <p className="font-open-sans font-semibold text-gray-950 dark:text-gray-50 text-sm">Job Boards (Catho, Vagas.com)</p>
                  <p className={`${textStyles.description} dark:text-gray-400`}>562 candidaturas • 24 contratações</p>
                </div>
                <Badge className="bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400 font-inter font-bold">
                  4.3%
                </Badge>
              </div>
              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                <div className="h-2 rounded-full bg-wedo-purple" style={{ width: '4.3%' }}></div>
              </div>
            </div>

            {/* Headhunting */}
            <div className="p-3 bg-gray-50 dark:bg-gray-800 rounded-md border border-gray-200 dark:border-gray-800">
              <div className="flex items-center justify-between mb-2">
                <div>
                  <p className="font-open-sans font-semibold text-gray-950 dark:text-gray-50 text-sm">Headhunting Especializado</p>
                  <p className={`${textStyles.description} dark:text-gray-400`}>132 candidaturas • 6 contratações</p>
                </div>
                <Badge className="bg-pink-100 text-pink-700 dark:bg-pink-900/30 dark:text-pink-400 font-inter font-bold">
                  4.5%
                </Badge>
              </div>
              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                <div className="h-2 rounded-full bg-wedo-magenta" style={{ width: '4.5%' }}></div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Qualidade do Processo */}
        <Card className={`${cardStyles.default} dark:bg-gray-950 dark:border-gray-700`}>
          <CardHeader className="pb-3">
            <CardTitle className={`${textStyles.subtitle} dark:text-gray-100 flex items-center gap-2`}>
              <Award className="w-3.5 h-3.5 text-wedo-purple" />
              Indicadores de Qualidade
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Taxa de Aceitação de Ofertas */}
            <div className="p-4 bg-green-50 dark:bg-green-900/20 rounded-md">
              <div className="flex items-center justify-between mb-2">
                <p className="text-sm font-open-sans font-semibold text-gray-950 dark:text-gray-50">Taxa de Aceitação de Ofertas</p>
                <div className="text-2xl font-inter font-bold text-green-600 dark:text-green-400">66%</div>
              </div>
              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                <div className="h-2 rounded-full bg-wedo-green-bright" style={{ width: '66%' }}></div>
              </div>
              <p className={`${textStyles.description} mt-2`}>Meta: 60% • +6% vs. meta</p>
            </div>

            {/* Tempo Médio de Fechamento */}
 <div className="p-4 bg-gray-50 dark:bg-gray-800 rounded-md">
              <div className="flex items-center justify-between mb-2">
                <p className="text-sm font-open-sans font-semibold text-gray-950 dark:text-gray-50">Tempo Médio de Fechamento</p>
 <div className="text-2xl font-inter font-bold text-gray-900 dark:text-gray-300">21<span className="text-sm">d</span></div>
              </div>
              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                <div className="h-2 rounded-full bg-gray-900" style={{ width: '70%' }}></div>
              </div>
              <p className={`${textStyles.bodySmall} text-green-600 dark:text-green-400 mt-2`}>-4 dias vs. mês anterior</p>
            </div>

            {/* Satisfação dos Contratados */}
            <div className="p-4 bg-purple-50 dark:bg-purple-900/20 rounded-md">
              <div className="flex items-center justify-between mb-2">
                <p className="text-sm font-open-sans font-semibold text-gray-950 dark:text-gray-50">Satisfação dos Contratados (30 dias)</p>
                <div className="text-2xl font-inter font-bold text-purple-600 dark:text-purple-400">8.7<span className="text-sm">/10</span></div>
              </div>
              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                <div className="h-2 rounded-full bg-wedo-purple" style={{ width: '87%' }}></div>
              </div>
              <p className={`${textStyles.description} mt-2`}>NPS: +74 (Excelente)</p>
            </div>

            {/* Retenção 90 dias */}
            <div className="p-4 bg-orange-50 dark:bg-orange-900/20 rounded-md">
              <div className="flex items-center justify-between mb-2">
                <p className="text-sm font-open-sans font-semibold text-gray-950 dark:text-gray-50">Retenção em 90 dias</p>
                <div className="text-2xl font-inter font-bold text-orange-600 dark:text-orange-400">92%</div>
              </div>
              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                <div className="h-2 rounded-full bg-wedo-orange" style={{ width: '92%' }}></div>
              </div>
              <p className={`${textStyles.description} mt-2`}>Meta: 85% • +7% vs. meta</p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Insights e Recomendações */}
      <Card className={`${cardStyles.default} dark:bg-gray-900 dark:border-gray-800`}>
        <CardHeader className="px-4 py-3">
          <CardTitle className={`${textStyles.title} dark:text-gray-100 flex items-center gap-2`}>
            <Lightbulb className="w-3.5 h-3.5 text-gray-600 dark:text-gray-400" />
            Insights de Performance
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex items-start gap-3">
            <CheckCircle className="w-3.5 h-3.5 mt-0.5 flex-shrink-0 text-wedo-green-bright" />
            <p className="text-sm font-open-sans text-gray-800 dark:text-gray-200">
              <strong>Indicações são o canal mais efetivo:</strong> 22.8% de conversão - 2x a média. Incentive programa de referral.
            </p>
          </div>
          <div className="flex items-start gap-3">
            <TrendingUp className="w-3.5 h-3.5 mt-0.5 flex-shrink-0 text-gray-700" />
            <p className="text-sm font-open-sans text-gray-800 dark:text-gray-200">
              <strong>LinkedIn gera volume:</strong> 38% das candidaturas vêm do LinkedIn. Otimizar descrições de vagas pode aumentar qualidade.
            </p>
          </div>
          <div className="flex items-start gap-3">
            <AlertTriangle className="w-3.5 h-3.5 mt-0.5 flex-shrink-0 text-wedo-orange" />
            <p className="text-sm font-open-sans text-gray-800 dark:text-gray-200">
              <strong>Job Boards com baixa conversão:</strong> 4.3% pode indicar descasamento de público. Reavaliar investimento nesses canais.
            </p>
          </div>
          <div className="flex items-start gap-3">
            <Award className="w-3.5 h-3.5 mt-0.5 flex-shrink-0 text-wedo-purple" />
            <p className="text-sm font-open-sans text-gray-800 dark:text-gray-200">
              <strong>Qualidade em alta:</strong> Retenção de 92% em 90 dias supera meta em 7%. Processo de seleção está bem calibrado.
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

// ===========================================================
// NOVOS DASHBOARDS PROPOSTOS
// ===========================================================

// 6. War Room Operacional
function WarRoomOperacionalPlaceholder() {
  return (
    <div className="space-y-3">
      {/* Header */}
      <div>
        <h1 className="text-sm leading-tight font-semibold font-['Open_Sans',sans-serif] text-gray-950 dark:text-gray-50 flex items-center gap-2">
          <AlertTriangle className="w-3.5 h-3.5 text-wedo-magenta" />
          War Room Operacional
        </h1>
        <p className="text-gray-600 dark:text-gray-400 mt-1 font-open-sans text-xs">
          Alertas críticos, ações urgentes e pipelines em risco que exigem atenção imediata
        </p>
      </div>

      {/* Alertas Críticos KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        <Card className="border-red-200 dark:border-red-800 bg-red-50 dark:bg-red-900/20">
          <CardContent className="p-3">
            <div className="flex items-start justify-between mb-2">
              <p className="text-xs tracking-tight font-open-sans text-red-700 dark:text-red-400 font-semibold">VAGAS EM RISCO</p>
              <AlertTriangle className="w-3.5 h-3.5 text-red-600" />
            </div>
            <div className="text-2xl font-inter font-bold text-red-600 dark:text-red-400">8</div>
            <p className={`${textStyles.bodySmall} text-red-700 dark:text-red-400 mt-1`}>&gt;45 dias sem candidatos</p>
          </CardContent>
        </Card>

        <Card className="border-orange-200 dark:border-orange-800 bg-orange-50 dark:bg-orange-900/20">
          <CardContent className="p-3">
            <div className="flex items-start justify-between mb-2">
              <p className="text-xs tracking-tight font-open-sans text-orange-700 dark:text-orange-400 font-semibold">AÇÕES URGENTES</p>
              <Target className="w-3.5 h-3.5 text-orange-600" />
            </div>
            <div className="text-2xl font-inter font-bold text-orange-600 dark:text-orange-400">23</div>
            <p className={`${textStyles.bodySmall} text-orange-700 dark:text-orange-400 mt-1`}>Aguardando ação RH</p>
          </CardContent>
        </Card>

        <Card className="border-yellow-200 dark:border-yellow-800 bg-yellow-50 dark:bg-yellow-900/20">
          <CardContent className="p-3">
            <div className="flex items-start justify-between mb-2">
              <p className="text-xs tracking-tight font-open-sans text-yellow-700 dark:text-yellow-400 font-semibold">EM ESPERA</p>
              <Users className="w-3.5 h-3.5 text-yellow-600" />
            </div>
            <div className="text-2xl font-inter font-bold text-yellow-600 dark:text-yellow-400">47</div>
            <p className={`${textStyles.bodySmall} text-yellow-700 dark:text-yellow-400 mt-1`}>&gt;5 dias sem feedback</p>
          </CardContent>
        </Card>
      </div>

      {/* Vagas Críticas Detalhadas */}
      <Card className="border-red-200 dark:border-red-800">
        <CardHeader className="pb-3 bg-red-50 dark:bg-red-900/20">
          <CardTitle className={`${textStyles.subtitle} dark:text-gray-100 flex items-center gap-2`}>
            <AlertTriangle className="w-3.5 h-3.5 text-red-600" />
            Vagas Críticas - Ação Imediata Necessária
          </CardTitle>
        </CardHeader>
        <CardContent className="pt-4 space-y-3">
          <div className="p-4 bg-red-50 dark:bg-red-900/20 rounded-md border-l-4 border-red-500">
            <div className="flex items-start justify-between mb-2">
              <div>
                <p className="font-open-sans font-semibold text-gray-950 dark:text-gray-50">Vaga #2847 - Senior ML Engineer</p>
                <p className="text-sm font-open-sans text-gray-600 dark:text-gray-400 mt-1">
                  62 dias aberta • 0 candidatos qualificados • Prioridade MÁXIMA
                </p>
              </div>
              <Badge className="bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400 font-inter shrink-0">CRÍTICO</Badge>
            </div>
            <div className="flex items-center gap-2 mt-3">
              <Button size="sm" className="bg-red-600 hover:bg-red-700 text-white font-open-sans">Revisar Requisitos</Button>
              <Button size="sm" variant="outline" className="font-open-sans">Buscar LIA Database</Button>
            </div>
          </div>

          <div className="p-4 bg-orange-50 dark:bg-orange-900/20 rounded-md border-l-4 border-orange-500">
            <div className="flex items-start justify-between mb-2">
              <div>
                <p className="font-open-sans font-semibold text-gray-950 dark:text-gray-50">Vaga #3012 - Tech Lead Backend</p>
                <p className="text-sm font-open-sans text-gray-600 dark:text-gray-400 mt-1">51 dias aberta • 3 candidatos em avaliação • Pipeline lento</p>
              </div>
              <Badge className="bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400 font-inter shrink-0">URGENTE</Badge>
            </div>
            <div className="flex items-center gap-2 mt-3">
              <Button size="sm" className="bg-orange-600 hover:bg-orange-700 text-white font-open-sans">Acelerar Processo</Button>
              <Button size="sm" variant="outline" className="font-open-sans">Ver Candidatos</Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Gargalos e Recomendações LIA */}
      <Card className="border-red-200 dark:border-red-800 rounded-md bg-white dark:bg-gray-900">
        <CardHeader className="px-4 py-3">
          <CardTitle className={`${textStyles.title} dark:text-gray-100 flex items-center gap-2`}>
            <Brain className="w-3.5 h-3.5 text-wedo-cyan" />
            Recomendações Urgentes da LIA
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex items-start gap-3">
            <AlertTriangle className="w-3.5 h-3.5 mt-0.5 flex-shrink-0 text-red-600" />
            <p className="text-sm font-open-sans text-gray-800 dark:text-gray-200">
              <strong>Vaga #2847 (ML Engineer) precisa de ação imediata:</strong> 62 dias sem candidatos. LIA sugere flexibilizar requisitos de "PhD obrigatório" para "Mestrado + 5 anos exp."
            </p>
          </div>
          <div className="flex items-start gap-3">
            <Target className="w-3.5 h-3.5 mt-0.5 flex-shrink-0 text-orange-600" />
            <p className="text-sm font-open-sans text-gray-800 dark:text-gray-200">
              <strong>Processo Tech Lead está 73% mais lento que a média:</strong> Gargalo identificado na aprovação do gestor. Sugere reunião de alinhamento.
            </p>
          </div>
          <div className="flex items-start gap-3">
            <Users className="w-3.5 h-3.5 mt-0.5 flex-shrink-0 text-yellow-600" />
            <p className="text-sm font-open-sans text-gray-800 dark:text-gray-200">
              <strong>47 candidatos em espera podem desistir:</strong> LIA identificou padrão histórico de 65% desistência após 7 dias sem contato. Agendar entrevistas urgente.
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

// 8. Voice Screening Dashboard
function VoiceScreeningDashboard() {
  const [analytics, setAnalytics] = useState<any>(null)
  const [screenings, setScreenings] = useState<any[]>([])
  const [isLoading, setIsLoading] = useState(true)

  React.useEffect(() => {
    fetchVoiceScreeningData()
  }, [])

  const fetchVoiceScreeningData = async () => {
    try {
      setIsLoading(true)
      
      // Fetch analytics e screenings do backend
      const [analyticsRes, screeningsRes] = await Promise.all([
        fetch('/api/backend-proxy/openmic/analytics'),
        fetch('/api/backend-proxy/openmic/screenings?limit=20')
      ])
      
      if (analyticsRes.ok) {
        const analyticsData = await analyticsRes.json()
        setAnalytics(analyticsData)
      }
      
      if (screeningsRes.ok) {
        const screeningsData = await screeningsRes.json()
        setScreenings(screeningsData.screenings || [])
      }
    } catch (error) {
      console.error('Failed to fetch voice screening data:', error)
    } finally {
      setIsLoading(false)
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center space-y-3">
          <Activity className="w-8 h-8 mx-auto text-gray-600 dark:text-gray-400 animate-spin" />
          <p className="text-sm font-open-sans text-gray-600 dark:text-gray-400">
            Carregando dados de Voice Screening...
          </p>
        </div>
      </div>
    )
  }

  const getRecommendationColor = (recommendation: string) => {
    switch (recommendation) {
      case 'strong_yes':
        return 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
      case 'interview':
 return 'bg-gray-100 text-gray-900 dark:text-gray-300'
      case 'maybe':
        return 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400'
      case 'reject':
        return 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'
      default:
 return 'bg-gray-100 text-gray-800 dark:bg-gray-900/30 dark:text-gray-400'
    }
  }

  const getRecommendationLabel = (recommendation: string) => {
    switch (recommendation) {
      case 'strong_yes':
        return 'Forte Sim'
      case 'interview':
        return 'Entrevistar'
      case 'maybe':
        return 'Talvez'
      case 'reject':
        return 'Rejeitar'
      default:
        return recommendation
    }
  }

  return (
    <div className="space-y-3">
      {/* Header */}
      <div>
        <h1 className="text-sm leading-tight font-semibold font-['Open_Sans',sans-serif] text-gray-950 dark:text-gray-50 flex items-center gap-2">
          <Phone className="w-3.5 h-3.5 text-gray-600 dark:text-gray-400" />
          Voice Screening Analytics
        </h1>
        <p className="text-gray-600 dark:text-gray-400 mt-1 font-open-sans text-xs">
          Análise de triagem por voz com IA - OpenMic.ai + LIA Assistant
        </p>
      </div>

      {/* KPIs Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-2.5">
        <Card className={`${cardStyles.default} dark:bg-gray-950 dark:border-gray-700`}>
          <CardContent className="p-4">
            <p className={`${textStyles.description} mb-1`}>Total de Screenings</p>
            <p className="text-xl font-bold font-inter text-gray-950 dark:text-gray-50">
              {analytics?.total_screenings || 0}
            </p>
          </CardContent>
        </Card>

        <Card className={`${cardStyles.default} dark:bg-gray-950 dark:border-gray-700`}>
          <CardContent className="p-4">
            <p className={`${textStyles.description} mb-1`}>Com Análise IA</p>
            <p className="text-xl font-bold font-inter text-gray-950 dark:text-gray-50">
              {analytics?.analyzed_screenings || 0}
            </p>
          </CardContent>
        </Card>

        <Card className={`${cardStyles.default} dark:bg-gray-950 dark:border-gray-700`}>
          <CardContent className="p-4">
            <p className={`${textStyles.description} mb-1`}>Score Médio Geral</p>
            <p className="text-xl font-bold font-inter text-gray-950 dark:text-gray-50">
              {analytics?.average_scores?.overall || 0}/100
            </p>
          </CardContent>
        </Card>

        <Card className={`${cardStyles.default} dark:bg-gray-950 dark:border-gray-700`}>
          <CardContent className="p-4">
            <p className={`${textStyles.description} mb-1`}>Score Técnico Médio</p>
            <p className="text-xl font-bold font-inter text-gray-950 dark:text-gray-50">
              {analytics?.average_scores?.technical || 0}/100
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Recommendation Breakdown */}
      {analytics?.recommendation_breakdown && Object.keys(analytics.recommendation_breakdown).length > 0 && (
        <Card className={`${cardStyles.default} dark:bg-gray-950 dark:border-gray-700`}>
          <CardHeader className="px-4 py-3">
            <CardTitle className={`${textStyles.title} dark:text-gray-100 flex items-center gap-2`}>
              <PieChart className="w-3.5 h-3.5 text-gray-600 dark:text-gray-400" />
              Distribuição de Recomendações
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-2">
              {Object.entries(analytics.recommendation_breakdown).map(([rec, count]: [string, any]) => (
                <div key={rec} className="p-3 bg-gray-50 dark:bg-gray-900 rounded-md border border-gray-200 dark:border-gray-800">
                  <p className={`${textStyles.description} mb-1`}>
                    {getRecommendationLabel(rec)}
                  </p>
                  <p className="text-lg font-bold font-inter text-gray-950 dark:text-gray-50">
                    {count}
                  </p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Recent Screenings List */}
      <Card className={`${cardStyles.default} dark:bg-gray-950 dark:border-gray-700`}>
        <CardHeader className="px-4 py-3">
          <CardTitle className={`${textStyles.title} dark:text-gray-100 flex items-center gap-2`}>
            <Activity className="w-3.5 h-3.5 text-gray-600 dark:text-gray-400" />
            Screenings Recentes ({screenings.length})
          </CardTitle>
        </CardHeader>
        <CardContent>
          {screenings.length === 0 ? (
            <div className="text-center py-8">
 <Phone className="w-12 h-12 mx-auto text-gray-300 dark:text-gray-200 mb-3" />
              <p className="text-sm font-open-sans text-gray-600 dark:text-gray-400">
                Nenhum screening realizado ainda
              </p>
              <p className="text-xs font-open-sans text-gray-800 dark:text-gray-200 mt-1">
                Use o endpoint /api/v1/openmic/test-call para iniciar um screening
              </p>
            </div>
          ) : (
            <div className="space-y-2">
              {screenings.map((screening) => (
                <div 
                  key={screening.id}
                  className="p-3 bg-gray-50 dark:bg-gray-900 rounded-md border border-gray-200 dark:border-gray-800 hover:border-gray-900 dark:hover:border-gray-50 dark:hover:border-gray-900 dark:hover:border-gray-50 transition-colors"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <p className="font-semibold font-open-sans text-sm text-gray-950 dark:text-gray-50 truncate">
                          {screening.candidate_name}
                        </p>
                        {screening.analysis && (
                          <Badge className={getRecommendationColor(screening.analysis.overall_recommendation)}>
                            {getRecommendationLabel(screening.analysis.overall_recommendation)}
                          </Badge>
                        )}
                      </div>
                      
                      <p className="text-xs font-open-sans text-gray-600 dark:text-gray-400 mb-2">
                        {screening.job_title} • {screening.duration_seconds}s • {screening.candidate_phone}
                      </p>

                      {screening.analysis && (
                        <>
                          <div className="flex items-center gap-3 mb-2">
                            <div className="flex items-center gap-1.5">
                              <span className={`${textStyles.description} dark:text-gray-400`}>Geral:</span>
                              <span className="text-xs font-bold font-inter text-gray-950 dark:text-gray-50">
                                {screening.analysis.overall_score}/100
                              </span>
                            </div>
                            <div className="flex items-center gap-1.5">
                              <span className={`${textStyles.description} dark:text-gray-400`}>Técnico:</span>
                              <span className="text-xs font-bold font-inter text-gray-950 dark:text-gray-50">
                                {screening.analysis.tech_score || 'N/A'}
                              </span>
                            </div>
                            <div className="flex items-center gap-1.5">
                              <span className={`${textStyles.description} dark:text-gray-400`}>Comunicação:</span>
                              <span className="text-xs font-bold font-inter text-gray-950 dark:text-gray-50">
                                {screening.analysis.comm_score || 'N/A'}
                              </span>
                            </div>
                          </div>

                          {screening.analysis.summary && (
                            <p className="text-xs font-open-sans text-gray-600 dark:text-gray-400 line-clamp-2">
                              {screening.analysis.summary}
                            </p>
                          )}

                          {screening.analysis.key_strengths && screening.analysis.key_strengths.length > 0 && (
                            <div className="mt-2 flex flex-wrap gap-1">
                              {screening.analysis.key_strengths.slice(0, 3).map((strength: string, idx: number) => (
                                <Badge 
                                  key={idx}
                                  className="bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400 text-xs tracking-tight"
                                >
                                  ✓ {strength}
                                </Badge>
                              ))}
                            </div>
                          )}
                        </>
                      )}
                    </div>

                    <div className="flex flex-col items-end gap-2">
                      <p className={`${textStyles.description} dark:text-gray-400`}>
                        {new Date(screening.created_at).toLocaleDateString('pt-BR')}
                      </p>
                      {screening.processing_status && (
 <Badge className="bg-gray-100 text-gray-800 dark:bg-gray-900/30 dark:text-gray-400 text-xs tracking-tight">
                          {screening.processing_status}
                        </Badge>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Integration Info Card */}
 <Card className="bg-gray-50 dark:bg-gray-800 border-gray-300 dark:border-gray-200">
        <CardContent className="p-4">
          <div className="flex items-start gap-3">
            <Brain className="w-4 h-4 mt-0.5 flex-shrink-0 text-wedo-cyan" />
            <div className="flex-1">
              <p className="font-semibold font-open-sans text-sm text-gray-950 dark:text-gray-50 mb-1">
                OpenMic.ai + LIA Integration
              </p>
              <p className={`${textStyles.bodySmall} dark:text-gray-400`}>
                Sistema de triagem por voz automática com análise dual: keywords básicos (~100ms) + Claude Sonnet 4.5 deep analysis (~10-15s). 
                Todas as ligações são gravadas, transcritas e analisadas automaticamente com 4 dimensões: técnica, comunicação, fit cultural e avaliação geral.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

// 7. Análise de Competências
function AnaliseCompetenciasPlaceholder() {
  return (
    <div className="space-y-3">
      {/* Header */}
      <div>
        <h1 className={`${textStyles.title} dark:text-gray-100 flex items-center gap-2`}>
          <Award className="w-3.5 h-3.5 text-wedo-green" />
          Análise de Competências
        </h1>
        <p className={`${textStyles.bodySmall} dark:text-gray-400 mt-1`}>
          Skills gap, competências emergentes e matriz de desenvolvimento de talentos
        </p>
      </div>

      {/* Skills Gap vs Demanda */}
      <Card className={`${cardStyles.default} dark:bg-gray-950 dark:border-gray-700`}>
        <CardHeader className="px-4 py-3">
          <CardTitle className={`${textStyles.title} dark:text-gray-100 flex items-center gap-2`}>
            <TrendingUp className="w-3.5 h-3.5 text-wedo-green" />
            Gap de Competências: Demanda vs Disponibilidade
          </CardTitle>
        </CardHeader>
        <CardContent className="pt-4 space-y-4">
          {/* ML/AI - Gap Crítico */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <div>
                <p className="font-open-sans font-semibold text-gray-950 dark:text-gray-50">Machine Learning / AI</p>
                <p className={`${textStyles.description} dark:text-gray-400`}>Demanda: 156 vagas • Disponível: 42 candidatos</p>
              </div>
              <Badge className="bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400 font-inter font-bold">Gap 73%</Badge>
            </div>
            <div className="flex w-full h-3 rounded-full overflow-hidden bg-gray-200 dark:bg-gray-700">
              <div className="bg-wedo-green-bright" style={{ width: '27%' }} title="Disponível"></div>
              <div className="bg-wedo-magenta" style={{ width: '73%' }} title="Gap"></div>
            </div>
          </div>

          {/* DevOps - Gap Alto */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <div>
                <p className="font-open-sans font-semibold text-gray-950 dark:text-gray-50">DevOps / Cloud (AWS/Azure/GCP)</p>
                <p className={`${textStyles.description} dark:text-gray-400`}>Demanda: 194 vagas • Disponível: 87 candidatos</p>
              </div>
              <Badge className="bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400 font-inter font-bold">Gap 55%</Badge>
            </div>
            <div className="flex w-full h-3 rounded-full overflow-hidden bg-gray-200 dark:bg-gray-700">
              <div className="bg-wedo-green-bright" style={{ width: '45%' }} title="Disponível"></div>
              <div className="bg-wedo-orange" style={{ width: '55%' }} title="Gap"></div>
            </div>
          </div>

          {/* React - Gap Controlado */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <div>
                <p className="font-open-sans font-semibold text-gray-950 dark:text-gray-50">React.js / Frontend Moderno</p>
                <p className={`${textStyles.description} dark:text-gray-400`}>Demanda: 287 vagas • Disponível: 198 candidatos</p>
              </div>
              <Badge className="bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400 font-inter font-bold">Gap 31%</Badge>
            </div>
            <div className="flex w-full h-3 rounded-full overflow-hidden bg-gray-200 dark:bg-gray-700">
              <div className="bg-wedo-green-bright" style={{ width: '69%' }} title="Disponível"></div>
              <div className="bg-wedo-orange" style={{ width: '31%' }} title="Gap"></div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Competências Emergentes & Treinamentos */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-2.5">
        {/* Competências Emergentes */}
        <Card className={`${cardStyles.default} dark:bg-gray-950 dark:border-gray-700`}>
          <CardHeader className="pb-3">
            <CardTitle className={`${textStyles.subtitle} dark:text-gray-100 flex items-center gap-2`}>
              <Activity className="w-3.5 h-3.5 text-gray-600 dark:text-gray-400" />
              Competências Emergentes (Crescimento &gt;50%)
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
 <div className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 rounded-md border border-gray-300 dark:border-gray-200">
              <div>
                <p className="font-open-sans font-semibold text-gray-950 dark:text-gray-50 text-sm">Prompt Engineering</p>
                <p className={`${textStyles.description} dark:text-gray-400`}>23 vagas este mês</p>
              </div>
 <Badge className="bg-gray-100 text-gray-900 dark:text-gray-300 font-inter font-bold">+340%</Badge>
            </div>

            <div className="flex items-center justify-between p-3 bg-purple-50 dark:bg-purple-900/20 rounded-md border border-purple-200 dark:border-purple-800">
              <div>
                <p className="font-open-sans font-semibold text-gray-950 dark:text-gray-50 text-sm">LLM Fine-tuning</p>
                <p className={`${textStyles.description} dark:text-gray-400`}>18 vagas este mês</p>
              </div>
              <Badge className="bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400 font-inter font-bold">+280%</Badge>
            </div>

            <div className="flex items-center justify-between p-3 bg-green-50 dark:bg-green-900/20 rounded-md border border-green-200 dark:border-green-800">
              <div>
                <p className="font-open-sans font-semibold text-gray-950 dark:text-gray-50 text-sm">Kubernetes / K8s</p>
                <p className={`${textStyles.description} dark:text-gray-400`}>64 vagas este mês</p>
              </div>
              <Badge className="bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400 font-inter font-bold">+120%</Badge>
            </div>
          </CardContent>
        </Card>

        {/* Treinamentos Recomendados */}
        <Card className={`${cardStyles.default} dark:bg-gray-950 dark:border-gray-700`}>
          <CardHeader className="pb-3">
            <CardTitle className={`${textStyles.subtitle} dark:text-gray-100 flex items-center gap-2`}>
              <Award className="w-3.5 h-3.5 text-wedo-green" />
              Treinamentos Recomendados
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="p-3 bg-red-50 dark:bg-red-900/20 rounded-md border-l-4 border-red-500">
              <div className="flex items-start justify-between mb-1">
                <p className="font-open-sans font-semibold text-gray-950 dark:text-gray-50 text-sm">Machine Learning Bootcamp</p>
                <Badge className={`${badgeStyles.error} dark:bg-red-900/30 dark:text-red-400`}>CRÍTICO</Badge>
              </div>
              <p className={`${textStyles.bodySmall} dark:text-gray-400`}>
                Gap de 73% • ROI estimado: R$ 280k economia em headhunting
              </p>
            </div>

            <div className="p-3 bg-orange-50 dark:bg-orange-900/20 rounded-md border-l-4 border-orange-500">
              <div className="flex items-start justify-between mb-1">
                <p className="font-open-sans font-semibold text-gray-950 dark:text-gray-50 text-sm">DevOps & Cloud Certification</p>
                <Badge className="bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400 text-xs font-inter">ALTO</Badge>
              </div>
              <p className={`${textStyles.bodySmall} dark:text-gray-400`}>
                Gap de 55% • Parceria com AWS Training disponível
              </p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Insights da LIA */}
      <Card className={`${cardStyles.default} dark:bg-gray-900 dark:border-gray-800`}>
        <CardHeader className="px-4 py-3">
          <CardTitle className={`${textStyles.title} dark:text-gray-100 flex items-center gap-2`}>
            <Brain className="w-3.5 h-3.5 text-wedo-cyan" />
            Insights Estratégicos de Competências
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex items-start gap-3">
            <AlertTriangle className="w-3.5 h-3.5 mt-0.5 flex-shrink-0 text-wedo-magenta" />
            <p className="text-sm font-open-sans text-gray-800 dark:text-gray-200">
              <strong>Gap crítico em ML/AI:</strong> 73% de gap pode inviabilizar expansão planejada. Investimento em bootcamp interno economizaria R$ 280k vs. headhunting.
            </p>
          </div>
          <div className="flex items-start gap-3">
            <TrendingUp className="w-3.5 h-3.5 mt-0.5 flex-shrink-0 text-gray-700" />
            <p className="text-sm font-open-sans text-gray-800 dark:text-gray-200">
              <strong>Prompt Engineering explodiu 340%:</strong> Competência emergente crítica. Considere treinamento interno urgente para engenheiros existentes.
            </p>
          </div>
          <div className="flex items-start gap-3">
            <CheckCircle className="w-3.5 h-3.5 mt-0.5 flex-shrink-0 text-wedo-green-bright" />
            <p className="text-sm font-open-sans text-gray-800 dark:text-gray-200">
              <strong>React.js com gap controlado:</strong> 31% de gap está gerenciável. Pipeline atual atende demanda projetada para próximos 3 meses.
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

// ============================================================
// SUB-DASHBOARDS DE PEOPLE ANALYTICS
// ============================================================

// Big Five Analytics Dashboard (Versão Compacta)
function BigFiveAnalyticsDashboard() {
  return (
    <div className="space-y-3">
      {/* KPIs Principais */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-2.5">
        <Card className={`${cardStyles.default} dark:bg-gray-950 dark:border-gray-800`}>
          <CardContent className="p-3">
            <div className="flex items-start justify-between mb-2">
              <p className={`${textStyles.bodySmall} dark:text-gray-400`}>Candidatos Avaliados</p>
              <Users className="w-3.5 h-3.5 text-wedo-purple" />
            </div>
            <div className="text-xl font-inter font-bold text-gray-950 dark:text-gray-50">247</div>
            <p className={`${textStyles.bodySmall} text-purple-600 dark:text-purple-400 mt-1`}>+12% vs. mês anterior</p>
          </CardContent>
        </Card>

        <Card className={`${cardStyles.default} dark:bg-gray-950 dark:border-gray-800`}>
          <CardContent className="p-3">
            <div className="flex items-start justify-between mb-2">
              <p className={`${textStyles.bodySmall} dark:text-gray-400`}>Acurácia de Predição</p>
              <Target className="w-3.5 h-3.5 text-wedo-green" />
            </div>
            <div className="text-xl font-inter font-bold text-gray-950 dark:text-gray-50">89%</div>
            <p className={`${textStyles.bodySmall} text-green-600 dark:text-green-400 mt-1`}>vs. 72% método tradicional</p>
          </CardContent>
        </Card>

        <Card className={`${cardStyles.default} dark:bg-gray-950 dark:border-gray-800`}>
          <CardContent className="p-3">
            <div className="flex items-start justify-between mb-2">
              <p className={`${textStyles.bodySmall} dark:text-gray-400`}>Redução de Turnover</p>
              <TrendingUp className="w-3.5 h-3.5 text-gray-600 dark:text-gray-400" />
            </div>
            <div className="text-xl font-inter font-bold text-gray-950 dark:text-gray-50">-24%</div>
 <p className={`${textStyles.bodySmall} text-gray-900 dark:text-gray-300 mt-1`}>com Big Five screening</p>
          </CardContent>
        </Card>

        <Card className={`${cardStyles.default} dark:bg-gray-950 dark:border-gray-800`}>
          <CardContent className="p-3">
            <div className="flex items-start justify-between mb-2">
              <p className={`${textStyles.bodySmall} dark:text-gray-400`}>Performance Média</p>
              <Award className="w-3.5 h-3.5 text-wedo-orange" />
            </div>
            <div className="text-xl font-inter font-bold text-gray-950 dark:text-gray-50">8.9</div>
            <p className={`${textStyles.bodySmall} text-orange-600 dark:text-orange-400 mt-1`}>contratados via Big Five</p>
          </CardContent>
        </Card>
      </div>

      {/* Distribuição por Traço */}
      <Card className="border-gray-200 dark:border-gray-800 rounded-md bg-white dark:bg-gray-950">
        <CardHeader className="px-4 py-3">
          <CardTitle className="text-xs font-sans font-open-sans font-semibold text-gray-950 dark:text-gray-50">
            Distribuição dos Traços de Personalidade
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {/* Abertura */}
          <div className="space-y-1.5">
            <div className="flex items-center justify-between">
              <span className="text-xs font-open-sans text-gray-800 dark:text-gray-200">Abertura</span>
              <span className="text-sm font-inter font-bold text-gray-950 dark:text-gray-50">68%</span>
            </div>
            <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
              <div className="h-2 rounded-full bg-wedo-purple" style={{ width: '68%' }}></div>
            </div>
          </div>

          {/* Conscienciosidade */}
          <div className="space-y-1.5">
            <div className="flex items-center justify-between">
              <span className="text-xs font-open-sans text-gray-800 dark:text-gray-200">Conscienciosidade</span>
              <span className="text-sm font-inter font-bold text-gray-950 dark:text-gray-50">74%</span>
            </div>
            <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
              <div className="h-2 rounded-full bg-wedo-green-bright" style={{ width: '74%' }}></div>
            </div>
          </div>

          {/* Extroversão */}
          <div className="space-y-1.5">
            <div className="flex items-center justify-between">
              <span className="text-xs font-open-sans text-gray-800 dark:text-gray-200">Extroversão</span>
              <span className="text-sm font-inter font-bold text-gray-950 dark:text-gray-50">61%</span>
            </div>
            <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
              <div className="h-2 rounded-full bg-gray-900" style={{ width: '61%' }}></div>
            </div>
          </div>

          {/* Amabilidade */}
          <div className="space-y-1.5">
            <div className="flex items-center justify-between">
              <span className="text-xs font-open-sans text-gray-800 dark:text-gray-200">Amabilidade</span>
              <span className="text-sm font-inter font-bold text-gray-950 dark:text-gray-50">72%</span>
            </div>
            <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
              <div className="h-2 rounded-full bg-wedo-orange" style={{ width: '72%' }}></div>
            </div>
          </div>

          {/* Estabilidade Emocional */}
          <div className="space-y-1.5">
            <div className="flex items-center justify-between">
              <span className="text-xs font-open-sans text-gray-800 dark:text-gray-200">Estabilidade Emocional</span>
              <span className="text-sm font-inter font-bold text-gray-950 dark:text-gray-50">55%</span>
            </div>
            <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
              <div className="h-2 rounded-full bg-wedo-magenta" style={{ width: '55%' }}></div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Correlação com Performance */}
      <Card className="border-gray-200 dark:border-gray-800 rounded-md bg-white dark:bg-gray-950">
        <CardHeader className="px-4 py-3">
          <CardTitle className={`${textStyles.subtitle} dark:text-gray-100 flex items-center gap-2`}>
            <BarChart3 className="w-3.5 h-3.5 text-gray-600 dark:text-gray-400" />
            Correlação Traços × Performance
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            <div className="flex items-center justify-between p-2 bg-gray-50 dark:bg-gray-800/50 rounded">
              <span className="text-xs font-open-sans text-gray-800 dark:text-gray-200">Conscienciosidade</span>
              <div className="flex items-center gap-2">
                <Badge className="bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400 text-xs tracking-tight">Muito Alta</Badge>
                <span className="text-sm font-inter font-bold">0.84</span>
              </div>
            </div>
            <div className="flex items-center justify-between p-2 bg-gray-50 dark:bg-gray-800/50 rounded">
              <span className="text-xs font-open-sans text-gray-800 dark:text-gray-200">Estabilidade</span>
              <div className="flex items-center gap-2">
 <Badge className="bg-gray-100 text-gray-900 dark:text-gray-300 text-xs tracking-tight">Alta</Badge>
                <span className="text-sm font-inter font-bold">0.71</span>
              </div>
            </div>
            <div className="flex items-center justify-between p-2 bg-gray-50 dark:bg-gray-800/50 rounded">
              <span className="text-xs font-open-sans text-gray-800 dark:text-gray-200">Abertura</span>
              <div className="flex items-center gap-2">
                <Badge className="bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400 text-xs tracking-tight">Alta</Badge>
                <span className="text-sm font-inter font-bold">0.67</span>
              </div>
            </div>
            <div className="flex items-center justify-between p-2 bg-gray-50 dark:bg-gray-800/50 rounded">
              <span className="text-xs font-open-sans text-gray-800 dark:text-gray-200">Amabilidade</span>
              <div className="flex items-center gap-2">
                <Badge className="bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400 text-xs tracking-tight">Alta</Badge>
                <span className="text-sm font-inter font-bold">0.63</span>
              </div>
            </div>
            <div className="flex items-center justify-between p-2 bg-gray-50 dark:bg-gray-800/50 rounded">
              <span className="text-xs font-open-sans text-gray-800 dark:text-gray-200">Extroversão</span>
              <div className="flex items-center gap-2">
 <Badge className="bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-400 text-xs tracking-tight">Moderada</Badge>
                <span className="text-sm font-inter font-bold">0.51</span>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

// Diversidade & Inclusão Dashboard
function DiversidadeInclusaoDashboard() {
  return (
    <div className="space-y-3">
      {/* KPIs de Diversidade */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-2.5">
        <Card className={`${cardStyles.default} dark:bg-gray-950 dark:border-gray-800`}>
          <CardContent className="p-3">
            <div className="flex items-start justify-between mb-2">
              <p className={`${textStyles.bodySmall} dark:text-gray-400`}>Pessoas com Deficiência</p>
              <Heart className="w-3.5 h-3.5 text-wedo-orange" />
            </div>
            <div className="text-xl font-inter font-bold text-gray-950 dark:text-gray-50">8.2%</div>
            <p className={`${textStyles.bodySmall} text-orange-600 dark:text-orange-400 mt-1`}>Meta: 5% (excedida)</p>
          </CardContent>
        </Card>

        <Card className={`${cardStyles.default} dark:bg-gray-950 dark:border-gray-800`}>
          <CardContent className="p-3">
            <div className="flex items-start justify-between mb-2">
              <p className={`${textStyles.bodySmall} dark:text-gray-400`}>Equidade de Gênero</p>
              <Users className="w-3.5 h-3.5 text-wedo-purple" />
            </div>
            <div className="text-xl font-inter font-bold text-gray-950 dark:text-gray-50">48%</div>
            <p className={`${textStyles.bodySmall} text-purple-600 dark:text-purple-400 mt-1`}>mulheres em tech</p>
          </CardContent>
        </Card>

        <Card className={`${cardStyles.default} dark:bg-gray-950 dark:border-gray-800`}>
          <CardContent className="p-3">
            <div className="flex items-start justify-between mb-2">
              <p className={`${textStyles.bodySmall} dark:text-gray-400`}>Diversidade Racial</p>
              <Users className="w-3.5 h-3.5 text-wedo-green" />
            </div>
            <div className="text-xl font-inter font-bold text-gray-950 dark:text-gray-50">42%</div>
            <p className={`${textStyles.bodySmall} text-green-600 dark:text-green-400 mt-1`}>população não-branca</p>
          </CardContent>
        </Card>

        <Card className={`${cardStyles.default} dark:bg-gray-950 dark:border-gray-800`}>
          <CardContent className="p-3">
            <div className="flex items-start justify-between mb-2">
              <p className={`${textStyles.bodySmall} dark:text-gray-400`}>LGBTQIA+</p>
              <Heart className="w-3.5 h-3.5 text-gray-600 dark:text-gray-400" />
            </div>
            <div className="text-xl font-inter font-bold text-gray-950 dark:text-gray-50">12%</div>
 <p className={`${textStyles.bodySmall} text-gray-900 dark:text-gray-300 mt-1`}>auto-declarados</p>
          </CardContent>
        </Card>
      </div>

      {/* Distribuição de Gênero e Racial */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
        <Card className="border-gray-200 dark:border-gray-800 rounded-md bg-white dark:bg-gray-950">
          <CardHeader className="px-4 py-3">
            <CardTitle className="text-xs font-sans font-open-sans font-semibold text-gray-950 dark:text-gray-50">
              Distribuição de Gênero por Cargo
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-open-sans text-gray-800 dark:text-gray-200">C-Level</span>
                <div className="flex items-center gap-2">
                  <span className="text-sm font-inter text-purple-600">40% M</span>
                  <span className="text-sm font-inter text-gray-950 dark:text-gray-50">60% H</span>
                </div>
              </div>
              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2 flex overflow-hidden">
                <div className="h-2 bg-wedo-purple" style={{ width: '40%' }}></div>
                <div className="h-2 bg-gray-900" style={{ width: '60%' }}></div>
              </div>
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-open-sans text-gray-800 dark:text-gray-200">Gerência</span>
                <div className="flex items-center gap-2">
                  <span className="text-sm font-inter text-purple-600">45% M</span>
                  <span className="text-sm font-inter text-gray-950 dark:text-gray-50">55% H</span>
                </div>
              </div>
              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2 flex overflow-hidden">
                <div className="h-2 bg-wedo-purple" style={{ width: '45%' }}></div>
                <div className="h-2 bg-gray-900" style={{ width: '55%' }}></div>
              </div>
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-open-sans text-gray-800 dark:text-gray-200">Técnico</span>
                <div className="flex items-center gap-2">
                  <span className="text-sm font-inter text-purple-600">48% M</span>
                  <span className="text-sm font-inter text-gray-950 dark:text-gray-50">52% H</span>
                </div>
              </div>
              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2 flex overflow-hidden">
                <div className="h-2 bg-wedo-purple" style={{ width: '48%' }}></div>
                <div className="h-2 bg-gray-900" style={{ width: '52%' }}></div>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="border-gray-200 dark:border-gray-800 rounded-md bg-white dark:bg-gray-950">
          <CardHeader className="px-4 py-3">
            <CardTitle className="text-xs font-sans font-open-sans font-semibold text-gray-950 dark:text-gray-50">
              Diversidade Racial
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <div className="flex items-center justify-between p-2 bg-gray-50 dark:bg-gray-800/50 rounded">
              <span className="text-xs font-open-sans text-gray-800 dark:text-gray-200">Brancos</span>
              <span className="text-sm font-inter font-bold">58%</span>
            </div>
            <div className="flex items-center justify-between p-2 bg-gray-50 dark:bg-gray-800/50 rounded">
              <span className="text-xs font-open-sans text-gray-800 dark:text-gray-200">Pardos</span>
              <span className="text-sm font-inter font-bold">24%</span>
            </div>
            <div className="flex items-center justify-between p-2 bg-gray-50 dark:bg-gray-800/50 rounded">
              <span className="text-xs font-open-sans text-gray-800 dark:text-gray-200">Pretos</span>
              <span className="text-sm font-inter font-bold">14%</span>
            </div>
            <div className="flex items-center justify-between p-2 bg-gray-50 dark:bg-gray-800/50 rounded">
              <span className="text-xs font-open-sans text-gray-800 dark:text-gray-200">Amarelos</span>
              <span className="text-sm font-inter font-bold">3%</span>
            </div>
            <div className="flex items-center justify-between p-2 bg-gray-50 dark:bg-gray-800/50 rounded">
              <span className="text-xs font-open-sans text-gray-800 dark:text-gray-200">Indígenas</span>
              <span className="text-sm font-inter font-bold">1%</span>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Metas e Progresso */}
      <Card className="border-gray-200 dark:border-gray-800 rounded-md bg-white dark:bg-gray-950">
        <CardHeader className="px-4 py-3">
          <CardTitle className={`${textStyles.subtitle} dark:text-gray-100 flex items-center gap-2`}>
            <Target className="w-3.5 h-3.5 text-wedo-green-bright" />
            Metas de Diversidade 2025
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex items-start gap-3">
            <CheckCircle className="w-3.5 h-3.5 mt-0.5 flex-shrink-0 text-wedo-green" />
            <div className="flex-1">
              <p className="text-sm font-open-sans font-semibold text-gray-950 dark:text-gray-50 mb-1">PCD: 8.2% atingido (meta 5%)</p>
              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                <div className="h-2 rounded-full bg-wedo-green" style={{ width: '100%' }}></div>
              </div>
            </div>
          </div>
          <div className="flex items-start gap-3">
            <TrendingUp className="w-3.5 h-3.5 mt-0.5 flex-shrink-0 text-gray-600 dark:text-gray-400" />
            <div className="flex-1">
              <p className="text-sm font-open-sans font-semibold text-gray-950 dark:text-gray-50 mb-1">Mulheres em Tech: 48% (meta 50%)</p>
              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                <div className="h-2 rounded-full bg-gray-700 dark:bg-gray-300" style={{ width: '96%' }}></div>
              </div>
            </div>
          </div>
          <div className="flex items-start gap-3">
            <AlertTriangle className="w-3.5 h-3.5 mt-0.5 flex-shrink-0 text-wedo-orange" />
            <div className="flex-1">
              <p className="text-sm font-open-sans font-semibold text-gray-950 dark:text-gray-50 mb-1">Liderança Negra: 12% (meta 20%)</p>
              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                <div className="h-2 rounded-full bg-wedo-orange" style={{ width: '60%' }}></div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

// NPS & Satisfação Dashboard
function NPSDashboard() {
  return (
    <div className="space-y-3">
      {/* KPIs de NPS */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-2.5">
        <Card className={`${cardStyles.default} dark:bg-gray-950 dark:border-gray-800`}>
          <CardContent className="p-3">
            <div className="flex items-start justify-between mb-2">
              <p className={`${textStyles.bodySmall} dark:text-gray-400`}>NPS Geral</p>
              <Award className="w-3.5 h-3.5 text-wedo-green" />
            </div>
            <div className="text-xl font-inter font-bold text-gray-950 dark:text-gray-50">+67</div>
            <p className={`${textStyles.bodySmall} text-green-600 dark:text-green-400 mt-1`}>Excelente (acima de 50)</p>
          </CardContent>
        </Card>

        <Card className={`${cardStyles.default} dark:bg-gray-950 dark:border-gray-800`}>
          <CardContent className="p-3">
            <div className="flex items-start justify-between mb-2">
              <p className={`${textStyles.bodySmall} dark:text-gray-400`}>Promotores</p>
              <CheckCircle className="w-3.5 h-3.5 text-wedo-green" />
            </div>
            <div className="text-xl font-inter font-bold text-gray-950 dark:text-gray-50">72%</div>
            <p className={`${textStyles.bodySmall} text-green-600 dark:text-green-400 mt-1`}>64 de 89 respostas</p>
          </CardContent>
        </Card>

        <Card className={`${cardStyles.default} dark:bg-gray-950 dark:border-gray-800`}>
          <CardContent className="p-3">
            <div className="flex items-start justify-between mb-2">
              <p className={`${textStyles.bodySmall} dark:text-gray-400`}>Neutros</p>
              <Activity className="w-3.5 h-3.5 text-gray-800 dark:text-gray-200" />
            </div>
            <div className="text-xl font-inter font-bold text-gray-950 dark:text-gray-50">23%</div>
            <p className={`${textStyles.bodySmall} dark:text-gray-400 mt-1`}>21 de 89 respostas</p>
          </CardContent>
        </Card>

        <Card className={`${cardStyles.default} dark:bg-gray-950 dark:border-gray-800`}>
          <CardContent className="p-3">
            <div className="flex items-start justify-between mb-2">
              <p className={`${textStyles.bodySmall} dark:text-gray-400`}>Detratores</p>
              <AlertTriangle className="w-3.5 h-3.5 text-wedo-magenta" />
            </div>
            <div className="text-xl font-inter font-bold text-gray-950 dark:text-gray-50">5%</div>
            <p className={`${textStyles.bodySmall} text-red-600 dark:text-red-400 mt-1`}>4 de 89 respostas</p>
          </CardContent>
        </Card>
      </div>

      {/* Distribuição NPS */}
      <Card className="border-gray-200 dark:border-gray-800 rounded-md bg-white dark:bg-gray-950">
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
                <span className="text-xs font-open-sans text-gray-800 dark:text-gray-200">Promotores (9-10)</span>
              </div>
              <span className="text-sm font-inter font-bold text-gray-950 dark:text-gray-50">72%</span>
            </div>
            <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3">
              <div className="h-3 rounded-full bg-wedo-green" style={{ width: '72%' }}></div>
            </div>
          </div>

          {/* Neutros */}
          <div className="space-y-1.5">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-gray-400"></div>
                <span className="text-xs font-open-sans text-gray-800 dark:text-gray-200">Neutros (7-8)</span>
              </div>
              <span className="text-sm font-inter font-bold text-gray-950 dark:text-gray-50">23%</span>
            </div>
            <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3">
              <div className="h-3 rounded-full bg-gray-400" style={{ width: '23%' }}></div>
            </div>
          </div>

          {/* Detratores */}
          <div className="space-y-1.5">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-wedo-magenta"></div>
                <span className="text-xs font-open-sans text-gray-800 dark:text-gray-200">Detratores (0-6)</span>
              </div>
              <span className="text-sm font-inter font-bold text-gray-950 dark:text-gray-50">5%</span>
            </div>
            <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3">
              <div className="h-3 rounded-full bg-wedo-magenta" style={{ width: '5%' }}></div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Satisfação por Etapa */}
      <Card className="border-gray-200 dark:border-gray-800 rounded-md bg-white dark:bg-gray-950">
        <CardHeader className="px-4 py-3">
          <CardTitle className="text-xs font-sans font-open-sans font-semibold text-gray-950 dark:text-gray-50">
            Satisfação por Etapa do Processo
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          <div className="flex items-center justify-between p-2 bg-gray-50 dark:bg-gray-800/50 rounded">
            <span className="text-xs font-open-sans text-gray-800 dark:text-gray-200">Aplicação Inicial</span>
            <div className="flex items-center gap-2">
              <Badge className="bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400 text-xs tracking-tight">Excelente</Badge>
              <span className="text-sm font-inter font-bold">9.2</span>
            </div>
          </div>
          <div className="flex items-center justify-between p-2 bg-gray-50 dark:bg-gray-800/50 rounded">
            <span className="text-xs font-open-sans text-gray-800 dark:text-gray-200">Comunicação</span>
            <div className="flex items-center gap-2">
 <Badge className="bg-gray-100 text-gray-900 dark:text-gray-300 text-xs tracking-tight">Muito Bom</Badge>
              <span className="text-sm font-inter font-bold">8.8</span>
            </div>
          </div>
          <div className="flex items-center justify-between p-2 bg-gray-50 dark:bg-gray-800/50 rounded">
            <span className="text-xs font-open-sans text-gray-800 dark:text-gray-200">Entrevistas</span>
            <div className="flex items-center gap-2">
              <Badge className="bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400 text-xs tracking-tight">Muito Bom</Badge>
              <span className="text-sm font-inter font-bold">8.6</span>
            </div>
          </div>
          <div className="flex items-center justify-between p-2 bg-gray-50 dark:bg-gray-800/50 rounded">
            <span className="text-xs font-open-sans text-gray-800 dark:text-gray-200">Tempo de Resposta</span>
            <div className="flex items-center gap-2">
              <Badge className="bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400 text-xs tracking-tight">Bom</Badge>
              <span className="text-sm font-inter font-bold">7.9</span>
            </div>
          </div>
          <div className="flex items-center justify-between p-2 bg-gray-50 dark:bg-gray-800/50 rounded">
            <span className="text-xs font-open-sans text-gray-800 dark:text-gray-200">Feedback Pós-Entrevista</span>
            <div className="flex items-center gap-2">
              <Badge className="bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400 text-xs tracking-tight">Regular</Badge>
              <span className="text-sm font-inter font-bold">6.8</span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Principais Feedbacks */}
      <Card className="border-gray-200 dark:border-gray-800 rounded-md bg-white dark:bg-gray-950">
        <CardHeader className="px-4 py-3">
          <CardTitle className={`${textStyles.subtitle} dark:text-gray-100 flex items-center gap-2`}>
            <Brain className="w-3.5 h-3.5 text-wedo-cyan" />
            Insights dos Candidatos
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex items-start gap-3">
            <CheckCircle className="w-3.5 h-3.5 mt-0.5 flex-shrink-0 text-wedo-green" />
            <p className="text-sm font-open-sans text-gray-800 dark:text-gray-200">
              <strong>Pontos Positivos:</strong> Plataforma intuitiva e processo transparente elogiados por 89% dos candidatos.
            </p>
          </div>
          <div className="flex items-start gap-3">
            <AlertTriangle className="w-3.5 h-3.5 mt-0.5 flex-shrink-0 text-wedo-orange" />
            <p className="text-sm font-open-sans text-gray-800 dark:text-gray-200">
              <strong>Oportunidade de Melhoria:</strong> Tempo de resposta pós-entrevista pode ser reduzido. Meta: responder em até 3 dias.
            </p>
          </div>
          <div className="flex items-start gap-3">
            <TrendingUp className="w-3.5 h-3.5 mt-0.5 flex-shrink-0 text-gray-600 dark:text-gray-400" />
            <p className="text-sm font-open-sans text-gray-800 dark:text-gray-200">
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
    color: '#9860D1'
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
    color: '#60D186'
  },
  {
    id: 'scheduling',
    name: 'Scheduling',
    description: 'Agendamento de entrevistas',
    status: 'active',
    actionsToday: 34,
    successRate: 99,
    avgResponseTime: 1.5,
    color: '#D19960'
  },
  {
    id: 'communication',
    name: 'Communication',
    description: 'E-mails e mensagens',
    status: 'idle',
    actionsToday: 89,
    successRate: 97,
    avgResponseTime: 0.5,
    color: '#D160AB'
  },
  {
    id: 'analytics',
    name: 'Analytics',
    description: 'Relatórios e insights',
    status: 'active',
    actionsToday: 23,
    successRate: 100,
    avgResponseTime: 3.2,
    color: '#60D1C5'
  },
  {
    id: 'recruiter-assistant',
    name: 'Recruiter Assistant',
    description: 'Assistente do recrutador',
    status: 'busy',
    actionsToday: 156,
    successRate: 95,
    avgResponseTime: 1.1,
    color: '#8860D1'
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

function AgentActivityDashboard() {
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
      case 'error': return 'bg-red-500'
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
      case 'success': return 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
      case 'pending': return 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400'
      case 'error': return 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'
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
        <h1 className={`${textStyles.title} dark:text-gray-100 flex items-center gap-2`}>
          <Brain className="w-3.5 h-3.5 text-wedo-cyan" />
          Atividade dos Agentes
        </h1>
        <p className={`${textStyles.bodySmall} dark:text-gray-400 mt-1`}>
          Monitoramento e métricas dos 7 agentes IA especializados da plataforma LIA
        </p>
      </div>

      {/* A. Seção KPIs (4 cards no topo) */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-2.5">
        {/* Total de Ações Hoje */}
        <Card className={`${cardStyles.default} dark:bg-gray-950 dark:border-gray-800`}>
          <CardContent className="p-3">
            <div className="flex items-start justify-between mb-2">
              <p className={`${textStyles.bodySmall} dark:text-gray-400`}>Total de Ações Hoje</p>
              <Activity className="w-3.5 h-3.5 text-gray-600 dark:text-gray-400" />
            </div>
            <div className="text-xl font-inter font-bold text-gray-950 dark:text-gray-50">{totalActionsToday}</div>
 <p className={`${textStyles.bodySmall} text-gray-900 dark:text-gray-300 mt-1`}>+18% vs. ontem</p>
          </CardContent>
        </Card>

        {/* Taxa de Sucesso */}
        <Card className={`${cardStyles.default} dark:bg-gray-950 dark:border-gray-800`}>
          <CardContent className="p-3">
            <div className="flex items-start justify-between mb-2">
              <p className={`${textStyles.bodySmall} dark:text-gray-400`}>Taxa de Sucesso</p>
              <CheckCircle className="w-3.5 h-3.5 text-wedo-green" />
            </div>
            <div className="text-xl font-inter font-bold text-gray-950 dark:text-gray-50">{avgSuccessRate}%</div>
            <p className={`${textStyles.bodySmall} text-green-600 dark:text-green-400 mt-1`}>Média geral dos agentes</p>
          </CardContent>
        </Card>

        {/* Tempo Médio de Resposta */}
        <Card className={`${cardStyles.default} dark:bg-gray-950 dark:border-gray-800`}>
          <CardContent className="p-3">
            <div className="flex items-start justify-between mb-2">
              <p className={`${textStyles.bodySmall} dark:text-gray-400`}>Tempo Médio de Resposta</p>
              <TrendingUp className="w-3.5 h-3.5 text-wedo-orange" />
            </div>
            <div className="text-xl font-inter font-bold text-gray-950 dark:text-gray-50">{avgResponseTime}s</div>
            <p className={`${textStyles.bodySmall} text-orange-600 dark:text-orange-400 mt-1`}>-0.3s vs. semana passada</p>
          </CardContent>
        </Card>

        {/* Agentes Ativos */}
        <Card className={`${cardStyles.default} dark:bg-gray-950 dark:border-gray-800`}>
          <CardContent className="p-3">
            <div className="flex items-start justify-between mb-2">
              <p className={`${textStyles.bodySmall} dark:text-gray-400`}>Agentes Ativos</p>
              <Brain className="w-3.5 h-3.5 text-wedo-purple" />
            </div>
            <div className="text-xl font-inter font-bold text-gray-950 dark:text-gray-50">{activeAgents}/7</div>
            <p className={`${textStyles.bodySmall} text-purple-600 dark:text-purple-400 mt-1`}>Sistema operacional</p>
          </CardContent>
        </Card>
      </div>

      {/* B. Grid de Status dos Agentes */}
      <Card className={`${cardStyles.default} dark:bg-gray-950 dark:border-gray-700`}>
        <CardHeader className="px-4 py-3">
          <CardTitle className={`${textStyles.subtitle} dark:text-gray-100 flex items-center gap-2`}>
            <Brain className="w-3.5 h-3.5 text-wedo-cyan" />
            Status dos Agentes Especializados
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 xl:grid-cols-7 gap-2.5">
            {agentsData.map((agent) => (
              <div 
                key={agent.id}
                className="p-3 bg-gray-50 dark:bg-gray-900 rounded-md border border-gray-200 dark:border-gray-800 hover:border-gray-900 dark:hover:border-gray-50 dark:hover:border-gray-900 dark:hover:border-gray-50 transition-colors"
              >
                {/* Header com status */}
                <div className="flex items-start justify-between mb-2">
                  <div className="flex items-center gap-1.5">
                    <div className={`w-2 h-2 rounded-full ${getStatusColor(agent.status)}`}></div>
                    <span className={`${textStyles.description} dark:text-gray-400`}>{getStatusLabel(agent.status)}</span>
                  </div>
                </div>

                {/* Nome e descrição */}
                <div className="mb-2">
                  <p className="font-semibold font-open-sans text-sm text-gray-950 dark:text-gray-50 truncate" style={{ color: agent.color }}>
                    {agent.name}
                  </p>
                  <p className="text-xs tracking-tight font-open-sans text-gray-800 dark:text-gray-200 truncate">
                    {agent.description}
                  </p>
                </div>

                {/* Métricas do dia */}
                <div className="space-y-1.5">
                  <div className="flex items-center justify-between">
                    <span className={`${textStyles.description} dark:text-gray-400`}>Ações</span>
                    <span className="text-xs font-inter font-bold text-gray-950 dark:text-gray-50">{agent.actionsToday}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className={`${textStyles.description} dark:text-gray-400`}>Sucesso</span>
                    <span className="text-xs font-inter font-bold text-green-600 dark:text-green-400">{agent.successRate}%</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className={`${textStyles.description} dark:text-gray-400`}>Tempo</span>
                    <span className="text-xs font-inter font-bold text-gray-950 dark:text-gray-50">{agent.avgResponseTime}s</span>
                  </div>
                </div>

                {/* Sparkline simplificado (visual bar) */}
                <div className="mt-2 flex items-end gap-0.5 h-6">
                  {[40, 65, 45, 80, 55, 70, 90, 60].map((value, idx) => (
                    <div 
                      key={idx}
                      className="flex-1 rounded-sm transition-all"
                      style={{ 
                        height: `${value}%`, 
                        backgroundColor: agent.color,
                        opacity: 0.4 + (idx * 0.08)
                      }}
                    ></div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* C. Gráfico de Atividade por Agente */}
      <Card className={`${cardStyles.default} dark:bg-gray-950 dark:border-gray-700`}>
        <CardHeader className="px-4 py-3">
          <CardTitle className={`${textStyles.subtitle} dark:text-gray-100 flex items-center gap-2`}>
            <BarChart3 className="w-3.5 h-3.5 text-gray-600 dark:text-gray-400" />
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
                        <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: agent.color }}></div>
                        <span className="text-xs font-open-sans font-medium text-gray-800 dark:text-gray-200">{agent.name}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-inter font-bold text-gray-950 dark:text-gray-50">{agent.actionsToday}</span>
                        <Badge className={`text-xs tracking-tight ${
                          agent.successRate >= 98 ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400' :
 agent.successRate >= 95 ? 'bg-gray-100 text-gray-900 dark:text-gray-300' :
                          'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400'
                        }`}>
                          {agent.successRate}%
                        </Badge>
                      </div>
                    </div>
                    <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                      <div 
                        className="h-2 rounded-full transition-all"
                        style={{ width: `${percentage}%`, backgroundColor: agent.color }}
                      ></div>
                    </div>
                  </div>
                )
              })}
          </div>
        </CardContent>
      </Card>

      {/* D. Tabela de Ações Recentes */}
      <Card className={`${cardStyles.default} dark:bg-gray-950 dark:border-gray-700`}>
        <CardHeader className="px-4 py-3">
          <div className="flex items-center justify-between">
            <CardTitle className={`${textStyles.subtitle} dark:text-gray-100 flex items-center gap-2`}>
              <Activity className="w-3.5 h-3.5 text-gray-600 dark:text-gray-400" />
              Ações Recentes
            </CardTitle>
            
            {/* Filtros */}
            <div className="flex items-center gap-2">
              <select
                value={selectedAgentFilter}
                onChange={(e) => setSelectedAgentFilter(e.target.value)}
                className="text-xs font-open-sans px-2 py-1 rounded-full border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 text-gray-800 dark:text-gray-200"
              >
                <option value="all">Todos os Agentes</option>
                {agentsData.map(agent => (
                  <option key={agent.id} value={agent.id}>{agent.name}</option>
                ))}
              </select>
              
              <select
                value={selectedTypeFilter}
                onChange={(e) => setSelectedTypeFilter(e.target.value)}
                className="text-xs font-open-sans px-2 py-1 rounded-full border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 text-gray-800 dark:text-gray-200"
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
                <tr className="border-b border-gray-200 dark:border-gray-800">
                  <th className="text-left py-2 px-2 text-xs tracking-tight font-open-sans font-semibold text-gray-800 dark:text-gray-200 uppercase">Hora</th>
                  <th className="text-left py-2 px-2 text-xs tracking-tight font-open-sans font-semibold text-gray-800 dark:text-gray-200 uppercase">Agente</th>
                  <th className="text-left py-2 px-2 text-xs tracking-tight font-open-sans font-semibold text-gray-800 dark:text-gray-200 uppercase">Tipo</th>
                  <th className="text-left py-2 px-2 text-xs tracking-tight font-open-sans font-semibold text-gray-800 dark:text-gray-200 uppercase">Descrição</th>
                  <th className="text-left py-2 px-2 text-xs tracking-tight font-open-sans font-semibold text-gray-800 dark:text-gray-200 uppercase">Status</th>
                </tr>
              </thead>
              <tbody>
                {filteredActions.map((action) => {
                  const agent = agentsData.find(a => a.id === action.agentId)
                  return (
                    <tr key={action.id} className="border-b border-gray-100 dark:border-gray-800 hover:bg-gray-50 dark:hover:bg-gray-900/50">
                      <td className="py-2 px-2">
                        <span className="text-xs font-inter font-medium text-gray-950 dark:text-gray-50">{action.time}</span>
                      </td>
                      <td className="py-2 px-2">
                        <div className="flex items-center gap-1.5">
                          <div className="w-2 h-2 rounded-full" style={{ backgroundColor: agent?.color || '#111827' }}></div>
                          <span className="text-xs font-open-sans font-medium text-gray-800 dark:text-gray-200">{action.agentName}</span>
                        </div>
                      </td>
                      <td className="py-2 px-2">
                        <Badge variant="outline" className="text-xs tracking-tight font-open-sans">
                          {action.type}
                        </Badge>
                      </td>
                      <td className="py-2 px-2">
                        <span className="text-xs font-open-sans text-gray-600 dark:text-gray-400 line-clamp-1 max-w-[200px]">{action.description}</span>
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
 <Activity className="w-8 h-8 mx-auto text-gray-300 dark:text-gray-200 mb-2" />
              <p className="text-xs font-open-sans text-gray-800 dark:text-gray-200">Nenhuma ação encontrada com os filtros selecionados</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Insights dos Agentes */}
      <Card className={`${cardStyles.default} dark:bg-gray-900 dark:border-gray-800`}>
        <CardHeader className="px-4 py-3">
          <CardTitle className={`${textStyles.title} dark:text-gray-100 flex items-center gap-2`}>
            <Brain className="w-3.5 h-3.5 text-wedo-cyan" />
            Insights do Sistema de Agentes
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex items-start gap-3">
            <CheckCircle className="w-3.5 h-3.5 mt-0.5 flex-shrink-0 text-wedo-green" />
            <p className="text-sm font-open-sans text-gray-800 dark:text-gray-200">
              <strong>Performance excelente:</strong> Agente Screening lidera com 215 ações e 96% de sucesso. Análise de CVs automatizada reduzindo tempo em 78%.
            </p>
          </div>
          <div className="flex items-start gap-3">
            <TrendingUp className="w-3.5 h-3.5 mt-0.5 flex-shrink-0 text-gray-600 dark:text-gray-400" />
            <p className="text-sm font-open-sans text-gray-800 dark:text-gray-200">
              <strong>Agente Sourcing ativo:</strong> 128 buscas realizadas hoje. Pipeline de talentos ampliado em 23 perfis qualificados.
            </p>
          </div>
          <div className="flex items-start gap-3">
            <AlertTriangle className="w-3.5 h-3.5 mt-0.5 flex-shrink-0 text-wedo-orange" />
            <p className="text-sm font-open-sans text-gray-800 dark:text-gray-200">
              <strong>Atenção:</strong> Agente Communication em modo idle. Considere revisar filas de mensagens pendentes.
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
