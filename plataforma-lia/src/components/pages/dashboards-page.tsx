"use client"

import React, { useState } from "react"
import dynamic from "next/dynamic"
import type { ComponentType, CSSProperties } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import {
  BarChart3, TrendingUp, Brain, Target, Users, PieChart,
  Heart, Award, CheckCircle, Activity, MapPin, Building,
  Lightbulb, AlertTriangle, ChevronLeft, ChevronRight, Lock, Unlock, Phone
} from "lucide-react"
const BigFiveDashboardPage = dynamic(() => import("./big-five-dashboard-page").then(m => ({ default: m.BigFiveDashboardPage })), {
  ssr: false,
  loading: () => <div className="h-64 bg-lia-bg-tertiary animate-pulse motion-reduce:animate-none rounded-lg" />,
})
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

import { LoadingDashboard } from "@/components/ui/loading"
const IndicadoresEstrategicosPlaceholder = dynamic(() => import("./dashboards-page/IndicadoresEstrategicosPlaceholder").then(m => ({ default: m.IndicadoresEstrategicosPlaceholder })), { ssr: false, loading: () => <LoadingDashboard /> })
const PrevisoesIAPlaceholder = dynamic(() => import("./dashboards-page/PrevisoesIAPlaceholder").then(m => ({ default: m.PrevisoesIAPlaceholder })), { ssr: false, loading: () => <LoadingDashboard /> })
const PeopleAnalyticsPlaceholder = dynamic(() => import("./dashboards-page/PeopleAnalyticsPlaceholder").then(m => ({ default: m.PeopleAnalyticsPlaceholder })), { ssr: false, loading: () => <LoadingDashboard /> })
const ModelosTrabalhoPlaceholder = dynamic(() => import("./dashboards-page/ModelosTrabalhoPlaceholder").then(m => ({ default: m.ModelosTrabalhoPlaceholder })), { ssr: false, loading: () => <LoadingDashboard /> })
const FunilPerformancePlaceholder = dynamic(() => import("./dashboards-page/FunilPerformancePlaceholder").then(m => ({ default: m.FunilPerformancePlaceholder })), { ssr: false, loading: () => <LoadingDashboard /> })
const WarRoomOperacionalPlaceholder = dynamic(() => import("./dashboards-page/WarRoomOperacionalPlaceholder").then(m => ({ default: m.WarRoomOperacionalPlaceholder })), { ssr: false, loading: () => <LoadingDashboard /> })
const VoiceScreeningDashboard = dynamic(() => import("./dashboards-page/VoiceScreeningDashboard").then(m => ({ default: m.VoiceScreeningDashboard })), { ssr: false, loading: () => <LoadingDashboard /> })
const AnaliseCompetenciasPlaceholder = dynamic(() => import("./dashboards-page/AnaliseCompetenciasPlaceholder").then(m => ({ default: m.AnaliseCompetenciasPlaceholder })), { ssr: false, loading: () => <LoadingDashboard /> })
const BigFiveAnalyticsDashboard = dynamic(() => import("./dashboards-page/BigFiveAnalyticsDashboard").then(m => ({ default: m.BigFiveAnalyticsDashboard })), { ssr: false, loading: () => <LoadingDashboard /> })
const DiversidadeInclusaoDashboard = dynamic(() => import("./dashboards-page/DiversidadeInclusaoDashboard").then(m => ({ default: m.DiversidadeInclusaoDashboard })), { ssr: false, loading: () => <LoadingDashboard /> })
const NPSDashboard = dynamic(() => import("./dashboards-page/NPSDashboard").then(m => ({ default: m.NPSDashboard })), { ssr: false, loading: () => <LoadingDashboard /> })
const AgentActivityDashboard = dynamic(() => import("./dashboards-page/AgentActivityDashboard").then(m => ({ default: m.AgentActivityDashboard })), { ssr: false, loading: () => <LoadingDashboard /> })

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
                <p className="text-center text-lia-text-secondary">
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
    <div className="flex gap-3 h-full px-3 pt-3 pb-6 bg-lia-bg-primary dark:bg-lia-bg-primary overflow-hidden">
      {/* Menu Lateral de Dashboards - Retrátil com Auto-Expand */}
      <div 
        className={`bg-lia-bg-secondary dark:bg-lia-bg-secondary border border-lia-border-subtle dark:border-lia-border-subtle rounded-md p-4 space-y-4 shrink-0 transition-colors motion-reduce:transition-none duration-300 ${
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
                    <Activity className="w-3.5 h-3.5 text-lia-text-secondary" />
                    Dashboards
                  </h2>
                  <p className={`${textStyles.description}`}>
                    Selecione um dashboard
                  </p>
                </div>
              )}
              <button
                onClick={toggleLock}
                className="p-1.5 rounded-md hover:bg-lia-bg-tertiary dark:hover:bg-lia-btn-primary-hover transition-colors motion-reduce:transition-none"
                title={isMenuLocked ? "Destravar menu (auto-expand habilitado)" : "Travar menu expandido"}
              >
                {isMenuLocked ? (
                  <Lock className="w-3.5 h-3.5 text-lia-text-secondary" />
                ) : (
                  <Unlock className="w-3.5 h-3.5 text-lia-text-primary" />
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
                    className={`w-full ${!shouldExpand ? 'flex justify-center' : 'text-left'} p-2 rounded-md transition-colors motion-reduce:transition-none ${
                      isActive
                        ? 'bg-lia-bg-tertiary dark:bg-lia-bg-secondary border border-lia-border-default dark:border-lia-border-default'
                        : 'hover:bg-lia-bg-secondary dark:hover:bg-lia-btn-primary-hover/50 border border-transparent'
                    }`}
                  >
                    {!shouldExpand ? (
                      // Modo colapsado: apenas ícone
                      <div className={`p-1.5 rounded-md ${
                        isActive
                          ? 'bg-lia-bg-primary dark:bg-lia-bg-primary'
                          : 'bg-lia-bg-tertiary dark:bg-lia-bg-secondary'
                      }`}>
                        <Icon 
                          className="w-3.5 h-3.5" 
                          style={{color: item.color}}
                        />
                      </div>
                    ) : (
                      // Modo expandido: layout completo
                      <div className="flex items-start justify-between gap-2">
                        <div className="flex items-start gap-2 flex-1 min-w-0">
                          <div className={`p-1.5 rounded-md ${
                            isActive
                              ? 'bg-lia-bg-primary dark:bg-lia-bg-primary'
                              : 'bg-lia-bg-tertiary dark:bg-lia-bg-secondary'
                          }`}>
                            <Icon 
                              className="w-3.5 h-3.5" 
                              style={{color: item.color}}
                            />
                          </div>
                          <div className="flex-1 min-w-0">
                            <h3 className={`${textStyles.label} mb-0.5 ${
                              isActive
                                ? 'text-lia-text-primary'
                                : ''
                            }`}>
                              {item.label}
                            </h3>
                            <p className={`${textStyles.description} line-clamp-2`}>
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
