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


export function ModelosTrabalhoPlaceholder() {
  return (
    <div className="space-y-3">
      {/* Header */}
      <div>
        <h1 className={`${textStyles.title} flex items-center gap-2`}>
          <PieChart className="w-3.5 h-3.5 text-wedo-orange" />
          Modelos de Trabalho
        </h1>
        <p className={`${textStyles.bodySmall} mt-1`}>
          Distribuição entre Remoto, Híbrido e Presencial - análises regionais e por departamento
        </p>
      </div>

      {/* Distribuição Geral + Satisfação */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-3">
        {/* Distribuição Geral */}
        <Card className="border-lia-border-subtle dark:border-lia-border-subtle lg:col-span-2">
          <CardHeader className="pb-3">
            <CardTitle className="text-base font-sans font-open-sans font-semibold text-lia-text-primary">
              Distribuição Geral de Modelos de Trabalho
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Remoto */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-gray-900"></div>
                  <span className="text-sm font-open-sans text-lia-text-primary">Remoto</span>
                </div>
                <span className="text-sm font-inter font-bold text-lia-text-primary">42%</span>
              </div>
              <div className="w-full bg-gray-200 dark:bg-lia-bg-elevated rounded-full h-3">
                <div className="h-3 rounded-full bg-gray-900 w-[42%]"></div>
              </div>
            </div>

            {/* Híbrido */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-wedo-green-bright"></div>
                  <span className="text-sm font-open-sans text-lia-text-primary">Híbrido</span>
                </div>
                <span className="text-sm font-inter font-bold text-lia-text-primary">35%</span>
              </div>
              <div className="w-full bg-gray-200 dark:bg-lia-bg-elevated rounded-full h-3">
                <div className="h-3 rounded-full bg-wedo-green-bright w-[35%]"></div>
              </div>
            </div>

            {/* Presencial */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-wedo-orange"></div>
                  <span className="text-sm font-open-sans text-lia-text-primary">Presencial</span>
                </div>
                <span className="text-sm font-inter font-bold text-lia-text-primary">23%</span>
              </div>
              <div className="w-full bg-gray-200 dark:bg-lia-bg-elevated rounded-full h-3">
                <div className="h-3 rounded-full bg-wedo-orange w-[23%]"></div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Satisfação Geral */}
        <Card className={`${cardStyles.default} dark:bg-lia-bg-primary dark:border-lia-border-subtle`}>
          <CardHeader className="pb-3">
            <CardTitle className="text-base font-sans font-open-sans font-semibold text-lia-text-primary">
              Satisfação Geral
            </CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col items-center justify-center py-6">
            <div className="text-2xl font-inter font-bold text-lia-text-primary mb-2">
              8.4<span className="text-sm text-lia-text-primary">/10</span>
            </div>
            <p className="text-sm font-open-sans text-lia-text-secondary text-center mb-4">
              Média de satisfação com modelo de trabalho
            </p>
            <Badge className="bg-status-success/15 text-status-success dark:bg-status-success/30 dark:text-status-success font-open-sans">
              <CheckCircle className="w-3 h-3 mr-1" />
              Acima da meta (8.0)
            </Badge>
          </CardContent>
        </Card>
      </div>

      {/* Análise Regional */}
      <Card className={`${cardStyles.default} dark:bg-lia-bg-primary dark:border-lia-border-subtle`}>
        <CardHeader className="pb-3">
          <CardTitle className={`${textStyles.subtitle} flex items-center gap-2`}>
            <MapPin className="w-3.5 h-3.5 text-lia-text-primary" />
            Distribuição por Região
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            {/* São Paulo */}
            <div className="space-y-3 p-4 bg-gray-50 dark:bg-lia-bg-secondary/50 rounded-md">
              <div className="flex items-center justify-between">
                <h4 className="font-open-sans font-semibold text-lia-text-primary">São Paulo</h4>
                <Badge variant="outline" className="text-xs tracking-tight font-inter">523 vagas</Badge>
              </div>
              <div className="space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <span className="font-open-sans text-lia-text-secondary">Remoto</span>
                  <span className="font-inter font-bold text-lia-text-primary">48%</span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="font-open-sans text-lia-text-secondary">Híbrido</span>
                  <span className="font-inter font-bold text-lia-text-primary">35%</span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="font-open-sans text-lia-text-secondary">Presencial</span>
                  <span className="font-inter font-bold text-lia-text-primary">17%</span>
                </div>
              </div>
            </div>

            {/* Rio de Janeiro */}
            <div className="space-y-3 p-4 bg-gray-50 dark:bg-lia-bg-secondary/50 rounded-md">
              <div className="flex items-center justify-between">
                <h4 className="font-open-sans font-semibold text-lia-text-primary">Rio de Janeiro</h4>
                <Badge variant="outline" className="text-xs tracking-tight font-inter">287 vagas</Badge>
              </div>
              <div className="space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <span className="font-open-sans text-lia-text-secondary">Remoto</span>
                  <span className="font-inter font-bold text-lia-text-primary">38%</span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="font-open-sans text-lia-text-secondary">Híbrido</span>
                  <span className="font-inter font-bold text-lia-text-primary">42%</span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="font-open-sans text-lia-text-secondary">Presencial</span>
                  <span className="font-inter font-bold text-lia-text-primary">20%</span>
                </div>
              </div>
            </div>

            {/* Minas Gerais */}
            <div className="space-y-3 p-4 bg-gray-50 dark:bg-lia-bg-secondary/50 rounded-md">
              <div className="flex items-center justify-between">
                <h4 className="font-open-sans font-semibold text-lia-text-primary">Minas Gerais</h4>
                <Badge variant="outline" className="text-xs tracking-tight font-inter">194 vagas</Badge>
              </div>
              <div className="space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <span className="font-open-sans text-lia-text-secondary">Remoto</span>
                  <span className="font-inter font-bold text-lia-text-primary">35%</span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="font-open-sans text-lia-text-secondary">Híbrido</span>
                  <span className="font-inter font-bold text-lia-text-primary">28%</span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="font-open-sans text-lia-text-secondary">Presencial</span>
                  <span className="font-inter font-bold text-lia-text-primary">37%</span>
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Análise por Departamento */}
      <Card className={`${cardStyles.default} dark:bg-lia-bg-primary dark:border-lia-border-subtle`}>
        <CardHeader className="pb-3">
          <CardTitle className={`${textStyles.subtitle} flex items-center gap-2`}>
            <Building className="w-3.5 h-3.5 text-lia-text-primary" />
            Distribuição por Departamento
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {/* Tecnologia */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm font-open-sans font-medium text-lia-text-primary">Tecnologia</span>
                <span className="text-xs tracking-tight font-inter text-lia-text-primary">78% Remoto • 18% Híbrido • 4% Presencial</span>
              </div>
              <div className="flex w-full h-2 rounded-full overflow-hidden bg-gray-200 dark:bg-lia-bg-elevated">
                <div className="bg-gray-900 w-[78%]"></div>
                <div className="bg-wedo-green-bright w-[18%]"></div>
                <div className="bg-wedo-orange w-[4%]"></div>
              </div>
            </div>

            {/* Vendas */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm font-open-sans font-medium text-lia-text-primary">Vendas</span>
                <span className="text-xs tracking-tight font-inter text-lia-text-primary">15% Remoto • 62% Híbrido • 23% Presencial</span>
              </div>
              <div className="flex w-full h-2 rounded-full overflow-hidden bg-gray-200 dark:bg-lia-bg-elevated">
                <div className="bg-gray-900 w-[15%]"></div>
                <div className="bg-wedo-green-bright w-[62%]"></div>
                <div className="bg-wedo-orange w-[23%]"></div>
              </div>
            </div>

            {/* Financeiro */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm font-open-sans font-medium text-lia-text-primary">Financeiro</span>
                <span className="text-xs tracking-tight font-inter text-lia-text-primary">32% Remoto • 51% Híbrido • 17% Presencial</span>
              </div>
              <div className="flex w-full h-2 rounded-full overflow-hidden bg-gray-200 dark:bg-lia-bg-elevated">
                <div className="bg-gray-900 w-[32%]"></div>
                <div className="bg-wedo-green-bright w-[51%]"></div>
                <div className="bg-wedo-orange w-[17%]"></div>
              </div>
            </div>

            {/* Operações */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm font-open-sans font-medium text-lia-text-primary">Operações</span>
                <span className="text-xs tracking-tight font-inter text-lia-text-primary">8% Remoto • 25% Híbrido • 67% Presencial</span>
              </div>
              <div className="flex w-full h-2 rounded-full overflow-hidden bg-gray-200 dark:bg-lia-bg-elevated">
                <div className="bg-gray-900 w-[8%]"></div>
                <div className="bg-wedo-green-bright w-[25%]"></div>
                <div className="bg-wedo-orange w-[67%]"></div>
              </div>
            </div>

            {/* Marketing */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm font-open-sans font-medium text-lia-text-primary">Marketing</span>
                <span className="text-xs tracking-tight font-inter text-lia-text-primary">55% Remoto • 38% Híbrido • 7% Presencial</span>
              </div>
              <div className="flex w-full h-2 rounded-full overflow-hidden bg-gray-200 dark:bg-lia-bg-elevated">
                <div className="bg-gray-900 w-[55%]"></div>
                <div className="bg-wedo-green-bright w-[38%]"></div>
                <div className="bg-wedo-orange w-[7%]"></div>
              </div>
            </div>

            {/* RH */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm font-open-sans font-medium text-lia-text-primary">Recursos Humanos</span>
                <span className="text-xs tracking-tight font-inter text-lia-text-primary">42% Remoto • 45% Híbrido • 13% Presencial</span>
              </div>
              <div className="flex w-full h-2 rounded-full overflow-hidden bg-gray-200 dark:bg-lia-bg-elevated">
                <div className="bg-gray-900 w-[42%]"></div>
                <div className="bg-wedo-green-bright w-[45%]"></div>
                <div className="bg-wedo-orange w-[13%]"></div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Insights e Recomendações */}
      <Card className={`${cardStyles.default} dark:bg-lia-bg-primary dark:border-lia-border-subtle`}>
        <CardHeader className="px-4 py-3">
          <CardTitle className={`${textStyles.title} flex items-center gap-2`}>
            <Lightbulb className="w-3.5 h-3.5 text-wedo-purple" />
            Insights da LIA
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex items-start gap-3">
            <CheckCircle className="w-3.5 h-3.5 mt-0.5 flex-shrink-0 text-wedo-green-bright" />
            <p className="text-sm font-open-sans text-lia-text-primary">
              <strong>Tecnologia lidera em trabalho remoto:</strong> 78% das vagas tech são remotas, refletindo tendência do mercado
            </p>
          </div>
          <div className="flex items-start gap-3">
            <AlertTriangle className="w-3.5 h-3.5 mt-0.5 flex-shrink-0 text-wedo-orange" />
            <p className="text-sm font-open-sans text-lia-text-primary">
              <strong>Operações predominantemente presencial:</strong> 67% exigem presença física - considere otimizar processos
            </p>
          </div>
          <div className="flex items-start gap-3">
            <TrendingUp className="w-3.5 h-3.5 mt-0.5 flex-shrink-0 text-lia-text-secondary" />
            <p className="text-sm font-open-sans text-lia-text-primary">
              <strong>Modelo híbrido em alta:</strong> Vendas (62%) e Financeiro (51%) preferem equilíbrio entre remoto e presencial
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

// 5. Funil & Performance
