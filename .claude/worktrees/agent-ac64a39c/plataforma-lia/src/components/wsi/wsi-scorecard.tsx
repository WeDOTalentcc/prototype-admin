"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Progress } from "@/components/ui/progress"
import {
  Brain, Target, MessageSquare, TrendingUp, AlertTriangle,
  CheckCircle, ChevronDown, ChevronUp, Award, BarChart3,
  Star, AlertCircle, FileText, Loader2
} from "lucide-react"
import { liaApi, WSIResultsResponse } from "@/services/lia-api"

interface WSIScorecardProps {
  candidateId: string
  candidateName?: string
  compact?: boolean
  showHistory?: boolean
  onViewDetails?: (resultId: string) => void
}

interface ScoreDisplay {
  value: number
  label: string
  color: string
  bgColor: string
}

const getScoreDisplay = (score: number): ScoreDisplay => {
  if (score >= 4.5) return { value: score, label: 'Excelente', color: 'text-green-600', bgColor: 'bg-green-100' }
  if (score >= 3.5) return { value: score, label: 'Alto', color: 'text-emerald-600', bgColor: 'bg-emerald-100' }
  if (score >= 2.5) return { value: score, label: 'Médio', color: 'text-yellow-600', bgColor: 'bg-yellow-100' }
  if (score >= 1.5) return { value: score, label: 'Regular', color: 'text-orange-600', bgColor: 'bg-orange-100' }
  return { value: score, label: 'Baixo', color: 'text-red-600', bgColor: 'bg-red-100' }
}

const getClassificationBadge = (classification: string) => {
  const config: Record<string, { color: string; bgColor: string }> = {
    excelente: { color: 'text-green-700', bgColor: 'bg-green-100' },
    alto: { color: 'text-emerald-700', bgColor: 'bg-emerald-100' },
    medio: { color: 'text-yellow-700', bgColor: 'bg-yellow-100' },
    regular: { color: 'text-orange-700', bgColor: 'bg-orange-100' },
    baixo: { color: 'text-red-700', bgColor: 'bg-red-100' }
  }
  return config[classification] || config.medio
}

export function WSIScorecard({
  candidateId,
  candidateName,
  compact = false,
  showHistory = false,
  onViewDetails
}: WSIScorecardProps) {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [results, setResults] = useState<WSIResultsResponse | null>(null)
  const [expanded, setExpanded] = useState(!compact)

  useEffect(() => {
    loadResults()
  }, [candidateId])

  const loadResults = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await liaApi.wsiGetCandidateResults(candidateId)
      setResults(data)
    } catch (err) {
      console.error('Failed to load WSI results:', err)
      setError(err instanceof Error ? err.message : 'Erro ao carregar resultados')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <Card className="border-dashed">
        <CardContent className="py-6 flex items-center justify-center">
          <Loader2 className="w-5 h-5 animate-spin text-muted-foreground" />
          <span className="ml-2 text-sm text-muted-foreground">Carregando WSI...</span>
        </CardContent>
      </Card>
    )
  }

  if (error) {
    return (
      <Card className="border-dashed border-red-200 dark:border-red-900">
        <CardContent className="py-6 flex items-center justify-center">
          <AlertCircle className="w-5 h-5 text-red-500" />
          <span className="ml-2 text-sm text-red-500">{error}</span>
        </CardContent>
      </Card>
    )
  }

  if (!results || results.total_screenings === 0) {
    return (
      <Card className="border-dashed">
        <CardContent className="py-6 text-center">
          <Brain className="w-8 h-8 text-wedo-cyan mx-auto mb-2" />
          <p className="text-sm text-muted-foreground">
            Nenhuma triagem WSI realizada
          </p>
        </CardContent>
      </Card>
    )
  }

  const latestResult = results.results[0]
  const scoreDisplay = getScoreDisplay(latestResult.overall_wsi)
  const classificationBadge = getClassificationBadge(latestResult.classification)

  if (compact && !expanded) {
    return (
      <Card 
        className="cursor-pointer hover:bg-muted/50 transition-colors"
        onClick={() => setExpanded(true)}
      >
        <CardContent className="py-3 px-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className={`w-10 h-10 rounded-full flex items-center justify-center ${scoreDisplay.bgColor}`}>
                <span className={`text-lg font-bold ${scoreDisplay.color}`}>
                  {latestResult.overall_wsi.toFixed(1)}
                </span>
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <span className="font-medium text-sm">Score WSI</span>
                  <Badge className={`${classificationBadge.bgColor} ${classificationBadge.color} text-[11px]`}>
                    {latestResult.classification}
                  </Badge>
                </div>
                <p className="text-xs text-muted-foreground">
                  {latestResult.screening_type === 'voice' ? 'Triagem por Voz' : 'Triagem por Texto'}
                </p>
              </div>
            </div>
            <ChevronDown className="w-4 h-4 text-muted-foreground" />
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm font-medium flex items-center gap-2">
            <Brain className="w-4 h-4 text-wedo-cyan" />
            Score WSI
            {candidateName && (
              <span className="text-muted-foreground font-normal">• {candidateName}</span>
            )}
          </CardTitle>
          {compact && (
            <Button 
              variant="ghost" 
              size="sm" 
              onClick={() => setExpanded(false)}
              className="h-6 w-6 p-0"
            >
              <ChevronUp className="w-4 h-4" />
            </Button>
          )}
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex items-center gap-4">
          <div className={`w-20 h-20 rounded-full flex flex-col items-center justify-center ${scoreDisplay.bgColor}`}>
            <span className={`text-2xl font-bold ${scoreDisplay.color}`}>
              {latestResult.overall_wsi.toFixed(1)}
            </span>
            <span className="text-[11px] text-muted-foreground">de 5.0</span>
          </div>

          <div className="flex-1 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground flex items-center gap-1">
                <Target className="w-3 h-3" />
                Técnico
              </span>
              <span className="font-medium">{latestResult.technical_wsi.toFixed(1)}</span>
            </div>
            <Progress 
              value={(latestResult.technical_wsi / 5) * 100} 
              className="h-1.5"
            />

            <div className="flex items-center justify-between mt-2">
              <span className="text-sm text-muted-foreground flex items-center gap-1">
                <MessageSquare className="w-3 h-3" />
                Comportamental
              </span>
              <span className="font-medium">{latestResult.behavioral_wsi.toFixed(1)}</span>
            </div>
            <Progress 
              value={(latestResult.behavioral_wsi / 5) * 100} 
              className="h-1.5"
            />
          </div>
        </div>

        <div className="flex items-center justify-between pt-2 border-t">
          <Badge className={`${classificationBadge.bgColor} ${classificationBadge.color}`}>
            <Award className="w-3 h-3 mr-1" />
            {latestResult.classification.charAt(0).toUpperCase() + latestResult.classification.slice(1)}
          </Badge>

          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            {latestResult.screening_type === 'voice' ? (
              <Badge variant="outline" className="text-[11px]">
                🎤 Voz
              </Badge>
            ) : (
              <Badge variant="outline" className="text-[11px]">
                💬 Texto
              </Badge>
            )}
            {latestResult.percentile && (
              <span className="flex items-center gap-1">
                <TrendingUp className="w-3 h-3" />
                Top {100 - latestResult.percentile}%
              </span>
            )}
          </div>
        </div>

        {showHistory && results.total_screenings > 1 && (
          <div className="pt-2 border-t">
            <p className="text-xs text-muted-foreground mb-2">
              Histórico ({results.total_screenings} triagens)
            </p>
            <div className="space-y-2">
              {results.results.slice(1, 4).map((result, idx) => (
                <div 
                  key={result.result_id}
                  className="flex items-center justify-between text-sm p-2 bg-muted/50 rounded cursor-pointer hover:bg-muted transition-colors"
                  onClick={() => onViewDetails?.(result.result_id)}
                >
                  <div className="flex items-center gap-2">
                    <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-medium ${getScoreDisplay(result.overall_wsi).bgColor} ${getScoreDisplay(result.overall_wsi).color}`}>
                      {result.overall_wsi.toFixed(1)}
                    </div>
                    <span className="text-xs text-muted-foreground">
                      {new Date(result.created_at).toLocaleDateString('pt-BR')}
                    </span>
                  </div>
                  <Badge variant="outline" className="text-[11px]">
                    {result.classification}
                  </Badge>
                </div>
              ))}
            </div>
          </div>
        )}

        {onViewDetails && (
          <Button 
            variant="outline" 
            size="sm" 
            className="w-full text-xs gap-1"
            onClick={() => onViewDetails(latestResult.result_id)}
          >
            <FileText className="w-3 h-3" />
            Ver Relatório Completo
          </Button>
        )}
      </CardContent>
    </Card>
  )
}

export function WSIScoreBadge({ score, classification }: { score: number; classification: string }) {
  const display = getScoreDisplay(score)
  const badge = getClassificationBadge(classification)

  return (
    <div className="inline-flex items-center gap-1.5">
      <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${display.bgColor} ${display.color}`}>
        {score.toFixed(1)}
      </div>
      <Badge className={`${badge.bgColor} ${badge.color} text-[11px]`}>
        {classification}
      </Badge>
    </div>
  )
}

export function WSIMiniScore({ score }: { score: number }) {
  const display = getScoreDisplay(score)

  return (
    <div 
      className={`inline-flex items-center justify-center w-8 h-8 rounded-full text-xs font-bold ${display.bgColor} ${display.color}`}
      title={`WSI: ${score.toFixed(1)} - ${display.label}`}
    >
      {score.toFixed(1)}
    </div>
  )
}
