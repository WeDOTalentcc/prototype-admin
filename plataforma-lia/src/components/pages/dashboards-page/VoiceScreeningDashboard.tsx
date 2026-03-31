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



interface OpenMicAnalytics {
  total_screenings?: number
  analyzed_screenings?: number
  average_scores?: { overall?: number; technical?: number }
  recommendation_breakdown?: Record<string, unknown>
  [key: string]: unknown
}


export function VoiceScreeningDashboard() {
  const [analytics, setAnalytics] = useState<OpenMicAnalytics | null>(null)
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const [screenings, setScreenings] = useState<any[]>([])
  const [isLoading, setIsLoading] = useState(true)

  React.useEffect(() => {
    fetchVoiceScreeningData()
  }, [])

  const fetchVoiceScreeningData = async () => {
    try {
      setIsLoading(true)
      
      // Fetch analytics e screenings do backend
      const [analyticsRes, screeningsRes] = await Promise.all([
        fetch('/api/backend-proxy/openmic/analytics'),
        fetch('/api/backend-proxy/openmic/screenings?limit=20')
      ])
      
      if (analyticsRes.ok) {
        const analyticsData = await analyticsRes.json()
        setAnalytics(analyticsData)
      }
      
      if (screeningsRes.ok) {
        const screeningsData = await screeningsRes.json()
        setScreenings(screeningsData.screenings || [])
      }
    } catch (error) {
    } finally {
      setIsLoading(false)
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center space-y-3">
          <Activity className="w-8 h-8 mx-auto text-lia-text-secondary dark:text-lia-text-tertiary animate-spin motion-reduce:animate-none" />
          <p className="text-sm font-open-sans text-lia-text-secondary dark:text-lia-text-tertiary">
            Carregando dados de Voice Screening...
          </p>
        </div>
      </div>
    )
  }

  const getRecommendationColor = (recommendation: string) => {
    switch (recommendation) {
      case 'strong_yes':
        return 'bg-status-success/15 text-status-success dark:bg-status-success/30 dark:text-status-success'
      case 'interview':
 return 'bg-gray-100 text-lia-text-primary dark:text-lia-text-secondary'
      case 'maybe':
        return 'bg-status-warning/15 text-status-warning dark:bg-status-warning/30 dark:text-status-warning'
      case 'reject':
        return 'bg-status-error/15 text-status-error dark:bg-status-error/30 dark:text-status-error'
      default:
 return 'bg-gray-100 text-lia-text-primary dark:bg-lia-bg-primary/30 dark:text-lia-text-tertiary'
    }
  }

  const getRecommendationLabel = (recommendation: string) => {
    switch (recommendation) {
      case 'strong_yes':
        return 'Forte Sim'
      case 'interview':
        return 'Entrevistar'
      case 'maybe':
        return 'Talvez'
      case 'reject':
        return 'Rejeitar'
      default:
        return recommendation
    }
  }

  return (
    <div className="space-y-3">
      {/* Header */}
      <div>
        <h1 className="text-sm leading-tight font-semibold font-['Open_Sans',sans-serif] text-lia-text-primary dark:text-lia-text-primary flex items-center gap-2">
          <Phone className="w-3.5 h-3.5 text-lia-text-secondary dark:text-lia-text-tertiary" />
          Voice Screening Analytics
        </h1>
        <p className="text-lia-text-secondary dark:text-lia-text-tertiary mt-1 font-open-sans text-xs">
          Análise de triagem por voz com IA - OpenMic.ai + LIA Assistant
        </p>
      </div>

      {/* KPIs Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-2.5">
        <Card className={`${cardStyles.default} dark:bg-lia-bg-primary dark:border-lia-border-subtle`}>
          <CardContent className="p-4">
            <p className={`${textStyles.description} mb-1`}>Total de Screenings</p>
            <p className="text-xl font-bold font-inter text-lia-text-primary dark:text-lia-text-primary">
              {analytics?.total_screenings || 0}
            </p>
          </CardContent>
        </Card>

        <Card className={`${cardStyles.default} dark:bg-lia-bg-primary dark:border-lia-border-subtle`}>
          <CardContent className="p-4">
            <p className={`${textStyles.description} mb-1`}>Com Análise IA</p>
            <p className="text-xl font-bold font-inter text-lia-text-primary dark:text-lia-text-primary">
              {analytics?.analyzed_screenings || 0}
            </p>
          </CardContent>
        </Card>

        <Card className={`${cardStyles.default} dark:bg-lia-bg-primary dark:border-lia-border-subtle`}>
          <CardContent className="p-4">
            <p className={`${textStyles.description} mb-1`}>Score Médio Geral</p>
            <p className="text-xl font-bold font-inter text-lia-text-primary dark:text-lia-text-primary">
              {analytics?.average_scores?.overall || 0}/100
            </p>
          </CardContent>
        </Card>

        <Card className={`${cardStyles.default} dark:bg-lia-bg-primary dark:border-lia-border-subtle`}>
          <CardContent className="p-4">
            <p className={`${textStyles.description} mb-1`}>Score Técnico Médio</p>
            <p className="text-xl font-bold font-inter text-lia-text-primary dark:text-lia-text-primary">
              {analytics?.average_scores?.technical || 0}/100
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Recommendation Breakdown */}
      {analytics?.recommendation_breakdown && Object.keys(analytics.recommendation_breakdown).length > 0 && (
        <Card className={`${cardStyles.default} dark:bg-lia-bg-primary dark:border-lia-border-subtle`}>
          <CardHeader className="px-4 py-3">
            <CardTitle className={`${textStyles.title} dark:text-lia-text-primary flex items-center gap-2`}>
              <PieChart className="w-3.5 h-3.5 text-lia-text-secondary dark:text-lia-text-tertiary" />
              Distribuição de Recomendações
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-2">
              {Object.entries(analytics.recommendation_breakdown).map(([rec, count]: [string, unknown]) => (
                <div key={rec} className="p-3 bg-gray-50 dark:bg-lia-bg-primary rounded-md border border-lia-border-subtle dark:border-lia-border-subtle">
                  <p className={`${textStyles.description} mb-1`}>
                    {getRecommendationLabel(rec)}
                  </p>
                  <p className="text-lg font-bold font-inter text-lia-text-primary dark:text-lia-text-primary">
                    {count}
                  </p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Recent Screenings List */}
      <Card className={`${cardStyles.default} dark:bg-lia-bg-primary dark:border-lia-border-subtle`}>
        <CardHeader className="px-4 py-3">
          <CardTitle className={`${textStyles.title} dark:text-lia-text-primary flex items-center gap-2`}>
            <Activity className="w-3.5 h-3.5 text-lia-text-secondary dark:text-lia-text-tertiary" />
            Screenings Recentes ({screenings.length})
          </CardTitle>
        </CardHeader>
        <CardContent>
          {screenings.length === 0 ? (
            <div className="text-center py-8">
 <Phone className="w-12 h-12 mx-auto text-lia-text-disabled dark:text-lia-text-primary mb-3" />
              <p className="text-sm font-open-sans text-lia-text-secondary dark:text-lia-text-tertiary">
                Nenhum screening realizado ainda
              </p>
              <p className="text-xs font-open-sans text-lia-text-primary dark:text-lia-text-primary mt-1">
                Use o endpoint /api/v1/openmic/test-call para iniciar um screening
              </p>
            </div>
          ) : (
            <div className="space-y-2">
              {screenings.map((screening) => (
                <div 
                  key={screening.id}
                  className="p-3 bg-gray-50 dark:bg-lia-bg-primary rounded-md border border-lia-border-subtle dark:border-lia-border-subtle hover:border-gray-900 dark:hover:border-gray-50 dark:hover:border-gray-900 dark:hover:border-gray-50 transition-colors motion-reduce:transition-none"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <p className="font-semibold font-open-sans text-sm text-lia-text-primary dark:text-lia-text-primary truncate">
                          {screening.candidate_name}
                        </p>
                        {screening.analysis && (
                          <Badge className={getRecommendationColor(screening.analysis.overall_recommendation)}>
                            {getRecommendationLabel(screening.analysis.overall_recommendation)}
                          </Badge>
                        )}
                      </div>
                      
                      <p className="text-xs font-open-sans text-lia-text-secondary dark:text-lia-text-tertiary mb-2">
                        {screening.job_title} • {screening.duration_seconds}s • {screening.candidate_phone}
                      </p>

                      {screening.analysis && (
                        <>
                          <div className="flex items-center gap-3 mb-2">
                            <div className="flex items-center gap-1.5">
                              <span className={`${textStyles.description} dark:text-lia-text-tertiary`}>Geral:</span>
                              <span className="text-xs font-bold font-inter text-lia-text-primary dark:text-lia-text-primary">
                                {screening.analysis.overall_score}/100
                              </span>
                            </div>
                            <div className="flex items-center gap-1.5">
                              <span className={`${textStyles.description} dark:text-lia-text-tertiary`}>Técnico:</span>
                              <span className="text-xs font-bold font-inter text-lia-text-primary dark:text-lia-text-primary">
                                {screening.analysis.tech_score || 'N/A'}
                              </span>
                            </div>
                            <div className="flex items-center gap-1.5">
                              <span className={`${textStyles.description} dark:text-lia-text-tertiary`}>Comunicação:</span>
                              <span className="text-xs font-bold font-inter text-lia-text-primary dark:text-lia-text-primary">
                                {screening.analysis.comm_score || 'N/A'}
                              </span>
                            </div>
                          </div>

                          {screening.analysis.summary && (
                            <p className="text-xs font-open-sans text-lia-text-secondary dark:text-lia-text-tertiary line-clamp-2">
                              {screening.analysis.summary}
                            </p>
                          )}

                          {screening.analysis.key_strengths && screening.analysis.key_strengths.length > 0 && (
                            <div className="mt-2 flex flex-wrap gap-1">
                              {screening.analysis.key_strengths.slice(0, 3).map((strength: string, idx: number) => (
                                <Badge 
                                  key={idx}
                                  className="bg-status-success/15 text-status-success dark:bg-status-success/30 dark:text-status-success text-xs tracking-tight"
                                >
                                  ✓ {strength}
                                </Badge>
                              ))}
                            </div>
                          )}
                        </>
                      )}
                    </div>

                    <div className="flex flex-col items-end gap-2">
                      <p className={`${textStyles.description} dark:text-lia-text-tertiary`}>
                        {new Date(screening.created_at).toLocaleDateString('pt-BR')}
                      </p>
                      {screening.processing_status && (
 <Badge className="bg-gray-100 text-lia-text-primary dark:bg-lia-bg-primary/30 dark:text-lia-text-tertiary text-xs tracking-tight">
                          {screening.processing_status}
                        </Badge>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Integration Info Card */}
 <Card className="bg-gray-50 dark:bg-lia-bg-secondary border-lia-border-default dark:border-lia-border-subtle">
        <CardContent className="p-4">
          <div className="flex items-start gap-3">
            <Brain className="w-4 h-4 mt-0.5 flex-shrink-0 text-wedo-cyan" />
            <div className="flex-1">
              <p className="font-semibold font-open-sans text-sm text-lia-text-primary dark:text-lia-text-primary mb-1">
                OpenMic.ai + LIA Integration
              </p>
              <p className={`${textStyles.bodySmall} dark:text-lia-text-tertiary`}>
                Sistema de triagem por voz automática com análise dual: keywords básicos (~100ms) + Claude Sonnet 4.5 deep analysis (~10-15s). 
                Todas as ligações são gravadas, transcritas e analisadas automaticamente com 4 dimensões: técnica, comunicação, fit cultural e avaliação geral.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

// 7. Análise de Competências
