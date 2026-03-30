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


export function AnaliseCompetenciasPlaceholder() {
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
              <Badge className="bg-status-error/15 text-status-error dark:bg-status-error/30 dark:text-status-error font-inter font-bold">Gap 73%</Badge>
            </div>
            <div className="flex w-full h-3 rounded-full overflow-hidden bg-gray-200 dark:bg-gray-700">
              <div className="bg-wedo-green-bright w-[27%]" title="Disponível"></div>
              <div className="bg-wedo-magenta w-[73%]" title="Gap"></div>
            </div>
          </div>

          {/* DevOps - Gap Alto */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <div>
                <p className="font-open-sans font-semibold text-gray-950 dark:text-gray-50">DevOps / Cloud (AWS/Azure/GCP)</p>
                <p className={`${textStyles.description} dark:text-gray-400`}>Demanda: 194 vagas • Disponível: 87 candidatos</p>
              </div>
              <Badge className="bg-wedo-orange/15 text-wedo-orange dark:bg-wedo-orange/30 dark:text-wedo-orange font-inter font-bold">Gap 55%</Badge>
            </div>
            <div className="flex w-full h-3 rounded-full overflow-hidden bg-gray-200 dark:bg-gray-700">
              <div className="bg-wedo-green-bright w-[45%]" title="Disponível"></div>
              <div className="bg-wedo-orange w-[55%]" title="Gap"></div>
            </div>
          </div>

          {/* React - Gap Controlado */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <div>
                <p className="font-open-sans font-semibold text-gray-950 dark:text-gray-50">React.js / Frontend Moderno</p>
                <p className={`${textStyles.description} dark:text-gray-400`}>Demanda: 287 vagas • Disponível: 198 candidatos</p>
              </div>
              <Badge className="bg-status-warning/15 text-status-warning dark:bg-status-warning/30 dark:text-status-warning font-inter font-bold">Gap 31%</Badge>
            </div>
            <div className="flex w-full h-3 rounded-full overflow-hidden bg-gray-200 dark:bg-gray-700">
              <div className="bg-wedo-green-bright w-[69%]" title="Disponível"></div>
              <div className="bg-wedo-orange w-[31%]" title="Gap"></div>
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

            <div className="flex items-center justify-between p-3 bg-wedo-purple/10 dark:bg-wedo-purple/20 rounded-md border border-wedo-purple/30 dark:border-wedo-purple/30">
              <div>
                <p className="font-open-sans font-semibold text-gray-950 dark:text-gray-50 text-sm">LLM Fine-tuning</p>
                <p className={`${textStyles.description} dark:text-gray-400`}>18 vagas este mês</p>
              </div>
              <Badge className="bg-wedo-purple/15 text-wedo-purple dark:bg-wedo-purple/30 dark:text-wedo-purple font-inter font-bold">+280%</Badge>
            </div>

            <div className="flex items-center justify-between p-3 bg-status-success/10 dark:bg-status-success/20 rounded-md border border-status-success/30 dark:border-status-success/30">
              <div>
                <p className="font-open-sans font-semibold text-gray-950 dark:text-gray-50 text-sm">Kubernetes / K8s</p>
                <p className={`${textStyles.description} dark:text-gray-400`}>64 vagas este mês</p>
              </div>
              <Badge className="bg-status-success/15 text-status-success dark:bg-status-success/30 dark:text-status-success font-inter font-bold">+120%</Badge>
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
            <div className="p-3 bg-status-error/10 dark:bg-status-error/20 rounded-md border-l-4 border-status-error/30">
              <div className="flex items-start justify-between mb-1">
                <p className="font-open-sans font-semibold text-gray-950 dark:text-gray-50 text-sm">Machine Learning Bootcamp</p>
                <Badge className={`${badgeStyles.error} dark:bg-status-error/30 dark:text-status-error`}>CRÍTICO</Badge>
              </div>
              <p className={`${textStyles.bodySmall} dark:text-gray-400`}>
                Gap de 73% • ROI estimado: R$ 280k economia em headhunting
              </p>
            </div>

            <div className="p-3 bg-wedo-orange/10 dark:bg-wedo-orange/20 rounded-md border-l-4 border-wedo-orange/30">
              <div className="flex items-start justify-between mb-1">
                <p className="font-open-sans font-semibold text-gray-950 dark:text-gray-50 text-sm">DevOps & Cloud Certification</p>
                <Badge className="bg-wedo-orange/15 text-wedo-orange dark:bg-wedo-orange/30 dark:text-wedo-orange text-xs font-inter">ALTO</Badge>
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
