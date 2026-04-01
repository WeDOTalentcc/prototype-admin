"use client"

import React from "react"
import { User, Mail, Phone, MapPin, Briefcase, GraduationCap, AlertTriangle, CheckCircle2, Star, TrendingUp, Lightbulb } from "lucide-react"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { cn } from "@/lib/utils"
import { type ResumeAnalysisResponse } from "@/services/lia-api"

interface ResumeAnalysisResultProps {
  result: ResumeAnalysisResponse
  className?: string
  compact?: boolean
}

export function ResumeAnalysisResult({ 
  result, 
  className,
  compact = false 
}: ResumeAnalysisResultProps) {
  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-status-success'
    if (score >= 60) return 'text-status-warning'
    return 'text-status-error'
  }

  const getScoreBgColor = (score: number) => {
    if (score >= 80) return 'bg-status-success'
    if (score >= 60) return 'bg-status-warning'
    return 'bg-status-error'
  }

  const getScoreLabel = (score: number) => {
    if (score >= 80) return 'Excelente'
    if (score >= 60) return 'Bom'
    if (score >= 40) return 'Regular'
    return 'Precisa melhorar'
  }

  if (compact) {
    return (
      <div className={cn("bg-lia-bg-primary border rounded-md p-4", className)}>
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gray-100 dark:bg-lia-bg-secondary rounded-full flex items-center justify-center">
              <User className="h-5 w-5 lia-text-600 dark:text-lia-text-tertiary" />
            </div>
            <div>
              <p className="font-medium lia-text-900">{result.candidate_name || 'Nome não identificado'}</p>
              {/* @ts-ignore TODO: fix type */}
              <div className="flex items-center gap-2 text-xs lia-text-500 mt-0.5">
                {(result.contact_info?.email as any) && (
                  {/* @ts-ignore TODO: fix type */}
                  <span className="flex items-center gap-1">
                    <Mail className="h-3 w-3" />
                    {(result.contact_info.email as React.ReactNode)}
                  </span>
                )}
              </div>
            </div>
          </div>
          
          <div className="text-right">
            <div className={cn("text-lg font-bold", getScoreColor(result.layout_score))}>
              {result.layout_score}%
            </div>
            <div className="text-xs lia-text-500">Layout Score</div>
          </div>
        </div>

        {result.improvement_suggestions.length > 0 && (
          <div className="mt-3 pt-3 border-t">
            <p className="text-xs font-medium lia-text-700 mb-2 flex items-center gap-1">
              <Lightbulb className="h-3 w-3 text-status-warning" />
              {result.improvement_suggestions.length} sugestão{result.improvement_suggestions.length > 1 ? 'ões' : ''} de melhoria
            </p>
          </div>
        )}
      </div>
    )
  }

  return (
    <Card className={cn("overflow-hidden", className)}>
      <CardHeader className="bg-gradient-to-r from-gray-100 dark:lia-from-800 to-white pb-4">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-4">
            <div className="w-14 h-14 bg-gray-100 dark:bg-lia-bg-secondary rounded-full flex items-center justify-center">
              <User className="h-7 w-7 lia-text-600 dark:text-lia-text-tertiary" />
            </div>
            <div>
              <CardTitle className="text-lg">
                {result.candidate_name || 'Nome não identificado'}
              </CardTitle>
              {/* @ts-ignore TODO: fix type */}
              <div className="flex flex-wrap items-center gap-3 text-sm lia-text-600 mt-1">
                {(result.contact_info?.email as any) && (
                  <span className="flex items-center gap-1">
                    <Mail className="h-3.5 w-3.5" />
                    {(result.contact_info.email as React.ReactNode)}
                  </span>
                )}
                {(result.contact_info?.phone as any) && (
                  <span className="flex items-center gap-1">
                    <Phone className="h-3.5 w-3.5" />
                    {(result.contact_info.phone as React.ReactNode)}
                  </span>
                )}
                {(result.contact_info?.location as any) && (
                  <span className="flex items-center gap-1">
                    <MapPin className="h-3.5 w-3.5" />
                    {(result.contact_info.location as React.ReactNode)}
                  </span>
                )}
              </div>
            </div>
          </div>
        </div>
      </CardHeader>

      <CardContent className="pt-4 space-y-6">
        <div className="bg-gray-50 rounded-md p-4">
          <div className="flex items-center justify-between mb-3">
            <span className="text-sm font-medium lia-text-700 flex items-center gap-2">
              <Star className="h-4 w-4 text-status-warning" />
              Qualidade do Layout
            </span>
            <div className="flex items-center gap-2">
              <span className={cn("text-2xl font-bold", getScoreColor(result.layout_score))}>
                {result.layout_score}%
              </span>
              <span className={cn(
                "text-xs px-2 py-0.5 rounded-full",
                result.layout_score >= 80 
                  ? "bg-status-success/15 text-status-success"
                  : result.layout_score >= 60
                    ? "bg-status-warning/15 text-status-warning"
                    : "bg-status-error/15 text-status-error"
              )}>
                {getScoreLabel(result.layout_score)}
              </span>
            </div>
          </div>
          <Progress 
            value={result.layout_score} 
            className={cn("h-3", getScoreBgColor(result.layout_score))}
          />
          <p className="text-xs lia-text-500 mt-2">
            Avaliação baseada em estrutura, formatação e legibilidade do currículo
          </p>
        </div>

        {result.improvement_suggestions.length > 0 && (
          <div>
            <h4 className="text-sm font-medium lia-text-900 mb-3 flex items-center gap-2">
              <TrendingUp className="h-4 w-4 lia-text-600 dark:text-lia-text-tertiary" />
              Sugestões de Melhoria
            </h4>
            <ul className="space-y-2">
              {result.improvement_suggestions.map((suggestion, index) => (
                <li 
                  key={`suggestion-${index}`}
                  className="flex items-start gap-3 p-3 bg-status-warning/10 rounded-md border border-status-warning/30"
                >
                  <AlertTriangle className="h-4 w-4 text-status-warning flex-shrink-0 mt-0.5" />
                  <span className="text-sm lia-text-700">{suggestion}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {result.improvement_suggestions.length === 0 && result.layout_score >= 80 && (
          <div className="flex items-center gap-3 p-4 bg-status-success/10 rounded-md border border-status-success/30">
            <CheckCircle2 className="h-5 w-5 text-status-success flex-shrink-0" />
            <div>
              <p className="text-sm font-medium text-status-success">Currículo bem estruturado!</p>
              <p className="text-xs text-status-success mt-0.5">
                O layout segue as melhores práticas de formatação.
              </p>
            </div>
          </div>
        )}

        {(result.contact_info?.linkedin as any) && (
          <div className="pt-4 border-t">
            <a 
              // @ts-ignore TODO: fix type
              href={result.contact_info.linkedin}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 text-sm lia-text-600 dark:text-lia-text-tertiary hover:lia-text-900"
            >
              <Briefcase className="h-4 w-4" />
              Ver perfil no LinkedIn
            </a>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
