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


export function IndicadoresEstrategicosPlaceholder() {
  return (
    <div className="space-y-3">
      {/* Header */}
      <div>
        <h1 className={`${textStyles.title} flex items-center gap-2`}>
          <Target className="w-3.5 h-3.5 text-wedo-purple" />
          Indicadores Estratégicos
        </h1>
        <p className={`${textStyles.bodySmall} mt-1`}>
          KPIs de negócio, performance de recrutadores e retorno sobre investimento
        </p>
      </div>

      {/* KPIs Principais */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-2.5">
        {/* Taxa de Crescimento */}
        <Card className={`${cardStyles.default} dark:bg-lia-bg-primary dark:border-lia-border-subtle`}>
          <CardContent className="p-3">
            <div className="flex items-start justify-between mb-2">
              <p className={`${textStyles.bodySmall}`}>Taxa de Crescimento</p>
              <TrendingUp className="w-3.5 h-3.5 text-wedo-purple" />
            </div>
            <div className="text-xl font-inter font-bold text-lia-text-primary">+28%</div>
            <p className={`${textStyles.bodySmall} text-wedo-purple dark:text-wedo-purple mt-1`}>vs. trimestre anterior</p>
          </CardContent>
        </Card>

        {/* Eficiência Operacional */}
        <Card className={`${cardStyles.default} dark:bg-lia-bg-primary dark:border-lia-border-subtle`}>
          <CardContent className="p-3">
            <div className="flex items-start justify-between mb-2">
              <p className={`${textStyles.bodySmall}`}>Eficiência Operacional</p>
              <Activity className="w-3.5 h-3.5 text-lia-text-secondary" />
            </div>
            <div className="text-xl font-inter font-bold text-lia-text-primary">87%</div>
 <p className={`${textStyles.bodySmall} text-lia-text-primary mt-1`}>+5% este mês</p>
          </CardContent>
        </Card>

        {/* ROI do Processo */}
        <Card className={`${cardStyles.default} dark:bg-lia-bg-primary dark:border-lia-border-subtle`}>
          <CardContent className="p-3">
            <div className="flex items-start justify-between mb-2">
              <p className={`${textStyles.bodySmall}`}>ROI do Processo</p>
              <Target className="w-3.5 h-3.5 text-wedo-green" />
            </div>
            <div className="text-xl font-inter font-bold text-lia-text-primary">340%</div>
            <p className={`${textStyles.bodySmall} text-status-success dark:text-status-success mt-1`}>Meta: 250%</p>
          </CardContent>
        </Card>

        {/* Budget Utilizado */}
        <Card className={`${cardStyles.default} dark:bg-lia-bg-primary dark:border-lia-border-subtle`}>
          <CardContent className="p-3">
            <div className="flex items-start justify-between mb-2">
              <p className={`${textStyles.bodySmall}`}>Budget Utilizado</p>
              <BarChart3 className="w-3.5 h-3.5 text-wedo-orange" />
            </div>
            <div className="text-xl font-inter font-bold text-lia-text-primary">67%</div>
            <p className={`${textStyles.bodySmall} text-wedo-orange dark:text-wedo-orange mt-1`}>R$ 842k / R$ 1.25M</p>
          </CardContent>
        </Card>
      </div>

      {/* Performance de Recrutadores & Time to Fill */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-2.5">
        {/* Performance de Recrutadores */}
        <Card className={`${cardStyles.default} dark:bg-lia-bg-primary dark:border-lia-border-subtle`}>
          <CardHeader className="pb-3">
            <CardTitle className={`${textStyles.subtitle} flex items-center gap-2`}>
              <Users className="w-3.5 h-3.5 text-wedo-green" />
              Performance de Recrutadores
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex items-center justify-between p-3 bg-status-success/10 dark:bg-status-success/20 rounded-md border border-status-success/30 dark:border-status-success/30">
              <div className="flex-1">
                <p className={`${textStyles.subtitle} text-lia-text-primary`}>Mariana Silva</p>
                <p className={`${textStyles.description}`}>23 contratações • 94% taxa de aprovação</p>
              </div>
              <Badge className={`${badgeStyles.success} dark:bg-status-success/30 dark:text-status-success`}>
                🥇 Top 1
              </Badge>
            </div>

 <div className="flex items-center justify-between p-3 bg-lia-bg-secondary dark:bg-lia-bg-secondary rounded-md border border-lia-border-default dark:border-lia-border-subtle">
              <div className="flex-1">
                <p className={`${textStyles.subtitle} text-lia-text-primary`}>Roberto Costa</p>
                <p className={`${textStyles.description}`}>19 contratações • 89% taxa de aprovação</p>
              </div>
 <Badge className={`${badgeStyles.info} dark:bg-lia-bg-secondary`}>
                🥈 Top 2
              </Badge>
            </div>

            <div className="flex items-center justify-between p-3 bg-wedo-purple/10 dark:bg-wedo-purple/20 rounded-md border border-wedo-purple/30 dark:border-wedo-purple/30">
              <div className="flex-1">
                <p className={`${textStyles.subtitle} text-lia-text-primary`}>Juliana Mendes</p>
                <p className={`${textStyles.description}`}>17 contratações • 91% taxa de aprovação</p>
              </div>
              <Badge className="bg-wedo-purple/15 text-wedo-purple dark:bg-wedo-purple/30 dark:text-wedo-purple text-micro font-medium">
                🥉 Top 3
              </Badge>
            </div>

            <div className="flex items-center justify-between p-3 bg-lia-bg-secondary dark:bg-lia-bg-secondary/50 rounded-md border border-lia-border-subtle dark:border-lia-border-subtle">
              <div className="flex-1">
                <p className={`${textStyles.subtitle} text-lia-text-primary`}>Carlos Almeida</p>
                <p className={`${textStyles.description}`}>15 contratações • 86% taxa de aprovação</p>
              </div>
              <Badge className={badgeStyles.default}>
                Top 4
              </Badge>
            </div>
          </CardContent>
        </Card>

        {/* Time to Fill por Senioridade */}
        <Card className={`${cardStyles.default} dark:bg-lia-bg-primary dark:border-lia-border-subtle`}>
          <CardHeader className="pb-3">
            <CardTitle className={`${textStyles.subtitle} flex items-center gap-2`}>
              <Activity className="w-3.5 h-3.5 text-wedo-orange" />
              Time to Fill por Senioridade
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className={`${textStyles.subtitle}`}>Júnior</span>
                <div className="flex items-center gap-2">
                  <span className="text-sm font-inter font-bold text-lia-text-primary">12 dias</span>
                  <Badge className={`${badgeStyles.success} dark:bg-status-success/30 dark:text-status-success`}>
                    -2d
                  </Badge>
                </div>
              </div>
              <div className="w-full bg-lia-interactive-active dark:bg-lia-bg-elevated rounded-full h-2">
                <div className="h-2 rounded-full bg-wedo-green-bright w-[40%]"></div>
              </div>
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className={`${textStyles.subtitle}`}>Pleno</span>
                <div className="flex items-center gap-2">
                  <span className="text-sm font-inter font-bold text-lia-text-primary">18 dias</span>
 <Badge className={`${badgeStyles.info} dark:bg-lia-bg-secondary`}>
                    -3d
                  </Badge>
                </div>
              </div>
              <div className="w-full bg-lia-interactive-active dark:bg-lia-bg-elevated rounded-full h-2">
                <div className="h-2 rounded-full bg-lia-btn-primary-bg w-[60%]"></div>
              </div>
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className={`${textStyles.subtitle}`}>Sênior</span>
                <div className="flex items-center gap-2">
                  <span className="text-sm font-inter font-bold text-lia-text-primary">27 dias</span>
                  <Badge className={`${badgeStyles.warning} dark:bg-wedo-orange/30 dark:text-wedo-orange`}>
                    -1d
                  </Badge>
                </div>
              </div>
              <div className="w-full bg-lia-interactive-active dark:bg-lia-bg-elevated rounded-full h-2">
                <div className="h-2 rounded-full bg-wedo-orange w-[90%]"></div>
              </div>
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className={`${textStyles.subtitle}`}>Especialista/C-Level</span>
                <div className="flex items-center gap-2">
                  <span className="text-sm font-inter font-bold text-lia-text-primary">45 dias</span>
                  <Badge className="bg-wedo-purple/15 text-wedo-purple dark:bg-wedo-purple/30 dark:text-wedo-purple text-micro font-medium">
                    +2d
                  </Badge>
                </div>
              </div>
              <div className="w-full bg-lia-interactive-active dark:bg-lia-bg-elevated rounded-full h-2">
                <div className="h-2 rounded-full bg-wedo-purple w-[100%]"></div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Skills Gap Analysis */}
      <Card className={`${cardStyles.default} dark:bg-lia-bg-primary dark:border-lia-border-subtle`}>
        <CardHeader className="pb-3">
          <CardTitle className={`${textStyles.subtitle} flex items-center gap-2`}>
            <AlertTriangle className="w-3.5 h-3.5 text-wedo-magenta" />
            Skills Gap Analysis - Competências Mais Difíceis de Preencher
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <div className="p-4 bg-status-error/10 dark:bg-status-error/20 rounded-md border-l-4 border-status-error/30">
              <div className="flex items-start justify-between mb-2">
                <p className={`${textStyles.subtitle} text-lia-text-primary`}>Machine Learning Engineer</p>
                <Badge className={`${badgeStyles.error} dark:bg-status-error/30 dark:text-status-error`}>
                  Crítico
                </Badge>
              </div>
              <div className="space-y-1">
                <div className={`flex items-center justify-between ${textStyles.bodySmall}`}>
                  <span className="font-open-sans text-lia-text-secondary">Vagas abertas</span>
                  <span className="font-inter font-bold text-lia-text-primary">14</span>
                </div>
                <div className={`flex items-center justify-between ${textStyles.bodySmall}`}>
                  <span className="font-open-sans text-lia-text-secondary">Tempo médio</span>
                  <span className="font-inter font-bold text-status-error dark:text-status-error">62 dias</span>
                </div>
                <div className={`flex items-center justify-between ${textStyles.bodySmall}`}>
                  <span className="font-open-sans text-lia-text-secondary">Taxa sucesso</span>
                  <span className="font-inter font-bold text-lia-text-primary">28%</span>
                </div>
              </div>
            </div>

            <div className="p-4 bg-wedo-orange/10 dark:bg-wedo-orange/20 rounded-md border-l-4 border-wedo-orange/30">
              <div className="flex items-start justify-between mb-2">
                <p className="text-sm font-open-sans font-semibold text-lia-text-primary">DevOps Architect</p>
                <Badge className="bg-wedo-orange/15 text-wedo-orange dark:bg-wedo-orange/30 dark:text-wedo-orange text-xs font-inter">
                  Alto
                </Badge>
              </div>
              <div className="space-y-1">
                <div className={`flex items-center justify-between ${textStyles.bodySmall}`}>
                  <span className="font-open-sans text-lia-text-secondary">Vagas abertas</span>
                  <span className="font-inter font-bold text-lia-text-primary">9</span>
                </div>
                <div className={`flex items-center justify-between ${textStyles.bodySmall}`}>
                  <span className="font-open-sans text-lia-text-secondary">Tempo médio</span>
                  <span className="font-inter font-bold text-wedo-orange dark:text-wedo-orange">48 dias</span>
                </div>
                <div className={`flex items-center justify-between ${textStyles.bodySmall}`}>
                  <span className="font-open-sans text-lia-text-secondary">Taxa sucesso</span>
                  <span className="font-inter font-bold text-lia-text-primary">42%</span>
                </div>
              </div>
            </div>

            <div className="p-4 bg-status-warning/10 dark:bg-status-warning/20 rounded-md border-l-4 border-status-warning/30">
              <div className="flex items-start justify-between mb-2">
                <p className="text-sm font-open-sans font-semibold text-lia-text-primary">Security Specialist</p>
                <Badge className="bg-status-warning/15 text-status-warning dark:bg-status-warning/30 dark:text-status-warning text-xs font-inter">
                  Médio
                </Badge>
              </div>
              <div className="space-y-1">
                <div className={`flex items-center justify-between ${textStyles.bodySmall}`}>
                  <span className="font-open-sans text-lia-text-secondary">Vagas abertas</span>
                  <span className="font-inter font-bold text-lia-text-primary">7</span>
                </div>
                <div className={`flex items-center justify-between ${textStyles.bodySmall}`}>
                  <span className="font-open-sans text-lia-text-secondary">Tempo médio</span>
                  <span className="font-inter font-bold text-status-warning dark:text-status-warning">35 dias</span>
                </div>
                <div className={`flex items-center justify-between ${textStyles.bodySmall}`}>
                  <span className="font-open-sans text-lia-text-secondary">Taxa sucesso</span>
                  <span className="font-inter font-bold text-lia-text-primary">58%</span>
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Budget vs Performance */}
      <Card className={`${cardStyles.default} dark:bg-lia-bg-primary dark:border-lia-border-subtle`}>
        <CardHeader className="pb-3">
          <CardTitle className={`${textStyles.subtitle} flex items-center gap-2`}>
            <BarChart3 className="w-3.5 h-3.5 text-wedo-purple" />
            Budget vs Performance por Departamento
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <div>
                  <span className="text-sm font-open-sans font-medium text-lia-text-primary">Tecnologia</span>
                  <p className={`${textStyles.description}`}>R$ 420k investidos • 47 contratações</p>
                </div>
                <Badge className={`${badgeStyles.success} dark:bg-status-success/30 dark:text-status-success`}>
                  112% ROI
                </Badge>
              </div>
              <div className="flex w-full h-2 rounded-full overflow-hidden bg-lia-interactive-active dark:bg-lia-bg-elevated">
                <div className="bg-wedo-green-bright w-[85%]" title="Performance"></div>
                <div className="bg-wedo-orange w-[15%]" title="Orçamento não utilizado"></div>
              </div>
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <div>
                  <span className="text-sm font-open-sans font-medium text-lia-text-primary">Vendas</span>
                  <p className={`${textStyles.description}`}>R$ 186k investidos • 28 contratações</p>
                </div>
 <Badge className={`${badgeStyles.info} dark:bg-lia-bg-secondary`}>
                  94% ROI
                </Badge>
              </div>
              <div className="flex w-full h-2 rounded-full overflow-hidden bg-lia-interactive-active dark:bg-lia-bg-elevated">
                <div className="bg-lia-btn-primary-bg w-[72%]" title="Performance"></div>
                <div className="bg-wedo-orange w-[28%]" title="Orçamento não utilizado"></div>
              </div>
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <div>
                  <span className="text-sm font-open-sans font-medium text-lia-text-primary">Marketing</span>
                  <p className={`${textStyles.description}`}>R$ 124k investidos • 19 contratações</p>
                </div>
                <Badge className="bg-wedo-purple/15 text-wedo-purple dark:bg-wedo-purple/30 dark:text-wedo-purple text-micro font-medium">
                  87% ROI
                </Badge>
              </div>
              <div className="flex w-full h-2 rounded-full overflow-hidden bg-lia-interactive-active dark:bg-lia-bg-elevated">
                <div className="bg-wedo-purple w-[68%]" title="Performance"></div>
                <div className="bg-wedo-orange w-[32%]" title="Orçamento não utilizado"></div>
              </div>
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <div>
                  <span className="text-sm font-open-sans font-medium text-lia-text-primary">Operações</span>
                  <p className={`${textStyles.description}`}>R$ 112k investidos • 15 contratações</p>
                </div>
                <Badge className={`${badgeStyles.warning} dark:bg-wedo-orange/30 dark:text-wedo-orange`}>
                  76% ROI
                </Badge>
              </div>
              <div className="flex w-full h-2 rounded-full overflow-hidden bg-lia-interactive-active dark:bg-lia-bg-elevated">
                <div className="bg-wedo-orange w-[58%]" title="Performance"></div>
                <div className="bg-wedo-purple w-[42%]" title="Orçamento não utilizado"></div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Insights Estratégicos */}
      <Card className={`${cardStyles.default} dark:bg-lia-bg-primary dark:border-lia-border-subtle`}>
        <CardHeader className="px-4 py-3">
          <CardTitle className={`${textStyles.title} flex items-center gap-2`}>
            <Target className="w-3.5 h-3.5 text-wedo-purple" />
            Recomendações Estratégicas
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex items-start gap-3">
            <CheckCircle className="w-3.5 h-3.5 mt-0.5 flex-shrink-0 text-wedo-green-bright" />
            <p className="text-sm font-open-sans text-lia-text-primary">
              <strong>Tech lidera ROI:</strong> Departamento de Tecnologia com 112% ROI - modelo de referência para outros setores.
            </p>
          </div>
          <div className="flex items-start gap-3">
            <AlertTriangle className="w-3.5 h-3.5 mt-0.5 flex-shrink-0 text-wedo-magenta" />
            <p className="text-sm font-open-sans text-lia-text-primary">
              <strong>Skills gap crítico:</strong> ML Engineer leva 62 dias em média. Considere parcerias estratégicas com universidades.
            </p>
          </div>
          <div className="flex items-start gap-3">
            <TrendingUp className="w-3.5 h-3.5 mt-0.5 flex-shrink-0 text-wedo-purple" />
            <p className="text-sm font-open-sans text-lia-text-primary">
              <strong>Crescimento acelerado:</strong> +28% vs. trimestre anterior. Pipeline atual suporta expansão planejada.
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

// 2. Previsões & IA
