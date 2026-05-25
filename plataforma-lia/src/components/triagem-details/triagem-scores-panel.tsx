"use client"

import { Progress } from "@/components/ui/progress"
import { Brain, Mic, MessageSquare, TrendingUp, BarChart3, Layers } from "lucide-react"
import type { WSIResultDetails } from "@/services/lia-api"

interface F11ReportData {
  seniority?: string
  seniority_weights?: { technical: number; behavioral: number }
  mode?: string
  question_count?: number
  [key: string]: unknown
}

interface TriagemScoresPanelProps {
  scores: WSIResultDetails["scores"]
  sessionInfo: WSIResultDetails["session"]
  f11Report: F11ReportData | null
  details: WSIResultDetails
}

// Escala WSI 0-10 (Task #512).
const wsiToPercent = (score: number) => Math.round((score / 10) * 100)

export function TriagemScoresPanel({ scores, sessionInfo, f11Report, details }: TriagemScoresPanelProps) {
  return (
    <div className="p-3 border border-lia-border-subtle bg-lia-bg-secondary rounded-lg">
      <h3 className="text-xs font-semibold flex items-center gap-2 mb-3 text-lia-text-primary">
        <Brain className="w-4 h-4 text-wedo-cyan" />
        Scores por Dimensão
      </h3>
      <div className="grid grid-cols-3 gap-3">
        <div className="text-center p-3 rounded-lg border border-lia-border-subtle">
          <p className="text-xl font-semibold text-lia-text-primary">{scores.overall_wsi.toFixed(1)}</p>
          <p className="text-micro text-lia-text-secondary">Geral ({wsiToPercent(scores.overall_wsi)}%)</p>
          <Progress value={wsiToPercent(scores.overall_wsi)} className="h-1.5 mt-1.5" />
        </div>
        <div className="text-center p-3 rounded-lg border border-lia-border-subtle">
          <p className="text-xl font-semibold text-lia-text-primary">{scores.technical_wsi.toFixed(1)}</p>
          <p className="text-micro text-lia-text-secondary">Comp. Técnicas ({wsiToPercent(scores.technical_wsi)}%)</p>
          <Progress value={wsiToPercent(scores.technical_wsi)} className="h-1.5 mt-1.5" />
        </div>
        <div className="text-center p-3 rounded-lg border border-lia-border-subtle">
          <p className="text-xl font-semibold text-lia-text-primary">{scores.behavioral_wsi.toFixed(1)}</p>
          <p className="text-micro text-lia-text-secondary">Comp. Comportamentais ({wsiToPercent(scores.behavioral_wsi)}%)</p>
          <Progress value={wsiToPercent(scores.behavioral_wsi)} className="h-1.5 mt-1.5" />
        </div>
      </div>
      <div className="flex items-center gap-3 mt-3 flex-wrap">
        <span className="flex items-center gap-1 text-micro text-lia-text-secondary bg-lia-bg-tertiary px-2 py-1 rounded-full">
          {sessionInfo.screening_type === 'voice' ? <Mic className="w-3 h-3" /> : <MessageSquare className="w-3 h-3" />}
          {sessionInfo.screening_type === 'voice' ? 'Triagem por Voz' : 'Triagem por Texto'}
        </span>
        {scores.percentile && (
          <span className="text-micro text-lia-text-secondary flex items-center gap-1">
            <TrendingUp className="w-3 h-3" />
            Top {100 - scores.percentile}%
          </span>
        )}
        {sessionInfo.started_at && (
          <span className="text-micro text-lia-text-secondary">
            {new Date(sessionInfo.started_at).toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' })}
          </span>
        )}
      </div>
      {f11Report?.seniority_weights && (
        <div className="flex items-center gap-1.5 text-xs text-lia-text-secondary bg-lia-bg-secondary border border-lia-border-subtle rounded-lg px-3 py-2 mt-2">
          <BarChart3 className="w-3 h-3 text-lia-text-secondary shrink-0" />
          <span>
            Para <span className="font-medium text-lia-text-secondary">{f11Report.seniority || details?.session?.seniority_label || 'N/A'}</span>: Competências Técnicas valem{' '}
            <span className="font-semibold text-lia-text-secondary">{Math.round(f11Report.seniority_weights.technical * 100)}%</span> e Comportamentais valem{' '}
            <span className="font-semibold text-lia-text-secondary">{Math.round(f11Report.seniority_weights.behavioral * 100)}%</span> do score final
          </span>
        </div>
      )}
      {f11Report?.mode && (
        <div className="flex items-center gap-2 mt-2">
          <span className="text-micro text-lia-text-secondary">Modo de triagem:</span>
          <span className="text-micro font-medium text-lia-text-secondary flex items-center gap-1">
            <Layers className="w-3 h-3 text-lia-text-secondary" />
            {f11Report.mode === 'compact' ? 'Compact' : f11Report.mode === 'full' ? 'Full' : f11Report.mode}
            {f11Report.question_count ? ` · ${f11Report.question_count} perguntas` : ''}
          </span>
        </div>
      )}
    </div>
  )
}
