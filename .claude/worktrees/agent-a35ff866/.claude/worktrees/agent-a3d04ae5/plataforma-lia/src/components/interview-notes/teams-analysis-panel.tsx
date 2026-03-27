"use client"

import * as React from "react"
import { useState } from "react"
import {
  Video,
  Loader2,
  CheckCircle,
  XCircle,
  AlertCircle,
  Clock,
  Bot,
  RefreshCw,
} from "lucide-react"
import { Card, CardHeader, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { InterviewAnalysisStatus, InterviewAnalysisResult } from "@/types/interview-notes"
import { cn } from "@/lib/utils"

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
    label: "Aguardando Transcrição",
    color: "bg-gray-100 text-gray-700",
    icon: Clock,
  },
  transcript_ready: {
    label: "Transcrição Pronta",
    color: "bg-blue-100 text-blue-700",
    icon: Video,
  },
  scheduled: {
    label: "Análise Agendada",
    color: "bg-yellow-100 text-yellow-700",
    icon: Clock,
  },
  analyzed: {
    label: "Analisado",
    color: "bg-green-100 text-green-700",
    icon: CheckCircle,
  },
  completed: {
    label: "Concluído",
    color: "bg-green-100 text-green-700",
    icon: CheckCircle,
  },
}

const recommendationConfig: Record<
  InterviewAnalysisResult["recommendation"],
  { label: string; color: string; icon: React.ElementType }
> = {
  approve: {
    label: "Aprovar",
    color: "bg-green-100 text-green-700 border-green-200",
    icon: CheckCircle,
  },
  reject: {
    label: "Reprovar",
    color: "bg-red-100 text-red-700 border-red-200",
    icon: XCircle,
  },
  pending_review: {
    label: "Revisão Necessária",
    color: "bg-yellow-100 text-yellow-700 border-yellow-200",
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
            <div className="text-3xl font-bold text-gray-900 dark:text-gray-50">
              {result.overall_wsi_score.toFixed(1)}
            </div>
            <div className="text-xs text-gray-500 dark:text-gray-400">Score WSI</div>
          </div>
          <div
            className={cn(
              "flex items-center gap-1.5 px-3 py-1.5 rounded-full border",
              recConfig.color
            )}
          >
            <RecIcon className="h-4 w-4" />
            <span className="text-sm font-medium">{recConfig.label}</span>
          </div>
        </div>
        <div className="text-right">
          <div className="text-sm text-gray-500 dark:text-gray-400">STAR Completeness</div>
          <div className="text-lg font-semibold text-gray-900 dark:text-gray-50">
            {(result.star_completeness * 100).toFixed(0)}%
          </div>
        </div>
      </div>

      {result.key_insights.length > 0 && (
        <div className="space-y-2">
          <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300">Pontos Fortes</h4>
          <ul className="space-y-1">
            {result.key_insights.map((insight, idx) => (
              <li
                key={idx}
                className="flex items-start gap-2 text-sm text-gray-600 dark:text-gray-400"
              >
                <CheckCircle className="h-4 w-4 text-green-500 mt-0.5 flex-shrink-0" />
                <span>{insight}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {result.concerns.length > 0 && (
        <div className="space-y-2">
          <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300">Pontos de Atenção</h4>
          <ul className="space-y-1">
            {result.concerns.map((concern, idx) => (
              <li
                key={idx}
                className="flex items-start gap-2 text-sm text-gray-600 dark:text-gray-400"
              >
                <AlertCircle className="h-4 w-4 text-amber-500 mt-0.5 flex-shrink-0" />
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
      <Card className="w-full rounded-md dark:bg-gray-800 dark:border-gray-700">
        <CardContent className="flex items-center justify-center py-8">
          <Loader2 className="h-6 w-6 animate-spin text-gray-400" />
          <span className="ml-2 text-sm text-gray-500 dark:text-gray-400">Carregando status...</span>
        </CardContent>
      </Card>
    )
  }

  const statusInfo = status ? statusConfig[status.status] : null
  const StatusIcon = statusInfo?.icon || Clock

  return (
    <Card className="w-full rounded-md dark:bg-gray-800 dark:border-gray-700">
      <CardHeader className="pb-3 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Bot className="h-5 w-5 text-wedo-cyan" />
            <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-50" style={{ fontFamily: "'Open Sans', sans-serif" }}>
              Análise de Entrevista Teams
            </h3>
          </div>
          <div className="flex items-center gap-2">
            {status && (
              <Badge className={cn("gap-1", statusInfo?.color)}>
                <StatusIcon className="h-3 w-3" />
                {statusInfo?.label}
              </Badge>
            )}
            <Button
              variant="ghost"
              size="sm"
              onClick={onRefresh}
              disabled={isLoading || isAnalyzing}
              className="h-8 w-8 p-0"
            >
              <RefreshCw className={cn("h-4 w-4", isLoading && "animate-spin")} />
            </Button>
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {!status && (
          <div className="text-center py-6 bg-gray-50 rounded-md">
            <Video className="h-8 w-8 text-gray-400 mx-auto mb-2" />
            <p className="text-sm text-gray-500 dark:text-gray-400">
              Nenhuma análise disponível para esta entrevista.
            </p>
          </div>
        )}

        {status?.error && (
          <div className="flex items-start gap-2 p-3 bg-red-50 border border-red-200 rounded-md">
            <XCircle className="h-4 w-4 text-red-500 mt-0.5" />
            <p className="text-sm text-red-700">{status.error}</p>
          </div>
        )}

        {status?.status === "awaiting_transcript" && (
          <div className="text-center py-6 bg-gray-50 rounded-md">
            <Clock className="h-8 w-8 text-gray-400 mx-auto mb-2" />
            <p className="text-sm text-gray-600 mb-1">
              Aguardando transcrição da entrevista Teams
            </p>
            <p className="text-xs text-gray-500">
              A transcrição será processada automaticamente quando disponível.
            </p>
          </div>
        )}

        {status?.status === "transcript_ready" && (
          <div className="text-center py-6 bg-blue-50 rounded-md space-y-3">
            <Video className="h-8 w-8 text-blue-500 mx-auto" />
            <p className="text-sm text-gray-700">
              Transcrição disponível! Clique para iniciar a análise.
            </p>
            <Button
              onClick={() => handleAnalyze(false)}
              disabled={isAnalyzing}
              className="gap-2 bg-gray-900 hover:bg-gray-800 text-white dark:bg-gray-50 dark:text-gray-900 dark:hover:bg-gray-200"
            >
              {isAnalyzing ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
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

        {(status?.status === "analyzed" || status?.status === "completed") &&
          status.analysis_result && (
            <>
              <AnalysisResultDisplay result={status.analysis_result} />
              <div className="pt-3 border-t dark:border-gray-700">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleAnalyze(true)}
                  disabled={isAnalyzing}
                  className="gap-2 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-700"
                >
                  {isAnalyzing ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin" />
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

        {status?.status === "scheduled" && (
          <div className="text-center py-6 bg-yellow-50 rounded-md">
            <Clock className="h-8 w-8 text-yellow-500 mx-auto mb-2" />
            <p className="text-sm text-gray-700">
              Análise agendada e será processada em breve.
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
