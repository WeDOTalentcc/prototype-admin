"use client"

import React from "react"
import { cn } from "@/lib/utils"
import { User, CheckCircle, XCircle, Target } from "lucide-react"
import type { CalibrationData, CalibrationCandidate } from "../wizard-types"

interface Props {
  data: Record<string, unknown>
  onApprove?: () => void
  onReject?: () => void
}

/**
 * CalibrationPanel — present candidates for calibration.
 * Follows CalibrationCardModal.tsx pattern (split profile + criteria).
 */
export function CalibrationPanel({ data, onApprove, onReject }: Props) {
  const d = data as unknown as CalibrationData
  const candidates = d.candidates || []
  const threshold = d.threshold || 3

  return (
    <div className="flex flex-col">
      {/* Progress header */}
      <div className="px-4 py-2.5 border-b border-lia-border-subtle flex items-center justify-between">
        <span className="text-xs text-lia-text-secondary font-['Open_Sans',sans-serif]">
          Calibracao: {d.approved_count || 0}/{threshold} perfis
        </span>
        {d.complete && (
          <span className="px-2 py-0.5 rounded bg-status-success/10 text-status-success text-[10px] font-medium font-['Open_Sans',sans-serif]">
            Completa
          </span>
        )}
      </div>

      {/* Candidate cards */}
      <div className="px-4 py-3 space-y-2">
        {candidates.map((c, i) => (
          <CandidateCard key={i} candidate={c} />
        ))}
        {candidates.length === 0 && (
          <p className="text-xs text-lia-text-tertiary font-['Open_Sans',sans-serif] text-center py-4">
            Aguardando candidatos para calibracao...
          </p>
        )}
      </div>
    </div>
  )
}

function CandidateCard({ candidate }: { candidate: CalibrationCandidate }) {
  const decided = !!candidate.decision

  return (
    <div className={cn(
      "rounded-md border overflow-hidden",
      decided ? "border-lia-border-subtle/50 opacity-70" : "border-lia-border-subtle",
    )}>
      <div className="flex items-start gap-2.5 px-3 py-2.5">
        <div className="w-8 h-8 rounded-full bg-lia-bg-secondary flex items-center justify-center flex-shrink-0">
          <User className="w-4 h-4 text-lia-text-disabled" />
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-lia-text-primary font-['Open_Sans',sans-serif] truncate">
            {candidate.name}
          </p>
          <p className="text-xs text-lia-text-secondary font-['Open_Sans',sans-serif] truncate">
            {candidate.current_title} @ {candidate.current_company}
          </p>
          <div className="flex items-center gap-1.5 mt-1">
            <Target className="w-3 h-3 text-wedo-cyan" />
            <span className="text-[10px] text-wedo-cyan font-medium font-['Open_Sans',sans-serif]">
              Match: {Math.round(candidate.match_score * 100)}%
            </span>
          </div>
        </div>

        {decided && (
          candidate.decision === "approved" ? (
            <CheckCircle className="w-5 h-5 text-status-success flex-shrink-0" />
          ) : (
            <XCircle className="w-5 h-5 text-status-error flex-shrink-0" />
          )
        )}
      </div>

      {/* Match criteria */}
      {candidate.match_criteria?.length > 0 && (
        <div className="px-3 pb-2.5 flex flex-wrap gap-1">
          {candidate.match_criteria.map((mc, i) => (
            <span
              key={i}
              className={cn(
                "px-1.5 py-0.5 rounded text-[10px] font-['Open_Sans',sans-serif]",
                mc.met ? "bg-status-success/10 text-status-success" : "bg-status-error/10 text-status-error",
              )}
            >
              {mc.criterion}
            </span>
          ))}
        </div>
      )}
    </div>
  )
}
