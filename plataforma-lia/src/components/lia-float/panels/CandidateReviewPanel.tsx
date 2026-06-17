"use client"

import React from "react"
import { Users, MapPin, Briefcase, GraduationCap, ThumbsUp, ThumbsDown, Bookmark, ChevronRight, CheckCircle2 } from "lucide-react"
import { cn } from "@/lib/utils"

interface ReviewCandidate {
  id: string | number
  name: string
  location?: string
  experience?: string
  education?: string
  match_score?: number
  current_title?: string
  current_company?: string
  status?: "pending" | "approved" | "rejected" | "saved"
}

interface CandidateReviewPanelProps {
  data: Record<string, unknown>
  onUpdateData?: (data: Record<string, unknown>) => void
}

function ScoreBadge({ score }: { score?: number }) {
  if (score == null) return null
  const pct = Math.round(score * 100)
  const color = pct >= 80 ? "text-status-success bg-status-success/10" : pct >= 60 ? "text-status-warning bg-status-warning/10" : "text-status-error bg-status-error/10"
  return (
    <span className={cn("text-micro font-semibold px-2 py-0.5 rounded-full", color)}>
      {pct}%
    </span>
  )
}

export function CandidateReviewPanel({ data, onUpdateData }: CandidateReviewPanelProps) {
  const candidates: ReviewCandidate[] = (data.candidates as ReviewCandidate[]) || []
  const totalReviewed = candidates.filter(c => c.status && c.status !== "pending").length
  const jobTitle = (data.job_title as string) || "Vaga"

  const handleAction = (candidateId: string | number, action: "approved" | "rejected" | "saved") => {
    const updated = candidates.map(c =>
      c.id === candidateId ? { ...c, status: action } : c
    )
    onUpdateData?.({ candidates: updated })
  }

  return (
    <div className="flex flex-col h-full">
      <div className="px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Users className="w-4 h-4 text-wedo-cyan" />
          <span className="text-sm font-semibold text-lia-text-primary">Review de Candidatos</span>
        </div>
        <span className="text-micro text-lia-text-muted">
          {totalReviewed}/{candidates.length} revisados
        </span>
      </div>

      <div className="px-4 py-2 bg-lia-bg-secondary">
        <p className="text-xs text-lia-text-secondary">{jobTitle}</p>
      </div>

      <div className="flex-1 overflow-y-auto px-4 py-3 space-y-3">
        {candidates.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center py-8">
            <Users className="w-8 h-8 text-lia-text-muted mb-2" />
            <p className="text-sm text-lia-text-disabled">Nenhum candidato para revisão</p>
          </div>
        ) : (
          candidates.map((c) => (
            <div
              key={c.id}
              className={cn(
                "p-3 rounded-lg border transition-colors",
                c.status === "approved" ? "border-status-success/30 bg-status-success/5" :
                c.status === "rejected" ? "border-status-error/30 bg-status-error/5" :
                c.status === "saved" ? "border-status-warning/30 bg-status-warning/5" :
                "border-lia-border-subtle bg-lia-bg-primary"
              )}
            >
              <div className="flex items-start justify-between mb-2">
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-lia-text-primary truncate">{c.name}</p>
                  {c.current_title && (
                    <p className="text-xs text-lia-text-secondary truncate">
                      {c.current_title}{c.current_company ? ` @ ${c.current_company}` : ""}
                    </p>
                  )}
                </div>
                <ScoreBadge score={c.match_score} />
              </div>

              <div className="flex flex-wrap gap-2 mb-2">
                {c.location && (
                  <span className="inline-flex items-center gap-1 text-micro text-lia-text-secondary">
                    <MapPin className="w-3 h-3" />{c.location}
                  </span>
                )}
                {c.experience && (
                  <span className="inline-flex items-center gap-1 text-micro text-lia-text-secondary">
                    <Briefcase className="w-3 h-3" />{c.experience}
                  </span>
                )}
                {c.education && (
                  <span className="inline-flex items-center gap-1 text-micro text-lia-text-secondary">
                    <GraduationCap className="w-3 h-3" />{c.education}
                  </span>
                )}
              </div>

              {(!c.status || c.status === "pending") && (
                <div className="flex items-center gap-2 pt-2 border-t border-lia-border-subtle">
                  <button
                    onClick={() => handleAction(c.id, "approved")}
                    className="flex-1 flex items-center justify-center gap-1 py-1.5 rounded-md text-xs font-medium text-status-success bg-status-success/10 hover:bg-status-success/20 transition-colors"
                  >
                    <ThumbsUp className="w-3 h-3" /> Aprovar
                  </button>
                  <button
                    onClick={() => handleAction(c.id, "rejected")}
                    className="flex-1 flex items-center justify-center gap-1 py-1.5 rounded-md text-xs font-medium text-status-error bg-status-error/10 hover:bg-status-error/20 transition-colors"
                  >
                    <ThumbsDown className="w-3 h-3" /> Rejeitar
                  </button>
                  <button
                    onClick={() => handleAction(c.id, "saved")}
                    className="flex items-center justify-center p-1.5 rounded-xl text-lia-text-secondary hover:bg-lia-bg-tertiary transition-colors"
                    title="Salvar para depois"
                  >
                    <Bookmark className="w-3.5 h-3.5" />
                  </button>
                </div>
              )}

              {c.status && c.status !== "pending" && (
                <div className="pt-2 border-t border-lia-border-subtle">
                  <span className={cn(
                    "text-xs font-medium",
                    c.status === "approved" ? "text-status-success" :
                    c.status === "rejected" ? "text-status-error" :
                    "text-status-warning"
                  )}>
                    {c.status === "approved" ? "Aprovado" : c.status === "rejected" ? "Rejeitado" : "Salvo"}
                  </span>
                </div>
              )}
            </div>
          ))
        )}
      </div>

      {candidates.length > 0 && (
        <div className="px-4 py-3 border-t border-lia-border-subtle flex-shrink-0 space-y-2">
          {totalReviewed === candidates.length && totalReviewed > 0 ? (
            <button
              onClick={() => onUpdateData?.({ ...data, calibration_finished: true })}
              className="w-full flex items-center justify-center gap-2 py-2.5 rounded-lg text-sm font-medium text-white bg-wedo-cyan hover:bg-wedo-cyan/90 transition-colors"
            >
              <CheckCircle2 className="w-4 h-4" /> Finalizar Calibração
            </button>
          ) : (
            <button className="w-full flex items-center justify-center gap-2 py-2 rounded-lg text-sm font-medium text-wedo-cyan-text hover:bg-lia-bg-secondary transition-colors">
              Revisar mais <ChevronRight className="w-3.5 h-3.5" />
            </button>
          )}
        </div>
      )}
    </div>
  )
}
