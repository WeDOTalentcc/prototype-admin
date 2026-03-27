"use client"

import React from "react"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Progress } from "@/components/ui/progress"
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
} from "lucide-react"

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
  recommendation: "Aprovado" | "Reprovado" | "Aguardando"
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

  const getScoreDisplay = (score: number) => {
    if (score >= 80) return { text: "text-wedo-green", icon: TrendingUp }
    if (score >= 60) return { text: "text-gray-700 dark:text-gray-300", icon: Minus }
    return { text: "text-wedo-magenta", icon: TrendingDown }
  }

  const getRecommendationBadge = (recommendation: string) => {
    const baseStyle = {
      borderColor: 'var(--lia-border-default)',
      backgroundColor: 'var(--lia-bg-primary)'
    }
    
    switch (recommendation) {
      case "Aprovado":
        return (
          <Badge 
            className="border"
            style={{ ...baseStyle, color: 'var(--lia-text-primary)' }}
          >
            <CheckCircle2 className="h-3 w-3 mr-1 text-wedo-green" />
            Aprovado
          </Badge>
        )
      case "Reprovado":
        return (
          <Badge 
            className="border"
            style={{ ...baseStyle, color: 'var(--lia-text-primary)' }}
          >
            <AlertCircle className="h-3 w-3 mr-1 text-wedo-magenta" />
            Reprovado
          </Badge>
        )
      default:
        return (
          <Badge 
            className="border"
            style={{ ...baseStyle, color: 'var(--lia-text-secondary)' }}
          >
            <Minus className="h-3 w-3 mr-1 text-gray-700 dark:text-gray-300" />
            Aguardando
          </Badge>
        )
    }
  }

  const getDimensionIcon = (score: number) => {
    const percent = score * 100
    if (percent >= 80) return <TrendingUp className="h-3 w-3 text-wedo-green" />
    if (percent >= 60) return <Minus className="h-3 w-3 text-gray-700 dark:text-gray-300" />
    return <TrendingDown className="h-3 w-3 text-wedo-magenta" />
  }

  const scoreDisplay = getScoreDisplay(percentage)

  return (
    <Card 
      className="w-full max-w-md border-l-4 overflow-hidden"
      style={{ 
        backgroundColor: 'var(--lia-bg-secondary)',
        borderLeftColor: 'var(--lia-border-default)'
      }}
    >
      <CardContent className="p-4">
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-center gap-3">
            <div 
              className="h-12 w-12 rounded-full flex items-center justify-center"
              style={{ backgroundColor: 'var(--lia-bg-tertiary)' }}
            >
              <Brain className="h-6 w-6 text-wedo-purple" />
            </div>
            <div>
              <div className="text-sm" style={{ color: 'var(--lia-text-tertiary)' }}>Avaliação WSI</div>
              <h4 className="font-semibold" style={{ color: 'var(--lia-text-primary)' }}>
                {data.candidate_name}
              </h4>
            </div>
          </div>
          
          <div className="text-right">
            <div className={`text-2xl font-bold ${scoreDisplay.text}`}>
              {percentage}%
            </div>
            <div className="text-xs" style={{ color: 'var(--lia-text-tertiary)' }}>
              {data.overall_score}/{data.max_score} pts
            </div>
          </div>
        </div>

        <div className="mt-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm" style={{ color: 'var(--lia-text-secondary)' }}>Score Geral</span>
            {getRecommendationBadge(data.recommendation)}
          </div>
          <div 
            className="relative h-2 rounded-full overflow-hidden"
            style={{ backgroundColor: 'var(--lia-bg-tertiary)' }}
          >
            <div 
              className="absolute inset-y-0 left-0 rounded-full transition-all duration-500"
              style={{ 
                width: `${percentage}%`,
                backgroundColor: 'var(--lia-text-primary)'
              }}
            />
          </div>
        </div>

        {!compact && data.dimensions && data.dimensions.length > 0 && (
          <div className="mt-4 space-y-2">
            <div className="text-sm font-medium" style={{ color: 'var(--lia-text-primary)' }}>
              Dimensões Avaliadas
            </div>
            {data.dimensions.slice(0, 4).map((dimension, index) => {
              const dimPercent = Math.round((dimension.score / dimension.max_score) * 100)
              return (
                <div key={index} className="flex items-center gap-2">
                  {getDimensionIcon(dimension.score / dimension.max_score)}
                  <span 
                    className="text-sm flex-1 truncate"
                    style={{ color: 'var(--lia-text-secondary)' }}
                  >
                    {dimension.name}
                  </span>
                  <div 
                    className="w-20 h-1.5 rounded-full overflow-hidden"
                    style={{ backgroundColor: 'var(--lia-bg-tertiary)' }}
                  >
                    <div 
                      className="h-full rounded-full"
                      style={{ 
                        width: `${dimPercent}%`,
                        backgroundColor: 'var(--lia-text-secondary)'
                      }}
                    />
                  </div>
                  <span 
                    className="text-xs w-8 text-right"
                    style={{ color: 'var(--lia-text-tertiary)' }}
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
            <div className="text-sm font-medium mb-2" style={{ color: 'var(--lia-text-primary)' }}>
              Pontos Fortes
            </div>
            <div className="space-y-1">
              {data.strengths.slice(0, 2).map((strength, index) => (
                <div 
                  key={index}
                  className="flex items-start gap-2 text-xs px-2 py-1 rounded"
                  style={{ 
                    backgroundColor: 'var(--lia-bg-tertiary)',
                    color: 'var(--lia-text-secondary)'
                  }}
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
            <div className="text-sm font-medium mb-2" style={{ color: 'var(--lia-text-primary)' }}>
              Áreas de Desenvolvimento
            </div>
            <div className="space-y-1">
              {data.development_areas.slice(0, 2).map((area, index) => (
                <div 
                  key={index}
                  className="flex items-start gap-2 text-xs px-2 py-1 rounded"
                  style={{ 
                    backgroundColor: 'var(--lia-bg-tertiary)',
                    color: 'var(--lia-text-secondary)'
                  }}
                >
                  <TrendingUp className="h-3 w-3 mt-0.5 shrink-0 text-gray-700 dark:text-gray-300" />
                  <span>{area}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {data.summary && !compact && (
          <div 
            className="mt-4 p-3 rounded-md"
            style={{ backgroundColor: 'var(--lia-bg-tertiary)' }}
          >
            <div className="text-xs mb-1" style={{ color: 'var(--lia-text-tertiary)' }}>
              Resumo da Avaliação
            </div>
            <p className="text-sm line-clamp-3" style={{ color: 'var(--lia-text-secondary)' }}>
              {data.summary}
            </p>
          </div>
        )}

        {(onViewDetails || onViewReport) && (
          <div 
            className="mt-4 pt-3 border-t flex items-center gap-2"
            style={{ borderColor: 'var(--lia-border-subtle)' }}
          >
            {onViewReport && (
              <Button 
                size="sm" 
                variant="outline"
                style={{ 
                  borderColor: 'var(--lia-border-default)',
                  color: 'var(--lia-text-primary)'
                }}
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
                className="ml-auto"
                style={{ color: 'var(--lia-text-secondary)' }}
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
            className="mt-3 text-xs text-right"
            style={{ color: 'var(--lia-text-tertiary)' }}
          >
            Avaliado em {data.evaluated_at}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
