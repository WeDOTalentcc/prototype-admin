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


export function PrevisoesIAPlaceholder() {
  return (
    <div className="space-y-3">
      {/* Header */}
      <div>
        <h1 className="text-sm leading-tight font-semibold font-['Open_Sans',sans-serif] text-lia-text-primary flex items-center gap-2">
          <Brain className="w-3.5 h-3.5 text-wedo-cyan" />
          Previsões & Inteligência Artificial
        </h1>
        <p className="text-lia-text-secondary mt-1 font-open-sans text-xs">
          Machine Learning, previsões de demanda, alertas inteligentes e scoring preditivo
        </p>
      </div>

      {/* ML Predictions - Próximos 30 dias */}
      <Card className={`${cardStyles.default} dark:bg-lia-bg-primary dark:border-lia-border-subtle`}>
        <CardHeader className="px-4 py-3">
          <CardTitle className={`${textStyles.title} flex items-center gap-2`}>
            <Brain className="w-3.5 h-3.5 text-wedo-cyan" />
            Previsões ML - Próximos 30 Dias
          </CardTitle>
        </CardHeader>
        <CardContent className="pt-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
            {/* Applications Prediction */}
 <div className="p-4 bg-white dark:bg-lia-bg-secondary rounded-md border border-lia-border-default dark:border-lia-border-subtle">
              <p className={`${textStyles.description} mb-1`}>Candidaturas Esperadas</p>
              <div className="flex items-baseline gap-2">
                <span className="text-2xl font-inter font-bold text-lia-text-primary">2.847</span>
                <Badge className={`${badgeStyles.success} dark:bg-status-success/30 dark:text-status-success`}>
                  +12%
                </Badge>
              </div>
              <p className={`${textStyles.description} mt-1`}>vs. média anterior</p>
            </div>

            {/* Hires Prediction */}
            <div className="p-4 bg-white dark:bg-lia-bg-secondary rounded-md border border-wedo-purple/30 dark:border-wedo-purple/30">
              <p className={`${textStyles.description} mb-1`}>Contratações Previstas</p>
              <div className="flex items-baseline gap-2">
                <span className="text-2xl font-inter font-bold text-lia-text-primary">127</span>
 <Badge className="bg-gray-100 text-lia-text-primary text-xs font-inter">
                  +8%
                </Badge>
              </div>
              <p className={`${textStyles.description} mt-1`}>vs. média anterior</p>
            </div>

            {/* Time to Fill Prediction */}
            <div className="p-4 bg-white dark:bg-lia-bg-secondary rounded-md border border-wedo-orange/30 dark:border-wedo-orange/30">
              <p className={`${textStyles.description} mb-1`}>Time-to-Fill Médio</p>
              <div className="flex items-baseline gap-2">
                <span className="text-2xl font-inter font-bold text-lia-text-primary">18</span>
                <span className="text-sm font-open-sans text-lia-text-primary">dias</span>
              </div>
              <p className={`${textStyles.bodySmall} text-status-success dark:text-status-success mt-1`}>-3 dias vs. anterior</p>
            </div>

            {/* Cost Prediction */}
            <div className="p-4 bg-white dark:bg-lia-bg-secondary rounded-md border border-status-success/30 dark:border-status-success/30">
              <p className={`${textStyles.description} mb-1`}>Custo por Contratação</p>
              <div className="flex items-baseline gap-2">
                <span className="text-2xl font-inter font-bold text-lia-text-primary">R$ 3.2k</span>
              </div>
              <p className={`${textStyles.bodySmall} text-status-success dark:text-status-success mt-1`}>-R$ 420 vs. anterior</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Scoring Inteligente & Alertas */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-2.5">
        {/* Scoring Inteligente - Top Performers */}
        <Card className={`${cardStyles.default} dark:bg-lia-bg-primary dark:border-lia-border-subtle`}>
          <CardHeader className="pb-3">
            <CardTitle className={`${textStyles.subtitle} flex items-center gap-2`}>
              <Award className="w-3.5 h-3.5 text-wedo-purple" />
              Top Candidatos - Score LIA
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex items-center justify-between p-3 bg-wedo-purple/10 dark:bg-wedo-purple/20 rounded-md border border-wedo-purple/30 dark:border-wedo-purple/30">
              <div>
                <p className="font-open-sans font-semibold text-lia-text-primary text-sm">Ana Silva</p>
                <p className={`${textStyles.description}`}>Senior Developer • React/Node</p>
              </div>
              <Badge className="bg-wedo-purple/15 text-wedo-purple dark:bg-wedo-purple/30 dark:text-wedo-purple font-inter font-bold">
                98/100
              </Badge>
            </div>

            <div className="flex items-center justify-between p-3 bg-wedo-purple/10 dark:bg-wedo-purple/20 rounded-md border border-wedo-purple/30 dark:border-wedo-purple/30">
              <div>
                <p className="font-open-sans font-semibold text-lia-text-primary text-sm">Carlos Mendes</p>
                <p className={`${textStyles.description}`}>Product Manager • SaaS</p>
              </div>
              <Badge className="bg-wedo-purple/15 text-wedo-purple dark:bg-wedo-purple/30 dark:text-wedo-purple font-inter font-bold">
                96/100
              </Badge>
            </div>

 <div className="flex items-center justify-between p-3 bg-gray-50 dark:bg-lia-bg-secondary rounded-md border border-lia-border-default dark:border-lia-border-subtle">
              <div>
                <p className="font-open-sans font-semibold text-lia-text-primary text-sm">Beatriz Costa</p>
                <p className={`${textStyles.description}`}>UX Designer • Figma Expert</p>
              </div>
 <Badge className="bg-gray-100 text-lia-text-primary font-inter font-bold">
                94/100
              </Badge>
            </div>

 <div className="flex items-center justify-between p-3 bg-gray-50 dark:bg-lia-bg-secondary rounded-md border border-lia-border-default dark:border-lia-border-subtle">
              <div>
                <p className="font-open-sans font-semibold text-lia-text-primary text-sm">Rafael Santos</p>
                <p className={`${textStyles.description}`}>Data Scientist • Python/ML</p>
              </div>
 <Badge className="bg-gray-100 text-lia-text-primary font-inter font-bold">
                93/100
              </Badge>
            </div>
          </CardContent>
        </Card>

        {/* Alertas em Tempo Real */}
        <Card className={`${cardStyles.default} dark:bg-lia-bg-primary dark:border-lia-border-subtle`}>
          <CardHeader className="pb-3">
            <CardTitle className={`${textStyles.subtitle} flex items-center gap-2`}>
              <AlertTriangle className="w-3.5 h-3.5 text-wedo-magenta" />
              Alertas Inteligentes
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex items-start gap-3 p-3 bg-status-error/10 dark:bg-status-error/20 rounded-md border-l-4 border-status-error/30">
              <AlertTriangle className="w-3.5 h-3.5 mt-0.5 flex-shrink-0 text-status-error" />
              <div>
                <p className="text-sm font-open-sans font-semibold text-lia-text-primary">Vaga #2847 em risco</p>
                <p className={`${textStyles.bodySmall} mt-1`}>
                  45 dias sem candidatos qualificados. LIA sugere ajustar requisitos.
                </p>
              </div>
            </div>

            <div className="flex items-start gap-3 p-3 bg-wedo-orange/10 dark:bg-wedo-orange/20 rounded-md border-l-4 border-wedo-orange/30">
              <AlertTriangle className="w-3.5 h-3.5 mt-0.5 flex-shrink-0 text-wedo-orange" />
              <div>
                <p className="text-sm font-open-sans font-semibold text-lia-text-primary">Pipeline lento - Tech Lead</p>
                <p className={`${textStyles.bodySmall} mt-1`}>
                  Tempo médio de resposta: 8 dias. Meta: 3 dias.
                </p>
              </div>
            </div>

            <div className="flex items-start gap-3 p-3 bg-status-success/10 dark:bg-status-success/20 rounded-md border-l-4 border-status-success/30">
              <CheckCircle className="w-3.5 h-3.5 mt-0.5 flex-shrink-0 text-status-success" />
              <div>
                <p className="text-sm font-open-sans font-semibold text-lia-text-primary">Candidato ideal identificado</p>
                <p className={`${textStyles.bodySmall} mt-1`}>
                  Ana Silva (98/100) corresponde perfeitamente à vaga #2941.
                </p>
              </div>
            </div>

 <div className="flex items-start gap-3 p-3 bg-gray-50 dark:bg-lia-bg-secondary rounded-md border-l-4 border-gray-900 dark:border-lia-border-medium">
              <Brain className="w-3.5 h-3.5 mt-0.5 flex-shrink-0 text-wedo-cyan" />
              <div>
                <p className="text-sm font-open-sans font-semibold text-lia-text-primary">Recomendação automática</p>
                <p className={`${textStyles.bodySmall} mt-1`}>
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
        <Card className={`${cardStyles.default} dark:bg-lia-bg-primary dark:border-lia-border-subtle`}>
          <CardHeader className="pb-3">
            <CardTitle className={`${textStyles.subtitle} flex items-center gap-2`}>
              <TrendingUp className="w-3.5 h-3.5 text-lia-text-secondary" />
              Skills Mais Demandadas
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm font-open-sans font-medium text-lia-text-primary">React.js</span>
                <div className="flex items-center gap-2">
                  <span className="text-xs tracking-tight font-inter text-lia-text-primary">287 vagas</span>
                  <Badge className={`${badgeStyles.success} dark:bg-status-success/30 dark:text-status-success`}>
                    +18%
                  </Badge>
                </div>
              </div>
              <div className="w-full bg-gray-200 dark:bg-lia-bg-elevated rounded-full h-2">
                <div className="h-2 rounded-full bg-gray-900 w-[92%]"></div>
              </div>
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm font-open-sans font-medium text-lia-text-primary">Python</span>
                <div className="flex items-center gap-2">
                  <span className="text-xs tracking-tight font-inter text-lia-text-primary">243 vagas</span>
                  <Badge className={`${badgeStyles.success} dark:bg-status-success/30 dark:text-status-success`}>
                    +22%
                  </Badge>
                </div>
              </div>
              <div className="w-full bg-gray-200 dark:bg-lia-bg-elevated rounded-full h-2">
                <div className="h-2 rounded-full bg-wedo-green-bright w-[85%]"></div>
              </div>
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm font-open-sans font-medium text-lia-text-primary">Node.js</span>
                <div className="flex items-center gap-2">
                  <span className="text-xs tracking-tight font-inter text-lia-text-primary">218 vagas</span>
 <Badge className="bg-gray-100 text-lia-text-primary text-xs font-inter">
                    +15%
                  </Badge>
                </div>
              </div>
              <div className="w-full bg-gray-200 dark:bg-lia-bg-elevated rounded-full h-2">
                <div className="h-2 rounded-full bg-gray-900 w-[78%]"></div>
              </div>
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm font-open-sans font-medium text-lia-text-primary">AWS</span>
                <div className="flex items-center gap-2">
                  <span className="text-xs tracking-tight font-inter text-lia-text-primary">194 vagas</span>
                  <Badge className="bg-wedo-purple/15 text-wedo-purple dark:bg-wedo-purple/30 dark:text-wedo-purple text-xs font-inter">
                    +28%
                  </Badge>
                </div>
              </div>
              <div className="w-full bg-gray-200 dark:bg-lia-bg-elevated rounded-full h-2">
                <div className="h-2 rounded-full bg-wedo-purple w-[71%]"></div>
              </div>
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm font-open-sans font-medium text-lia-text-primary">Machine Learning</span>
                <div className="flex items-center gap-2">
                  <span className="text-xs tracking-tight font-inter text-lia-text-primary">156 vagas</span>
                  <Badge className="bg-wedo-purple/15 text-wedo-purple dark:bg-wedo-purple/30 dark:text-wedo-purple text-xs font-inter">
                    +34%
                  </Badge>
                </div>
              </div>
              <div className="w-full bg-gray-200 dark:bg-lia-bg-elevated rounded-full h-2">
                <div className="h-2 rounded-full bg-wedo-purple w-[62%]"></div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Demanda por Área - Previsão */}
        <Card className={`${cardStyles.default} dark:bg-lia-bg-primary dark:border-lia-border-subtle`}>
          <CardHeader className="pb-3">
            <CardTitle className={`${textStyles.subtitle} flex items-center gap-2`}>
              <BarChart3 className="w-3.5 h-3.5 text-wedo-purple" />
              Previsão de Demanda por Área
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="p-3 bg-gray-50 dark:bg-lia-bg-secondary rounded-md">
              <div className="flex items-center justify-between mb-2">
                <p className="text-sm font-open-sans font-semibold text-lia-text-primary">Tecnologia</p>
                <Badge className="bg-wedo-purple/15 text-wedo-purple dark:bg-wedo-purple/30 dark:text-wedo-purple text-micro font-medium">
                  +42 vagas
                </Badge>
              </div>
              <p className={`${textStyles.bodySmall}`}>
                Expansão prevista no Q1 2025. LIA recomenda pipeline proativo.
              </p>
            </div>

            <div className="p-3 bg-gray-50 dark:bg-lia-bg-secondary rounded-md">
              <div className="flex items-center justify-between mb-2">
                <p className="text-sm font-open-sans font-semibold text-lia-text-primary">Vendas</p>
 <Badge className={`${badgeStyles.info} dark:bg-lia-bg-secondary`}>
                  +28 vagas
                </Badge>
              </div>
              <p className={`${textStyles.bodySmall}`}>
                Crescimento sustentado. Pipeline atual é suficiente.
              </p>
            </div>

            <div className="p-3 bg-gray-50 dark:bg-lia-bg-secondary rounded-md">
              <div className="flex items-center justify-between mb-2">
                <p className="text-sm font-open-sans font-semibold text-lia-text-primary">Marketing</p>
                <Badge className={`${badgeStyles.success} dark:bg-status-success/30 dark:text-status-success`}>
                  +15 vagas
                </Badge>
              </div>
              <p className={`${textStyles.bodySmall}`}>
                Demanda estável. Foco em perfis sênior.
              </p>
            </div>

            <div className="p-3 bg-gray-50 dark:bg-lia-bg-secondary rounded-md">
              <div className="flex items-center justify-between mb-2">
                <p className="text-sm font-open-sans font-semibold text-lia-text-primary">Operações</p>
                <Badge className={`${badgeStyles.warning} dark:bg-wedo-orange/30 dark:text-wedo-orange`}>
                  +8 vagas
                </Badge>
              </div>
              <p className={`${textStyles.bodySmall}`}>
                Crescimento moderado. Priorizar retenção.
              </p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Insights da LIA */}
      <Card className={`${cardStyles.default} dark:bg-lia-bg-primary dark:border-lia-border-subtle`}>
        <CardHeader className="px-4 py-3">
          <CardTitle className={`${textStyles.title} flex items-center gap-2`}>
            <Brain className="w-3.5 h-3.5 text-wedo-cyan" />
            Recomendações Estratégicas da LIA
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex items-start gap-3">
            <CheckCircle className="w-3.5 h-3.5 mt-0.5 flex-shrink-0 text-wedo-green-bright" />
            <p className="text-sm font-open-sans text-lia-text-primary">
              <strong>Antecipação de demanda:</strong> Tecnologia terá pico em 30 dias. Inicie sourcing proativo para React e AWS.
            </p>
          </div>
          <div className="flex items-start gap-3">
            <TrendingUp className="w-3.5 h-3.5 mt-0.5 flex-shrink-0 text-wedo-purple" />
            <p className="text-sm font-open-sans text-lia-text-primary">
              <strong>Machine Learning em alta:</strong> Demanda cresceu 34% este mês. Considere parcerias com bootcamps especializados.
            </p>
          </div>
          <div className="flex items-start gap-3">
            <Activity className="w-3.5 h-3.5 mt-0.5 flex-shrink-0 text-lia-text-secondary" />
            <p className="text-sm font-open-sans text-lia-text-primary">
              <strong>Otimização de custos:</strong> Pipeline automatizado reduziu custo por contratação em 12% este mês.
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

// 3. People Analytics (Big Five + D&I + NPS)
