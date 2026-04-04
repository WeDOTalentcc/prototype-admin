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
import dynamic from "next/dynamic"
import { LoadingDashboard } from "@/components/ui/loading"
const BigFiveDashboardPage = dynamic(() => import("../big-five-dashboard-page").then(m => ({ default: m.BigFiveDashboardPage })), { ssr: false, loading: () => <LoadingDashboard /> })
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


import { BigFiveAnalyticsDashboard } from './BigFiveAnalyticsDashboard'
import { DiversidadeInclusaoDashboard } from './DiversidadeInclusaoDashboard'
import { NPSDashboard } from './NPSDashboard'

export function PeopleAnalyticsPlaceholder() {
  const [activeSubDashboard, setActiveSubDashboard] = useState<'bigfive' | 'diversidade' | 'nps'>('bigfive')

  return (
    <div className="space-y-3">
      {/* Header com Navegação Interna */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className={`${textStyles.title} flex items-center gap-2`}>
            <Users className="w-3.5 h-3.5 text-wedo-green" />
            People Analytics
          </h1>
          <p className={`${textStyles.bodySmall} mt-1`}>
            Big Five, Diversidade & Inclusão, NPS e Satisfação de candidatos
          </p>
        </div>

        {/* Tabs de Navegação */}
        <div className="flex gap-2">
          <Button
            // @ts-ignore // TODO: fix type
            // @ts-ignore // TODO: fix type
            variant={activeSubDashboard === 'bigfive' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setActiveSubDashboard('bigfive')}
            className="text-xs h-7 px-3 font-open-sans"
          >
            <Brain className="w-3 h-3 mr-1.5 text-wedo-cyan" />
            Big Five
          </Button>
          <Button
            // @ts-ignore // TODO: fix type
            variant={activeSubDashboard === 'diversidade' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setActiveSubDashboard('diversidade')}
            className="text-xs h-7 px-3 font-open-sans"
          >
            <Heart className="w-3 h-3 mr-1.5" />
            Diversidade
          </Button>
          <Button
            // @ts-ignore // TODO: fix type
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
