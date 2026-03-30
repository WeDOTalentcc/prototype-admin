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


export function DiversidadeInclusaoDashboard() {
  return (
    <div className="space-y-3">
      {/* KPIs de Diversidade */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-2.5">
        <Card className={`${cardStyles.default} dark:bg-gray-950 dark:border-gray-800`}>
          <CardContent className="p-3">
            <div className="flex items-start justify-between mb-2">
              <p className={`${textStyles.bodySmall} dark:text-lia-text-tertiary`}>Pessoas com Deficiência</p>
              <Heart className="w-3.5 h-3.5 text-wedo-orange" />
            </div>
            <div className="text-xl font-inter font-bold text-gray-950 dark:text-gray-50">8.2%</div>
            <p className={`${textStyles.bodySmall} text-wedo-orange dark:text-wedo-orange mt-1`}>Meta: 5% (excedida)</p>
          </CardContent>
        </Card>

        <Card className={`${cardStyles.default} dark:bg-gray-950 dark:border-gray-800`}>
          <CardContent className="p-3">
            <div className="flex items-start justify-between mb-2">
              <p className={`${textStyles.bodySmall} dark:text-lia-text-tertiary`}>Equidade de Gênero</p>
              <Users className="w-3.5 h-3.5 text-wedo-purple" />
            </div>
            <div className="text-xl font-inter font-bold text-gray-950 dark:text-gray-50">48%</div>
            <p className={`${textStyles.bodySmall} text-wedo-purple dark:text-wedo-purple mt-1`}>mulheres em tech</p>
          </CardContent>
        </Card>

        <Card className={`${cardStyles.default} dark:bg-gray-950 dark:border-gray-800`}>
          <CardContent className="p-3">
            <div className="flex items-start justify-between mb-2">
              <p className={`${textStyles.bodySmall} dark:text-lia-text-tertiary`}>Diversidade Racial</p>
              <Users className="w-3.5 h-3.5 text-wedo-green" />
            </div>
            <div className="text-xl font-inter font-bold text-gray-950 dark:text-gray-50">42%</div>
            <p className={`${textStyles.bodySmall} text-status-success dark:text-status-success mt-1`}>população não-branca</p>
          </CardContent>
        </Card>

        <Card className={`${cardStyles.default} dark:bg-gray-950 dark:border-gray-800`}>
          <CardContent className="p-3">
            <div className="flex items-start justify-between mb-2">
              <p className={`${textStyles.bodySmall} dark:text-lia-text-tertiary`}>LGBTQIA+</p>
              <Heart className="w-3.5 h-3.5 text-gray-600 dark:text-lia-text-tertiary" />
            </div>
            <div className="text-xl font-inter font-bold text-gray-950 dark:text-gray-50">12%</div>
 <p className={`${textStyles.bodySmall} text-gray-900 dark:text-lia-text-secondary mt-1`}>auto-declarados</p>
          </CardContent>
        </Card>
      </div>

      {/* Distribuição de Gênero e Racial */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
        <Card className="border-lia-border-subtle dark:border-gray-800 rounded-md bg-white dark:bg-gray-950">
          <CardHeader className="px-4 py-3">
            <CardTitle className="text-xs font-sans font-open-sans font-semibold text-gray-950 dark:text-gray-50">
              Distribuição de Gênero por Cargo
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-open-sans text-gray-800 dark:text-lia-text-primary">C-Level</span>
                <div className="flex items-center gap-2">
                  <span className="text-sm font-inter text-wedo-purple">40% M</span>
                  <span className="text-sm font-inter text-gray-950 dark:text-gray-50">60% H</span>
                </div>
              </div>
              <div className="w-full bg-gray-200 dark:bg-lia-bg-elevated rounded-full h-2 flex overflow-hidden">
                <div className="h-2 bg-wedo-purple w-[40%]"></div>
                <div className="h-2 bg-gray-900 w-[60%]"></div>
              </div>
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-open-sans text-gray-800 dark:text-lia-text-primary">Gerência</span>
                <div className="flex items-center gap-2">
                  <span className="text-sm font-inter text-wedo-purple">45% M</span>
                  <span className="text-sm font-inter text-gray-950 dark:text-gray-50">55% H</span>
                </div>
              </div>
              <div className="w-full bg-gray-200 dark:bg-lia-bg-elevated rounded-full h-2 flex overflow-hidden">
                <div className="h-2 bg-wedo-purple w-[45%]"></div>
                <div className="h-2 bg-gray-900 w-[55%]"></div>
              </div>
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-open-sans text-gray-800 dark:text-lia-text-primary">Técnico</span>
                <div className="flex items-center gap-2">
                  <span className="text-sm font-inter text-wedo-purple">48% M</span>
                  <span className="text-sm font-inter text-gray-950 dark:text-gray-50">52% H</span>
                </div>
              </div>
              <div className="w-full bg-gray-200 dark:bg-lia-bg-elevated rounded-full h-2 flex overflow-hidden">
                <div className="h-2 bg-wedo-purple w-[48%]"></div>
                <div className="h-2 bg-gray-900 w-[52%]"></div>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="border-lia-border-subtle dark:border-gray-800 rounded-md bg-white dark:bg-gray-950">
          <CardHeader className="px-4 py-3">
            <CardTitle className="text-xs font-sans font-open-sans font-semibold text-gray-950 dark:text-gray-50">
              Diversidade Racial
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <div className="flex items-center justify-between p-2 bg-gray-50 dark:bg-lia-bg-secondary/50 rounded-md">
              <span className="text-xs font-open-sans text-gray-800 dark:text-lia-text-primary">Brancos</span>
              <span className="text-sm font-inter font-bold">58%</span>
            </div>
            <div className="flex items-center justify-between p-2 bg-gray-50 dark:bg-lia-bg-secondary/50 rounded-md">
              <span className="text-xs font-open-sans text-gray-800 dark:text-lia-text-primary">Pardos</span>
              <span className="text-sm font-inter font-bold">24%</span>
            </div>
            <div className="flex items-center justify-between p-2 bg-gray-50 dark:bg-lia-bg-secondary/50 rounded-md">
              <span className="text-xs font-open-sans text-gray-800 dark:text-lia-text-primary">Pretos</span>
              <span className="text-sm font-inter font-bold">14%</span>
            </div>
            <div className="flex items-center justify-between p-2 bg-gray-50 dark:bg-lia-bg-secondary/50 rounded-md">
              <span className="text-xs font-open-sans text-gray-800 dark:text-lia-text-primary">Amarelos</span>
              <span className="text-sm font-inter font-bold">3%</span>
            </div>
            <div className="flex items-center justify-between p-2 bg-gray-50 dark:bg-lia-bg-secondary/50 rounded-md">
              <span className="text-xs font-open-sans text-gray-800 dark:text-lia-text-primary">Indígenas</span>
              <span className="text-sm font-inter font-bold">1%</span>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Metas e Progresso */}
      <Card className="border-lia-border-subtle dark:border-gray-800 rounded-md bg-white dark:bg-gray-950">
        <CardHeader className="px-4 py-3">
          <CardTitle className={`${textStyles.subtitle} dark:text-lia-text-primary flex items-center gap-2`}>
            <Target className="w-3.5 h-3.5 text-wedo-green-bright" />
            Metas de Diversidade 2025
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex items-start gap-3">
            <CheckCircle className="w-3.5 h-3.5 mt-0.5 flex-shrink-0 text-wedo-green" />
            <div className="flex-1">
              <p className="text-sm font-open-sans font-semibold text-gray-950 dark:text-gray-50 mb-1">PCD: 8.2% atingido (meta 5%)</p>
              <div className="w-full bg-gray-200 dark:bg-lia-bg-elevated rounded-full h-2">
                <div className="h-2 rounded-full bg-wedo-green w-[100%]"></div>
              </div>
            </div>
          </div>
          <div className="flex items-start gap-3">
            <TrendingUp className="w-3.5 h-3.5 mt-0.5 flex-shrink-0 text-gray-600 dark:text-lia-text-tertiary" />
            <div className="flex-1">
              <p className="text-sm font-open-sans font-semibold text-gray-950 dark:text-gray-50 mb-1">Mulheres em Tech: 48% (meta 50%)</p>
              <div className="w-full bg-gray-200 dark:bg-lia-bg-elevated rounded-full h-2">
                <div className="h-2 rounded-full bg-gray-700 dark:bg-gray-300 w-[96%]"></div>
              </div>
            </div>
          </div>
          <div className="flex items-start gap-3">
            <AlertTriangle className="w-3.5 h-3.5 mt-0.5 flex-shrink-0 text-wedo-orange" />
            <div className="flex-1">
              <p className="text-sm font-open-sans font-semibold text-gray-950 dark:text-gray-50 mb-1">Liderança Negra: 12% (meta 20%)</p>
              <div className="w-full bg-gray-200 dark:bg-lia-bg-elevated rounded-full h-2">
                <div className="h-2 rounded-full bg-wedo-orange w-[60%]"></div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

// NPS & Satisfação Dashboard
