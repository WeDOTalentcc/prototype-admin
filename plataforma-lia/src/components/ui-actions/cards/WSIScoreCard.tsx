"use client"

import React from"react"
import { Card, CardContent } from"@/components/ui/card"
import { Chip } from "@/components/ui/chip"
import { Button } from"@/components/ui/button"
import { Progress } from"@/components/ui/progress"
import {
  Brain,
  Star,
  TrendingUp,
  TrendingDown,
  Minus,
  CheckCircle2,
  AlertCircle,
  FileText,
  ExternalLink
} from"lucide-react"

interface WSIDimension {
  name: string
  score: number
  max_score: number
  level: string
}

interface WSIScoreData {
  candidate_id: string
  candidate_name: string
  overall_score: number
  max_score: number
  recommendation:"Aprovado" |"Reprovado" |"Aguardando"
  dimensions: WSIDimension[]
  strengths?: string[]
  development_areas?: string[]
  summary?: string
  evaluated_at?: string
}

interface WSIScoreCardProps {
  data: WSIScoreData
  onViewDetails?: () => void
  onViewReport?: () => void
  compact?: boolean
}

export function WSIScoreCard({
  data,
  onViewDetails,
  onViewReport,
  compact = false
}: WSIScoreCardProps) {
  const percentage = Math.round((data.overall_score / data.max_score) * 100)

  const getClassification = (pct: number) => {
    if (pct >= 90) return { label:"Excepcional", color:"text-status-success", bg:"bg-status-success/15" }
    if (pct >= 80) return { label:"Excelente", color:"text-status-success", bg:"bg-status-success/15" }
    if (pct >= 70) return { label:"Alto", color:"text-wedo-cyan-text", bg:"bg-wedo-cyan/15" }
    if (pct >= 60) return { label:"Médio", color:"text-status-warning", bg:"bg-status-warning/15" }
    if (pct >= 45) return { label:"Abaixo da média", color:"text-wedo-orange-text", bg:"bg-wedo-orange/15" }
    return { label:"Regular / Baixo", color:"text-status-error", bg:"bg-status-error/15" }
  }

  const getScoreDisplay = (score: number) => {
    if (score >= 90) return { text:"text-status-success", icon: TrendingUp }
    if (score >= 80) return { text:"text-status-success", icon: TrendingUp }
    if (score >= 70) return { text:"text-wedo-cyan-text", icon: TrendingUp }
    if (score >= 60) return { text:"text-status-warning", icon: Minus }
    if (score >= 45) return { text:"text-wedo-orange-text", icon: TrendingDown }
    return { text:"text-status-error", icon: TrendingDown }
  }

  const getRecommendationBadge = (recommendation: string) => {
    switch (recommendation) {
      case"Aprovado":
        return (
          <Chip variant="neutral" muted
            className="border border-lia-border-default bg-lia-bg-primary text-lia-text-primary"
          >
            <CheckCircle2 className="h-3 w-3 mr-1 text-wedo-green" />
            Aprovado
          </Chip>
        )
      case"Reprovado":
        return (
          <Chip variant="neutral" muted
            className="border border-lia-border-default bg-lia-bg-primary text-lia-text-primary"
          >
            <AlertCircle className="h-3 w-3 mr-1 text-wedo-magenta" />
            Reprovado
          </Chip>
        )
      default:
        return (
          <Chip variant="neutral" muted
            className="border border-lia-border-default bg-lia-bg-primary text-lia-text-secondary"
          >
            <Minus className="h-3 w-3 mr-1 text-lia-text-secondary" />
            Aguardando
          </Chip>
        )
    }
  }

  const getDimensionIcon = (score: number) => {
    const percent = score * 100
    if (percent >= 90) return <TrendingUp className="h-3 w-3 text-status-success" />
    if (percent >= 80) return <TrendingUp className="h-3 w-3 text-status-success" />
    if (percent >= 70) return <TrendingUp className="h-3 w-3 text-wedo-cyan-text" />
    if (percent >= 60) return <Minus className="h-3 w-3 text-status-warning" />
    if (percent >= 45) return <TrendingDown className="h-3 w-3 text-wedo-orange-text" />
    return <TrendingDown className="h-3 w-3 text-status-error" />
  }

  const scoreDisplay = getScoreDisplay(percentage)
  const classification = getClassification(percentage)

  return (
    <Card
      className="w-full max-w-md border-l-4 overflow-hidden bg-lia-bg-secondary"
     
    >
      <CardContent className="p-4">
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-center gap-3">
            <div
              className="h-12 w-12 rounded-full flex items-center justify-center bg-lia-bg-tertiary"
            >
              <Brain className="h-6 w-6 text-wedo-purple" />
            </div>
            <div>
              <div className="text-sm text-lia-text-tertiary">Avaliação WSI</div>
              <h4 className="font-semibold text-lia-text-primary">
                {data.candidate_name}
              </h4>
              <span className={`inline-flex items-center px-1.5 py-0.5 text-micro font-medium rounded-full ${classification.bg} ${classification.color}`}>
                {classification.label}
              </span>
            </div>
          </div>

          <div className="text-right">
            <div className={`text-2xl font-semibold ${scoreDisplay.text}`}>
              {percentage}%
            </div>
            <div className="text-xs text-lia-text-tertiary">
              {data.overall_score}/{data.max_score} pts
            </div>
          </div>
        </div>

        <div className="mt-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-lia-text-secondary">Score Geral</span>
            {getRecommendationBadge(data.recommendation)}
          </div>
          <div
            className="relative h-2 rounded-full overflow-hidden bg-lia-bg-tertiary"
          >
            <div
              className="absolute inset-y-0 left-0 rounded-full transition-[width,height] duration-500 bg-lia-text-primary"
              style={{width: `${percentage}%`}}
            />
          </div>
        </div>

        {!compact && data.dimensions && data.dimensions.length > 0 && (
          <div className="mt-4 space-y-2">
            <div className="text-sm font-medium text-lia-text-primary">
              Dimensões Avaliadas
            </div>
            {data.dimensions.slice(0, 4).map((dimension, index) => {
              const dimPercent = Math.round((dimension.score / dimension.max_score) * 100)
              return (
                <div key={dimension.name} className="flex items-center gap-2">
                  {getDimensionIcon(dimension.score / dimension.max_score)}
                  <span
                    className="text-sm flex-1 truncate text-lia-text-secondary"
                  >
                    {dimension.name}
                  </span>
                  <div
                    className="w-20 h-1.5 rounded-full overflow-hidden bg-lia-bg-tertiary"
                  >
                    <div
                      className="h-full rounded-full bg-lia-text-secondary"
                      style={{width: `${dimPercent}%`}}
                    />
                  </div>
                  <span
                    className="text-xs w-8 text-right text-lia-text-tertiary"
                  >
                    {dimPercent}%
                  </span>
                </div>
              )
            })}
          </div>
        )}

        {!compact && data.strengths && data.strengths.length > 0 && (
          <div className="mt-4">
            <div className="text-sm font-medium mb-2 text-lia-text-primary">
              Pontos Fortes
            </div>
            <div className="space-y-1">
              {data.strengths.slice(0, 2).map((strength, index) => (
                <div
                  key={`strength-${index}`}
                  className="flex items-start gap-2 text-xs px-2 py-1 rounded-xl bg-lia-bg-tertiary text-lia-text-secondary"
                >
                  <Star className="h-3 w-3 mt-0.5 shrink-0 text-wedo-green" />
                  <span>{strength}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {!compact && data.development_areas && data.development_areas.length > 0 && (
          <div className="mt-3">
            <div className="text-sm font-medium mb-2 text-lia-text-primary">
              Áreas de Desenvolvimento
            </div>
            <div className="space-y-1">
              {data.development_areas.slice(0, 2).map((area, index) => (
                <div
                  key={`area-${index}`}
                  className="flex items-start gap-2 text-xs px-2 py-1 rounded-xl bg-lia-bg-tertiary text-lia-text-secondary"
                >
                  <TrendingUp className="h-3 w-3 mt-0.5 shrink-0 text-lia-text-secondary" />
                  <span>{area}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {data.summary && !compact && (
          <div
            className="mt-4 p-3 rounded-xl bg-lia-bg-tertiary"
          >
            <div className="text-xs mb-1 text-lia-text-tertiary">
              Resumo da Avaliação
            </div>
            <p className="text-sm line-clamp-3 text-lia-text-secondary">
              {data.summary}
            </p>
          </div>
        )}

        {(onViewDetails || onViewReport) && (
          <div
            className="mt-4 pt-3 border-t flex items-center gap-2 border-lia-border-subtle"
          >
            {onViewReport && (
              <Button
                size="sm"
                variant="outline"
                className="border-lia-border-default text-lia-text-primary hover:bg-lia-interactive-hover transition-colors cursor-pointer"
                onClick={onViewReport}
              >
                <FileText className="h-3.5 w-3.5 mr-1.5" />
                Ver Parecer
              </Button>
            )}
            {onViewDetails && (
              <Button
                size="sm"
                variant="ghost"
                className="ml-auto text-lia-text-secondary hover:bg-lia-interactive-hover transition-colors cursor-pointer"
                onClick={onViewDetails}
              >
                Detalhes Completos
                <ExternalLink className="h-3.5 w-3.5 ml-1.5" />
              </Button>
            )}
          </div>
        )}

        {data.evaluated_at && (
          <div
            className="mt-3 text-xs text-right text-lia-text-tertiary"
          >
            Avaliado em {data.evaluated_at}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
