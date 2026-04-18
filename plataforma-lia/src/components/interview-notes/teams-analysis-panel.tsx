"use client"

import * as React from"react"
import { useState } from"react"
import {
  Video,
  Loader2,
  CheckCircle,
  XCircle,
  AlertCircle,
  Clock,
  Bot,
  RefreshCw,
} from"lucide-react"
import { Card, CardHeader, CardContent } from"@/components/ui/card"
import { Button } from"@/components/ui/button"
import { Chip } from "@/components/ui/chip"
import { InterviewAnalysisStatus, InterviewAnalysisResult } from"@/types/interview-notes"
import { cn } from"@/lib/utils"

interface TeamsAnalysisPanelProps {
  interviewId: string
  status: InterviewAnalysisStatus | null
  isLoading?: boolean
  onAnalyze: (forceRefresh?: boolean) => Promise<void>
  onRefresh: () => void
}

const statusConfig: Record<
  InterviewAnalysisStatus["status"],
  { label: string; color: string; icon: React.ElementType }
> = {
  awaiting_transcript: {
    label:"Aguardando Transcrição",
    color:"bg-lia-bg-tertiary text-lia-text-secondary",
    icon: Clock,
  },
  transcript_ready: {
    label:"Transcrição Pronta",
    color:"",
    icon: Video,
  },
  scheduled: {
    label:"Análise Agendada",
    color:"",
    icon: Clock,
  },
  analyzed: {
    label:"Analisado",
    color:"",
    icon: CheckCircle,
  },
  completed: {
    label:"Concluído",
    color:"",
    icon: CheckCircle,
  },
}

const recommendationConfig: Record<
  InterviewAnalysisResult["recommendation"],
  { label: string; color: string; icon: React.ElementType }
> = {
  approve: {
    label:"Aprovar",
    color:" border-status-success/30",
    icon: CheckCircle,
  },
  reject: {
    label:"Reprovar",
    color:" border-status-error/30",
    icon: XCircle,
  },
  pending_review: {
    label:"Revisão Necessária",
    color:" border-status-warning/30",
    icon: AlertCircle,
  },
}

function AnalysisResultDisplay({ result }: { result: InterviewAnalysisResult }) {
  const recConfig = recommendationConfig[result.recommendation]
  const RecIcon = recConfig.icon

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="text-center">
            <div className="text-3xl font-semibold text-lia-text-primary">
              {result.overall_wsi_score.toFixed(1)}
            </div>
            <div className="text-xs text-lia-text-tertiary">Score WSI</div>
          </div>
          <div
            className={cn("flex items-center gap-1.5 px-3 py-1.5 rounded-full border",
              recConfig.color
            )}
          >
            <RecIcon className="h-4 w-4" />
            <span className="text-sm font-medium">{recConfig.label}</span>
          </div>
        </div>
        <div className="text-right">
          <div className="text-sm text-lia-text-tertiary">STAR Completeness</div>
          <div className="text-lg font-semibold text-lia-text-primary">
            {(result.star_completeness * 100).toFixed(0)}%
          </div>
        </div>
      </div>

      {result.key_insights.length > 0 && (
        <div className="space-y-2">
          <h4 className="text-sm font-medium text-lia-text-secondary">Pontos Fortes</h4>
          <ul className="space-y-1">
            {result.key_insights.map((insight, idx) => (
              <li
                key={idx}
                className="flex items-start gap-2 text-sm text-lia-text-secondary"
              >
                <CheckCircle className="h-4 w-4 text-status-success mt-0.5 flex-shrink-0" />
                <span>{insight}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {result.concerns.length > 0 && (
        <div className="space-y-2">
          <h4 className="text-sm font-medium text-lia-text-secondary">Pontos de Atenção</h4>
          <ul className="space-y-1">
            {result.concerns.map((concern, idx) => (
              <li
                key={idx}
                className="flex items-start gap-2 text-sm text-lia-text-secondary"
              >
                <AlertCircle className="h-4 w-4 text-status-warning mt-0.5 flex-shrink-0" />
                <span>{concern}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}

export function TeamsAnalysisPanel({
  interviewId,
  status,
  isLoading = false,
  onAnalyze,
  onRefresh,
}: TeamsAnalysisPanelProps) {
  const [isAnalyzing, setIsAnalyzing] = useState(false)

  const handleAnalyze = async (forceRefresh = false) => {
    setIsAnalyzing(true)
    try {
      await onAnalyze(forceRefresh)
    } finally {
      setIsAnalyzing(false)
    }
  }

  if (isLoading) {
    return (
      <Card className="w-full rounded-xl dark:bg-lia-bg-secondary dark:border-lia-border-subtle">
        <CardContent className="flex items-center justify-center py-8">
          <Loader2 className="h-6 w-6 animate-spin motion-reduce:animate-none text-lia-text-secondary" />
          <span className="ml-2 text-sm text-lia-text-tertiary">Carregando status...</span>
        </CardContent>
      </Card>
    )
  }

  const statusInfo = status ? statusConfig[status.status] : null
  const StatusIcon = statusInfo?.icon || Clock

  return (
    <Card className="w-full rounded-xl dark:bg-lia-bg-secondary dark:border-lia-border-subtle">
      <CardHeader className="pb-3 dark:border-lia-border-subtle">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Bot className="h-5 w-5 text-wedo-cyan" />
            <h3 className="text-sm font-semibold text-lia-text-primary">
              Análise de Entrevista Teams
            </h3>
          </div>
          <div className="flex items-center gap-2">
            {status && (
              <Chip variant="neutral" muted className={cn("gap-1", statusInfo?.color)}>
                <StatusIcon className="h-3 w-3" />
                {statusInfo?.label}
              </Chip>
            )}
            <Button
              variant="ghost"
              size="sm"
              onClick={onRefresh}
              disabled={isLoading || isAnalyzing}
              className="h-8 w-8 p-0"
            >
              <RefreshCw className={cn("h-4 w-4", isLoading &&"animate-spin motion-reduce:animate-none")} />
            </Button>
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {!status && (
          <div className="text-center py-6 bg-lia-bg-secondary rounded-xl">
            <Video className="h-8 w-8 text-lia-text-secondary mx-auto mb-2" />
            <p className="text-sm text-lia-text-tertiary">
              Nenhuma análise disponível para esta entrevista.
            </p>
          </div>
        )}

        {status?.error && (
          <div className="flex items-start gap-2 p-3 bg-status-error/10 border border-status-error/30 rounded-xl">
            <XCircle className="h-4 w-4 text-status-error mt-0.5" />
            <p className="text-sm text-status-error">{status.error}</p>
          </div>
        )}

        {status?.status ==="awaiting_transcript" && (
          <div className="text-center py-6 bg-lia-bg-secondary rounded-xl">
            <Clock className="h-8 w-8 text-lia-text-secondary mx-auto mb-2" />
            <p className="text-sm text-lia-text-secondary mb-1">
              Aguardando transcrição da entrevista Teams
            </p>
            <p className="text-xs text-lia-text-secondary">
              A transcrição será processada automaticamente quando disponível.
            </p>
          </div>
        )}

        {status?.status ==="transcript_ready" && (
          <div className="text-center py-6 bg-wedo-cyan/10 rounded-xl space-y-3">
            <Video className="h-8 w-8 text-wedo-cyan-dark mx-auto" />
            <p className="text-sm text-lia-text-secondary">
              Transcrição disponível! Clique para iniciar a análise.
            </p>
            <Button
              onClick={() => handleAnalyze(false)}
              disabled={isAnalyzing}
              className="gap-2 bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text dark:hover:bg-lia-interactive-active"
            >
              {isAnalyzing ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin motion-reduce:animate-none" />
                  Analisando...
                </>
              ) : (
                <>
                  <Bot className="h-4 w-4" />
                  Analisar Agora
                </>
              )}
            </Button>
          </div>
        )}

        {(status?.status ==="analyzed" || status?.status ==="completed") &&
          status.analysis_result && (
            <>
              <AnalysisResultDisplay result={status.analysis_result} />
              <div className="pt-3 border-t dark:border-lia-border-subtle">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleAnalyze(true)}
                  disabled={isAnalyzing}
                  className="gap-2 dark:border-lia-border-default dark:hover:bg-lia-bg-inverse"
                >
                  {isAnalyzing ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin motion-reduce:animate-none" />
                      Reanalisando...
                    </>
                  ) : (
                    <>
                      <RefreshCw className="h-4 w-4" />
                      Reanalisar
                    </>
                  )}
                </Button>
              </div>
            </>
          )}

        {status?.status ==="scheduled" && (
          <div className="text-center py-6 bg-status-warning/10 rounded-md">
            <Clock className="h-8 w-8 text-status-warning mx-auto mb-2" />
            <p className="text-sm text-lia-text-secondary">
              Análise agendada e será processada em breve.
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
