"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import {
  Brain,
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  CheckCircle,
  XCircle,
  RefreshCw,
  ThumbsUp,
  ThumbsDown,
  Scale,
  Target,
  Lightbulb,
  ArrowRight,
  Clock
} from "lucide-react"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog"
import { cn } from "@/lib/utils"

interface CalibrationStats {
  period_days: number
  total_events: number
  explicit_feedback: {
    total: number
    agree: number
    disagree: number
    agreement_rate: number
  }
  implicit_feedback: {
    advances: number
    rejects: number
  }
  divergences: {
    total: number
    high_score_rejects: number
    low_score_advances: number
    explicit_disagree: number
  }
  accuracy_indicator: number
}

interface Divergence {
  id: string
  type: string
  candidate_id: string
  job_id?: string
  lia_score?: number
  recruiter_action?: string
  stage_from?: string
  stage_to?: string
  feedback_reason?: string
  score_delta?: number
  created_at?: string
}

interface Suggestion {
  id: string
  suggestion_type: string
  dimension?: string
  current_weight?: number
  suggested_weight?: number
  title: string
  description?: string
  rationale?: string
  supporting_evidence?: Array<{ metric: string; value: any }>
  impact_score?: number
  confidence?: number
  status: string
}

interface CalibrationDashboardData {
  stats: CalibrationStats
  divergences: Divergence[]
  suggestions: Suggestion[]
  weights: Array<{
    id: string
    dimension: string
    base_weight: number
    adjusted_weight: number
    confidence: number
    sample_size: number
  }>
  generated_at: string
}

const mockData: CalibrationDashboardData = {
  stats: {
    period_days: 30,
    total_events: 127,
    explicit_feedback: {
      total: 45,
      agree: 38,
      disagree: 7,
      agreement_rate: 84.4
    },
    implicit_feedback: {
      advances: 52,
      rejects: 30
    },
    divergences: {
      total: 12,
      high_score_rejects: 4,
      low_score_advances: 5,
      explicit_disagree: 3
    },
    accuracy_indicator: 90.6
  },
  divergences: [
    {
      id: "1",
      type: "implicit_reject",
      candidate_id: "cand-1",
      lia_score: 82,
      recruiter_action: "reject",
      stage_from: "Triagem",
      stage_to: "Rejeitado",
      created_at: new Date().toISOString()
    },
    {
      id: "2",
      type: "implicit_advance",
      candidate_id: "cand-2",
      lia_score: 58,
      recruiter_action: "advance",
      stage_from: "Triagem",
      stage_to: "Entrevista",
      created_at: new Date(Date.now() - 86400000).toISOString()
    },
    {
      id: "3",
      type: "explicit_disagree",
      candidate_id: "cand-3",
      lia_score: 75,
      feedback_reason: "Candidato tem experiência prática importante não capturada no CV",
      created_at: new Date(Date.now() - 172800000).toISOString()
    }
  ],
  suggestions: [
    {
      id: "sugg-1",
      suggestion_type: "weight_adjustment",
      dimension: "experience_years",
      current_weight: 0.3,
      suggested_weight: 0.4,
      title: "Aumentar peso de experiência prática",
      description: "Você avançou 5 candidatos com nota LIA < 60 nos últimos 30 dias.",
      rationale: "Candidatos com menos pontuação técnica estão sendo promovidos. Talvez a experiência prática seja mais importante para estas vagas.",
      supporting_evidence: [
        { metric: "low_score_advances", value: 5 },
        { metric: "period", value: "30 dias" }
      ],
      impact_score: 0.6,
      confidence: 0.5,
      status: "pending"
    }
  ],
  weights: [
    { id: "w1", dimension: "technical_skills", base_weight: 0.7, adjusted_weight: 0.7, confidence: 0.8, sample_size: 50 },
    { id: "w2", dimension: "experience_years", base_weight: 0.3, adjusted_weight: 0.3, confidence: 0.6, sample_size: 50 },
    { id: "w3", dimension: "cultural_fit", base_weight: 0.2, adjusted_weight: 0.25, confidence: 0.7, sample_size: 35 }
  ],
  generated_at: new Date().toISOString()
}

export function CalibrationDashboard() {
  const [data, setData] = useState<CalibrationDashboardData>(mockData)
  const [loading, setLoading] = useState(false)
  const [selectedSuggestion, setSelectedSuggestion] = useState<Suggestion | null>(null)
  const [rejectReason, setRejectReason] = useState("")
  const [actionLoading, setActionLoading] = useState(false)

  const fetchData = async () => {
    setLoading(true)
    try {
      const response = await fetch("/api/backend-proxy/calibration/dashboard?days=30")
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

  const handleApproveSuggestion = async (suggestionId: string) => {
    setActionLoading(true)
    try {
      const response = await fetch(`/api/backend-proxy/calibration/suggestions/${suggestionId}/approve`, {
        method: "POST"
      })
      if (response.ok) {
        setData(prev => ({
          ...prev,
          suggestions: prev.suggestions.filter(s => s.id !== suggestionId)
        }))
        setSelectedSuggestion(null)
      }
    } catch (error) {
    } finally {
      setActionLoading(false)
    }
  }

  const handleRejectSuggestion = async (suggestionId: string) => {
    setActionLoading(true)
    try {
      const response = await fetch(`/api/backend-proxy/calibration/suggestions/${suggestionId}/reject`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ reason: rejectReason })
      })
      if (response.ok) {
        setData(prev => ({
          ...prev,
          suggestions: prev.suggestions.filter(s => s.id !== suggestionId)
        }))
        setSelectedSuggestion(null)
        setRejectReason("")
      }
    } catch (error) {
    } finally {
      setActionLoading(false)
    }
  }

  const getAccuracyColor = (accuracy: number) => {
    if (accuracy >= 90) return "text-gray-600 dark:text-gray-400"
    if (accuracy >= 80) return "text-status-success"
    if (accuracy >= 70) return "text-status-warning"
    return "text-status-error"
  }

  const getDivergenceIcon = (type: string) => {
    switch (type) {
      case "implicit_reject":
        return <TrendingDown className="w-4 h-4 text-gray-800 dark:text-gray-200" />
      case "implicit_advance":
        return <TrendingUp className="w-4 h-4 text-gray-600 dark:text-gray-400" />
      case "explicit_disagree":
        return <ThumbsDown className="w-4 h-4 text-gray-600" />
      default:
        return <AlertTriangle className="w-4 h-4 text-gray-600" />
    }
  }

  const getDivergenceLabel = (type: string) => {
    switch (type) {
      case "implicit_reject":
        return "Rejeitou candidato com nota alta"
      case "implicit_advance":
        return "Avançou candidato com nota baixa"
      case "explicit_disagree":
        return "Discordou da avaliação"
      default:
        return "Divergência"
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Scale className="w-5 h-5 text-gray-600 dark:text-gray-400" />
          <h2 className="text-lg font-semibold font-sans text-gray-950 dark:text-gray-50">
            Calibração do Modelo LIA
          </h2>
          <Badge variant="outline" className="text-gray-600 dark:text-gray-400 border-gray-900 dark:border-gray-50">
            Últimos {data.stats.period_days} dias
          </Badge>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={fetchData}
          disabled={loading}
          className="gap-2"
        >
          <RefreshCw className={cn("w-4 h-4", loading && "animate-spin")} />
          Atualizar
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="bg-gray-50 dark:bg-gray-800/50">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-gray-600">Precisão LIA</p>
                <p className={cn("text-2xl font-bold", getAccuracyColor(data.stats.accuracy_indicator))}>
                  {data.stats.accuracy_indicator.toFixed(1)}%
                </p>
              </div>
              <Brain className="w-8 h-8 text-wedo-cyan opacity-50" />
            </div>
          </CardContent>
        </Card>

        <Card className="">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-gray-600">Taxa de Concordância</p>
                <p className="text-2xl font-bold text-gray-950 dark:text-gray-50">
                  {data.stats.explicit_feedback.agreement_rate.toFixed(1)}%
                </p>
                <p className="text-xs text-gray-600">
                  {data.stats.explicit_feedback.agree}/{data.stats.explicit_feedback.total} feedbacks
                </p>
              </div>
              <ThumbsUp className="w-8 h-8 text-gray-600 opacity-50" />
            </div>
          </CardContent>
        </Card>

        <Card className="">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-gray-600">Divergências</p>
                <p className="text-2xl font-bold text-gray-800 dark:text-gray-200">
                  {data.stats.divergences.total}
                </p>
                <p className="text-xs text-gray-600">
                  Nos últimos {data.stats.period_days} dias
                </p>
              </div>
              <AlertTriangle className="w-8 h-8 text-gray-600 opacity-50" />
            </div>
          </CardContent>
        </Card>

        <Card className="">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-gray-600">Ações Capturadas</p>
                <p className="text-2xl font-bold text-gray-950 dark:text-gray-50">
                  {data.stats.total_events}
                </p>
                <p className="text-xs text-gray-600">
                  {data.stats.implicit_feedback.advances} avanços, {data.stats.implicit_feedback.rejects} rejeições
                </p>
              </div>
              <Target className="w-8 h-8 text-gray-600 opacity-50" />
            </div>
          </CardContent>
        </Card>
      </div>

      {data.suggestions.length > 0 && (
        <Card className="bg-gray-50 dark:bg-gray-800/50">
          <CardHeader className="pb-2">
            <CardTitle className="text-base flex items-center gap-2 font-sans">
              <Lightbulb className="w-5 h-5 text-gray-600 dark:text-gray-400" />
              Sugestões de Calibração
              <Badge className="bg-gray-900 dark:bg-gray-50 text-white dark:text-gray-900">
                {data.suggestions.length} pendente{data.suggestions.length > 1 ? "s" : ""}
              </Badge>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {data.suggestions.map((suggestion) => (
                <div
                  key={suggestion.id}
                  className="p-4 bg-white dark:bg-gray-800 rounded-md"
                >
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1">
                      <h4 className="font-medium font-sans text-gray-950 dark:text-gray-50">
                        {suggestion.title}
                      </h4>
                      <p className="text-sm text-gray-800 dark:text-gray-200 mt-1">
                        {suggestion.description}
                      </p>
                      {suggestion.dimension && (
                        <div className="flex items-center gap-2 mt-2">
                          <Badge variant="outline" className="text-xs">
                            {suggestion.dimension}
                          </Badge>
                          <span className="text-xs text-gray-600">
                            {suggestion.current_weight} → {suggestion.suggested_weight}
                          </span>
                          {suggestion.confidence && (
                            <span className="text-xs text-gray-600">
                              ({(suggestion.confidence * 100).toFixed(0)}% confiança)
                            </span>
                          )}
                        </div>
                      )}
                    </div>
                    <div className="flex gap-2">
                      <Button
                        size="sm"
                        variant="outline"
                        className="gap-1"
                        onClick={() => setSelectedSuggestion(suggestion)}
                      >
                        Ver detalhes
                        <ArrowRight className="w-3 h-3" />
                      </Button>
                      <Button
                        size="sm"
                        className="bg-gray-900 hover:bg-gray-800 text-white dark:bg-gray-50 dark:text-gray-900 dark:hover:bg-gray-200 gap-1"
                        onClick={() => handleApproveSuggestion(suggestion.id)}
                        disabled={actionLoading}
                      >
                        <CheckCircle className="w-4 h-4" />
                        Aprovar
                      </Button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="">
          <CardHeader className="pb-2">
            <CardTitle className="text-base flex items-center gap-2 font-sans">
              <AlertTriangle className="w-5 h-5 text-gray-600" />
              Divergências Recentes
            </CardTitle>
          </CardHeader>
          <CardContent>
            {data.divergences.length === 0 ? (
              <div className="text-center py-8 text-gray-600">
                <CheckCircle className="w-12 h-12 mx-auto mb-2 text-gray-600 dark:text-gray-400 opacity-50" />
                <p>Nenhuma divergência significativa</p>
                <p className="text-sm">LIA e recrutadores estão alinhados</p>
              </div>
            ) : (
              <div className="space-y-3">
                {data.divergences.map((divergence) => (
                  <div
                    key={divergence.id}
                    className="flex items-start gap-3 p-3 bg-gray-50 dark:bg-gray-800 rounded-md"
                  >
                    {getDivergenceIcon(divergence.type)}
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-950 dark:text-gray-50">
                        {getDivergenceLabel(divergence.type)}
                      </p>
                      <p className="text-xs text-gray-600 mt-0.5">
                        Nota LIA: {divergence.lia_score}%
                        {divergence.stage_from && divergence.stage_to && (
                          <span className="ml-2">
                            {divergence.stage_from} → {divergence.stage_to}
                          </span>
                        )}
                      </p>
                      {divergence.feedback_reason && (
                        <p className="text-xs text-gray-800 dark:text-gray-200 mt-1 italic">
                          "{divergence.feedback_reason}"
                        </p>
                      )}
                    </div>
                    {divergence.created_at && (
                      <span className="text-xs text-gray-600 flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        {new Date(divergence.created_at).toLocaleDateString("pt-BR")}
                      </span>
                    )}
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        <Card className="">
          <CardHeader className="pb-2">
            <CardTitle className="text-base flex items-center gap-2 font-sans">
              <Scale className="w-5 h-5 text-gray-600 dark:text-gray-400" />
              Pesos Atuais
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {data.weights.map((weight) => (
                <div key={weight.id}>
                  <div className="flex justify-between items-center mb-1">
                    <span className="text-sm text-gray-800 dark:text-gray-200 capitalize">
                      {weight.dimension.replace(/_/g, " ")}
                    </span>
                    <span className="text-sm font-medium text-gray-950 dark:text-gray-50">
                      {(weight.adjusted_weight * 100).toFixed(0)}%
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                    <div
                      className="bg-gray-700 dark:bg-gray-300 h-2 rounded-full transition-all"
                      style={{ width: `${weight.adjusted_weight * 100}%` }}
                    />
                  </div>
                  <div className="flex justify-between mt-1">
                    <span className="text-xs text-gray-600">
                      Base: {(weight.base_weight * 100).toFixed(0)}%
                    </span>
                    <span className="text-xs text-gray-600">
                      {weight.sample_size} amostras
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      <Dialog open={!!selectedSuggestion} onOpenChange={() => setSelectedSuggestion(null)}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 font-sans">
              <Lightbulb className="w-5 h-5 text-gray-600 dark:text-gray-400" />
              {selectedSuggestion?.title}
            </DialogTitle>
          </DialogHeader>
          
          {selectedSuggestion && (
            <div className="space-y-4">
              <p className="text-sm text-gray-800 dark:text-gray-200">
                {selectedSuggestion.description}
              </p>
              
              {selectedSuggestion.rationale && (
                <div className="p-3 bg-gray-50 dark:bg-gray-800 rounded-md">
                  <p className="text-sm font-medium text-gray-800 dark:text-gray-200 mb-1">
                    Racional:
                  </p>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    {selectedSuggestion.rationale}
                  </p>
                </div>
              )}

              {selectedSuggestion.supporting_evidence && (
                <div>
                  <p className="text-sm font-medium text-gray-800 dark:text-gray-200 mb-2">
                    Evidências:
                  </p>
                  <div className="flex flex-wrap gap-2">
                    {selectedSuggestion.supporting_evidence.map((evidence, idx) => (
                      <Badge key={idx} variant="outline">
                        {evidence.metric}: {evidence.value}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}

              {selectedSuggestion.dimension && (
                <div className="flex items-center gap-4 p-3 bg-gray-100 dark:bg-gray-800 rounded-md">
                  <div>
                    <p className="text-xs text-gray-600">Peso Atual</p>
                    <p className="text-lg font-bold text-gray-950 dark:text-gray-50">
                      {((selectedSuggestion.current_weight || 0) * 100).toFixed(0)}%
                    </p>
                  </div>
                  <ArrowRight className="w-5 h-5 text-gray-600 dark:text-gray-400" />
                  <div>
                    <p className="text-xs text-gray-600">Peso Sugerido</p>
                    <p className="text-lg font-bold text-gray-900 dark:text-gray-50">
                      {((selectedSuggestion.suggested_weight || 0) * 100).toFixed(0)}%
                    </p>
                  </div>
                </div>
              )}

              <div>
                <p className="text-sm font-medium text-gray-800 dark:text-gray-200 mb-2">
                  Motivo para rejeitar (opcional):
                </p>
                <Textarea
                  value={rejectReason}
                  onChange={(e) => setRejectReason(e.target.value)}
                  placeholder="Explique por que você discorda desta sugestão..."
                  className="h-20 resize-none"
                />
              </div>
            </div>
          )}

          <DialogFooter className="gap-2">
            <Button
              variant="outline"
              onClick={() => {
                if (selectedSuggestion) {
                  handleRejectSuggestion(selectedSuggestion.id)
                }
              }}
              disabled={actionLoading}
              className="gap-1"
            >
              <XCircle className="w-4 h-4" />
              Rejeitar
            </Button>
            <Button
              className="bg-gray-900 hover:bg-gray-800 text-white dark:bg-gray-50 dark:text-gray-900 dark:hover:bg-gray-200 gap-1"
              onClick={() => {
                if (selectedSuggestion) {
                  handleApproveSuggestion(selectedSuggestion.id)
                }
              }}
              disabled={actionLoading}
            >
              <CheckCircle className="w-4 h-4" />
              Aprovar Ajuste
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
