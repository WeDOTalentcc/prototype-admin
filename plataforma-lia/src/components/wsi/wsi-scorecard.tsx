"use client"

import { useState, useEffect } from"react"
import { Card, CardContent, CardHeader, CardTitle } from"@/components/ui/card"
import { Badge } from"@/components/ui/badge"
import { Button } from"@/components/ui/button"
import { Progress } from"@/components/ui/progress"
import {
  Brain, Target, MessageSquare, TrendingUp, AlertTriangle,
  CheckCircle, ChevronDown, ChevronUp, Award, BarChart3,
  Star, AlertCircle, FileText, Loader2
} from"lucide-react"
import { liaApi, WSIResultsResponse } from"@/services/lia-api"

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

const WSI_CLASSIFICATION_CONFIG: Record<string, { label: string; color: string; bgColor: string; textColor: string }> = {
  excepcional:    { label: 'Excepcional',      color: 'text-status-success', bgColor: 'bg-status-success/15', textColor: 'var(--status-success)' },
  excelente:      { label: 'Excelente',         color: 'text-status-success',   bgColor: 'bg-status-success/15',   textColor: 'var(--status-success)' },
  alto:           { label: 'Alto',               color: 'text-wedo-cyan-dark',   bgColor: 'bg-wedo-cyan/15',    textColor: 'var(--lia-text-secondary)' },
  medio:          { label: 'Médio',              color: 'text-status-warning',  bgColor: 'bg-status-warning/15',   textColor: 'var(--status-warning)' },
  abaixo_da_media:{ label: 'Abaixo da média',   color: 'text-wedo-orange', bgColor: 'bg-wedo-orange/15',  textColor: 'var(--status-warning)' },
  regular:        { label: 'Regular / Baixo',   color: 'text-status-error',    bgColor: 'bg-status-error/15',     textColor: 'var(--status-error)' },
}

const getClassificationConfig = (classification: string) =>
  WSI_CLASSIFICATION_CONFIG[classification] ?? WSI_CLASSIFICATION_CONFIG.medio

const getScoreDisplay = (score: number): ScoreDisplay => {
  if (score >= 4.5) return { value: score, label: 'Excepcional',    color: 'text-status-success', bgColor: 'bg-status-success/15' }
  if (score >= 4.0) return { value: score, label: 'Excelente',      color: 'text-status-success',   bgColor: 'bg-status-success/15' }
  if (score >= 3.5) return { value: score, label: 'Alto',            color: 'text-wedo-cyan-dark',    bgColor: 'bg-wedo-cyan/15' }
  if (score >= 3.0) return { value: score, label: 'Médio',           color: 'text-status-warning',  bgColor: 'bg-status-warning/15' }
  if (score >= 2.25) return { value: score, label: 'Abaixo da média',color: 'text-wedo-orange', bgColor: 'bg-wedo-orange/15' }
  return { value: score, label: 'Regular / Baixo', color: 'text-status-error', bgColor: 'bg-status-error/15' }
}

const getClassificationBadge = (classification: string) => {
  const cfg = getClassificationConfig(classification)
  return { color: cfg.color, bgColor: cfg.bgColor }
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
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [candidateId])

  const loadResults = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await liaApi.wsiGetCandidateResults(candidateId)
      setResults(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao carregar resultados')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <Card className="border-dashed">
        <CardContent className="py-6 flex items-center justify-center">
          <Loader2 className="w-5 h-5 animate-spin motion-reduce:animate-none text-lia-text-tertiary" />
          <span className="ml-2 text-sm text-lia-text-tertiary">Carregando WSI...</span>
        </CardContent>
      </Card>
    )
  }

  if (error) {
    return (
      <Card className="border-dashed border-status-error/30 dark:border-status-error/30">
        <CardContent className="py-6 flex items-center justify-center">
          <AlertCircle className="w-5 h-5 text-status-error" />
          <span className="ml-2 text-sm text-status-error">{error}</span>
        </CardContent>
      </Card>
    )
  }

  if (!results || results.total_screenings === 0) {
    return (
      <Card className="border-dashed">
        <CardContent className="py-6 text-center">
          <Brain className="w-8 h-8 text-wedo-cyan mx-auto mb-2" />
          <p className="text-sm text-lia-text-tertiary">
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
        className="cursor-pointer hover:bg-lia-bg-tertiary/50 transition-colors motion-reduce:transition-none"
        onClick={() => setExpanded(true)}
      >
        <CardContent className="py-3 px-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className={`w-10 h-10 rounded-full flex items-center justify-center ${scoreDisplay.bgColor}`}>
                <span className={`text-lg font-semibold ${scoreDisplay.color}`}>
                  {latestResult.overall_wsi.toFixed(1)}
                </span>
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <span className="font-medium text-sm">Score WSI</span>
                  <Badge className={`${classificationBadge.bgColor} ${classificationBadge.color} text-xs`}>
                    {latestResult.classification}
                  </Badge>
                </div>
                <p className="text-xs text-lia-text-tertiary">
                  {latestResult.screening_type === 'voice' ? 'Triagem por Voz' : 'Triagem por Texto'}
                </p>
              </div>
            </div>
            <ChevronDown className="w-4 h-4 text-lia-text-tertiary" />
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
              <span className="text-lia-text-tertiary font-normal">• {candidateName}</span>
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
            <span className={`text-2xl font-semibold ${scoreDisplay.color}`}>
              {latestResult.overall_wsi.toFixed(1)}
            </span>
            <span className="text-xs text-lia-text-tertiary">de 5.0</span>
          </div>

          <div className="flex-1 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-sm text-lia-text-tertiary flex items-center gap-1">
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
              <span className="text-sm text-lia-text-tertiary flex items-center gap-1">
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
            {getClassificationConfig(latestResult.classification).label}
          </Badge>

          <div className="flex items-center gap-2 text-xs text-lia-text-tertiary">
            {latestResult.screening_type === 'voice' ? (
              <Badge variant="outline" className="text-xs">
                🎤 Voz
              </Badge>
            ) : (
              <Badge variant="outline" className="text-xs">
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
            <p className="text-xs text-lia-text-tertiary mb-2">
              Histórico ({results.total_screenings} triagens)
            </p>
            <div className="space-y-2">
              {results.results.slice(1, 4).map((result, idx) => (
                <div 
                  key={result.result_id}
                  className="flex items-center justify-between text-sm p-2 bg-lia-bg-tertiary/50 rounded-md cursor-pointer hover:bg-lia-bg-tertiary transition-colors motion-reduce:transition-none"
                  onClick={() => onViewDetails?.(result.result_id)}
                >
                  <div className="flex items-center gap-2">
                    <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-medium ${getScoreDisplay(result.overall_wsi).bgColor} ${getScoreDisplay(result.overall_wsi).color}`}>
                      {result.overall_wsi.toFixed(1)}
                    </div>
                    <span className="text-xs text-lia-text-tertiary">
                      {new Date(result.created_at).toLocaleDateString('pt-BR')}
                    </span>
                  </div>
                  <Badge variant="outline" className="text-xs">
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
      <Badge className={`${badge.bgColor} ${badge.color} text-xs`}>
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
