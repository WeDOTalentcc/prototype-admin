"use client"

import React from "react"
import { cn } from "@/lib/utils"
import { User, CheckCircle, XCircle, Target, ThumbsUp, ThumbsDown, Users } from "lucide-react"
import type { CalibrationData, CalibrationCandidate } from "../wizard-types"

interface CriterionItem {
  label: string
  type: "must_have" | "sourcing"
}

interface Props {
  data: Record<string, unknown>
  onApprove?: () => void
  onReject?: () => void
}

/**
 * CalibrationPanel — present candidates for calibration.
 * Enforces minimum 3 profile approvals before allowing advancement.
 * Shows pool counter + Must-haves vs Sourcing Constraints sections.
 */
export function CalibrationPanel({ data, onApprove, onReject }: Props) {
  const d = data as unknown as CalibrationData & {
    pool_count?: number
    criteria?: CriterionItem[]
  }
  const candidates = d.candidates || []
  const threshold = d.threshold || 3
  const approvedCount = d.approved_count || 0
  const canAdvance = approvedCount >= threshold
  const poolCount = d.pool_count ?? null
  const mustHaves = d.criteria?.filter((c) => c.type === "must_have") ?? []
  const sourcingConstraints = d.criteria?.filter((c) => c.type === "sourcing") ?? []

  const handleApproveCandidate = (candidateId: string) => {
    window.dispatchEvent(new CustomEvent("lia:wizard-edit-question", {
      detail: { type: "calibration_approve", candidateId },
    }))
  }

  const handleRejectCandidate = (candidateId: string) => {
    window.dispatchEvent(new CustomEvent("lia:wizard-edit-question", {
      detail: { type: "calibration_reject", candidateId },
    }))
  }

  return (
    <div className="flex flex-col">
      {/* Progress header */}
      <div className="px-4 py-2.5 border-b border-lia-border-subtle">
        <div className="flex items-center justify-between">
          <span className="text-xs text-lia-text-secondary">
            Calibração: {approvedCount}/{threshold} perfis
          </span>
          <div className="flex items-center gap-2">
            {/* Pool counter — updates as user gives feedback */}
            {poolCount !== null && (
              <span className="flex items-center gap-1 text-[10px] text-wedo-cyan font-medium">
                <Users className="w-3 h-3" aria-hidden="true" />
                {poolCount.toLocaleString("pt-BR")} compatíveis
              </span>
            )}
            {d.complete && (
              <span className="px-2 py-0.5 rounded bg-status-success/10 text-status-success text-[10px] font-medium">
                Completa
              </span>
            )}
          </div>
        </div>
        {/* Progress bar */}
        <div className="mt-1.5 h-1.5 rounded-full bg-lia-bg-tertiary overflow-hidden">
          <div
            className={cn(
              "h-full rounded-full transition-[width] duration-300",
              canAdvance ? "bg-status-success" : "bg-wedo-cyan"
            )}
            style={{ width: `${Math.min(100, (approvedCount / threshold) * 100)}%` }}
          />
        </div>
        {!canAdvance && (
          <p className="text-[10px] text-status-warning mt-1">
            Avalie pelo menos {threshold} perfis para continuar
          </p>
        )}
      </div>

      {/* Criteria overview — Must-haves vs Sourcing Constraints */}
      {(mustHaves.length > 0 || sourcingConstraints.length > 0) && (
        <div className="px-4 py-2.5 border-b border-lia-border-subtle space-y-2">
          {mustHaves.length > 0 && (
            <div>
              <p className="text-[10px] font-semibold text-lia-text-disabled uppercase tracking-wide mb-1">
                Must-haves (eliminatórios)
              </p>
              <div className="flex flex-wrap gap-1">
                {mustHaves.map((c, i) => (
                  <span
                    key={i}
                    className="px-1.5 py-0.5 rounded text-[10px] bg-gray-900 text-white"
                  >
                    {c.label}
                  </span>
                ))}
              </div>
            </div>
          )}
          {sourcingConstraints.length > 0 && (
            <div>
              <p className="text-[10px] font-semibold text-lia-text-disabled uppercase tracking-wide mb-1">
                Preferências (sourcing)
              </p>
              <div className="flex flex-wrap gap-1">
                {sourcingConstraints.map((c, i) => (
                  <span
                    key={i}
                    className="px-1.5 py-0.5 rounded text-[10px] border border-lia-border-subtle text-lia-text-secondary"
                  >
                    {c.label}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Candidate cards */}
      <div className="px-4 py-3 space-y-2">
        {candidates.map((c) => (
          <CandidateCard
            key={c.id}
            candidate={c}
            onApproveCandidate={handleApproveCandidate}
            onRejectCandidate={handleRejectCandidate}
          />
        ))}
        {candidates.length === 0 && (
          <div className="text-center py-4">
            <div className="w-5 h-5 mx-auto mb-2 border-2 border-wedo-cyan border-t-transparent rounded-full animate-spin" />
            <p className="text-xs text-lia-text-tertiary">
              Aguardando candidatos para calibracao...
            </p>
          </div>
        )}
      </div>

      {/* Advance footer */}
      {candidates.length > 0 && (
        <div className="flex-shrink-0 px-4 py-3 border-t border-lia-border-subtle bg-lia-bg-primary">
          <button
            onClick={onApprove}
            disabled={!canAdvance}
            className={cn(
              "w-full flex items-center justify-center gap-2 px-3 py-2.5 rounded-md text-sm font-medium transition-colors",
              canAdvance
                ? "bg-wedo-cyan text-white hover:bg-wedo-cyan/90"
                : "bg-lia-bg-tertiary text-lia-text-disabled cursor-not-allowed"
            )}
          >
            <CheckCircle className="w-4 h-4" />
            {canAdvance ? "Calibracao completa — Avancar" : `Faltam ${threshold - approvedCount} perfis`}
          </button>
        </div>
      )}
    </div>
  )
}

function CandidateCard({
  candidate,
  onApproveCandidate,
  onRejectCandidate,
}: {
  candidate: CalibrationCandidate
  onApproveCandidate: (id: string) => void
  onRejectCandidate: (id: string) => void
}) {
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
          <p className="text-sm font-medium text-lia-text-primary truncate">
            {candidate.name}
          </p>
          <p className="text-xs text-lia-text-secondary truncate">
            {candidate.current_title} @ {candidate.current_company}
          </p>
          <div className="flex items-center gap-1.5 mt-1">
            <Target className="w-3 h-3 text-wedo-cyan" />
            <span className="text-[10px] text-wedo-cyan font-medium">
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
        <div className="px-3 pb-2 flex flex-wrap gap-1">
          {candidate.match_criteria.map((mc, i) => (
            <span
              key={i}
              className={cn(
                "px-1.5 py-0.5 rounded text-[10px]",
                mc.met ? "bg-status-success/10 text-status-success" : "bg-status-error/10 text-status-error",
              )}
            >
              {mc.criterion}
            </span>
          ))}
        </div>
      )}

      {/* Action buttons — only if not decided */}
      {!decided && (
        <div className="flex border-t border-lia-border-subtle">
          <button
            onClick={() => onRejectCandidate(candidate.id)}
            className="flex-1 flex items-center justify-center gap-1.5 px-3 py-2 text-xs font-medium text-status-error hover:bg-status-error/5 transition-colors"
          >
            <ThumbsDown className="w-3.5 h-3.5" />
            Rejeitar
          </button>
          <div className="w-px bg-lia-border-subtle" />
          <button
            onClick={() => onApproveCandidate(candidate.id)}
            className="flex-1 flex items-center justify-center gap-1.5 px-3 py-2 text-xs font-medium text-status-success hover:bg-status-success/5 transition-colors"
          >
            <ThumbsUp className="w-3.5 h-3.5" />
            Aprovar
          </button>
        </div>
      )}
    </div>
  )
}
