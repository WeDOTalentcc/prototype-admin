"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Progress } from "@/components/ui/progress"
import {
  TrendingUp, TrendingDown, AlertTriangle, Target, Clock, Users,
  Zap, Brain, BarChart3, Activity, RefreshCw, ChevronRight,
  CheckCircle, XCircle, AlertCircle, ArrowUpRight, ArrowDownRight
} from "lucide-react"

interface PredictionFactor {
  factor: string
  value: string | number
  normalized: number
  weight: number
  contribution: number
}

interface HiringPrediction {
  candidate_id: string
  candidate_name: string
  job_title: string
  probability: number
  probability_label: string
  confidence: number
  top_strengths: PredictionFactor[]
  areas_of_concern: PredictionFactor[]
  recommendation: string
}

interface DropoutRisk {
  candidate_id: string
  candidate_name: string
  job_title: string
  risk_score: number
  risk_level: string
  risk_factors: string[]
  recommended_actions: string[]
}

interface TimeToFill {
  job_id: string
  job_title: string
  estimated_days: number
  confidence: number
  current_stage: string
  bottleneck: string | null
}

interface PipelineForecast {
  week: number
  predicted_hires: number
  predicted_interviews: number
  confidence: number
}

interface DashboardData {
  summary: {
    total_active_jobs: number
    jobs_on_track: number
    jobs_at_risk: number
    high_risk_candidates: number
    quick_win_opportunities: number
  }
  predictions: {
    high_risk_candidates: DropoutRisk[]
    jobs_at_risk: TimeToFill[]
    quick_wins: HiringPrediction[]
    pipeline_health: PipelineForecast[]
  }
  insights: {
    type: string
    title: string
    description: string
    action: string
  }[]
}

const mockDashboardData: DashboardData = {
  summary: {
    total_active_jobs: 18,
    jobs_on_track: 14,
    jobs_at_risk: 4,
    high_risk_candidates: 7,
    quick_win_opportunities: 12
  },
  predictions: {
    high_risk_candidates: [
      {
        candidate_id: "1",
        candidate_name: "João Silva",
        job_title: "Frontend Developer",
        risk_score: 78,
        risk_level: "high",
        risk_factors: ["Tempo em pipeline > 30 dias", "Sem resposta há 5 dias"],
        recommended_actions: ["Ligar urgente", "Oferecer update do processo"]
      },
      {
        candidate_id: "2",
        candidate_name: "Maria Santos",
        job_title: "UX Designer",
        risk_score: 65,
        risk_level: "medium",
        risk_factors: ["Participando de outros processos", "Expectativa salarial alta"],
        recommended_actions: ["Agilizar feedback", "Revisar proposta"]
      },
      {
        candidate_id: "3",
        candidate_name: "Pedro Costa",
        job_title: "Product Manager",
        risk_score: 82,
        risk_level: "high",
        risk_factors: ["Recebeu proposta concorrente", "Processo lento"],
        recommended_actions: ["Contato imediato", "Acelerar decisão"]
      }
    ],
    jobs_at_risk: [
      {
        job_id: "1",
        job_title: "Tech Lead Backend",
        estimated_days: 45,
        confidence: 72,
        current_stage: "Entrevistas finais",
        bottleneck: "Agenda do gestor"
      },
      {
        job_id: "2",
        job_title: "Data Engineer",
        estimated_days: 52,
        confidence: 65,
        current_stage: "Triagem",
        bottleneck: "Poucos candidatos qualificados"
      }
    ],
    quick_wins: [
      {
        candidate_id: "4",
        candidate_name: "Ana Oliveira",
        job_title: "Frontend Developer",
        probability: 89,
        probability_label: "Muito Alta",
        confidence: 92,
        top_strengths: [
          { factor: "wsi_score", value: 92, normalized: 0.92, weight: 0.3, contribution: 0.276 },
          { factor: "skills_match", value: "95%", normalized: 0.95, weight: 0.15, contribution: 0.1425 }
        ],
        areas_of_concern: [],
        recommendation: "Priorizar para oferta"
      },
      {
        candidate_id: "5",
        candidate_name: "Carlos Mendes",
        job_title: "Backend Developer",
        probability: 85,
        probability_label: "Alta",
        confidence: 88,
        top_strengths: [
          { factor: "experience_match", value: "8 anos", normalized: 0.9, weight: 0.2, contribution: 0.18 },
          { factor: "interview_performance", value: "Excelente", normalized: 0.88, weight: 0.15, contribution: 0.132 }
        ],
        areas_of_concern: [],
        recommendation: "Avançar para próxima etapa"
      }
    ],
    pipeline_health: [
      { week: 1, predicted_hires: 3, predicted_interviews: 12, confidence: 90 },
      { week: 2, predicted_hires: 2, predicted_interviews: 10, confidence: 85 },
      { week: 3, predicted_hires: 4, predicted_interviews: 15, confidence: 78 },
      { week: 4, predicted_hires: 2, predicted_interviews: 8, confidence: 72 }
    ]
  },
  insights: [
    {
      type: "warning",
      title: "4 vagas em risco de atraso",
      description: "Time to fill acima da média do mercado",
      action: "Revisar estratégia de sourcing"
    },
    {
      type: "success",
      title: "12 candidatos com alta probabilidade",
      description: "Oportunidades de contratação rápida identificadas",
      action: "Priorizar follow-up"
    },
    {
      type: "info",
      title: "Pipeline saudável para próximas 4 semanas",
      description: "Previsão de 11 contratações",
      action: "Manter ritmo atual"
    }
  ]
}

export function PredictiveAnalyticsTab() {
  const [data, setData] = useState<DashboardData>(mockDashboardData)
  const [loading, setLoading] = useState(false)
  const [selectedView, setSelectedView] = useState<"overview" | "risks" | "opportunities">("overview")

  const fetchData = async () => {
    setLoading(true)
    try {
      const response = await fetch("/api/backend-proxy/analytics/predictions/dashboard")
      if (response.ok) {
        const result = await response.json()
        if (result.success && result.data) {
          setData(result.data)
        }
      }
    } catch (error) {
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [])

  const getRiskColor = (level: string) => {
    switch (level) {
      case "critical": return "text-status-error bg-status-error/15"
      case "high": return "text-wedo-orange bg-wedo-orange/15"
      case "medium": return "text-status-warning bg-status-warning/15"
      case "low": return "text-status-success bg-status-success/15"
      default: return "lia-text-base bg-gray-100"
    }
  }

  const getProbabilityColor = (prob: number) => {
    if (prob >= 80) return "text-status-success"
    if (prob >= 60) return "text-lia-text-secondary dark:text-lia-text-tertiary"
    if (prob >= 40) return "text-status-warning"
    return "text-status-error"
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Brain className="w-5 h-5 text-wedo-cyan" />
          <h2 className="text-lg font-sans font-semibold text-lia-text-primary">
            Analytics Preditivo
          </h2>
          <Badge variant="outline" className="text-lia-text-secondary dark:text-lia-text-tertiary border-gray-900">
            Powered by LIA
          </Badge>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={fetchData}
          disabled={loading}
          className="gap-2"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          Atualizar
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
        <Card className="bg-gray-50 dark:bg-lia-bg-secondary">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs lia-text-base">Vagas Ativas</p>
                <p className="text-2xl font-bold text-lia-text-primary">{data.summary.total_active_jobs}</p>
              </div>
              <BarChart3 className="w-8 h-8 lia-text-base opacity-50" />
            </div>
          </CardContent>
        </Card>

 <Card className="bg-gray-50 dark:bg-lia-bg-secondary">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs lia-text-base">No Prazo</p>
                <p className="text-2xl font-bold text-lia-text-primary">{data.summary.jobs_on_track}</p>
              </div>
              <CheckCircle className="w-8 h-8 text-lia-text-secondary dark:text-lia-text-tertiary opacity-50" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-status-warning/10 dark:bg-status-warning/20">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs lia-text-base">Em Risco</p>
                <p className="text-2xl font-bold text-lia-text-primary dark:text-lia-text-primary">{data.summary.jobs_at_risk}</p>
              </div>
              <AlertTriangle className="w-8 h-8 lia-text-base opacity-50" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-status-error/10 dark:bg-status-error/20">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs lia-text-base">Candidatos em Risco</p>
                <p className="text-2xl font-bold text-lia-text-primary dark:text-lia-text-primary">{data.summary.high_risk_candidates}</p>
              </div>
              <XCircle className="w-8 h-8 lia-text-base opacity-50" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-status-success/10 dark:bg-status-success/20">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs lia-text-base">Quick Wins</p>
                <p className="text-2xl font-bold text-lia-text-primary">{data.summary.quick_win_opportunities}</p>
              </div>
              <Zap className="w-8 h-8 text-lia-text-secondary dark:text-lia-text-tertiary opacity-50" />
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="flex gap-2 mb-4">
        <Button
          variant={selectedView === "overview" ? "default" : "outline"}
          size="sm"
          onClick={() => setSelectedView("overview")}
        >
          Visão Geral
        </Button>
        <Button
          variant={selectedView === "risks" ? "default" : "outline"}
          size="sm"
          onClick={() => setSelectedView("risks")}
        >
          Riscos
        </Button>
        <Button
          variant={selectedView === "opportunities" ? "default" : "outline"}
          size="sm"
          onClick={() => setSelectedView("opportunities")}
        >
          Oportunidades
        </Button>
      </div>

      {selectedView === "overview" && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-sans flex items-center gap-2">
                <Activity className="w-4 h-4 text-lia-text-secondary dark:text-lia-text-tertiary" />
                Insights da LIA
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {data.insights.map((insight, index) => (
                <div
                  key={index}
                  className={`p-3 rounded-md ${
 insight.type === "warning" ? "bg-wedo-orange/10 dark:bg-wedo-orange/10/20" :
                    insight.type === "success" ? "bg-status-success/10 dark:bg-status-success/20" :
                    "bg-gray-100 dark:bg-lia-bg-secondary"
                  }`}
                >
                  <div className="flex items-start gap-3">
                    {insight.type === "warning" ? (
                      <AlertTriangle className="w-5 h-5 text-wedo-orange mt-0.5" />
                    ) : insight.type === "success" ? (
                      <CheckCircle className="w-5 h-5 text-status-success mt-0.5" />
                    ) : (
                      <AlertCircle className="w-5 h-5 text-lia-text-secondary dark:text-lia-text-tertiary mt-0.5" />
                    )}
                    <div className="flex-1">
                      <p className="font-medium text-sm text-lia-text-primary">{insight.title}</p>
                      <p className="text-xs lia-text-base mt-0.5">{insight.description}</p>
                      <Button variant="link" size="sm" className="h-auto p-0 mt-1 text-xs">
                        {insight.action} <ChevronRight className="w-3 h-3 ml-1" />
                      </Button>
                    </div>
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-sans flex items-center gap-2">
                <TrendingUp className="w-4 h-4 text-status-success" />
                Previsão de Pipeline (4 semanas)
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {data.predictions.pipeline_health.map((week) => (
                  <div key={week.week} className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="lia-text-base">Semana {week.week}</span>
                      <span className="font-medium">
                        {week.predicted_hires} contratações previstas
                      </span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Progress value={week.confidence} className="flex-1 h-2" />
                      <span className="text-xs lia-text-base w-12">{week.confidence}%</span>
                    </div>
                    <p className="text-xs lia-text-base">
                      {week.predicted_interviews} entrevistas previstas
                    </p>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {selectedView === "risks" && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-sans flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-status-error" />
                Candidatos em Risco de Desistência
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {data.predictions.high_risk_candidates.map((candidate) => (
                <div
                  key={candidate.candidate_id}
                  className="p-3 rounded-md bg-gray-50 dark:bg-lia-bg-secondary/50"
                >
                  <div className="flex items-start justify-between mb-2">
                    <div>
                      <p className="font-medium text-sm">{candidate.candidate_name}</p>
                      <p className="text-xs lia-text-base">{candidate.job_title}</p>
                    </div>
                    <Badge className={getRiskColor(candidate.risk_level)}>
                      {candidate.risk_score}% risco
                    </Badge>
                  </div>
                  <div className="space-y-1 mb-2">
                    {candidate.risk_factors.map((factor, idx) => (
                      <p key={idx} className="text-xs text-status-error flex items-center gap-1">
                        <XCircle className="w-3 h-3" /> {factor}
                      </p>
                    ))}
                  </div>
                  <div className="flex gap-2">
                    {candidate.recommended_actions.slice(0, 2).map((action, idx) => (
                      <Button key={idx} variant="outline" size="sm" className="text-xs h-7">
                        {action}
                      </Button>
                    ))}
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-sans flex items-center gap-2">
                <Clock className="w-4 h-4 text-wedo-orange" />
                Vagas em Risco de Atraso
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {data.predictions.jobs_at_risk.map((job) => (
                <div
                  key={job.job_id}
                  className="p-3 rounded-md bg-gray-50 dark:bg-lia-bg-secondary/50"
                >
                  <div className="flex items-start justify-between mb-2">
                    <div>
                      <p className="font-medium text-sm">{job.job_title}</p>
                      <p className="text-xs lia-text-base">{job.current_stage}</p>
                    </div>
                    <div className="text-right">
                      <p className="font-medium text-wedo-orange">{job.estimated_days} dias</p>
                      <p className="text-xs lia-text-base">{job.confidence}% confiança</p>
                    </div>
                  </div>
                  {job.bottleneck && (
                    <p className="text-xs text-wedo-orange flex items-center gap-1">
                      <AlertTriangle className="w-3 h-3" />
                      Gargalo: {job.bottleneck}
                    </p>
                  )}
                </div>
              ))}
            </CardContent>
          </Card>
        </div>
      )}

      {selectedView === "opportunities" && (
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-sans flex items-center gap-2">
              <Zap className="w-4 h-4 text-lia-text-secondary dark:text-lia-text-tertiary" />
              Quick Wins - Alta Probabilidade de Contratação
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {data.predictions.quick_wins.map((candidate) => (
                <div
                  key={candidate.candidate_id}
                  className="p-4 rounded-md bg-status-success/10 dark:bg-status-success/10"
                >
                  <div className="flex items-start justify-between mb-3">
                    <div>
                      <p className="font-medium">{candidate.candidate_name}</p>
                      <p className="text-sm lia-text-base">{candidate.job_title}</p>
                    </div>
                    <div className="text-right">
                      <p className={`text-2xl font-bold ${getProbabilityColor(candidate.probability)}`}>
                        {candidate.probability}%
                      </p>
                      <p className="text-xs lia-text-base">probabilidade</p>
                    </div>
                  </div>
                  
                  <div className="mb-3">
                    <p className="text-xs lia-text-base mb-1">Pontos Fortes</p>
                    <div className="flex flex-wrap gap-1">
                      {candidate.top_strengths.map((strength, idx) => (
                        <Badge key={idx} variant="outline" className="text-xs bg-status-success/15 text-status-success border-status-success/30">
                          {strength.factor}: {typeof strength.value === 'number' ? `${strength.value}%` : strength.value}
                        </Badge>
                      ))}
                    </div>
                  </div>

                  <div className="flex items-center justify-between">
                    <p className="text-xs lia-text-base">{candidate.recommendation}</p>
                    <Button size="sm" className="bg-gray-900 hover:bg-gray-800 text-white dark:hover:bg-gray-200">
                      Ação <ChevronRight className="w-3 h-3 ml-1" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
