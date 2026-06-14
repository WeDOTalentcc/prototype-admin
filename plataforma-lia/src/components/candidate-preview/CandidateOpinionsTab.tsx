"use client"

import React from "react"
import { textStyles } from "@/lib/design-tokens"
import { Chip } from "@/components/ui/chip"
import { FileText, AlertCircle } from "lucide-react"
import { OpinionCard } from "@/components/candidate-preview/OpinionCard"

interface CandidateOpinionsTabProps {
  opinionsHistory: Record<string, any>[]
  isLoadingHistory: boolean
  isErrorHistory?: boolean
  onRetryHistory?: () => void
  expandedOpinionId: unknown
  setExpandedOpinionId: (id: unknown) => void
  copiedItemId: string | null
  handleCopyOpinion: (opinion: Record<string, any>) => void
}

export function CandidateOpinionsTab({
  opinionsHistory,
  isLoadingHistory,
  isErrorHistory,
  onRetryHistory,
  expandedOpinionId,
  setExpandedOpinionId,
  copiedItemId,
  handleCopyOpinion,
}: CandidateOpinionsTabProps) {
  return (
    <div className="p-3 space-y-3">
      {/* Loading */}
      {isLoadingHistory && (
        <div className="space-y-3">
          {[1, 2].map((i) => (
            <div key={i} className="bg-lia-bg-primary border border-lia-border-subtle rounded-xl p-4 animate-pulse motion-reduce:animate-none">
              <div className="flex items-center gap-3 mb-3">
                <div className="w-8 h-8 bg-lia-interactive-active rounded-full"></div>
                <div className="flex-1">
                  <div className="w-32 h-4 bg-lia-interactive-active rounded-md mb-1"></div>
                  <div className="w-24 h-3 bg-lia-interactive-active rounded-md"></div>
                </div>
              </div>
              <div className="space-y-2">
                <div className="w-full h-3 bg-lia-interactive-active rounded-md"></div>
                <div className="w-3/4 h-3 bg-lia-interactive-active rounded-md"></div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Error State (loud + retry) — substitui o catch silencioso anterior */}
      {!isLoadingHistory && isErrorHistory && (
        <div className="bg-lia-bg-primary border border-lia-border-subtle rounded-xl p-6 text-center" role="alert">
          <div className="w-12 h-12 rounded-full bg-status-warning/10 flex items-center justify-center mx-auto mb-3">
            <AlertCircle className="w-6 h-6 text-status-warning" />
          </div>
          <p className={`${textStyles.subtitle} mb-1`}>Não foi possível carregar os pareceres</p>
          {onRetryHistory && (
            <button onClick={onRetryHistory} className="text-xs text-wedo-cyan-text hover:underline mt-1">
              Tentar novamente
            </button>
          )}
        </div>
      )}

      {/* Empty State */}
      {!isLoadingHistory && !isErrorHistory && opinionsHistory.length === 0 && (
        <div className="bg-lia-bg-primary border border-lia-border-subtle rounded-xl p-6 text-center">
          <div className="w-12 h-12 rounded-full bg-lia-bg-tertiary flex items-center justify-center mx-auto mb-3">
            <FileText className="w-6 h-6 text-lia-text-muted" />
          </div>
          <p className={`${textStyles.subtitle} mb-1`}>Nenhum parecer disponível</p>
          <p className={textStyles.description}>
            Os pareceres são gerados ao analisar o candidato em uma vaga ou após triagens.
          </p>
        </div>
      )}

      {/* Opinions List — histórico versionado (pareceres job-directed + WSI) */}
      {!isLoadingHistory && !isErrorHistory && opinionsHistory.length > 0 && (
        <div className="space-y-3">
          {opinionsHistory.map((opinion: Record<string, any>) => (
            <div key={opinion.id as string} className="relative">
              {!opinion.is_current && (
                <Chip variant="neutral" muted className="absolute top-2 right-2 text-micro px-1.5 py-0 h-4 flex items-center bg-lia-bg-tertiary text-lia-text-tertiary z-10">
                  v{(opinion.version as React.ReactNode)} - Histórico
                </Chip>
              )}
              <OpinionCard
                opinion={opinion}
                isExpanded={expandedOpinionId === (opinion.id as string)}
                onToggle={() => setExpandedOpinionId(
                  expandedOpinionId === opinion.id ? null : opinion.id as string
                )}
                type={opinion.opinion_type === 'wsi' ? 'wsi' : 'general'}
                copiedItemId={copiedItemId}
                onCopyOpinion={handleCopyOpinion}
              />
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
