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


export function WarRoomOperacionalPlaceholder() {
  return (
    <div className="space-y-3">
      {/* Header */}
      <div>
        <h1 className="text-sm leading-tight font-semibold font-['Open_Sans',sans-serif] text-lia-text-primary dark:text-lia-text-primary flex items-center gap-2">
          <AlertTriangle className="w-3.5 h-3.5 text-wedo-magenta" />
          War Room Operacional
        </h1>
        <p className="text-lia-text-secondary dark:text-lia-text-tertiary mt-1 font-open-sans text-xs">
          Alertas críticos, ações urgentes e pipelines em risco que exigem atenção imediata
        </p>
      </div>

      {/* Alertas Críticos KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        <Card className="border-status-error/30 dark:border-status-error/30 bg-status-error/10 dark:bg-status-error/20">
          <CardContent className="p-3">
            <div className="flex items-start justify-between mb-2">
              <p className="text-xs tracking-tight font-open-sans text-status-error dark:text-status-error font-semibold">VAGAS EM RISCO</p>
              <AlertTriangle className="w-3.5 h-3.5 text-status-error" />
            </div>
            <div className="text-2xl font-inter font-bold text-status-error dark:text-status-error">8</div>
            <p className={`${textStyles.bodySmall} text-status-error dark:text-status-error mt-1`}>&gt;45 dias sem candidatos</p>
          </CardContent>
        </Card>

        <Card className="border-wedo-orange/30 dark:border-wedo-orange/30 bg-wedo-orange/10 dark:bg-wedo-orange/20">
          <CardContent className="p-3">
            <div className="flex items-start justify-between mb-2">
              <p className="text-xs tracking-tight font-open-sans text-wedo-orange dark:text-wedo-orange font-semibold">AÇÕES URGENTES</p>
              <Target className="w-3.5 h-3.5 text-wedo-orange" />
            </div>
            <div className="text-2xl font-inter font-bold text-wedo-orange dark:text-wedo-orange">23</div>
            <p className={`${textStyles.bodySmall} text-wedo-orange dark:text-wedo-orange mt-1`}>Aguardando ação RH</p>
          </CardContent>
        </Card>

        <Card className="border-status-warning/30 dark:border-status-warning/30 bg-status-warning/10 dark:bg-status-warning/20">
          <CardContent className="p-3">
            <div className="flex items-start justify-between mb-2">
              <p className="text-xs tracking-tight font-open-sans text-status-warning dark:text-status-warning font-semibold">EM ESPERA</p>
              <Users className="w-3.5 h-3.5 text-status-warning" />
            </div>
            <div className="text-2xl font-inter font-bold text-status-warning dark:text-status-warning">47</div>
            <p className={`${textStyles.bodySmall} text-status-warning dark:text-status-warning mt-1`}>&gt;5 dias sem feedback</p>
          </CardContent>
        </Card>
      </div>

      {/* Vagas Críticas Detalhadas */}
      <Card className="border-status-error/30 dark:border-status-error/30">
        <CardHeader className="pb-3 bg-status-error/10 dark:bg-status-error/20">
          <CardTitle className={`${textStyles.subtitle} dark:text-lia-text-primary flex items-center gap-2`}>
            <AlertTriangle className="w-3.5 h-3.5 text-status-error" />
            Vagas Críticas - Ação Imediata Necessária
          </CardTitle>
        </CardHeader>
        <CardContent className="pt-4 space-y-3">
          <div className="p-4 bg-status-error/10 dark:bg-status-error/20 rounded-md border-l-4 border-status-error/30">
            <div className="flex items-start justify-between mb-2">
              <div>
                <p className="font-open-sans font-semibold text-lia-text-primary dark:text-lia-text-primary">Vaga #2847 - Senior ML Engineer</p>
                <p className="text-sm font-open-sans text-lia-text-secondary dark:text-lia-text-tertiary mt-1">
                  62 dias aberta • 0 candidatos qualificados • Prioridade MÁXIMA
                </p>
              </div>
              <Badge className="bg-status-error/15 text-status-error dark:bg-status-error/30 dark:text-status-error font-inter shrink-0">CRÍTICO</Badge>
            </div>
            <div className="flex items-center gap-2 mt-3">
              <Button size="sm" className="bg-status-error hover:bg-status-error text-white font-open-sans">Revisar Requisitos</Button>
              <Button size="sm" variant="outline" className="font-open-sans">Buscar LIA Database</Button>
            </div>
          </div>

          <div className="p-4 bg-wedo-orange/10 dark:bg-wedo-orange/20 rounded-md border-l-4 border-wedo-orange/30">
            <div className="flex items-start justify-between mb-2">
              <div>
                <p className="font-open-sans font-semibold text-lia-text-primary dark:text-lia-text-primary">Vaga #3012 - Tech Lead Backend</p>
                <p className="text-sm font-open-sans text-lia-text-secondary dark:text-lia-text-tertiary mt-1">51 dias aberta • 3 candidatos em avaliação • Pipeline lento</p>
              </div>
              <Badge className="bg-wedo-orange/15 text-wedo-orange dark:bg-wedo-orange/30 dark:text-wedo-orange font-inter shrink-0">URGENTE</Badge>
            </div>
            <div className="flex items-center gap-2 mt-3">
              <Button size="sm" className="bg-wedo-orange hover:bg-wedo-orange/10 text-white font-open-sans">Acelerar Processo</Button>
              <Button size="sm" variant="outline" className="font-open-sans">Ver Candidatos</Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Gargalos e Recomendações LIA */}
      <Card className="border-status-error/30 dark:border-status-error/30 rounded-md bg-white dark:bg-lia-bg-primary">
        <CardHeader className="px-4 py-3">
          <CardTitle className={`${textStyles.title} dark:text-lia-text-primary flex items-center gap-2`}>
            <Brain className="w-3.5 h-3.5 text-wedo-cyan" />
            Recomendações Urgentes da LIA
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex items-start gap-3">
            <AlertTriangle className="w-3.5 h-3.5 mt-0.5 flex-shrink-0 text-status-error" />
            <p className="text-sm font-open-sans text-lia-text-primary dark:text-lia-text-primary">
              <strong>Vaga #2847 (ML Engineer) precisa de ação imediata:</strong> 62 dias sem candidatos. LIA sugere flexibilizar requisitos de "PhD obrigatório" para "Mestrado + 5 anos exp."
            </p>
          </div>
          <div className="flex items-start gap-3">
            <Target className="w-3.5 h-3.5 mt-0.5 flex-shrink-0 text-wedo-orange" />
            <p className="text-sm font-open-sans text-lia-text-primary dark:text-lia-text-primary">
              <strong>Processo Tech Lead está 73% mais lento que a média:</strong> Gargalo identificado na aprovação do gestor. Sugere reunião de alinhamento.
            </p>
          </div>
          <div className="flex items-start gap-3">
            <Users className="w-3.5 h-3.5 mt-0.5 flex-shrink-0 text-status-warning" />
            <p className="text-sm font-open-sans text-lia-text-primary dark:text-lia-text-primary">
              <strong>47 candidatos em espera podem desistir:</strong> LIA identificou padrão histórico de 65% desistência após 7 dias sem contato. Agendar entrevistas urgente.
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

// 8. Voice Screening Dashboard
