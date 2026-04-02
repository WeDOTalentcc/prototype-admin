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


export function BigFiveAnalyticsDashboard() {
  return (
    <div className="space-y-3">
      {/* KPIs Principais */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-2.5">
        <Card className={`${cardStyles.default} dark:bg-lia-bg-primary dark:border-lia-border-subtle`}>
          <CardContent className="p-3">
            <div className="flex items-start justify-between mb-2">
              <p className={`${textStyles.bodySmall}`}>Candidatos Avaliados</p>
              <Users className="w-3.5 h-3.5 text-wedo-purple" />
            </div>
            <div className="text-xl font-inter font-bold text-lia-text-primary">247</div>
            <p className={`${textStyles.bodySmall} text-wedo-purple dark:text-wedo-purple mt-1`}>+12% vs. mês anterior</p>
          </CardContent>
        </Card>

        <Card className={`${cardStyles.default} dark:bg-lia-bg-primary dark:border-lia-border-subtle`}>
          <CardContent className="p-3">
            <div className="flex items-start justify-between mb-2">
              <p className={`${textStyles.bodySmall}`}>Acurácia de Predição</p>
              <Target className="w-3.5 h-3.5 text-wedo-green" />
            </div>
            <div className="text-xl font-inter font-bold text-lia-text-primary">89%</div>
            <p className={`${textStyles.bodySmall} text-status-success dark:text-status-success mt-1`}>vs. 72% método tradicional</p>
          </CardContent>
        </Card>

        <Card className={`${cardStyles.default} dark:bg-lia-bg-primary dark:border-lia-border-subtle`}>
          <CardContent className="p-3">
            <div className="flex items-start justify-between mb-2">
              <p className={`${textStyles.bodySmall}`}>Redução de Turnover</p>
              <TrendingUp className="w-3.5 h-3.5 text-lia-text-secondary" />
            </div>
            <div className="text-xl font-inter font-bold text-lia-text-primary">-24%</div>
 <p className={`${textStyles.bodySmall} text-lia-text-primary mt-1`}>com Big Five screening</p>
          </CardContent>
        </Card>

        <Card className={`${cardStyles.default} dark:bg-lia-bg-primary dark:border-lia-border-subtle`}>
          <CardContent className="p-3">
            <div className="flex items-start justify-between mb-2">
              <p className={`${textStyles.bodySmall}`}>Performance Média</p>
              <Award className="w-3.5 h-3.5 text-wedo-orange" />
            </div>
            <div className="text-xl font-inter font-bold text-lia-text-primary">8.9</div>
            <p className={`${textStyles.bodySmall} text-wedo-orange dark:text-wedo-orange mt-1`}>contratados via Big Five</p>
          </CardContent>
        </Card>
      </div>

      {/* Distribuição por Traço */}
      <Card className="border-lia-border-subtle dark:border-lia-border-subtle rounded-md bg-lia-bg-primary dark:bg-lia-bg-primary">
        <CardHeader className="px-4 py-3">
          <CardTitle className="text-xs font-sans font-open-sans font-semibold text-lia-text-primary">
            Distribuição dos Traços de Personalidade
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {/* Abertura */}
          <div className="space-y-1.5">
            <div className="flex items-center justify-between">
              <span className="text-xs font-open-sans text-lia-text-primary">Abertura</span>
              <span className="text-sm font-inter font-bold text-lia-text-primary">68%</span>
            </div>
            <div className="w-full bg-lia-interactive-active dark:bg-lia-bg-elevated rounded-full h-2">
              <div className="h-2 rounded-full bg-wedo-purple w-[68%]"></div>
            </div>
          </div>

          {/* Conscienciosidade */}
          <div className="space-y-1.5">
            <div className="flex items-center justify-between">
              <span className="text-xs font-open-sans text-lia-text-primary">Conscienciosidade</span>
              <span className="text-sm font-inter font-bold text-lia-text-primary">74%</span>
            </div>
            <div className="w-full bg-lia-interactive-active dark:bg-lia-bg-elevated rounded-full h-2">
              <div className="h-2 rounded-full bg-wedo-green-bright w-[74%]"></div>
            </div>
          </div>

          {/* Extroversão */}
          <div className="space-y-1.5">
            <div className="flex items-center justify-between">
              <span className="text-xs font-open-sans text-lia-text-primary">Extroversão</span>
              <span className="text-sm font-inter font-bold text-lia-text-primary">61%</span>
            </div>
            <div className="w-full bg-lia-interactive-active dark:bg-lia-bg-elevated rounded-full h-2">
              <div className="h-2 rounded-full bg-lia-btn-primary-bg w-[61%]"></div>
            </div>
          </div>

          {/* Amabilidade */}
          <div className="space-y-1.5">
            <div className="flex items-center justify-between">
              <span className="text-xs font-open-sans text-lia-text-primary">Amabilidade</span>
              <span className="text-sm font-inter font-bold text-lia-text-primary">72%</span>
            </div>
            <div className="w-full bg-lia-interactive-active dark:bg-lia-bg-elevated rounded-full h-2">
              <div className="h-2 rounded-full bg-wedo-orange w-[72%]"></div>
            </div>
          </div>

          {/* Estabilidade Emocional */}
          <div className="space-y-1.5">
            <div className="flex items-center justify-between">
              <span className="text-xs font-open-sans text-lia-text-primary">Estabilidade Emocional</span>
              <span className="text-sm font-inter font-bold text-lia-text-primary">55%</span>
            </div>
            <div className="w-full bg-lia-interactive-active dark:bg-lia-bg-elevated rounded-full h-2">
              <div className="h-2 rounded-full bg-wedo-magenta w-[55%]"></div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Correlação com Performance */}
      <Card className="border-lia-border-subtle dark:border-lia-border-subtle rounded-md bg-lia-bg-primary dark:bg-lia-bg-primary">
        <CardHeader className="px-4 py-3">
          <CardTitle className={`${textStyles.subtitle} flex items-center gap-2`}>
            <BarChart3 className="w-3.5 h-3.5 text-lia-text-secondary" />
            Correlação Traços × Performance
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            <div className="flex items-center justify-between p-2 bg-lia-bg-secondary dark:bg-lia-bg-secondary/50 rounded-md">
              <span className="text-xs font-open-sans text-lia-text-primary">Conscienciosidade</span>
              <div className="flex items-center gap-2">
                <Badge className="bg-status-success/15 text-status-success dark:bg-status-success/30 dark:text-status-success text-xs tracking-tight">Muito Alta</Badge>
                <span className="text-sm font-inter font-bold">0.84</span>
              </div>
            </div>
            <div className="flex items-center justify-between p-2 bg-lia-bg-secondary dark:bg-lia-bg-secondary/50 rounded-md">
              <span className="text-xs font-open-sans text-lia-text-primary">Estabilidade</span>
              <div className="flex items-center gap-2">
 <Badge className="bg-lia-bg-tertiary text-lia-text-primary text-xs tracking-tight">Alta</Badge>
                <span className="text-sm font-inter font-bold">0.71</span>
              </div>
            </div>
            <div className="flex items-center justify-between p-2 bg-lia-bg-secondary dark:bg-lia-bg-secondary/50 rounded-md">
              <span className="text-xs font-open-sans text-lia-text-primary">Abertura</span>
              <div className="flex items-center gap-2">
                <Badge className="bg-wedo-purple/15 text-wedo-purple dark:bg-wedo-purple/30 dark:text-wedo-purple text-xs tracking-tight">Alta</Badge>
                <span className="text-sm font-inter font-bold">0.67</span>
              </div>
            </div>
            <div className="flex items-center justify-between p-2 bg-lia-bg-secondary dark:bg-lia-bg-secondary/50 rounded-md">
              <span className="text-xs font-open-sans text-lia-text-primary">Amabilidade</span>
              <div className="flex items-center gap-2">
                <Badge className="bg-wedo-orange/15 text-wedo-orange dark:bg-wedo-orange/30 dark:text-wedo-orange text-xs tracking-tight">Alta</Badge>
                <span className="text-sm font-inter font-bold">0.63</span>
              </div>
            </div>
            <div className="flex items-center justify-between p-2 bg-lia-bg-secondary dark:bg-lia-bg-secondary/50 rounded-md">
              <span className="text-xs font-open-sans text-lia-text-primary">Extroversão</span>
              <div className="flex items-center gap-2">
 <Badge className="bg-lia-bg-tertiary text-lia-text-primary dark:bg-lia-bg-secondary text-xs tracking-tight">Moderada</Badge>
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
