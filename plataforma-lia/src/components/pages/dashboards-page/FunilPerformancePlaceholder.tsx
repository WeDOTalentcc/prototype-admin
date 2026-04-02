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


export function FunilPerformancePlaceholder() {
  return (
    <div className="space-y-3">
      {/* Header */}
      <div>
        <h1 className={`${textStyles.title} flex items-center gap-2`}>
          <TrendingUp className="w-3.5 h-3.5 text-lia-text-secondary" />
          Funil & Performance
        </h1>
        <p className={`${textStyles.bodySmall} mt-1`}>
          Análise de conversão do pipeline, efetividade por canal e qualidade do processo
        </p>
      </div>

      {/* Funil de Conversão Visual */}
      <Card className={`${cardStyles.default} dark:bg-lia-bg-primary dark:border-lia-border-subtle`}>
        <CardHeader className="px-4 py-3">
          <CardTitle className={`${textStyles.title} flex items-center gap-2`}>
            <BarChart3 className="w-3.5 h-3.5 text-lia-text-secondary" />
            Funil de Conversão do Pipeline
          </CardTitle>
        </CardHeader>
        <CardContent className="pt-6">
          <div className="space-y-4">
            {/* Candidaturas Recebidas */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-open-sans font-semibold text-lia-text-primary">Candidaturas Recebidas</p>
                  <p className={`${textStyles.description}`}>100% do funil</p>
                </div>
                <span className="text-lg font-inter font-bold text-lia-text-primary">3.247</span>
              </div>
              <div className="w-full h-4 rounded-full" style={{background: 'linear-gradient(to right, var(--gray-700), var(--gray-600))'}}></div>
            </div>

            {/* Triagem LIA */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-open-sans font-semibold text-lia-text-primary">Triagem LIA Aprovada</p>
                  <p className={`${textStyles.description}`}>62% conversão</p>
                </div>
                <span className="text-lg font-inter font-bold text-lia-text-primary">2.013</span>
              </div>
              <div className="w-full bg-gray-200 dark:bg-lia-bg-elevated rounded-full h-4">
                <div className="h-4 rounded-full bg-gray-900 w-[62%]"></div>
              </div>
            </div>

            {/* Entrevistas Agendadas */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-open-sans font-semibold text-lia-text-primary">Entrevistas Agendadas</p>
                  <p className={`${textStyles.description}`}>38% conversão (total)</p>
                </div>
                <span className="text-lg font-inter font-bold text-lia-text-primary">1.234</span>
              </div>
              <div className="w-full bg-gray-200 dark:bg-lia-bg-elevated rounded-full h-4">
                <div className="h-4 rounded-full bg-wedo-purple w-[38%]"></div>
              </div>
            </div>

            {/* Ofertas Enviadas */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-open-sans font-semibold text-lia-text-primary">Ofertas Enviadas</p>
                  <p className={`${textStyles.description}`}>18% conversão (total)</p>
                </div>
                <span className="text-lg font-inter font-bold text-lia-text-primary">585</span>
              </div>
              <div className="w-full bg-gray-200 dark:bg-lia-bg-elevated rounded-full h-4">
                <div className="h-4 rounded-full bg-wedo-orange w-[18%]"></div>
              </div>
            </div>

            {/* Contratações Finalizadas */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-open-sans font-semibold text-lia-text-primary">Contratações Finalizadas</p>
                  <p className={`${textStyles.description}`}>12% conversão (total)</p>
                </div>
                <span className="text-lg font-inter font-bold text-status-success dark:text-status-success">389</span>
              </div>
              <div className="w-full bg-gray-200 dark:bg-lia-bg-elevated rounded-full h-4">
                <div className="h-4 rounded-full bg-wedo-green-bright w-[12%]"></div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Performance por Canal & Taxas de Conversão */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-2.5">
        {/* Performance por Canal de Divulgação */}
        <Card className={`${cardStyles.default} dark:bg-lia-bg-primary dark:border-lia-border-subtle`}>
          <CardHeader className="pb-3">
            <CardTitle className={`${textStyles.subtitle} flex items-center gap-2`}>
              <Target className="w-3.5 h-3.5 text-wedo-green" />
              Performance por Canal de Divulgação
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {/* LinkedIn */}
            <div className="p-3 bg-gray-50 dark:bg-lia-bg-secondary rounded-md border border-lia-border-subtle dark:border-lia-border-subtle">
              <div className="flex items-center justify-between mb-2">
                <div>
                  <p className="font-open-sans font-semibold text-lia-text-primary text-sm">LinkedIn Jobs</p>
                  <p className={`${textStyles.description}`}>1.247 candidaturas • 178 contratações</p>
                </div>
 <Badge className="bg-gray-100 text-lia-text-primary font-inter font-bold">
                  14.3%
                </Badge>
              </div>
              <div className="w-full bg-gray-200 dark:bg-lia-bg-elevated rounded-full h-2">
                <div className="h-2 rounded-full bg-gray-900" style={{width: '14.3%'}}></div>
              </div>
            </div>

            {/* Indicações */}
            <div className="p-3 bg-gray-50 dark:bg-lia-bg-secondary rounded-md border border-lia-border-subtle dark:border-lia-border-subtle">
              <div className="flex items-center justify-between mb-2">
                <div>
                  <p className="font-open-sans font-semibold text-lia-text-primary text-sm">Indicações Internas</p>
                  <p className={`${textStyles.description}`}>412 candidaturas • 94 contratações</p>
                </div>
                <Badge className="bg-status-success/15 text-status-success dark:bg-status-success/30 dark:text-status-success font-inter font-bold">
                  22.8%
                </Badge>
              </div>
              <div className="w-full bg-gray-200 dark:bg-lia-bg-elevated rounded-full h-2">
                <div className="h-2 rounded-full bg-wedo-green-bright" style={{width: '22.8%'}}></div>
              </div>
            </div>

            {/* Site Corporativo */}
            <div className="p-3 bg-gray-50 dark:bg-lia-bg-secondary rounded-md border border-lia-border-subtle dark:border-lia-border-subtle">
              <div className="flex items-center justify-between mb-2">
                <div>
                  <p className="font-open-sans font-semibold text-lia-text-primary text-sm">Site Corporativo</p>
                  <p className={`${textStyles.description}`}>894 candidaturas • 87 contratações</p>
                </div>
                <Badge className="bg-wedo-orange/15 text-wedo-orange dark:bg-wedo-orange/30 dark:text-wedo-orange font-inter font-bold">
                  9.7%
                </Badge>
              </div>
              <div className="w-full bg-gray-200 dark:bg-lia-bg-elevated rounded-full h-2">
                <div className="h-2 rounded-full bg-wedo-orange" style={{width: '9.7%'}}></div>
              </div>
            </div>

            {/* Job Boards */}
            <div className="p-3 bg-gray-50 dark:bg-lia-bg-secondary rounded-md border border-lia-border-subtle dark:border-lia-border-subtle">
              <div className="flex items-center justify-between mb-2">
                <div>
                  <p className="font-open-sans font-semibold text-lia-text-primary text-sm">Job Boards (Catho, Vagas.com)</p>
                  <p className={`${textStyles.description}`}>562 candidaturas • 24 contratações</p>
                </div>
                <Badge className="bg-wedo-purple/15 text-wedo-purple dark:bg-wedo-purple/30 dark:text-wedo-purple font-inter font-bold">
                  4.3%
                </Badge>
              </div>
              <div className="w-full bg-gray-200 dark:bg-lia-bg-elevated rounded-full h-2">
                <div className="h-2 rounded-full bg-wedo-purple" style={{width: '4.3%'}}></div>
              </div>
            </div>

            {/* Headhunting */}
            <div className="p-3 bg-gray-50 dark:bg-lia-bg-secondary rounded-md border border-lia-border-subtle dark:border-lia-border-subtle">
              <div className="flex items-center justify-between mb-2">
                <div>
                  <p className="font-open-sans font-semibold text-lia-text-primary text-sm">Headhunting Especializado</p>
                  <p className={`${textStyles.description}`}>132 candidaturas • 6 contratações</p>
                </div>
                <Badge className="bg-wedo-magenta/15 text-wedo-magenta dark:bg-wedo-magenta/30 dark:text-wedo-magenta font-inter font-bold">
                  4.5%
                </Badge>
              </div>
              <div className="w-full bg-gray-200 dark:bg-lia-bg-elevated rounded-full h-2">
                <div className="h-2 rounded-full bg-wedo-magenta" style={{width: '4.5%'}}></div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Qualidade do Processo */}
        <Card className={`${cardStyles.default} dark:bg-lia-bg-primary dark:border-lia-border-subtle`}>
          <CardHeader className="pb-3">
            <CardTitle className={`${textStyles.subtitle} flex items-center gap-2`}>
              <Award className="w-3.5 h-3.5 text-wedo-purple" />
              Indicadores de Qualidade
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Taxa de Aceitação de Ofertas */}
            <div className="p-4 bg-status-success/10 dark:bg-status-success/20 rounded-md">
              <div className="flex items-center justify-between mb-2">
                <p className="text-sm font-open-sans font-semibold text-lia-text-primary">Taxa de Aceitação de Ofertas</p>
                <div className="text-2xl font-inter font-bold text-status-success dark:text-status-success">66%</div>
              </div>
              <div className="w-full bg-gray-200 dark:bg-lia-bg-elevated rounded-full h-2">
                <div className="h-2 rounded-full bg-wedo-green-bright w-[66%]"></div>
              </div>
              <p className={`${textStyles.description} mt-2`}>Meta: 60% • +6% vs. meta</p>
            </div>

            {/* Tempo Médio de Fechamento */}
 <div className="p-4 bg-gray-50 dark:bg-lia-bg-secondary rounded-md">
              <div className="flex items-center justify-between mb-2">
                <p className="text-sm font-open-sans font-semibold text-lia-text-primary">Tempo Médio de Fechamento</p>
 <div className="text-2xl font-inter font-bold text-lia-text-primary">21<span className="text-sm">d</span></div>
              </div>
              <div className="w-full bg-gray-200 dark:bg-lia-bg-elevated rounded-full h-2">
                <div className="h-2 rounded-full bg-gray-900 w-[70%]"></div>
              </div>
              <p className={`${textStyles.bodySmall} text-status-success dark:text-status-success mt-2`}>-4 dias vs. mês anterior</p>
            </div>

            {/* Satisfação dos Contratados */}
            <div className="p-4 bg-wedo-purple/10 dark:bg-wedo-purple/20 rounded-md">
              <div className="flex items-center justify-between mb-2">
                <p className="text-sm font-open-sans font-semibold text-lia-text-primary">Satisfação dos Contratados (30 dias)</p>
                <div className="text-2xl font-inter font-bold text-wedo-purple dark:text-wedo-purple">8.7<span className="text-sm">/10</span></div>
              </div>
              <div className="w-full bg-gray-200 dark:bg-lia-bg-elevated rounded-full h-2">
                <div className="h-2 rounded-full bg-wedo-purple w-[87%]"></div>
              </div>
              <p className={`${textStyles.description} mt-2`}>NPS: +74 (Excelente)</p>
            </div>

            {/* Retenção 90 dias */}
            <div className="p-4 bg-wedo-orange/10 dark:bg-wedo-orange/20 rounded-md">
              <div className="flex items-center justify-between mb-2">
                <p className="text-sm font-open-sans font-semibold text-lia-text-primary">Retenção em 90 dias</p>
                <div className="text-2xl font-inter font-bold text-wedo-orange dark:text-wedo-orange">92%</div>
              </div>
              <div className="w-full bg-gray-200 dark:bg-lia-bg-elevated rounded-full h-2">
                <div className="h-2 rounded-full bg-wedo-orange w-[92%]"></div>
              </div>
              <p className={`${textStyles.description} mt-2`}>Meta: 85% • +7% vs. meta</p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Insights e Recomendações */}
      <Card className={`${cardStyles.default} dark:bg-lia-bg-primary dark:border-lia-border-subtle`}>
        <CardHeader className="px-4 py-3">
          <CardTitle className={`${textStyles.title} flex items-center gap-2`}>
            <Lightbulb className="w-3.5 h-3.5 text-lia-text-secondary" />
            Insights de Performance
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex items-start gap-3">
            <CheckCircle className="w-3.5 h-3.5 mt-0.5 flex-shrink-0 text-wedo-green-bright" />
            <p className="text-sm font-open-sans text-lia-text-primary">
              <strong>Indicações são o canal mais efetivo:</strong> 22.8% de conversão - 2x a média. Incentive programa de referral.
            </p>
          </div>
          <div className="flex items-start gap-3">
            <TrendingUp className="w-3.5 h-3.5 mt-0.5 flex-shrink-0 text-lia-text-secondary" />
            <p className="text-sm font-open-sans text-lia-text-primary">
              <strong>LinkedIn gera volume:</strong> 38% das candidaturas vêm do LinkedIn. Otimizar descrições de vagas pode aumentar qualidade.
            </p>
          </div>
          <div className="flex items-start gap-3">
            <AlertTriangle className="w-3.5 h-3.5 mt-0.5 flex-shrink-0 text-wedo-orange" />
            <p className="text-sm font-open-sans text-lia-text-primary">
              <strong>Job Boards com baixa conversão:</strong> 4.3% pode indicar descasamento de público. Reavaliar investimento nesses canais.
            </p>
          </div>
          <div className="flex items-start gap-3">
            <Award className="w-3.5 h-3.5 mt-0.5 flex-shrink-0 text-wedo-purple" />
            <p className="text-sm font-open-sans text-lia-text-primary">
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
