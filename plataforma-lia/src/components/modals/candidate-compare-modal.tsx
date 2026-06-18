"use client"

/**
 * D9 — Modal de Análise Comparativa Visual
 *
 * Renderiza resultado de comparação lado a lado para 2-4 candidatos.
 * Lazy-load: fetch ocorre ao abrir o modal.
 */
import React, { useEffect } from "react"
import { getPercentageScoreColorClass } from "@/lib/score-utils"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Loader2, Trophy, AlertCircle, Users } from "lucide-react"
import { cn } from "@/lib/utils"
import { useCandidateCompare } from "@/hooks/candidates/use-candidate-compare"

interface CandidateInfo {
  id: string
  name: string
}

interface CandidateCompareModalProps {
  open: boolean
  onClose: () => void
  candidates: CandidateInfo[]
  jobId?: string
  companyId?: string
}

function getScoreColor(score: number): string {
  return getPercentageScoreColorClass(score)
}

function ScoreBar({ value, max = 100 }: { value: number | null; max?: number }) {
  if (value == null) return <span className="text-micro text-lia-text-muted">—</span>
  const pct = Math.round((value / max) * 100)
  return (
    <div className="flex items-center gap-1.5">
      <div className="flex-1 h-1.5 bg-lia-interactive-active rounded-full">
        <div
          className={cn(
            "h-1.5 rounded-full",
            pct >= 80 ? "bg-status-success" : pct >= 60 ? "bg-status-warning" : "bg-status-error"
          )}
          style={{width: `${pct}%`}}
        />
      </div>
      <span className={cn("text-micro font-semibold w-8 text-right", getScoreColor(value))}>
        {Math.round(value)}
      </span>
    </div>
  )
}

import { useLiaModalTracking } from '@/lib/use-lia-modal-tracking'

export function CandidateCompareModal({
  open,
  onClose,
  candidates,
  jobId,
  companyId,
}: CandidateCompareModalProps) {
  // P0-2 (2026-06-18): notify LIA which modal is open
  useLiaModalTracking('candidate-compare', open)
  const { data, loading, error, compare, reset } = useCandidateCompare()

  useEffect(() => {
    if (open && candidates.length >= 2) {
      compare(
        candidates.map((c) => c.id),
        jobId,
        companyId
      )
    }
    if (!open) reset()
  }, [open]) // eslint-disable-line react-hooks/exhaustive-deps

  const nameById = Object.fromEntries(candidates.map((c) => [c.id, c.name]))

  return (
    <Dialog open={open} onOpenChange={(v) => !v && onClose()}>
      <DialogContent className="max-w-2xl" data-testid="candidate-compare-modal">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2 text-sm font-semibold">
            <Users className="h-4 w-4" />
            Comparação de Candidatos
          </DialogTitle>
        </DialogHeader>

        {loading && (
          <div className="flex items-center justify-center py-10" role="status" aria-live="polite" aria-label="Carregando...">
            <Loader2 className="h-5 w-5 animate-spin motion-reduce:animate-none text-lia-text-muted" />
            <span className="ml-2 text-sm text-lia-text-tertiary">Comparando...</span>
          </div>
        )}

        {error && !loading && (
          <div className="flex items-center gap-2 py-4 text-sm text-lia-text-tertiary">
            <AlertCircle className="h-4 w-4 text-status-warning" />
            <span>{error}</span>
          </div>
        )}

        {data && !loading && (
          <div className="space-y-4">
            {/* Winner banner */}
            {data.winner && (
              <div className="flex items-center gap-2 p-3 bg-status-success/10 dark:bg-status-success/20 rounded-lg border border-status-success/30 dark:border-status-success/30">
                <Trophy className="h-4 w-4 text-status-success" />
                <div>
                  <span className="text-xs font-semibold text-status-success" aria-live="polite" aria-atomic="true">
                    Candidato indicado: {data.winner_name || nameById[data.winner] || data.winner}
                  </span>
                  <span className="ml-2 text-micro text-status-success opacity-70">
                    Confiança: {Math.round(data.confidence * 100)}%
                  </span>
                </div>
              </div>
            )}

            {/* Scores gerais */}
            <div>
              <p className="text-xs font-semibold text-lia-text-secondary mb-2">
                Score Geral
              </p>
              <div className="grid gap-1.5">
                {Object.entries(data.candidate_scores).map(([cId, score]) => (
                  <div key={cId} className="grid grid-cols-[1fr_auto] items-center gap-2">
                    <div>
                      <p className="text-micro font-medium text-lia-text-primary truncate">
                        {nameById[cId] || cId}
                      </p>
                      <ScoreBar value={score} />
                    </div>
                    <span className={cn("text-sm font-bold", getScoreColor(score))}>
                      {Math.round(score)}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* Dimensões */}
            {Object.keys(data.dimension_comparison).length > 0 && (
              <div>
                <p className="text-xs font-semibold text-lia-text-secondary mb-2">
                  Por Dimensão
                </p>
                <div className="space-y-2">
                  {Object.entries(data.dimension_comparison)
                    .slice(0, 5)
                    .map(([dim, scores]) => (
                      <div key={dim}>
                        <p className="text-micro text-lia-text-tertiary capitalize mb-1">
                          {dim.replace(/_/g, " ")}
                        </p>
                        <div className="grid gap-0.5">
                          {Object.entries(scores)
                            .filter(([, v]) => typeof v === "number")
                            .map(([cId, v]) => (
                              <div key={cId} className="flex items-center gap-2">
                                <span className="text-micro text-lia-text-tertiary w-20 truncate">
                                  {nameById[cId] || cId}
                                </span>
                                <div className="flex-1">
                                  <ScoreBar value={v as number} />
                                </div>
                              </div>
                            ))}
                        </div>
                      </div>
                    ))}
                </div>
              </div>
            )}

            {/* Análise */}
            {data.analysis && (
              <div className="pt-2 border-t border-lia-border-subtle">
                <p className="text-micro text-lia-text-secondary leading-relaxed line-clamp-4">
                  {data.analysis}
                </p>
              </div>
            )}
          </div>
        )}
      </DialogContent>
    </Dialog>
  )
}
